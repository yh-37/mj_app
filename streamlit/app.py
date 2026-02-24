"""Home page for the Mahjong Stats Dashboard."""
import streamlit as st

st.set_page_config(
    page_title="麻雀成績ダッシュボード",
    page_icon="🀄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🀄 麻雀成績ダッシュボード")
st.markdown("""
サイドバーからページを選択してください。

| ページ | 内容 |
|---|---|
| 🀄 **Hamada の成績** | フリー・セット対局の個人成績、累計スコア推移、順位分布など |
| 👥 **プレイヤー別成績** | グループ・プレイヤーを選択してセット対局の個人成績を確認 |
""")
