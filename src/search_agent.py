"""
Azure AI SearchとAzure OpenAIを組み合わせたNETIS検索エージェント
"""
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
from src.embedding_generator import EmbeddingGenerator


class NETISSearchAgent:
    """NETIS技術検索エージェント"""

    def __init__(self):
        """初期化"""
        load_dotenv()

        # Azure Search設定
        self.search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.search_api_key = os.getenv('AZURE_SEARCH_API_KEY')
        self.index_name = os.getenv('AZURE_SEARCH_INDEX_NAME', 'netis-index')

        # Azure OpenAI設定
        self.openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.openai_api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
        self.api_version = os.getenv('AZURE_OPENAI_API_VERSION')

        # クライアント初期化
        self.search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.search_api_key)
        )

        self.openai_client = AzureOpenAI(
            api_key=self.openai_api_key,
            api_version=self.api_version,
            azure_endpoint=self.openai_endpoint
        )

        self.embedding_generator = EmbeddingGenerator()

        # 会話履歴
        self.conversation_history: List[Dict[str, str]] = []
        self.last_search_results: List[Dict[str, Any]] = []

    def search(
        self,
        query: str,
        top: int = 10,
        filters: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        ハイブリッド検索を実行

        Args:
            query: 検索クエリ
            top: 取得件数
            filters: ODataフィルタ式

        Returns:
            検索結果のリスト
        """
        # クエリのエンベディングを生成
        query_vector = self.embedding_generator.generate_embedding(query)

        # ベクトル検索クエリを作成
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top,
            fields="searchable_text_vector"
        )

        # ハイブリッド検索実行
        results = self.search_client.search(
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

        self.last_search_results = formatted_results
        return formatted_results

    def format_search_results_for_display(
        self,
        results: List[Dict[str, Any]],
        show_details: bool = False
    ) -> str:
        """
        検索結果を表示用にフォーマット

        Args:
            results: 検索結果
            show_details: 詳細情報を表示するか

        Returns:
            フォーマットされた文字列
        """
        if not results:
            return "該当する技術が見つかりませんでした。"

        output = f"\n検索結果: {len(results)}件の技術が見つかりました\n"
        output += "=" * 80 + "\n\n"

        for i, result in enumerate(results, 1):
            output += f"【{i}】{result['tech_name']}\n"
            output += f"URL: {result['url']}\n"
            output += f"\n【概要】\n{result['abstract']}\n"

            if show_details:
                if result.get('innovation'):
                    output += f"\n【新規性・期待される効果】\n{result['innovation']}\n"
                if result.get('conditions'):
                    output += f"\n【適用条件】\n{result['conditions']}\n"
                if result.get('scope'):
                    output += f"\n【適用範囲】\n{result['scope']}\n"
                if result.get('notes'):
                    output += f"\n【留意事項】\n{result['notes']}\n"

            # 分類情報
            categories = []
            for j in range(1, 4):
                cat = result.get(f'category{j}', '')
                if cat:
                    categories.append(cat)
            if categories:
                output += f"\n【分類】{' > '.join(categories)}\n"

            output += "\n" + "-" * 80 + "\n\n"

        return output

    def chat(self, user_message: str) -> str:
        """
        ユーザーメッセージに対して応答を生成

        Args:
            user_message: ユーザーのメッセージ

        Returns:
            エージェントの応答
        """
        # 会話履歴に追加
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # システムプロンプトを構築
        system_prompt = self._build_system_prompt()

        # メッセージ構築
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history[-10:])  # 最新10件のみ使用

        # OpenAI呼び出し
        response = self.openai_client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )

        assistant_message = response.choices[0].message.content

        # 会話履歴に追加
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def _build_system_prompt(self) -> str:
        """システムプロンプトを構築"""
        return """あなたはNETIS（新技術情報提供システム）の検索アシスタントです。
建設業従事者が適切な新技術を見つけるお手伝いをします。

【役割】
1. ユーザーの質問から適切な検索クエリを判断する
2. 検索結果を分かりやすく提示する
3. フォローアップ質問で絞り込みをサポートする
4. 技術の詳細について質問されたら、該当技術の詳細情報を提供する
5. 技術の比較を求められたら、複数技術を比較して提示する

【対応パターン】
- 「〜の技術を探している」→ 検索を実行して結果を提示
- 「もっと絞り込みたい」→ 分類や条件での絞り込みを提案
- 「N番目について詳しく」→ 該当技術の詳細を表示
- 「AとBを比較して」→ 2つの技術を比較

【出力形式】
- 初回検索: 技術名 + アブストラクト + URL（最大10件）
- 詳細表示: 適用条件、留意事項、新規性なども含める
- フォローアップ質問を自然に提案する

現在の検索結果数: """ + str(len(self.last_search_results))

    def process_query(self, user_input: str) -> str:
        """
        ユーザー入力を処理して応答を生成

        Args:
            user_input: ユーザーの入力

        Returns:
            応答メッセージ
        """
        # 検索が必要かどうかを判定（簡易版）
        search_keywords = ['探して', '検索', '教えて', '技術', '工法', '対策', 'ありますか', 'ください']
        needs_search = any(keyword in user_input for keyword in search_keywords)

        # 検索実行
        if needs_search and not self.last_search_results:
            results = self.search(user_input, top=10)
            results_text = self.format_search_results_for_display(results)

            # チャットで応答生成
            context = f"以下の検索結果を踏まえて、ユーザーに分かりやすく提示し、フォローアップ質問を提案してください:\n\n{results_text}"
            return self.chat(context + "\n\nユーザーの質問: " + user_input)

        # 詳細表示や比較の場合
        else:
            return self.chat(user_input)

    def reset_conversation(self):
        """会話履歴をリセット"""
        self.conversation_history = []
        self.last_search_results = []


if __name__ == "__main__":
    # テスト実行
    agent = NETISSearchAgent()

    # テスト検索
    results = agent.search("トンネル 漏水対策", top=3)
    print(agent.format_search_results_for_display(results))
