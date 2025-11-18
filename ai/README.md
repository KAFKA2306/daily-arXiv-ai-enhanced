# ai ディレクトリ

LLM要約のテンプレートとスクリプトをまとめたモジュールです。DeepSeekなどOpenAI互換APIを呼び出し、論文サマリーを整形します。

## 役割
- `enhance.py` がJSONLファイルを読み込み、AIセクションを埋めます。
- `structure.py` はLangChainのStructured Output用モデルを定義します。
- `system.txt` と `template.txt` はプロンプトテンプレートです。

## 代表的なコマンド
- `python ai/enhance.py --data data/2025-11-18.jsonl --max_workers 4`
- `OPENAI_API_KEY=xxx OPENAI_BASE_URL=https://api.example.com/v1 python ai/enhance.py --data data/<DATE>.jsonl`

## 運用メモ
- `.env` が存在すれば自動で読み込まれます。
- APIクォータ節約のため `--max_workers` を環境に応じて調整してください。
