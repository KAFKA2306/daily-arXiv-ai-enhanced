# daily_arxiv/daily_arxiv/spiders ディレクトリ

実際にarXivから論文リストを取得するクローラスクリプトを置いています。

## 役割
- `arxiv.py` が `name="arxiv"` のスパイダーを提供し、`CATEGORIES` 環境変数に従って対象分野を切り替えます。
- 取得したIDと分類をエクスポートして後段のAI処理に渡します。

## コマンド例
- `cd daily_arxiv && scrapy crawl arxiv -O ../data/$(date +%Y-%m-%d).jsonl`
- `cd daily_arxiv && scrapy shell https://arxiv.org/list/cs.CV/new` でセレクタを検証します。

## メモ
- 解析対象ページ構造が変わった場合はCSSセレクタをここで更新します。
- `CATEGORIES` はカンマ区切りで複数指定できます。
