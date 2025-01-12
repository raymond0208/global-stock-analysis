import yfinance as yf
import pandas as pd

class StockMetrics:
    def get_stock_metrics(self, symbol):
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # Calculate metrics
            metrics = {
                'Score': self._calculate_score(info),
                'ROE (%)': info.get('returnOnEquity', 0) * 100,
                'Operating Margin (%)': info.get('operatingMargins', 0) * 100,
                'EPS/Price (%)': (info.get('trailingEps', 0) / info.get('currentPrice', 1)) * 100,
                'Quick Ratio': info.get('quickRatio', 0),
                'Free Cash Flow ($M)': info.get('freeCashflow', 0) / 1000000,
                'P/E Ratio': info.get('trailingPE', 0)
            }
            
            metrics['Recommendation'] = self._get_recommendation(metrics['Score'])
            return metrics
            
        except Exception as e:
            print(f"Error fetching metrics for {symbol}: {str(e)}")
            return None
            
    def _calculate_score(self, info):
        score = 50  # Base score
        
        # ROE Impact
        roe = info.get('returnOnEquity', 0)
        if roe > 0.2: score += 10
        elif roe > 0.15: score += 5
        elif roe < 0: score -= 10
        
        # Operating Margin Impact
        op_margin = info.get('operatingMargins', 0)
        if op_margin > 0.5: score += 10
        elif op_margin > 0.2: score += 5
        elif op_margin < 0: score -= 10
        
        # P/E Ratio Impact
        pe = info.get('trailingPE', 0)
        if 0 < pe < 20: score += 10
        elif 20 <= pe < 30: score += 5
        elif pe > 50: score -= 10
        
        return max(0, min(100, score))  # Ensure score is between 0 and 100
        
    def _get_recommendation(self, score):
        if score >= 80: return "Strong Buy"
        elif score >= 60: return "Buy"
        elif score >= 40: return "Hold"
        elif score >= 20: return "Sell"
        else: return "Strong Sell" 