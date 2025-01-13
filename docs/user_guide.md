# Stock Analysis Application - User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Features](#features)
4. [Using the Application](#using-the-application)
5. [Understanding the Analysis](#understanding-the-analysis)
6. [Exporting Reports](#exporting-reports)

## Introduction
The Stock Analysis Application is a powerful tool that helps you analyze stocks using various technical and financial metrics. It provides real-time data analysis, visualization, and reporting capabilities to help you make informed investment decisions.

## Getting Started

### System Requirements
- Python 3.12 or higher
- Internet connection for real-time stock data

### Installation
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   streamlit run src/main.py
   ```

## Features
- Real-time stock search and analysis
- Technical analysis indicators
- Financial metrics evaluation
- Export capabilities (Excel and PDF)
- Interactive charts and visualizations

## Using the Application

### Searching for Stocks
1. Enter a stock symbol or company name in the search bar
2. As you type (minimum 2 characters), matching suggestions will appear
3. Select a stock from the dropdown list
4. Click "Analyze Stock" to view the analysis

### Stock Analysis Components

#### Analysis Score
- A gauge showing the overall analysis score (0-100)
- Color-coded for quick assessment:
  - Red (0-35): High Risk
  - Orange (35-50): Moderate Risk
  - Yellow (50-65): Neutral
  - Light Green (65-80): Good
  - Green (80-100): Excellent

#### Technical Analysis
The technical analysis section includes three key indicators:

1. **20-Day Moving Average**
   - Shows short-term price trends
   - Helps identify immediate support/resistance levels

2. **50-Day Moving Average**
   - Shows medium-term price trends
   - Used for identifying broader market trends

3. **Relative Strength Index (RSI)**
   - Measures momentum and overbought/oversold conditions
   - Scale of 0-100:
     - Above 70: Potentially overbought
     - Below 30: Potentially oversold

#### Profitability Metrics
Key financial metrics displayed:
- ROE (Return on Equity)
- Operating Margin
- EPS/Price Ratio
- Quick Ratio
- Free Cash Flow
- P/E Ratio

## Understanding the Analysis

### Analysis Score Interpretation
- **90-100**: Excellent investment potential
- **80-89**: Strong performance
- **65-79**: Good performance
- **50-64**: Average performance
- **35-49**: Below average
- **0-34**: Poor performance

### Technical Indicators
- **Moving Averages**: Help identify trends
  - Price above MA: Bullish trend
  - Price below MA: Bearish trend
  - Crossovers: Potential trend changes

- **RSI (Relative Strength Index)**
  - Above 70: Stock might be overvalued
  - Below 30: Stock might be undervalued
  - 40-60: Neutral zone

### Financial Metrics
- **ROE**: Higher is better, indicates efficient use of equity
- **Operating Margin**: Higher indicates better operational efficiency
- **EPS/Price**: Higher ratio suggests better value
- **Quick Ratio**: Above 1 indicates good short-term liquidity
- **Free Cash Flow**: Positive and growing is preferred
- **P/E Ratio**: Lower might indicate better value (industry dependent)

## Exporting Reports

### Excel Report
Click "Download Excel Report" to get a detailed spreadsheet containing:
- **Summary Sheet**: All key metrics and analysis results
- **Time Series Data**: Historical data including:
  - Stock prices
  - Moving averages
  - RSI values

### PDF Report
Click "Download PDF Report" to get a comprehensive report including:
- Analysis summary
- All technical charts
- Financial metrics
- Date and time of analysis

The PDF report is ideal for:
- Sharing analysis with others
- Keeping historical records
- Printing physical copies

### Report Naming Convention
Both Excel and PDF reports are named using the format:
```
{SYMBOL}_analysis_{YYYYMMDD}.{extension}
```
Example: `AAPL_analysis_20240320.pdf`

## Tips for Best Use
1. **Regular Analysis**: Monitor stocks regularly for trend changes
2. **Compare Metrics**: Look at multiple metrics before making decisions
3. **Export Reports**: Save reports to track performance over time
4. **Technical + Fundamental**: Use both technical and fundamental metrics for balanced analysis

## Support
For technical support or questions, please:
1. Check the GitHub repository issues section
2. Create a new issue if needed
3. Provide detailed information about your problem

---

*Note: This application is for informational purposes only and should not be considered as financial advice. Always do your own research and consult with financial professionals before making investment decisions.* 