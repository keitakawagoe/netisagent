"""
Azure AI Searchのインデックス作成とデータ投入を行うモジュール
"""
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)
from typing import List, Dict, Any
import os
from dotenv import load_dotenv


class AzureSearchIndexer:
    """Azure AI Searchのインデックス管理クラス"""

    def __init__(self, endpoint: str = None, api_key: str = None, index_name: str = None):
        """
        初期化

        Args:
            endpoint: Azure Search エンドポイント
            api_key: Azure Search APIキー
            index_name: インデックス名
        """
        # 環境変数から読み込み
        load_dotenv()

        self.endpoint = endpoint or os.getenv('AZURE_SEARCH_ENDPOINT')
        self.api_key = api_key or os.getenv('AZURE_SEARCH_API_KEY')
        self.index_name = index_name or os.getenv('AZURE_SEARCH_INDEX_NAME', 'netis-index')

        if not self.endpoint or not self.api_key:
            raise ValueError("Azure Search endpoint and API key are required")

        self.credential = AzureKeyCredential(self.api_key)
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=self.credential
        )

    def create_index(self) -> SearchIndex:
        """
        NETISデータ用のインデックスを作成

        Returns:
            作成されたSearchIndex
        """
        # ベクトル検索設定
        vector_search = VectorSearch(
            profiles=[
                VectorSearchProfile(
                    name="netis-vector-profile",
                    algorithm_configuration_name="netis-hnsw-config"
                )
            ],
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="netis-hnsw-config"
                )
            ]
        )

        # フィールド定義
        fields = [
            # ID（必須）
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True
            ),

            # 基本情報
            SearchableField(
                name="tech_name",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=False,
                sortable=False
            ),
            SearchableField(
                name="abstract",
                type=SearchFieldDataType.String,
                searchable=True,
                analyzer_name="ja.microsoft"
            ),
            SearchableField(
                name="overview",
                type=SearchFieldDataType.String,
                searchable=True,
                analyzer_name="ja.microsoft"
            ),
            SearchableField(
                name="innovation",
                type=SearchFieldDataType.String,
                searchable=True,
                analyzer_name="ja.microsoft"
            ),
            SearchableField(
                name="scope",
                type=SearchFieldDataType.String,
                searchable=True,
                analyzer_name="ja.microsoft"
            ),
            SearchableField(
                name="conditions",
                type=SearchFieldDataType.String,
                searchable=True,
                analyzer_name="ja.microsoft"
            ),
            SearchableField(
                name="notes",
                type=SearchFieldDataType.String,
                searchable=True,
                analyzer_name="ja.microsoft"
            ),

            # メタデータ（フィルタリング用）
            SimpleField(
                name="category1",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True
            ),
            SimpleField(
                name="category2",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True
            ),
            SimpleField(
                name="category3",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True
            ),
            SimpleField(
                name="category4",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True
            ),
            SimpleField(
                name="category5",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True
            ),
            SimpleField(
                name="evaluation",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True
            ),
            SimpleField(
                name="period",
                type=SearchFieldDataType.String,
                filterable=True
            ),

            # 表示用フィールド
            SimpleField(
                name="url",
                type=SearchFieldDataType.String,
                filterable=False
            ),
            SimpleField(
                name="subtitle",
                type=SearchFieldDataType.String,
                filterable=False
            ),
            SimpleField(
                name="standards",
                type=SearchFieldDataType.String,
                filterable=False
            ),

            # ベクトル検索用（統合テキスト）
            SearchField(
                name="searchable_text_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,  # text-embedding-3-smallの次元数（デフォルト1536）
                vector_search_profile_name="netis-vector-profile"
            ),

            # 統合テキスト（検索用）
            SearchableField(
                name="searchable_text",
                type=SearchFieldDataType.String,
                searchable=True,
                analyzer_name="ja.microsoft"
            )
        ]

        # インデックス作成
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search
        )

        print(f"Creating index: {self.index_name}")
        result = self.index_client.create_or_update_index(index)
        print(f"Index created: {result.name}")

        return result

    def delete_index(self):
        """インデックスを削除"""
        print(f"Deleting index: {self.index_name}")
        self.index_client.delete_index(self.index_name)
        print("Index deleted")

    def upload_documents(self, documents: List[Dict[str, Any]], batch_size: int = 100):
        """
        ドキュメントをアップロード

        Args:
            documents: アップロードするドキュメントのリスト
            batch_size: バッチサイズ
        """
        search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=self.credential
        )

        total = len(documents)
        print(f"Uploading {total} documents in batches of {batch_size}...")

        for i in range(0, total, batch_size):
            batch = documents[i:i + batch_size]
            result = search_client.upload_documents(documents=batch)

            succeeded = sum([1 for r in result if r.succeeded])
            print(f"Batch {i // batch_size + 1}: {succeeded}/{len(batch)} documents uploaded")

        print("All documents uploaded successfully")

    def get_index_stats(self) -> Dict[str, Any]:
        """
        インデックスの統計情報を取得

        Returns:
            統計情報の辞書
        """
        search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=self.credential
        )

        stats = search_client.get_document_count()
        return {"document_count": stats}


if __name__ == "__main__":
    # テスト実行
    indexer = AzureSearchIndexer()

    # インデックス作成
    indexer.create_index()

    # 統計情報取得
    stats = indexer.get_index_stats()
    print(f"\nIndex stats: {stats}")
