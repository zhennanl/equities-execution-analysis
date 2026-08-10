"""IB harvest — 5-minute TWSE bars for event windows, years deep.

RUNS ON BILL'S MACHINE (not the sandbox): needs a logged-in TWS or
IB Gateway with API enabled. Session 9i.

WHY IB: historical-bar depth limits are lifted for bar sizes >= 1
minute (TWS API docs) — 5m bars reach YEARS back for subscribed
exchanges, and IB TRADES bars are expected to INCLUDE the closing
auction print (verified empirically by this script's sanity check,
never assumed).

SETUP (one-time, ~10 min):
  1. TWS (or IB Gateway) -> File > Global Configuration > API >
     Settings: Enable ActiveX and Socket Clients; note the port
     (7497 TWS paper/live default 7496; Gateway 4001/4002).
  2. Client Portal -> Settings -> Market Data Subscriptions: check
     whether "Taiwan Stock Exchange" is available to your account
     and subscribe if so (small monthly fee; cancel after harvest).
     If unavailable, run this script anyway — step `verify` also
     tries DELAYED data, which sometimes serves historical bars
     without a subscription.
  3. pip install ib_async
  4. python scripts/ib_harvest.py verify   (proves connectivity +
     TW data entitlement on ONE name before any bulk fetch)
  5. python scripts/ib_harvest.py fetch    (pacing-compliant; ~25-40
     min for the full event set; resumable — rerun anytime)
  6. python scripts/ib_harvest.py sanity   (per-day bar-sum vs
     official TWSE daily volume: ratio ~1.0 -> bars INCLUDE the
     auction -> this source supersedes TV for everything)

Output: data/ib_bars.json  {code: {"5m": [[ts, o, c, v], ...]}} —
same row shape as tv_bars.json so the execution studies can consume
it with src tag "5m_ib" (studies prefer IB where present once
sanity passes).
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "data" / "ib_bars.json"
HOST, PORTS = "127.0.0.1", (7497, 7496, 4001, 4002)

# IB's TWSE historical floor, bracketed EMPIRICALLY on 2026-08-04
# (Bill's account): 2023-03-17 fails, 2023-05-31 works -> earliest
# covered event = the May-2023 MSCI SAIR. Windows with effective
# dates before this are skipped without an API call. LOWER this if
# IB ever deepens coverage (rerun fetch; skipped windows were never
# marked done, so they fill automatically).
IB_FLOOR = "2023-05-01"


def _connect():
    from ib_async import IB
    ib = IB()
    last = None
    for port in PORTS:
        try:
            ib.connect(HOST, port, clientId=17, timeout=6)
            # session 9i: never wait forever on a data-farm request
            # (ADJUSTED_LAST on an unentitled/uncovered farm returns
            # NOTHING — default RequestTimeout=0 hangs the script)
            ib.RequestTimeout = 30
            print(f"connected on port {port}")
            return ib
        except Exception as e:                        # noqa: BLE001
            last = e
    raise SystemExit(f"No TWS/Gateway reachable on {PORTS}: {last}\n"
                     "Is TWS running with API enabled?")


def _contract(code):
    from ib_async import Stock
    return Stock(code, "TWSE", "TWD")


def _qualify(ib, code):
    """TWSE first, TPEX fallback (bridge names 5274/6223/4174/...
    live on the Taipei Exchange). Returns a qualified contract or
    None."""
    from ib_async import Stock
    for exch in ("TWSE", "TPEX"):
        c = Stock(code, exch, "TWD")
        try:
            ib.qualifyContracts(c)
            if c.conId:
                return c
        except Exception:                             # noqa: BLE001
            continue
    return None


def _ib_event_set():
    """IB is not bound by TV's 2022 depth floor: FTSE events with
    codes+effective back to 2018-03 + the MSCI TW registry. IB's
    true 5m floor is discovered EMPIRICALLY (too-old windows return
    0 bars and are skipped, never marked done)."""
    from agents.time_machine import MSCI_TW
    keys = json.loads(
        (ROOT / "data" / "ftse_tw50_changes.json").read_text(
            encoding="utf-8"))
    out = []
    for k in sorted(keys):
        v = keys[k]
        if not v.get("effective") or v["effective"] < "2018-01":
            continue
        names = {a["code"]: "Buy" for a in v.get("adds", [])}
        names.update({d["code"]: "Sell" for d in v.get("dels", [])})
        if names:
            out.append((f"FTSE {k}", "FTSE", v["effective"], names))
    for k, v in MSCI_TW.items():
        names = {c: "Buy" for c in v["adds"]}
        names.update({c: "Sell" for c in v["dels"]})
        out.append((k, "MSCI", v["effective"], names))
    # session 9i: the TW ALIAS BRIDGE unlocks MSCI events 2015 ->
    # Aug-2025 (data/msci_tw_events.json; bridge-matched aliases are
    # UNVERIFIED until their event print confirms — the fetch itself
    # is the validator)
    bridge = ROOT / "data" / "msci_tw_events.json"
    if bridge.exists():
        have = {e[2] for e in out}
        for season, v in json.loads(
                bridge.read_text(encoding="utf-8")).items():
            if not v.get("eff") or v["eff"] in have \
                    or v["eff"] >= "2025-08":
                continue
            names = {c: "Buy" for c in v["adds"]}
            names.update({c: "Sell" for c in v["dels"]})
            if names:
                out.append((f"MSCI {season}", "MSCI", v["eff"],
                            names))
    return out


def _windows():
    """(code, start_date, end_date, eff) per event window. Window =
    eff-33d -> eff+7d: covers the FULL announcement->effective
    period plus ~2 weeks of pre-announcement tape (prediction
    features) plus the post-print reversal week."""
    import pandas as pd
    jobs = []
    for _, _, eff, names in _ib_event_set():
        a = (pd.Timestamp(eff) - pd.Timedelta(days=30)
             ).strftime("%Y%m%d")
        b = (pd.Timestamp(eff) + pd.Timedelta(days=7)
             ).strftime("%Y%m%d")
        for code in names:
            jobs.append((code, a, b, eff))
    return jobs


def verify():
    ib = _connect()
    c = _contract("2330")
    ib.qualifyContracts(c)
    print("contract qualified:", c.conId, c.exchange)
    for mdt, label in ((1, "LIVE"), (3, "DELAYED")):
        ib.reqMarketDataType(mdt)
        try:
            # UTC dash notation (Error-10314-safe on new TWS builds):
            # 14:00 Taipei = 06:00 UTC on the May-29 print day
            bars = ib.reqHistoricalData(
                c, endDateTime="20260529-06:00:00",
                durationStr="1 D", barSizeSetting="5 mins",
                whatToShow="TRADES", useRTH=True)
            print(f"{label}: {len(bars)} bars for 2330 on the "
                  f"May-29 print day"
                  + (f"; last bar {bars[-1].date} vol "
                     f"{bars[-1].volume}" if bars else ""))
            if bars:
                print("VERIFY OK — proceed to `fetch`")
                ib.disconnect()
                return
        except Exception as e:                        # noqa: BLE001
            print(f"{label}: {str(e)[:90]}")
    print("No TW historical data served — check the TWSE market-data "
          "subscription in Client Portal.")
    ib.disconnect()


def fetch():
    ib = _connect()
    # LIVE market data type: TAI offers no delayed feed, so type 3
    # raises "No market data permissions" even with a valid TWSE
    # subscription (verify proved LIVE works)
    ib.reqMarketDataType(1)
    cache = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    jobs = _windows()
    done_keys = {k for c in cache.values()
                 for k in c.get("_windows", [])}
    pre_floor = sum(1 for j in jobs if j[3] < IB_FLOOR)
    todo = [(c, a, b, eff) for c, a, b, eff in jobs
            if f"{c}|{eff}" not in done_keys and eff >= IB_FLOOR]
    print(f"{len(todo)} of {len(jobs)} windows to fetch "
          f"({pre_floor} below the {IB_FLOOR} IB floor skipped; "
          "pacing: ~6s/request)")
    for i, (code, a, b, eff) in enumerate(todo):
        con = _qualify(ib, code)
        if con is None:
            print(f"{i+1}/{len(todo)} {code} {eff}: no contract on "
                  "TWSE/TPEX — skipped", flush=True)
            time.sleep(2)
            continue
        try:
            # UTC dash notation; 15:00 Taipei = 07:00 UTC
            bars = ib.reqHistoricalData(
                con, endDateTime=f"{b}-07:00:00",
                durationStr="40 D", barSizeSetting="5 mins",
                whatToShow="TRADES", useRTH=True)
        except Exception as e:                        # noqa: BLE001
            print(code, eff, "FAIL", str(e)[:60])
            time.sleep(6)
            continue
        # Volume unit VERIFIED in shares (verify showed 2330's 13:30
        # auction bar at 50.97M — share-scale, not lots). Note the
        # separate 13:30 bar = the closing auction print itself.
        rows = [[bar.date.strftime("%Y-%m-%d %H:%M"),
                 float(bar.open), float(bar.close),
                 float(bar.volume)]
                for bar in bars]
        if not rows:                 # failed windows are NOT marked
            print(f"{i+1}/{len(todo)} {code} {eff}: 0 bars — will "
                  "retry on next run", flush=True)
            time.sleep(6)
            continue
        d = cache.setdefault(code, {})
        existing = {r[0] for r in d.get("5m", [])}
        d["5m"] = sorted(d.get("5m", [])
                         + [r for r in rows
                            if r[0] not in existing])
        d.setdefault("_windows", []).append(f"{code}|{eff}")
        tmp = OUT.with_suffix(".tmp")
        tmp.write_text(json.dumps(cache), encoding="utf-8")
        tmp.replace(OUT)
        print(f"{i+1}/{len(todo)} {code} {eff}: {len(rows)} bars",
              flush=True)
        time.sleep(6)                # 60 req / 10 min compliance
    ib.disconnect()


def sanity():
    """Bar-sum vs official daily volume, per event T-day. Ratio ~1.0
    -> IB bars INCLUDE the auction (upgrade); ~continuous-share ->
    they don't; ~0.001 -> the lots-vs-shares factor needs flipping.
    NOTHING is assumed — this step decides how the studies use IB."""
    cache = json.loads(OUT.read_text(encoding="utf-8"))
    sd = json.loads((ROOT / "data" / "tw_history" /
                     "stock_day.json").read_text(encoding="utf-8"))
    from scripts.tv_harvest import event_set
    print(f"{'code':6s} {'t_day':12s} {'ib_sum':>14s} "
          f"{'official':>14s} {'ratio':>7s}")
    for _, _, eff, names in event_set():
        for code in names:
            b = [r for r in cache.get(code, {}).get("5m", [])
                 if r[0].startswith(eff)]
            if not b:
                continue
            off = None
            for m in sd.get(code, {}):
                for r in sd[code][m]:
                    if r[0] == eff:
                        off = float(r[1])
            if not off:
                continue
            s = sum(r[3] for r in b)
            print(f"{code:6s} {eff:12s} {s:14.0f} {off:14.0f} "
                  f"{s / off:7.3f}")


def probe():
    """Single-name 1-day test:
      python scripts/ib_harvest.py probe 8454
      python scripts/ib_harvest.py probe 2330 20180618
    — separates entitlement problems from data-absence problems and
    measures IB's true historical 5m floor."""
    code = sys.argv[2] if len(sys.argv) > 2 else "8454"
    day = sys.argv[3] if len(sys.argv) > 3 else "20260529"
    ib = _connect()
    ib.reqMarketDataType(1)
    c = _qualify(ib, code)
    if c is None:
        print(f"{code}: no contract on TWSE/TPEX")
        ib.disconnect()
        return
    bars = ib.reqHistoricalData(
        c, endDateTime=f"{day}-06:00:00", durationStr="1 D",
        barSizeSetting="5 mins", whatToShow="TRADES", useRTH=True)
    print(f"{code}: {len(bars)} bars"
          + (f"; last {bars[-1].date} vol {bars[-1].volume}"
             if bars else " — see error above"))
    ib.disconnect()


# APAC probe set: one liquid benchmark per market, IB exchange codes.
# KR is listed although IB retail rarely has KRX — the probe output
# is the answer either way. CN-A rides Stock Connect northbound.
APAC_PROBES = [
    # Japan REMOVED for now (user decision 2026-08-04: TSE Equities
    # L1 = JPY 3,000/mo not yet purchased; re-add the line
    # ("Japan","7203","TSEJ","JPY") when subscribed)
    ("HongKong", "700", "SEHK", "HKD"),
    ("ChinaA-NB", "600519", "SEHKNTL", "CNH"),
    ("Singapore", "D05", "SGX", "SGD"),
    ("Australia", "BHP", "ASX", "AUD"),
    ("India", "RELIANCE", "NSE", "INR"),
    # KRX confirmed working (fee-waived Korea Equities Bundle);
    # "KSE" was a wrong exchange code, not a closed door
    ("Korea", "005930", "KRX", "KRW"),
]


def probe_apac():
    """Per-market floor probe:
      python scripts/ib_harvest.py probe_apac            (recent day)
      python scripts/ib_harvest.py probe_apac 20230616   (past day)
    Reads: bars -> market visible+covered at that date; 'no security
    definition' -> exchange not offered to this account; 'no market
    data permissions' -> subscription missing OR date pre-coverage
    (disambiguate by probing a recent date first)."""
    from ib_async import Stock
    day = sys.argv[2] if len(sys.argv) > 2 else None
    ib = _connect()
    ib.reqMarketDataType(1)
    end = f"{day}-06:00:00" if day else ""
    for mkt, sym, exch, ccy in APAC_PROBES:
        try:
            c = Stock(sym, exch, ccy)
            ib.qualifyContracts(c)
            if not c.conId:
                print(f"{mkt:11s} {sym}@{exch}: NO CONTRACT")
                continue
            bars = ib.reqHistoricalData(
                c, endDateTime=end, durationStr="1 D",
                barSizeSetting="5 mins", whatToShow="TRADES",
                useRTH=True)
            tail = (f"last {bars[-1].date} vol {bars[-1].volume}"
                    if bars else "0 bars")
            print(f"{mkt:11s} {sym}@{exch}: {len(bars)} bars — "
                  f"{tail}")
        except Exception as e:                        # noqa: BLE001
            print(f"{mkt:11s} {sym}@{exch}: ERROR {str(e)[:60]}")
    ib.disconnect()


APAC_OUT = ROOT / "data" / "ib_bars_apac.json"


def fetch_apac_windows():
    """Harvest the APAC manifest (HK decade + CN SAIRs 2018+):
      python scripts/ib_harvest.py fetch_apac
    407 windows, ~6s pacing => ~45 min; resumable/atomic. Window =
    eff-45d -> eff+7d (pre-announcement baseline for the
    anticipation study + the reversal week). endDateTime 09:00 UTC
    covers HK (16:10) and CN (15:00) session ends."""
    import pandas as pd
    manifest = json.loads(
        (ROOT / "data" / "apac_harvest_manifest.json").read_text(encoding="utf-8"))
    ib = _connect()
    ib.reqMarketDataType(1)
    cache = (json.loads(APAC_OUT.read_text(encoding="utf-8"))
             if APAC_OUT.exists() else {})
    done = {w for c in cache.values() for w in c.get("_windows", [])}
    todo = [m for m in manifest
            if f"{m['sym']}|{m['eff']}" not in done]
    print(f"{len(todo)} of {len(manifest)} windows to fetch")
    from ib_async import Stock
    for i, m in enumerate(todo):
        key = f"{m['market']}|{m['sym']}"
        b = (pd.Timestamp(m["eff"])
             + pd.Timedelta(days=7)).strftime("%Y%m%d")
        try:
            c = Stock(m["sym"], m["exch"], m["ccy"])
            ib.qualifyContracts(c)
            if not c.conId:
                raise ValueError("no contract")
            bars = ib.reqHistoricalData(
                c, endDateTime=f"{b}-09:00:00", durationStr="50 D",
                barSizeSetting="5 mins", whatToShow="TRADES",
                useRTH=True)
        except Exception as e:                        # noqa: BLE001
            print(f"{i+1}/{len(todo)} {key} {m['eff']}: FAIL "
                  f"{str(e)[:50]}", flush=True)
            time.sleep(3)
            continue
        rows = [[bar.date.strftime("%Y-%m-%d %H:%M"),
                 float(bar.open), float(bar.close),
                 float(bar.volume)] for bar in bars]
        if not rows:
            print(f"{i+1}/{len(todo)} {key} {m['eff']}: 0 bars — "
                  "retry next run", flush=True)
            time.sleep(6)
            continue
        d = cache.setdefault(key, {"exch": m["exch"],
                                   "side_by_eff": {}})
        existing = {r[0] for r in d.get("5m", [])}
        d["5m"] = sorted(d.get("5m", [])
                         + [r for r in rows if r[0] not in existing])
        d.setdefault("_windows", []).append(
            f"{m['sym']}|{m['eff']}")
        d["side_by_eff"][m["eff"]] = m["side"]
        tmp = APAC_OUT.with_suffix(".tmp")
        tmp.write_text(json.dumps(cache), encoding="utf-8")
        tmp.replace(APAC_OUT)
        print(f"{i+1}/{len(todo)} {key} {m['eff']}: {len(rows)} "
              "bars", flush=True)
        time.sleep(6)
    ib.disconnect()


def sanity_apac():
    """Bar-sums vs the decade study's official daily volumes
    (baostock CN / yfinance HK) on T-days — per-market unit and
    auction-inclusion calibration, exactly as TW's sanity was."""
    cache = json.loads(APAC_OUT.read_text(encoding="utf-8"))
    ref = json.loads((ROOT / "data" / "decade_windows.json")
                     .read_text(encoding="utf-8"))
    print(f"{'key':16s} {'t_day':12s} {'ib_sum':>14s} "
          f"{'official':>14s} {'ratio':>8s}")
    shown = 0
    for rkey, v in ref.items():
        season, code = rkey.split("|")
        sym = (str(int(code[:4])) if code.endswith(".HK")
               else code[3:] if code[:3] in ("sh.", "sz.")
               else None)
        if not sym:
            continue
        for mkt in ("CN", "HK"):
            c = cache.get(f"{mkt}|{sym}")
            if not c:
                continue
            days = {}
            for r in v.get("rows", []):
                days[r[0]] = r[2]
            for d in sorted(days)[-3:]:
                bars = [r for r in c.get("5m", [])
                        if r[0].startswith(d)]
                if not bars or not days[d]:
                    continue
                s = sum(r[3] for r in bars)
                print(f"{mkt+'|'+sym:16s} {d:12s} {s:14.0f} "
                      f"{days[d]:14.0f} {s/days[d]:8.3f}")
                shown += 1
                break
        if shown >= 25:
            break


def probe_tw_deep():
    """Does ANY data type reach deeper than TRADES for TWSE?
      python scripts/ib_harvest.py probe_tw_deep 20180615
    Tests TRADES / MIDPOINT / BID_ASK / ADJUSTED_LAST on 2330."""
    day = sys.argv[2] if len(sys.argv) > 2 else "20180615"
    ib = _connect()
    ib.reqMarketDataType(1)
    c = _contract("2330")
    ib.qualifyContracts(c)
    for what in ("TRADES", "ADJUSTED_LAST", "MIDPOINT", "BID_ASK"):
        try:
            bars = ib.reqHistoricalData(
                c, endDateTime=f"{day}-06:00:00", durationStr="1 D",
                barSizeSetting="5 mins", whatToShow=what,
                useRTH=True)
            tail = (f"last {bars[-1].date}" if bars else
                    "(0 = no data OR request timed out after 30s)")
            print(f"{what:14s}: {len(bars)} bars {tail}",
                  flush=True)
        except Exception as e:                        # noqa: BLE001
            print(f"{what:14s}: ERROR/TIMEOUT {str(e)[:60]}",
                  flush=True)
    ib.disconnect()


if __name__ == "__main__":
    {"verify": verify, "fetch": fetch, "sanity": sanity,
     "probe": probe, "probe_apac": probe_apac,
     "probe_tw_deep": probe_tw_deep,
     "fetch_apac": fetch_apac_windows, "sanity_apac": sanity_apac}[
        sys.argv[1] if len(sys.argv) > 1 else "verify"]()
