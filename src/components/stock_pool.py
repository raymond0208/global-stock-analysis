import streamlit as st
import pandas as pd
from src.models.stock_metrics import StockMetrics
from src.utils.data_fetcher import DataFetcher

class StockPoolComponent:
    def __init__(self):
        self.stock_metrics = StockMetrics()
        self.data_fetcher = DataFetcher()

    def add_stock(self, symbol, name):
        if not symbol:
            st.error("Please enter a stock symbol")
            return
            
        if symbol in st.session_state.stock_pool:
            st.warning(f"{symbol} is already in your stock pool")
            return
            
        # Verify the stock exists
        info = self.data_fetcher.get_stock_info(symbol)
        if info:
            if not name:  # If user didn't provide a name, use the one from API
                name = info['name']
            st.session_state.stock_pool[symbol] = name
            st.session_state.storage_manager.save_stock_pool(st.session_state.stock_pool)
            st.success(f"Added {symbol} to your stock pool")
        else:
            st.error(f"Could not verify stock symbol {symbol}")

    def remove_stock(self, symbol):
        if symbol in st.session_state.stock_pool:
            del st.session_state.stock_pool[symbol]
            st.session_state.storage_manager.save_stock_pool(st.session_state.stock_pool)
            st.session_state.show_remove_message = f"Removed {symbol} from your stock pool"
            st.rerun()

    def render(self):
        st.title("Stock Pool Management")
        
        if 'show_remove_message' in st.session_state:
            st.success(st.session_state.show_remove_message)
            del st.session_state.show_remove_message
        
        # Add new stock section
        with st.form("add_stock_form"):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                symbol = st.text_input("Stock Symbol(Enter stock symbol-e.g. AAPL for Apple Inc.)").upper()
            with col2:
                name = st.text_input("Company Name (optional)")
            with col3:
                submitted = st.form_submit_button("Add Stock")
                if submitted:
                    self.add_stock(symbol, name)

        # Display current stock pool
        if 'stock_pool' not in st.session_state:
            st.session_state.stock_pool = {}

        if st.session_state.stock_pool:
            st.subheader("Current Stock Pool")
            stock_list = list(st.session_state.stock_pool.items())
            results = []
            for symbol, name in stock_list:
                with st.spinner(f"Analyzing {symbol}..."):
                    metrics = self.stock_metrics.get_stock_metrics(symbol)
                    if metrics:
                        metrics['Symbol'] = symbol
                        metrics['Company'] = name
                        results.append(metrics)

            if results:
                # Add index column starting from 1
                df = pd.DataFrame(results)
                df.index = range(1, len(df) + 1)
                df.index.name = 'Number'
                
                # Reorder columns with Symbol and Company first
                cols = ['Symbol', 'Company'] + [col for col in df.columns if col not in ['Symbol', 'Company']]
                df = df[cols]
                
                # Apply highlighting only to numeric columns
                numeric_cols = [col for col in df.columns if col not in ['Symbol', 'Company', 'Recommendation']]
                
                # Create styler with highlighting only for numeric columns
                styler = df.style.highlight_max(subset=numeric_cols, axis=0)
                st.dataframe(styler)

                # Create columns for remove buttons
                cols = st.columns(4)
                for idx, (symbol, _) in enumerate(stock_list):
                    with cols[idx % 4]:
                        if st.button(f"Remove {symbol}", key=f"remove_{symbol}"):
                            self.remove_stock(symbol)