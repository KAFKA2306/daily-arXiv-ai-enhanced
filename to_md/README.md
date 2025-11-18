# to_md ディレクトリ

JSONLデータをMarkdown日報に変換するためのスクリプトとテンプレートを格納します。

## 役割
- `convert.py` がカテゴリーごとの目次と論文カードを生成します。
- `paper_template.md` は1件ずつの出力テンプレートです。

## コマンド例
- `python to_md/convert.py --data data/2025-11-18_AI_enhanced_Chinese.jsonl`
- 好みのカテゴリー順にしたい場合は `CATEGORIES="cs.AI,cs.CL" python to_md/convert.py --data data/<FILE>.jsonl`

## メモ
- 入力ファイルには `AI` フィールド（tldr等）が揃っている必要があります。
- 出力されたMarkdownは `data/YYYY-MM-DD.md` に保存されます。
