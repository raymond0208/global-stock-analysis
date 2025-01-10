# Default API keys (for development only)
FRED_API_KEY = ""
ALPHA_VANTAGE_KEY = ""

try:
    from local_config import *
except ImportError:
    pass 