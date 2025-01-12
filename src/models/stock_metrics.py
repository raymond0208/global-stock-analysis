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
        score = 0  # Start from 0 instead of base 50
        
        # Profitability Metrics (40% of total score)
        # ROE Score (15%)
        roe = info.get('returnOnEquity', 0) * 100
        if roe > 20: score += 15
        elif roe > 15: score += 12
        elif roe > 10: score += 8
        elif roe > 5: score += 4
        
        # Operating Margin Score (15%)
        op_margin = info.get('operatingMargins', 0) * 100
        if op_margin > 25: score += 15
        elif op_margin > 20: score += 12
        elif op_margin > 15: score += 8
        elif op_margin > 10: score += 4
        
        # EPS/Price Score (10%)
        eps_price = (info.get('trailingEps', 0) / info.get('currentPrice', 1)) * 100
        if eps_price > 5: score += 10
        elif eps_price > 3: score += 8
        elif eps_price > 2: score += 5
        elif eps_price > 1: score += 2
        
        # Liquidity Metrics (30% of total score)
        # Quick Ratio Score (15%)
        quick_ratio = info.get('quickRatio', 0)
        if quick_ratio > 2: score += 15
        elif quick_ratio > 1.5: score += 12
        elif quick_ratio > 1: score += 8
        elif quick_ratio > 0.5: score += 4
        
        # Free Cash Flow Score (15%)
        fcf = info.get('freeCashflow', 0) / 1000000  # Convert to millions
        if fcf > 10000: score += 15
        elif fcf > 5000: score += 12
        elif fcf > 1000: score += 8
        elif fcf > 0: score += 4
        
        # P/E Ratio Valuation Score (30% of total score)
        pe = info.get('trailingPE', 0)
        if 0 < pe < 15: score += 30
        elif 15 <= pe < 20: score += 25
        elif 20 <= pe < 25: score += 20
        elif 25 <= pe < 30: score += 15
        elif 30 <= pe < 40: score += 10
        elif 40 <= pe < 50: score += 5
        
        return max(0, min(100, score))  # Ensure score is between 0 and 100
        
    def _get_recommendation(self, score):
        if score >= 80: return "Strong Buy"
        elif score >= 60: return "Buy"
        elif score >= 40: return "Hold"
        elif score >= 20: return "Sell"
        else: return "Strong Sell" 