# css ディレクトリ

Web UI の見た目を決めるスタイルシート群です。`index.html`, `settings.html`, `statistic.html` から直接読み込まれます。

## 役割
- `styles.css`: トップページの基本レイアウト。
- `settings.css`: 設定UIのカードやフォーム装飾。
- `statistic.css`: 統計画面のチャート用スタイル。
- `screenshot-placeholder.svg`: 未取得時の代替イメージ。

## コマンド例
- Prettier が使える環境では `npx prettier --write css/*.css` で整形できます。
- ローカル確認は `python -m http.server 4173` を実行して `http://localhost:4173/index.html` を開くのが手軽です。

## メモ
- CSS変数やメディアクエリは `styles.css` に集約しておくと保守しやすくなります。
- 色やフォントを変えたらスクリーンショットも更新してください。
