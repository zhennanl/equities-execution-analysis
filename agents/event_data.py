"""Event-positioning data beyond investor-type flows (session 7h).

Implements the priority queue of docs/EVENT_POSITIONING_DATA_BY_PHASE.md:

    1. Short balances (TWSE TWT93U): margin-short (retail 融券) AND SBL
       short-sale (借券賣出, institutional) balances, per stock, per day
       — the one dataset that serves three phases (pre-announcement
       build, A->T trajectory, T+ unwind) and decomposes the
       within-foreign netting left open in session 7e.
    2. Block-trade tape (TWSE BFIAUU): size done off the continuous
       session during the event window.
    3. TDCC weekly shareholding distribution: holder counts and shares
       by size bracket — LATEST WEEK ONLY via open data (documented
       limitation: forward-looking tool, cannot backtest past events).
    4. Indicative closing-auction snapshot: parser for the TWSE MIS
       intraday format — LIVE-ONLY during 13:25-13:30, not
       backtestable; wired for the cockpit, tested on canned payload.
    5. ETF units outstanding: PROTOCOL status — daily units are
       published by issuers/TDCC but not via a stable free API found
       from this sandbox; the desk source is named in the registry.

Every fetcher returns raw-payload -> tidy DataFrame via a separately
testable parse_* function (canned-payload tests, no network in suite).
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

CACHE_PATH = (Path(__file__).resolve().parent.parent / "data"
              / "event_data_cache.json")

_UA = {"User-Agent": "Mozilla/5.0"}


def _num(x):
    try:
        return float(str(x).replace(",", ""))
    except Exception:
        return np.nan


def _get_json(url: str, timeout: int = 25) -> dict:
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


# ---------------------------------------------------------------- 1. TWT93U
# Columns: 0 code | margin-short block: 1 prev bal, 2 sold, 3 covered,
# 4 redeemed, 5 current bal, 6 next-day quota | SBL block: 7 prev bal,
# 8 sold today, 9 returned, 10 adjustments, 11 current bal, 12 quota.

def parse_twt93u(payload: dict) -> pd.DataFrame:
    rows = []
    for r in payload.get("data", []):
        rows.append({
            "ticker": str(r[0]).strip(),
            "margin_short_prev": _num(r[1]),
            "margin_short_bal": _num(r[5]),
            "sbl_prev": _num(r[7]),
            "sbl_sold": _num(r[8]),
            "sbl_returned": _num(r[9]),
            "sbl_bal": _num(r[11]),
            "sbl_quota": _num(r[12]),      # 8g: borrow-capacity input
        })
    return pd.DataFrame(rows)


def fetch_twse_short_balance(date: str) -> pd.DataFrame:
    """date: YYYYMMDD. One call returns ALL TWSE stocks for the day."""
    url = ("https://www.twse.com.tw/en/exchangeReport/TWT93U"
           f"?response=json&date={date}")
    payload = _get_json(url)
    if payload.get("stat") != "OK":
        return pd.DataFrame()
    return parse_twt93u(payload)


# ---------------------------------------------------------------- 2. BFIAUU

def parse_bfiauu(payload: dict) -> pd.DataFrame:
    rows = []
    for r in payload.get("data", []):
        rows.append({
            "ticker": str(r[0]).strip(),
            "classification": str(r[1]).strip(),
            "price": _num(r[2]),
            "volume": _num(r[3]),
            "value": _num(r[4]),
        })
    return pd.DataFrame(rows)


def fetch_twse_block_trades(date: str) -> pd.DataFrame:
    url = ("https://www.twse.com.tw/en/block/BFIAUU"
           f"?response=json&date={date}&selectType=S")
    payload = _get_json(url)
    if payload.get("stat") != "OK":
        return pd.DataFrame()
    return parse_bfiauu(payload)


# ------------------------------------------------------------------ 3. TDCC

# TDCC 集保戶股權分散表 brackets: 1..15 ascending size (15 = 1,000,001+
# shares), 16 = difference adjustment, 17 = total. "Large holder"
# threshold used below: brackets >= 12 (400,001+ shares) — an assumption,
# stated wherever reported.
TDCC_LARGE_BRACKET_MIN = 12


def parse_tdcc_distribution(csv_text: str,
                            tickers: list[str] | None = None) -> pd.DataFrame:
    rows = []
    for line in csv_text.splitlines()[1:]:
        parts = line.strip().split(",")
        if len(parts) < 6:
            continue
        date, code, bracket, holders, shares, pct = parts[:6]
        code = code.strip()
        if tickers is not None and code not in tickers:
            continue
        rows.append({"date": date, "ticker": code,
                     "bracket": int(bracket), "holders": _num(holders),
                     "shares": _num(shares), "pct": _num(pct)})
    return pd.DataFrame(rows)


def fetch_tdcc_distribution(tickers: list[str]) -> pd.DataFrame:
    """LATEST WEEK ONLY — the open-data endpoint serves one snapshot.
    Historical weeks need a desk archive built by scheduled fetches."""
    url = "https://opendata.tdcc.com.tw/getOD.ashx?id=1-5"
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        text = r.read().decode("utf-8-sig", errors="replace")
    return parse_tdcc_distribution(text, tickers)


def tdcc_concentration(df: pd.DataFrame, ticker: str) -> dict:
    """Share of deposited stock held in large brackets (>=400,001 sh)."""
    d = df[(df["ticker"] == ticker) & (df["bracket"] <= 15)]
    if d.empty:
        return {"available": False, "ticker": ticker}
    total = d["shares"].sum()
    large = d[d["bracket"] >= TDCC_LARGE_BRACKET_MIN]["shares"].sum()
    return {"available": True, "ticker": ticker,
            "date": d["date"].iloc[0],
            "large_holder_pct": round(100 * large / total, 2)
            if total else np.nan,
            "retail_holders": int(d[d["bracket"] <= 5]["holders"].sum())}


# ------------------------------------------------- 4. Indicative auction
# TWSE MIS intraday snapshot fields (msgArray element): c=code,
# z=last/indicative price, tv=tentative matched volume (lots), s=matched,
# b/a=bid/ask queues. During 13:25-13:30 z/tv are the SIMULATED close.
# LIVE-ONLY: there is no historical archive of these snapshots.

def parse_auction_snapshot(msg: dict) -> dict:
    def f(k):
        v = msg.get(k, "-")
        if v in ("-", "", None):
            return np.nan
        # MIS bid/ask queues are underscore-joined ladders; take level 1
        return _num(str(v).split("_")[0])
    return {"ticker": str(msg.get("c", "")).strip(),
            "indicative_price": f("z"),
            "indicative_volume_lots": f("tv"),
            "cumulative_volume_lots": f("v"),
            "best_bid": f("b"),
            "best_ask": f("a")}


# ------------------------------------------------------------- analyzers

def short_balance_series(cache: dict, ticker: str) -> pd.DataFrame:
    """cache["short"]: {date: {ticker: [margin_bal, sbl_bal]}}."""
    rows = []
    for date, day in sorted(cache.get("short", {}).items()):
        if ticker in day:
            m, s = day[ticker]
            rows.append({"date": pd.Timestamp(date), "margin_short": m,
                         "sbl": s, "total_short": m + s})
    return pd.DataFrame(rows).set_index("date") if rows else pd.DataFrame()


def phase_deltas(series: pd.DataFrame, ann_date: str,
                 eff_date: str) -> dict:
    """Change in short balances across the three phases, in shares and
    as % of the balance on the last pre-announcement day."""
    if series.empty:
        return {"available": False}
    ann, eff = pd.Timestamp(ann_date), pd.Timestamp(eff_date)
    pre = series[series.index < ann]
    mid = series[(series.index >= ann) & (series.index <= eff)]
    post = series[series.index > eff]
    if pre.empty or mid.empty:
        return {"available": False}
    base = pre["total_short"].iloc[-1]
    out = {"available": True, "base_total_short": base}
    for name, seg, ref in (
            ("pre_ann_build", pre, pre["total_short"].iloc[0]),
            ("ann_to_T", mid, base),
            ("post_T", post, mid["total_short"].iloc[-1] if not mid.empty
             else base)):
        if seg.empty:
            out[name] = np.nan
            out[name + "_pct"] = np.nan
            continue
        chg = seg["total_short"].iloc[-1] - ref
        out[name] = chg
        out[name + "_pct"] = round(100 * chg / ref, 1) if ref else np.nan
    # SBL vs margin split over A->T (institutional vs retail short)
    if not mid.empty:
        out["ann_to_T_sbl"] = mid["sbl"].iloc[-1] - base_sbl(pre)
        out["ann_to_T_margin"] = (mid["margin_short"].iloc[-1]
                                  - pre["margin_short"].iloc[-1])
    return out


def base_sbl(pre: pd.DataFrame) -> float:
    return pre["sbl"].iloc[-1]


def block_prints(cache: dict, ticker: str, start: str, end: str) -> dict:
    """Block-trade activity for one name inside [start, end]."""
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    total_value, n, days = 0.0, 0, []
    for date, rows in sorted(cache.get("blocks", {}).items()):
        d = pd.Timestamp(date)
        if not (s <= d <= e):
            continue
        for r in rows:
            if str(r[0]).strip() == ticker:
                total_value += _num(r[4])
                n += 1
                days.append(date)
    return {"ticker": ticker, "n_prints": n,
            "total_value_twd": total_value, "days": sorted(set(days))}


# ------------------------------------------------ 7i: improvement layer
# Everything below converts the 7h GRADED findings into machinery.
# Heuristic constants are v1, grounded on the two graded events and
# marked for recalibration as the event library grows.

CROWDING_BANDS = (25.0, 5.0)          # pre-ann build %: HIGH >=25, MED >=5


def crowding_score(series: pd.DataFrame, ann_date: str) -> dict:
    """Pre-announcement crowding from the short ledger. Finding 7h-1:
    this tracks the CONSENSUS candidate list (including its errors), so
    it is a crowding gauge — never a truth signal."""
    if series.empty:
        return {"available": False}
    pre = series[series.index < pd.Timestamp(ann_date)]
    if len(pre) < 2:
        return {"available": False}
    base = pre["total_short"].iloc[0]
    build = pre["total_short"].iloc[-1] - base
    pct = 100 * build / base if base else np.nan
    band = ("HIGH" if pct >= CROWDING_BANDS[0]
            else "MED" if pct >= CROWDING_BANDS[1] else "LOW")
    return {"available": True, "pre_ann_build_pct": round(pct, 1),
            "crowding": band}


def crowding_overlay(predicted: dict[str, bool], cache: dict,
                     ann_date: str) -> pd.DataFrame:
    """PREDICTION calibration. predicted: ticker -> True if our engine
    flags it. Cross-classifies model call x street positioning:

      flagged + HIGH  -> CONSENSUS: priced; expect less T-day pressure
      flagged + LOW   -> UNPRICED: our differentiated call — largest
                         execution edge if right, check universe if alone
      not flagged + HIGH -> STREET-ONLY: the street is positioned for a
                         change we do not predict — re-check universe
                         and rules BEFORE the announcement (the
                         TaiwanCement cell, inverted)
    """
    rows = []
    for tkr, flagged in predicted.items():
        cs = crowding_score(short_balance_series(cache, tkr), ann_date)
        if not cs.get("available"):
            continue
        band = cs["crowding"]
        read = ("CONSENSUS (priced)" if flagged and band == "HIGH"
                else "UNPRICED (our call)" if flagged and band == "LOW"
                else "STREET-ONLY (re-check universe/rules)"
                if not flagged and band == "HIGH"
                else "unremarkable")
        rows.append({"ticker": tkr, "model_flag": flagged,
                     "pre_ann_build_pct": cs["pre_ann_build_pct"],
                     "crowding": band, "read": read})
    return pd.DataFrame(rows)


def drift_composition(series: pd.DataFrame, foreign_net_sum: float,
                      ann_date: str, eff_date: str) -> dict:
    """WHO drives the A->T move for a delete: new shorting vs long
    selling. Finding 7h-2: MSCI front-running was long-seller-led
    (THSR arb-short share ~15-20%). foreign_net_sum: cumulative T86
    foreign net over A->T (negative for deletes), shares."""
    if series.empty or not foreign_net_sum or foreign_net_sum >= 0:
        return {"available": False}
    ann, eff = pd.Timestamp(ann_date), pd.Timestamp(eff_date)
    pre = series[series.index < ann]
    mid = series[(series.index >= ann) & (series.index <= eff)]
    if pre.empty or mid.empty:
        return {"available": False}
    new_shorts = max(mid["sbl"].iloc[-1] - pre["sbl"].iloc[-1], 0.0)
    frac = new_shorts / abs(foreign_net_sum)
    label = ("SHORT_LED" if frac >= 0.5
             else "MIXED" if frac >= 0.25 else "LONG_SELLER_LED")
    return {"available": True, "arb_short_frac": round(frac, 2),
            "composition": label}


SETTLEMENT_LAG_DAYS = 2               # 7h: THSR SBL cliff landed at T+2


def completion_clock(series: pd.DataFrame, eff_date: str) -> dict:
    """EXECUTION timing for S3's completion leg on a delete: how far the
    arb unwind has run. Judged only after T+SETTLEMENT_LAG_DAYS sessions
    (borrow returned for shares bought ON the print posts at T+2)."""
    if series.empty:
        return {"available": False}
    eff = pd.Timestamp(eff_date)
    pre = series[series.index < eff]
    post = series[series.index > eff]
    if pre.empty or post.empty:
        return {"available": False}
    peak = max(pre["total_short"].iloc[-1], pre["total_short"].max())
    floor = pre["total_short"].iloc[0]
    last = post["total_short"].iloc[-1]
    denom = peak - floor
    unwind = (peak - last) / denom if denom > 0 else np.nan
    unwind = float(np.clip(unwind, 0, 2)) if not np.isnan(unwind) else np.nan
    settled = len(post) > SETTLEMENT_LAG_DAYS
    phase = ("PRE-SETTLEMENT (do not judge yet)" if not settled
             else "NOT_STARTED" if unwind < 0.1
             else "UNWINDING (complete the S3 leg into the covering bid)"
             if unwind < 0.7 else "MOSTLY_DONE (covering bid fading)")
    return {"available": True, "unwind_frac": round(unwind, 2)
            if not np.isnan(unwind) else np.nan,
            "post_sessions": len(post), "phase": phase}


# (pressure multiplier, reversal fraction) by crowding band — v1
# heuristic: a heavily pre-positioned name has spent part of its
# pressure before T and carries a larger covering bounce. Calibrate
# from the event library as it accumulates graded events.
CROWDING_PATH_ADJ = {"HIGH": (0.60, 0.65), "MED": (1.00, 0.50),
                     "LOW": (1.15, 0.40)}


def crowding_adjusted_params(pressure_bps: float,
                             crowding: str | None) -> tuple[float, float]:
    """Returns (pressure_bps, reversal_frac) for the frontier path."""
    mult, rev = CROWDING_PATH_ADJ.get(crowding or "MED", (1.0, 0.5))
    return pressure_bps * mult, rev


def etf_creation_proxy(cache: dict, etf_ticker: str, start: str,
                       end: str) -> dict:
    """7h-4: paired-trade blocks in the ETF line = in-kind
    creation/redemption baskets — the free proxy for the units feed."""
    b = block_prints(cache, etf_ticker, start, end)
    return {"ticker": etf_ticker, "n_prints": b["n_prints"],
            "creation_proxy_value_twd": b["total_value_twd"],
            "note": "paired blocks in the ETF line proxy primary-market "
                    "activity; direction (create vs redeem) needs the "
                    "issuer units report (PROTOCOL)"}


# ------------------------------------- multi-market crowding (session 8g)
# One normalized schema for every market: cache["short"][date][code] =
# [primary_short_bal, secondary_bal]. short_balance_series() and the
# review-engine crowding read then work UNCHANGED on any market. Units
# differ per market (shares / lots / disclosed-position shares) — the
# crowding read is % -change within a series, so units cancel; the
# registry records them anyway.


def _get_bytes(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_sfc_short_csv(text: str) -> pd.DataFrame:
    """SFC HK weekly aggregated reportable short positions CSV.
    Columns: Date, Stock Code, Stock Name, shares, HK$. Codes are
    zero-padded to 4 so '177' joins universe ticker '0177.HK'."""
    rows = []
    for ln in text.splitlines()[1:]:
        p = ln.split(",")
        if len(p) < 5:
            continue
        code = p[1].strip()
        if not code.isdigit():
            continue
        rows.append({"ticker": code.zfill(4), "name": p[2].strip(),
                     "short_shares": _num(p[3]), "short_hkd": _num(p[4])})
    return pd.DataFrame(rows)


def fetch_hk_short_positions(max_files: int = 8) -> dict:
    """Scrape the SFC page for weekly CSV links, fetch the most recent
    max_files. Returns {date: DataFrame}. Weekly cadence — a 30-obs
    crowding window spans ~7 months; reads are labeled 'weekly'."""
    page = _get_bytes(
        "https://www.sfc.hk/en/Regulatory-functions/Market/"
        "Short-position-reporting/Aggregated-reportable-short-"
        "positions-of-specified-shares").decode("utf-8", "ignore")
    links = re.findall(
        r'href="(https://www\.sfc\.hk/-/media/[^"]*Short_Position_'
        r'Reporting_Aggregated_Data_(\d{8})\.csv[^"]*)"', page)
    out = {}
    for url, d in links[:max_files]:
        date = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        out[date] = parse_sfc_short_csv(
            _get_bytes(url).decode("utf-8-sig", "ignore"))
    return out


def parse_jpx_short_xls(raw: bytes) -> pd.DataFrame:
    """JPX daily Short_Positions.xls: one row per (stock, discloser)
    for positions >=0.5% of shares out. Sum shares per code = the
    disclosed short balance (a floor on true shorts — sub-0.5%
    positions are invisible; consistent floor => valid deltas)."""
    import xlrd
    sh = xlrd.open_workbook(file_contents=raw).sheet_by_index(0)
    agg = {}
    for i in range(8, sh.nrows):
        code = sh.cell_value(i, 2)
        shares = sh.cell_value(i, 11)
        if not code or not isinstance(shares, (int, float)):
            continue
        c = str(int(code)) if isinstance(code, float) else str(code)
        agg[c] = agg.get(c, 0.0) + float(shares)
    return pd.DataFrame([{"ticker": k, "short_shares": v}
                         for k, v in agg.items()])


def fetch_jpx_short_positions(max_files: int = 6) -> dict:
    """Scrape the JPX English short-selling page for daily XLS links."""
    page = _get_bytes(
        "https://www.jpx.co.jp/english/markets/public/short-selling/"
        "index.html").decode("utf-8", "ignore")
    links = re.findall(
        r'href="(/english/markets/public/short-selling/[^"]+/'
        r'(\d{8})_Short_Positions\.xls)"', page)
    out = {}
    for path, d in links[:max_files]:
        date = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        out[date] = parse_jpx_short_xls(
            _get_bytes("https://www.jpx.co.jp" + path))
    return out


def parse_tpex_margin(payload: dict) -> pd.DataFrame:
    """TPEx margin/balance JSON (fills the .TWO gap TWT93U leaves):
    col 0 code, col 14 margin-short balance (lots)."""
    rows = []
    for r in payload.get("tables", [{}])[0].get("data", []):
        code = str(r[0]).strip()
        if not code.isdigit():
            continue
        rows.append({"ticker": code, "short_bal_lots": _num(r[14])})
    return pd.DataFrame(rows)


def fetch_tpex_short_balance(date: str) -> pd.DataFrame:
    """date: YYYY/MM/DD."""
    payload = _get_json("https://www.tpex.org.tw/www/zh-tw/margin/"
                        f"balance?date={date}&response=json")
    return parse_tpex_margin(payload)


def merge_into_short_cache(cache: dict, date: str, df: pd.DataFrame,
                           col: str) -> dict:
    """Normalize any market's per-date frame into the TWT93U cache
    schema {short: {date: {code: [bal, 0]}}} consumed by
    short_balance_series()."""
    day = cache.setdefault("short", {}).setdefault(date, {})
    for _, r in df.iterrows():
        v = r[col]
        if pd.notna(v):
            day[r["ticker"]] = [float(v), 0.0]
    return cache


# Per-market crowding source registry — the honest coverage grid.
# status: LIVE (fetcher works from sandbox) / PROTOCOL (source exists,
# anti-bot or login-gated from sandbox; works on a desk network) /
# STRUCTURAL (no public per-stock short-balance product exists).
CROWDING_SOURCES = {
    "Taiwan":    {"status": "LIVE", "cadence": "daily",
                  "source": "TWSE TWT93U (margin-short + SBL, shares) "
                            "+ TPEx margin/balance for .TWO (lots)"},
    "Japan":     {"status": "LIVE", "cadence": "daily",
                  "source": "JPX Short_Positions.xls — disclosed "
                            "positions >=0.5%, summed per stock "
                            "(floor, not census; deltas valid)"},
    "HongKong":  {"status": "LIVE", "cadence": "weekly",
                  "source": "SFC aggregated reportable short "
                            "positions CSV (shares + HK$)"},
    "China":     {"status": "LIVE (H-lines) / PROTOCOL (A-lines)",
                  "cadence": "weekly",
                  "source": "H-lines via the SFC HK file; A-line "
                            "margin balances (SSE/SZSE) TLS-blocked "
                            "from sandbox"},
    "Korea":     {"status": "PROTOCOL", "cadence": "daily",
                  "source": "KRX short balance — login-gated from "
                            "sandbox; desk/vendor feed on-site"},
    "Malaysia":  {"status": "PROTOCOL", "cadence": "daily",
                  "source": "Bursa RSS short-sale reports — 403 from "
                            "sandbox"},
    "India":     {"status": "STRUCTURAL", "cadence": "-",
                  "source": "no public per-stock short-balance "
                            "product; SLB volumes only (thin)"},
    "Indonesia": {"status": "STRUCTURAL", "cadence": "-",
                  "source": "short selling restricted to a small "
                            "eligible list; no balance disclosure"},
}


# -------------------------------------------------------------- registry

EVENT_DATA_COVERAGE = {
    "short_balances_tw": {
        "source": "TWSE TWT93U (margin-short + SBL, per stock, daily)",
        "phases": ["pre-announcement", "ann->T", "post-T"],
        "status": "IMPLEMENTED",
    },
    "block_trades_tw": {
        "source": "TWSE BFIAUU daily block-trade tape",
        "phases": ["pre-announcement", "ann->T"],
        "status": "IMPLEMENTED",
    },
    "tdcc_distribution": {
        "source": "TDCC open data 1-5, weekly shareholding by bracket",
        "phases": ["pre-announcement", "post-T"],
        "status": "IMPLEMENTED (latest-week snapshot only; historical "
                  "archive requires scheduled fetches going forward)",
    },
    "indicative_auction_tw": {
        "source": "TWSE MIS intraday snapshot, 13:25-13:30 simulated "
                  "close",
        "phases": ["T"],
        "status": "PARSER ONLY (live-only feed; no historical archive "
                  "exists — cockpit integration, not backtestable)",
    },
    "etf_units": {
        "source": "Issuer daily unit reports / TDCC; no stable free API "
                  "located from sandbox",
        "phases": ["pre-announcement", "ann->T", "post-T"],
        "status": "PROTOCOL",
    },
    "futures_basis_oi": {
        "source": "TAIFEX / SGX daily reports (form-gated downloads)",
        "phases": ["pre-announcement", "ann->T"],
        "status": "PROTOCOL",
    },
}
