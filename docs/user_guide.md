# Stock Analysis Application — User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Markets](#markets)
4. [Portfolio](#portfolio)
5. [Stock Analysis](#stock-analysis)
6. [Macro Analysis](#macro-analysis)
7. [Settings](#settings)
8. [Understanding the Scoring System](#understanding-the-scoring-system)
9. [Exporting Reports](#exporting-reports)
10. [Tips for Best Use](#tips-for-best-use)

---

## Introduction

The Stock Analysis Application is an all-in-one investment research tool that brings together:

- A live **watchlist** of any stocks from the SG, HK, and US markets
- A **multi-currency portfolio tracker** with FX-adjusted P&L and rebalancing guidance
- Per-stock **technical and fundamental analysis** with downloadable reports
- **Macro-economic indicators** to gauge broader market conditions

All data is fetched in real time from Yahoo Finance and (optionally) the FRED API. No personal financial data is sent to any external server.

---

## Getting Started

### System Requirements

- Python 3.12 or higher
- Internet connection for live data

### Installation

```bash
git clone https://github.com/raymond0208/global-stock-analysis.git
cd global-stock-analysis
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### Navigation

Use the **sidebar** on the left to switch between pages:

| Page | Purpose |
|------|---------|
| Markets | Live index overview and personal watchlist |
| Portfolio | Multi-currency portfolio tracker and analyser |
| Stock Analysis | Deep-dive analysis and report export for any stock |
| Macro Analysis | Federal Reserve and economic indicators |
| Settings | API keys and feature flags |

---

## Markets

The Markets page gives you a live overview of major indices and your personal watchlist.

### Index Overview

Four index cards appear at the top of the page:

| Index | Ticker |
|-------|--------|
| S&P 500 | ^GSPC |
| NASDAQ | ^IXIC |
| Dow Jones | ^DJI |
| VIX (Volatility) | ^VIX |

Each card shows the current price, today's change (absolute and %), and a 1-month sparkline chart. Prices refresh every 5 minutes via cache.

### Watchlist

The watchlist displays all stocks you have added, with the following columns:

| Column | Description |
|--------|-------------|
| Symbol / Company | Ticker and full name |
| Price | Latest price with day-change % (green / red) |
| P/E Ratio | Price-to-earnings ratio |
| ROE % | Return on equity |
| Free Cash Flow | In millions USD |
| Score | Composite analysis score (0–100) |
| Recommendation | Strong Buy / Buy / Hold / Sell / Strong Sell |

Score badges are colour-coded:

| Colour | Score range | Meaning |
|--------|-------------|---------|
| Green | 80–100 | Strong |
| Blue | 60–79 | Good |
| Yellow | 40–59 | Neutral |
| Red | 20–39 | Weak |
| Grey | 0–19 | Poor |

A progress bar ("Analysing {symbol}…") is shown on first load as each stock's metrics are fetched. Subsequent page visits within the same session use the cached results.

### Adding Stocks to the Watchlist

1. Type a symbol or company name (minimum 2 characters) in the search box on the right.
2. Select the stock from the dropdown suggestions.
3. Click **Add to Watchlist**.

Stocks from the SG (`.SI`), HK (`.HK`), and US markets are all supported.

### Removing Stocks

Expand the **Remove holdings** section below the table, tick the stocks to remove, then click **Remove Selected**.

---

## Portfolio

The Portfolio page tracks your personal holdings across SGD, HKD, and USD denominated stocks, with all values normalised to SGD using live FX rates.

### Adding a Holding

1. Expand **Add Holding** (opens automatically when the portfolio is empty).
2. Fill in the form:

| Field | Description |
|-------|-------------|
| Symbol | Stock ticker (e.g. `NVDA`, `9988`, `D05`) |
| Company | Display name |
| Shares | Number of shares held |
| Avg Cost Price | Your average purchase price in the holding's currency |
| Currency | SGD, HKD, or USD |

3. Click **Add Holding**.

Holdings are saved to disk and persist across app restarts.

### Holdings Tab

The Holdings tab shows a summary across four cards at the top:

- **Total Value (SGD)** — current market value converted to SGD
- **Cost Basis (SGD)** — total amount invested, converted to SGD
- **Gain / Loss (SGD)** — unrealised P&L in SGD
- **Return %** — overall percentage return

Below the cards, holdings are grouped by region (SG / HK / US) and show:

| Column | Description |
|--------|-------------|
| Symbol | Ticker |
| Company | Name |
| Currency | SGD / HKD / USD |
| Shares | Units held |
| Avg Cost | Purchase price in local currency |
| Live Price | Current price in local currency |
| Market Value | Current value in local currency |
| Gain / Loss % | Unrealised return (green / red) |

**FX rates** (HKDSGD, USDSGD) are fetched from Yahoo Finance and cached for 5 minutes. If a rate cannot be fetched, sensible defaults are used (1 USD = 1.35 SGD, 1 HKD = 0.173 SGD).

### Analysis Tab

The Analysis tab breaks down portfolio composition:

- **Geographic Exposure** — donut chart showing the split between SG, HK, and US holdings by market value
- **Sector Allocation** — donut chart showing sector weights across all holdings
- **Weighted Score** — portfolio-level composite score (0–100), colour-coded by strength
- **Weighted P/E** — market-cap-weighted P/E ratio
- **Portfolio Beta** — market-cap-weighted beta with a risk label (Low / Medium / High)
- **Position Weights** — horizontal bar chart of each holding's weight; positions above 25% are highlighted in amber with a warning

### Suggested Portfolio Tab

The app calculates a suggested target allocation by scoring each holding and capping any single position at 25%.

- A **grouped bar chart** compares your current weights (grey) against the suggested weights (blue)
- A **rebalancing table** lists the actions needed:

| Column | Description |
|--------|-------------|
| Action | Buy / Sell / Hold badge |
| Stock | Ticker |
| Current % | Present weight |
| Suggested % | Target weight |
| Δ% | Weight difference |
| Est. SGD Δ | Estimated trade value in SGD |

Rows are sorted by the size of the change, largest first.

### Performance Tab

Select a period with the radio buttons: **1M · 3M · 6M · 1Y · All**.

The line chart plots:

| Line | Description |
|------|-------------|
| My Portfolio | Actual historical SGD value of your holdings |
| Suggested Portfolio | Hypothetical value had you followed the suggested weights from the start |
| S&P 500 (normalised) | S&P 500 scaled to your starting portfolio value, as a benchmark |

Hover over any date to see exact SGD values. Return metrics for the selected period are shown below the chart.

---

## Stock Analysis

The Stock Analysis page provides an in-depth analysis of any single stock.

### Searching for a Stock

1. Type a symbol or company name (minimum 2 characters) in the search box.
2. Select the stock from the dropdown.
3. Click **Analyse Stock**.

### Analysis Score and Recommendation

A **Plotly gauge** (0–100) and a **recommendation badge** summarise the stock at a glance:

| Score | Recommendation |
|-------|---------------|
| 80–100 | Strong Buy |
| 65–79 | Buy |
| 50–64 | Hold |
| 35–49 | Sell |
| 0–34 | Strong Sell |

### Technical Analysis

Three interactive line charts (1-year history):

| Chart | Description |
|-------|-------------|
| 20-Day Moving Average | Short-term trend; price above = bullish |
| 50-Day Moving Average | Medium-term trend; crossovers signal potential reversals |
| RSI (14-period) | Above 70 = potentially overbought; below 30 = potentially oversold |

### Profitability Metrics

| Metric | What it means |
|--------|--------------|
| ROE % | Return on equity — higher is better |
| Operating Margin % | Operational efficiency |
| EPS / Price % | Earnings yield — higher suggests better value |
| Quick Ratio | Liquidity; above 1 is healthy |
| Free Cash Flow ($M) | Cash generated after capex; positive and growing is preferred |
| P/E Ratio | Valuation; compare within the same sector |

### Exporting Reports

Two download buttons appear after a stock is analysed:

**Excel Report** (`{SYMBOL}_analysis_{YYYYMMDD}.xlsx`)
- Sheet 1 — Summary: all key metrics
- Sheet 2 — Time Series: daily prices, moving averages, RSI

**PDF Report** (`{SYMBOL}_analysis_{YYYYMMDD}.pdf`)
- Title, date, and full metrics table
- All three technical charts embedded as images
- Suitable for printing or sharing

---

## Macro Analysis

The Macro Analysis page provides a high-level view of the economic environment using data from the Federal Reserve (FRED).

> **Requires a FRED API key.** Enter it in Settings. Free keys are available at [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html).

### Indicators

| Indicator | Description |
|-----------|-------------|
| Federal Funds Rate (%) | Current overnight lending rate set by the Fed |
| GDP Growth Rate (%) | Latest quarter-over-quarter GDP change |
| CPI Year-over-Year (%) | Annual inflation rate |
| Manufacturing PMI | Proxy for manufacturing activity |

### Market Sentiment Score

A composite gauge (0–100) derived from all four indicators, with a plain-English recommendation (e.g. "Moderate risk environment — balanced approach recommended").

The **Detailed Analysis** expander shows the current value, threshold reference, and impact explanation for each indicator.

---

## Settings

The Settings page lets you configure API keys and toggle optional features.

### API Keys

| Key | Feature unlocked |
|-----|-----------------|
| FRED API Key | Macro Analysis page |
| Alpha Vantage Key | Alternative data source |

If either key is missing, a warning banner appears in the sidebar with a link to Settings.

Keys are stored locally and are never committed to the repository.

### Feature Flags

| Flag | Default | Effect |
|------|---------|--------|
| Enable Macro Analysis | On | Shows / hides the Macro Analysis page |

---

## Understanding the Scoring System

Each stock receives a composite score (0–100) calculated from:

- **Technical signals** — moving average trends, RSI position
- **Profitability** — ROE, operating margin
- **Valuation** — P/E ratio, EPS/price ratio
- **Liquidity** — quick ratio
- **Cash generation** — free cash flow

### Score Reference

| Range | Assessment |
|-------|-----------|
| 80–100 | Excellent |
| 65–79 | Good |
| 50–64 | Average |
| 35–49 | Below average |
| 0–34 | Poor |

The same score powers both the watchlist recommendation badges and the portfolio rebalancing algorithm.

---

## Tips for Best Use

1. **Build the watchlist first** — add all stocks you follow on the Markets page before using Portfolio. The watchlist and portfolio share the same scoring engine.

2. **Let the cache warm up** — the first load per session fetches live data for every stock. Subsequent interactions within the same session are instant.

3. **Use the Suggested Portfolio as a guide** — the algorithm caps any single position at 25%. Use the rebalancing table as a starting point, not a mandate.

4. **Export regularly** — PDF and Excel reports are timestamped. Build a folder of monthly snapshots to track how your analysis evolves.

5. **Check Macro Analysis before acting** — a high individual stock score matters less in a high-rate, contracting-GDP environment. Use the sentiment gauge as a sanity check.

6. **Multi-currency note** — live FX rates are cached for 5 minutes. For large portfolios with significant HKD or USD exposure, refresh the page after 5 minutes to get updated SGD totals.

---

## Support

- Browse or open issues: [GitHub Issues](https://github.com/raymond0208/global-stock-analysis/issues)
- Please include your Python version, OS, and a description of the error when reporting bugs.

---

*This application is for informational purposes only and does not constitute financial advice. Always conduct your own research and consult a qualified financial professional before making investment decisions.*
