# Stock Financial Metrics Analysis

This Python application fetches and analyzes financial metrics for major tech companies including Microsoft, Google, ServiceNow, NVIDIA, and Tesla.

## Project Structure
```
stock-report/
├── README.md           # Project documentation
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore patterns
└── stock_analysis.py  # Main application script
└── industry_pe.py      # Industry P/E Ratio calculation
```

## Metrics Calculated
- Working Capital (Current Assets - Current Liabilities)
- Free Cash Flow (Operating Cash Flow - Capital Expenditures)
- Quick Ratio ((Cash + Short Term Investments) / Current Liabilities)
- Current Ratio (Current Assets / Current Liabilities)
- Industry P/E Ratio based on selected stocks(Price per Share / Earnings per Share)

## Prerequisites
- Python 3.12 or higher
- Git (for version control)
- Internet connection (for fetching financial data)

## Setup and Installation

1. Create and activate a virtual environment:
```bash
# Create virtual environment with Python 3.12
python3.12 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

2. Upgrade pip and install required tools:
```bash
python -m pip install --upgrade pip setuptools wheel
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python3.12 stock_analysis.py
python3.12 industry_pe.py
```

## Output Format
The application will display:
1. A formatted table containing:
- Company name
- Working Capital (in millions)
- Free Cash Flow (in millions)
- Quick Ratio
- Current Ratio

2. A list of P/E ratios for the selected stocks
- Trailing Twelve Month P/E ratio
- Forward P/E ratio (Can be configured)


## Troubleshooting

### Virtual Environment Issues
If you encounter issues with package imports or pip:

1. Ensure you're using the correct Python version:
```bash
python --version  # Should show Python 3.12.x
```

2. Verify virtual environment activation:
```bash
# You should see (venv) at the start of your prompt
# If not, reactivate the virtual environment
source venv/bin/activate  # On macOS/Linux
```

3. If problems persist, recreate the virtual environment:
```bash
# Remove old environment
rm -rf venv

# Create new environment
python3.12 -m venv venv

# Activate and install dependencies
source venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## Notes
- All monetary values (Working Capital and Free Cash Flow) are displayed in millions (M)
- The application uses the yfinance library to fetch financial data
- Due to rate limiting, you might need to wait a few seconds between requests
- Make sure you have a stable internet connection when running the application