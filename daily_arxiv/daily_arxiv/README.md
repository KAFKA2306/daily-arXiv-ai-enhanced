# daily_arxiv/daily_arxiv パッケージ

Scrapy で arXiv を巡回し、生の JSONL を作るアプリケーションロジック一式です。`/home/kafka/projects/daily-arXiv-ai-enhanced/daily_arxiv/daily_arxiv` 以下の各モジュールを押さえておくと調査や改修時に迷いません。

## 主要ファイルと役割
- `spiders/arxiv.py`: `CATEGORIES` 環境変数をカンマ区切りで受け取り、対象カテゴリごとの `/list/<cat>/new` を巡回する単一スパイダー。`self.target_categories` で対象集合を持ち、抽出した arXiv ID とカテゴリ候補を `yield` します。
- `items.py`: `DailyArxivItem` で ID フィールドを最低限定義。必要なら `abstract`, `authors` などを追加して `pipelines.py` への受け渡しを明示できます。
- `pipelines.py`: `arxiv` Python SDK を使い ID から正式メタデータ（タイトル、著者、コメント、PDF/ABS URL）を補完する永続化パイプライン。`ITEM_PIPELINES` で優先度 300 に登録済みです。
- `middlewares.py`: Spider/Downloader ミドルウェアの雛形。現在はログや例外フックのみですが、プロキシやリトライを追加する際の置き場所です。
- `settings.py`: BOT 名、モジュールパス、`ITEM_PIPELINES`、`FEED_EXPORT_ENCODING` など Scrapy のグローバル設定を保持し、`scrapy.cfg` から参照されます。
- `check_stats.py`: 最新 `data/YYYY-MM-DD.jsonl` を走査し、重複が無ければ終了コード 0、重複のみなら 1、例外時に 2 を返す後続処理ガード。
- `__init__.py`: Python パッケージの初期化子で、モジュール解決に必要です。

## 設定ファイル・環境変数候補
- `daily_arxiv/config.yaml`: Scrapy を単体実行したい場合のカテゴリやモデル名のデフォルト。GitHub Actions では Secrets/Variables で上書きされるため、あくまでローカルの候補値です。
- 環境変数 `CATEGORIES`, `LANGUAGE`, `MODEL_NAME`: `run.sh` や Actions から注入され、スパイダーや後段 AI パイプラインの挙動を切り替える主要パラメータ。カテゴリは `cs.CL,cs.CV` のように入力します。
- `OPENAI_API_KEY`, `OPENAI_BASE_URL`: Scrapy 自体は参照しませんが、`check_stats.py` 以降の AI ステージと連動させる際に同じシェルで export しておくと一気通貫で検証できます。

## データフローの目安
1. `scrapy crawl arxiv -O ../data/<日付>.jsonl` を実行すると、`pipelines.py` が arXiv API 呼び出しを行い詳細付き JSONL を `data/` 配下へ書き出します。
2. `python daily_arxiv/daily_arxiv/check_stats.py` が直近ファイルを検査し、重複のみなら終了コード 1 で GitHub Actions の AI ステージをスキップします。
3. 正常（終了コード 0）の場合、`ai/enhance.py` → `to_md/convert.py` が `<日付>_AI_enhanced_<LANG>.jsonl` と Markdown を生成します。
4. `assets/file-list.txt` 更新や README 再生成は `run.sh` に委譲されますが、元データはこのパッケージが供給源です。

## コマンド例
- `python daily_arxiv/daily_arxiv/check_stats.py` で重複検査。CI と同じ終了コードで挙動を再現できます。
- `PYTHONPATH=daily_arxiv scrapy crawl arxiv -O data/$(date +%Y-%m-%d).jsonl -s LOG_LEVEL=INFO` とすると、ルート直下からでも実行できログレベルも調整できます。
- `cd daily_arxiv && scrapy list` で利用可能なスパイダー候補を確認します（現状 `arxiv` のみ）。

## 開発メモ
- `middlewares.py` や `pipelines.py` を改修したら `settings.py` を通じて有効化されているか確認してください。特に複数パイプラインを追加した際は優先度が衝突しやすいので注意。
- arXiv へのアクセスが失敗する場合は `pipelines.py` 内で `arxiv.Client` のページサイズ（`self.page_size`）や再試行戦略を調整するのが第一候補です。
- 依存ライブラリはルートの `pyproject.toml` / `uv.lock` にまとまっています。Scrapy 側だけ検証したいときは `.venv` をアクティブにして `uv pip` ではなく `uv run scrapy ...` を使うと衝突を避けられます。
