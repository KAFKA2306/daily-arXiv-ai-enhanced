# リポジトリガイドライン

英語と中国語はすべて日本語に翻訳すること。

## プロジェクト構成とモジュール
Scrapy プロジェクトは `daily_arxiv/daily_arxiv` にあり、spider、pipeline、重複検査 (`check_stats.py`) が `data/YYYY-MM-DD.jsonl` を生成します。`ai/` 配下の `enhance.py` とテンプレート群が AI 要約ファイル `<date>_AI_enhanced_<LANG>.jsonl` を作り、`to_md/convert.py` と `paper_template.md` が GitHub Pages 用 Markdown を出力します。静的サイトは `index.html`、`settings.html`、`css/`、`js/`、`assets/`、`images/` で構成され、`update_readme.py`、`template.md`、`readme_content_template.md` がドキュメントを再生成します。大きな成果物は `data/` か厳選サンプル用の `assets/` `images/` に限定してください。

## ビルド・テスト・開発コマンド
- `uv sync` で Python 3.12 依存を `.venv` に同期。
- `source .venv/bin/activate && bash run.sh` が crawl → dedup → AI → Markdown を一括実行。事前に `OPENAI_API_KEY` `OPENAI_BASE_URL` `LANGUAGE` `CATEGORIES` `MODEL_NAME` に加え、必要なら `MAX_PAPERS` `SORT_BY` `SORT_ORDER` を export。
- `scrapy crawl arxiv -o data/2025-11-18.jsonl` は AI 処理を飛ばして spider 改修を検証。
- `python daily_arxiv/daily_arxiv/check_stats.py` は dedup 結果を表示し、終了コード `0` 続行 `1` 新規なし `2` エラーを示します。
- `python ai/enhance.py --data data/2025-11-18.jsonl` と `python to_md/convert.py --data data/2025-11-18_AI_enhanced_Japanese.jsonl` で後段ステージを個別に確認。

## コーディング規約と命名
Python コードは PEP 8、インデント 4 スペース、`snake_case` 関数、定数は大文字、公開ヘルパーへ docstring を付与。Scrapy の spider 名は小文字 (`arxiv` など)、pipeline クラス名は役割を明確に。YAML と環境変数キーは既存の大文字小文字を踏襲します。フロントエンド JS は camelCase、CSS セレクタは kebab-case、静的ファイル名は短く意味のある語を使います。

## テスト運用指針
現状 pytest は無いため、再現性のあるパイプライン実行を回帰テストとみなします。シークレット無しで `bash run.sh` を実行すると crawl と dedup、`assets/file-list.txt` 更新までを確認できます。AI や Markdown を触る場合はシークレットをセットし、同じコマンドでもう一度流すか、小さな `data/` フィクスチャで `python ai/enhance.py ...` `python to_md/convert.py ...` を順番に実行し差分を確認してください。GitHub Actions (`.github/workflows/run.yml`) は 01:30 UTC にスケジュールされるので、PR では最新ジョブの成否を言及します。

## コミットとプルリクエスト
日次取り込みは `update: YYYY-MM-DD arXiv papers` 形式を継続し、構造変更は `feat:` `fix:` `refactor:` などで区別します。PR では変更内容の概要、影響ディレクトリ (`daily_arxiv/` `ai/` `to_md/` `assets/` など)、追加した環境変数やシークレット、UI が変わる場合のスクリーンショットやサンプル Markdown を必ず記載。`data/` 差分は意図した日付に限定し、`bash run.sh` や CI の実行結果も明記してください。

## セキュリティと設定ヒント
`OPENAI_API_KEY` `OPENAI_BASE_URL` `ACCESS_PASSWORD` (任意) と `LANGUAGE` `CATEGORIES` `MODEL_NAME` `MAX_PAPERS` `SORT_BY` `SORT_ORDER` `EMAIL` `NAME` などの変数はリポジトリ設定に保存し、コードへハードコードしないでください。ローカル検証時は必要なシェルでのみ export し、作業後に unset します。パスワードを更新したら GitHub Actions か `setup-local-auth.sh` を実行し、`js/auth-config.js` のハッシュが新しい値へ置き換わったことを確認してからデプロイします。
