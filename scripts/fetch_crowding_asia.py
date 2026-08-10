#!/usr/bin/env python3
"""Build/extend data/crowding_asia_cache.json — the multi-market
crowding archive (session 8g). One normalized TWT93U-style cache per
market: {market: {"short": {date: {code: [bal, 0]}}}}.

Usage:
  python scripts/fetch_crowding_asia.py hk [max_files]
  python scripts/fetch_crowding_asia.py jp [max_files]
  python scripts/fetch_crowding_asia.py tpex [n_days]
  python scripts/fetch_crowding_asia.py status

Incremental: existing dates are skipped, so repeated runs extend the
archive (45s-sandbox-safe chunks). LIVE markets only — KR/MY are
PROTOCOL, IN/ID STRUCTURAL (see event_data.CROWDING_SOURCES).
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.event_data import (CROWDING_SOURCES,                    # noqa
                               fetch_hk_short_positions,
                               fetch_jpx_short_positions,
                               fetch_tpex_short_balance,
                               merge_into_short_cache)

CACHE = Path("data/crowding_asia_cache.json")


def load():
    return json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}


def save(c):
    CACHE.write_text(json.dumps(c), encoding="utf-8")
    for mkt, mc in c.items():
        dates = sorted(mc.get("short", {}))
        n = len(mc.get("short", {}).get(dates[-1], {})) if dates else 0
        print(f"{mkt:10s} {len(dates)} dates "
              f"({dates[0] if dates else '-'} -> "
              f"{dates[-1] if dates else '-'}), latest {n} names")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    arg = int(sys.argv[2]) if len(sys.argv) > 2 else None
    cache = load()
    if mode == "hk":
        mc = cache.setdefault("HongKong", {})
        have = set(mc.get("short", {}))
        for date, df in fetch_hk_short_positions(arg or 8).items():
            if date not in have and not df.empty:
                merge_into_short_cache(mc, date, df, "short_shares")
    elif mode == "jp":
        mc = cache.setdefault("Japan", {})
        have = set(mc.get("short", {}))
        for date, df in fetch_jpx_short_positions(arg or 6).items():
            if date not in have and not df.empty:
                merge_into_short_cache(mc, date, df, "short_shares")
    elif mode == "tpex":
        mc = cache.setdefault("TaiwanOTC", {})
        have = set(mc.get("short", {}))
        d, got, tries = dt.date.today(), 0, 0
        while got < (arg or 5) and tries < 15:
            tries += 1
            d -= dt.timedelta(days=1)
            if d.weekday() >= 5:
                continue
            date = d.isoformat()
            if date in have:
                got += 1
                continue
            df = fetch_tpex_short_balance(d.strftime("%Y/%m/%d"))
            if not df.empty:
                merge_into_short_cache(mc, date, df, "short_bal_lots")
                got += 1
    elif mode == "status":
        for m, s in CROWDING_SOURCES.items():
            print(f"{m:10s} {s['status']:30s} {s['cadence']:7s} "
                  f"{s['source']}")
    save(cache)


if __name__ == "__main__":
    main()
