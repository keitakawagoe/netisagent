import azure.functions as func
import json
import logging
import os
from typing import List
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI


# =============================================================================
# EmbeddingGenerator クラス（統合版）
# =============================================================================
class EmbeddingGenerator:
    """Azure OpenAIを使用してテキストの埋め込みを生成するクラス"""

    def __init__(self):
        """環境変数からAzure OpenAIの設定を読み込み、クライアントを初期化"""
        self.endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        self.deployment_name = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        self.api_version = os.environ.get("AZURE_OPENAI_API_VERSION")

        if not all([self.endpoint, self.api_key, self.deployment_name]):
            raise ValueError("必要な環境変数が設定されていません。")

        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )

    def generate_embedding(self, text: str) -> List[float]:
        """
        テキストから埋め込みベクトルを生成

        Args:
            text (str): 埋め込みを生成するテキスト

        Returns:
            List[float]: 1536次元の埋め込みベクトル
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.deployment_name
            )
            return response.data[0].embedding

        except Exception as e:
            logging.error(f"埋め込み生成エラー: {str(e)}")
            raise


# =============================================================================
# Azure Functions App
# =============================================================================
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# 環境変数から設定を読み込み
AZURE_SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.environ.get("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX_NAME")

# EmbeddingGeneratorの初期化
embedding_generator = EmbeddingGenerator()

# Azure AI Searchクライアントの初期化
search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name=AZURE_SEARCH_INDEX_NAME,
    credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
)


@app.route(route="search", methods=["GET"])
def search_netis(req: func.HttpRequest) -> func.HttpResponse:
    """
    NETIS技術検索エンドポイント

    クエリパラメータ:
        - query (str): 検索クエリ（必須）
        - top (int): 取得件数（デフォルト: 10、最大: 20）
        - category (str): 工事分類フィルタ（オプション）

    Returns:
        JSON形式の検索結果
    """
    logging.info('NETIS検索リクエストを受信しました')

    try:
        # クエリパラメータの取得
        query = req.params.get('query')
        if not query:
            return func.HttpResponse(
                json.dumps({
                    "error": "クエリパラメータ 'query' は必須です",
                    "message": "検索クエリを指定してください（例: ?query=トンネルの漏水対策）"
                }, ensure_ascii=False),
                status_code=400,
                mimetype="application/json"
            )

        # top パラメータ（デフォルト: 10、最大: 20）
        try:
            top = int(req.params.get('top', '10'))
            top = min(max(top, 1), 20)  # 1-20の範囲に制限
        except ValueError:
            top = 10

        # category フィルタ（オプション）
        category = req.params.get('category')

        logging.info(f'検索クエリ: {query}, 取得件数: {top}, カテゴリ: {category}')

        # ベクトル検索用の埋め込み生成
        query_vector = embedding_generator.generate_embedding(query)

        # ベクトルクエリの作成
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top,
            fields="searchable_text_vector"
        )

        # フィルタの構築
        filters = None
        if category:
            filters = f"search.in(category1, '{category}', '|') or search.in(category2, '{category}', '|') or search.in(category3, '{category}', '|')"

        # ハイブリッド検索の実行
        results = search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=filters,
            top=top
        )

        # 結果の整形
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.get("id", ""),
                "tech_name": result.get("techName", ""),
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
                "score": result.get("@search.score", 0.0)
            })

        # レスポンスの作成
        response_data = {
            "query": query,
            "count": len(formatted_results),
            "results": formatted_results
        }

        logging.info(f'検索完了: {len(formatted_results)}件の結果を取得')

        return func.HttpResponse(
            json.dumps(response_data, ensure_ascii=False, indent=2),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f'検索エラー: {str(e)}')
        return func.HttpResponse(
            json.dumps({
                "error": "内部サーバーエラー",
                "message": str(e)
            }, ensure_ascii=False),
            status_code=500,
            mimetype="application/json"
        )
