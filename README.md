# リポジトリ概要
本プロジェクトは https://arxiv.org の最新論文を毎日クロールし、LLM（既定では DeepSeek）で**日本語要約**を生成して GitHub Pages に公開する自動パイプラインです。サーバー不要で、GitHub Actions + Pages のみで運用できます。

最新の公開サイトは `https://kafka2306.github.io/daily-arXiv-ai-enhanced/` で閲覧できます。

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
   - **Variables**: `CATEGORIES`（例: `cs.CL, cs.CV`）、`LANGUAGE`（未指定時は自動で `Japanese`）、`MODEL_NAME`（未指定時は `gemini-2.5-pro-preview`）、`EMAIL` と `NAME`（CI が git commit/push する際に使用）。
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
- `python ai/enhance.py --data data/<日付>.jsonl` : AI 要約のみ再実行。
- `python to_md/convert.py --data data/<日付>_AI_enhanced_Japanese.jsonl` : Markdown のみ再生成。
- `python3 update_readme.py` : README 再生成。
- `bash setup-local-auth.sh` : `js/auth-config.js` にパスワードハッシュを注入。

## GitHub Pages 設定メモ
1. GitHub の `Settings > Pages` で `Build and deployment` を `Deploy from a branch` に設定。
2. `Branch` を `main`, `/(root)` に指定し保存。
3. デプロイ完了後、`https://<ユーザー名>.github.io/daily-arXiv-ai-enhanced/` を確認。`pages-build-deployment` ワークフローが成功しているか `Actions` で確認できます。
4. カスタムドメインを使う場合は `Custom domain` を設定し、DNS を `username.github.io` に向け、HTTPS を有効にしてください。

## キーワード／著者フィルタの設定方法
- `settings.html` からキーワード／著者を入力して `Add` すると、`localStorage` の `preferredKeywords` / `preferredAuthors` に保存されます（実装: `js/settings.js`, `js/app.js`）。
- `Reset to Default` ボタンで初期化、`Save Settings` で即時保存、パスワード保護時は `Auth.logout()` で再認証できます。
- arXivカテゴリ自体を変える場合は GitHub の `Settings > Secrets and variables > Actions > Variables` にある `CATEGORIES` を更新し、次回ワークフロー実行で反映されます。
