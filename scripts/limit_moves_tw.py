"""Taiwan limit-up/limit-down incidence — baseline vs event days.

Session 9h. TWSE bands are ±10% from previous close, with limit prices
rounded TO TICK (up-limit rounded down, down-limit rounded up; tick
table by price level). We compute exact limit prices per name from the
official daily file (MI_INDEX ALLBUT0999: OHLC + signed change ->
previous close; last-bid/ask columns reveal LOCKED books: at a locked
limit-up there is no ask).

Definitions (per name-day, common stocks: 4-digit non-"00" codes with
volume and a previous close):
  touched_up   : High  >= exact limit-up price
  locked_close : Close >= exact limit-up (still pinned at the bell)
  book_locked  : locked_close AND last-ask empty (no seller remained)
  (mirror definitions for down)

Usage: python scripts/limit_moves_tw.py [fetch|report]
"""
import json
import math
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "tw_limits.json"
DOC = ROOT / "docs" / "case_studies" / "TW_LIMIT_MOVES_2026.md"

BASE_DAYS = [d.strftime("%Y%m%d") for d in
             pd.bdate_range("2026-07-01", "2026-07-28")]
EVENT_DAYS = {"20260226": "MSCI QIR print", "20260320": "FTSE print",
              "20260529": "MSCI SAIR print", "20260618": "FTSE print"}


def tick(p):
    for hi, t in ((10, 0.01), (50, 0.05), (100, 0.1), (500, 0.5),
                  (1000, 1.0)):
        if p < hi:
            return t
    return 5.0


def limit_up(prev):
    x = prev * 1.1
    return round(math.floor(round(x / tick(x), 6)) * tick(x), 2)


def limit_down(prev):
    x = prev * 0.9
    return round(math.ceil(round(x / tick(x), 6)) * tick(x), 2)


def _num(s):
    s = str(s).replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def fetch_day(date):
    r = requests.get("https://www.twse.com.tw/rwd/en/afterTrading/"
                     "MI_INDEX", params={"date": date,
                                         "type": "ALLBUT0999",
                                         "response": "json"},
                     headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    j = r.json()
    for t in j.get("tables", []):
        if "Highest Price" in t.get("fields", []):
            rows = []
            for d in t["data"]:
                code = d[0].strip()
                if len(code) != 4 or code.startswith("00"):
                    continue
                vol, o, h, lo, c = (_num(d[1]), _num(d[4]), _num(d[5]),
                                    _num(d[6]), _num(d[7]))
                chg = _num(d[9]) or 0.0
                sign = 1 if "+" in d[8] else (-1 if "-" in d[8] else 0)
                ask = _num(d[12])
                if not vol or c is None or h is None:
                    continue
                prev = c - sign * chg
                if prev <= 0:
                    continue
                rows.append([code, prev, h, lo, c,
                             1 if ask is None else 0])
            return rows
    return []


def fetch():
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    days = BASE_DAYS + list(EVENT_DAYS)
    todo = [d for d in days if d not in cache]
    print(f"{len(todo)} days missing")
    for d in todo:
        time.sleep(1.5)
        rows = fetch_day(d)
        if rows:
            cache[d] = rows
        print(d, len(rows), flush=True)
        CACHE.write_text(json.dumps(cache), encoding="utf-8")


def day_stats(rows):
    n = len(rows)
    tu = ld = lu_close = ld_close = lock_book = 0
    ups, downs = [], []
    eps = 1e-6
    for code, prev, h, lo, c, noask in rows:
        lu, ldn = limit_up(prev), limit_down(prev)
        if h >= lu - eps:
            tu += 1
            if c >= lu - eps:
                lu_close += 1
                ups.append(code)
                if noask:
                    lock_book += 1
        if lo is not None and lo <= ldn + eps:
            ld += 1
            if c <= ldn + eps:
                ld_close += 1
                downs.append(code)
    return {"n": n, "touched_up": tu, "locked_up": lu_close,
            "book_locked_up": lock_book, "touched_down": ld,
            "locked_down": ld_close, "up_names": ups,
            "down_names": downs}


def table():
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    rows = []
    for d in sorted(cache):
        s = day_stats(cache[d])
        rows.append({"date": d, "kind": EVENT_DAYS.get(d, "baseline"),
                     **{k: s[k] for k in
                        ("n", "touched_up", "locked_up",
                         "book_locked_up", "touched_down",
                         "locked_down")},
                     "pct_touch_up": round(100 * s["touched_up"]
                                           / s["n"], 2),
                     "pct_lock_up": round(100 * s["locked_up"]
                                          / s["n"], 2),
                     "pct_touch_dn": round(100 * s["touched_down"]
                                           / s["n"], 2),
                     "up_names": s["up_names"][:12],
                     "down_names": s["down_names"][:12]})
    return pd.DataFrame(rows)


def report():
    df = table()
    base = df[df["kind"] == "baseline"]
    print(df.drop(columns=["up_names", "down_names"]).to_string(
        index=False))
    print(f"\nbaseline avg: touch-up {base['pct_touch_up'].mean():.2f}%"
          f"  lock-up {base['pct_lock_up'].mean():.2f}%"
          f"  touch-down {base['pct_touch_dn'].mean():.2f}%")
    return df


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    {"fetch": fetch, "report": report}[cmd]()
