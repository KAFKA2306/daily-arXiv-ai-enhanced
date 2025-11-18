# js ディレクトリ

フロントエンドのロジックをまとめたプレーンなESモジュール群です。ビルドツールを介さず、ブラウザで直接実行します。

## 役割
- `app.js`: トップページで論文カードを描画。
- `auth.js` / `auth-config.js`: パスワード保護されたページのバリデーション。
- `settings.js`: UI設定フォームの保存/ロード。
- `statistic.js`: 統計ページのチャート描画。

## コマンド例
- Node.js で構文チェック: `node --check js/app.js`
- 素早くリロードする場合は `npm install -g live-server` 後に `live-server --port=4173` を実行します。

## メモ
- fetch先やAPIキーをハードコードしないよう `auth-config.js` を経由します。
- 変更後は主要ブラウザ（Chrome/Firefox/Edge）での表示を確認してください。
