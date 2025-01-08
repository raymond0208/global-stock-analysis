import yfinance as yf
import pandas as pd
from tabulate import tabulate

# List of companies to analyze
companies = {
    'Microsoft': 'MSFT',
    'Google': 'GOOGL',
    'ServiceNow': 'NOW',
    'NVIDIA': 'NVDA',
    'Tesla': 'TSLA'
}

def get_financial_metrics(ticker_symbol):
    """Fetch and calculate financial metrics for a given company."""
    stock = yf.Ticker(ticker_symbol)
    
    try:
        # Get the most recent financial statements
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cash_flow
        
        if balance_sheet.empty or cash_flow.empty:
            print(f"No data available for {ticker_symbol}")
            return None
        
        # Get the most recent values (first column)
        current_assets = balance_sheet.loc['Current Assets'].iloc[0]
        current_liabilities = balance_sheet.loc['Current Liabilities'].iloc[0]
        cash = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0]
        
        try:
            short_term_investments = balance_sheet.loc['Other Short Term Investments'].iloc[0]
        except:
            short_term_investments = 0
        
        # Get cash flow metrics
        operating_cash_flow = cash_flow.loc['Operating Cash Flow'].iloc[0]
        capital_expenditures = abs(cash_flow.loc['Capital Expenditure'].iloc[0])
        
        # The working capital is already calculated by yfinance
        working_capital = balance_sheet.loc['Working Capital'].iloc[0]
        
        # Calculate other metrics
        free_cash_flow = operating_cash_flow - capital_expenditures
        quick_ratio = (cash + short_term_investments) / current_liabilities
        current_ratio = current_assets / current_liabilities
        
        return {
            'Working Capital': working_capital,
            'Free Cash Flow': free_cash_flow,
            'Quick Ratio': quick_ratio,
            'Current Ratio': current_ratio
        }
    except Exception as e:
        print(f"Error processing {ticker_symbol}: {str(e)}")
        return None

def main():
    results = []
    
    for company_name, ticker in companies.items():
        print(f"Fetching data for {company_name}...")
        metrics = get_financial_metrics(ticker)
        
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
    
    # Format numeric columns (millions for working capital and free cash flow)
    numeric_cols = ['Working Capital', 'Free Cash Flow']
    df[numeric_cols] = df[numeric_cols].apply(lambda x: x.map(lambda v: '{:,.0f}'.format(v/1e6)))
    
    # Add 'M' suffix for millions
    df[numeric_cols] = df[numeric_cols] + 'M'
    
    # Format ratio columns
    ratio_cols = ['Quick Ratio', 'Current Ratio']
    df[ratio_cols] = df[ratio_cols].apply(lambda x: x.map('{:.2f}'.format))
    
    # Print the results
    print("\nFinancial Metrics Analysis")
    print("=" * 80)
    print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))
    print("\nNote: Working Capital and Free Cash Flow are in millions (M)")

if __name__ == "__main__":
    main()