# daily_arxiv/daily_arxiv パッケージ

Scrapy のアプリケーションロジックを収めたPythonパッケージです。

## 役割
- `items.py` にデータ構造、`pipelines.py` に永続化処理、`middlewares.py` に通信系のカスタマイズを実装しています。
- `settings.py` でスロットルや並列数を制御します。
- `check_stats.py` はデータ重複を検査し、GitHub Actionsの後続ステップを制御します。

## コマンド例
- `python daily_arxiv/daily_arxiv/check_stats.py` で直近データの重複を確認します。
- `PYTHONPATH=daily_arxiv python -m daily_arxiv.check_stats` としてモジュール実行することもできます。

## メモ
- `middlewares.py` や `pipelines.py` を改修する際はScrapyの設定に反映するのを忘れないでください。
- 依存ライブラリは `pyproject.toml` にまとまっています。
