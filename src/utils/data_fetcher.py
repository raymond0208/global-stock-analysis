import yfinance as yf

class DataFetcher:
    def get_stock_info(self, symbol):
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            return {
                'name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'country': info.get('country', '')
            }
        except Exception as e:
            print(f"Error fetching info for {symbol}: {str(e)}")
            return None 