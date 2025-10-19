"""
Azure OpenAIを使用してテキストのエンベディングを生成するモジュール
"""
from openai import AzureOpenAI
from typing import List
import os
from dotenv import load_dotenv
import time


class EmbeddingGenerator:
    """エンベディング生成クラス"""

    def __init__(
        self,
        endpoint: str = None,
        api_key: str = None,
        deployment_name: str = None,
        api_version: str = None
    ):
        """
        初期化

        Args:
            endpoint: Azure OpenAI エンドポイント
            api_key: Azure OpenAI APIキー
            deployment_name: デプロイメント名
            api_version: APIバージョン
        """
        load_dotenv()

        self.endpoint = endpoint or os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_key = api_key or os.getenv('AZURE_OPENAI_API_KEY')
        self.deployment_name = deployment_name or os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT')
        self.api_version = api_version or os.getenv('AZURE_OPENAI_API_VERSION')

        if not all([self.endpoint, self.api_key, self.deployment_name]):
            raise ValueError("Azure OpenAI credentials are required")

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )

    def generate_embedding(self, text: str) -> List[float]:
        """
        単一テキストのエンベディングを生成

        Args:
            text: エンベディング対象のテキスト

        Returns:
            エンベディングベクトル
        """
        if not text or not text.strip():
            # 空文字列の場合はゼロベクトルを返す
            return [0.0] * 1536

        response = self.client.embeddings.create(
            input=text,
            model=self.deployment_name
        )

        return response.data[0].embedding

    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 16,
        delay: float = 0.5
    ) -> List[List[float]]:
        """
        複数テキストのエンベディングをバッチ生成

        Args:
            texts: エンベディング対象のテキストリスト
            batch_size: バッチサイズ
            delay: バッチ間の待機時間（秒）

        Returns:
            エンベディングベクトルのリスト
        """
        embeddings = []
        total = len(texts)

        print(f"Generating embeddings for {total} texts...")

        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size

            print(f"Processing batch {batch_num}/{total_batches}...")

            # 空文字列を除外
            non_empty_texts = [t if t and t.strip() else " " for t in batch]

            response = self.client.embeddings.create(
                input=non_empty_texts,
                model=self.deployment_name
            )

            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)

            # レート制限対策
            if i + batch_size < total:
                time.sleep(delay)

        print(f"Generated {len(embeddings)} embeddings")
        return embeddings


if __name__ == "__main__":
    # テスト実行
    generator = EmbeddingGenerator()

    # 単一テキストのテスト
    test_text = "トンネルの漏水対策工法"
    embedding = generator.generate_embedding(test_text)
    print(f"Generated embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
