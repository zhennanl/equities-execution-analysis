#!/usr/bin/env python3
"""Harvest TWSE T86 institutional flows for the full event history.

    py scripts/tw_t86_harvest.py --dry-run        # plan, no network
    py scripts/tw_t86_harvest.py --windows-only   # just what the study needs
    py scripts/tw_t86_harvest.py                  # everything, resumable

WHY THIS EXISTS. data/twse_institutional.json holds 22 days, because
fetch_investor_flow.py was written for the 2026 windows off a hardcoded
date list and filtered to 15 tickers. That is enough to describe one
review and not enough to test anything: the Taiwan case study had to
report foreign net buy as unavailable. This harvests the history instead.

WHAT IT COSTS. One request returns every stock for one day, so the bill
is per DAY and not per ticker — ~3,479 sessions from the T86 epoch to
today, about 2.9 hours at the default 3s pacing. --windows-only trims it
to sessions inside an event window, which is most of what matters and a
fraction of the wait. Both are resumable: re-running skips what is
already banked, so an interrupted run costs nothing.

THREE DESIGN DECISIONS WORTH KNOWING

1. The trading calendar comes from data/twii_daily.json, not from a
   weekday rule. Taiwan's calendar has lunar-new-year closures, typhoon
   days and make-up SATURDAYS. Guessing would waste ~1,300 requests on
   closed days and still miss the Saturdays.

2. Storage is one gzipped shard per year, not one big JSON. All stocks
   for 14 years is ~2.7M rows; a single file would be ~100MB and would be
   rewritten in full on every flush. Shards keep a resumed run cheap.

3. `total` is NOT stored. parse_t86 proves foreign + trust + dealer ==
   total on every row before the row is accepted, so storing the total
   would be storing a number we already know. Deriving it on read cannot
   drift; a stored copy can.

THE PARSER IS THE PART THAT MATTERS. TWSE has shipped three different
T86 column layouts (11, 15 and 18 columns). Reading historical days with
the modern offsets returns foreign+trust as "foreign" and a gross sell
figure as "trust" — plausible-looking, entirely wrong, and silent. See
agents/investor_flow._T86_LAYOUTS.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.investor_flow import T86LayoutError, parse_t86  # noqa: E402

OUT = ROOT / "data" / "twse_t86"
MANIFEST = OUT / "_manifest.json"
CAL = ROOT / "data" / "twii_daily.json"
WINDOWS = ROOT / "data" / "tw_event_windows.json"

# T86 does not exist before this date; asking is a guaranteed empty
T86_EPOCH = "2012-05-02"
URL = "https://www.twse.com.tw/rwd/en/fund/T86"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36")

# sessions either side of an event to keep under --windows-only
PAD_BEFORE, PAD_AFTER = 25, 25


# ── calendar ──────────────────────────────────────────────────────────────

def sessions() -> list:
    """Real TWSE trading days, from the TAIEX daily series."""
    if not CAL.exists():
        raise SystemExit(f"missing {CAL.relative_to(ROOT)} — the trading "
                         f"calendar comes from it")
    return sorted(k for k in json.loads(CAL.read_text(encoding="utf-8"))
                  if k >= T86_EPOCH)


def window_dates(cal: list) -> set:
    """Sessions inside PAD_BEFORE/PAD_AFTER of any Taiwan event leg.

    Anchored on BOTH the announcement and the effective date, because the
    borrow build and the print are measured from different ends and a
    window that covers only one of them cannot see the handoff.
    """
    if not WINDOWS.exists():
        return set()
    idx = {d: i for i, d in enumerate(cal)}
    keep = set()
    for v in json.loads(
            WINDOWS.read_text(encoding="utf-8"))["windows"].values():
        for anchor in (v.get("ann"), v.get("eff")):
            if not anchor:
                continue
            # an announcement can fall on a non-session; take the next one
            i = idx.get(anchor)
            if i is None:
                nxt = [d for d in cal if d >= anchor]
                if not nxt:
                    continue
                i = idx[nxt[0]]
            lo = max(0, i - PAD_BEFORE)
            keep.update(cal[lo:i + PAD_AFTER + 1])
    return keep


# ── store ─────────────────────────────────────────────────────────────────

def shard_path(date: str) -> Path:
    return OUT / f"{date[:4]}.json.gz"


def read_shard(year: str) -> dict:
    p = OUT / f"{year}.json.gz"
    if not p.exists():
        return {}
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def write_shard(year: str, payload: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / f"{year}.json.gz.tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        json.dump(payload, fh, separators=(",", ":"), sort_keys=True)
    tmp.replace(OUT / f"{year}.json.gz")     # atomic: no half-written shard


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"_what": "TWSE T86 harvest log — one entry per attempted date",
            "_source": URL, "days": {}}


def save_manifest(m: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, indent=1, sort_keys=True),
                        encoding="utf-8")


# ── fetch ─────────────────────────────────────────────────────────────────

def fetch_day(session, date: str, timeout: int = 25):
    """One session's rows, or None when TWSE reports no data.

    Returns (rows, ncols). Raises on transport or layout failure so the
    caller can decide between retrying and stopping.
    """
    import requests

    r = session.get(URL, params={"date": date.replace("-", ""),
                                 "selectType": "ALL", "response": "json"},
                    timeout=timeout)
    if r.status_code == 429:
        raise TimeoutError("rate limited")
    r.raise_for_status()
    try:
        d = r.json()
    except ValueError:
        # TWSE serves an HTML error page under load rather than a 5xx
        raise TimeoutError("non-JSON response (throttled?)")
    if d.get("stat") != "OK":
        return None, 0
    df = parse_t86(d)                        # validates the identity
    if df.empty:
        return None, 0
    ncols = len(d["data"][0])
    rows = [[t, int(f), int(tr), int(de)] for t, f, tr, de in zip(
        df["ticker"], df["foreign_net"], df["trust_net"], df["dealer_net"])]
    return rows, ncols


# ── read side, for downstream scripts ─────────────────────────────────────

def load_t86(tickers=None, start=None, end=None) -> dict:
    """{date: {ticker: {foreign_net, trust_net, dealer_net}}}.

    The reader every analysis should use — it hides the sharding, and it
    reconstructs total_inst_net rather than trusting a stored copy.
    """
    want = set(tickers) if tickers else None
    out = {}
    for p in sorted(OUT.glob("[0-9][0-9][0-9][0-9].json.gz")):
        # NOT p.stem — Path strips one suffix, so "2016.json.gz" stems to
        # "2016.json" and every shard reads back empty
        for date, rows in read_shard(p.name.split(".")[0]).items():
            if (start and date < start) or (end and date > end):
                continue
            day = {}
            for code, f, t, de in rows:
                if want and code not in want:
                    continue
                day[code] = {"foreign_net": f, "trust_net": t,
                             "dealer_net": de, "total_inst_net": f + t + de}
            if day:
                out[date] = day
    return out


# ── driver ────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="start", default=T86_EPOCH)
    ap.add_argument("--to", dest="end",
                    default=dt.date.today().isoformat())
    ap.add_argument("--limit", type=int, default=0,
                    help="stop after N fetched days (0 = no cap)")
    ap.add_argument("--sleep", type=float, default=3.0,
                    help="seconds between requests (default 3.0)")
    ap.add_argument("--windows-only", action="store_true",
                    help="only sessions near an event")
    ap.add_argument("--retry-errors", action="store_true",
                    help="re-attempt dates previously logged as errors")
    ap.add_argument("--dry-run", action="store_true",
                    help="show the plan, touch no network")
    a = ap.parse_args()

    cal = [d for d in sessions() if a.start <= d <= a.end]
    if a.windows_only:
        keep = window_dates(sessions())
        if not keep:
            print("!! no event windows found — falling back to all days")
        else:
            cal = [d for d in cal if d in keep]

    man = load_manifest()
    days = man["days"]
    todo = [d for d in cal
            if d not in days
            or (a.retry_errors and days[d].get("status") == "error")]

    est = len(todo) * a.sleep / 60
    print(f"calendar   {len(cal)} sessions  {a.start} -> {a.end}"
          f"{'  [windows-only]' if a.windows_only else ''}")
    print(f"banked     {len([d for d in cal if d in days])}")
    print(f"to fetch   {len(todo)}   (~{est:.0f} min at {a.sleep}s)")
    if a.dry_run:
        print("\ndry run — nothing fetched")
        if todo:
            print(f"first {todo[0]}  last {todo[-1]}")
        return 0
    if not todo:
        print("\nnothing to do — ALL CACHED")
        return 0
    if a.limit:
        todo = todo[:a.limit]

    import requests
    ses = requests.Session()
    ses.headers.update({"User-Agent": UA,
                        "Referer": "https://www.twse.com.tw/"})

    shards, dirty = {}, set()
    ok = empty = err = 0
    layouts = {}

    def flush():
        for y in sorted(dirty):
            write_shard(y, shards[y])
        dirty.clear()
        save_manifest(man)

    try:
        for n, date in enumerate(todo, 1):
            year = date[:4]
            if year not in shards:
                shards[year] = read_shard(year)
            backoff = a.sleep
            for attempt in range(4):
                try:
                    rows, ncols = fetch_day(ses, date)
                    break
                except T86LayoutError as e:
                    # never retried: a layout change is not transient, and
                    # continuing would bank rows we cannot vouch for
                    print(f"\nLAYOUT CHANGE at {date}\n  {e}")
                    flush()
                    return 2
                except Exception as e:                  # transport/throttle
                    if attempt == 3:
                        days[date] = {"status": "error", "err": str(e)[:120]}
                        err += 1
                        rows = ncols = None
                        break
                    backoff *= 2
                    print(f"  retry {date} in {backoff:.0f}s ({e})")
                    time.sleep(backoff)
            else:
                rows = ncols = None

            if rows:
                shards[year][date] = rows
                dirty.add(year)
                days[date] = {"status": "ok", "rows": len(rows),
                              "cols": ncols}
                layouts[ncols] = layouts.get(ncols, 0) + 1
                ok += 1
            elif rows is None and ncols == 0:
                # TWSE answered and said there is nothing — a real closure
                days[date] = {"status": "empty"}
                empty += 1

            if n % 20 == 0:
                flush()
                print(f"  {n}/{len(todo)}  {date}  "
                      f"ok={ok} empty={empty} err={err}")
            time.sleep(a.sleep)
    except KeyboardInterrupt:
        print("\ninterrupted — flushing what is already fetched")
    finally:
        flush()

    print(f"\nok {ok} | empty {empty} | error {err}")
    if layouts:
        print("layouts seen: " + ", ".join(
            f"{k}-col x{v}" for k, v in sorted(layouts.items())))
    print(f"-> {OUT.relative_to(ROOT)}/  ({len(list(OUT.glob('*.json.gz')))} "
          f"shards)")
    if err:
        print(f"   {err} dates errored — re-run with --retry-errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
