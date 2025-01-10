import yfinance as yf
import pandas as pd
from tabulate import tabulate
from profitability_analysis import get_profitability_metrics
from stock_cash_analysis import get_financial_metrics
from industry_pe import get_tech_pe_ratios

# List of companies to analyze
companies = {
    'Microsoft': 'MSFT',
    'Google': 'GOOGL',
    'ServiceNow': 'NOW',
    'NVIDIA': 'NVDA',
    'Tesla': 'TSLA',
    'Apple': 'AAPL',
    'Amazon': 'AMZN',
    'Meta': 'META',
    'NVIDIA': 'NVDA',
    'Intel': 'INTC',
    'Advanced Micro Devices': 'AMD',
    'Adobe': 'ADBE',
    'Salesforce': 'CRM'
}

def get_recommendation_score(profitability_metrics, financial_metrics, pe_ratio, avg_pe):
    """Calculate a recommendation score based on all metrics"""
    score = 0
    max_score = 100
    
    # Profitability Metrics (40% of total score)
    if profitability_metrics:
        # ROE Score (15%)
        roe = float(profitability_metrics['ROE (%)'])
        if roe > 20: score += 15
        elif roe > 15: score += 12
        elif roe > 10: score += 8
        elif roe > 5: score += 4
        
        # Operating Margin Score (15%)
        op_margin = float(profitability_metrics['Operating Margin (%)'])
        if op_margin > 25: score += 15
        elif op_margin > 20: score += 12
        elif op_margin > 15: score += 8
        elif op_margin > 10: score += 4
        
        # EPS/Price Score (10%)
        eps_price = float(profitability_metrics['EPS/Price (%)'])
        if eps_price > 5: score += 10
        elif eps_price > 3: score += 8
        elif eps_price > 2: score += 5
        elif eps_price > 1: score += 2

    # Liquidity Metrics (30% of total score)
    if financial_metrics:
        # Quick Ratio Score (15%)
        quick_ratio = float(financial_metrics['Quick Ratio'])
        if quick_ratio > 2: score += 15
        elif quick_ratio > 1.5: score += 12
        elif quick_ratio > 1: score += 8
        elif quick_ratio > 0.5: score += 4
        
        # Free Cash Flow Score (15%)
        fcf = float(financial_metrics['Free Cash Flow']) / 1e6  # Convert to millions
        if fcf > 10000: score += 15
        elif fcf > 5000: score += 12
        elif fcf > 1000: score += 8
        elif fcf > 0: score += 4

    # Valuation Metrics (30% of total score)
    if pe_ratio and pe_ratio > 0:
        # P/E Ratio relative to industry average
        pe_score = 30 * (1 - (pe_ratio / avg_pe))
        if pe_score > 0:
            score += min(30, pe_score)

    return score

def get_recommendation(score):
    if score >= 80: return "Strong Buy"
    elif score >= 65: return "Buy"
    elif score >= 50: return "Hold"
    elif score >= 35: return "Sell"
    else: return "Strong Sell"

def main():
    results = []
    
    # Get industry average P/E
    pe_df, avg_pe = get_tech_pe_ratios()
    
    for company_name, ticker in companies.items():
        print(f"Analyzing {company_name}...")
        
        # Gather all metrics
        profitability = get_profitability_metrics(ticker)
        financial = get_financial_metrics(ticker)
        pe_ratio = pe_df.loc[ticker]['P/E Ratio'] if ticker in pe_df.index else None
        
        if profitability and financial and pe_ratio:
            score = get_recommendation_score(profitability, financial, pe_ratio, avg_pe)
            recommendation = get_recommendation(score)
            
            results.append({
                'Company': company_name,
                'Score': score,
                'Recommendation': recommendation,
                'P/E Ratio': pe_ratio,
                'ROE (%)': profitability['ROE (%)'],
                'Quick Ratio': financial['Quick Ratio'],
                'EPS/Price (%)': profitability['EPS/Price (%)']
            })
    
    # Create and format DataFrame
    df = pd.DataFrame(results)
    df = df.sort_values('Score', ascending=False)
    
    # Format numeric columns
    df['Score'] = df['Score'].apply(lambda x: f"{x:.1f}")
    df['P/E Ratio'] = df['P/E Ratio'].apply(lambda x: f"{x:.1f}")
    
    print("\nStock Recommendations Analysis")
    print("=" * 100)
    print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))
    print("\nRecommendation Criteria:")
    print("Strong Buy  : Score >= 80")
    print("Buy         : Score >= 65")
    print("Hold        : Score >= 50")
    print("Sell        : Score >= 35")
    print("Strong Sell : Score < 35")

if __name__ == "__main__":
    main() 