"""T86 history harvest — SIGNED institutional flow by investor
type, per stock, 2015 -> now (c-67).

THE missing dataset for effective-date liquidity work: TWSE's T86
publishes, daily per stock, net buy/sell for each institutional
class — FOREIGN investors, domestic INVESTMENT TRUSTS, and DEALER
PROP DESKS (the arbitrage footprint itself, signed). Our window
features previously used foreign HOLDING deltas; this file gives
signed daily FLOW and decomposes it by who traded.

Format evolves across eras (15 fields in 2015, 18 in 2026) —
we therefore store the RAW row per watch name plus two
era-robust extracts:
  foreign_net = column 3 (stable across eras)
  total_net   = last numeric column (三大法人合計, stable)
Full decomposition (trust / dealer-self / dealer-hedge) is parsed
at ANALYSIS time from the raw rows with the era's field count.

Store: data/t86_history.json
  {yyyymmdd: {code: {"f": foreign_net, "t": total_net,
                     "raw": [...], "nf": n_fields}}}

Pacing note: this hits the SAME TWSE host as the SBL harvester —
run them SEQUENTIALLY in one terminal (SBL first, then this), not
simultaneously. ~2,950 days x ~2.2s ≈ 2h, resumable.

Usage:
  py scripts\\t86_history_harvest.py harvest [--limit N]
  py scripts\\t86_history_harvest.py status
"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "data" / "t86_history.json"
URL = ("https://www.twse.com.tw/en/fund/T86?response=json"
       "&date={d}&selectType=ALL")
START, END = dt.date(2015, 1, 5), dt.date.today()


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


def _num(x):
    try:
        return float(str(x).replace(",", ""))
    except Exception:                          # noqa: BLE001
        return None


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
    print(f"{len(todo)} days to fetch (of {len(days)}; "
          f"{len(store)} stored); watch {len(watch)} names")
    fails = 0
    for i, day in enumerate(todo):
        try:
            j = requests.get(URL.format(d=day), headers={
                "User-Agent": "Mozilla/5.0"}, timeout=25).json()
            rows = j.get("data", [])
            rec = {}
            for row in rows:
                code = str(row[0]).strip()
                if code in watch:
                    nums = [_num(x) for x in row[1:]]
                    last = next((v for v in reversed(nums)
                                 if v is not None), None)
                    rec[code] = {"f": _num(row[3]),
                                 "t": last,
                                 "raw": [str(x) for x in row],
                                 "nf": len(row)}
            store[day] = rec
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
        time.sleep(2.2)
    _save(store)
    filled = sum(1 for v in store.values() if v)
    print(f"done; {len(store)} days ({filled} with data)")
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
