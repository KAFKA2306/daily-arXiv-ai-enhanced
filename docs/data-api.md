# arXiv catalog distribution API v1

`data/*.jsonl` を正準アーカイブとして維持しつつ、検索・分析しやすい決定的な配布物を `build/api/v1/` に生成します。既存JSONLは変更しません。

## 配布物

| ファイル | 内容 |
| --- | --- |
| `manifest.json` | 件数、期間、元ファイルSHA-256、配布物SHA-256、キャッシュ方針、出典 |
| `papers.json` | 全日次JSONLをarXiv IDで統合したJSON |
| `papers.csv` | 表計算・DuckDB等で扱いやすいCSV |
| `facets.json` | primary category、category、公開年、公開日の件数索引 |

同一arXiv IDが複数日次ファイルに存在する場合、`extraction_date` が最も新しいレコードを採用します。元レコードは削除しないため履歴は `data/*.jsonl` に残ります。

## 生成

```bash
python scripts/build_arxiv_catalog.py --data-dir data --output-dir build/api/v1
```

外部通信は行いません。同じ入力から同じJSON/CSV/manifestを生成します。

## 差分同期

最初に `manifest.json` を取得し、`files.<name>.sha256` が前回値と異なる配布物だけを再取得してください。推奨キャッシュ時間は3600秒です。

```python
import hashlib, json, urllib.request

base = "https://raw.githubusercontent.com/KAFKA2306/daily-arXiv-ai-enhanced/main/api/v1"
with urllib.request.urlopen(f"{base}/manifest.json") as r:
    manifest = json.load(r)

# papers.jsonを取得した後の検証例
raw = open("papers.json", "rb").read()
assert hashlib.sha256(raw).hexdigest() == manifest["files"]["papers.json"]["sha256"]
```

## データ辞書

`papers.json` の各論文は既存JSONLと同じフィールドを保持します。主要フィールドは `id`（arXiv version付きID）、`title`、`authors`、`abstract`、`categories`、`primary_category`、`published`、`arxiv_url`、`pdf_url`、`extraction_date` です。欠損可能な書誌属性は `null` のまま保持します。

`papers.csv` では `authors` と `categories` を `|` 区切りに変換し、それ以外は既存値を保持します。

## 出典・利用条件

メタデータ取得元はarXivです。API仕様は <https://info.arxiv.org/help/api/user-manual.html>、API利用条件は <https://info.arxiv.org/help/api/tou.html> を参照してください。論文本文・個別コンテンツの再利用条件は各論文のライセンスに従ってください。

## バージョニング

v1では既存フィールドの意味を破壊的に変更しません。互換性を壊す変更は新しいAPIバージョンへ分離します。
