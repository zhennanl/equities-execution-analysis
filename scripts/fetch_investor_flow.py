#!/usr/bin/env python3
"""Cached TWSE institutional-flow fetch for the 2026 event windows.
One call per trading day (all stocks). Re-run until ALL CACHED."""
import datetime as dt
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.investor_flow import fetch_twse_institutional, CACHE_PATH

# May window (MSCI: ann May 12, eff May 29) + June window (TW50: ann
# Jun 5, eff Jun 18) + post days
DATES = ["2026-05-12","2026-05-14","2026-05-18","2026-05-20","2026-05-22",
         "2026-05-25","2026-05-26","2026-05-27","2026-05-28","2026-05-29",
         "2026-06-01","2026-06-02",
         "2026-06-05","2026-06-08","2026-06-10","2026-06-11","2026-06-12",
         "2026-06-15","2026-06-16","2026-06-17","2026-06-18","2026-06-22"]
BATCH = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 5


def main():
    cache = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}
    done = 0
    for ds in DATES:
        if ds in cache or done >= BATCH:
            continue
        try:
            df = fetch_twse_institutional(dt.date.fromisoformat(ds))
            # keep only our 13 event names + TSMC control to keep cache small
            keep = {"3443","3665","8046","4958","2002","1301","2207","6919",
                    "1102","2474","2610","2324","2633","1504","2330"}
            sub = df[df["ticker"].isin(keep)]
            cache[ds] = sub.to_dict(orient="records")
            print(f"OK  {ds}: {len(sub)} event-name rows")
        except Exception as e:
            cache[ds] = []
            print(f"ERR {ds}: {e}")
        done += 1
        CACHE_PATH.parent.mkdir(exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache, indent=1))
        time.sleep(1.5)
    rem = [d for d in DATES if d not in cache]
    print(f"cached {len([d for d in DATES if d in cache])}/{len(DATES)}"
          + (" — ALL CACHED" if not rem else ""))


if __name__ == "__main__":
    main()
