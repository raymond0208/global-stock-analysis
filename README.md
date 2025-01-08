# Stock Financial Metrics Analysis

This Python application fetches and analyzes financial metrics for major tech companies.
Sample code includes Microsoft, Google, ServiceNow, NVIDIA, and Tesla.


## Metrics Calculated
- Working Capital (Current Assets - Current Liabilities)
- Free Cash Flow (Operating Cash Flow - Capital Expenditures)
- Quick Ratio ((Cash + Short Term Investments) / Current Liabilities)
- Current Ratio (Current Assets / Current Liabilities)

## Setup and Installation

1. Create and activate a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python3 stock_analysis.py
```
or 
```bash
python3.12 stock_analysis.py
```

## Output Format
The application will display a formatted table containing:
- Company name
- Working Capital (in millions)
- Free Cash Flow (in millions)
- Quick Ratio
- Current Ratio

## Notes
- All monetary values (Working Capital and Free Cash Flow) are displayed in millions (M)
- The application uses the yfinance library to fetch financial data
- Due to rate limiting, you might need to wait a few seconds between requests