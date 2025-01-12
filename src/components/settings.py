import streamlit as st
from src.utils.config_manager import ConfigManager

class SettingsComponent:
    def __init__(self):
        self.config_manager = st.session_state.config_manager

    def render(self):
        st.title("Settings")

        # API Keys Section
        st.header("API Keys Configuration")
        
        # FRED API Key
        fred_key = self.config_manager.get_api_key('fred_api_key')
        new_fred_key = st.text_input(
            "FRED API Key",
            value=fred_key,
            type="password",
            help="Get your API key from https://fred.stlouisfed.org/docs/api/api_key.html"
        )
        if new_fred_key != fred_key:
            self.config_manager.update_api_key('fred_api_key', new_fred_key)
            st.success("FRED API key updated!")

        # Alpha Vantage API Key
        alpha_key = self.config_manager.get_api_key('alpha_vantage_key')
        new_alpha_key = st.text_input(
            "Alpha Vantage API Key",
            value=alpha_key,
            type="password",
            help="Get your API key from https://www.alphavantage.co/support/#api-key"
        )
        if new_alpha_key != alpha_key:
            self.config_manager.update_api_key('alpha_vantage_key', new_alpha_key)
            st.success("Alpha Vantage API key updated!")

        # Feature Flags Section
        st.header("Feature Configuration")
        
        # Macro Analysis Toggle
        macro_enabled = self.config_manager.get_feature_flag('enable_macro_analysis')
        if st.toggle("Enable Macro Analysis", value=macro_enabled):
            if not macro_enabled:
                self.config_manager.update_feature_flag('enable_macro_analysis', True)
                st.success("Macro Analysis enabled!")
        else:
            if macro_enabled:
                self.config_manager.update_feature_flag('enable_macro_analysis', False)
                st.success("Macro Analysis disabled!")

        # Technical Analysis Toggle
        stock_analysis_enabled = self.config_manager.get_feature_flag('enable_stock_analysis')
        if st.toggle("Enable Stock Analysis", value=stock_analysis_enabled):
            if not stock_analysis_enabled:
                self.config_manager.update_feature_flag('enable_stock_analysis', True)
                st.success("Stock Analysis enabled!")
        else:
            if stock_analysis_enabled:
                self.config_manager.update_feature_flag('enable_stock_analysis', False)
                st.success("Stock Analysis disabled!")

        # Display current configuration
        if st.checkbox("Show Current Configuration"):
            st.json(self.config_manager.config) 