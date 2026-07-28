#!/usr/bin/env python3
"""Chunked, cached fetch of TWSE short balances (TWT93U) + block trades
(BFIAUU) across the May-SAIR / June-TW50 event windows, plus the latest
TDCC weekly distribution. Re-run until 'ALL CACHED'.
Cache: data/event_data_cache.json (derived data, gitignored).

Usage: python scripts/fetch_event_data.py [n_dates_per_run]
       python scripts/fetch_event_data.py forward
The 'forward' mode appends TODAY's short/block data and a date-keyed
TDCC weekly snapshot — run daily (schedule it) to build the archive
that makes Phase-0 crowding tests properly testable at the Aug 12 QIR.
"""
import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.event_data import (fetch_tdcc_distribution,          # noqa: E402
                               fetch_twse_block_trades,
                               fetch_twse_short_balance)

CACHE = Path("data/event_data_cache.json")

# Event names + controls (false-flagged survivors 1101/1326/2615, anchor
# 2330, ETF 0050 for block-tape context)
KEEP = ["3443", "3665", "8046", "4958", "2002", "1301", "2207", "6919",
        "9910", "3231", "2379", "6669",
        "1102", "2474", "2610", "2324", "2633",
        "1101", "1326", "2615", "2330", "0050"]

DATES = [d.strftime("%Y%m%d")
         for d in pd.bdate_range("2026-04-27", "2026-06-30")]


def forward_mode():
    """Append today's data + date-keyed TDCC snapshot (archive builder).
    Aug-12 QIR watchlist names are added to KEEP before announcement."""
    import datetime as dt
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    cache.setdefault("short", {})
    cache.setdefault("blocks", {})
    cache.setdefault("tdcc_archive", {})
    today = dt.date.today().strftime("%Y%m%d")
    if today not in cache["short"]:
        sb = fetch_twse_short_balance(today)
        if not sb.empty:
            sb = sb[sb["ticker"].isin(KEEP)]
            cache["short"][today] = {
                r["ticker"]: [r["margin_short_bal"], r["sbl_bal"]]
                for _, r in sb.iterrows()}
            bt = fetch_twse_block_trades(today)
            cache["blocks"][today] = [
                [r["ticker"], r["classification"], r["price"],
                 r["volume"], r["value"]]
                for _, r in bt.iterrows() if r["ticker"] in KEEP]
            print(f"forward: {today} appended")
        else:
            print(f"forward: {today} no session yet")
    df = fetch_tdcc_distribution(KEEP)
    if not df.empty:
        wk = str(df["date"].iloc[0])
        if wk not in cache["tdcc_archive"]:
            cache["tdcc_archive"][wk] = df.to_dict("records")
            print(f"forward: TDCC week {wk} archived")
    CACHE.write_text(json.dumps(cache))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "forward":
        forward_mode()
        return
    n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() \
        else 8
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    cache.setdefault("short", {})
    cache.setdefault("blocks", {})
    cache.setdefault("holidays", [])

    pending = [d for d in DATES
               if d not in cache["short"] and d not in cache["holidays"]]
    done = 0
    for date in pending:
        if done >= n:
            break
        sb = fetch_twse_short_balance(date)
        time.sleep(0.6)
        if sb.empty:                       # holiday / no session
            cache["holidays"].append(date)
            done += 1
            continue
        sb = sb[sb["ticker"].isin(KEEP)]
        cache["short"][date] = {
            r["ticker"]: [r["margin_short_bal"], r["sbl_bal"]]
            for _, r in sb.iterrows()}
        bt = fetch_twse_block_trades(date)
        time.sleep(0.6)
        cache["blocks"][date] = [
            [r["ticker"], r["classification"], r["price"], r["volume"],
             r["value"]]
            for _, r in bt.iterrows() if r["ticker"] in KEEP]
        done += 1
        print(f"{date}: short {len(cache['short'].get(date, {}))} names, "
              f"blocks {len(cache['blocks'].get(date, []))}")

    if not pending[done:]:
        if "tdcc" not in cache:
            df = fetch_tdcc_distribution(KEEP)
            cache["tdcc"] = df.to_dict("records")
            print(f"TDCC latest week: {len(df)} rows")
        print("ALL CACHED")
    else:
        print(f"{len(pending) - done} dates remaining")
    CACHE.write_text(json.dumps(cache))


if __name__ == "__main__":
    main()
