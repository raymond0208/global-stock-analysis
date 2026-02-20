import streamlit as st

# set_page_config must be the very first Streamlit call in the script.
# Placing it here, before any project imports, guarantees that regardless
# of what those imports do at module level.
st.set_page_config(
    page_title="Stock Analyzer",
    page_icon="📈",
    layout="wide"
)

from src.main import StockAnalyzerApp

app = StockAnalyzerApp()
app.run()
