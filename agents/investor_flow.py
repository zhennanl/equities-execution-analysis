"""Investor-type flow attribution — solving the WHO limitation of the
positioning trajectory (session 7e).

The 7d study inferred arb-vs-tracker from price/volume divergence. For
Taiwan, inference is unnecessary: TWSE publishes DAILY per-stock
institutional flows (the 三大法人 data) — foreign investors, investment
trusts (投信 — which IS the domestic tracker complex: Yuanta 0050,
Fubon 006208...), and dealers. Free, official, per stock, per day.

    fetch_twse_institutional(date)   one call returns ALL stocks for a day
    attribute_window(...)            per-name daily foreign/trust/dealer
                                     net flows across the A->T window
    handoff_metrics(...)             the arb->tracker handoff, measured:
                                     who bought early, who bought the
                                     print, and whether the T-day is a
                                     transfer between them

Identification logic (disclosed): for FTSE TW50 events the tracker is
DOMESTIC (investment trusts) and foreign flow is arb/discretionary; for
MSCI events the tracker flow itself is FOREIGN (EM/ACWI funds), so
foreign nets carry tracker+arb combined and trusts are the domestic
bystander — the same data, two different reading grids, stated per event.
"""
from __future__ import annotations

import datetime as _dt
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

CACHE_PATH = (Path(__file__).resolve().parent.parent / "data"
              / "twse_institutional.json")


def _num(x):
    try:
        return float(str(x).replace(",", ""))
    except Exception:
        return np.nan


def parse_t86(payload: dict) -> pd.DataFrame:
    """Parse the TWSE T86 response (EN layout: code, foreign-ex-dealer
    B/S/net, foreign-dealer B/S/net, trust B/S/net, dealer aggregate...,
    total-3-institution net in the LAST column)."""
    rows = []
    for r in payload.get("data", []):
        code = str(r[0]).strip()
        foreign = _num(r[3]) + _num(r[6])          # ex-dealer + dealer arms
        trust = _num(r[9])
        total = _num(r[-1])
        dealer = total - foreign - trust
        rows.append({"ticker": code, "foreign_net": foreign,
                     "trust_net": trust, "dealer_net": dealer,
                     "total_inst_net": total})
    return pd.DataFrame(rows)


def fetch_twse_institutional(date: _dt.date, session=None) -> pd.DataFrame:
    """One day, all stocks (net shares by investor type). Cached callers
    should store per-date frames; this function is a thin fetch."""
    import requests
    r = (session or requests).get(
        "https://www.twse.com.tw/rwd/en/fund/T86",
        params={"date": date.strftime("%Y%m%d"), "selectType": "ALL",
                "response": "json"}, timeout=20)
    d = r.json()
    if d.get("stat") != "OK":
        return pd.DataFrame()
    return parse_t86(d)


def attribute_window(cache: dict, tickers: list) -> pd.DataFrame:
    """cache: {date_str: [t86 rows...]} -> long frame (date, ticker,
    foreign_net, trust_net, dealer_net) for the requested tickers."""
    out = []
    for ds, rows in sorted(cache.items()):
        df = pd.DataFrame(rows)
        if df.empty:
            continue
        sub = df[df["ticker"].isin(tickers)]
        for _, r in sub.iterrows():
            out.append({"date": ds, **r.to_dict()})
    return pd.DataFrame(out)


def handoff_metrics(flows: pd.DataFrame, ticker: str, t_date: str,
                    side: str) -> dict:
    """The WHO decomposition for one event name.

    pre-window = all cached days before T; T-day separately. Sign
    convention: positive = net buying. For an ADD (side='Buy'), the
    tracker must end up long; for a DELETE, short/sold."""
    f = flows[flows["ticker"] == ticker].sort_values("date")
    if f.empty:
        return {"available": False, "ticker": ticker}
    pre = f[f["date"] < t_date]
    t = f[f["date"] == t_date]
    if t.empty:
        return {"available": False, "ticker": ticker,
                "reason": f"no T-day row for {t_date}"}
    t = t.iloc[0]
    d = {"available": True, "ticker": ticker, "side": side,
         "pre_foreign_net": float(pre["foreign_net"].sum()),
         "pre_trust_net": float(pre["trust_net"].sum()),
         "t_foreign_net": float(t["foreign_net"]),
         "t_trust_net": float(t["trust_net"]),
         "t_dealer_net": float(t["dealer_net"])}
    # the handoff test: on T, do trusts (domestic trackers) and foreigners
    # trade OPPOSITE ways, with the tracker side matching the index flow?
    idx_sign = 1.0 if side == "Buy" else -1.0
    d["t_handoff"] = bool(np.sign(d["t_trust_net"]) == idx_sign
                          and np.sign(d["t_foreign_net"]) == -idx_sign
                          and abs(d["t_foreign_net"]) > 0)
    d["arb_prepositioned"] = bool(np.sign(d["pre_foreign_net"]) == idx_sign
                                  and abs(d["pre_foreign_net"])
                                  > abs(d["pre_trust_net"]))
    return d


# ── multi-market registry (session 7f) ─────────────────────────────────────

INVESTOR_FLOW_COVERAGE = [
    {"Market": "Taiwan (TWSE)", "Dataset": "T86 institutional daily (foreign/trust/dealer per stock)",
     "Granularity": "per-stock, daily", "Access": "free official API", "Status": "IMPLEMENTED"},
    {"Market": "Taiwan (TPEx)", "Dataset": "TPEx institutional daily (same trio, OTC names — MPI!)",
     "Granularity": "per-stock, daily", "Access": "free official API", "Status": "IMPLEMENTED"},
    {"Market": "Korea (KRX)", "Dataset": "Foreign + institution net per stock (KRX data; Naver mirror used — desk uses KRX/KOSCOM feed)",
     "Granularity": "per-stock, daily", "Access": "free (mirror) / official feed", "Status": "IMPLEMENTED"},
    {"Market": "Japan (TSE)", "Dataset": "Investor-type flows (foreign/individual/prop)",
     "Granularity": "MARKET-WIDE, weekly — no per-stock", "Access": "free JPX", "Status": "aggregate only"},
    {"Market": "Japan (TSE)", "Dataset": "Per-stock short-sale positions >=0.2%",
     "Granularity": "per-holder, daily", "Access": "free JPX", "Status": "protocol (short side only)"},
    {"Market": "Hong Kong (HKEX)", "Dataset": "CCASS participant shareholding (per stock, per broker/custodian!)",
     "Granularity": "per-stock per-participant, daily snapshot", "Access": "free, form-scrape", "Status": "protocol"},
    {"Market": "China-A", "Dataset": "Northbound Connect holdings via CCASS (foreign channel per stock)",
     "Granularity": "per-stock, daily holdings", "Access": "free HKEX", "Status": "protocol"},
    {"Market": "Indonesia (IDX)", "Dataset": "Foreign vs domestic per stock",
     "Granularity": "per-stock, daily", "Access": "free IDX", "Status": "roadmap"},
    {"Market": "Thailand (SET)", "Dataset": "Investor-type (foreign/institution/retail/prop)",
     "Granularity": "MARKET-WIDE, daily", "Access": "free SET", "Status": "aggregate only"},
    {"Market": "India (NSE)", "Dataset": "FII/DII daily + per-stock bulk/block deals",
     "Granularity": "market-wide daily; per-deal disclosures", "Access": "free NSE", "Status": "aggregate + deals"},
]


def fetch_tpex_institutional(date: _dt.date, session=None) -> pd.DataFrame:
    """TPEx (Taiwan OTC) daily institutional flows — same trio as TWSE
    T86, for TPEx-listed names (e.g. MPI 6223)."""
    import requests
    r = (session or requests).get(
        "https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade",
        params={"type": "Daily", "sect": "EW",
                "date": date.strftime("%Y/%m/%d"), "response": "json"},
        timeout=20)
    d = r.json()
    tables = d.get("tables", [])
    if not tables or not tables[0].get("data"):
        return pd.DataFrame()
    return parse_tpex(tables[0])


def parse_tpex(table: dict) -> pd.DataFrame:
    """TPEx layout: 代號, 名稱, [foreign-ex-dealer B/S/N], [foreign-dealer
    B/S/N], [foreign total B/S/N], [trust B/S/N], [dealer self B/S/N],
    [dealer hedge B/S/N], [dealer total B/S/N], total-3-inst net (last).
    Parsed defensively: foreign = cols after name (net at idx 4 + dealer
    arm net at idx 7); trust net at idx 13; total = last column."""
    rows = []
    for r in table.get("data", []):
        code = str(r[0]).strip()
        try:
            foreign = _num(r[4]) + _num(r[7])
            trust = _num(r[13])
            total = _num(r[-1])
            dealer = total - foreign - trust
        except (IndexError, TypeError):
            continue
        rows.append({"ticker": code, "foreign_net": foreign,
                     "trust_net": trust, "dealer_net": dealer,
                     "total_inst_net": total})
    return pd.DataFrame(rows)


def fetch_krx_investor_naver(code: str, pages: int = 3,
                             session=None) -> pd.DataFrame:
    """Korea per-stock daily investor flows via the Naver Finance mirror
    of KRX data (columns: date, close, ..., institution net, foreign
    net). A desk replaces this with the KRX/KOSCOM feed — the mirror is
    for research reproducibility, disclosed."""
    import io
    import requests
    frames = []
    ses = session or requests
    for page in range(1, pages + 1):
        r = ses.get("https://finance.naver.com/item/frgn.naver",
                    params={"code": code, "page": page},
                    headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        for df in pd.read_html(io.StringIO(r.text)):
            cols = [str(c) for c in df.columns]
            if any("외국인" in c for c in cols) and len(df) > 3:
                frames.append(df)
                break
        time.sleep(0.8)
    if not frames:
        return pd.DataFrame()
    return parse_naver_frgn(pd.concat(frames, ignore_index=True))


def parse_naver_frgn(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten the Naver frgn table -> (date, inst_net, foreign_net)."""
    flat = df.copy()
    flat.columns = ["_".join(str(x) for x in c) if isinstance(c, tuple)
                    else str(c) for c in df.columns]
    date_col = next(c for c in flat.columns if "날짜" in c)
    inst_col = next(c for c in flat.columns if "기관" in c)
    # foreign net = the 순매매량 column under 외국인 (not 보유주수/보유율)
    for_col = next(c for c in flat.columns
                   if "외국인" in c and ("순매매" in c or c.endswith("순매매량")))
    out = flat[[date_col, inst_col, for_col]].copy()
    out.columns = ["date", "inst_net", "foreign_net"]
    out = out.dropna(subset=["date"])
    out["date"] = out["date"].astype(str).str.replace(".", "-", regex=False)
    out = out[out["date"].str.match(r"\d{4}-\d{2}-\d{2}")]
    for c in ("inst_net", "foreign_net"):
        out[c] = (out[c].astype(str).str.replace(",", "")
                  .str.replace("+", "", regex=False).astype(float))
    return out.sort_values("date").reset_index(drop=True)
