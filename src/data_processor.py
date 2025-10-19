"""
NETISデータをExcelから読み込み、Azure AI Search用に整形するモジュール
"""
import pandas as pd
from typing import List, Dict, Any
import json
from pathlib import Path


class NETISDataProcessor:
    """NETISデータ処理クラス"""

    def __init__(self, excel_path: str):
        """
        初期化

        Args:
            excel_path: Excelファイルのパス
        """
        self.excel_path = Path(excel_path)
        self.df = None

    def load_excel(self) -> pd.DataFrame:
        """
        Excelファイルを読み込む

        Returns:
            pandas DataFrame
        """
        print(f"Loading Excel file: {self.excel_path}")
        self.df = pd.read_excel(self.excel_path)
        print(f"Loaded {len(self.df)} records")
        return self.df

    def clean_data(self) -> pd.DataFrame:
        """
        データをクリーンアップ
        - NaN値を空文字列に変換
        - 不要なカラムを削除

        Returns:
            クリーンアップされたDataFrame
        """
        if self.df is None:
            raise ValueError("データが読み込まれていません。先にload_excel()を実行してください。")

        # Unnamed: 0 カラムを削除
        if 'Unnamed: 0' in self.df.columns:
            self.df = self.df.drop('Unnamed: 0', axis=1)

        # NaN値を空文字列に変換
        self.df = self.df.fillna('')

        print("Data cleaned successfully")
        return self.df

    def convert_to_search_documents(self) -> List[Dict[str, Any]]:
        """
        Azure AI Search用のドキュメント形式に変換

        Returns:
            検索ドキュメントのリスト
        """
        if self.df is None:
            raise ValueError("データが読み込まれていません。")

        documents = []

        for idx, row in self.df.iterrows():
            # 一意のIDを生成（行番号ベース）
            doc_id = f"netis_{idx:04d}"

            # ベクトル化対象フィールドを結合（検索用の統合テキスト）
            searchable_text = ' '.join([
                str(row.get('アブストラクト', '')),
                str(row.get('概要', '')),
                str(row.get('新規性及び期待される効果', '')),
                str(row.get('適用範囲', ''))
            ]).strip()

            document = {
                'id': doc_id,
                'url': str(row.get('概要リンク', '')),
                'tech_name': str(row.get('技術名称', '')),
                'abstract': str(row.get('アブストラクト', '')),
                'overview': str(row.get('概要', '')),
                'innovation': str(row.get('新規性及び期待される効果', '')),
                'conditions': str(row.get('適用条件', '')),
                'scope': str(row.get('適用範囲', '')),
                'notes': str(row.get('留意事項', '')),
                'subtitle': str(row.get('副題', '')),
                'category1': str(row.get('分類 1', '')),
                'category2': str(row.get('分類 2', '')),
                'category3': str(row.get('分類 3', '')),
                'category4': str(row.get('分類 4', '')),
                'category5': str(row.get('分類 5', '')),
                'evaluation': str(row.get('事後評価', '')),
                'period': str(row.get('適用期間等', '')),
                'standards': str(row.get('適用される基準', '')),
                'searchable_text': searchable_text  # ベクトル検索用
            }

            documents.append(document)

        print(f"Converted {len(documents)} documents")
        return documents

    def save_to_json(self, documents: List[Dict[str, Any]], output_path: str):
        """
        ドキュメントをJSONファイルに保存

        Args:
            documents: 検索ドキュメントのリスト
            output_path: 出力ファイルパス
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)

        print(f"Saved documents to: {output_path}")

    def process_all(self, output_json_path: str = None) -> List[Dict[str, Any]]:
        """
        全処理を実行（読み込み → クリーンアップ → 変換）

        Args:
            output_json_path: JSON出力パス（オプション）

        Returns:
            検索ドキュメントのリスト
        """
        self.load_excel()
        self.clean_data()
        documents = self.convert_to_search_documents()

        if output_json_path:
            self.save_to_json(documents, output_json_path)

        return documents


if __name__ == "__main__":
    # テスト実行
    processor = NETISDataProcessor("../netisデータ.xlsx")
    documents = processor.process_all("../data/processed/netis_documents.json")

    # サンプル表示
    print("\n=== Sample Document ===")
    print(json.dumps(documents[0], ensure_ascii=False, indent=2))
