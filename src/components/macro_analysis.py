import streamlit as st
import plotly.graph_objects as go
from src.models.macro_metrics import MacroMetrics

class MacroAnalysisComponent:
    def __init__(self):
        self.macro_metrics = MacroMetrics()

    def render_gauge(self, value, title, min_val=0, max_val=100):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            title={'text': title},
            gauge={
                'axis': {'range': [min_val, max_val]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 20], 'color': "red"},
                    {'range': [20, 40], 'color': "orange"},
                    {'range': [40, 60], 'color': "yellow"},
                    {'range': [60, 80], 'color': "lightgreen"},
                    {'range': [80, 100], 'color': "green"}
                ]
            }
        ))
        fig.update_layout(height=300)
        return fig

    def render(self):
        st.title("Macro-Economic Analysis")
        
        try:
            # Get macro metrics
            with st.spinner("Fetching macro-economic data..."):
                metrics = self.macro_metrics.get_macro_metrics()
            
            if not metrics:
                st.error("Unable to fetch macro-economic data. Please check your FRED API key in Settings.")
                return
            
            # Create columns for metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Federal Funds Rate", f"{metrics['Federal_Funds_Rate']:.2f}%")
                st.metric("GDP Growth Rate", f"{metrics['GDP_Growth']:.2f}%")
            
            with col2:
                st.metric("CPI Year-over-Year", f"{metrics['CPI_YoY']:.2f}%")
                st.metric("Manufacturing PMI", f"{metrics['Manufacturing_PMI']:.1f}")

            # Calculate and display market sentiment
            sentiment = self.macro_metrics.get_macro_recommendation(metrics)
            score = self.macro_metrics.calculate_market_score(metrics)
            
            st.subheader("Market Sentiment Analysis")
            st.plotly_chart(self.render_gauge(score, "Market Sentiment Score"))
            st.info(f"Current Market Sentiment: {sentiment}")

            # Display detailed analysis
            st.subheader("Detailed Analysis")
            with st.expander("View Analysis"):
                self._render_detailed_analysis(metrics)
        except Exception as e:
            st.error(f"Error rendering macro analysis: {str(e)}")

    def _render_detailed_analysis(self, metrics):
        analysis = {
            "Federal Funds Rate": {
                "value": metrics['Federal_Funds_Rate'],
                "impact": "Higher rates typically indicate tighter monetary policy, which can slow economic growth but help control inflation.",
                "threshold": "Current target range is typically between 0-5%"
            },
            "CPI (Inflation)": {
                "value": metrics['CPI_YoY'],
                "impact": "High inflation can erode purchasing power and lead to tighter monetary policy.",
                "threshold": "Fed's target is around 2%"
            },
            "GDP Growth": {
                "value": metrics['GDP_Growth'],
                "impact": "Indicates overall economic health and expansion/contraction.",
                "threshold": "Healthy growth is typically 2-3%"
            },
            "Manufacturing PMI": {
                "value": metrics['Manufacturing_PMI'],
                "impact": "Above 50 indicates expansion, below 50 indicates contraction.",
                "threshold": "50 is the neutral point"
            }
        }

        for metric, data in analysis.items():
            st.markdown(f"**{metric}**")
            st.markdown(f"Current Value: {data['value']:.2f}")
            st.markdown(f"Impact: {data['impact']}")
            st.markdown(f"Threshold: {data['threshold']}")
            st.markdown("---") 