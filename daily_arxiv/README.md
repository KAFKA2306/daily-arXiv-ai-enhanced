# daily_arxiv ディレクトリ

Scrapy プロジェクトのルートです。`scrapy.cfg` や `config.yaml` を介してクロール設定を制御します。

## 役割
- `scrapy.cfg` でモジュールパスやログ設定を宣言します。
- `config.yaml` はGitHub Actionsから上書きされる環境設定の雛形です。

## `config.yaml` の例
ローカル検証時にカテゴリや LLM モデルを試す場合は、`daily_arxiv/config.yaml` に以下のような候補値を置いておくと分かりやすいです（Actions では Secrets/Variables が優先されます）。

```yaml
arxiv:
  categories:  # 論文カテゴリ
    - cs.AI
    - cs.LG
    - cs.CL
    - cs.CV
    - stat.ML
    - cs.IR
    - cs.HC
    - cs.SE
    - q-fin.ST

llm:
  model_name: 'gemini-2.5-pro-preview'  # 使用するLLMモデル
```

各カテゴリの狙いは以下の通りです。生成系の基盤技術（cs.AI/cs.LG/stat.ML）と応用面（cs.CL/cs.CV/cs.IR）、人間中心設計（cs.HC）、ソフトウェア工学（cs.SE）、計量ファイナンス（q-fin.ST）をすべて拾う構成で、日々の生成AI関連研究を広くカバーできます。

## コマンド例
- `cd daily_arxiv && scrapy crawl arxiv -O ../data/$(date +%Y-%m-%d).jsonl`
- `cd daily_arxiv && scrapy list` で利用可能なスパイダーを確認します。

## メモ
- `CATEGORIES` などの環境変数を設定してから実行すると対象分野を切り替えられます。
- ローカル実行時は `pip install -r requirements.txt` 相当の依存を整えてください。
