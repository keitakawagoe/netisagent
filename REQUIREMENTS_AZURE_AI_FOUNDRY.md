# Azure AI Foundry連携 - 要件定義書

**作成日**: 2025-10-19
**ブランチ**: feature/azure-ai-foundry-integration

---

## 🎯 プロジェクト概要

**目標**: Azure AI Foundry のエージェントプレイグラウンドから、OpenAPI経由でNETIS検索機能を呼び出せるようにする

**現状**:
- ✅ NETISエージェント（Streamlit）が稼働中
- ✅ Azure Functions App (`func-api-emm626t4gwnom`) が South India に存在
- ✅ Azure AI Foundry プロジェクトが稼働中

**移行方針**: Streamlit アプリを完全に廃止し、Azure AI Foundry へ移行

---

## 📋 合意事項

### A. 基本方針
✅ **呼び出し方式**: システムプロンプトで指定し、エージェントが自動的にNETIS検索を使用
✅ **Streamlit**: 完全に移行（廃止）

### B. 技術スタック
✅ **Azure Functions App**: 既存の `func-api-emm626t4gwnom` (South India) を使用
✅ **Pythonランタイム**: Python 3.11（Azure Functionsの推奨バージョン）
✅ **OpenAPI生成**: 手動作成（シンプルなJSON定義）
✅ **認証**: API Key 認証（推奨）

### C. 機能範囲
✅ **公開API**: 検索、チャット、フォローアップを統合したAPI
✅ **システムプロンプト**: エージェントの動作をプロンプトで制御

---

## 🔍 技術調査結果

### 1. Azure AI Foundry Agent Playground の仕組み

#### OpenAPI アクション登録手順
1. **エージェント画面**で対象エージェントを選択
2. **Setup ペイン**で「Action」→「Add」→「OpenAPI 3.0 specified tool」を選択
3. **ツール名**と**説明**を入力（説明は重要：モデルがいつ使うかを判断）
4. **OpenAPI仕様**を貼り付け（JSON形式）
5. **認証方式**を選択（API Key / Managed Identity / Anonymous）

#### システムプロンプトの役割
```
例:
「あなたはNETIS技術検索の専門家です。
ユーザーが建設技術について質問したら、必ず netis_search ツールを使って検索してください。
検索結果は分かりやすく整理して提示し、必要に応じてフォローアップ質問を促してください。」
```

→ **プロンプトでエージェントの振る舞いを制御**

---

### 2. OpenAPI スキーマの要件

#### 必須要素
- ✅ **OpenAPI 3.0** 形式
- ✅ **operationId**: 各関数に必須（英数字と`_`、`-`のみ）
- ✅ **description**: モデルが関数を選ぶ判断材料
- ✅ **parameters**: 詳細なスキーマ定義
- ✅ **responses**: 応答形式の定義

#### 認証方式
Azure AI Foundry がサポートする3つの方式：
1. **Anonymous**: 認証なし（非推奨）
2. **API Key**: 推奨（Custom Connection で設定）
3. **Managed Identity**: Microsoft Entra ID 認証

**推奨**: API Key 認証
- 理由: セットアップが簡単、Azure AI Foundry で標準サポート

---

## 🏗️ システムアーキテクチャ

```
┌─────────────────────────────────────┐
│  Azure AI Foundry                   │
│  Agent Playground                   │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  システムプロンプト           │  │
│  │  「NETIS検索の専門家...」    │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  OpenAPI Action:             │  │
│  │  netis_search               │  │
│  └──────────────────────────────┘  │
└───────────┬─────────────────────────┘
            │ HTTPS + API Key
            ▼
┌─────────────────────────────────────┐
│  Azure Functions App                │
│  (func-api-emm626t4gwnom)          │
│  South India / Python 3.11          │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  /api/search                 │  │
│  │  - NETIS技術検索             │  │
│  │  - ハイブリッド検索           │  │
│  │  - フォローアップ対応         │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  OpenAPI 3.0 仕様            │  │
│  │  (手動作成JSON)              │  │
│  └──────────────────────────────┘  │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  Azure AI Search                    │
│  (netis-index)                     │
│  415ドキュメント                    │
└─────────────────────────────────────┘
```

---

## 📝 実装する API エンドポイント

### `/api/search` - NETIS技術検索

**機能**: 自然言語クエリでNETIS技術を検索

**OpenAPI 定義**:
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "NETIS Search API",
    "version": "1.0.0",
    "description": "NETIS建設技術検索API"
  },
  "servers": [
    {
      "url": "https://func-api-emm626t4gwnom.azurewebsites.net"
    }
  ],
  "paths": {
    "/api/search": {
      "get": {
        "operationId": "search_netis",
        "summary": "NETIS技術を検索",
        "description": "建設技術情報データベース（NETIS）から、自然言語クエリで技術を検索します。ハイブリッド検索（キーワード + ベクトル）を使用。",
        "parameters": [
          {
            "name": "query",
            "in": "query",
            "required": true,
            "schema": {
              "type": "string"
            },
            "description": "検索クエリ（例: トンネルの漏水対策）"
          },
          {
            "name": "top",
            "in": "query",
            "required": false,
            "schema": {
              "type": "integer",
              "default": 10
            },
            "description": "取得件数（最大20）"
          },
          {
            "name": "category",
            "in": "query",
            "required": false,
            "schema": {
              "type": "string"
            },
            "description": "工事分類フィルタ（例: トンネル工事）"
          }
        ],
        "responses": {
          "200": {
            "description": "検索結果",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "results": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "tech_name": {
                            "type": "string"
                          },
                          "abstract": {
                            "type": "string"
                          },
                          "url": {
                            "type": "string"
                          },
                          "overview": {
                            "type": "string"
                          },
                          "innovation": {
                            "type": "string"
                          },
                          "score": {
                            "type": "number"
                          }
                        }
                      }
                    },
                    "count": {
                      "type": "integer"
                    },
                    "query": {
                      "type": "string"
                    }
                  }
                }
              }
            }
          }
        },
        "security": [
          {
            "apiKey": []
          }
        ]
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

**処理フロー**:
1. クエリ受信
2. Azure OpenAI でエンベディング生成
3. Azure AI Search でハイブリッド検索
4. 結果を JSON で返却

---

## ⚙️ システムプロンプト（提案）

```
# NETIS建設技術検索エージェント

あなたは国土交通省のNETIS（新技術情報提供システム）に登録された建設技術の検索を専門とするエージェントです。

## 役割
- ユーザーが建設技術について質問したら、必ず `search_netis` ツールを使用して検索を実行してください
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

## 🔐 認証設定

### 推奨: API Key 認証

#### Azure Functions 側
- HTTPトリガーで `authLevel: "function"` を設定
- Function App の API Key を使用

#### Azure AI Foundry 側
1. **Connected resources** で Custom Connection を作成
2. 接続名: `netis-api-connection`
3. 認証の種類: `API key`
4. Header name: `x-functions-key`
5. Key value: Function App の API Key

---

## 📦 必要なPythonライブラリ

```txt
azure-functions
azure-search-documents
openai
python-dotenv
```

---

## 🚀 デプロイフロー

### 1. ローカル開発
```bash
cd function_app
func start
```

### 2. Function App へデプロイ
```bash
func azure functionapp publish func-api-emm626t4gwnom
```

### 3. Azure AI Foundry 設定
1. エージェント画面で「Action」→「Add」→「OpenAPI 3.0 specified tool」
2. OpenAPI JSON を貼り付け
3. API Key 認証を設定（Custom Connection）
4. システムプロンプトを入力

### 4. テスト
- Agent Playground でクエリ実行
- 検索結果の確認
- フォローアップ質問のテスト

---

## 📂 ファイル構成

```
netisagent/
├── function_app/                  # Azure Functions プロジェクト
│   ├── function_app.py           # メイン関数
│   ├── requirements.txt          # 依存ライブラリ
│   ├── host.json                 # Functions 設定
│   ├── .env.template             # 環境変数テンプレート
│   └── openapi.json              # OpenAPI 3.0 仕様
├── src/                          # 既存のソースコード（再利用）
│   ├── search_agent.py
│   ├── embedding_generator.py
│   └── ...
└── REQUIREMENTS_AZURE_AI_FOUNDRY.md  # この要件定義書
```

---

## ✅ 承認済み確認事項

1. **Pythonランタイム**: Python 3.11 ✅
2. **認証**: API Key 認証 ✅
3. **API 名**: `/api/search` ✅
4. **システムプロンプト**: 上記の提案内容 ✅
5. **既存コードの再利用**: `src/search_agent.py` のコードを移植 ✅

---

**承認日**: 2025-10-19
**承認者**: ユーザー（OK確認済み）
