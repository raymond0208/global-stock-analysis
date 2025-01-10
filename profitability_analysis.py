import yfinance as yf
import pandas as pd
from tabulate import tabulate

# List of companies to analyze (same as other files)
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

def get_profitability_metrics(ticker_symbol):
    """Fetch and calculate profitability metrics for a given company."""
    stock = yf.Ticker(ticker_symbol)
    
    try:
        # Get financial statements
        income_stmt = stock.financials
        balance_sheet = stock.balance_sheet
        
        if income_stmt.empty or balance_sheet.empty:
            print(f"No data available for {ticker_symbol}")
            return None
            
        # Get the most recent values (first column)
        total_revenue = income_stmt.loc['Total Revenue'].iloc[0]
        operating_income = income_stmt.loc['Operating Income'].iloc[0]
        net_income = income_stmt.loc['Net Income'].iloc[0]
        
        # Get balance sheet metrics for ROE and ROA
        total_assets = balance_sheet.loc['Total Assets'].iloc[0]
        
        # Get EPS and current price from stock info
        info = stock.info
        eps = info.get('trailingEps', 0)  # Get trailing twelve months EPS
        current_price = info.get('currentPrice', 0)  # Get current stock price
        
        # Calculate EPS/Price ratio as percentage
        eps_price_ratio = (eps / current_price * 100) if current_price > 0 else 0
        
        # Try different possible keys for stockholder equity
        equity_keys = ['Stockholders Equity', 'Total Stockholder Equity', 'Total Equity']
        total_equity = None
        for key in equity_keys:
            if key in balance_sheet.index:
                total_equity = balance_sheet.loc[key].iloc[0]
                break
                
        if total_equity is None:
            raise ValueError(f"Could not find equity value in balance sheet for {ticker_symbol}")
        
        # Calculate profitability ratios
        operating_margin = (operating_income / total_revenue) * 100
        net_profit_margin = (net_income / total_revenue) * 100
        roe = (net_income / total_equity) * 100
        roa = (net_income / total_assets) * 100
        
        return {
            'Operating Margin (%)': operating_margin,
            'Net Profit Margin (%)': net_profit_margin,
            'ROE (%)': roe,
            'ROA (%)': roa,
            'Net Income ($M)': net_income / 1e6,  # Convert to millions
            'EPS/Price (%)': eps_price_ratio
        }
    except Exception as e:
        print(f"Error processing {ticker_symbol}: {str(e)}")
        return None

def main():
    results = []
    
    # Remove the test_companies line and use the full companies dictionary
    for company_name, ticker in companies.items():
        print(f"Fetching profitability data for {company_name}...")
        metrics = get_profitability_metrics(ticker)
        
        if metrics:
            metrics['Company'] = company_name
            results.append(metrics)
        else:
            print(f"Could not fetch data for {company_name}")
    
    if not results:
        print("No data could be retrieved for any company.")
        return
    
    # Convert results to DataFrame
    df = pd.DataFrame(results)
    
    # Reorder columns to put Company first
    cols = ['Company'] + [col for col in df.columns if col != 'Company']
    df = df[cols]
    
    # Format numeric columns
    for col in df.columns:
        if col != 'Company':
            df[col] = df[col].apply(lambda x: '{:.2f}'.format(x))
    
    # Print the results
    print("\nProfitability Metrics Analysis")
    print("=" * 100)
    print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))
    print("\nNote: Net Income is in millions ($M)")
    print("      ROE = Return on Equity")
    print("      ROA = Return on Assets")
    print("      EPS/Price = (Earnings Per Share / Current Stock Price) %")

if __name__ == "__main__":
    main() 