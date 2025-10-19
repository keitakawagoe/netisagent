# Azure Functions デプロイ手順書

## 📋 前提条件

- Azure CLI がインストールされていること
- Azure Functions Core Tools がインストールされていること
- Python 3.11 がインストールされていること
- Azure サブスクリプションにアクセスできること

---

## 🚀 デプロイ手順

### 1. Azure にログイン

```bash
az login
```

### 2. Function App の環境変数を設定

Azure Portal で `func-api-emm626t4gwnom` を開き、「構成」→「アプリケーション設定」で以下を設定：

| 設定名 | 値 |
|--------|-----|
| `AZURE_SEARCH_ENDPOINT` | `https://agent-ai-searchemm626t4gwnom.search.windows.net` |
| `AZURE_SEARCH_API_KEY` | Azure AI Search の API Key |
| `AZURE_SEARCH_INDEX_NAME` | `netis-index` |
| `AZURE_OPENAI_ENDPOINT` | `https://llm-demo.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI の API Key |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `gpt-4.1` |
| `AZURE_OPENAI_API_VERSION` | `2024-02-15-preview` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | `text-embedding-3-small` |

### 3. Function App にデプロイ

```bash
cd function_app
func azure functionapp publish func-api-emm626t4gwnom
```

### 4. デプロイ確認

```bash
# エンドポイントをテスト
curl "https://func-api-emm626t4gwnom.azurewebsites.net/api/search?query=トンネル&code=YOUR_FUNCTION_KEY"
```

---

## 🔐 API Key の取得

### Function App の API Key を取得

1. Azure Portal で `func-api-emm626t4gwnom` を開く
2. 「関数」→「search」→「関数キー」
3. `default` キーの値をコピー

この API Key は Azure AI Foundry の Custom Connection で使用します。

---

## 🤖 Azure AI Foundry での設定

### 1. Custom Connection の作成

1. Azure AI Foundry Portal を開く
2. **Connected resources** → **新しい接続**
3. 以下を入力：
   - 接続名: `netis-api-connection`
   - 認証の種類: `API key`
   - Header name: `x-functions-key`
   - Key value: Function App の API Key（上記で取得）

### 2. OpenAPI Action の登録

1. **エージェント画面**を開く
2. **Setup ペイン** → **Action** → **Add** → **OpenAPI 3.0 specified tool**
3. 以下を入力：
   - Tool name: `netis_search`
   - Description: `NETIS建設技術データベースを検索します`
4. **OpenAPI specification** に `function_app/openapi.json` の内容を貼り付け
5. **Authentication** で `netis-api-connection` を選択
6. **Save**

### 3. システムプロンプトの設定

エージェントの **Instructions** フィールドに以下を入力：

```
# NETIS建設技術検索エージェント

あなたは国土交通省のNETIS（新技術情報提供システム）に登録された建設技術の検索を専門とするエージェントです。

## 役割
- ユーザーが建設技術について質問したら、必ず `netis_search` ツールを使用して検索を実行してください
- 検索結果は技術名、概要、URLを含めて分かりやすく整理して提示してください
- ユーザーが詳細を知りたい場合や絞り込みたい場合は、追加の検索を実行してください

## 検索のベストプラクティス
1. 初回検索は広めのクエリで実行（例: 「トンネル 対策」）
2. 結果が多すぎる場合は、ユーザーに絞り込み条件を確認
3. 技術の比較を求められたら、複数の技術を並べて特徴を説明
4. 適用条件や留意事項も重要なので、必要に応じて言及

## 応答フォーマット
検索結果は以下の形式で提示してください：

【検索結果: N件】

1. **技術名**
   - 概要: ...
   - 新規性: ...
   - URL: ...

2. **技術名**
   ...

必要に応じて「さらに詳しい情報が必要ですか？」「絞り込みますか？」などのフォローアップ質問を添えてください。
```

---

## ✅ テスト

Agent Playground で以下のクエリをテスト：

1. 「トンネルの漏水対策技術を教えて」
2. 「環境負荷が少ない工法は？」
3. 「道路の舗装に使える技術を探している」

---

## 🐛 トラブルシューティング

### エラー: `ModuleNotFoundError: No module named 'src'`

**原因**: `src` モジュールが Function App にデプロイされていない

**解決策**: プロジェクトルートから `src` フォルダもデプロイする必要があります。

```bash
# function_app ディレクトリで
cd ../
func azure functionapp publish func-api-emm626t4gwnom --publish-local-settings
```

### エラー: `Authentication failed`

**原因**: Function App の API Key が正しく設定されていない

**解決策**:
1. Azure Portal で Function Key を確認
2. Azure AI Foundry の Custom Connection を更新

### 検索結果が返ってこない

**原因**: Azure AI Search の接続情報が正しくない

**解決策**:
1. Function App の「構成」で環境変数を確認
2. `AZURE_SEARCH_ENDPOINT` と `AZURE_SEARCH_API_KEY` が正しいか確認

---

## 📝 メンテナンス

### ログの確認

```bash
# Azure Portal でログストリームを確認
func azure functionapp logstream func-api-emm626t4gwnom
```

### Function App の再起動

```bash
az functionapp restart --name func-api-emm626t4gwnom --resource-group rg-hikariagenttrial
```

---

**更新日**: 2025-10-19
