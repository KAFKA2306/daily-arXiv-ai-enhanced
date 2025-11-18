# .github/workflows ディレクトリ

CI/CD を定義するYAMLファイルを置きます。現在は `run.yml` のみで、クロール→AI処理→Pages更新の一連を担います。

## コマンド例
- `gh workflow run run.yml --ref main` で手動トリガーできます。
- 実行ログを追う場合は `gh run watch` を利用してください。

## メモ
- `schedule` と `workflow_dispatch` の両方を有効にしており、必要に応じてCronを調整します。
- 依存シークレットの名称を変更したら `run.yml` も必ず更新してください。
