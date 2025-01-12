import streamlit as st
from src.components.stock_pool import StockPoolComponent
from src.components.stock_analysis import StockAnalysisComponent
from src.components.macro_analysis import MacroAnalysisComponent
from src.components.settings import SettingsComponent
from src.utils.config_manager import ConfigManager

class StockAnalyzerApp:
    def __init__(self):
        st.set_page_config(
            page_title="Stock Analyzer",
            page_icon="📈",
            layout="wide"
        )
        self.config_manager = ConfigManager()
        self.initialize_session_state()

    def initialize_session_state(self):
        if 'storage_manager' not in st.session_state:
            from src.utils.storage_manager import StorageManager
            st.session_state.storage_manager = StorageManager()
        
        if 'stock_pool' not in st.session_state:
            st.session_state.stock_pool = st.session_state.storage_manager.load_stock_pool()
        
        if 'favorite_stocks' not in st.session_state:
            st.session_state.favorite_stocks = st.session_state.storage_manager.load_favorite_stocks()
        
        if 'config_manager' not in st.session_state:
            st.session_state.config_manager = self.config_manager

    def run(self):
        st.sidebar.title("Navigation")
        
        # Check if API keys are configured
        fred_key = self.config_manager.get_api_key('fred_api_key')
        alpha_key = self.config_manager.get_api_key('alpha_vantage_key')
        
        if not (fred_key and alpha_key):
            st.warning("Please configure your API keys in the Settings page")
        
        page = st.sidebar.radio(
            "Select a page",
            ["Stock Pool", "Stock Analysis", "Macro Analysis", "Settings"]
        )

        try:
            if page == "Stock Pool":
                StockPoolComponent().render()
            elif page == "Stock Analysis":
                StockAnalysisComponent().render()
            elif page == "Macro Analysis":
                if self.config_manager.get_feature_flag('enable_macro_analysis'):
                    MacroAnalysisComponent().render()
                else:
                    st.info("Macro Analysis is currently disabled. Enable it in Settings.")
            else:
                SettingsComponent().render()
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    app = StockAnalyzerApp()
    app.run() 