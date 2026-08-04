# 研究プロファイル

特定分野の論文収集条件、検索式、基準文献、品質規則を保存する場所です。
通常の日次取得とは分離し、テーマごとに再現可能な条件で実行します。

## 光学多層薄膜の構造逆設計

- 設定: [`optical_multilayer_thin_film_ja.yaml`](./optical_multilayer_thin_film_ja.yaml)
- 実行: [`run_optical_multilayer_thin_film_ja.sh`](./run_optical_multilayer_thin_film_ja.sh)

対象範囲は次のとおりです。

- 古典的最適化と転送行列法
- JAXなどを使った微分可能な多層光学計算
- 直列型ニューラルネットワーク
- 拡散モデル、フローマッチング、自己回帰生成
- エリプソメトリ逆解析
- 反射率・透過率からの膜厚、屈折率、消衰係数推定
- 工程内反射率計測と時系列モデル

## 実行方法

リポジトリのルートで実行します。

```bash
bash research_profiles/run_optical_multilayer_thin_film_ja.sh
```

取得件数などは環境変数で上書きできます。

```bash
MAX_PAPERS=20 \
SORT_BY=submitted_date \
bash research_profiles/run_optical_multilayer_thin_film_ja.sh
```

検索式を一時的に変更する場合は、`ARXIV_QUERY`を明示します。

```bash
ARXIV_QUERY='all:"multilayer thin film" AND all:"inverse design"' \
bash research_profiles/run_optical_multilayer_thin_film_ja.sh
```

## 品質規則

- arXiv掲載と査読済みを同一視しません。
- arXiv ID、版、著者、日付、原文URLを保存します。
- 改題された同一arXiv論文は、別論文ではなく版履歴として管理します。
- DOIと掲載誌情報は出版社または学会の公式情報で照合します。
- AI要約と原論文の記述を分離します。
- GitHub実装は、論文とは別にライセンス、更新状態、再現手順を記録します。
