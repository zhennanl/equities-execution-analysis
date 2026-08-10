"""5-minute bars around index events — ANNOUNCEMENT-anchored,
and an empirical probe of what IB actually serves (c-183).

TWO PROBLEMS WITH THE EXISTING HARVEST.

1. THE WINDOW IS ANCHORED ON THE WRONG DATE. ib_harvest.py
   fetches eff-30 -> eff+7 calendar days. But MSCI announces a
   median of 18 days BEFORE the effective date (range 16-23,
   n=34 measured from msci_tw_events.json). So the current
   window opens only ~12 days before the announcement. Bill
   wants a MONTH of pre-announcement behaviour; that needs
   ann-35 -> eff+7, which is ~55 calendar days from an
   effective-date anchor, not 40.

   This matters because the pre-announcement window is where
   the interesting question lives: does anything move BEFORE
   MSCI tells the market? A window that opens 12 days out
   cannot distinguish "no front-running" from "we did not
   look early enough".

2. WHAT IB SERVES PER MARKET WAS NEVER MEASURED. IB's APAC
   coverage depends on the ACCOUNT's market-data subscriptions
   and on IB's own history depth per exchange, both of which
   differ by entity and change over time. Rather than assert a
   table from memory, `probe` asks IB directly — one small
   historical request per exchange — and prints what came
   back. A measured "works / does not work / not subscribed"
   beats a confident list that may be wrong.

KNOWN, because it was bracketed empirically on Bill's account
(2026-08-04): IB's TWSE 5m history begins about 2023-05-01.
2023-03-17 failed, 2023-05-31 worked. Events before that
cannot be harvested from IB at any window width.

RUNS ON BILL'S MACHINE — needs a logged-in TWS or IB Gateway
with the API enabled. Not the sandbox.

Usage:
  python scripts\\ib_window_harvest.py probe
  python scripts\\ib_window_harvest.py plan   [Taiwan]
  python scripts\\ib_window_harvest.py fetch  [Taiwan]
Out: data/ib_bars_windows.json
"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "ib_bars_windows.json"
HOST, PORTS = "127.0.0.1", (7497, 7496, 4001, 4002)

# How far either side of the event. PRE is measured from the
# ANNOUNCEMENT, not the effective date — that is the whole fix.
PRE_ANN_DAYS = 35
POST_EFF_DAYS = 7

# IB exchange code + a liquid probe symbol per market. The
# probe tells us which of these the account can actually reach.
# c-184: ENTITLEMENT read from Bill's actual IBKR market-data
# page (2026-08-08). "have" = already subscribed at no cost;
# "cheap"/"paid" = offered, price noted; "none" = IB does not
# sell equity data for that market at all.
ENTITLEMENT = {
    "Korea":      ("have",  "Korea Equities Bundle (P,L1) — FEE WAIVED"),
    "HongKong":   ("have",  "HK Securities Exchange (L1) — FEE WAIVED"),
    "Taiwan":     ("cheap", "Taiwan Stock Exchange USD 1.00 + "
                            "Taipei Exchange (L1) USD 0.45 /mo"),
    "China":      ("cheap", "SSE 5-sec snapshot via HKEx USD 1.00 + "
                            "SZSE 3-sec USD 1.00 /mo (both WAIVED "
                            "above USD 5 monthly commissions); "
                            "direct L1 feeds are USD 26.50 / 26.00"),
    "Singapore":  ("paid",  "SGX Equities (L1) SGD 14.00 /mo"),
    "Japan":      ("paid",  "Japan (TSE) Equities (P,L1) JPY 3,000 /mo"),
    "Malaysia":   ("paid",  "Bursa Malaysia Securities (P,L2) USD 21.50 /mo"),
    "Australia":  ("paid",  "CBOE Australia (P,L1) USD 74 — NOTE this is "
                            "the Cboe/Chi-X venue, NOT ASX primary. "
                            "ASX Total (P,L2) is AUD 152 /mo"),
    "India":      ("none",  "not offered — the only India line is SGX "
                            "India Connect (Nifty FUTURES, non-residents). "
                            "Indian cash equities need an IBKR India entity"),
    "Thailand":   ("none",  "not offered"),
    "Indonesia":  ("none",  "not offered"),
    "NewZealand": ("none",  "not offered"),
}

EXCHANGES = {
    "Taiwan":     ("TWSE", "2330", "TWD"),
    "Japan":      ("TSEJ", "7203", "JPY"),
    "HongKong":   ("SEHK", "700", "HKD"),
    "Korea":      ("KRX", "005930", "KRW"),   # c-190: KSE fails
    "Singapore":  ("SGX", "D05", "SGD"),
    "Australia":  ("ASX", "BHP", "AUD"),
    "India":      ("NSE", "RELIANCE", "INR"),
    "Thailand":   ("SET", "PTT", "THB"),
    "Malaysia":   ("BURSA", "1155", "MYR"),
    "Indonesia":  ("IDX", "BBCA", "IDR"),
    "NewZealand": ("NZX", "SPK", "NZD"),
    "China":      ("SEHKNTL", "600519", "CNH"),
}
# c-190 re-measured on Bill's account. The daily-depth ladder
# shows Taiwan failing at 5 Y and succeeding at 3 Y, which
# brackets the edge between 2021-08 and 2023-08 — consistent
# with the earlier 2023-05 bracket. NOT yet pinned to a day;
# run `ib_history_edge.py edge Taiwan` for that.
#
# China's 2014-11-14 IS a real edge, and it is not arbitrary:
# Shanghai-Hong Kong Stock Connect opened 2014-11-17. IB's
# A-share history begins when the instrument became reachable.
IB_FLOOR = {"Taiwan": "2023-05-01", "China": "2014-11-14"}


def _connect():
    from ib_async import IB
    ib = IB()
    last = None
    for port in PORTS:
        try:
            ib.connect(HOST, port, clientId=17, timeout=8)
            print(f"connected on port {port}")
            return ib
        except Exception as e:                     # noqa: BLE001
            last = e
    raise SystemExit(
        f"no TWS/Gateway on {PORTS}: {last}\n"
        "Start TWS or IB Gateway, then File > Global "
        "Configuration > API > Settings > Enable ActiveX and "
        "Socket Clients.")


def probe():
    """Ask IB what it will actually serve, per market.

    This is the honest answer to 'which APAC markets does IBKR
    give 5-minute data for'. It depends on the account, so it
    is measured here rather than assumed.
    """
    from ib_async import Stock
    ib = _connect()
    rows = {}
    for mkt, (exch, sym, ccy) in EXCHANGES.items():
        ent, note = ENTITLEMENT.get(mkt, ("?", ""))
        rec = {"exchange": exch, "probe_symbol": sym,
               "entitlement": ent, "entitlement_note": note}
        if ent == "none":
            rec["status"] = "IB DOES NOT SELL THIS MARKET"
            rows[mkt] = rec
            print(f"  {mkt:11} {exch:9} not offered by IB")
            continue
        try:
            c = Stock(sym, exch, ccy)
            det = ib.reqContractDetails(c)
            if not det:
                rec["status"] = "NO CONTRACT — exchange or " \
                                "symbol not available"
                rows[mkt] = rec
                print(f"  {mkt:11} {exch:9} NO CONTRACT")
                continue
            rec["contract_ok"] = True
            # c-184: test TRADES *and* MIDPOINT separately.
            # A subscription described as "top of book (L1)" is
            # QUOTE data; our bars use whatToShow="TRADES",
            # which is last-sale. On some exchanges an L1 quote
            # entitlement does NOT unlock trade history, and the
            # failure looks identical to "not subscribed". This
            # tells the two apart.
            for what in ("TRADES", "MIDPOINT"):
                try:
                    b = ib.reqHistoricalData(
                        det[0].contract, endDateTime="",
                        durationStr="5 D",
                        barSizeSetting="5 mins",
                        whatToShow=what, useRTH=True,
                        formatDate=1)
                except Exception as e:             # noqa: BLE001
                    rec[what] = f"ERROR {str(e)[:70]}"
                    continue
                rec[what] = f"{len(b)} bars" if b else "none"
                time.sleep(1.2)
            # DEPTH matters as much as availability: a feed that
            # only reaches back a month cannot cover 2023 events.
            try:
                deep = ib.reqHistoricalData(
                    det[0].contract, endDateTime="",
                    durationStr="3 Y", barSizeSetting="1 day",
                    whatToShow="TRADES", useRTH=True,
                    formatDate=1)
                rec["daily_depth_from"] = (str(deep[0].date)
                                           if deep else None)
            except Exception as e:                 # noqa: BLE001
                rec["daily_depth_from"] = f"ERROR {str(e)[:60]}"
            ok = str(rec.get("TRADES", "")).endswith("bars")
            rec["status"] = "OK (TRADES)" if ok else (
                "NO TRADE HISTORY — quote entitlement may not "
                "cover last-sale bars")
            print(f"  {mkt:11} {exch:9} TRADES={rec.get('TRADES')} "
                  f"MID={rec.get('MIDPOINT')} "
                  f"from={rec.get('daily_depth_from')}")
        except Exception as e:                     # noqa: BLE001
            rec["status"] = f"ERROR: {str(e)[:120]}"
            print(f"  {mkt:11} {exch:9} ERROR {str(e)[:60]}")
        time.sleep(1.5)
        rows[mkt] = rec
    ib.disconnect()
    p = ROOT / "data" / "ib_market_probe.json"
    p.write_text(json.dumps(
        {"asof": dt.date.today().isoformat(),
         "note": "MEASURED on this account. IB entitlements "
                 "differ by account and entity; re-run after "
                 "changing subscriptions.",
         "markets": rows}, indent=1), encoding="utf-8")
    print(f"\n-> {p.name}")
    return rows


def windows(market="Taiwan"):
    """(code, ann, eff, start, end) per index event.

    Anchored on the ANNOUNCEMENT so the pre-event window is a
    real month of pre-announcement trading.
    """
    import pandas as pd
    ev = json.loads((ROOT / "data" / "msci_tw_events.json")
                    .read_text(encoding="utf-8"))
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    g = df[df.market == market]
    floor = IB_FLOOR.get(market)
    out = []
    for rev, v in ev.items():
        ann, eff = v.get("ann"), v.get("eff")
        if not (ann and eff):
            continue
        if floor and str(eff) < floor:
            continue
        start = (pd.Timestamp(ann)
                 - pd.Timedelta(days=PRE_ANN_DAYS)).date()
        end = (pd.Timestamp(eff)
               + pd.Timedelta(days=POST_EFF_DAYS)).date()
        codes = sorted({str(r.code).strip()
                        for _, r in g[g.review == rev].iterrows()
                        if str(r.code).strip()})
        for c in codes:
            out.append({"code": c, "review": rev,
                        "ann": str(ann)[:10], "eff": str(eff)[:10],
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                        "span_days": (end - start).days})
    return out


def plan(market="Taiwan"):
    w = windows(market)
    if not w:
        print(f"{market}: no windows above the IB floor")
        return w
    spans = [x["span_days"] for x in w]
    print(f"{market}: {len(w)} name-events, "
          f"{len({x['review'] for x in w})} reviews")
    print(f"  window span: {min(spans)}-{max(spans)} calendar "
          f"days (was 37 anchored on effective)")
    print(f"  earliest {min(x['start'] for x in w)}  "
          f"latest {max(x['end'] for x in w)}")
    print(f"  est. runtime at ~11 s/request: "
          f"{len(w) * 11 / 60:.0f} min")
    for x in w[:3]:
        print(f"    {x['code']} {x['review']}: {x['start']} -> "
              f"{x['end']}  (ann {x['ann']}, eff {x['eff']})")
    return w


def fetch(market="Taiwan"):
    from ib_async import Stock
    exch, _, ccy = EXCHANGES[market]
    jobs = plan(market)
    if not jobs:
        return
    cache = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    done = {k for c in cache.values()
            for k in c.get("_windows", [])}
    ib = _connect()
    got = 0
    for i, jb in enumerate(jobs, 1):
        tag = f"{jb['code']}|{jb['review']}"
        if tag in done:
            continue
        try:
            det = ib.reqContractDetails(
                Stock(jb["code"], exch, ccy))
            if not det:
                print(f"  {tag}: no contract")
                continue
            # IB counts duration back from endDateTime
            dur = max(jb["span_days"], 30)
            bars = ib.reqHistoricalData(
                det[0].contract,
                endDateTime=f"{jb['end'].replace('-', '')}"
                            f"-09:00:00",
                durationStr=f"{dur} D",
                barSizeSetting="5 mins", whatToShow="TRADES",
                useRTH=True, formatDate=1)
            if not bars:
                print(f"  {tag}: no bars")
                continue
            rows = [[str(b.date)[:16], b.open, b.close, b.volume]
                    for b in bars
                    if jb["start"] <= str(b.date)[:10] <= jb["end"]]
            d = cache.setdefault(jb["code"], {})
            d.setdefault("5m", [])
            seen = {r[0] for r in d["5m"]}
            d["5m"] += [r for r in rows if r[0] not in seen]
            d["5m"].sort()
            d.setdefault("_windows", []).append(tag)
            got += 1
        except Exception as e:                     # noqa: BLE001
            print(f"  {tag}: {str(e)[:90]}")
        if i % 10 == 0:
            OUT.write_text(json.dumps(cache), encoding="utf-8")
            print(f"  {i}/{len(jobs)} ({got} fetched)",
                  flush=True)
        time.sleep(11)      # IB pacing: <60 requests / 10 min
    OUT.write_text(json.dumps(cache), encoding="utf-8")
    ib.disconnect()
    print(f"-> {OUT.name}: {len(cache)} codes, {got} new windows")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    mkt = sys.argv[2] if len(sys.argv) > 2 else "Taiwan"
    if cmd == "probe":
        probe()
    elif cmd == "fetch":
        fetch(mkt)
    else:
        plan(mkt)
