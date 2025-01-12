import streamlit as st
import pandas as pd
from fredapi import Fred
from src.utils.config_manager import ConfigManager

class MacroMetrics:
    def __init__(self):
        config = ConfigManager()
        self.fred = Fred(api_key=config.get_api_key('fred_api_key'))
        
    def _safe_get_series(self, series_id, name):
        try:
            data = self.fred.get_series(series_id)
            return data.iloc[-1] if not data.empty else None
        except Exception as e:
            print(f"Error fetching {name}: {str(e)}")  # Debug output
            return None

    def get_macro_metrics(self):
        try:
            # Updated series IDs
            ffr = self._safe_get_series('FEDFUNDS', 'Federal Funds Rate')  # Changed from DFF
            gdp = self._safe_get_series('GDP', 'GDP')  # Changed from GDPC1
            cpi = self._safe_get_series('CPIAUCSL', 'CPI')
            pmi = self._safe_get_series('MANEMP', 'Manufacturing Employment')  # Changed from ISM

            if None in [ffr, gdp, cpi, pmi]:
                print("One or more metrics returned None")  # Debug output
                return None

            # Calculate GDP growth rate
            gdp_series = self.fred.get_series('GDP')
            gdp_growth = ((gdp_series.iloc[-1] - gdp_series.iloc[-2]) / gdp_series.iloc[-2]) * 100

            # Calculate CPI YoY change
            cpi_series = self.fred.get_series('CPIAUCSL')
            cpi_yoy = ((cpi_series.iloc[-1] - cpi_series.iloc[-13]) / cpi_series.iloc[-13]) * 100

            return {
                'Federal_Funds_Rate': ffr,
                'GDP_Growth': gdp_growth,
                'CPI_YoY': cpi_yoy,
                'Manufacturing_PMI': pmi
            }
        except Exception as e:
            print(f"Error in get_macro_metrics: {str(e)}")  # Debug output
            return None

    def calculate_market_score(self, metrics):
        # Simple scoring system (0-100)
        score = 50  # Neutral starting point
        
        # Adjust based on metrics
        if metrics['GDP_Growth'] > 2:
            score += 10
        elif metrics['GDP_Growth'] < 0:
            score -= 15
            
        if metrics['CPI_YoY'] < 2:
            score += 10
        elif metrics['CPI_YoY'] > 5:
            score -= 15
            
        if metrics['Manufacturing_PMI'] > 50:
            score += 10
        else:
            score -= 10
            
        return max(0, min(100, score))  # Ensure score is between 0 and 100

    def get_macro_recommendation(self, metrics):
        score = self.calculate_market_score(metrics)
        if score >= 80:
            return "Very Bullish"
        elif score >= 60:
            return "Bullish"
        elif score >= 40:
            return "Neutral"
        elif score >= 20:
            return "Bearish"
        else:
            return "Very Bearish" 