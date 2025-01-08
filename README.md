# Stock Financial Metrics Analysis

This Python application fetches and analyzes financial metrics for major tech companies including Microsoft, Google, ServiceNow, NVIDIA, and Tesla.

## Project Structure
```
stock-report/
├── README.md           # Project documentation
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore patterns
└── stock_analysis.py  # Main application script
```

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
- Make sure you have a stable internet connection when running the application
- The .gitignore file is configured to exclude:
  - Virtual environment (venv/)
  - Python cache files (__pycache__/)
  - IDE specific files (.idea/, .vscode/)
  - Log files and OS-specific files

## Troubleshooting
If you encounter issues:
1. Ensure your virtual environment is activated
2. Verify all dependencies are installed correctly
3. Check your internet connection
4. Try running the script again after a few minutes if you encounter rate limiting