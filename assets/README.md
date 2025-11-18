# assets ディレクトリ

ロゴ・動画などのバイナリアセットを格納しています。`file-list.txt` で同梱物を追跡します。

## 役割
- `logo*.png` はフロントエンドのブランド画像に利用します。
- `video-480p.mp4` はトップページのデモ動画です。

## 運用メモ
- 一覧を更新するときは `ls assets > assets/file-list.txt` を実行してください。
- ffmpeg が導入済みなら `ffmpeg -i assets/video-480p.mp4 -vf scale=1280:-2 assets/video-720p.mp4` で別解像度を生成できます。
- 大きなバイナリを追加する際は `.gitignore` への追記も検討してください。
