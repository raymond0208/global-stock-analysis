import pandas as pd


class PortfolioMetrics:
    """Pure-calculation class — no Streamlit, no yfinance calls."""

    # ── FX helpers ────────────────────────────────────────────────────────

    def get_sgd_price(self, local_price: float, currency: str, fx_rates: dict) -> float:
        """Convert a local-currency price to SGD.

        fx_rates expects keys 'HKD' and 'USD' with float values representing
        how many SGD one unit of that currency buys (e.g. {'HKD': 0.173, 'USD': 1.35}).
        SGD → SGD is 1:1.
        """
        if currency == "SGD":
            return local_price
        rate = fx_rates.get(currency, 1.0)
        return local_price * rate

    # ── Portfolio value ───────────────────────────────────────────────────

    def get_portfolio_value_sgd(
        self,
        holdings: list[dict],
        prices_local: dict,
        fx_rates: dict,
    ) -> float:
        """Total portfolio value in SGD."""
        total = 0.0
        for h in holdings:
            sym = h["symbol"]
            price_local = prices_local.get(sym)
            if price_local is None:
                continue
            total += h["shares"] * self.get_sgd_price(price_local, h["currency"], fx_rates)
        return total

    def get_cost_basis_sgd(self, holdings: list[dict], fx_rates: dict) -> float:
        """Total cost basis in SGD (purchase_price × shares converted to SGD)."""
        total = 0.0
        for h in holdings:
            total += h["shares"] * self.get_sgd_price(h["purchase_price"], h["currency"], fx_rates)
        return total

    # ── Weights ───────────────────────────────────────────────────────────

    def get_weights(
        self,
        holdings: list[dict],
        prices_local: dict,
        fx_rates: dict,
    ) -> dict:
        """Returns {symbol: fraction_of_total_sgd_value} (values sum to 1.0)."""
        total = self.get_portfolio_value_sgd(holdings, prices_local, fx_rates)
        if total == 0:
            return {}
        weights = {}
        for h in holdings:
            sym = h["symbol"]
            price_local = prices_local.get(sym)
            if price_local is None:
                continue
            value_sgd = h["shares"] * self.get_sgd_price(price_local, h["currency"], fx_rates)
            weights[sym] = value_sgd / total
        return weights

    # ── Allocation ────────────────────────────────────────────────────────

    def get_region_allocation(
        self,
        holdings: list[dict],
        prices_local: dict,
        fx_rates: dict,
    ) -> dict:
        """Returns {'SG': pct, 'HK': pct, 'US': pct} as percentages (0–100)."""
        total = self.get_portfolio_value_sgd(holdings, prices_local, fx_rates)
        if total == 0:
            return {}
        region_values = {}
        for h in holdings:
            sym = h["symbol"]
            price_local = prices_local.get(sym)
            if price_local is None:
                continue
            currency = h["currency"]
            if currency == "SGD":
                region = "SG"
            elif currency == "HKD":
                region = "HK"
            else:
                region = "US"
            value_sgd = h["shares"] * self.get_sgd_price(price_local, currency, fx_rates)
            region_values[region] = region_values.get(region, 0.0) + value_sgd
        return {region: val / total * 100 for region, val in region_values.items()}

    def get_sector_allocation(
        self,
        holdings: list[dict],
        prices_local: dict,
        fx_rates: dict,
        sector_map: dict,
    ) -> dict:
        """Returns {sector: pct} as percentages (0–100). 'Unknown' for missing sectors."""
        total = self.get_portfolio_value_sgd(holdings, prices_local, fx_rates)
        if total == 0:
            return {}
        sector_values = {}
        for h in holdings:
            sym = h["symbol"]
            price_local = prices_local.get(sym)
            if price_local is None:
                continue
            sector = sector_map.get(sym) or "Unknown"
            value_sgd = h["shares"] * self.get_sgd_price(price_local, h["currency"], fx_rates)
            sector_values[sector] = sector_values.get(sector, 0.0) + value_sgd
        return {s: v / total * 100 for s, v in sector_values.items()}

    # ── Weighted metrics ──────────────────────────────────────────────────

    def get_weighted_metric(
        self,
        holdings: list[dict],
        prices_local: dict,
        fx_rates: dict,
        metric_map: dict,
        key: str,
    ) -> float:
        """SGD-value-weighted average of metric_map[symbol][key]."""
        weights = self.get_weights(holdings, prices_local, fx_rates)
        total = 0.0
        for sym, w in weights.items():
            val = (metric_map.get(sym) or {}).get(key)
            if val is not None and val != 0:
                total += w * float(val)
        return total

    # ── Suggested weights ─────────────────────────────────────────────────

    def suggest_weights(
        self,
        candidates: list,
        scores: dict,
        cap: float = 0.25,
    ) -> dict:
        """Score-proportional weights capped at `cap`, redistributed iteratively.

        1. raw_weight[s] = score[s] / sum(scores)
        2. Cap any weight > cap; redistribute surplus proportionally.
        3. Repeat until stable.
        4. Return normalised dict (sums to 1.0).
        """
        valid = [c for c in candidates if scores.get(c, 0) > 0]
        if not valid:
            n = len(candidates)
            return {c: 1.0 / n for c in candidates} if n > 0 else {}

        weights = {c: scores[c] for c in valid}
        # Normalise
        total = sum(weights.values())
        weights = {c: v / total for c, v in weights.items()}

        for _ in range(100):  # max iterations
            capped = {c: min(w, cap) for c, w in weights.items()}
            surplus = sum(w - cap for c, w in weights.items() if w > cap)
            if surplus < 1e-9:
                break
            # Redistribute surplus to uncapped stocks proportionally
            uncapped = {c: w for c, w in capped.items() if w < cap - 1e-9}
            if not uncapped:
                break
            uncapped_total = sum(uncapped.values())
            for c in uncapped:
                capped[c] += surplus * (capped[c] / uncapped_total)
            weights = capped

        # Final normalise
        total = sum(weights.values())
        if total > 0:
            weights = {c: v / total for c, v in weights.items()}
        # Add zero-weight candidates that were excluded
        for c in candidates:
            if c not in weights:
                weights[c] = 0.0
        return weights

    # ── Rebalancing ───────────────────────────────────────────────────────

    def get_rebalancing_actions(
        self,
        holdings: list[dict],
        prices_local: dict,
        fx_rates: dict,
        suggested_weights: dict,
        total_sgd: float,
    ) -> list:
        """Returns list of dicts with rebalancing info per stock.

        Each dict: {symbol, company, current_pct, suggested_pct,
                    delta_pct, delta_sgd, action}
        action = 'Buy' | 'Sell' | 'Hold' (|delta_pct| < 1% threshold)
        """
        current_weights = self.get_weights(holdings, prices_local, fx_rates)
        company_map = {h["symbol"]: h["company"] for h in holdings}

        all_symbols = set(current_weights.keys()) | set(suggested_weights.keys())
        actions = []
        for sym in sorted(all_symbols):
            current_pct = current_weights.get(sym, 0.0) * 100
            suggested_pct = suggested_weights.get(sym, 0.0) * 100
            delta_pct = suggested_pct - current_pct
            delta_sgd = delta_pct / 100 * total_sgd

            if abs(delta_pct) < 1.0:
                action = "Hold"
            elif delta_pct > 0:
                action = "Buy"
            else:
                action = "Sell"

            actions.append({
                "symbol": sym,
                "company": company_map.get(sym, sym),
                "current_pct": current_pct,
                "suggested_pct": suggested_pct,
                "delta_pct": delta_pct,
                "delta_sgd": delta_sgd,
                "action": action,
            })
        return actions

    # ── Historical value ──────────────────────────────────────────────────

    def get_historical_value(
        self,
        holdings: list[dict],
        price_histories: dict,
        fx_histories: dict,
    ) -> pd.Series:
        """Daily portfolio value in SGD.

        value(t) = Σ shares_i × close_i(t) × fx_i(t)

        fx_histories keys: 'HKD', 'USD' → pd.Series of SGD-per-unit rates.
        """
        if not holdings or not price_histories:
            return pd.Series(dtype=float)

        # Build aligned date index (inner join across all available series)
        all_series = []
        for h in holdings:
            sym = h["symbol"]
            hist = price_histories.get(sym)
            if hist is not None and not hist.empty:
                all_series.append(hist)

        if not all_series:
            return pd.Series(dtype=float)

        # Start from the intersection of all date indexes
        common_index = all_series[0].index
        for s in all_series[1:]:
            common_index = common_index.intersection(s.index)

        if len(common_index) == 0:
            return pd.Series(dtype=float)

        total = pd.Series(0.0, index=common_index)
        for h in holdings:
            sym = h["symbol"]
            hist = price_histories.get(sym)
            if hist is None or hist.empty:
                continue
            hist_aligned = hist.reindex(common_index)
            if hist_aligned.isna().all():
                continue

            currency = h["currency"]
            if currency == "SGD":
                fx = pd.Series(1.0, index=common_index)
            else:
                fx_hist = fx_histories.get(currency)
                if fx_hist is not None and not fx_hist.empty:
                    fx = fx_hist.reindex(common_index).ffill().fillna(1.0)
                else:
                    fx = pd.Series(1.0, index=common_index)

            total += h["shares"] * hist_aligned.ffill() * fx

        return total

    def get_hypothetical_value(
        self,
        suggested_weights: dict,
        total_invested_sgd: float,
        price_histories: dict,
        fx_histories: dict,
        start_date,
    ) -> pd.Series:
        """Hypothetical daily portfolio value using suggested_weights.

        Allocates total_invested_sgd by suggested_weights from start_date.
        Returns daily SGD value Series on the same date index as actual.
        """
        if not suggested_weights or not price_histories:
            return pd.Series(dtype=float)

        # Collect relevant series
        relevant = {
            sym: price_histories[sym]
            for sym, w in suggested_weights.items()
            if w > 0 and sym in price_histories and price_histories[sym] is not None
        }
        if not relevant:
            return pd.Series(dtype=float)

        common_index = list(relevant.values())[0].index
        for s in relevant.values():
            common_index = common_index.intersection(s.index)

        if len(common_index) == 0:
            return pd.Series(dtype=float)

        # Filter to start_date
        common_index = common_index[common_index >= pd.Timestamp(start_date)]
        if len(common_index) == 0:
            return pd.Series(dtype=float)

        total = pd.Series(0.0, index=common_index)

        # Need to determine currency for each symbol from price_histories context
        # Since we don't have holdings here, we'll guess from symbol suffix
        def _guess_currency(sym: str) -> str:
            if sym.endswith(".SI"):
                return "SGD"
            if sym.endswith(".HK"):
                return "HKD"
            return "USD"

        for sym, weight in suggested_weights.items():
            if weight <= 0 or sym not in relevant:
                continue
            hist = relevant[sym].reindex(common_index).ffill()
            if hist.isna().all() or hist.iloc[0] == 0:
                continue

            currency = _guess_currency(sym)
            if currency == "SGD":
                fx = pd.Series(1.0, index=common_index)
            else:
                fx_hist = fx_histories.get(currency)
                if fx_hist is not None and not fx_hist.empty:
                    fx = fx_hist.reindex(common_index).ffill().fillna(1.0)
                else:
                    fx = pd.Series(1.0, index=common_index)

            # Convert start price to SGD
            start_price_sgd = hist.iloc[0] * fx.iloc[0]
            if start_price_sgd == 0:
                continue

            allocated_sgd = total_invested_sgd * weight
            shares = allocated_sgd / start_price_sgd
            total += shares * hist * fx

        return total
