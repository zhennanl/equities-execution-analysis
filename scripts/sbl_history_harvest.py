"""SBL borrow-balance HISTORY harvest — 2015 -> Apr-2026 (c-66).

Closes the borrow-data gap the pattern study declared: our caches
hold securities-lending balances only from Apr-2026. Source:
TWSE's own TWT93U day-file (verified live: serves 2015+ with a
stable 14-field format; ~900-1,300 rows/day, all listed names).

Per day we store ONLY our tracked names (vintage/event set,
~150): {yyyymmdd: {code: [sbl_sell_qty, sbl_balance]}} — the same
shape as the existing live cache, so every borrow analysis reads
both seamlessly.

Field map (14-col row, stable 2015-2026, verified on 2330/2408):
  [0] code | [1-6] margin-short section | [7] SBL prev balance
  [8] SBL sell qty | [9] SBL return | [10] adjustment
  [11] SBL CURRENT BALANCE | [12] next-day quota | [13] note

Resumable (skips stored dates; holidays cached as empty), atomic,
politely paced (~1.8s/request). Full run ≈ 2,800 trading days ≈
1.5-2 h — run it in a SECOND terminal; it hits TWSE, not FinMind,
so it does NOT collide with the census harvest.

Usage:
  py scripts\\sbl_history_harvest.py harvest              (all)
  py scripts\\sbl_history_harvest.py harvest --limit 200  (chunk)
  py scripts\\sbl_history_harvest.py status

Note on borrow FEE RATES (the cost dimension): FinMind's fee-rate
dataset is paid-tier; TWSE publishes SBL transaction fee data on
its securities-lending pages — investigating that endpoint is the
follow-up once balances land. Balances alone already unlock the
decade borrow-panel test.
"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "data" / "sbl_history.json"
URL = ("https://www.twse.com.tw/en/exchangeReport/TWT93U"
       "?response=json&date={d}")
START, END = dt.date(2015, 1, 5), dt.date.today()
# (END was 2026-04-24 in c-66 assuming the live cache covers
# onward; c-82 found the live cache tracks only the 18-name
# watch set — the day-file history now runs to today so ALL
# 150 names stay covered.)


def watch_names():
    cache = json.loads((ROOT / "data" / "tw_vintage_cache.json")
                       .read_text())
    return {k.split("|")[1] for k in cache
            if k.startswith("sh|")}


def _load():
    return json.loads(OUT.read_text()) if OUT.exists() else {}


def _save(d):
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(d))
    tmp.replace(OUT)


def harvest(limit=None):
    import requests
    watch = watch_names()
    store = _load()
    days = []
    d = START
    while d <= END:
        if d.weekday() < 5:
            days.append(d.strftime("%Y%m%d"))
        d += dt.timedelta(days=1)
    todo = [x for x in days if x not in store]
    if limit:
        todo = todo[:int(limit)]
    print(f"{len(todo)} days to fetch (of {len(days)} candidate "
          f"weekdays; {len(store)} already stored); watch set "
          f"{len(watch)} names")
    fails = 0
    for i, day in enumerate(todo):
        try:
            r = requests.get(URL.format(d=day), headers={
                "User-Agent": "Mozilla/5.0"}, timeout=25)
            j = r.json()
            rows = j.get("data", [])
            rec = {}
            for row in rows:
                code = str(row[0]).strip()
                if code in watch:
                    try:
                        sell = float(str(row[8]).replace(",", ""))
                        bal = float(str(row[11]).replace(",", ""))
                        rec[code] = [sell, bal]
                    except Exception:          # noqa: BLE001
                        continue
            store[day] = rec        # empty dict = holiday, cached
            fails = 0
            if (i + 1) % 25 == 0:
                _save(store)
                filled = sum(1 for v in store.values() if v)
                print(f"  {i+1}/{len(todo)} ({day}) | trading "
                      f"days stored: {filled}")
        except Exception as ex:                # noqa: BLE001
            fails += 1
            print(day, "ERR", str(ex)[:50],
                  "— backing off 60s" if fails >= 3 else "")
            if fails >= 3:
                time.sleep(60)
                fails = 0
        time.sleep(1.8)
    _save(store)
    filled = sum(1 for v in store.values() if v)
    print(f"done; {len(store)} days stored ({filled} trading "
          f"days with data)")
    if len(store) < len(days):
        print("-> rerun to continue (resumable)")


def status():
    store = _load()
    filled = {d: len(v) for d, v in store.items() if v}
    if not filled:
        print("empty")
        return
    ds = sorted(filled)
    print(f"{len(store)} days stored, {len(filled)} with data | "
          f"{ds[0]} -> {ds[-1]} | median names/day "
          f"{sorted(filled.values())[len(filled)//2]}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    lim = (sys.argv[sys.argv.index("--limit") + 1]
           if "--limit" in sys.argv else None)
    if cmd == "harvest":
        harvest(lim)
    else:
        status()
