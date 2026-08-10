"""Exactly where does IB's 5-minute history begin? (c-189)

TWO JOBS, both answering questions the summary probe could not.

  edge MARKET   Binary-searches the true first date on which IB
                serves 5m bars. The earlier figure for Taiwan —
                "around 2023-05" — came from two spot checks
                (2023-03-17 failed, 2023-05-31 worked), which
                brackets a TEN-WEEK window. That is not a date,
                it is a range, and the harvest floor is built on
                it. This narrows it to a few days.

  why MARKET    Prints the RAW IB error for a failed request.
                Japan resolved its contract but returned no bars
                on live, delayed and delayed-frozen alike. Two
                very different things produce that:
                    354 = market data not subscribed  -> paying
                          for the TSE feed would fix it
                    162 = historical service error    -> may be
                          pacing or a data-type permission, and
                          paying might change nothing
                The summary table collapses both to "--". This
                does not.

WHY BISECTION AND NOT A LOOP. IB rate-limits historical
requests hard (roughly 60 per 10 minutes; a burst gets a
multi-minute soft ban). Walking back month by month over a
decade is ~120 requests. Bisecting 2010->today is about 12.

HOLIDAYS ARE THE TRAP. A single date returning nothing proves
nothing — it may be a Sunday or Lunar New Year. So each probe
asks for a 5-DAY window ending at the candidate date and treats
ANY bar as evidence of coverage.

RUNS ON BILL'S MACHINE — needs TWS or IB Gateway with the API
enabled.

Usage:
  python scripts\\ib_history_edge.py edge Taiwan
  python scripts\\ib_history_edge.py why  Japan
  python scripts\\ib_history_edge.py edge          (all working)
Out: data/ib_history_edges.json
"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "ib_history_edges.json"
HOST, PORTS = "127.0.0.1", (7497, 7496, 4001, 4002)
PACE = 11          # seconds between historical requests

sys.path.insert(0, str(ROOT / "scripts"))
try:
    from ib_probe import CANDIDATES
except ImportError:                                # noqa: BLE001
    CANDIDATES = {"Taiwan": ([("TWSE", "2330", "TWD")], "TSMC")}

# markets the c-187 probe proved reachable
WORKING = ["Taiwan", "HongKong", "Singapore", "Australia",
           "India", "China"]


# c-191 BUG I SHIPPED, and its correction.
#
# ib_async does NOT raise a Python exception when IB rejects a
# historical request. It fires an ASYNCHRONOUS error event and
# returns an empty list. So every `except Exception` in this
# file caught nothing, and the script printed
#     "EMPTY (no error)"
# for requests that had in fact returned
#     "Error 162: No market data permissions for TSEJ STK".
#
# The error text was visible in the console only because
# ib_async logs it itself. My own reading guide then said
# "EMPTY with no error -> genuinely nothing there", which was
# exactly backwards for this case: there WAS an error and the
# script was blind to it.
#
# Fix: subscribe to ib.errorEvent and stamp the last error onto
# each request. Nothing is inferred from silence any more.
_ERRORS = []


def _hook(ib):
    def on_err(reqId, code, msg, contract=None):
        _ERRORS.append((reqId, code, str(msg)[:120]))
    try:
        ib.errorEvent += on_err
    except Exception:                              # noqa: BLE001
        pass


def _last_error():
    return _ERRORS[-1] if _ERRORS else None


def _connect():
    try:
        from ib_async import IB
    except ImportError:
        raise SystemExit("pip install ib_async")
    ib = IB()
    for port in PORTS:
        try:
            ib.connect(HOST, port, clientId=93, timeout=8)
            print(f"connected 127.0.0.1:{port}")
            _hook(ib)
            return ib
        except Exception:                          # noqa: BLE001
            continue
    raise SystemExit(f"no TWS/Gateway on {PORTS}")


def _contract(ib, market):
    from ib_async import Stock
    cands, _ = CANDIDATES[market]
    for exch, sym, ccy in cands:
        try:
            det = ib.reqContractDetails(Stock(sym, exch, ccy))
            if det:
                return det[0].contract, f"{sym}@{exch}"
        except Exception:                          # noqa: BLE001
            pass
        time.sleep(0.6)
    return None, None


def _has_data(ib, con, on_date, verbose=False):
    """Any 5m bars in the 5 days ending on_date? Holiday-safe."""
    end = on_date.strftime("%Y%m%d") + "-23:59:59"
    try:
        b = ib.reqHistoricalData(
            con, endDateTime=end, durationStr="5 D",
            barSizeSetting="5 mins", whatToShow="TRADES",
            useRTH=True, formatDate=1)
        ok = bool(b)
    except Exception as e:                         # noqa: BLE001
        ok = False
        if verbose:
            print(f"      {on_date}: {str(e)[:80]}")
    if verbose:
        print(f"      {on_date}: {'DATA' if ok else 'none'}")
    time.sleep(PACE)
    return ok


def edge(market, lo=dt.date(2005, 1, 1), verbose=True):
    """Binary-search the earliest date IB serves 5m bars."""
    ib = _connect()
    con, label = _contract(ib, market)
    if not con:
        print(f"{market}: contract did not resolve")
        ib.disconnect()
        return None
    hi = dt.date.today() - dt.timedelta(days=7)
    print(f"\n{market} ({label}): bisecting {lo} .. {hi}")
    if not _has_data(ib, con, hi, verbose):
        print(f"  {market}: no data even at {hi} — nothing to "
              f"bisect. Run `why {market}`.")
        ib.disconnect()
        return None
    if _has_data(ib, con, lo, verbose):
        print(f"  history reaches at least {lo} (the floor of "
              f"this search)")
        ib.disconnect()
        return lo.isoformat()
    # invariant: lo has NO data, hi HAS data
    n = 0
    while (hi - lo).days > 5:
        mid = lo + (hi - lo) / 2
        if _has_data(ib, con, mid, verbose):
            hi = mid
        else:
            lo = mid
        n += 1
    ib.disconnect()
    print(f"  EDGE: first data between {lo} and {hi} "
          f"({n} requests)")
    res = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    res[market] = {"contract": label,
                   "no_data_on_or_before": lo.isoformat(),
                   "data_by": hi.isoformat(),
                   "measured": dt.date.today().isoformat(),
                   "method": "bisection, 5-day probe window, "
                             "TRADES 5-min, useRTH"}
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"  -> {OUT.name}")
    return hi.isoformat()


def why(market):
    """Raw IB errors for a market that returns no bars."""
    ib = _connect()
    con, label = _contract(ib, market)
    if not con:
        print(f"{market}: contract did not resolve at all")
        ib.disconnect()
        return
    print(f"\n{market} ({label}) — raw responses:")
    for mdt, lab in [(1, "live"), (3, "delayed"),
                     (4, "delayed-frozen")]:
        ib.reqMarketDataType(mdt)
        for what in ("TRADES", "MIDPOINT", "BID_ASK"):
            before = len(_ERRORS)
            try:
                b = ib.reqHistoricalData(
                    con, endDateTime="", durationStr="5 D",
                    barSizeSetting="5 mins", whatToShow=what,
                    useRTH=True, formatDate=1)
            except Exception as e:                 # noqa: BLE001
                b, _ERRORS_local = [], str(e)[:95]
                print(f"  {lab:15} {what:9} -> RAISED "
                      f"{_ERRORS_local}")
                continue
            if b:
                print(f"  {lab:15} {what:9} -> {len(b)} bars")
            else:
                new = _ERRORS[before:]
                if new:
                    rid, code, msg = new[-1]
                    print(f"  {lab:15} {what:9} -> EMPTY, "
                          f"IB error {code}: {msg}")
                else:
                    print(f"  {lab:15} {what:9} -> EMPTY and "
                          f"IB reported NO error")
            time.sleep(2.0)
    print("\n  READ IT LIKE THIS:")
    print("    354  -> market data not subscribed. Paying for "
          "the exchange feed should fix it.")
    print("    162  -> historical service error. Often pacing, "
          "sometimes a data-type permission — paying may NOT "
          "help. Re-run once, alone, before concluding.")
    print("    EMPTY *with* an error code -> the code is the "
          "answer; ignore the emptiness.")
    print("    EMPTY and IB reported NO error -> only THEN is "
          "the data genuinely absent.")
    ib.disconnect()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "edge"
    mkt = sys.argv[2] if len(sys.argv) > 2 else None
    if cmd == "why":
        why(mkt or "Japan")
    elif mkt:
        edge(mkt)
    else:
        for m in WORKING:
            try:
                edge(m)
            except Exception as e:                 # noqa: BLE001
                print(f"{m}: {str(e)[:90]}")
