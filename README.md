# リポジトリ概要
本プロジェクトは https://arxiv.org の最新論文を毎日クロールし、LLM（既定では DeepSeek）で**日本語要約**を生成して GitHub Pages に公開する自動パイプラインです。サーバー不要で、GitHub Actions + Pages のみで運用できます。

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
1. リポジトリを fork し、必要なら `buy-me-a-coffee/README.md` などの著者情報を更新します。
2. `Settings > Secrets and variables > Actions` に以下を登録します。
   - **Secrets**: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, （任意）`ACCESS_PASSWORD`。
   - **Variables**: `CATEGORIES`（例: `cs.CL, cs.CV`）、`LANGUAGE=Japanese`、`MODEL_NAME`、`EMAIL`、`NAME`。
3. `.github/workflows/run.yml` の主なステップと実行コマンド:
   - 依存解決: `curl -LsSf https://astral.sh/uv/install.sh | sh` → `uv sync`
   - クローリング: `. venv` 有効化後 `scrapy crawl arxiv -o data/<日付>.jsonl`
   - 重複検査: `python daily_arxiv/check_stats.py`
   - AI 要約: `python ai/enhance.py --data data/<日付>.jsonl`
   - Markdown 変換: `python to_md/convert.py --data data/<日付>_AI_enhanced_<LANGUAGE>.jsonl`
   - ファイル一覧更新: `ls data/*.jsonl | sed 's|data/||' > assets/file-list.txt`
   - 認証設定: `js/auth-config.js` の `PLACEHOLDER_PASSWORD_HASH` を Secrets ベースのハッシュで置換
4. `Actions > arXiv-daily-ai-enhanced` から `Run workflow` ボタンで手動実行できます。デフォルトのスケジュールは cron `30 1 * * *` (UTC) です。必要に応じて `run.yml` の `schedule` を編集してください。
5. README を更新したい場合はこの `template.md` を編集し、`python3 update_readme.py`（Windows なら `py update_readme.py` など）を実行して再生成します。

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