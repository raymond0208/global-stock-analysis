import yfinance as yf
import pandas as pd

def get_tech_pe_ratios():
    tech_companies = {
        'AAPL': 'Apple',
        'MSFT': 'Microsoft',
        'GOOGL': 'Alphabet',
        'META': 'Meta',
        'NVDA': 'NVIDIA'
    }
    
    pe_data = {}
    for symbol in tech_companies.keys():
        try:
            stock = yf.Ticker(symbol)
            pe_data[symbol] = {'P/E Ratio': stock.info.get('forwardPE', 0)}
        except:
            continue
    
    pe_df = pd.DataFrame.from_dict(pe_data, orient='index')
    avg_pe = pe_df['P/E Ratio'].mean()
    
    return pe_df, avg_pe 