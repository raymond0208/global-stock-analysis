import io
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta

from src.models.portfolio_metrics import PortfolioMetrics
from src.models.stock_metrics import StockMetrics


# ── Module-level cached helpers ───────────────────────────────────────────────

@st.cache_data(ttl=300)
def _fetch_price(symbol: str):
    """Return current price and day-change for a single stock (local currency)."""
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


@st.cache_data(ttl=300)
def _fetch_fx(pair: str):
    """Fetch latest FX rate. pair e.g. 'HKDSGD=X', 'USDSGD=X'.
    Returns float (SGD per 1 unit of foreign currency) or None.
    """
    try:
        hist = yf.Ticker(pair).history(period="5d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception:
        return None


@st.cache_data(ttl=600)
def _fetch_info(symbol: str):
    """Return {sector, beta, longName} from yfinance."""
    try:
        info = yf.Ticker(symbol).info
        return {
            "sector":   info.get("sector") or "Unknown",
            "beta":     info.get("beta"),
            "longName": info.get("longName") or symbol,
        }
    except Exception:
        return None


@st.cache_data(ttl=86400)
def _fetch_history(symbol: str, period: str = "1y"):
    """Fetch Close price history as a timezone-naive pd.Series."""
    try:
        hist = yf.Ticker(symbol).history(period=period)
        if hist.empty:
            return None
        s = hist["Close"]
        if s.index.tz is not None:
            s.index = s.index.tz_convert(None)
        return s
    except Exception:
        return None


# ── Phillip Securities PDF parser ────────────────────────────────────────────

def _parse_phillip_pdf(pdf_bytes: bytes) -> list:
    """Parse Phillip Securities Holdings PDF.

    Column layout (0-indexed):
      0 = Company name / exchange section header ("SG","HK","US") / totals
      1 = Stock Code
      2 = Quantity on Hand (a)   → shares
      3 = Traded Curr             → currency
      4 = Average Cost Price      → purchase_price
      5–10 = ignored (fetched live from yfinance)

    Returns list of {symbol, company, shares, purchase_price, currency}.
    """
    try:
        import pdfplumber
    except ImportError:
        st.error("pdfplumber not installed. Run: pip install pdfplumber")
        return []

    holdings = []
    current_exchange = "US"  # default

    def _clean_float(val) -> float:
        if val is None:
            return 0.0
        s = str(val).replace(",", "").strip()
        try:
            return float(s)
        except ValueError:
            return 0.0

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    for row in table:
                        if not row or len(row) < 5:
                            continue

                        col0 = str(row[0] or "").strip()
                        col1 = str(row[1] or "").strip()

                        # Detect exchange section headers
                        if col0 in {"SG", "HK", "US"} and not col1:
                            current_exchange = col0
                            continue

                        # Skip header rows, total rows, blank rows
                        if not col1:
                            continue
                        if "Stock Code" in col1 or "TOTAL" in col0.upper() or "GRAND" in col0.upper():
                            continue
                        if col1 in {"Stock Code", "Code"}:
                            continue

                        # Parse the holding
                        company       = col0 or col1
                        raw_symbol    = col1
                        shares        = _clean_float(row[2] if len(row) > 2 else None)
                        currency      = str(row[3] or "").strip() if len(row) > 3 else ""
                        purchase_price = _clean_float(row[4] if len(row) > 4 else None)

                        if shares <= 0:
                            continue
                        if not currency:
                            # Infer currency from exchange
                            currency = {"SG": "SGD", "HK": "HKD", "US": "USD"}.get(current_exchange, "USD")

                        # Symbol normalisation
                        if current_exchange == "SG":
                            symbol = raw_symbol + ".SI"
                        elif current_exchange == "HK":
                            symbol = raw_symbol.zfill(4) + ".HK"
                        else:
                            symbol = raw_symbol  # US: as-is

                        holdings.append({
                            "symbol":         symbol,
                            "company":        company,
                            "shares":         shares,
                            "purchase_price": purchase_price,
                            "currency":       currency,
                        })
    except Exception as e:
        st.error(f"Error parsing PDF: {e}")

    return holdings


# ── Main component ────────────────────────────────────────────────────────────

class PortfolioComponent:

    _PERIOD_MAP = {
        "1M":  "1mo",
        "3M":  "3mo",
        "6M":  "6mo",
        "1Y":  "1y",
        "All": "1y",   # No purchase dates stored; default to 1Y
    }

    def __init__(self):
        self.pm = PortfolioMetrics()
        self.sm = StockMetrics()
        self._init_session_state()

    def _init_session_state(self):
        if "portfolio" not in st.session_state:
            st.session_state.portfolio = (
                st.session_state.storage_manager.load_portfolio()
            )
        if "pdf_preview" not in st.session_state:
            st.session_state.pdf_preview = None

    # ── FX rates helper ───────────────────────────────────────────────────

    def _get_fx_rates(self) -> dict:
        hkd = _fetch_fx("HKDSGD=X") or 0.173
        usd = _fetch_fx("USDSGD=X") or 1.35
        return {"HKD": hkd, "USD": usd, "SGD": 1.0}

    # ── Prices helper ─────────────────────────────────────────────────────

    def _get_prices_local(self, holdings: list) -> dict:
        return {h["symbol"]: (_fetch_price(h["symbol"]) or {}).get("price") for h in holdings}

    # ── Tab 1: Holdings ───────────────────────────────────────────────────

    def _tab_holdings(self):
        holdings = st.session_state.portfolio.get("holdings", [])

        # ── Summary cards ──
        if holdings:
            fx_rates     = self._get_fx_rates()
            prices_local = self._get_prices_local(holdings)
            total_sgd    = self.pm.get_portfolio_value_sgd(holdings, prices_local, fx_rates)
            cost_sgd     = self.pm.get_cost_basis_sgd(holdings, fx_rates)
            gain_sgd     = total_sgd - cost_sgd
            gain_pct     = (gain_sgd / cost_sgd * 100) if cost_sgd > 0 else 0.0

            cols = st.columns(4, gap="small")
            cards = [
                ("Total Value (SGD)",  f"S${total_sgd:,.2f}", None),
                ("Cost Basis (SGD)",   f"S${cost_sgd:,.2f}",  None),
                ("Gain / Loss (SGD)",  f"{'+'if gain_sgd>=0 else ''}{gain_sgd:,.2f}", gain_sgd),
                ("Return %",          f"{'+'if gain_pct>=0 else ''}{gain_pct:.2f}%", gain_pct),
            ]
            for col, (label, value, sign) in zip(cols, cards):
                with col:
                    with st.container(border=True):
                        color = ("#16a34a" if sign is not None and sign >= 0
                                 else "#dc2626" if sign is not None and sign < 0
                                 else "#0f172a")
                        st.markdown(
                            f'<div style="font-size:0.75rem;color:#64748b;margin-bottom:4px">{label}</div>'
                            f'<div style="font-size:1.2rem;font-weight:700;color:{color}">{value}</div>',
                            unsafe_allow_html=True,
                        )

        # ── Import / Manual entry ──
        left, right = st.columns([2, 1], gap="large")

        with right:
            st.markdown('<div class="sec-head">Import PDF</div>', unsafe_allow_html=True)
            with st.container(border=True):
                uploaded = st.file_uploader(
                    "Phillip Securities PDF",
                    type=["pdf"],
                    label_visibility="collapsed",
                )
                if uploaded and st.button("Parse PDF", type="primary", use_container_width=True):
                    parsed = _parse_phillip_pdf(uploaded.read())
                    if parsed:
                        st.session_state.pdf_preview = parsed
                        st.success(f"Parsed {len(parsed)} holdings — review below.")
                    else:
                        st.warning("No holdings found. Check the PDF format.")

            if st.session_state.pdf_preview:
                st.markdown('<div class="sec-head">Review & Confirm</div>', unsafe_allow_html=True)
                df_preview = pd.DataFrame(st.session_state.pdf_preview)
                df_edited  = st.data_editor(
                    df_preview,
                    use_container_width=True,
                    num_rows="dynamic",
                    key="pdf_editor",
                )
                if st.button("Confirm & Save", type="primary", use_container_width=True):
                    new_holdings = df_edited.to_dict("records")
                    # Coerce numeric types
                    for h in new_holdings:
                        h["shares"]         = float(h.get("shares", 0) or 0)
                        h["purchase_price"] = float(h.get("purchase_price", 0) or 0)
                    st.session_state.portfolio = {"holdings": new_holdings}
                    st.session_state.storage_manager.save_portfolio(st.session_state.portfolio)
                    st.session_state.pdf_preview = None
                    st.success("Portfolio saved!")
                    st.rerun()

            st.markdown('<div class="sec-head">Add Manually</div>', unsafe_allow_html=True)
            with st.container(border=True):
                with st.form("add_holding_form", clear_on_submit=True):
                    sym      = st.text_input("Symbol", placeholder="e.g. 0700.HK")
                    company  = st.text_input("Company", placeholder="e.g. TENCENT HOLDINGS")
                    shares   = st.number_input("Shares", min_value=0.0, step=1.0)
                    price    = st.number_input("Avg Cost Price", min_value=0.0, step=0.01)
                    currency = st.selectbox("Currency", ["SGD", "HKD", "USD"])
                    if st.form_submit_button("Add Holding", type="primary", use_container_width=True):
                        if sym and shares > 0:
                            entry = {
                                "symbol":         sym.strip().upper(),
                                "company":        company.strip() or sym.strip().upper(),
                                "shares":         float(shares),
                                "purchase_price": float(price),
                                "currency":       currency,
                            }
                            st.session_state.portfolio["holdings"].append(entry)
                            st.session_state.storage_manager.save_portfolio(st.session_state.portfolio)
                            st.success(f"Added {entry['symbol']}")
                            st.rerun()
                        else:
                            st.warning("Enter a symbol and shares.")

        # ── Holdings table ──
        with left:
            if not holdings:
                st.info("No holdings yet. Import a Phillip Securities PDF or add manually.")
                return

            fx_rates     = self._get_fx_rates()
            prices_local = self._get_prices_local(holdings)

            # Group by currency / region
            regions = {"SGD": "SG", "HKD": "HK", "USD": "US"}
            grouped: dict[str, list] = {"SG": [], "HK": [], "US": []}
            for h in holdings:
                r = regions.get(h["currency"], "US")
                grouped[r].append(h)

            rows_html = ""
            to_delete = []

            for region, region_holdings in grouped.items():
                if not region_holdings:
                    continue
                ccy_color = {"SG": "#3b82f6", "HK": "#f59e0b", "US": "#10b981"}.get(region, "#94a3b8")
                rows_html += (
                    f'<tr style="background:#f8fafc">'
                    f'  <td colspan="8">'
                    f'    <span style="font-size:0.7rem;font-weight:700;color:{ccy_color};'
                    f'    letter-spacing:0.05em;text-transform:uppercase">'
                    f'    {region} Exchange</span>'
                    f'  </td>'
                    f'</tr>'
                )
                for h in region_holdings:
                    sym    = h["symbol"]
                    ccy    = h["currency"]
                    p_data = _fetch_price(sym)
                    price_local = p_data["price"] if p_data else None
                    value_local = (price_local * h["shares"]) if price_local else None
                    value_sgd   = (
                        self.pm.get_sgd_price(price_local * h["shares"], ccy, fx_rates)
                        if price_local is not None else None
                    )
                    gl_pct = (
                        (price_local - h["purchase_price"]) / h["purchase_price"] * 100
                        if h["purchase_price"] and price_local is not None else None
                    )

                    ccy_sym = {"SGD": "S$", "HKD": "HK$", "USD": "US$"}.get(ccy, "$")

                    price_str = f"{ccy_sym}{price_local:,.3f}" if price_local else "—"
                    value_str = f"{ccy_sym}{value_local:,.2f}" if value_local else "—"
                    gl_str    = ""
                    gl_color  = "#64748b"
                    if gl_pct is not None:
                        gl_color = "#16a34a" if gl_pct >= 0 else "#dc2626"
                        gl_str   = f"{'+'if gl_pct>=0 else ''}{gl_pct:.1f}%"

                    rows_html += (
                        f'<tr>'
                        f'  <td><div class="wl-sym">{sym}</div></td>'
                        f'  <td><div class="wl-corp">{h["company"]}</div></td>'
                        f'  <td style="text-align:right">{ccy}</td>'
                        f'  <td style="text-align:right">{h["shares"]:,.0f}</td>'
                        f'  <td style="text-align:right">{ccy_sym}{h["purchase_price"]:,.3f}</td>'
                        f'  <td style="text-align:right">{price_str}</td>'
                        f'  <td style="text-align:right">{value_str}</td>'
                        f'  <td style="text-align:right;color:{gl_color}">{gl_str}</td>'
                        f'</tr>'
                    )
                    to_delete.append(sym)

            st.markdown(
                f'<table class="wl-table">'
                f'<thead><tr>'
                f'  <th>Symbol</th><th>Company</th><th>CCY</th><th>Shares</th>'
                f'  <th>Avg Cost</th><th>Live Price</th><th>Mkt Value</th><th>G/L %</th>'
                f'</tr></thead>'
                f'<tbody>{rows_html}</tbody>'
                f'</table>',
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)

            with st.expander("Remove holdings"):
                sel = st.multiselect(
                    "Select to remove",
                    options=[h["symbol"] for h in holdings],
                    format_func=lambda x: f"{x} — {next((h['company'] for h in holdings if h['symbol']==x), x)}",
                )
                if st.button("Remove selected", type="primary"):
                    new_holdings = [h for h in holdings if h["symbol"] not in sel]
                    st.session_state.portfolio = {"holdings": new_holdings}
                    st.session_state.storage_manager.save_portfolio(st.session_state.portfolio)
                    st.rerun()

    # ── Tab 2: Analysis ───────────────────────────────────────────────────

    def _tab_analysis(self):
        holdings = st.session_state.portfolio.get("holdings", [])
        if not holdings:
            st.info("Add holdings in the Holdings tab first.")
            return

        fx_rates     = self._get_fx_rates()
        prices_local = self._get_prices_local(holdings)

        # Build info map
        info_map   = {h["symbol"]: _fetch_info(h["symbol"]) for h in holdings}
        sector_map = {sym: (info_map[sym] or {}).get("sector", "Unknown") for sym in info_map}
        beta_map   = {sym: (info_map[sym] or {}).get("beta") for sym in info_map}

        # Allocation data
        region_alloc = self.pm.get_region_allocation(holdings, prices_local, fx_rates)
        sector_alloc = self.pm.get_sector_allocation(holdings, prices_local, fx_rates, sector_map)
        weights      = self.pm.get_weights(holdings, prices_local, fx_rates)

        # ── Row 1: Donut charts ──
        col_geo, col_sec = st.columns(2, gap="large")

        with col_geo:
            st.markdown('<div class="sec-head">Geographic Exposure</div>', unsafe_allow_html=True)
            if region_alloc:
                colors = {"SG": "#3b82f6", "HK": "#f59e0b", "US": "#10b981"}
                fig = go.Figure(go.Pie(
                    labels=list(region_alloc.keys()),
                    values=list(region_alloc.values()),
                    hole=0.55,
                    marker_colors=[colors.get(r, "#94a3b8") for r in region_alloc],
                    textinfo="label+percent",
                    hovertemplate="%{label}: %{value:.1f}%<extra></extra>",
                ))
                fig.update_layout(
                    height=280,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=True,
                    legend=dict(orientation="h", y=-0.1),
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with col_sec:
            st.markdown('<div class="sec-head">Sector Allocation</div>', unsafe_allow_html=True)
            if sector_alloc:
                sorted_sec = sorted(sector_alloc.items(), key=lambda x: x[1], reverse=True)
                fig = go.Figure(go.Pie(
                    labels=[s[0] for s in sorted_sec],
                    values=[s[1] for s in sorted_sec],
                    hole=0.55,
                    textinfo="label+percent",
                    hovertemplate="%{label}: %{value:.1f}%<extra></extra>",
                ))
                fig.update_layout(
                    height=280,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=True,
                    legend=dict(orientation="h", y=-0.1),
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # ── Row 2: Weighted metric cards ──
        st.markdown("---")
        metric_map = {}
        for h in holdings:
            sym = h["symbol"]
            m = self.sm.get_stock_metrics(sym)
            if m:
                metric_map[sym] = m

        w_score = self.pm.get_weighted_metric(holdings, prices_local, fx_rates, metric_map, "Score")
        w_pe    = self.pm.get_weighted_metric(holdings, prices_local, fx_rates, metric_map, "P/E Ratio")

        # Weighted beta
        w_beta = 0.0
        for sym, w in weights.items():
            b = beta_map.get(sym)
            if b is not None:
                w_beta += w * float(b)

        def _badge_style(score):
            if score >= 80: return "#dcfce7", "#15803d"
            if score >= 60: return "#dbeafe", "#1d4ed8"
            if score >= 40: return "#fef9c3", "#854d0e"
            if score >= 20: return "#fee2e2", "#991b1b"
            return "#f1f5f9", "#475569"

        if w_beta < 0.8:
            beta_label, beta_color = "Low Risk",  "#16a34a"
        elif w_beta < 1.3:
            beta_label, beta_color = "Medium Risk", "#d97706"
        else:
            beta_label, beta_color = "High Risk",  "#dc2626"

        m_cols = st.columns(3, gap="small")
        bg, fg = _badge_style(w_score)
        with m_cols[0]:
            with st.container(border=True):
                st.markdown(
                    f'<div style="font-size:0.75rem;color:#64748b">Weighted Score</div>'
                    f'<span class="badge" style="background:{bg};color:{fg};font-size:1rem">'
                    f'{w_score:.0f}</span>',
                    unsafe_allow_html=True,
                )
        with m_cols[1]:
            with st.container(border=True):
                st.markdown(
                    f'<div style="font-size:0.75rem;color:#64748b">Weighted P/E</div>'
                    f'<div style="font-size:1.1rem;font-weight:700;color:#0f172a">{w_pe:.1f}x</div>',
                    unsafe_allow_html=True,
                )
        with m_cols[2]:
            with st.container(border=True):
                st.markdown(
                    f'<div style="font-size:0.75rem;color:#64748b">Portfolio Beta</div>'
                    f'<div style="font-size:1.1rem;font-weight:700;color:#0f172a">{w_beta:.2f} '
                    f'<span style="font-size:0.75rem;color:{beta_color};font-weight:600">'
                    f'{beta_label}</span></div>',
                    unsafe_allow_html=True,
                )

        # ── Row 3: Weight bar chart + concentration warning ──
        st.markdown("---")
        st.markdown('<div class="sec-head">Position Weights</div>', unsafe_allow_html=True)

        if weights:
            sorted_w = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:15]
            syms   = [s[0] for s in sorted_w]
            pcts   = [s[1] * 100 for s in sorted_w]
            colors_bar = ["#f59e0b" if p > 25 else "#3b82f6" for p in pcts]

            fig = go.Figure(go.Bar(
                x=pcts, y=syms, orientation="h",
                marker_color=colors_bar,
                text=[f"{p:.1f}%" for p in pcts],
                textposition="outside",
                hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
            ))
            fig.add_vline(x=25, line_dash="dash", line_color="#ef4444", line_width=1)
            fig.update_layout(
                height=max(300, len(syms) * 28),
                margin=dict(l=80, r=60, t=20, b=20),
                xaxis=dict(title="Weight (%)", showgrid=False),
                yaxis=dict(autorange="reversed"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Concentration warning
            over_cap = [(sym, pct) for sym, pct in zip(syms, pcts) if pct > 25]
            if over_cap:
                msgs = ", ".join(f"**{sym}** ({pct:.1f}%)" for sym, pct in over_cap)
                st.warning(
                    f"Concentration warning: {msgs} exceed the 25% cap. "
                    "See Suggested Portfolio tab for rebalancing recommendations."
                )

    # ── Tab 3: Suggested Portfolio ────────────────────────────────────────

    def _tab_suggested(self):
        holdings = st.session_state.portfolio.get("holdings", [])
        if not holdings:
            st.info("Add holdings in the Holdings tab first.")
            return

        fx_rates     = self._get_fx_rates()
        prices_local = self._get_prices_local(holdings)

        # Candidate pool = holdings + watchlist
        holding_syms = [h["symbol"] for h in holdings]
        watchlist    = list(st.session_state.get("stock_pool", {}).keys())
        candidates   = list(dict.fromkeys(holding_syms + watchlist))  # deduplicate, preserve order

        # Fetch scores (cached in session state)
        cache_key = "portfolio_scores"
        if cache_key not in st.session_state:
            st.session_state[cache_key] = {}

        scores = {}
        missing = [c for c in candidates if c not in st.session_state[cache_key]]
        if missing:
            bar = st.progress(0, text="Loading scores…")
            for i, sym in enumerate(missing):
                bar.progress((i + 1) / len(missing), text=f"Scoring {sym}…")
                m = self.sm.get_stock_metrics(sym)
                st.session_state[cache_key][sym] = (m or {}).get("Score", 0)
            bar.empty()

        for c in candidates:
            scores[c] = st.session_state[cache_key].get(c, 0)

        suggested_weights = self.pm.suggest_weights(candidates, scores, cap=0.25)
        total_sgd         = self.pm.get_portfolio_value_sgd(holdings, prices_local, fx_rates)
        actions           = self.pm.get_rebalancing_actions(
            holdings, prices_local, fx_rates, suggested_weights, total_sgd
        )

        # ── Grouped bar chart ──
        st.markdown('<div class="sec-head">Current vs Suggested Weights</div>', unsafe_allow_html=True)

        current_w = self.pm.get_weights(holdings, prices_local, fx_rates)
        chart_syms = sorted(
            [a["symbol"] for a in actions],
            key=lambda s: suggested_weights.get(s, 0),
            reverse=True,
        )[:20]

        cur_pcts = [current_w.get(s, 0) * 100 for s in chart_syms]
        sug_pcts = [suggested_weights.get(s, 0) * 100 for s in chart_syms]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Current", x=cur_pcts, y=chart_syms, orientation="h",
            marker_color="#94a3b8",
            hovertemplate="%{y} current: %{x:.1f}%<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            name="Suggested", x=sug_pcts, y=chart_syms, orientation="h",
            marker_color="#3b82f6",
            hovertemplate="%{y} suggested: %{x:.1f}%<extra></extra>",
        ))
        fig.add_vline(x=25, line_dash="dash", line_color="#ef4444", line_width=1)
        fig.update_layout(
            barmode="group",
            height=max(350, len(chart_syms) * 32),
            margin=dict(l=80, r=60, t=20, b=20),
            xaxis=dict(title="Weight (%)", showgrid=False),
            yaxis=dict(autorange="reversed"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=1.05),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # ── Rebalancing table ──
        st.markdown('<div class="sec-head">Rebalancing Actions</div>', unsafe_allow_html=True)

        action_colors = {"Buy": ("#dcfce7", "#15803d"), "Sell": ("#fee2e2", "#991b1b"), "Hold": ("#f1f5f9", "#475569")}
        rows_html = ""
        for a in sorted(actions, key=lambda x: abs(x["delta_pct"]), reverse=True):
            bg, fg = action_colors.get(a["action"], ("#f1f5f9", "#475569"))
            sign   = "+" if a["delta_pct"] >= 0 else ""
            rows_html += (
                f'<tr>'
                f'  <td><span class="badge" style="background:{bg};color:{fg}">{a["action"]}</span></td>'
                f'  <td><div class="wl-sym">{a["symbol"]}</div>'
                f'      <div class="wl-corp">{a["company"]}</div></td>'
                f'  <td style="text-align:right">{a["current_pct"]:.1f}%</td>'
                f'  <td style="text-align:right">{a["suggested_pct"]:.1f}%</td>'
                f'  <td style="text-align:right;color:{"#16a34a" if a["delta_pct"]>=0 else "#dc2626"}">'
                f'    {sign}{a["delta_pct"]:.1f}%</td>'
                f'  <td style="text-align:right;color:{"#16a34a" if a["delta_sgd"]>=0 else "#dc2626"}">'
                f'    {sign}S${abs(a["delta_sgd"]):,.0f}</td>'
                f'</tr>'
            )

        st.markdown(
            f'<table class="wl-table">'
            f'<thead><tr>'
            f'  <th>Action</th><th>Stock</th>'
            f'  <th>Current %</th><th>Suggested %</th><th>Δ%</th><th>Est. SGD Δ</th>'
            f'</tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            f'</table>',
            unsafe_allow_html=True,
        )

    # ── Tab 4: Performance ────────────────────────────────────────────────

    def _tab_performance(self):
        holdings = st.session_state.portfolio.get("holdings", [])
        if not holdings:
            st.info("Add holdings in the Holdings tab first.")
            return

        period_options = ["1M", "3M", "6M", "1Y", "All"]
        period = st.radio("Period", period_options, index=3, horizontal=True, label_visibility="collapsed")
        yf_period = self._PERIOD_MAP.get(period, "1y")

        # Fetch price histories (show spinner)
        with st.spinner("Loading price history…"):
            price_histories = {}
            for h in holdings:
                sym = h["symbol"]
                hist = _fetch_history(sym, yf_period)
                if hist is not None:
                    price_histories[sym] = hist

            # FX histories
            fx_hkd_hist = _fetch_history("HKDSGD=X", yf_period)
            fx_usd_hist = _fetch_history("USDSGD=X", yf_period)
            fx_histories = {}
            if fx_hkd_hist is not None:
                fx_histories["HKD"] = fx_hkd_hist
            if fx_usd_hist is not None:
                fx_histories["USD"] = fx_usd_hist

            # S&P 500
            sp500_hist = _fetch_history("^GSPC", yf_period)

        # Compute actual portfolio value
        fx_rates     = self._get_fx_rates()
        prices_local = self._get_prices_local(holdings)
        actual_series = self.pm.get_historical_value(holdings, price_histories, fx_histories)

        if actual_series.empty:
            st.warning("Not enough price history to build performance chart.")
            return

        # Compute suggested portfolio value
        scores_cache = st.session_state.get("portfolio_scores", {})
        candidates   = list({h["symbol"] for h in holdings} | set(st.session_state.get("stock_pool", {}).keys()))
        scores       = {c: scores_cache.get(c, 0) for c in candidates}
        suggested_weights = self.pm.suggest_weights(candidates, scores, cap=0.25)

        start_date   = actual_series.index[0]
        cost_sgd     = self.pm.get_cost_basis_sgd(holdings, fx_rates)
        total_inv    = cost_sgd if cost_sgd > 0 else actual_series.iloc[0]

        suggested_series = self.pm.get_hypothetical_value(
            suggested_weights, total_inv, price_histories, fx_histories, start_date
        )

        # Normalise S&P 500 to same starting SGD value
        sp500_norm = None
        if sp500_hist is not None and not sp500_hist.empty:
            sp500_aligned = sp500_hist.reindex(actual_series.index).ffill()
            if not sp500_aligned.empty and sp500_aligned.iloc[0] != 0:
                sp500_norm = sp500_aligned * (actual_series.iloc[0] / sp500_aligned.iloc[0])

        # ── Plotly line chart ──
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=actual_series.index,
            y=actual_series.values,
            name="My Portfolio",
            line=dict(color="#3b82f6", width=2),
            hovertemplate="S$%{y:,.0f}<extra>My Portfolio</extra>",
        ))

        if not suggested_series.empty:
            fig.add_trace(go.Scatter(
                x=suggested_series.index,
                y=suggested_series.values,
                name="Suggested Portfolio",
                line=dict(color="#16a34a", width=2, dash="dash"),
                hovertemplate="S$%{y:,.0f}<extra>Suggested</extra>",
            ))

        if sp500_norm is not None:
            fig.add_trace(go.Scatter(
                x=sp500_norm.index,
                y=sp500_norm.values,
                name="S&P 500 (normalised)",
                line=dict(color="#94a3b8", width=1.5),
                hovertemplate="S$%{y:,.0f}<extra>S&P 500</extra>",
            ))

        fig.update_layout(
            height=420,
            hovermode="x unified",
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False, title="SGD Value"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=1.05),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # ── Return summary ──
        if len(actual_series) > 1:
            ret_pct = (actual_series.iloc[-1] - actual_series.iloc[0]) / actual_series.iloc[0] * 100
            sign    = "+" if ret_pct >= 0 else ""
            col_l, col_r = st.columns(2, gap="large")
            with col_l:
                st.metric(
                    f"Portfolio return ({period})",
                    f"S${actual_series.iloc[-1]:,.0f}",
                    f"{sign}{ret_pct:.2f}%",
                )
            if not suggested_series.empty and len(suggested_series) > 1:
                sug_ret = (suggested_series.iloc[-1] - suggested_series.iloc[0]) / suggested_series.iloc[0] * 100
                sug_sign = "+" if sug_ret >= 0 else ""
                with col_r:
                    st.metric(
                        f"Suggested return ({period})",
                        f"S${suggested_series.iloc[-1]:,.0f}",
                        f"{sug_sign}{sug_ret:.2f}%",
                    )

    # ── Main entry point ──────────────────────────────────────────────────

    def render(self):
        st.title("Portfolio Analysis")

        tab1, tab2, tab3, tab4 = st.tabs(
            ["📋 Holdings", "📊 Analysis", "💡 Suggested Portfolio", "📈 Performance"]
        )
        with tab1:
            self._tab_holdings()
        with tab2:
            self._tab_analysis()
        with tab3:
            self._tab_suggested()
        with tab4:
            self._tab_performance()
