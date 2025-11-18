# リポジトリ概要
本プロジェクトは https://arxiv.org の最新論文を毎日クロールし、LLM（既定では DeepSeek）で**日本語要約**を生成して GitHub Pages に公開する自動パイプラインです。サーバー不要で、GitHub Actions + Pages のみで運用できます。

最新の公開サイトは https://kafka2306.github.io/daily-arXiv-ai-enhanced/ で閲覧できます。

> **法的注意**: 学術データに関する各国の規制や検閲要件を必ず確認してください。派生物を公開する場合は、中国本土からアクセス可能な入口を削除し、原論文および AI 生成物の内容審査を行う義務があります。

## 主な機能
- **ゼロインフラ運用**: GitHub Actions がクローリング〜要約〜Markdown 化を自動化し、Pages が公開を担当。
- **日本語 AI 要約**: `LANGUAGE=Japanese` を既定とし、DeepSeek など任意のモデルでカテゴリ別サマリーを生成。
- **柔軟なカテゴリ**: `CATEGORIES` で cs.CV/cs.AI/cs.CL など任意の arXiv 分野を指定可能。
- **多端末対応 UI**: `index.html`・`settings.html` などのフロントエンドでフィルタ、キーワード検索、ローカル設定保存が可能。
- **再利用しやすい成果物**: `data/` に JSONL、`to_md/` に Markdown を保存し、下流分析や別サイトにも流用できます。

## デモ
- 公開サイト: https://dw-dengwei.github.io/daily-arXiv-ai-enhanced/
- Pages を有効化すると `https://<GitHubユーザー名>.github.io/daily-arXiv-ai-enhanced/` で閲覧できます。

## GitHub Actions 設定と実行フロー
2. `Settings > Secrets and variables > Actions` で以下を設定します。
   - **Secrets**: `OPENAI_API_KEY`（必須）、`OPENAI_BASE_URL`（Gemini 以外を使う場合のみ）、`ACCESS_PASSWORD`（任意。未設定だとハッシュは `DISABLED_NO_PASSWORD_SET_IN_SECRETS` で固定）。
   - **Variables**: `CATEGORIES`（例: `cs.CL, cs.CV`）、`LANGUAGE`（未指定時は自動で `Japanese`）、`MODEL_NAME`（未指定時は `gemini-2.5-pro-preview`）、`MIN_INTERVAL_SECONDS`（LLM 呼び出しのグローバル最小間隔。既定は `60` 秒で 1 件/分を保証）、`EMAIL` と `NAME`（CI が git commit/push する際に使用）。
3. `.github/workflows/run.yml` は以下の構成です（`permissions` で `contents/pages/id-token` を write に設定し、`concurrency` で `github-pages` グループを共有）。
   - **依存インストール**: `actions/checkout@v4` → `uv` をスクリプトで導入し `uv sync`。すべて `.venv` に展開します。
   - **Crawl ステップ**: `.venv` を有効化し、日付付き JSONL を再生成。`LANGUAGE` と `MODEL_NAME` は空ならデフォルトをセットし、`MODEL_NAME` が `gemini-*` なら `OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai` を自動補完します。
   - **Dedup ステップ**: `python daily_arxiv/check_stats.py` の終了コードを `has_new_content`/`skip_reason` に変換。`1`（新規なし）や `2`（処理エラー）の場合は後続処理をスキップします。
   - **AI → Markdown**: 新規データがある場合のみ `ai/enhance.py` → `to_md/convert.py` を実行し、`assets/file-list.txt` をリストアップ。`update_readme.py` が存在すれば README も再生成します。
   - **認証ハッシュ更新**: `ACCESS_PASSWORD` を openssl で SHA-256 化し、`js/auth-config.js` の `passwordHash` 値を `python3 -c` ワンライナーで置換。未設定時は警告だけ出して固定文字列を埋め込みます。
   - **サマリー & Commit/Pull/Push**: dedup が `true` のときのみ `git add .` → `git commit -m "update: <UTC日付> arXiv papers"` → 最大 3 回リトライ付きで `git push origin main`。push 失敗時は都度 `git pull --no-edit` でリベースします。
   - **GitHub Pages アーティファクト**: `public-site/` を作成し、`index.html` `settings.html` `login.html` `statistic.html` をコピー → `actions/upload-pages-artifact@v4` でアップロードします。
   - **Deploy ジョブ**: `needs: build` の `deploy` ジョブが `actions/deploy-pages@v4` を呼び出し、`environment: github-pages` へ公開。`steps.deployment.outputs.page_url` が自動で環境 URL に入ります。
4. ワークフローは cron `30 1 * * *`（UTC、毎日 10:30 JST）で自動実行され、`Actions > arXiv-daily-ai-enhanced > Run workflow` から手動起動も可能です。dedup で新着が無い場合は Crawl の成果のみで終了し、Pages デプロイ・コミットはスキップされます。
5. README の反映を強制したい場合は `template.md` を編集し、`python3 update_readme.py`（もしくは CI 実行で自動）を使って `README.md` を再生成してください。

## ローカル実行と検証コマンド
- `uv sync` : `pyproject.toml` / `uv.lock` を基に Python 3.12 依存を `.venv` へ展開。
- `source .venv/bin/activate && bash run.sh` : クローリング→重複検査→AI→Markdown→`assets/file-list.txt` 更新までを一括実行。`OPENAI_API_KEY`, `OPENAI_BASE_URL`, `LANGUAGE=Japanese`, `CATEGORIES`, `MODEL_NAME` を事前に export。
- `scrapy crawl arxiv -o data/<日付>.jsonl` : spider の単体検証。
- `python daily_arxiv/daily_arxiv/check_stats.py` : 重複検査（終了コード 0=続行/1=新規なし/2=エラー）。
- `python ai/enhance.py --data data/<日付>.jsonl --min-interval-secs 60` : AI 要約のみ再実行。`--min-interval-secs` を増減させると LLM コールの全体レート（既定 60 秒＝1件/分）を調整できます。
- `python to_md/convert.py --data data/<日付>_AI_enhanced_Japanese.jsonl` : Markdown のみ再生成。
- `python3 update_readme.py` : README 再生成。
- `bash setup-local-auth.sh` : `js/auth-config.js` にパスワードハッシュを注入。

## 設定値の変更ガイド
本番の GitHub Actions、ローカル検証、公開サイトの 3 つで設定箇所が分かれます。下記の手順に沿って更新すると、検索条件や API、サイトの挙動を安全に変更できます。

### 1. API／LLM 設定
#### GitHub Actions（本番環境）
1. GitHub のリポジトリで「Settings（設定）> Secrets and variables > Actions」を開きます。
2. **Secrets** に以下を登録します。
   - `OPENAI_API_KEY`: 利用する API キー（必須）。Gemini を使用する場合もキーを格納します。
   - `OPENAI_BASE_URL`: 既定は空で問題ありません。OpenAI 公式を使うなら `https://api.openai.com/v1`、Gemini なら `https://generativelanguage.googleapis.com/v1beta/openai` などを入力します。
   - `ACCESS_PASSWORD`: サイトをパスワード保護したい場合のみ設定します。未設定なら公開ページは誰でも閲覧できます。
3. **Variables** に以下を登録または更新します。
   - `MODEL_NAME`: 例 `gemini-2.5-pro-preview`。Gemini 系を指定した場合はワークフローが自動で `OPENAI_BASE_URL` を補完します。
   - `LANGUAGE`: 要約出力言語。既定は `Japanese`（AI 出力ファイル名や Markdown ファイルの参照言語にも使われます）。
   - `MIN_INTERVAL_SECONDS`: LLM 呼び出しのグローバル最小間隔（秒）。CI ではこの値が `--min-interval-secs` に渡され、並列ワーカーがあっても常に 1 コールごとに最低この時間だけ待機します。60 秒推奨。
   - `EMAIL` / `NAME`: CI がコミットする際の `user.email` / `user.name`。
4. 変更後に `Actions > arXiv-daily-ai-enhanced > Run workflow` から手動実行し、ログで `Using model ...` `OPENAI_BASE_URL=...` が期待通りか確認します。

#### ローカル検証用の設定
1. ルートに `.env` を作成し、以下のように記述します（`.env` はコミットしないでください）。
   ```bash
   OPENAI_API_KEY=xxxxx
   OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
   LANGUAGE=Japanese
   CATEGORIES="cs.AI, cs.CL"
   MODEL_NAME=gemini-2.5-pro-preview
   MIN_INTERVAL_SECONDS=60
   ACCESS_PASSWORD=任意のパスワード
   ```
2. `source .venv/bin/activate && export $(cat .env | xargs)` のように読み込んでから `bash run.sh` を実行すると、CI と同じ設定で再現できます。
3. パスワード付きでローカル UI を試す場合は `.env` を読み込んだ状態で `bash setup-local-auth.sh` を実行し、生成された `js/auth-config.js` をブラウザで参照します。

#### LLM コール間隔の制御
1. `ai/enhance.py` は `--min-interval-secs`（デフォルト 60 秒）で **グローバルな最小待機時間** を設けており、並列ワーカーが複数あっても LLM 呼び出しはこの間隔で直列化されます。
2. GitHub Actions では `vars.MIN_INTERVAL_SECONDS` の値がそのまま `--min-interval-secs` に渡されます。1 分より速くしたい場合や、逆に余裕を持たせたい場合は Vars を変更してから次のワークフローを起動してください。
3. ローカルで挙動を確認したい場合は `python ai/enhance.py --data ... --min-interval-secs 30` のように任意の秒数を指定すれば、その場でレートを切り替えられます。

### 2. クローリング対象・検索条件の更新手順
1. GitHub の「Settings > Secrets and variables > Actions > Variables」で `CATEGORIES` を編集します。値は `cs.AI, cs.CL` のようにカンマ区切り・半角スペース付きで記述すると `daily_arxiv/daily_arxiv/spiders/arxiv.py` のパーサーと一致します。
2. `LANGUAGE` を変更すると `ai/enhance.py` が `<日付>_AI_enhanced_<LANGUAGE>.jsonl` を生成し、`to_md/convert.py` の `--data` 引数にも同じ言語名が必要になります。
3. 変更の事前確認にはローカルで `scrapy crawl arxiv -o data/テスト日付.jsonl` を実行し、`python daily_arxiv/daily_arxiv/check_stats.py` が終了コード `0` で終わるか確認してください。
4. カテゴリ追加や除外の結果を即時に反映させたい場合は `Actions` から手動でワークフローを起動するか、ローカルで `bash run.sh` を回して差分を `git diff data/` で確認します。
5. サイト側でキーワード検索や本文全文検索をデフォルト状態に戻したい場合は `localStorage` を空にするか、後述の `settings.html` で「Reset to Default」を押します。これにより API 側で増減させたカテゴリのみが反映されます。

### 3. サイト設定（UI／ローカル検索／認証）
#### 公開ページのテキスト・ロゴ
1. サイトタイトルや説明文を変える場合は `index.html`, `settings.html`, `statistic.html` の `<head>` 内にある `<title>`/`meta`/ロゴ経路を編集します。
2. 画像やサンプル Markdown を差し替える場合は `assets/` `images/` に置き換え、`assets/file-list.txt` を `bash run.sh` で再生成しておきます。
3. 変更内容を GitHub Pages に反映させるには `git add` → `git commit` の後、CI もしくは `Actions` でのデプロイ完了を確認します。

#### フロントエンド検索・フィルタの操作
1. ブラウザで `https://<ユーザー名>.github.io/daily-arXiv-ai-enhanced/settings.html` を開き、`Preferred Keywords` / `Preferred Authors` 入力欄に文字列を入れて `Add` ボタンを押します。
2. 追加した条件は `localStorage.preferredKeywords` / `localStorage.preferredAuthors` に配列として保存され、`index.html` 側のフィルタタブに即時反映されます。
3. 条件を削除したい場合は各タグの `×` を押すか、ページ最下部の「Reset to Default」を押してください。`Reset` は `localStorage` を完全に初期化します。
4. テキスト検索バー（虫眼鏡アイコン）を使うと、AI 要約本文やタイトルの全文検索がオンになります。状態はセッション毎に保持され、追加の設定ファイルは不要です。

#### パスワード保護
1. 公開サイトにログイン保護をかけたい場合、GitHub の Secrets に `ACCESS_PASSWORD` を追加します。CI が `js/auth-config.js` の `passwordHash` を自動上書きし、`login.html` が有効になります。
2. ローカルで同じ挙動を再現するには `.env` に `ACCESS_PASSWORD` を入れた上で `bash setup-local-auth.sh` を実行し、その後に `login.html` をブラウザで開いて入力テストを行います。

## GitHub Pages 設定メモ
1. GitHub の `Settings > Pages` で `Build and deployment` を `Deploy from a branch` に設定。
2. `Branch` を `main`, `/(root)` に指定し保存。
3. デプロイ完了後、`https://<ユーザー名>.github.io/daily-arXiv-ai-enhanced/` を確認。`pages-build-deployment` ワークフローが成功しているか `Actions` で確認できます。
4. カスタムドメインを使う場合は `Custom domain` を設定し、DNS を `username.github.io` に向け、HTTPS を有効にしてください。
