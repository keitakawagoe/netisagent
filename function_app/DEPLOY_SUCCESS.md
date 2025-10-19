# NETIS Search API - Azure AI Foundry 連携成功ガイド

## 概要

このドキュメントでは、NETIS Search APIをAzure Function Appにデプロイし、Azure AI Foundry Agent Playgroundで使用可能にするまでの**実際に成功した手順**を記録します。

---

## 🎯 完成した環境

### Function App情報
- **名前**: `netis-search-api`
- **URL**: `https://netis-search-api.azurewebsites.net/api/search`
- **API Key**: `<YOUR_FUNCTION_APP_KEY>` (Azure Portalで取得)
- **プラン**: 従量課金（Consumption）
- **リージョン**: Japan East
- **ランタイム**: Python 3.11

### API機能
- ハイブリッド検索（キーワード + ベクトル検索）
- Azure AI Search統合
- Azure OpenAI Embeddings統合
- 415件のNETIS建設技術データベース

---

## 📋 前提条件

以下のリソースが必要です：

- Azure Subscription
- Azure AI Search（インデックス: `netis-index`）
- Azure OpenAI（Embedding: `text-embedding-3-small`）
- Azure CLI（ローカル環境）
- Azure Functions Core Tools

---

## 🚀 デプロイ手順

### Step 1: Function Appの作成

```bash
az functionapp create \
  --resource-group rg-hikariagenttrial \
  --consumption-plan-location japaneast \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name netis-search-api \
  --storage-account kawagoetest \
  --os-type Linux
```

**重要ポイント**:
- `--os-type Linux` は必須（Python対応）
- `--consumption-plan-location` で従量課金プランを指定

---

### Step 2: 環境変数の設定

```bash
az functionapp config appsettings set \
  --name netis-search-api \
  --resource-group <YOUR_RESOURCE_GROUP> \
  --settings \
    AZURE_SEARCH_ENDPOINT="<YOUR_AZURE_SEARCH_ENDPOINT>" \
    AZURE_SEARCH_API_KEY="<YOUR_AZURE_SEARCH_KEY>" \
    AZURE_SEARCH_INDEX_NAME="netis-index" \
    AZURE_OPENAI_ENDPOINT="<YOUR_AZURE_OPENAI_ENDPOINT>" \
    AZURE_OPENAI_API_KEY="<YOUR_AZURE_OPENAI_KEY>" \
    AZURE_OPENAI_DEPLOYMENT_NAME="<YOUR_GPT_DEPLOYMENT>" \
    AZURE_OPENAI_API_VERSION="2024-02-15-preview" \
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-3-small"
```

---

### Step 3: コードのデプロイ

#### 3-1. ベクトルフィールド名の修正

`function_app.py` の122行目を修正：

```python
# 修正前
fields="descriptionVector"

# 修正後
fields="searchable_text_vector"
```

#### 3-2. デプロイ実行

```bash
cd function_app
func azure functionapp publish netis-search-api --python
```

**成功の確認**:
```
Functions in netis-search-api:
    search_netis - [httpTrigger]
        Invoke url: https://netis-search-api.azurewebsites.net/api/search
```

---

### Step 4: API動作確認

```bash
curl -X GET 'https://netis-search-api.azurewebsites.net/api/search?query=トンネル&top=2' \
  -H 'x-functions-key: <YOUR_FUNCTION_APP_KEY>'
```

**期待される結果**:
```json
{
  "query": "トンネル",
  "count": 2,
  "results": [...]
}
```

---

## 🔗 Azure AI Foundry 連携手順

### Step 1: Playgroundを開く

1. https://ai.azure.com/ にアクセス
2. プロジェクトを選択
3. 左メニューから **「Playgrounds」** → **「Chat」** または **「Agents」** を選択

---

### Step 2: カスタムツールを作成

1. 画面右側の **「Tools」** セクションで **「+ Add tool」** をクリック
2. **「Custom tool」** または **「カスタムツール」** を選択

#### ツールの詳細（Step 1/3）

- **名前**: `NETIS_kawagoe`（任意の名前）
- **説明**:
  ```
  NETIS（新技術情報提供システム）から建設技術を検索します。ハイブリッド検索（キーワード + ベクトル）を使用して、意味的に類似した技術も検出します。トンネル工事、道路工事、橋梁工事など、様々な工事分類で技術を検索できます。
  ```

**「次へ」** をクリック

---

### Step 3: スキーマの定義（Step 2/3）

#### 認証方法の設定

1. **認証方法**ドロップダウンを **「API Key」** に変更

2. 以下を入力：
   - **Header name**: `x-functions-key`
   - **API Key**: `<YOUR_FUNCTION_APP_KEY>` (Azure Portalで取得したキー)

#### OpenAPIスキーマの貼り付け

テキストエリアに `openapi.json` の内容を全て貼り付け：

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "NETIS Search API",
    "version": "1.0.0",
    "description": "NETIS建設技術検索API - Azure AI Foundry Agent用"
  },
  "servers": [
    {
      "url": "https://netis-search-api.azurewebsites.net"
    }
  ],
  "paths": {
    "/api/search": {
      "get": {
        "operationId": "search_netis",
        "summary": "NETIS技術を検索",
        ...
      }
    }
  },
  "components": {
    "securitySchemes": {
      "apiKey": {
        "type": "apiKey",
        "in": "header",
        "name": "x-functions-key"
      }
    }
  }
}
```

**「次へ」** をクリック

---

### Step 4: レビューと作成（Step 3/3）

1. 設定内容を確認
2. **「ツールの作成」** をクリック

---

## ✅ 動作テスト

Playgroundのチャット画面で以下のクエリを試してください：

### テストクエリ例

```
トンネルの漏水対策技術を教えて
```

```
環境負荷が少ない道路工事の技術を3つ探してください
```

```
橋梁工事で使える最新技術は何がありますか？
```

### 期待される動作

1. Agentが自動的にNETIS検索APIを呼び出す
2. 検索結果から関連技術を抽出
3. 自然言語で技術の概要を説明
4. NETIS URLを提供

---

## 🔧 トラブルシューティング

### Error: HTTP 401 Unauthorized

**原因**: API Keyが正しく設定されていない

**解決策**:
1. ツール設定で認証情報を再確認
2. ヘッダー名が `x-functions-key` であることを確認
3. API Keyの値にスペースや改行が含まれていないか確認

---

### Error: Unknown field 'descriptionVector'

**原因**: Azure AI Searchのベクトルフィールド名が間違っている

**解決策**:
`function_app.py` のベクトルフィールド名を `searchable_text_vector` に修正して再デプロイ

```python
vector_query = VectorizedQuery(
    vector=query_vector,
    k_nearest_neighbors=top,
    fields="searchable_text_vector"  # ← 正しいフィールド名
)
```

---

### 検索結果が返ってこない

**原因**: 環境変数が正しく設定されていない

**確認方法**:
```bash
az functionapp config appsettings list \
  --name netis-search-api \
  --resource-group rg-hikariagenttrial
```

---

## 📊 API仕様

### エンドポイント

```
GET https://netis-search-api.azurewebsites.net/api/search
```

### パラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|----------|-----|------|----------|------|
| `query` | string | ✅ | - | 検索クエリ |
| `top` | integer | ❌ | 10 | 取得件数（1-20） |
| `category` | string | ❌ | - | 工事分類フィルタ |

### レスポンス

```json
{
  "query": "検索クエリ",
  "count": 2,
  "results": [
    {
      "id": "netis_0043",
      "tech_name": "技術名",
      "abstract": "概要",
      "url": "https://www.netis.mlit.go.jp/...",
      "category1": "工事分類1",
      "score": 0.0167
    }
  ]
}
```

---

## 🎉 成功のポイント

### 1. Function Appプランの選択
- ❌ **Flex Consumption**: Python v2モデルと互換性なし
- ✅ **Consumption**: Python v2モデルと互換性あり

### 2. 認証方法
- ❌ **Connections経由**: ValidationErrorが発生
- ✅ **カスタムツールで直接設定**: 成功

### 3. ベクトルフィールド名
- ❌ `descriptionVector`: エラー
- ✅ `searchable_text_vector`: 成功

### 4. デプロイ方法
- ✅ Azure CLI + Functions Core Tools
- ✅ 統合版コード（`function_app_standalone.py` → `function_app.py`）

---

## 📁 関連ファイル

- `function_app.py` - メイン関数コード
- `function_app_standalone.py` - 統合版コード（依存関係なし）
- `openapi.json` - OpenAPI 3.0仕様
- `requirements.txt` - Python依存関係
- `AZURE_AI_FOUNDRY_SETUP.md` - 詳細セットアップガイド

---

## 🔗 参考リンク

- [Azure Functions Documentation](https://learn.microsoft.com/azure/azure-functions/)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [NETIS公式サイト](https://www.netis.mlit.go.jp/)

---

## 📝 作成日

2025-10-19

**作成者**: Claude Code
**環境**: Azure Functions (Python 3.11) + Azure AI Foundry
