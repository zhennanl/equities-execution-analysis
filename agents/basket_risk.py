"""Basket-level risk decomposition + Stage-0 RFQ artifacts — the missing
basket lens (everything else in the platform is per-name).

    risk_decomposition     basket return series vs a hedgeable index:
                           beta, tracking error, hedgeable (systematic) vs
                           idiosyncratic variance split, and per-name TE
                           contributions (leave-one-out). This is the
                           number a PT desk quotes risk off — and the
                           quantitative core of the agency-vs-principal
                           comparison (AGENCY_VS_PRINCIPAL_DECISION.md).
    blind_profile          the masked RFQ profile a client actually sends:
                           lines, gross, side balance, %ADV buckets,
                           market mix, TE/beta — and NO names.
    agency_quote_sketch    the structured agency response: expected cost
                           by liquidity bucket, hardest-tail note, TE
                           context — a rationale FRAMEWORK, explicitly not
                           a price (commission is commercial).
    aggregate_basket_costs weighted pre-trade cost with a contribution
                           Pareto — which names ARE the basket's cost.

Inputs are explicit (price panel + basket frame) so everything tests
offline; a live path can feed yfinance closes into the same functions.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

TRADING_DAYS = 252
MIN_OBS = 40


@dataclass
class BasketRisk:
    available: bool
    reason: str = ""
    n_names: int = 0
    n_obs: int = 0
    gross_notional: float = 0.0
    net_notional: float = 0.0
    beta: float = 0.0                  # basket beta vs the hedge index
    te_ann: float = 0.0                # annualized tracking error (resid vol)
    total_vol_ann: float = 0.0
    hedgeable_share: float = 0.0       # R^2: variance the index hedge removes
    hedge_notional: float = 0.0        # beta x net notional (futures to sell/buy)
    contributors: pd.DataFrame = None  # leave-one-out TE contribution per name
    note: str = ""


def _basket_returns(basket: pd.DataFrame, prices: pd.DataFrame) -> pd.Series:
    """Signed-notional-weighted daily log returns, normalized by GROSS
    notional (so a balanced long-short basket has small returns — the
    point). basket: ticker, side, shares, price. prices: wide close panel."""
    rets = np.log(prices / prices.shift()).dropna()
    w = {}
    gross = float((basket["shares"] * basket["price"]).sum())
    for _, r in basket.iterrows():
        sgn = 1.0 if str(r["side"]).capitalize() == "Buy" else -1.0
        w[r["ticker"]] = sgn * float(r["shares"] * r["price"]) / gross
    cols = [t for t in w if t in rets.columns]
    return (rets[cols] * pd.Series({t: w[t] for t in cols})).sum(axis=1), w, gross


def risk_decomposition(basket: pd.DataFrame, prices: pd.DataFrame,
                       index_prices: pd.Series) -> BasketRisk:
    """OLS of basket returns on hedge-index returns. TE = annualized
    residual vol; hedgeable share = R^2; contributors = leave-one-out TE
    delta (drop the name, re-run, how much TE falls)."""
    missing = [t for t in basket["ticker"] if t not in prices.columns]
    if missing:
        return BasketRisk(False, reason=f"price panel missing {missing[:5]}")
    br, w, gross = _basket_returns(basket, prices)
    ir = np.log(index_prices / index_prices.shift()).dropna()
    df = pd.concat([br.rename("b"), ir.rename("m")], axis=1).dropna()
    if len(df) < MIN_OBS:
        return BasketRisk(False, reason=f"need >= {MIN_OBS} overlapping "
                          f"return days, have {len(df)}")
    x, y = df["m"].to_numpy(), df["b"].to_numpy()
    beta = float(np.cov(y, x)[0, 1] / np.var(x)) if np.var(x) > 0 else 0.0
    resid = y - beta * x
    te = float(resid.std(ddof=1) * np.sqrt(TRADING_DAYS))
    tot = float(y.std(ddof=1) * np.sqrt(TRADING_DAYS))
    r2 = float(1 - resid.var() / y.var()) if y.var() > 0 else 0.0
    net = float(sum(np.sign(1 if str(r["side"]).capitalize() == "Buy" else -1)
                    * r["shares"] * r["price"] for _, r in basket.iterrows()))

    rows = []
    for t in basket["ticker"]:
        sub = basket[basket["ticker"] != t]
        if sub.empty:
            continue
        br2, _, _ = _basket_returns(sub, prices)
        d2 = pd.concat([br2.rename("b"), ir.rename("m")], axis=1).dropna()
        yy, xx = d2["b"].to_numpy(), d2["m"].to_numpy()
        b2 = float(np.cov(yy, xx)[0, 1] / np.var(xx)) if np.var(xx) > 0 else 0.0
        te2 = float((yy - b2 * xx).std(ddof=1) * np.sqrt(TRADING_DAYS))
        rows.append({"ticker": t, "te_without_bps": round(te2 * 1e4, 1),
                     "te_contribution_bps": round((te - te2) * 1e4, 1)})
    contrib = (pd.DataFrame(rows)
               .sort_values("te_contribution_bps", ascending=False)
               .reset_index(drop=True))

    note = (f"Basket beta {beta:.2f} vs hedge index; TE {te:.2%} ann. "
            f"({te * 1e4:.0f} bps); {r2:.0%} of variance is hedgeable — "
            + ("a tight-tracking basket (risk desks bid these TIGHT; "
               "agency premium-saving argument is strongest)."
               if r2 >= 0.7 else
               "meaningfully idiosyncratic — a risk bid would price the "
               "unhedgeable residual; agency lets the client keep that "
               "premium if they can carry the variance.")
            + " LOO contributions show which names ARE the tracking risk.")
    return BasketRisk(True, n_names=int(len(basket)), n_obs=int(len(df)),
                      gross_notional=round(gross, 0), net_notional=round(net, 0),
                      beta=round(beta, 3), te_ann=round(te, 4),
                      total_vol_ann=round(tot, 4),
                      hedgeable_share=round(max(0.0, r2), 3),
                      hedge_notional=round(beta * net, 0),
                      contributors=contrib, note=note)


# ── Stage-0 artifacts ──────────────────────────────────────────────────────

ADV_BUCKETS = ((0, 1, "<1% ADV"), (1, 5, "1-5%"), (5, 10, "5-10%"),
               (10, np.inf, ">10%"))


def blind_profile(basket: pd.DataFrame, adv_usd: dict = None,
                  risk: BasketRisk = None) -> dict:
    """The masked RFQ profile — everything a client shares pre-award,
    nothing that identifies a name. Output text contains NO tickers."""
    b = basket.copy()
    b["notional"] = b["shares"] * b["price"]
    gross = float(b["notional"].sum())
    buy = float(b.loc[b["side"].str.capitalize() == "Buy", "notional"].sum())
    mix = (b.groupby("market")["notional"].sum() / gross * 100).round(1)
    buckets = {}
    if adv_usd:
        pct = b.apply(lambda r: r["notional"] / adv_usd.get(r["ticker"], np.nan)
                      * 100, axis=1)
        for lo, hi, name in ADV_BUCKETS:
            share = float(b.loc[(pct >= lo) & (pct < hi), "notional"].sum()
                          / gross * 100)
            buckets[name] = round(share, 1)
        tail = float(pct.quantile(0.9)) if pct.notna().any() else None
    else:
        tail = None
    prof = {"n_lines": int(len(b)), "gross_usd": round(gross, 0),
            "buy_pct": round(buy / gross * 100, 1),
            "net_imbalance_pct": round((2 * buy - gross) / gross * 100, 1),
            "market_mix_pct": {str(k): float(v) for k, v in mix.items()},
            "adv_buckets_pct_of_gross": buckets or "ADV not supplied",
            "p90_line_pct_adv": None if tail is None else round(tail, 1),
            "beta": None if risk is None or not risk.available else risk.beta,
            "te_ann_bps": None if risk is None or not risk.available
            else round(risk.te_ann * 1e4, 0),
            "hedgeable_share": None if risk is None or not risk.available
            else risk.hedgeable_share}
    L = ["BLIND BASKET PROFILE (no names disclosed)", "-" * 44,
         f"{prof['n_lines']} lines | gross ~{gross:,.0f} USD | "
         f"{prof['buy_pct']:.0f}% buys (net {prof['net_imbalance_pct']:+.0f}%)",
         "Market mix: " + ", ".join(f"{k} {v:.0f}%"
                                    for k, v in prof["market_mix_pct"].items())]
    if buckets:
        L.append("Liquidity: " + ", ".join(f"{k}: {v:.0f}%"
                                           for k, v in buckets.items())
                 + (f" | P90 line = {tail:.1f}% ADV" if tail else ""))
    if prof["te_ann_bps"] is not None:
        L.append(f"vs hedge index: beta {prof['beta']:.2f}, TE "
                 f"{prof['te_ann_bps']:.0f} bps ann., "
                 f"{prof['hedgeable_share']:.0%} hedgeable")
    prof["text"] = "\n".join(L)
    return prof


def agency_quote_sketch(profile: dict, cost_by_bucket_bps: dict = None) -> str:
    """The agency-side response rationale. A FRAMEWORK with the numbers we
    can defend — never a commission (commercial, desk-head territory)."""
    costs = cost_by_bucket_bps or {"<1% ADV": (2, 5), "1-5%": (5, 12),
                                   "5-10%": (12, 25), ">10%": (25, 60)}
    L = ["AGENCY QUOTE RATIONALE (framework — commission is commercial)",
         "-" * 44,
         f"Basket: {profile['n_lines']} lines, ~{profile['gross_usd']:,.0f} "
         f"gross, net {profile['net_imbalance_pct']:+.0f}%."]
    b = profile.get("adv_buckets_pct_of_gross")
    if isinstance(b, dict):
        for k, v in b.items():
            lo, hi = costs.get(k, (None, None))
            if v and lo is not None:
                L.append(f"  {k}: {v:.0f}% of gross -> expected impact+spread "
                         f"{lo}-{hi} bps (sqrt-law at Medium urgency)")
        worst = [k for k, v in b.items() if k == ">10%" and v > 10]
        if worst:
            L.append("  ⚠ >10%-ADV tail exceeds 10% of gross — multi-day "
                     "schedule or dark-patient routing; this tail is what a "
                     "risk bid would charge most for.")
    if profile.get("te_ann_bps") is not None:
        L.append(f"Tracking context: TE {profile['te_ann_bps']:.0f} bps ann., "
                 f"{profile['hedgeable_share']:.0%} hedgeable — "
                 + ("tight tracker: the variance a risk premium would insure "
                    "is small; agency should win on all-in cost."
                    if (profile["hedgeable_share"] or 0) >= 0.7 else
                    "material idiosyncratic risk: quantify the client's "
                    "variance tolerance before comparing to risk bids."))
    L.append("Benchmark options: arrival / interval VWAP / close — cost "
             "estimates above are arrival-basis; close-benchmark shifts "
             "timing risk, not expected impact.")
    return "\n".join(L)


# ── basket-level pre-trade cost aggregation ────────────────────────────────

def aggregate_basket_costs(per_name: pd.DataFrame, top_k: int = 5) -> dict:
    """per_name: ticker, notional, est_cost_bps -> gross-weighted basket
    cost + contribution Pareto (which names ARE the cost)."""
    p = per_name.dropna(subset=["notional", "est_cost_bps"]).copy()
    if p.empty:
        return {"available": False, "reason": "no costed names"}
    gross = float(p["notional"].sum())
    p["cost_usd"] = p["notional"] * p["est_cost_bps"] / 1e4
    total = float(p["cost_usd"].sum())
    wavg = total / gross * 1e4
    p = p.sort_values("cost_usd", ascending=False)
    p["cum_share"] = (p["cost_usd"].cumsum() / total).round(3)
    top = p.head(top_k)
    return {"available": True, "gross_usd": round(gross, 0),
            "wavg_cost_bps": round(wavg, 1),
            "est_cost_usd": round(total, 0),
            "top_contributors": top[["ticker", "notional", "est_cost_bps",
                                     "cost_usd", "cum_share"]]
            .reset_index(drop=True),
            "top_share": round(float(top["cost_usd"].sum() / total), 3),
            "note": f"{top_k} names carry {top['cost_usd'].sum() / total:.0%} "
                    "of the basket's expected cost — the pre-trade "
                    "conversation is about these, not the other "
                    f"{len(p) - top_k if len(p) > top_k else 0}."}


# ── demo data ──────────────────────────────────────────────────────────────

def demo_panel(n_days: int = 120, seed: int = 12):
    """Index + 8 names: five high-beta trackers, two high-idio names, one
    negative-beta hedge-ish name; basket long 6 / short 2 -> known
    decomposition to recover. Returns (basket_df, prices, index_prices,
    adv_usd)."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2026-01-05", periods=n_days)
    m = rng.normal(0.0003, 0.011, n_days)
    specs = [("TRK1", 1.0, .004), ("TRK2", 1.1, .005), ("TRK3", .9, .004),
             ("TRK4", 1.0, .006), ("TRK5", 1.05, .005),
             ("IDIO1", .6, .025), ("IDIO2", .5, .030), ("NEG1", -.3, .012)]
    prices = {}
    for t, b, s in specs:
        r = b * m + rng.normal(0, s, n_days)
        prices[t] = 100 * np.exp(np.cumsum(r))
    prices = pd.DataFrame(prices, index=idx)
    index_prices = pd.Series(100 * np.exp(np.cumsum(m)), index=idx,
                             name="INDEX")
    basket = pd.DataFrame({
        "ticker": [t for t, _, _ in specs],
        "market": ["Japan (TSE)"] * 3 + ["Hong Kong (HKEX)"] * 3
        + ["Taiwan (TWSE)"] * 2,
        "side": ["Buy"] * 6 + ["Sell"] * 2,
        "shares": [10_000] * 5 + [20_000, 15_000, 12_000],
        "price": [float(prices[t].iloc[-1]) for t, _, _ in specs]})
    adv = {t: float(prices[t].iloc[-1]) * v for t, v in
           zip(prices.columns, [2e6, 1.5e6, 3e6, 8e4, 1e6, 5e4, 6e4, 5e5])}
    return basket, prices, index_prices, adv
