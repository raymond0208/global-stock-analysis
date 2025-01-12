import json
import os

class StorageManager:
    def __init__(self):
        self.data_dir = "data"
        self.ensure_data_directory()
        self.stock_pool_file = os.path.join(self.data_dir, "stock_pool.json")
        self.favorite_stocks_file = os.path.join(self.data_dir, "favorite_stocks.json")

    def ensure_data_directory(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def save_stock_pool(self, stock_pool):
        with open(self.stock_pool_file, 'w') as f:
            json.dump(stock_pool, f)

    def load_stock_pool(self):
        if os.path.exists(self.stock_pool_file):
            with open(self.stock_pool_file, 'r') as f:
                return json.load(f)
        return {}

    def save_favorite_stocks(self, favorite_stocks):
        with open(self.favorite_stocks_file, 'w') as f:
            json.dump(favorite_stocks, f)

    def load_favorite_stocks(self):
        if os.path.exists(self.favorite_stocks_file):
            with open(self.favorite_stocks_file, 'r') as f:
                return json.load(f)
        return []