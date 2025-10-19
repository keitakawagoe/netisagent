#!/usr/bin/env python3
"""
NETISデータをAzure AI Searchに投入するメインスクリプト

使用方法:
    python upload_to_search.py
"""
from src.data_processor import NETISDataProcessor
from src.embedding_generator import EmbeddingGenerator
from src.search_indexer import AzureSearchIndexer
from pathlib import Path
import sys


def main():
    """メイン処理"""
    print("=" * 60)
    print("NETIS Data Upload to Azure AI Search")
    print("=" * 60)

    try:
        # ステップ1: Excelデータの読み込みと整形
        print("\n[Step 1/4] Loading and processing Excel data...")
        excel_path = Path(__file__).parent / "netisデータ.xlsx"

        if not excel_path.exists():
            print(f"Error: Excel file not found: {excel_path}")
            sys.exit(1)

        processor = NETISDataProcessor(str(excel_path))
        documents = processor.process_all(
            output_json_path="data/processed/netis_documents.json"
        )

        print(f"✓ Processed {len(documents)} documents")

        # ステップ2: エンベディングの生成
        print("\n[Step 2/4] Generating embeddings...")
        generator = EmbeddingGenerator()

        # searchable_textからエンベディングを生成
        texts = [doc['searchable_text'] for doc in documents]
        embeddings = generator.generate_embeddings_batch(
            texts,
            batch_size=16,
            delay=0.5
        )

        # ドキュメントにエンベディングを追加
        for doc, embedding in zip(documents, embeddings):
            doc['searchable_text_vector'] = embedding

        print(f"✓ Generated embeddings for {len(embeddings)} documents")

        # ステップ3: インデックスの作成
        print("\n[Step 3/4] Creating search index...")
        indexer = AzureSearchIndexer()

        # 既存インデックスがあれば削除確認
        try:
            stats = indexer.get_index_stats()
            print(f"Existing index found with {stats['document_count']} documents")
            response = input("Delete and recreate index? (yes/no): ")
            if response.lower() == 'yes':
                indexer.delete_index()
                indexer.create_index()
            else:
                print("Using existing index")
        except Exception:
            # インデックスが存在しない場合は新規作成
            indexer.create_index()

        print("✓ Index ready")

        # ステップ4: ドキュメントのアップロード
        print("\n[Step 4/4] Uploading documents to search index...")
        indexer.upload_documents(documents, batch_size=10)

        # 最終統計
        final_stats = indexer.get_index_stats()
        print(f"\n✓ Upload completed")
        print(f"  Total documents in index: {final_stats['document_count']}")

        print("\n" + "=" * 60)
        print("SUCCESS: All data uploaded to Azure AI Search!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
