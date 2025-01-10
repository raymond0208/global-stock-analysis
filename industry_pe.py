import yfinance as yf
import pandas as pd

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

def get_tech_pe_ratios():
    # List of major US tech companies and their ticker symbols, inline with industry_pe.py stocks.
    
    # Create a dictionary to store P/E ratios
    pe_ratios = {}
    
    for company_name, ticker in companies.items():
        try:
            stock = yf.Ticker(ticker)
            print(f"Fetching profitability data for {company_name}...")

            #pe_ratio = stock.info.get('forwardPE')  # Get forward next 12 months P/E ratio
            pe_ratio = stock.info.get('trailingPE')  # Get Trailing Twelve Month(TTM) P/E ratio

            if pe_ratio and pe_ratio > 0:  # Only include positive P/E ratios
                pe_ratios[ticker] = pe_ratio
            else:
                print(f"No valid P/E ratio found for {ticker}")
                print("-" * 40)  # Add a separator line
        except Exception as e:
            print(f"Error processing {ticker}: {str(e)}")
            print("-" * 40)  # Add a separator line
            continue
    
    # Convert to DataFrame for better visualization
    df = pd.DataFrame.from_dict(pe_ratios, orient='index', columns=['P/E Ratio'])
    df.index.name = 'Ticker'
    
    # Calculate average P/E ratio
    avg_pe = df['P/E Ratio'].mean()
    
    return df, avg_pe

# Run the analysis
df, avg_pe = get_tech_pe_ratios()

# Print results
print("\nP/E Ratios for Major Tech Companies:")
print(df)
print(f"\nAverage P/E Ratio: {avg_pe:.2f}")