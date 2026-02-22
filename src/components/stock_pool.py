import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import requests
from src.models.stock_metrics import StockMetrics
from src.utils.data_fetcher import DataFetcher


# ── Module-level cached data helpers ─────────────────────────────────────

@st.cache_data(ttl=300)
def _fetch_index(symbol: str):
    """Return price, day-change and 1-month close history for a market index."""
    try:
        hist = yf.Ticker(symbol).history(period="1mo")
        if hist.empty or len(hist) < 2:
            return None
        cur, prev = hist["Close"].iloc[-1], hist["Close"].iloc[-2]
        return {
            "price":      cur,
            "change_pct": (cur - prev) / prev * 100,
            "change_abs": cur - prev,
            "history":    hist["Close"].tolist(),
        }
    except Exception:
        return None


@st.cache_data(ttl=300)
def _fetch_price(symbol: str):
    """Return current price and day-change for a single stock."""
    try:
        hist = yf.Ticker(symbol).history(period="5d")
        if hist.empty or len(hist) < 2:
            return None
        cur, prev = hist["Close"].iloc[-1], hist["Close"].iloc[-2]
        return {
            "price":      cur,
            "change_pct": (cur - prev) / prev * 100,
            "change_abs": cur - prev,
        }
    except Exception:
        return None


# ── Component ─────────────────────────────────────────────────────────────

class StockPoolComponent:
    _INDICES = [
        ("S&P 500",   "^GSPC"),
        ("NASDAQ",    "^IXIC"),
        ("Dow Jones", "^DJI"),
        ("VIX",       "^VIX"),
    ]

    def __init__(self):
        self.stock_metrics = StockMetrics()
        self.data_fetcher  = DataFetcher()
        if "stock_pool" not in st.session_state:
            st.session_state.stock_pool = {}
        if "clear_search" not in st.session_state:
            st.session_state.clear_search = False

    # ── Search / Add / Remove ─────────────────────────────────────────────

    def search_stocks(self, query):
        if not query or len(query) < 2:
            return []
        try:
            url = (
                "https://query1.finance.yahoo.com/v1/finance/search"
                f"?q={query}&quotesCount=20&newsCount=0&enableFuzzyQuery=false"
            )
            data = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).json()
            out = []
            for q in data.get("quotes", []):
                sym, name = q.get("symbol", ""), q.get("longname", "")
                if (sym and name
                        and not any(x in sym for x in ["-", "^", "="])
                        and isinstance(sym, str) and isinstance(name, str)):
                    out.append({"label": f"{sym} - {name}",
                                "value": {"symbol": sym, "name": name}})
            return out
        except Exception as e:
            print(f"Error searching stocks: {e}")
            return []

    def handle_search_change(self):
        if "stock_search_input" in st.session_state:
            st.session_state.search_query = st.session_state.stock_search_input
            st.session_state.selected_stock = None

    def add_stock(self, symbol, name):
        if symbol in st.session_state.stock_pool:
            st.warning(f"{symbol} is already in your watchlist")
            return False
        st.session_state.stock_pool[symbol] = name
        if hasattr(st.session_state, "storage_manager"):
            st.session_state.storage_manager.save_stock_pool(st.session_state.stock_pool)
        return True

    def remove_stock(self, symbol):
        if symbol in st.session_state.stock_pool:
            del st.session_state.stock_pool[symbol]
            if hasattr(st.session_state, "storage_manager"):
                st.session_state.storage_manager.save_stock_pool(st.session_state.stock_pool)
            st.session_state.show_remove_message = f"Removed {symbol} from your watchlist"
            if "stock_metrics_results" in st.session_state:
                del st.session_state.stock_metrics_results
            st.rerun()

    # ── Rendering helpers ─────────────────────────────────────────────────

    @staticmethod
    def _sparkline(history: list, positive: bool) -> go.Figure:
        color = "#16a34a" if positive else "#dc2626"
        fill  = "rgba(22,163,74,0.10)" if positive else "rgba(220,38,38,0.10)"
        fig = go.Figure(go.Scatter(
            y=history, mode="lines",
            line=dict(color=color, width=1.5),
            fill="tozeroy", fillcolor=fill,
        ))
        fig.update_layout(
            height=55,
            margin=dict(l=0, r=0, t=2, b=0),
            xaxis=dict(visible=False, fixedrange=True),
            yaxis=dict(visible=False, fixedrange=True),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        return fig

    @staticmethod
    def _badge_style(score: float):
        if score >= 80:
            return "#dcfce7", "#15803d"
        if score >= 60:
            return "#dbeafe", "#1d4ed8"
        if score >= 40:
            return "#fef9c3", "#854d0e"
        if score >= 20:
            return "#fee2e2", "#991b1b"
        return "#f1f5f9", "#475569"

    # ── Section: market indices ───────────────────────────────────────────

    def _render_indices(self):
        st.markdown('<div class="sec-head">Index Movement</div>', unsafe_allow_html=True)
        cols = st.columns(4, gap="small")
        for (name, sym), col in zip(self._INDICES, cols):
            with col:
                with st.container(border=True):
                    data = _fetch_index(sym)
                    if data:
                        pos   = data["change_pct"] >= 0
                        color = "#16a34a" if pos else "#dc2626"
                        arrow = "↑" if pos else "↓"
                        sign  = "+" if pos else ""
                        st.markdown(
                            f'<div class="idx-label">{name}</div>'
                            f'<div class="idx-price">{data["price"]:,.2f}</div>'
                            f'<div class="idx-change" style="color:{color}">'
                            f'{arrow}&nbsp;{sign}{data["change_pct"]:.2f}%'
                            f'&ensp;<span style="color:#cbd5e1;font-weight:400">'
                            f'{sign}{data["change_abs"]:,.2f}</span></div>',
                            unsafe_allow_html=True,
                        )
                        st.plotly_chart(
                            self._sparkline(data["history"], pos),
                            use_container_width=True,
                            config={"displayModeBar": False},
                        )
                    else:
                        st.caption(f"{name} — unavailable")

    # ── Section: watchlist table ──────────────────────────────────────────

    def _render_watchlist(self, df: pd.DataFrame):
        st.markdown('<div class="sec-head">Your Watchlist</div>', unsafe_allow_html=True)

        prices = {sym: _fetch_price(sym) for sym in df["Symbol"]}

        rows = ""
        for _, row in df.iterrows():
            sym   = row["Symbol"]
            corp  = row["Company"]
            score = float(row.get("Score", 0) or 0)
            rec   = row.get("Recommendation", "—")
            pe    = row.get("P/E Ratio", 0) or 0
            roe   = row.get("ROE (%)", 0) or 0
            fcf   = row.get("Free Cash Flow ($M)", 0) or 0

            pd_  = prices.get(sym)
            if pd_:
                price_str = f"${pd_['price']:,.2f}"
                pos       = pd_["change_pct"] >= 0
                chg_color = "#16a34a" if pos else "#dc2626"
                chg_str   = f"{'↑' if pos else '↓'} {'+' if pos else ''}{pd_['change_pct']:.2f}%"
            else:
                price_str = "—"
                chg_color = "#94a3b8"
                chg_str   = ""

            bg, fg = self._badge_style(score)

            rows += (
                f'<tr>'
                f'  <td><div class="wl-sym">{sym}</div>'
                f'      <div class="wl-corp">{corp}</div></td>'
                f'  <td><div class="wl-price">{price_str}</div>'
                f'      <div class="wl-chg" style="color:{chg_color}">{chg_str}</div></td>'
                f'  <td class="wl-meta">P/E&nbsp;{pe:.1f}<br>ROE&nbsp;{roe:.1f}%<br>'
                f'      FCF&nbsp;${fcf:,.0f}M</td>'
                f'  <td><span class="badge" style="background:{bg};color:{fg}">'
                f'      {score:.0f}&nbsp;·&nbsp;{rec}</span></td>'
                f'</tr>'
            )

        st.markdown(
            f'<table class="wl-table">'
            f'<thead><tr>'
            f'  <th>Stock</th><th>Price / Change</th>'
            f'  <th>Key Metrics</th><th>Score</th>'
            f'</tr></thead>'
            f'<tbody>{rows}</tbody>'
            f'</table>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander("Remove stocks from watchlist"):
            sel = st.multiselect(
                "Select to remove",
                options=df["Symbol"].tolist(),
                format_func=lambda x: f"{x} — {st.session_state.stock_pool.get(x, '')}",
            )
            if st.button("Remove selected", type="primary"):
                for s in sel:
                    self.remove_stock(s)

    # ── Section: add-to-watchlist panel ──────────────────────────────────

    def _render_add_panel(self):
        st.markdown('<div class="sec-head">Add to Watchlist</div>', unsafe_allow_html=True)
        with st.container(border=True):
            if "search_query" not in st.session_state:
                st.session_state.search_query = ""

            default_val = (
                "" if st.session_state.clear_search
                else st.session_state.get("stock_search_input", "")
            )
            query = st.text_input(
                "Symbol or company name",
                value=default_val,
                key="stock_search_input",
                on_change=self.handle_search_change,
                label_visibility="collapsed",
                placeholder="Search e.g. AAPL or Apple",
            )
            if st.session_state.clear_search:
                st.session_state.clear_search = False

            if "selected_stock" not in st.session_state:
                st.session_state.selected_stock = None

            if query and len(query) >= 2:
                suggestions = self.search_stocks(query)
                if suggestions:
                    sel = st.selectbox(
                        "Pick a stock",
                        options=[{"label": "Select…", "value": None}] + suggestions,
                        format_func=lambda x: (
                            x["label"] if isinstance(x, dict) and x.get("label")
                            else "Select…"
                        ),
                        key="stock_selector",
                        label_visibility="collapsed",
                    )
                    if sel and isinstance(sel, dict) and sel.get("value"):
                        st.session_state.selected_stock = sel

            if st.button("Add to Watchlist", type="primary", use_container_width=True):
                sel = st.session_state.selected_stock
                if sel and isinstance(sel, dict) and sel.get("value"):
                    v = sel["value"]
                    if isinstance(v, dict) and "symbol" in v and "name" in v:
                        if self.add_stock(v["symbol"], v["name"]):
                            st.success(f"Added {v['symbol']}")
                            st.session_state.clear_search = True
                            st.session_state.selected_stock = None
                            st.session_state.search_query = ""
                            if "stock_metrics_results" in st.session_state:
                                del st.session_state.stock_metrics_results
                            st.rerun()
                else:
                    st.warning("Select a stock first")

        # Pool size info
        n = len(st.session_state.stock_pool)
        if n:
            st.caption(f"{n} stock{'s' if n != 1 else ''} in your watchlist")

    # ── Main entry point ──────────────────────────────────────────────────

    def render(self):
        st.title("Markets")

        if "show_remove_message" in st.session_state:
            st.success(st.session_state.show_remove_message)
            del st.session_state.show_remove_message

        # ── Market indices strip ──
        self._render_indices()
        st.markdown("---")

        # ── Two-column layout: watchlist (left) + add panel (right) ──
        left, right = st.columns([3, 1], gap="large")

        with right:
            self._render_add_panel()

        with left:
            if not st.session_state.stock_pool:
                st.info(
                    "Your watchlist is empty. "
                    "Search for a stock on the right and click **Add to Watchlist**."
                )
                return

            # Load (or use cached) metrics
            if "stock_metrics_results" not in st.session_state:
                pool = list(st.session_state.stock_pool.items())
                bar  = st.progress(0, text="Loading watchlist…")
                results = []
                for i, (sym, name) in enumerate(pool):
                    bar.progress((i + 1) / len(pool), text=f"Analysing {sym}…")
                    m = self.stock_metrics.get_stock_metrics(sym)
                    if m:
                        m["Symbol"]  = sym
                        m["Company"] = name
                        results.append(m)
                bar.empty()
                st.session_state.stock_metrics_results = results

            results = st.session_state.stock_metrics_results
            if not results:
                st.warning("Could not load metrics. Check your internet connection.")
                return

            try:
                df = pd.DataFrame(results).copy()
                df = df[df["Symbol"].isin(st.session_state.stock_pool.keys())]
                if not df.empty:
                    self._render_watchlist(df)
            except Exception as e:
                st.error(f"Error displaying watchlist: {e}")
                if "stock_metrics_results" in st.session_state:
                    del st.session_state.stock_metrics_results
