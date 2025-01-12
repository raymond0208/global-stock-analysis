import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from src.models.stock_metrics import StockMetrics
import numpy as np

class StockAnalysisComponent:
    def __init__(self):
        self.stock_metrics = StockMetrics()

    def render_score_gauge(self, score, title):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={'text': title},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 35], 'color': "red"},
                    {'range': [35, 50], 'color': "orange"},
                    {'range': [50, 65], 'color': "yellow"},
                    {'range': [65, 80], 'color': "lightgreen"},
                    {'range': [80, 100], 'color': "green"}
                ]
            }
        ))
        fig.update_layout(height=300)
        return fig

    def fetch_stock_data(self, symbol):
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period="1y")
            if data.empty:
                return None
            # Handle infinite values
            data = data.replace([np.inf, -np.inf], np.nan)
            data = data.dropna()
            return data
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            return None

    def calculate_moving_average(self, data, period):
        try:
            ma = data['Close'].rolling(window=period).mean()
            # Convert to DataFrame with date index
            ma_df = pd.DataFrame({
                'Date': data.index,
                'Value': ma.values
            }).dropna()
            ma_df.set_index('Date', inplace=True)
            return ma_df
        except Exception as e:
            st.error(f"Error calculating moving average: {str(e)}")
            return pd.DataFrame()

    def calculate_rsi(self, data, period=14):
        try:
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            # Convert to DataFrame with date index
            rsi_df = pd.DataFrame({
                'Date': data.index,
                'Value': rsi.values
            }).dropna()
            rsi_df.set_index('Date', inplace=True)
            return rsi_df
        except Exception as e:
            st.error(f"Error calculating RSI: {str(e)}")
            return pd.DataFrame()

    def create_line_chart(self, data, title):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Value'], mode='lines', name=title))
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Value",
            height=400
        )
        return fig

    def render(self):
        if 'favorite_stocks' not in st.session_state:
            st.session_state.favorite_stocks = []

        st.title("Stock Analysis")
        
        symbol = st.text_input("Enter Stock Symbol").upper()
        
        if symbol:
            metrics = self.stock_metrics.get_stock_metrics(symbol)
            stock_data = self.fetch_stock_data(symbol)
            
            if metrics and stock_data is not None:
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(
                        self.render_score_gauge(
                            metrics['Score'], 
                            f"{symbol} Analysis Score"
                        )
                    )
                with col2:
                    st.info(f"Recommendation: {metrics['Recommendation']}")
                
                ma_20 = self.calculate_moving_average(stock_data, 20)
                ma_50 = self.calculate_moving_average(stock_data, 50)
                rsi = self.calculate_rsi(stock_data)

                if not ma_20.empty and not ma_50.empty and not rsi.empty:
                    with st.expander("Technical Analysis"):
                        st.markdown("### 20-Day Moving Average")
                        st.plotly_chart(self.create_line_chart(ma_20, "20-Day Moving Average"), use_container_width=True)
                        st.markdown("### 50-Day Moving Average")
                        st.plotly_chart(self.create_line_chart(ma_50, "50-Day Moving Average"), use_container_width=True)
                        st.markdown("### Relative Strength Index (RSI)")
                        st.plotly_chart(self.create_line_chart(rsi, "RSI"), use_container_width=True)

                    with st.expander("Profitability Metrics"):
                        st.metric("ROE (%)", f"{metrics['ROE (%)']:.2f}%")
                        st.metric("Operating Margin (%)", f"{metrics['Operating Margin (%)']:.2f}%")
                        st.metric("EPS/Price (%)", f"{metrics['EPS/Price (%)']:.2f}%")
                        st.metric("Quick Ratio", f"{metrics['Quick Ratio']:.2f}")
                        st.metric("Free Cash Flow", f"${metrics['Free Cash Flow ($M)']:.0f}M")
                        st.metric("P/E Ratio", f"{metrics['P/E Ratio']:.2f}")

                    if st.button("Add to Favorites"):
                        if symbol not in st.session_state.favorite_stocks:
                            st.session_state.favorite_stocks.append(symbol)
                            st.session_state.storage_manager.save_favorite_stocks(st.session_state.favorite_stocks)
                            st.success(f"Added {symbol} to favorites!")
            else:
                st.error(f"Could not fetch data for {symbol}")

        if st.session_state.favorite_stocks:
            st.subheader("Favorite Stocks Analysis")
            results = []
            for fav_symbol in st.session_state.favorite_stocks:
                metrics = self.stock_metrics.get_stock_metrics(fav_symbol)
                if metrics:
                    metrics['Symbol'] = fav_symbol
                    results.append(metrics)

            if results:
                df = pd.DataFrame(results)
                st.dataframe(df.style.highlight_max(axis=0)) 

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
            st.success(f"Added {symbol} to your stock pool")
        else:
            st.error(f"Could not verify stock symbol {symbol}")

    def remove_stock(self, symbol):
        if symbol in st.session_state.stock_pool:
            del st.session_state.stock_pool[symbol]
            st.success(f"Removed {symbol} from your stock pool") 