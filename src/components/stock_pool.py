import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from src.models.stock_metrics import StockMetrics
from src.utils.data_fetcher import DataFetcher

class StockPoolComponent:
    def __init__(self):
        self.stock_metrics = StockMetrics()
        self.data_fetcher = DataFetcher()
        # Initialize stock pool in session state if it doesn't exist
        if 'stock_pool' not in st.session_state:
            st.session_state.stock_pool = {}
        if 'clear_search' not in st.session_state:
            st.session_state.clear_search = False

    def search_stocks(self, query):
        """Search for stocks using Yahoo Finance API"""
        if not query or len(query) < 2:
            return []
            
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=20&newsCount=0&enableFuzzyQuery=false"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            data = response.json()
            
            suggestions = []
            if 'quotes' in data:
                for quote in data['quotes']:
                    if 'symbol' in quote and 'longname' in quote:
                        symbol = quote['symbol']
                        name = quote['longname']
                        # Filter out non-stock symbols and ensure both symbol and name are strings
                        if not any(x in symbol for x in ['-', '^', '=']) and isinstance(symbol, str) and isinstance(name, str):
                            suggestions.append({
                                "label": f"{symbol} - {name}",
                                "value": {"symbol": symbol, "name": name}
                            })
            return suggestions
        except Exception as e:
            print(f"Error searching stocks: {str(e)}")
            return []

    def handle_search_change(self):
        """Handle search input changes"""
        if 'stock_search_input' in st.session_state:
            st.session_state.search_query = st.session_state.stock_search_input
            # Reset selected stock when search changes
            st.session_state.selected_stock = None

    def add_stock(self, symbol, name):
        """Add stock to pool"""
        if symbol in st.session_state.stock_pool:
            st.warning(f"{symbol} is already in your stock pool")
            return False
        
        st.session_state.stock_pool[symbol] = name
        if hasattr(st.session_state, 'storage_manager'):
            st.session_state.storage_manager.save_stock_pool(st.session_state.stock_pool)
        return True

    def remove_stock(self, symbol):
        """Remove stock from pool"""
        if symbol in st.session_state.stock_pool:
            del st.session_state.stock_pool[symbol]
            if hasattr(st.session_state, 'storage_manager'):
                st.session_state.storage_manager.save_stock_pool(st.session_state.stock_pool)
            st.session_state.show_remove_message = f"Removed {symbol} from your stock pool"
            # Clear any cached results
            if 'stock_metrics_results' in st.session_state:
                del st.session_state.stock_metrics_results
            # Force a complete rerun to refresh the UI
            st.experimental_rerun()

    def render(self):
        st.title("Stock Pool Management")
        
        if 'show_remove_message' in st.session_state:
            st.success(st.session_state.show_remove_message)
            del st.session_state.show_remove_message

        # Create a container for search with custom CSS
        search_container = st.container()
        with search_container:
            # Initialize session state for search
            if 'search_query' not in st.session_state:
                st.session_state.search_query = ''
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # If clear_search is True, we want to show empty input
                default_value = "" if st.session_state.clear_search else st.session_state.get('stock_search_input', '')
                
                search_query = st.text_input(
                    "Search by Symbol or Company Name",
                    value=default_value,
                    key="stock_search_input",
                    on_change=self.handle_search_change,
                    help="Type to search stocks",
                    label_visibility="visible"
                )
                
                # Reset clear_search flag after input is rendered
                if st.session_state.clear_search:
                    st.session_state.clear_search = False
                
                # Store selected stock in session state
                if 'selected_stock' not in st.session_state:
                    st.session_state.selected_stock = None
                
                # Only show suggestions if we have a valid search query
                if search_query and len(search_query) >= 2:
                    suggestions = self.search_stocks(search_query)
                    if suggestions:
                        selected = st.selectbox(
                            "Select a stock",
                            options=[{"label": "Select a stock...", "value": None}] + suggestions,
                            format_func=lambda x: x["label"] if x and isinstance(x, dict) and "label" in x else "Select a stock...",
                            key="stock_selector",
                            label_visibility="collapsed"
                        )
                        
                        # Update selected stock in session state
                        if selected and isinstance(selected, dict) and selected.get("value"):
                            st.session_state.selected_stock = selected
            
            with col2:
                if st.button("Add Stock", key="add_stock_button"):
                    if (st.session_state.selected_stock and 
                        isinstance(st.session_state.selected_stock, dict) and 
                        st.session_state.selected_stock.get("value")):
                        
                        selected_value = st.session_state.selected_stock["value"]
                        if isinstance(selected_value, dict) and "symbol" in selected_value and "name" in selected_value:
                            symbol = selected_value["symbol"]
                            name = selected_value["name"]
                            
                            if self.add_stock(symbol, name):
                                st.success(f"Added {symbol} to your stock pool")
                                # Set flag to clear search on next render
                                st.session_state.clear_search = True
                                # Clear selection
                                st.session_state.selected_stock = None
                                st.session_state.search_query = ''
                                if 'stock_metrics_results' in st.session_state:
                                    del st.session_state.stock_metrics_results
                                st.experimental_rerun()
                    else:
                        st.warning("Please select a stock first")

        # Display current stock pool
        if st.session_state.stock_pool:
            st.subheader("Current Stock Pool")
            stock_list = list(st.session_state.stock_pool.items())
            
            # Create a container for the stock pool display
            pool_container = st.container()
            
            with pool_container:
                # Use cached results if available, otherwise analyze stocks
                if 'stock_metrics_results' not in st.session_state:
                    results = []
                    for symbol, name in stock_list:
                        with st.spinner(f"Analyzing {symbol}..."):
                            metrics = self.stock_metrics.get_stock_metrics(symbol)
                            if metrics:
                                metrics['Symbol'] = symbol
                                metrics['Company'] = name
                                results.append(metrics)
                    st.session_state.stock_metrics_results = results
                
                results = st.session_state.stock_metrics_results
                
                if results:
                    try:
                        # Create DataFrame
                        df = pd.DataFrame(results).copy()  # Create a copy to avoid modifications to cached data
                        
                        # Ensure DataFrame rows match current stock pool
                        df = df[df['Symbol'].isin(st.session_state.stock_pool.keys())]
                        
                        if not df.empty:
                            # Reset index to ensure continuous numbering
                            df = df.reset_index(drop=True)
                            # Add index column starting from 1
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
                            
                            # Create remove buttons
                            button_cols = st.columns(4)
                            current_symbols = df['Symbol'].tolist()
                            for idx, symbol in enumerate(current_symbols):
                                with button_cols[idx % 4]:
                                    if st.button(f"Remove {symbol}", key=f"remove_{symbol}_{idx}"):
                                        self.remove_stock(symbol)
                    
                    except Exception as e:
                        st.error(f"Error displaying stock metrics: {str(e)}")
                        # Clear cached results if there's an error
                        if 'stock_metrics_results' in st.session_state:
                            del st.session_state.stock_metrics_results