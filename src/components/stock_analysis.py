import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import requests
from src.models.stock_metrics import StockMetrics
import numpy as np
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image
import base64
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


@st.cache_data(ttl=300)
def _fetch_price(symbol: str):
    """5-minute cached current price and day-change."""
    try:
        hist = yf.Ticker(symbol).history(period="5d")
        if hist.empty or len(hist) < 2:
            return None
        cur, prev = hist["Close"].iloc[-1], hist["Close"].iloc[-2]
        return {
            "price":      cur,
            "change_pct": (cur - prev) / prev * 100,
            "change_abs": cur - prev,
        }
    except Exception:
        return None

class StockAnalysisComponent:
    def __init__(self):
        self.stock_metrics = StockMetrics()
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
            st.session_state.selected_stock = None

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
        st.title("Stock Analysis")
        
        # Search functionality
        search_container = st.container()
        with search_container:
            if 'search_query' not in st.session_state:
                st.session_state.search_query = ''
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                default_value = "" if st.session_state.clear_search else st.session_state.get('stock_search_input', '')
                search_query = st.text_input(
                    "Search by Symbol or Company Name",
                    value=default_value,
                    key="stock_search_input",
                    on_change=self.handle_search_change,
                    help="Type to search stocks",
                    label_visibility="visible"
                )
                
                if st.session_state.clear_search:
                    st.session_state.clear_search = False
                
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
                        
                        if selected and isinstance(selected, dict) and selected.get("value"):
                            st.session_state.selected_stock = selected
            
            with col2:
                if st.button("Analyze Stock"):
                    if (st.session_state.selected_stock and 
                        isinstance(st.session_state.selected_stock, dict) and 
                        st.session_state.selected_stock.get("value")):
                        
                        selected_value = st.session_state.selected_stock["value"]
                        if isinstance(selected_value, dict) and "symbol" in selected_value:
                            symbol = selected_value["symbol"]
                            st.session_state.analyzed_symbol = symbol
                            st.session_state.clear_search = True
                            st.session_state.selected_stock = None
                            st.session_state.search_query = ''
                            st.rerun()
                    else:
                        st.warning("Please select a stock first")

        # Display analysis for searched stock
        if hasattr(st.session_state, 'analyzed_symbol'):
            symbol = st.session_state.analyzed_symbol
            metrics = self.stock_metrics.get_stock_metrics(symbol)
            stock_data = self.fetch_stock_data(symbol)

            if metrics and stock_data is not None:
                # ── Perplexity-style stock header ──────────────────────────
                price_data = _fetch_price(symbol)
                if price_data:
                    pos   = price_data["change_pct"] >= 0
                    color = "#16a34a" if pos else "#dc2626"
                    arrow = "↑" if pos else "↓"
                    sign  = "+" if pos else ""
                    st.markdown(
                        f'<div class="sa-sym">{symbol}</div>'
                        f'<div class="sa-price">${price_data["price"]:,.2f}</div>'
                        f'<div class="sa-chg" style="color:{color}">'
                        f'{arrow}&nbsp;{sign}{price_data["change_pct"]:.2f}%'
                        f'&ensp;<span style="color:#94a3b8;font-weight:400;font-size:0.85rem">'
                        f'({sign}${price_data["change_abs"]:,.2f})</span></div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown("<br>", unsafe_allow_html=True)

                # ── Score gauge + recommendation ───────────────────────────
                rec = metrics['Recommendation']
                rec_colors = {
                    "Strong Buy": ("#dcfce7", "#15803d"),
                    "Buy":        ("#dbeafe", "#1d4ed8"),
                    "Hold":       ("#fef9c3", "#854d0e"),
                    "Sell":       ("#fee2e2", "#991b1b"),
                    "Strong Sell":("#fee2e2", "#7f1d1d"),
                }
                rbg, rfg = rec_colors.get(rec, ("#f1f5f9", "#475569"))

                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(
                        self.render_score_gauge(metrics['Score'], f"{symbol} Analysis Score"),
                        use_container_width=True,
                    )
                with col2:
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    st.markdown(
                        f'<span style="background:{rbg};color:{rfg};padding:6px 16px;'
                        f'border-radius:999px;font-size:0.88rem;font-weight:700">'
                        f'Recommendation: {rec}</span>',
                        unsafe_allow_html=True,
                    )

                self.display_detailed_analysis(symbol, stock_data, metrics)

    def create_export_data(self, symbol, metrics, stock_data, ma_20, ma_50, rsi):
        """Create export data dictionary with all analysis results"""
        export_data = {
            'Analysis Date': pd.Timestamp.now().strftime('%Y-%m-%d'),
            'Symbol': symbol,
            'Analysis Score': metrics['Score'],
            'Recommendation': metrics['Recommendation'],
            'ROE (%)': metrics['ROE (%)'],
            'Operating Margin (%)': metrics['Operating Margin (%)'],
            'EPS/Price (%)': metrics['EPS/Price (%)'],
            'Quick Ratio': metrics['Quick Ratio'],
            'Free Cash Flow ($M)': metrics['Free Cash Flow ($M)'],
            'P/E Ratio': metrics['P/E Ratio'],
        }
        
        # Create DataFrames for time series data
        price_df = stock_data[['Close']].copy()
        price_df.columns = ['Stock Price']
        
        ma20_df = ma_20.copy()
        ma20_df.columns = ['20-Day MA']
        
        ma50_df = ma_50.copy()
        ma50_df.columns = ['50-Day MA']
        
        rsi_df = rsi.copy()
        rsi_df.columns = ['RSI']
        
        # Combine all time series data
        time_series_df = pd.concat([price_df, ma20_df, ma50_df, rsi_df], axis=1)
        
        return export_data, time_series_df

    def export_to_excel(self, symbol, export_data, time_series_df):
        """Export data to Excel file with multiple sheets"""
        output = io.BytesIO()
        
        # Convert timezone-aware timestamps to timezone-naive
        time_series_df = time_series_df.copy()
        if time_series_df.index.tz is not None:
            time_series_df.index = time_series_df.index.tz_convert(None)
        else:
            time_series_df.index = time_series_df.index.tz_localize(None)
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Write summary sheet
            summary_df = pd.DataFrame([export_data])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Write time series sheet
            time_series_df.to_excel(writer, sheet_name='Time Series Data')
            
            # Get workbook and add formats
            workbook = writer.book
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D3D3D3',
                'border': 1
            })
            
            # Format Summary sheet
            worksheet = writer.sheets['Summary']
            for col_num, value in enumerate(summary_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 15)
            
            # Format Time Series sheet
            worksheet = writer.sheets['Time Series Data']
            for col_num, value in enumerate(time_series_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 12)
        
        return output.getvalue()

    def create_matplotlib_chart(self, data, title):
        """Create a matplotlib chart for PDF export"""
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(data.index, data['Value'])
        ax.set_title(title)
        ax.set_xlabel('Date')
        ax.set_ylabel('Value')
        ax.grid(True)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Convert plot to PNG image
        img_buffer = io.BytesIO()
        canvas = FigureCanvas(fig)
        canvas.print_png(img_buffer)
        plt.close(fig)  # Close the figure to free memory
        
        return img_buffer.getvalue()

    def export_to_pdf(self, symbol, metrics, stock_data, ma_20, ma_50, rsi):
        """Export analysis results to PDF"""
        pdf_buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Create the story (content) for the PDF
        story = []
        
        # Add title
        story.append(Paragraph(f"Stock Analysis Report - {symbol}", getSampleStyleSheet()['Title']))
        story.append(Spacer(1, 12))
        
        # Add date
        story.append(Paragraph(f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}", getSampleStyleSheet()['Normal']))
        story.append(Spacer(1, 12))
        
        # Add summary metrics
        story.append(Paragraph("Summary Metrics", getSampleStyleSheet()['Heading1']))
        summary_data = [
            ['Metric', 'Value'],
            ['Analysis Score', f"{metrics['Score']:.2f}"],
            ['Recommendation', metrics['Recommendation']],
            ['ROE (%)', f"{metrics['ROE (%)']:.2f}%"],
            ['Operating Margin (%)', f"{metrics['Operating Margin (%)']:.2f}%"],
            ['EPS/Price (%)', f"{metrics['EPS/Price (%)']:.2f}%"],
            ['Quick Ratio', f"{metrics['Quick Ratio']:.2f}"],
            ['Free Cash Flow ($M)', f"${metrics['Free Cash Flow ($M)']:.0f}M"],
            ['P/E Ratio', f"{metrics['P/E Ratio']:.2f}"]
        ]
        
        # Create summary table
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Add charts section header
        story.append(Paragraph("Technical Analysis Charts", getSampleStyleSheet()['Heading1']))
        story.append(Spacer(1, 12))
        
        # Add charts with descriptions
        charts_data = [
            ("20-Day Moving Average", ma_20),
            ("50-Day Moving Average", ma_50),
            ("Relative Strength Index (RSI)", rsi)
        ]
        
        for title, data in charts_data:
            story.append(Paragraph(title, getSampleStyleSheet()['Heading2']))
            story.append(Spacer(1, 6))
            try:
                chart_png = self.create_matplotlib_chart(data, title)
                story.append(Image(io.BytesIO(chart_png), width=450, height=225))
                story.append(Spacer(1, 12))
            except Exception as e:
                story.append(Paragraph(f"Error generating chart: {str(e)}", getSampleStyleSheet()['Normal']))
                story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        return pdf_buffer.getvalue()

    def display_detailed_analysis(self, symbol, stock_data, metrics):
        """Display detailed analysis for a stock"""
        ma_20 = self.calculate_moving_average(stock_data, 20)
        ma_50 = self.calculate_moving_average(stock_data, 50)
        rsi = self.calculate_rsi(stock_data)

        if not ma_20.empty and not ma_50.empty and not rsi.empty:
            with st.expander("Technical Analysis", expanded=True):
                st.markdown("### 20-Day Moving Average")
                st.plotly_chart(self.create_line_chart(ma_20, "20-Day Moving Average"), use_container_width=True)
                st.markdown("### 50-Day Moving Average")
                st.plotly_chart(self.create_line_chart(ma_50, "50-Day Moving Average"), use_container_width=True)
                st.markdown("### Relative Strength Index (RSI)")
                st.plotly_chart(self.create_line_chart(rsi, "RSI"), use_container_width=True)

            with st.expander("Profitability Metrics", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("ROE (%)", f"{metrics['ROE (%)']:.2f}%")
                    st.metric("Operating Margin (%)", f"{metrics['Operating Margin (%)']:.2f}%")
                    st.metric("EPS/Price (%)", f"{metrics['EPS/Price (%)']:.2f}%")
                with col2:
                    st.metric("Quick Ratio", f"{metrics['Quick Ratio']:.2f}")
                    st.metric("Free Cash Flow", f"${metrics['Free Cash Flow ($M)']:.0f}M")
                    st.metric("P/E Ratio", f"{metrics['P/E Ratio']:.2f}")
            
            # Export functionality
            st.markdown("---")
            st.subheader("Export Analysis")
            
            # Create export data
            export_data, time_series_df = self.create_export_data(symbol, metrics, stock_data, ma_20, ma_50, rsi)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Export Excel
                excel_data = self.export_to_excel(symbol, export_data, time_series_df)
                st.download_button(
                    label="Download Excel Report",
                    data=excel_data,
                    file_name=f"{symbol}_analysis_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            with col2:
                # Export PDF
                pdf_data = self.export_to_pdf(symbol, metrics, stock_data, ma_20, ma_50, rsi)
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_data,
                    file_name=f"{symbol}_analysis_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )

