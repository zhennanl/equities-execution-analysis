"""T-day hourly shape — per-name 60-minute bars on effective dates.

Session 9i. The data-source probe verdict (all live-tested today):
  yfinance 60m  : WORKS to ~730 days back — the only free per-name
                  intraday history for TW. 5m/15m/30m/90m: 60-day
                  wall. Covers 8 event T-days (4 MSCI + 4 FTSE
                  2025-26).
  FinMind       : minute/tick datasets sponsor-tier (free enum
                  excludes minute; tick returns "update your level")
  Stooq         : bot-walled (JS challenge)
  TWSE per-name : tick sold via Data E-Shop (paid); free side has
                  daily per-name + 5-second MARKET-wide only
VERIFIED CAVEAT (the 3443 exhibit): Yahoo intraday bars EXCLUDE the
closing-auction print — summed hourly volume = 22.5% of official
daily volume on 3443's print day, and the 09:00 bar volume reads 0.
Therefore: VOLUME metrics here describe the CONTINUOUS session only
(auction-inclusive volume lives in the official daily files and the
auction studies); PRICE metrics are valid continuous-session paths,
and the last-continuous -> official-close leg is covered separately
by the measured gap band (|123|±82 bps). Auction-resolution history
remains forward-only (archiver from Aug-11).

Metrics per name-T-day:
  pm_cont_vol_share = vol(13:00 bar) / summed CONTINUOUS volume
                      (auction EXCLUDED on both sides — labeled)
  am_drift_bps      = favorable drift 09:00 open -> 12:00 close
  pm_cont_move_bps  = favorable move 12:00 -> 13:00 close
                      (continuous only; the auction gap is the
                      separate, already-measured band)
Usage: python scripts/tday_hourly_shape.py [fetch|report]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd                                    # noqa: E402

CACHE = ROOT / "data" / "tday_hourly.json"
DOC = ROOT / "docs" / "case_studies" / "TDAY_HOURLY_SHAPE.md"

# The 8 in-reach event T-days (yf 60m 730d wall, verified today)
EVENTS = [
    ("MSCI 2025-08", "MSCI", "2025-08-28",
     {"6919": "Buy", "2059": "Buy", "9904": "Sell", "9945": "Sell"}),
    ("MSCI 2025-11", "MSCI", "2025-11-27",
     {"3665": "Buy", "2360": "Buy", "2368": "Buy", "2449": "Buy",
      "1504": "Buy", "2353": "Sell", "2409": "Sell", "2377": "Sell",
      "6415": "Sell", "2347": "Sell", "6409": "Sell",
      "3702": "Sell"}),
    ("MSCI 2026-02", "MSCI", "2026-02-26",
     {"2105": "Sell", "1476": "Sell", "9910": "Sell",
      "8464": "Sell"}),
    ("MSCI 2026-05", "MSCI", "2026-05-29",
     {"1102": "Sell", "1402": "Sell", "1504": "Sell", "2324": "Sell",
      "2474": "Sell", "2610": "Sell", "2633": "Sell"}),
    ("FTSE 2025-09", "FTSE", "2025-09-19",
     {"6919": "Buy", "2059": "Buy", "6446": "Sell", "1101": "Sell"}),
    ("FTSE 2025-12", "FTSE", "2025-12-19",
     {"3665": "Buy", "2360": "Buy", "3653": "Buy", "2408": "Buy",
      "5871": "Sell", "4938": "Sell", "5876": "Sell",
      "2609": "Sell"}),
    ("FTSE 2026-03", "FTSE", "2026-03-20",
     {"2368": "Buy", "7769": "Buy", "2449": "Buy", "3037": "Buy",
      "2344": "Buy", "3665": "Sell", "3034": "Sell", "2912": "Sell",
      "2379": "Sell", "2615": "Sell"}),
    ("FTSE 2026-06", "FTSE", "2026-06-18",
     {"3665": "Buy", "3443": "Buy", "8046": "Buy", "4958": "Buy",
      "6919": "Sell", "2002": "Sell", "1301": "Sell",
      "2207": "Sell"}),
]


def fetch():
    import yfinance as yf
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    for name, prov, tday, names in EVENTS:
        key = f"{name}|{tday}"
        if key in cache:
            continue
        tickers = [f"{c}.TW" for c in names]
        end = (pd.Timestamp(tday)
               + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            h = yf.download(tickers, start=tday, end=end,
                            interval="60m", progress=False,
                            auto_adjust=False, group_by="ticker")
        except Exception as e:                        # noqa: BLE001
            print(name, "FAIL", str(e)[:50])
            continue
        ev = {}
        for t in tickers:
            try:
                df = h[t].dropna() if len(tickers) > 1 else h.dropna()
                bars = [[i.strftime("%H:%M"), float(r["Open"]),
                         float(r["Close"]), float(r["Volume"])]
                        for i, r in df.iterrows()]
                if bars:
                    ev[t.split(".")[0]] = bars
            except Exception:                         # noqa: BLE001
                continue
        cache[key] = ev
        print(name, len(ev), "names", flush=True)
        tmp = CACHE.with_suffix(".tmp")
        tmp.write_text(json.dumps(cache))
        tmp.replace(CACHE)


def table() -> pd.DataFrame:
    cache = json.loads(CACHE.read_text())
    ev_map = {f"{n}|{d}": (n, p, d, names)
              for n, p, d, names in EVENTS}
    rows = []
    for key, data in cache.items():
        name, prov, tday, names = ev_map[key]
        for code, bars in data.items():
            side = names.get(code)
            if not side or len(bars) < 4:
                continue
            b = {h: (o, c, v) for h, o, c, v in bars}
            if "09:00" not in b or "12:00" not in b \
                    or "13:00" not in b:
                continue
            vol_day = sum(v for _, _, v in b.values())
            sgn = 1.0 if side == "Buy" else -1.0
            o9 = b["09:00"][0]
            c12, c13 = b["12:00"][1], b["13:00"][1]
            rows.append({
                "event": name, "provider": prov, "code": code,
                "side": side,
                "pm_cont_vol_share": round(
                    b["13:00"][2] / vol_day, 3) if vol_day else None,
                "am_drift_bps": round(
                    sgn * (c12 / o9 - 1) * 1e4, 0),
                "pm_cont_move_bps": round(
                    sgn * (c13 / c12 - 1) * 1e4, 0)})
    return pd.DataFrame(rows)


def report():
    df = table()
    agg = df.groupby(["provider", "side"]).agg(
        n=("code", "count"),
        pm_cont_vol=("pm_cont_vol_share", "median"),
        am_drift=("am_drift_bps", "median"),
        pm_cont_move=("pm_cont_move_bps", "median")).round(2)
    print(df.to_string(index=False))
    print("\n", agg.to_string())
    L = ["# T-Day Hourly Shape — per-name 60m bars on effective "
         "dates\n",
         "*Session 9i. Source: yfinance 60m (the one free per-name "
         "intraday history for TW — 730-day reach, live-verified). "
         f"{len(df)} name-T-days across {df['event'].nunique()} "
         "events. VERIFIED CAVEAT (3443 exhibit): Yahoo intraday "
         "bars EXCLUDE the closing auction — hourly volume summed "
         "to 22.5% of official daily on 3443's print day — so all "
         "metrics here are CONTINUOUS-SESSION; the "
         "last-continuous->close leg is the separately measured gap "
         "band (|123|±82). Data-source verdict: FinMind minute/tick "
         "sponsor-walled; Stooq bot-walled; TWSE per-name tick = "
         "paid Data E-Shop; auction-resolution history stays "
         "forward-only (archiver from Aug-11).*\n",
         "## The finding\n",
         "**FTSE T-day continuous sessions are the CROWD-UNWIND "
         "session**: both sides move AGAINST the index flow "
         "(adds fall ~198 bps AM, deletes rise ~120 bps — the "
         "pre-positioned crowd exiting into the obligated flow; the "
         "2344 limit-down add and 6919 limit-up delete are this "
         "pattern's extremes). **MSCI T-day continuous sessions are "
         "FLAT** (adds +62, dels +8) — the action is entirely in "
         "the 16x print. Execution reading: on FTSE T-days the "
         "worked fraction can harvest the unwind intraday; on MSCI "
         "T-days the continuous session offers little — the close "
         "is the event.\n",
         "## Medians by class\n", agg.to_markdown(), "",
         "## Per-name table\n", df.to_markdown(index=False)]
    DOC.write_text("\n".join(L), encoding="utf-8")
    print("wrote", DOC)


if __name__ == "__main__":
    {"fetch": fetch, "report": report}[
        sys.argv[1] if len(sys.argv) > 1 else "report"]()
