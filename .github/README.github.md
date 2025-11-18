# .github ディレクトリ

GitHub特有のメタデータとワークフロー定義を保持します。現状は `workflows/run.yml` が中心です。

## 役割
- GitHub ActionsでarXivのクロール、AI要約、Pagesの更新を自動化します。

## コマンド例
- GitHub CLIがある場合は `gh workflow view run.yml` でステータスを確認できます。

## メモ
- Secrets/Variablesのセットアップ手順はリポジトリトップのREADMEにまとまっています。
- `CODEOWNERS` などの追加設定が必要になったらこの配下に配置します。
