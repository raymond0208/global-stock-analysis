import streamlit as st

# Must be the very first Streamlit call
st.set_page_config(
    page_title="Stock Analyzer",
    page_icon="📈",
    layout="wide"
)

# ── Global CSS (Perplexity Finance-inspired) ──────────────────────────────
st.markdown("""
<style>
/* ── Reset & base ── */
.stApp { background-color: #f8fafc; }
#MainMenu, footer { visibility: hidden; }
header { visibility: hidden; }
.block-container { padding-top: 1.25rem; padding-bottom: 2rem; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
}
[data-testid="stSidebar"] hr { border-color: #e2e8f0; }

/* ── Index card text (rendered via st.markdown HTML) ── */
.idx-label {
    font-size: 0.68rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.idx-price {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
    margin: 3px 0 2px;
    font-variant-numeric: tabular-nums;
}
.idx-change {
    font-size: 0.78rem;
    font-weight: 600;
}

/* ── Section heading ── */
.sec-head {
    font-size: 0.72rem;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    margin: 1.4rem 0 0.55rem;
    padding-bottom: 6px;
    border-bottom: 1px solid #e2e8f0;
}

/* ── Watchlist table ── */
.wl-table {
    width: 100%;
    border-collapse: collapse;
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
}
.wl-table th {
    text-align: left;
    padding: 7px 14px;
    font-size: 0.67rem;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    border-bottom: 1px solid #e2e8f0;
    background: #f8fafc;
}
.wl-table td {
    padding: 11px 14px;
    border-bottom: 1px solid #f1f5f9;
    vertical-align: middle;
}
.wl-table tr:last-child td { border-bottom: none; }
.wl-table tr:hover td { background: #f8fafc; }
.wl-sym  { font-size: 0.92rem; font-weight: 700; color: #0f172a; }
.wl-corp { font-size: 0.75rem; color: #94a3b8; margin-top: 1px; }
.wl-price { font-size: 0.95rem; font-weight: 600; color: #0f172a;
             font-variant-numeric: tabular-nums; }
.wl-chg  { font-size: 0.78rem; font-weight: 600; margin-top: 2px;
             font-variant-numeric: tabular-nums; }
.wl-meta { font-size: 0.73rem; color: #94a3b8; line-height: 1.65; }

/* ── Score badge ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    white-space: nowrap;
}

/* ── Stock analysis page header ── */
.sa-sym   { font-size: 0.72rem; font-weight: 700; color: #64748b;
             text-transform: uppercase; letter-spacing: 0.08em; }
.sa-price { font-size: 2.1rem; font-weight: 700; color: #0f172a;
             font-variant-numeric: tabular-nums; margin: 4px 0 2px; }
.sa-chg   { font-size: 0.95rem; font-weight: 600; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

from src.main import StockAnalyzerApp

app = StockAnalyzerApp()
app.run()
