"""Does TWT93U actually serve back to its published start? (c-226)

TWSE publishes the answer on the report page itself:

    TWT93U 融券借券賣出餘額
    「本資訊自民國94年7月1日起開始提供」  = 2005-07-01
    https://www.twse.com.tw/zh/trading/margin/twt93u.html

Which is TEN YEARS deeper than the 2015 our docs asserted, twice,
without a source. c-225 downgraded that claim to "unmeasured" after
our own probe served 2014-06-16; c-226 loaded the page and found the
claim was simply false.

So this script's job changed. It no longer hunts for an unknown
floor — it CHECKS THE PUBLISHED ONE, because a published start date
and what the JSON endpoint returns are different facts, and only one
of them is the one our harvester lives with.

Walks back from today to the published start, then bisects if a
region comes back empty. TWSE holidays and suspensions mean ONE
empty day proves nothing, so each candidate is tried on up to 4
nearby trading days and counts as served if any returns rows.

Politely paced. Hits TWSE — run it in its own terminal, not
alongside another TWSE harvest.

Usage:
  py scripts\\sbl_floor_probe.py            walk + bisect
  py scripts\\sbl_floor_probe.py 2006-03-01 test one date
"""
import datetime as dt
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sbl_floor.json"
# TWSE's own published start for TWT93U (ROC 94-07-01).
PUBLISHED_START = "2005-07-01"
URL = ("https://www.twse.com.tw/en/exchangeReport/TWT93U"
       "?response=json&date={d}")
PACE = 2.0
NEARBY = 4          # trading days to try around a candidate


def _fetch(d):
    """Rows for one day, or None if TWSE served nothing."""
    req = urllib.request.Request(
        URL.format(d=d.strftime("%Y%m%d")),
        headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            j = json.loads(r.read().decode("utf-8"))
    except Exception as e:                         # noqa: BLE001
        print(f"    {d} transport error {type(e).__name__}")
        return None
    finally:
        time.sleep(PACE)
    if str(j.get("stat", "")).upper() != "OK":
        return None
    return j.get("data") or []


def served(d0):
    """Did TWSE serve this WEEK? (holidays prove nothing.)"""
    d, tried = d0, 0
    while tried < NEARBY:
        if d.weekday() < 5:
            rows = _fetch(d)
            tried += 1
            if rows:
                print(f"    {d}  {len(rows)} rows")
                return d, len(rows)
            print(f"    {d}  empty")
        d += dt.timedelta(days=1)
    return None, 0


def probe():
    today = dt.date.today()
    print("TWT93U floor probe — doubling walk, then bisect\n")
    good, bad = None, None
    # reaches past the published 2005-07-01 start
    for yrs in (1, 2, 4, 6, 8, 10, 12, 16, 19, 21, 24):
        cand = today.replace(year=today.year - yrs)
        print(f"  -{yrs}y  {cand}")
        hit, n = served(cand)
        if hit:
            good = (hit, n)
        else:
            bad = cand
            break
    if good is None:
        print("\nNo date served. TWSE may be unreachable — this "
              "is a transport result, not a data floor.")
        return
    if bad is None:
        print(f"\nServed as far back as the walk went "
              f"({good[0]}). Extend STEPS if you want more.")
        res = {"floor_at_or_before": good[0].isoformat(),
               "bracket": [None, good[0].isoformat()]}
    else:
        lo, hi = bad, good[0]
        print(f"\n  bracket {lo} .. {hi} — bisecting")
        while (hi - lo).days > 20:
            mid = lo + (hi - lo) / 2
            print(f"  mid {mid}")
            hit, n = served(mid)
            if hit:
                hi = hit
            else:
                lo = mid
        res = {"floor_at_or_before": hi.isoformat(),
               "last_empty": lo.isoformat(),
               "bracket": [lo.isoformat(), hi.isoformat()]}
    res.update(measured=dt.date.today().isoformat(),
               source="TWSE TWT93U day-file, en endpoint",
               published_start=PUBLISHED_START,
               note="Compare against published_start. If the "
                    "endpoint stops later than TWSE says it "
                    "publishes, that gap is the real limit "
                    "and belongs in the docs. Our 2015 "
                    "harvest start is a separate CHOICE.")
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"\n-> {OUT.name}: {json.dumps(res, indent=1)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        d = dt.date.fromisoformat(sys.argv[1])
        print(f"single date {d}")
        hit, n = served(d)
        print("SERVED" if hit else "NOTHING",
              f"({n} rows)" if hit else "")
    else:
        probe()
