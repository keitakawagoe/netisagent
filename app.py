"""
NETISエージェント - Streamlit Webアプリケーション
"""
import streamlit as st
from src.search_agent import NETISSearchAgent
import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))


def init_session_state():
    """セッション状態の初期化"""
    if 'agent' not in st.session_state:
        st.session_state.agent = NETISSearchAgent()
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []


def display_search_results(results):
    """検索結果を表示"""
    if not results:
        st.warning("該当する技術が見つかりませんでした。")
        return

    st.success(f"{len(results)}件の技術が見つかりました")

    for i, result in enumerate(results, 1):
        with st.expander(f"【{i}】{result['tech_name']}", expanded=(i <= 3)):
            # URL
            st.markdown(f"🔗 [NETISページを開く]({result['url']})")

            # アブストラクト
            st.markdown("**概要**")
            st.write(result['abstract'])

            # 分類
            categories = []
            for j in range(1, 4):
                cat = result.get(f'category{j}', '')
                if cat:
                    categories.append(cat)
            if categories:
                st.markdown(f"**分類:** {' > '.join(categories)}")

            # 詳細情報トグル
            show_details = st.checkbox(f"詳細を表示", key=f"detail_{i}")

            if show_details:
                if result.get('innovation'):
                    st.markdown("**新規性・期待される効果**")
                    st.write(result['innovation'])

                if result.get('scope'):
                    st.markdown("**適用範囲**")
                    st.write(result['scope'])

                if result.get('conditions'):
                    st.markdown("**適用条件**")
                    st.write(result['conditions'])

                if result.get('notes'):
                    st.markdown("**留意事項**")
                    st.write(result['notes'])


def main():
    """メインアプリケーション"""
    st.set_page_config(
        page_title="NETISエージェント",
        page_icon="🏗️",
        layout="wide"
    )

    # タイトル
    st.title("🏗️ NETISエージェント")
    st.markdown("建設技術をAIで検索・提案します")

    # セッション状態の初期化
    init_session_state()

    # サイドバー
    with st.sidebar:
        st.header("設定")

        # 検索件数設定
        top_k = st.slider("検索結果数", min_value=5, max_value=20, value=10)

        # フィルタ設定（将来の拡張用）
        st.markdown("---")
        st.subheader("絞り込み（オプション）")

        filter_category = st.selectbox(
            "分類で絞り込み",
            ["すべて", "道路維持修繕工", "トンネル補修補強工", "仮設工", "舗装工"],
            index=0
        )

        # 会話リセットボタン
        if st.button("会話をリセット"):
            st.session_state.agent.reset_conversation()
            st.session_state.messages = []
            st.session_state.search_results = []
            st.success("会話をリセットしました")
            st.rerun()

        # 使い方ガイド
        st.markdown("---")
        st.subheader("使い方")
        st.markdown("""
        **検索例:**
        - 「トンネルの漏水対策技術を教えて」
        - 「環境負荷が少ない工法は？」
        - 「道路の舗装に使える技術」

        **フォローアップ:**
        - 「1番目の技術について詳しく教えて」
        - 「もっと絞り込みたい」
        - 「1番と3番を比較して」
        """)

    # メインコンテンツエリア
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("チャット")

        # チャット履歴表示
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # ユーザー入力
        if prompt := st.chat_input("技術について質問してください..."):
            # ユーザーメッセージを表示
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # エージェント処理
            with st.chat_message("assistant"):
                with st.spinner("検索中..."):
                    # 検索キーワードを含む場合は検索実行
                    search_keywords = ['探して', '検索', '教えて', '技術', '工法', '対策', 'ありますか', 'ください']
                    needs_search = any(keyword in prompt for keyword in search_keywords)

                    if needs_search:
                        # フィルタ構築
                        filter_expr = None
                        if filter_category != "すべて":
                            filter_expr = f"category1 eq '{filter_category}'"

                        # 検索実行
                        results = st.session_state.agent.search(
                            query=prompt,
                            top=top_k,
                            filters=filter_expr
                        )
                        st.session_state.search_results = results

                        # 検索結果を整形
                        results_text = st.session_state.agent.format_search_results_for_display(results)

                        # AIによる応答生成
                        context = f"以下の検索結果を踏まえて応答してください:\n\n{results_text}\n\nユーザーの質問: {prompt}"
                        response = st.session_state.agent.chat(context)
                    else:
                        # 通常の会話
                        # 検索結果がある場合はコンテキストに含める
                        if st.session_state.search_results:
                            results_context = "\n\n直前の検索結果:\n"
                            for i, r in enumerate(st.session_state.search_results, 1):
                                results_context += f"{i}. {r['tech_name']}\n"
                            response = st.session_state.agent.chat(results_context + "\n\n" + prompt)
                        else:
                            response = st.session_state.agent.chat(prompt)

                    st.markdown(response)

            # アシスタントメッセージを保存
            st.session_state.messages.append({"role": "assistant", "content": response})

    with col2:
        st.subheader("検索結果")

        if st.session_state.search_results:
            display_search_results(st.session_state.search_results)
        else:
            st.info("検索を実行すると、ここに結果が表示されます")


if __name__ == "__main__":
    main()
