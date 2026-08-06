"""Roadmap harvester — the remaining liquidity datasets, one
engine (c-68).

Datasets (all probed live before inclusion):
  margin    MI_MARGN day-file 2015+ — retail margin long/short
            balances per stock (raw rows stored, era-tolerant)
  daytrade  TWTB4U day-file 2015+ — per-stock day-trading volume
            and values (CH3 toll-collector CAPACITY)
  blocks    BFIAUU day-file 2015+ — block trades (institutional
            crossing footprint; trade-level rows per watch name)
  taifex    OpenAPI daily futures report — CURRENT-DAY capture
            (capture-forward for single-stock-futures OI, the
            CH3.5 derivatives channel; historical backfill via
            TAIFEX download forms = separate investigation)

All day-file harvesters share the engine: iterate weekdays
2015-01 -> now, fetch, subset to the 150 watch names, store RAW
rows (+ field count) so era changes never corrupt extracts,
resumable/atomic, polite pacing, 60s backoff.

SEQUENCING: these hit the same TWSE host as the SBL/T86
harvesters — run ONE TWSE harvester at a time (any order), in the
second terminal. `taifex` hits a different host and is a light
daily capture (safe anytime; schedule it with the sentinels).

Usage:
  py scripts\\roadmap_harvest.py margin   [--limit N]
  py scripts\\roadmap_harvest.py daytrade [--limit N]
  py scripts\\roadmap_harvest.py blocks   [--limit N]
  py scripts\\roadmap_harvest.py taifex            (today only)
  py scripts\\roadmap_harvest.py status
"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

START = dt.date(2015, 1, 5)
CFG = {
    "margin": {
        "url": ("https://www.twse.com.tw/en/exchangeReport/"
                "MI_MARGN?response=json&date={d}&selectType=ALL"),
        "out": "margin_history.json", "pace": 2.2},
    "daytrade": {
        "url": ("https://www.twse.com.tw/en/exchangeReport/"
                "TWTB4U?response=json&date={d}"),
        "out": "daytrade_history.json", "pace": 2.0},
    "blocks": {
        "url": ("https://www.twse.com.tw/en/block/BFIAUU"
                "?response=json&date={d}&selectType=S"),
        "out": "blocks_history.json", "pace": 2.0},
    "auction5s": {
        # MI_5MINS: OFFICIAL market-wide 5-sec accumulated
        # bid/ask orders + trades, 09:00->13:30 incl. the whole
        # 13:25-13:30 call window (order ARRIVAL into the
        # auction; trades freeze until the 13:30 cross prints).
        # Market-level, NOT per stock — the per-stock indicative
        # path remains capture-forward (Mar-2020 regime).
        # We store rows from 13:20:00 on (121/day) + the 13:00
        # row as an afternoon reference.
        "url": ("https://www.twse.com.tw/en/exchangeReport/"
                "MI_5MINS?response=json&date={d}"),
        "out": "auction5s_history.json", "pace": 2.0,
        "mode": "time"},
}


def watch_names():
    cache = json.loads((ROOT / "data" / "tw_vintage_cache.json")
                       .read_text())
    return {k.split("|")[1] for k in cache
            if k.startswith("sh|")}


def _rows(j):
    if "data" in j and j["data"]:
        return j["data"]
    for t in reversed(j.get("tables", [])):
        if t.get("data"):
            return t["data"]
    return []


def harvest(ds, limit=None):
    import requests
    cfg = CFG[ds]
    out = ROOT / "data" / cfg["out"]
    store = json.loads(out.read_text()) if out.exists() else {}
    watch = watch_names()
    days = []
    d = START
    while d <= dt.date.today():
        if d.weekday() < 5:
            days.append(d.strftime("%Y%m%d"))
        d += dt.timedelta(days=1)
    todo = [x for x in days if x not in store]
    if limit:
        todo = todo[:int(limit)]
    print(f"{ds}: {len(todo)} days to fetch "
          f"(of {len(days)}; {len(store)} stored)")
    fails = 0
    for i, day in enumerate(todo):
        try:
            j = requests.get(cfg["url"].format(d=day), headers={
                "User-Agent": "Mozilla/5.0"}, timeout=25).json()
            if cfg.get("mode") == "time":
                rec = [[str(x) for x in row] for row in _rows(j)
                       if str(row[0]) == "13:00:00"
                       or str(row[0]) >= "13:20:00"]
            else:
                rec = {}
                for row in _rows(j):
                    code = str(row[0]).strip()
                    if code in watch:
                        entry = {"raw": [str(x) for x in row],
                                 "nf": len(row)}
                        if ds == "blocks":
                            rec.setdefault(code, []).append(entry)
                        else:
                            rec[code] = entry
            store[day] = rec
            fails = 0
            if (i + 1) % 25 == 0:
                tmp = out.with_suffix(".tmp")
                tmp.write_text(json.dumps(store))
                tmp.replace(out)
                filled = sum(1 for v in store.values() if v)
                print(f"  {i+1}/{len(todo)} ({day}) | days with "
                      f"data: {filled}")
        except Exception as ex:                # noqa: BLE001
            fails += 1
            print(day, "ERR", str(ex)[:50],
                  "— backing off 60s" if fails >= 3 else "")
            if fails >= 3:
                time.sleep(60)
                fails = 0
        time.sleep(cfg["pace"])
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(store))
    tmp.replace(out)
    print(f"{ds} done; {len(store)} days stored")
    if len(store) < len(days):
        print("-> rerun to continue (resumable)")


def taifex_capture():
    """Capture-forward: today's full TAIFEX daily futures report
    (JSON list). Single-stock-futures OI for watch underlyings is
    extracted at analysis time once the contract->underlying map
    is built (queued investigation); raw capture loses nothing."""
    import requests
    out = ROOT / "data" / "taifex_daily.json"
    store = json.loads(out.read_text()) if out.exists() else {}
    day = dt.date.today().strftime("%Y%m%d")
    r = requests.get("https://openapi.taifex.com.tw/v1/"
                     "DailyMarketReportFut",
                     headers={"User-Agent": "Mozilla/5.0",
                              "Accept": "application/json"},
                     timeout=30)
    data = r.json()
    store[day] = data
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(store))
    tmp.replace(out)
    print(f"taifex: captured {len(data)} contract rows for {day} "
          f"({len(store)} days archived). Schedule daily with the "
          "sentinels; SSF underlying-map = queued investigation")


def status():
    for ds, cfg in CFG.items():
        p = ROOT / "data" / cfg["out"]
        if p.exists():
            s = json.loads(p.read_text())
            filled = sorted(d for d, v in s.items() if v)
            print(f"{ds:9s} {len(s)} days "
                  + (f"({filled[0]}->{filled[-1]})" if filled
                     else "(none with data)"))
        else:
            print(f"{ds:9s} not started")
    p = ROOT / "data" / "taifex_daily.json"
    print("taifex   ",
          f"{len(json.loads(p.read_text()))} days captured"
          if p.exists() else "not started")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    lim = (sys.argv[sys.argv.index("--limit") + 1]
           if "--limit" in sys.argv else None)
    if cmd in CFG:
        harvest(cmd, lim)
    elif cmd == "taifex":
        taifex_capture()
    else:
        status()
