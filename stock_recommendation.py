import yfinance as yf
import pandas as pd
from tabulate import tabulate
from profitability_analysis import get_profitability_metrics
from stock_cash_analysis import get_financial_metrics
from industry_pe import get_tech_pe_ratios
import requests
from datetime import datetime, timedelta
from fredapi import Fred
from alpha_vantage.timeseries import TimeSeries
from config import FRED_API_KEY, ALPHA_VANTAGE_KEY

# Import API configurations
from config import FRED_API_KEY, ALPHA_VANTAGE_KEY
fred = Fred(api_key=FRED_API_KEY)

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
    'Salesforce': 'CRM',
    'Palantir': 'PLTR'
}

def get_macro_metrics():
    """Fetch macro-economic indicators from FRED and Alpha Vantage"""
    try:
        # Get Federal Funds Rate (FFR)
        ffr_series = fred.get_series('FEDFUNDS')
        ffr = ffr_series.iloc[-1]  # Use iloc for position-based indexing
        
        # Get CPI Year-over-Year change
        cpi_series = fred.get_series('CPIAUCSL', frequency='m')  # Monthly frequency
        cpi_yoy = cpi_series.pct_change(12).iloc[-1] * 100  # Calculate YoY change
        
        # Get GDP Growth Rate (Real GDP, Quarterly, Percent Change)
        gdp_series = fred.get_series('GDPC1', frequency='q')  # Quarterly frequency
        gdp_growth = gdp_series.pct_change().iloc[-1] * 100
        
        # Get Unemployment Rate
        unemp_series = fred.get_series('UNRATE', frequency='m')  # Monthly frequency
        unemployment = unemp_series.iloc[-1]
        
        # Get Manufacturing PMI using requests directly
        pmi_url = f"https://www.alphavantage.co/query?function=ECONOMIC_INDICATOR&symbol=ISM_MAN_PMI&apikey={ALPHA_VANTAGE_KEY}"
        response = requests.get(pmi_url)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                pmi = float(data['data'][0]['value'])  # Get latest PMI value
            else:
                print("PMI data not available in expected format")
                pmi = 50  # Use neutral PMI value as fallback
        else:
            print(f"Failed to fetch PMI data: Status code {response.status_code}")
            pmi = 50  # Use neutral PMI value as fallback
        
        macro_data = {
            'Federal_Funds_Rate': ffr,
            'CPI_YoY': cpi_yoy,
            'GDP_Growth': gdp_growth,
            'Unemployment': unemployment,
            'Manufacturing_PMI': pmi
        }
        
        # Validate all values are numbers
        for key, value in macro_data.items():
            if not isinstance(value, (int, float)):
                print(f"Warning: {key} has invalid value: {value}")
                return None
        
        return macro_data
        
    except Exception as e:
        print(f"Error fetching macro data: {str(e)}")
        return None

def get_recommendation_score(profitability_metrics, financial_metrics, pe_ratio, avg_pe):
    """Calculate a recommendation score based on company metrics"""
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
        quick_ratio = round(quick_ratio, 2)
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

def get_macro_recommendation(macro_metrics):
    """Analyze macro-economic conditions and provide market sentiment"""
    if not macro_metrics:
        return "No macro data available"
    
    score = 0
    max_score = 100
    
    # Federal Funds Rate impact (25 points)
    ffr = macro_metrics['Federal_Funds_Rate']
    if ffr < 3: score += 25
    elif ffr < 4: score += 20
    elif ffr < 5: score += 15
    elif ffr < 6: score += 10
    
    # CPI impact (25 points)
    cpi = macro_metrics['CPI_YoY']
    if cpi < 2: score += 25
    elif cpi < 3: score += 20
    elif cpi < 4: score += 15
    elif cpi < 5: score += 10
    
    # PMI impact (20 points)
    pmi = macro_metrics['Manufacturing_PMI']
    if pmi > 55: score += 20
    elif pmi > 50: score += 15
    elif pmi > 45: score += 10
    
    # GDP Growth impact (30 points)
    gdp = macro_metrics['GDP_Growth']
    if gdp > 3: score += 30
    elif gdp > 2: score += 25
    elif gdp > 1: score += 15
    elif gdp > 0: score += 10
    
    # Determine market sentiment
    if score >= 80:
        return "Strongly Bullish Market"
    elif score >= 60:
        return "Bullish Market"
    elif score >= 40:
        return "Neutral Market"
    elif score >= 20:
        return "Bearish Market"
    else:
        return "Strongly Bearish Market"

def main():
    results = []
    
    # Get macro economic data and analysis
    print("Analyzing Macro-Economic Conditions...")
    macro_metrics = get_macro_metrics()
    market_sentiment = get_macro_recommendation(macro_metrics)
    
    # Display macro analysis
    print("\nMacro-Economic Analysis")
    print("=" * 80)
    if macro_metrics:
        print(f"Federal Funds Rate: {macro_metrics['Federal_Funds_Rate']:.2f}%")
        print(f"CPI Year-over-Year: {macro_metrics['CPI_YoY']:.2f}%")
        print(f"GDP Growth Rate: {macro_metrics['GDP_Growth']:.2f}%")
        print(f"Manufacturing PMI: {macro_metrics['Manufacturing_PMI']:.1f}")
        print(f"\nMarket Sentiment: {market_sentiment}")
    else:
        print("Could not fetch macro-economic data")
    
    print("\n" + "=" * 80)
    
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
                'ROE (%)': f"{profitability['ROE (%)']:.2f}",
                'Quick Ratio': f"{financial['Quick Ratio']:.2f}",
                'EPS/Price (%)': f"{profitability['EPS/Price (%)']:.2f}"
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