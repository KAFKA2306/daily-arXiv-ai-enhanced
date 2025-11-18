# 🚀 daily-arXiv-ai-enhanced

> [!CAUTION]
> 学術データに検閲や配信制限が課されている地域では、本コードの実行やデプロイに細心の注意を払い、関連する法規・ポリシーを必ず確認してください。
>
> [!CAUTION]
> このリポジトリを派生・再配布する場合は、中国本土からアクセス可能な入り口を削除し、原論文およびAI生成物の内容審査義務を履行してください。未対応のまま公開した場合に生じる法的責任は、派生者・利用者自身に帰属します。

本ツールは、arXiv論文の自動クロールとAI要約を組み合わせ、最新研究をストレスなく追跡できるよう再設計したソリューションです。

## ✨ 主な特徴

🎯 **ゼロインフラ運用**
- GitHub Actions と Pages だけで完結し、サーバー不要
- 無料枠でそのまま運用可能

🤖 **AIによる要約**
- DeepSeek を使った毎日の論文クロール & 要約
- 1日あたり約0.2元（人民元）と低コスト

💫 **快適な閲覧体験**
- 興味分野に応じた論文の自動ハイライト
- PC/モバイル両対応のレスポンシブUI
- ローカルストレージに嗜好を保存しプライバシーを確保
- 日付レンジを柔軟にフィルタリング

👉 **[今すぐ試す](https://dw-dengwei.github.io/daily-arXiv-ai-enhanced/)** — インストール不要で即利用できます。

https://github.com/user-attachments/assets/b25712a4-fb8d-484f-863d-e8da6922f9d7



# 使い方
このリポジトリは **cs.CV, cs.GR, cs.CL, cs.AI** の論文を毎日収集し、**DeepSeek** で **中国語** に要約します。
他カテゴリ・他言語・他LLMを使いたい場合は下記手順に従ってください。セットアップ無しで利用したい場合は https://dw-dengwei.github.io/daily-arXiv-ai-enhanced/ にアクセスしてください。気に入ったらスターをお願いします。

**セットアップ手順**
1. リポジトリをフォークし、[buy-me-a-coffee](./buy-me-a-coffee/README.md) から作者向けリンクを削除します。
2. `自分のリポジトリ -> Settings -> Secrets and variables -> Actions` に移動します。
3. **Secrets**（暗号化される機密情報）タブを開きます。
4. `OPENAI_API_KEY` と `OPENAI_BASE_URL` の2つのリポジトリシークレットを作成し、対応する値を設定します。
5. **任意**: `secrets.ACCESS_PASSWORD` にパスワードを設定すると、公開ページへのアクセスを制限できます（参考: https://github.com/dw-dengwei/daily-arXiv-ai-enhanced/pull/64）。
6. **Variables**（平文で参照できる非機密設定）タブに移動します。
7. 以下のリポジトリ変数を作成します。
   1. `CATEGORIES`: 例 `"cs.CL, cs.CV"`
   2. `LANGUAGE`: 例 `"Chinese"` `"English"`
   3. `MODEL_NAME`: 例 `"deepseek-chat"`
   4. `EMAIL`: GitHub への push で使うメール
   5. `NAME`: GitHub への push で使う名前
8. `自分のリポジトリ -> Actions -> arXiv-daily-ai-enhanced` を開きます。
9. **Run workflow** を手動実行して動作を確認できます（処理時間は約1時間）。既定では毎日自動実行されます。スケジュールを変更したい場合は `.github/workflows/run.yml` を編集します。
10. GitHub Pages を設定します。`Settings -> Pages` で `Build and deployment: Deploy from a branch`、`Branch: main / (root)` を選択し保存します。数分後に https://<username>.github.io/daily-arXiv-ai-enhanced/ を確認してください。詳細は [このIssue](https://github.com/dw-dengwei/daily-arXiv-ai-enhanced/issues/14) を参照してください。

# 計画
https://github.com/users/dw-dengwei/projects/3 を参照してください。

# コントリビューター
コード提供・不具合報告・アイデア共有をしてくださった皆さまに感謝します！
<table>
  <tbody>
    <tr>
      <td align="center" valign="top">
        <a href="https://github.com/JianGuanTHU"><img src="https://avatars.githubusercontent.com/u/44895708?v=4" width="100px;" alt="JianGuanTHU"/><br /><sub><b>JianGuanTHU</b></sub></a><br />
      </td>
      <td align="center" valign="top">
        <a href="https://github.com/Chi-hong22"><img src="https://avatars.githubusercontent.com/u/75403952?v=4" width="100px;" alt="Chi-hong22"/><br /><sub><b>Chi-hong22</b></sub></a><br />
      </td>
      <td align="center" valign="top">
        <a href="https://github.com/chaozg"><img src="https://avatars.githubusercontent.com/u/69794131?v=4" width="100px;" alt="chaozg"/><br /><sub><b>chaozg</b></sub></a><br />
      </td>
      <td align="center" valign="top">
        <a href="https://github.com/quantum-ctrl"><img src="https://avatars.githubusercontent.com/u/16505311?v=4" width="100px;" alt="quantum-ctrl"/><br /><sub><b>quantum-ctrl</b></sub></a><br />
      </td>
      <td align="center" valign="top">
        <a href="https://github.com/Zhao2z"><img src="https://avatars.githubusercontent.com/u/141019403?v=4" width="100px;" alt="Zhao2z"/><br /><sub><b>Zhao2z</b></sub></a><br />
      </td>
      <td align="center" valign="top">
        <a href="https://github.com/eclipse0922"><img src="https://avatars.githubusercontent.com/u/6214316?v=4" width="100px;" alt="eclipse0922"/><br /><sub><b>eclipse0922</b></sub></a><br />
      </td>
    </tr>


  </tbody>
  <tbody>
   <tr>
      <td align="center" valign="top">
        <a href="https://github.com/xuemian168"><img src="https://avatars.githubusercontent.com/u/38741078?v=4" width="100px;" alt="xuemian168"/><br /><sub><b>xuemian168</b></sub></a><br />
      </td>
   </tr>
  </tbody>
</table>

# 謝辞
応援・紹介してくださったコミュニティ／メディアに感謝します！
<table>
  <tbody>
    <tr>
      <td align="center" valign="top">
        <a href="https://x.com/GitHub_Daily/status/1930610556731318781"><img src="https://pbs.twimg.com/profile_images/1660876795347111937/EIo6fIr4_400x400.jpg" width="100px;" alt="Github_Daily"/><br /><sub><b>Github_Daily</b></sub></a><br />
      </td>
      <td align="center" valign="top">
        <a href="https://x.com/aigclink/status/1930897858963853746"><img src="https://pbs.twimg.com/profile_images/1729450995850027008/gllXr6bh_400x400.jpg" width="100px;" alt="AIGCLINK"/><br /><sub><b>AIGCLINK</b></sub></a><br />
      </td>
      <td align="center" valign="top">
        <a href="https://www.ruanyifeng.com/blog/2025/06/weekly-issue-353.html"><img src="https://avatars.githubusercontent.com/u/905434" width="100px;" alt="阮一峰的网络日志"/><br /><sub><b>阮一峰的网络日志 <br> 科技爱好者周刊 <br> （第 353 期）</b></sub></a><br />
      </td>
      <td align="center" valign="top">
        <a href="https://hellogithub.com/periodical/volume/111"><img src="https://github.com/user-attachments/assets/eff6b6dd-0323-40c4-9db6-444a51bbc80a" width="100px;" alt="《HelloGitHub》第 111 期"/><br /><sub><b>《HelloGitHub》<br> 月刊第 111 期</b></sub></a><br />
      </td>
    </tr>
  </tbody>
</table>

# スター履歴

[![Stargazers over time](https://starchart.cc/dw-dengwei/daily-arXiv-ai-enhanced.svg?variant=adaptive)](https://starchart.cc/dw-dengwei/daily-arXiv-ai-enhanced)

# コーヒーの差し入れ
[こちら](./buy-me-a-coffee/README.md)
