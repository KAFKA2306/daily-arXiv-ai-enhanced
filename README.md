# Daily arXiv AI Enhanced — arXiv論文の日本語要約パイプライン

**公開サイト:** https://kafka2306.github.io/daily-arXiv-ai-enhanced/

arXivの公開レコードを定期取得し、設定したLLMで日本語要約を生成して、GitHub Pagesへ公開する自動パイプラインです。

原論文の情報とAI生成文を混同せず、論文ID、版、著者、日付、カテゴリ、出典URL、使用モデル、生成設定を追跡できる状態で保存します。

## できること

- 指定したarXivカテゴリの新着レコードを取得
- 論文タイトル、著者、抄録、版、日付、URLを保存
- LLMによる日本語要約を生成
- 同一論文・同一版の重複を検出
- JSONL、Markdown、静的Webページを生成
- キーワード・著者フィルターをブラウザへ保存
- 取得や生成に失敗した日の公開を抑止

## 処理の流れ

```text
arXiv公開レコードを取得
  → 論文ID・版・著者・日付・カテゴリを検証
  → 既存データとの重複を確認
  → LLMへ要約を依頼
  → 原文とAI要約を別フィールドへ保存
  → Markdown・静的ページを生成
  → 内容とリンクを検証
  → GitHub Pagesへ公開
```

次の情報が欠ける成果物は`quarantine`として公開しません。

- arXiv IDと版
- 原論文URL
- 入力レコード
- 使用モデル
- 生成設定
- 実行ワークフローの記録

機械可読な定義:

- [プロジェクト・オントロジー](ontology/project.yaml)
- [共通因果・証拠オントロジー](https://github.com/KAFKA2306/know/blob/main/ontology/causal-evidence-core.yaml)

## GitHub Actionsの設定

`Settings > Secrets and variables > Actions`で設定します。

### Secrets

| 名前 | 内容 |
| --- | --- |
| `OPENAI_API_KEY` | 使用するOpenAI互換APIのキー |
| `OPENAI_BASE_URL` | 既定以外のAPIを使う場合のURL |
| `ACCESS_PASSWORD` | 任意のサイト保護用パスワード |

### Variables

| 名前 | 例・内容 |
| --- | --- |
| `CATEGORIES` | `cs.AI, cs.CL` |
| `LANGUAGE` | 既定は`Japanese` |
| `MODEL_NAME` | 使用モデル名 |
| `MIN_INTERVAL_SECONDS` | LLM呼び出し間隔 |
| `MAX_PAPERS` | 1回の取得上限 |
| `SORT_BY` | `relevance`、`submitted_date`など |
| `SORT_ORDER` | `desc`または`asc` |
| `EMAIL` / `NAME` | CIコミット用のGit識別情報 |

APIキー、パスワード、`.env`はコミットしません。

## ローカル実行

```bash
uv sync
source .venv/bin/activate
bash run.sh
```

個別処理:

```bash
scrapy crawl arxiv -o data/<date>.jsonl
python daily_arxiv/daily_arxiv/check_stats.py
python ai/enhance.py --data data/<date>.jsonl --min-interval-secs 60
python to_md/convert.py --data data/<date>_AI_enhanced_Japanese.jsonl
bash setup-local-auth.sh
```

ローカル設定例:

```bash
OPENAI_API_KEY=xxxxx
OPENAI_BASE_URL=https://example.com/v1
LANGUAGE=Japanese
CATEGORIES="cs.AI, cs.CL"
MODEL_NAME=<configured-model>
MIN_INTERVAL_SECONDS=60
MAX_PAPERS=10
SORT_BY=relevance
SORT_ORDER=desc
ACCESS_PASSWORD=<optional>
```

## 公開前の確認

1. arXiv ID、版、日付、原論文URLが保存されている
2. 重複検査が成功している
3. AI要約が原文とは別に保存されている
4. 生成ページから原論文へ移動できる
5. 使用モデルと生成設定が追跡できる
6. Actions実行結果と公開内容が一致する

## 注意

- AI要約は原論文の代替ではありません
- AI要約は著者自身の文章・見解ではありません
- arXiv掲載は査読済み、再現済み、正しいことを意味しません
- 技術的評価を加える場合は、その根拠と評価方法を別に記録します
- 原論文とarXivの利用条件に従い、本文を必要以上に複製しません

**README最終監査:** 2026-08-01
