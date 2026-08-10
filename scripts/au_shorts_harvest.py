"""ASIC daily short positions for AU event windows (c-129).

ASIC publishes, every trading day, the aggregate reported short
position of EVERY ASX product — the best public short data in
APAC, delisted-safe (a name delisted later still appears in the
files from when it traded), direct CSV, no auth:

  https://download.asic.gov.au/short-selling/
      RR{YYYYMMDD}-001-SSDailyAggShortPos.csv
  columns: Product, Product Code, Reported Short Positions,
           Total Product in Issue, % of Total Product in Issue
           Reported as Short Positions

VERIFIED 2026-08-07 from this host (200, CSV). Note the T+4
publication lag ASIC applies — positions are as of the date in
the filename; the file appears ~4 business days later, which
does NOT affect historical harvesting.

For every Australian mover 2015+ we pull the short series over
the event window -> the DEL-side crowding overlay (borrow-build
analogue of Taiwan's SBL).

Usage:  py scripts\\au_shorts_harvest.py harvest
Output: data/au_event_shorts.json  (resumable, day-cached)
"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "au_event_shorts.json"
UA = {"User-Agent": "Mozilla/5.0"}
PAD = 25


def _events():
    sys.path.insert(0, str(ROOT / "scripts"))
    from apac_event_days import calendar, movers
    cal = calendar()
    byrev = {}
    for rev, tick, act, name in movers("Australia"):
        code = str(tick).split(".")[0].upper()
        byrev.setdefault(rev, []).append((code, act, name))
    return cal, byrev


def _day(d):
    """{ASX_code: (short_shares, pct_of_issue)} or None."""
    import requests
    u = ("https://download.asic.gov.au/short-selling/"
         f"RR{d:%Y%m%d}-001-SSDailyAggShortPos.csv")
    r = requests.get(u, headers=UA, timeout=40)
    if r.status_code != 200 or "Product" not in r.text[:200]:
        return None
    out = {}
    txt = r.content.decode("utf-8", errors="ignore")
    # 5 columns; product NAMES can contain commas, so split
    # from the RIGHT into 4 -> [name+code glued? no: rsplit 4]
    for ln in txt.splitlines()[1:]:
        p = ln.rsplit(",", 4)
        if len(p) == 5:
            code = p[1].strip().strip('"').upper()
            try:
                out[code] = (float(p[2]), float(p[4]))
            except ValueError:
                pass
    return out


def harvest():
    cal, byrev = _events()
    cache = (json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists()
             else {"source": "ASIC SSDailyAggShortPos "
                             "(delisted-safe day-files)",
                   "series": {}, "_days": {}})
    for rev in sorted(byrev, key=lambda r: cal[r][0],
                      reverse=True):
        if all(f"{rev}|{c}" in cache["series"]
               for c, _, _ in byrev[rev]):
            continue
        a = (dt.date.fromisoformat(cal[rev][0])
             - dt.timedelta(days=PAD))
        b = (dt.date.fromisoformat(cal[rev][1])
             + dt.timedelta(days=PAD))
        ser = {c: [] for c, _, _ in byrev[rev]}
        d = a
        while d <= b:
            if d.weekday() < 5:
                k = d.isoformat()
                if k in cache["_days"]:
                    day = cache["_days"][k]
                else:
                    full = _day(d)
                    day = ({c: full[c] for c, _, _ in byrev[rev]
                            if full and c in full}
                           if full else {})
                    cache["_days"][k] = day
                    time.sleep(0.7)
                for c, _, _ in byrev[rev]:
                    if c in day:
                        ser[c].append({"d": k,
                                       "short": day[c][0],
                                       "pct": day[c][1]})
            d += dt.timedelta(days=1)
        for c, act, name in byrev[rev]:
            cache["series"][f"{rev}|{c}"] = {
                "rev": rev, "code": c, "action": act,
                "name": name, "ann": cal[rev][0],
                "eff": cal[rev][1], "rows": ser[c]}
        OUT.write_text(json.dumps(cache), encoding="utf-8")
        got = sum(1 for c, _, _ in byrev[rev] if ser[c])
        print(f"AU shorts {rev}: {got}/{len(byrev[rev])}",
              flush=True)
    n = len(cache["series"])
    ok = sum(1 for v in cache["series"].values() if v["rows"])
    print(f"done: {ok}/{n} series", flush=True)


if __name__ == "__main__":
    harvest()
