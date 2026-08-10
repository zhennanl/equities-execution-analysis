"""A market proxy for every APAC market (c-272).

    py scripts\\apac_market_proxy.py check    # what is missing
    py scripts\\apac_market_proxy.py run      # harvest
    py scripts\\apac_market_proxy.py verify   # coverage vs the panel

WHY THIS IS THE FIRST JOB FOR ANY NEW MARKET.

A three-week raw return mostly measures the market, not the
index event. Taiwan proved the size of that: market-adjusting
took the published addition drift from +3.4% to +2.0% and the
deletion drift from -1.4% to -2.3%. **Roughly 45% of the
addition "edge" was beta.** Every other APAC market is still
sitting on raw returns because none of them has an index series
on disk — so their numbers carry that same unmeasured error.

WHAT COUNTS AS A PROXY. The rule is that it has to move for the
same reason the stock does, on the same calendar. A broad local
benchmark in LOCAL currency is right; a USD-denominated ETF is
wrong, because it mixes in the exchange rate and its own
premium. So each market takes its own headline index, and the
window prices are local, so no FX enters anywhere.

Yahoo carries all of them as ^-prefixed symbols. The harvest is
one request per market and the whole thing is a few minutes.

INDEX CHOICE, one line of reasoning each:
  Taiwan      ^TWII   TAIEX, already on disk as twii_daily.json
  Japan       ^N225   Nikkei 225. TOPIX (^TOPX) is broader and
                      would be the better match for a mid-cap
                      event; recorded as a known compromise
                      because Yahoo's TOPIX history is patchy.
  Korea       ^KS11   KOSPI. KOSDAQ names take ^KQ11 — the two
                      boards diverge enough to matter, so the
                      harvest keeps both and the analyser picks
                      per name.
  Hong Kong   ^HSI    Hang Seng.
  China       000001.SS  SSE Composite; Shenzhen names take
                      399001.SZ. Same two-board logic as Korea.
  India       ^NSEI   NIFTY 50 — the panel is priced from NSE
                      bhavcopy, so the calendars match.
  Australia   ^AXJO   S&P/ASX 200.
  Singapore   ^STI    Straits Times.
  Malaysia    ^KLSE   FTSE Bursa Malaysia KLCI.
  Thailand    ^SET.BK SET Index.
  Indonesia   ^JKSE   Jakarta Composite.
  New Zealand ^NZ50   S&P/NZX 50.
  Philippines ^PSI    PSEi — harvested even though the price
                      panel is empty, so that market is blocked
                      on one thing rather than two.

THE VERIFY STEP IS NOT OPTIONAL. A proxy that does not cover an
event's dates silently falls back to raw returns for that event,
which mixes adjusted and unadjusted numbers inside one median.
`verify` reports per-market coverage against the actual event
windows and fails loudly under 95%.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "apac_market_proxy.json"
WIN = ROOT / "data" / "apac_event_windows"

PROXY = {
    "Taiwan": [("^TWII", "TAIEX")],
    "Japan": [("^N225", "Nikkei 225")],
    "Korea": [("^KS11", "KOSPI"), ("^KQ11", "KOSDAQ")],
    "HongKong": [("^HSI", "Hang Seng")],
    "China": [("000001.SS", "SSE Composite"),
              ("399001.SZ", "SZSE Component")],
    "India": [("^NSEI", "NIFTY 50")],
    "Australia": [("^AXJO", "S&P/ASX 200")],
    "Singapore": [("^STI", "Straits Times")],
    "Malaysia": [("^KLSE", "FTSE Bursa Malaysia KLCI")],
    "Thailand": [("^SET.BK", "SET Index")],
    "Indonesia": [("^JKSE", "Jakarta Composite")],
    "NewZealand": [("^NZ50", "S&P/NZX 50")],
    "Philippines": [("^PSI", "PSEi")],
}
START = "2014-06-01"        # a year before the panel opens
MIN_COVERAGE = 0.95


def _load():
    return json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() \
        else {"_what": "daily closes, local currency, per market",
              "_source": "Yahoo Finance", "series": {}}


def _save(d):
    OUT.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


def check():
    have = _load()["series"]
    need = []
    for mkt, syms in PROXY.items():
        for sym, name in syms:
            n = len(have.get(sym) or {})
            flag = "" if n > 500 else "  <- MISSING"
            print(f"  {mkt:<12}{sym:<12}{name:<28}{n:>6} days{flag}")
            if n <= 500:
                need.append((mkt, sym, name))
    print(f"\n  to harvest: {len(need)}")
    return need


def run(only=None):
    import yfinance as yf
    d = _load()
    todo = check()
    if only:
        todo = [t for t in todo if t[0] == only]
    print()
    for mkt, sym, name in todo:
        try:
            df = yf.download(sym, start=START, progress=False,
                             auto_adjust=False)
            if df is None or df.empty:
                print(f"  {sym:<12} EMPTY — no data returned")
                continue
            close = df["Close"]
            if hasattr(close, "columns"):
                close = close.iloc[:, 0]
            ser = {str(i.date()): round(float(v), 4)
                   for i, v in close.items() if v == v}
            d["series"][sym] = ser
            d.setdefault("_meta", {})[sym] = {
                "market": mkt, "name": name,
                "first": min(ser), "last": max(ser), "n": len(ser)}
            _save(d)
            print(f"  {sym:<12}{name:<28}{len(ser):>6} days  "
                  f"{min(ser)} .. {max(ser)}", flush=True)
        except Exception as e:                     # noqa: BLE001
            print(f"  {sym:<12} FAILED {type(e).__name__}: "
                  f"{str(e)[:60]}")
        time.sleep(1.5)
    verify()


def verify():
    """Coverage against the ACTUAL event windows, per market.

    The number that matters is not how many days the index has,
    it is what share of the panel's price days it can adjust.
    """
    d = _load()
    series = d.get("series", {})
    print(f"\n{'market':<13}{'proxy':<12}{'event days':>12}"
          f"{'covered':>10}{'':>4}")
    bad = []
    for mkt, syms in PROXY.items():
        f = (ROOT / "data" / "tw_event_windows.json") if mkt == "Taiwan" \
            else WIN / f"{mkt}.json"
        if not f.exists():
            continue
        w = (json.loads(f.read_text(encoding="utf-8"))
             .get("windows") or {})
        days = [r["d"] for v in w.values()
                if isinstance(v, dict) and v.get("px")
                for r in v["px"]]
        if not days:
            print(f"{mkt:<13}{'-':<12}{0:>12}{'no priced windows':>20}")
            continue
        best = None
        for sym, _ in syms:
            s = series.get(sym) or {}
            cov = sum(1 for x in days if x in s) / len(days)
            if best is None or cov > best[1]:
                best = (sym, cov)
        ok = best[1] >= MIN_COVERAGE
        print(f"{mkt:<13}{best[0]:<12}{len(days):>12}"
              f"{best[1]:>9.1%}{'' if ok else '   BELOW 95%':>4}")
        if not ok:
            bad.append((mkt, best[0], best[1]))
    if bad:
        print(f"\n  {len(bad)} market(s) below {MIN_COVERAGE:.0%}. "
              f"Those must stay on RAW returns and say so — a "
              f"partly-adjusted median is worse than an honestly "
              f"unadjusted one.")
        return False
    print("\n  every market has a usable proxy.")
    return True


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "run":
        run(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "verify":
        verify()
    else:
        check()
