# data ディレクトリ

取得済みの論文データとAI強化済みデータ、Markdownレポートを日付ごとに保存します。ファイル数が多いためクリーンアップ方針を決めておくと管理しやすくなります。

## ファイル命名規則
- `YYYY-MM-DD.jsonl`: 生のクローリング結果。
- `YYYY-MM-DD_AI_enhanced_Chinese.jsonl`: AIで補強されたフィールド付きJSONL。
- `YYYY-MM-DD.md`: `to_md/convert.py` で生成される日報Markdown。

## コマンド例
- 最新ファイルを確認: `ls data | tail`
- 新しいデータ収集: `cd daily_arxiv && scrapy crawl arxiv -O ../data/$(date +%Y-%m-%d).jsonl`
- Markdown化: `python to_md/convert.py --data data/2025-11-18_AI_enhanced_Chinese.jsonl`

## メモ
- データを公開ページに反映する前に `ai/enhance.py` を通してAIフィールドを埋めてください。
- 過去ファイルの整理や圧縮を行う場合はバックアップを忘れずに。
