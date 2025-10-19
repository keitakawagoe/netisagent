"""
NETIS検索 Azure Function
Azure AI Foundry Agent Playground から呼び出されるAPI
"""
import azure.functions as func
import logging
import json
import os
from typing import Optional

# 既存のsrcモジュールをインポート
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.embedding_generator import EmbeddingGenerator
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# グローバル変数として初期化（コールドスタート対策）
search_client = None
embedding_generator = None


def initialize_clients():
    """Azure Search と Embedding Generator を初期化"""
    global search_client, embedding_generator

    if search_client is None:
        search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        search_api_key = os.getenv('AZURE_SEARCH_API_KEY')
        index_name = os.getenv('AZURE_SEARCH_INDEX_NAME', 'netis-index')

        search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(search_api_key)
        )

    if embedding_generator is None:
        embedding_generator = EmbeddingGenerator()


@app.route(route="search", methods=["GET"])
def search_netis(req: func.HttpRequest) -> func.HttpResponse:
    """
    NETIS技術検索エンドポイント

    Parameters:
        query (str): 検索クエリ（必須）
        top (int): 取得件数（デフォルト: 10、最大: 20）
        category (str): 工事分類フィルタ（オプション）

    Returns:
        JSON: 検索結果
    """
    logging.info('NETIS search function processed a request.')

    try:
        # クライアント初期化
        initialize_clients()

        # パラメータ取得
        query = req.params.get('query')
        if not query:
            return func.HttpResponse(
                json.dumps({
                    "error": "クエリパラメータ'query'は必須です",
                    "example": "/api/search?query=トンネルの漏水対策"
                }, ensure_ascii=False),
                status_code=400,
                mimetype="application/json"
            )

        top = int(req.params.get('top', '10'))
        top = min(top, 20)  # 最大20件に制限

        category = req.params.get('category')

        # フィルタ構築
        filters = None
        if category:
            filters = f"category1 eq '{category}' or category2 eq '{category}' or category3 eq '{category}'"

        logging.info(f'Search query: {query}, top: {top}, category: {category}')

        # クエリのエンベディング生成
        query_vector = embedding_generator.generate_embedding(query)

        # ベクトル検索クエリを作成
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top,
            fields="searchable_text_vector"
        )

        # ハイブリッド検索実行
        results = search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=filters,
            top=top,
            select=[
                "id", "tech_name", "abstract", "url", "overview",
                "innovation", "conditions", "scope", "notes",
                "category1", "category2", "category3",
                "evaluation", "subtitle"
            ]
        )

        # 結果を整形
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.get("id", ""),
                "tech_name": result.get("tech_name", ""),
                "abstract": result.get("abstract", ""),
                "url": result.get("url", ""),
                "overview": result.get("overview", ""),
                "innovation": result.get("innovation", ""),
                "conditions": result.get("conditions", ""),
                "scope": result.get("scope", ""),
                "notes": result.get("notes", ""),
                "category1": result.get("category1", ""),
                "category2": result.get("category2", ""),
                "category3": result.get("category3", ""),
                "evaluation": result.get("evaluation", ""),
                "subtitle": result.get("subtitle", ""),
                "score": result.get("@search.score", 0)
            })

        # レスポンス作成
        response_data = {
            "query": query,
            "count": len(formatted_results),
            "results": formatted_results
        }

        logging.info(f'Search completed. Found {len(formatted_results)} results.')

        return func.HttpResponse(
            json.dumps(response_data, ensure_ascii=False, indent=2),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f'Error in search function: {str(e)}')
        return func.HttpResponse(
            json.dumps({
                "error": "検索中にエラーが発生しました",
                "details": str(e)
            }, ensure_ascii=False),
            status_code=500,
            mimetype="application/json"
        )
