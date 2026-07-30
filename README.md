# Daily arXiv AI Enhanced

arXivの公開レコードを定期取得し、設定されたLLMで日本語要約を生成してGitHub Pagesへ公開する自動パイプラインです。

- 公開サイト: https://kafka2306.github.io/daily-arXiv-ai-enhanced/

## 因果・証拠オントロジー

上位システムは `ScholarlySummaryPublicationPipeline` です。

```text
arXiv公開レコード
→ 論文ID・版・著者・日付・カテゴリの保持
→ 重複判定
→ LLM要約生成
→ SourceText / AIGeneratedSummary の分離
→ Markdown変換
→ 検証
→ Pages公開
```

原論文のタイトル、著者、抄録、カテゴリなどの出典情報と、AIが生成した要約・評価を別クラスとして保存します。AI要約を著者の主張として扱いません。arXiv ID、版、出典URL、入力レコード、モデル、生成設定、ワークフロー実行が欠ける成果物は `quarantine` とし、公開しません。

- [プロジェクト・オントロジー](ontology/project.yaml)
- [共通因果・証拠オントロジー](https://github.com/KAFKA2306/know/blob/main/ontology/causal-evidence-core.yaml)

## 主な機能

- GitHub ActionsとPagesによるサーバーレス運用
- arXivカテゴリを指定した公開レコード取得
- 設定可能なLLMによる日本語要約
- 重複検査と失敗時の公開抑止
- JSONL、Markdown、静的ページの生成
- キーワード・著者フィルタをブラウザの`localStorage`へ保存

## GitHub Actions設定

`Settings > Secrets and variables > Actions`で設定します。

### Secrets

- `OPENAI_API_KEY`: 利用するOpenAI互換APIのキー
- `OPENAI_BASE_URL`: 利用先が既定値と異なる場合
- `ACCESS_PASSWORD`: 任意のサイト保護用パスワード

### Variables

- `CATEGORIES`: 例 `cs.AI, cs.CL`
- `LANGUAGE`: 既定 `Japanese`
- `MODEL_NAME`: 使用するモデル名
- `MIN_INTERVAL_SECONDS`: LLM呼出しの最小間隔
- `MAX_PAPERS`: 1回に取得する上限
- `SORT_BY`: `relevance`、`submitted_date`、`last_updated_date`など実装が受け付ける値
- `SORT_ORDER`: `desc` または `asc`
- `EMAIL` / `NAME`: CIコミット用Git識別情報

ワークフローは、取得、重複検査、要約、Markdown変換、成果物生成、Pagesデプロイを順に実行します。新規レコードがない場合や処理エラーの場合は、後続の生成・公開をスキップします。

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

`.env`、APIキー、パスワードはコミットしません。

## 設定変更時の検証

1. 同じ設定でローカル取得を実行する。
2. JSONLにarXiv ID、版、日付、出典URLが保持されていることを確認する。
3. 重複検査の終了状態を確認する。
4. AI要約が原文フィールドと別に保存されていることを確認する。
5. 生成Markdownから原論文へ到達できることを確認する。
6. Actions実行後、公開ページと生成コミットを照合する。

## 公開上の境界

- AI要約は原論文の代替ではありません。
- 査読済みであること、再現性、技術的妥当性を自動的に保証しません。
- 科学的評価を追加する場合は、その評価のモデル、手順、根拠、限界を別の主張として記録します。
- 原論文の利用条件とarXivの規約を確認し、必要以上の本文複製を行いません。