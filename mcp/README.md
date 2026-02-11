# MCP (Model Context Protocol) サーバー設定

このディレクトリには、Claude Desktop等で使用するMCP サーバーの設定例が含まれています。

## MCP サーバーとは

Model Context Protocol (MCP) は、LLMアプリケーションが外部ツールやデータソースに安全にアクセスするための標準プロトコルです。MCPサーバーを使うことで、Claude DesktopからGitHub、Web検索、ファイルシステムなどへアクセスできるようになります。

## 設定済みのMCPサーバー

`config.example.json` には以下のMCPサーバーが設定されています:

### 1. **GitHub** (`@modelcontextprotocol/server-github`)

- GitHubリポジトリの閲覧・操作
- イシュー、プルリクエストの管理
- 必要な環境変数: `GITHUB_TOKEN`

### 2. **Brave Search** (`@modelcontextprotocol/server-brave-search`)

- Brave Search APIを使ったWeb検索
- リアルタイムの情報取得
- 必要な環境変数: `BRAVE_API_KEY`

### 3. **Fetch** (`@modelcontextprotocol/server-fetch`)

- WebコンテンツのフェッチとLLM用への変換
- API キー不要

### 4. **Filesystem** (`@modelcontextprotocol/server-filesystem`)

- ローカルファイルシステムへの安全なアクセス
- 読み取り・書き込み権限の設定可能
- 環境変数でアクセス可能なディレクトリを制限

### 5. **Git** (`mcp-server-git`)

- Gitリポジトリの操作
- コミット履歴の閲覧、ブランチ操作など
- Python実装（`uvx`で実行）

## セットアップ手順

### 1. Claude Desktop設定ファイルの場所

Claude DesktopのMCP設定ファイルは以下の場所にあります:

- **Linux**: `~/.config/Claude/claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### 2. 設定ファイルのコピー

```bash
# Linux/macOSの場合
cp mcp/config.example.json ~/.config/Claude/claude_desktop_config.json

# または手動でconfig.example.jsonの内容をコピーして貼り付け
```

### 3. API キーの設定

#### GitHub Personal Access Token (PAT)

1. GitHubにログイン
2. Settings → Developer settings → Personal access tokens → Tokens (classic)
3. "Generate new token (classic)" をクリック
4. スコープで最低限 `repo` を選択（プライベートリポジトリにアクセスする場合）
5. 生成されたトークンをコピー
6. `claude_desktop_config.json` の `GITHUB_TOKEN` に設定

参考: <https://docs.github.com/ja/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens>

#### Brave Search API Key

1. [Brave Search API](https://brave.com/search/api/) にアクセス
2. アカウント作成またはログイン
3. API キーを取得（無料プランあり: 月2,000リクエストまで）
4. `claude_desktop_config.json` の `BRAVE_API_KEY` に設定

### 4. Claude Desktopの再起動

設定を反映するため、Claude Desktopを再起動してください。

## 追加可能なMCPサーバー

必要に応じて、以下のMCPサーバーも追加できます:

### Memory (`@modelcontextprotocol/server-memory`)

Knowledge graphベースの永続メモリシステム

```json
"memory": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-memory"]
}
```

### Sequential Thinking (`@modelcontextprotocol/server-sequentialthinking`)

動的で反射的な問題解決

```json
"sequential-thinking": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-sequentialthinking"]
}
```

### Time (`@modelcontextprotocol/server-time`)

時刻とタイムゾーン変換

```json
"time": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-time"]
}
```

## トラブルシューティング

### MCPサーバーが接続されない

1. Claude Desktopを完全に再起動
2. 設定ファイルのJSONフォーマットが正しいか確認
3. API キーが正しく設定されているか確認
4. エラーログを確認（Claude Desktop → Settings → Developer → Show Logs）

### `npx` または `uvx` コマンドが見つからない

- **npx**: Node.jsをインストール <https://nodejs.org/>
- **uvx**: uvをインストール <https://docs.astral.sh/uv/getting-started/installation/>

```bash
# uvのインストール（Linux/macOS）
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### GitHubサーバーでPermission Denied

- GitHub PATのスコープに `repo` 権限が含まれているか確認
- 組織のリポジトリにアクセスする場合は、PATで組織へのアクセス権限を付与

## 参考リンク

- [Model Context Protocol 公式サイト](https://modelcontextprotocol.io/)
- [MCP Servers リポジトリ](https://github.com/modelcontextprotocol/servers)
- [Claude Desktop MCP ドキュメント](https://docs.anthropic.com/claude/docs/model-context-protocol)
