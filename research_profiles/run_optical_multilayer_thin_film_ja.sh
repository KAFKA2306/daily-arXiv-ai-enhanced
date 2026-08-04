#!/usr/bin/env bash
set -euo pipefail

# 光学多層薄膜の逆設計に限定して、既存の日次処理を実行する。
export LANGUAGE="${LANGUAGE:-Japanese}"
export CATEGORIES="${CATEGORIES:-physics.optics,physics.comp-ph,cs.LG}"
export ARXIV_QUERY="${ARXIV_QUERY:-(all:\"multilayer thin film\" OR all:\"optical multilayer\" OR all:\"thin-film stack\") AND (all:\"inverse design\" OR all:\"inverse problem\" OR all:ellipsometry OR all:reflectometry OR all:\"transfer matrix\")}"
export SORT_BY="${SORT_BY:-submitted_date}"
export SORT_ORDER="${SORT_ORDER:-desc}"
export MAX_PAPERS="${MAX_PAPERS:-50}"

printf '%s\n' "光学多層薄膜の研究プロファイルで実行します。"
printf 'ARXIV_QUERY=%s\n' "$ARXIV_QUERY"
printf 'CATEGORIES=%s\n' "$CATEGORIES"
printf 'MAX_PAPERS=%s\n' "$MAX_PAPERS"

exec bash run.sh
