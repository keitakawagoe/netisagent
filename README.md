# NETISエージェント - 建設技術検索システム

NETISデータをAzure AI Searchで検索可能にし、AIチャットで対話的に技術を探せるシステムです。

## 💡 概要

このシステムは、NETIS（新技術情報提供システム）の技術データ（415件）をAzure AI Searchに投入し、建設業従事者がチャットインターフェースを通じて自然な質問で技術を検索・比較・詳細確認できるようにします。

### 主な機能

- **ハイブリッド検索**: セマンティック検索とキーワード検索を組み合わせた高精度な検索
- **AIチャット**: 自然な会話で技術を探索
- **フォローアップ質問**: AIが絞り込みや詳細確認をサポート
- **分類フィルタ**: 工事種別での絞り込みが可能
- **詳細情報表示**: 適用条件、留意事項、新規性などの詳細を確認可能

## 🚀 セットアップ

### 1. 環境準備

```bash
# リポジトリのクローン
git clone <repository-url>
cd netisagent

# 必要なライブラリをインストール
pip install -r requirements.txt
```

### 2. Azure環境設定

`.env.template` をコピーして `.env` を作成し、以下の情報を設定してください：

```bash
cp .env.template .env
```

`.env` ファイルを編集：

```
# Azure AI Search設定
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_API_KEY=your-search-api-key
AZURE_SEARCH_INDEX_NAME=netis-index

# Azure OpenAI設定
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

### 3. データ投入

```bash
# NETISデータをAzure AI Searchに投入
python upload_to_search.py
```

このスクリプトは以下を実行します：
1. Excelファイル(`netisデータ.xlsx`)の読み込み
2. エンベディングの生成
3. インデックスの作成
4. ドキュメントのアップロード

### 4. アプリケーション起動

```bash
# Streamlit Webアプリを起動
streamlit run app.py
```

ブラウザで `http://localhost:8501` を開くとアプリケーションが表示されます。

## 📖 使い方

### 検索例

チャット欄に自然な質問を入力してください：

- 「トンネルの漏水対策技術を教えて」
- 「環境負荷が少ない工法は？」
- 「道路の舗装に使える技術を探している」

### フォローアップ質問

検索結果が表示されたら、さらに詳しく質問できます：

- 「1番目の技術について詳しく教えて」
- 「もっと絞り込みたい」
- 「1番と3番を比較して」

### 絞り込み

サイドバーから分類フィルタを選択して、特定の工事種別に絞り込めます。

## 📁 プロジェクト構造

```
netisagent/
├── src/                               # ソースコード
│   ├── data_processor.py              # Excelデータ処理
│   ├── embedding_generator.py         # エンベディング生成
│   ├── search_indexer.py              # インデックス管理
│   └── search_agent.py                # 検索エージェント
├── config/                            # 設定ファイル（将来用）
├── data/                              # データディレクトリ
│   └── processed/                     # 処理済みデータ
├── upload_to_search.py                # データ投入スクリプト
├── app.py                             # Streamlit Webアプリ
├── requirements.txt                   # 依存ライブラリ
├── .env.template                      # 環境変数テンプレート
├── .env                               # 環境変数（要作成）
└── netisデータ.xlsx                   # 元データ
```

## 🔧 技術スタック

- **データ処理**: pandas, openpyxl
- **検索**: Azure AI Search
- **AI**: Azure OpenAI (GPT-4, text-embedding-ada-002)
- **UI**: Streamlit
- **言語**: Python 3.11+

## 📝 システムアーキテクチャ

```
┌─────────────────────┐
│  Streamlit Web UI   │ ← ユーザーインターフェース
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Search Agent      │ ← チャット処理・検索管理
│   (search_agent.py) │
└──────────┬──────────┘
           │
           ▼
     ┌────┴────┐
     │         │
     ▼         ▼
┌─────────┐ ┌──────────────┐
│ Azure   │ │ Azure OpenAI │
│ AI      │ │ (GPT-4 +     │
│ Search  │ │  Embeddings) │
└─────────┘ └──────────────┘
```

### インデックス設計

- **ベクトル化フィールド**: アブストラクト、概要、新規性、適用範囲
- **フィルタラブル**: 分類1〜5、事後評価、適用期間
- **検索可能**: 技術名称、適用条件、留意事項
- **表示専用**: URL、副題、基準

## 🔍 検索設定詳細

### インデックス基本情報
- **インデックス名**: `netis-index`
- **ドキュメント数**: 415件
- **検索方式**: ハイブリッド検索（キーワード + ベクトル）

### フィールド構成と検索方式

#### 1. キーワード検索対象フィールド（日本語アナライザー使用）

| フィールド名 | 内容 | 検索設定 |
|------------|------|---------|
| `tech_name` | 技術名称 | searchable |
| `abstract` | 新規性・期待される効果 | searchable + `ja.microsoft` |
| `overview` | 従来技術と比較 | searchable + `ja.microsoft` |
| `innovation` | 新規性・効果 | searchable + `ja.microsoft` |
| `scope` | 適用範囲 | searchable + `ja.microsoft` |
| `conditions` | 適用条件 | searchable + `ja.microsoft` |
| `notes` | 留意事項 | searchable + `ja.microsoft` |
| `searchable_text` | 統合テキスト（上記を結合） | searchable + `ja.microsoft` |

**動作**: 日本語の形態素解析を行い、単語レベルでマッチング

#### 2. ベクトル検索対象フィールド

| フィールド名 | 内容 | 検索設定 |
|------------|------|---------|
| `searchable_text_vector` | 統合テキストのエンベディング | ベクトル検索 (1536次元) |

- **エンベディングモデル**: `text-embedding-3-small`
- **アルゴリズム**: HNSW（高速近似最近傍探索）
- **動作**: 意味的類似性でマッチング

#### 3. フィルタリング用フィールド

| フィールド名 | 内容 | 設定 |
|------------|------|------|
| `category1` | 工事分類1 | filterable + facetable |
| `category2` | 工事分類2 | filterable + facetable |
| `category3` | 工事分類3 | filterable + facetable |
| `category4` | 工事分類4 | filterable + facetable |
| `category5` | 工事分類5 | filterable + facetable |
| `evaluation` | 評価 | filterable + facetable |
| `period` | 掲載期間 | filterable |

**動作**: 検索結果の絞り込みに使用（アプリのサイドバーで選択可能）

#### 4. 表示専用フィールド（検索対象外）

| フィールド名 | 内容 |
|------------|------|
| `url` | NETIS URL |
| `subtitle` | サブタイトル |
| `standards` | 設計比較対象技術、または従来技術の名称 |

### 実際の検索フロー

ユーザーが「トンネルの漏水対策技術を教えて」と入力した場合：

```
1. クエリのエンベディング生成
   ↓
2. Azure AI Search に送信
   ├─ キーワード検索: "トンネル" "漏水" "対策" "技術" を含むドキュメントを探す
   │  （tech_name, abstract, overview, innovation, scope, conditions, notes から）
   │
   └─ ベクトル検索: 意味的に類似したドキュメントを探す
      （searchable_text_vector から上位k件）
   ↓
3. Azure AI Search が両方のスコアを統合してランキング
   ↓
4. 上位10件（デフォルト）を返却
```

### 検索パラメータ

| パラメータ | 設定値 | 説明 |
|----------|--------|------|
| `search_text` | ユーザーのクエリ | キーワード検索用 |
| `vector_queries` | クエリのエンベディング | ベクトル検索用 |
| `k_nearest_neighbors` | 10（デフォルト） | ベクトル検索の取得件数 |
| `top` | 10（デフォルト） | 最終的な返却件数 |
| `filter` | カテゴリフィルタ（任意） | 工事分類での絞り込み |

### ハイブリッド検索のメリット

1. **キーワード検索**: 完全一致・部分一致で確実にヒット
2. **ベクトル検索**: 同義語・類似表現でもヒット
3. **スコア統合**: 両方の良いところを組み合わせた最適なランキング

**例**：
- 「漏水」→「水漏れ」「浸水」「湧水」なども意味的に類似とみなされる
- 「対策」→「防止」「抑制」「低減」なども関連技術として検出

## 🐛 トラブルシューティング

### データ投入エラー

- Azure AI Searchの認証情報が正しいか確認してください
- インデックス名が重複していないか確認してください

### エンベディング生成エラー

- Azure OpenAIのデプロイメント名が正しいか確認してください
- レート制限に達していないか確認してください

### 検索結果が表示されない

- データが正しく投入されているか確認してください: `インデックス統計情報をチェック`

## 📝 ライセンス

このプロジェクトは独自ライセンスの下で公開されています。

---

**NETIS Search Agent - AI-Powered Construction Technology Search System**
