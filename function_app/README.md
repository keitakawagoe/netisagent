# NETIS Search Azure Function

Azure AI Foundry Agent Playground から NETIS検索機能を呼び出すための Azure Functions API

---

## 📋 概要

このAzure Functionは、NETIS（新技術情報提供システム）の建設技術データベースを検索するAPIを提供します。
Azure AI Foundry のエージェントプレイグラウンドから OpenAPI 経由で呼び出され、自然言語クエリでハイブリッド検索を実行します。

---

## 🏗️ アーキテクチャ

```
Azure AI Foundry Agent
       ↓ (OpenAPI 3.0)
Azure Functions API (/api/search)
       ↓
Azure AI Search (netis-index)
       ↓
415件の建設技術データ
```

---

## 📁 ファイル構成

```
function_app/
├── function_app.py              # メイン関数
├── requirements.txt             # 依存ライブラリ
├── host.json                    # Functions設定
├── openapi.json                 # OpenAPI 3.0 仕様
├── local.settings.json.template # 環境変数テンプレート
├── .gitignore                   # Git除外設定
├── DEPLOY.md                    # デプロイ手順書
└── README.md                    # このファイル
```

---

## 🚀 クイックスタート

### 1. ローカル開発環境のセットアップ

```bash
# ディレクトリに移動
cd function_app

# 環境変数ファイルを作成
cp local.settings.json.template local.settings.json

# local.settings.json を編集して Azure の接続情報を設定
```

### 2. ローカルで実行

```bash
# Azure Functions Core Tools でローカル実行
func start
```

### 3. テスト

```bash
# 別のターミナルで
curl "http://localhost:7071/api/search?query=トンネルの漏水対策"
```

---

## 🔌 API エンドポイント

### `GET /api/search`

**説明**: NETIS技術を検索

**パラメータ**:
| 名前 | 型 | 必須 | 説明 | 例 |
|------|-----|------|------|-----|
| `query` | string | ✅ | 検索クエリ | `トンネルの漏水対策` |
| `top` | integer | ❌ | 取得件数（最大20） | `10` |
| `category` | string | ❌ | 工事分類フィルタ | `トンネル工事` |

**レスポンス例**:
```json
{
  "query": "トンネルの漏水対策",
  "count": 5,
  "results": [
    {
      "id": "CB-140015-A",
      "tech_name": "トンネル漏水対策工法",
      "abstract": "トンネル内の漏水を効果的に防ぐ技術...",
      "url": "https://www.netis.mlit.go.jp/...",
      "overview": "従来工法と比較して...",
      "innovation": "新規性としては...",
      "score": 15.2
    }
  ]
}
```

---

## 🔐 認証

Azure Functions の API Key 認証を使用：

**Header**:
```
x-functions-key: YOUR_FUNCTION_KEY
```

---

## 📦 依存ライブラリ

```txt
azure-functions
azure-search-documents
openai
python-dotenv
```

---

## 🌐 デプロイ

詳細は [DEPLOY.md](./DEPLOY.md) を参照してください。

### デプロイコマンド

```bash
func azure functionapp publish func-api-emm626t4gwnom
```

---

## 🔗 関連リンク

- [Azure Functions ドキュメント](https://learn.microsoft.com/ja-jp/azure/azure-functions/)
- [Azure AI Foundry Agent Service](https://learn.microsoft.com/ja-jp/azure/ai-foundry/agents/)
- [OpenAPI 3.0 仕様](https://swagger.io/specification/)

---

## 📝 開発メモ

### 既存コードの再利用

このFunctionは、既存の `src/search_agent.py` と `src/embedding_generator.py` を再利用しています。

### ハイブリッド検索

- **キーワード検索**: 完全一致・部分一致
- **ベクトル検索**: 意味的類似性（1536次元エンベディング）
- **統合**: Azure AI Search が自動的に両方のスコアを組み合わせ

---

**更新日**: 2025-10-19
