# Azure AI Foundry 連携手順

## 概要
このドキュメントでは、デプロイ済みのNETIS Search APIをAzure AI Foundry Agent Playgroundで利用する手順を説明します。

---

## 前提条件

以下の情報が必要です：

- **Function App名**: `netis-search-api`
- **API URL**: `https://netis-search-api.azurewebsites.net/api/search`
- **API Key**: `<YOUR_FUNCTION_APP_KEY>` (Azure Portalで取得)
- **OpenAPI定義**: `function_app/openapi.json`

---

## 手順

### 1. Azure AI Foundryポータルにアクセス

1. ブラウザで以下のURLを開く：
   ```
   https://ai.azure.com/
   ```

2. Azureアカウントでサインイン

3. 既存のプロジェクトを選択（または新規作成）

---

### 2. Custom API Connectionを作成

1. 左メニューから **「Settings」** または **「設定」** を選択

2. **「Connections」** タブを開く

3. **「+ New connection」** をクリック

4. 接続タイプから **「Custom Keys」** を選択

5. 以下の情報を入力：
   - **Connection name**: `netis-search-api-connection`
   - **Authentication type**: `API Key`
   - **Key name**: `x-functions-key`
   - **Key value**: `<YOUR_FUNCTION_APP_KEY>`

6. **「Create」** をクリック

---

### 3. Agent Playgroundでツールを追加

1. 左メニューから **「Playgrounds」** → **「Agent」** を選択

2. 画面上部の **「Tools」** セクションで **「+ Add tool」** をクリック

3. **「OpenAPI」** を選択

4. 以下の情報を入力：
   - **Tool name**: `NETIS Search`
   - **OpenAPI specification**: 以下の方法で指定
     - **Method A**: `openapi.json` ファイルをアップロード
     - **Method B**: 以下のURLを入力（GitHub等にホストする場合）
       ```
       https://raw.githubusercontent.com/<your-repo>/openapi.json
       ```
     - **Method C**: JSON内容を直接貼り付け

5. **Connection** で `netis-search-api-connection` を選択

6. **「Add」** をクリック

---

### 4. 動作テスト

Agent Playgroundで以下のような自然言語クエリを試してください：

#### テストクエリ例：

```
トンネルの漏水対策に使える技術を3つ教えてください
```

```
環境負荷が少ない道路工事の技術を探しています
```

```
橋梁工事で使える新しい技術はありますか？
```

#### 期待される動作：

1. Agentが自動的にNETIS Search APIを呼び出す
2. 検索結果から関連技術を抽出
3. 自然言語で技術の概要を説明
4. 必要に応じてNETISのURLを提供

---

## トラブルシューティング

### API Keyエラーが発生する場合

1. Azure Portalで Function App `netis-search-api` を開く
2. 左メニュー → **「関数」** → `search_netis` → **「関数キー」**
3. `default` キーの値をコピーして再設定

### 検索結果が返ってこない場合

1. Azure Portalで Function App `netis-search-api` を開く
2. 左メニュー → **「ログストリーム」** でエラーログを確認
3. 環境変数が正しく設定されているか確認：
   - `AZURE_SEARCH_ENDPOINT`
   - `AZURE_SEARCH_API_KEY`
   - `AZURE_SEARCH_INDEX_NAME`
   - `AZURE_OPENAI_ENDPOINT`
   - `AZURE_OPENAI_API_KEY`
   - `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`

### OpenAPIスキーマエラーが発生する場合

`openapi.json` のサーバーURLが正しいか確認：
```json
"servers": [
  {
    "url": "https://netis-search-api.azurewebsites.net"
  }
]
```

---

## API仕様

### エンドポイント
```
GET https://netis-search-api.azurewebsites.net/api/search
```

### クエリパラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|----------|-----|------|----------|------|
| `query` | string | ✅ | - | 検索クエリ（例: トンネルの漏水対策） |
| `top` | integer | ❌ | 10 | 取得件数（1-20） |
| `category` | string | ❌ | - | 工事分類フィルタ |

### ヘッダー

```
x-functions-key: <YOUR_FUNCTION_APP_KEY>
```

### レスポンス例

```json
{
  "query": "トンネル",
  "count": 2,
  "results": [
    {
      "id": "netis_0043",
      "tech_name": "LED情報パネル",
      "abstract": "道路の維持修繕工事での情報表示技術...",
      "url": "https://www.netis.mlit.go.jp/netis/pubsearch/details?regNo=...",
      "category1": "道路維持修繕工",
      "score": 0.0167
    }
  ]
}
```

---

## 参考リンク

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [Azure Functions Documentation](https://learn.microsoft.com/azure/azure-functions/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [NETIS公式サイト](https://www.netis.mlit.go.jp/)
