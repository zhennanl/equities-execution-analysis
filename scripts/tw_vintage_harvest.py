"""TW vintage harvest — the PIT-backtest data unlock (session 9i).

Fetches, per name, the two verified FinMind series that rebuild
historical universes:
  - TaiwanStockShareholding: NumberOfSharesIssued (daily, 2015+),
    foreign holding %, FOL — TWSE + TPEx + DELISTED names
  - TaiwanStockPrice: daily close/volume for names yfinance lacks
    (delisted) — survivorship fix

Cache: data/tw_vintage_cache.json — resumable, atomic writes.
Token: env FINMIND_TOKEN (optional; free registration raises rate
limits). Politeness pacing between requests.

Commands:
  python scripts/tw_vintage_harvest.py probe
  python scripts/tw_vintage_harvest.py fetch [--limit N]
  python scripts/tw_vintage_harvest.py sanity
"""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

API = "https://api.finmindtrade.com/api/v4/data"
CACHE = ROOT / "data" / "tw_vintage_cache.json"
START, END = "2015-01-01", "2026-08-01"
PACE_S = 1.2


def _get(dataset, data_id, start, end):
    import requests
    params = {"dataset": dataset, "data_id": data_id,
              "start_date": start, "end_date": end}
    tok = os.environ.get("FINMIND_TOKEN")
    if tok:
        params["token"] = tok
    r = requests.get(API, params=params, timeout=60)
    r.raise_for_status()
    j = r.json()
    if j.get("status") != 200:
        raise RuntimeError(f"{data_id}: {j.get('msg')}")
    return j["data"]


def _load():
    return json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}


def _save(d):
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    tmp.replace(CACHE)


def harvest_names():
    """~350 names: every decade-key name (incl. delisted) + current
    members + alias-bridge codes + boundary set."""
    names = set()
    ev = ROOT / "data" / "msci_tw_events.json"
    if ev.exists():
        d = json.loads(ev.read_text(encoding="utf-8"))
        for season in d.values():          # {season: {adds:{code:name}}}
            for k in ("adds", "dels"):
                for code in season.get(k, {}):
                    names.add(str(code).split(".")[0])
    br = ROOT / "data" / "decade_bridge.json"
    if br.exists():
        d = json.loads(br.read_text(encoding="utf-8")).get("map", {})
        for key, code in d.items():        # {"TW|NAME": "2330.TW"}
            if key.startswith("TW|") and str(code).endswith(
                    (".TW", ".TWO")):
                names.add(str(code).split(".")[0])
    from scripts.pit_may2026_asia import UNIVERSES
    for t, _ in UNIVERSES["Taiwan"]:
        names.add(t.split(".")[0])
    # corporate-event exits (delisted mid-quarter, absent from the
    # review key — the M&A channel; Inotera/Micron Dec-2016 is the
    # canonical case and the survivorship test anchor)
    names.update({"3474"})
    # c-43: ALL current members (EWT anchor) — completes the
    # historical member ladder for PIT time-travel (never-changed
    # members were previously unpriced at past dates)
    ewt = ROOT / "data" / "ewt_members.json"
    if ewt.exists():
        names.update(json.loads(ewt.read_text(encoding="utf-8"))["codes"])
    return sorted(n for n in names if n and n[0].isdigit())


def probe():
    for ds, sid, s, e in (
            ("TaiwanStockShareholding", "2330", "2015-01-05",
             "2015-01-07"),
            ("TaiwanStockShareholding", "3474", "2016-06-01",
             "2016-06-03"),                    # delisted
            ("TaiwanStockPrice", "3474", "2016-06-01",
             "2016-06-03")):
        try:
            rows = _get(ds, sid, s, e)
            print(f"OK   {ds} {sid}: {len(rows)} rows "
                  f"(e.g. {rows[0].get('NumberOfSharesIssued') or rows[0].get('close')})")
        except Exception as ex:                # noqa: BLE001
            print(f"FAIL {ds} {sid}: {ex}")
        time.sleep(PACE_S)
    print(f"harvest set: {len(harvest_names())} names")


def fetch(limit=None):
    names = harvest_names()
    cache = _load()
    todo = [n for n in names
            if f"sh|{n}" not in cache or f"px|{n}" not in cache]
    if limit:
        todo = todo[:int(limit)]
    print(f"{len(todo)} of {len(names)} names to fetch")
    for i, n in enumerate(todo):
        for tag, ds, keep in (
                ("sh", "TaiwanStockShareholding",
                 ("date", "NumberOfSharesIssued",
                  "ForeignInvestmentSharesRatio",
                  "ForeignInvestmentUpperLimitRatio")),
                ("px", "TaiwanStockPrice",
                 ("date", "close", "Trading_Volume"))):
            key = f"{tag}|{n}"
            if key in cache:
                continue
            try:
                rows = _get(ds, n, START, END)
                # keep monthly-boundary + change rows to bound size:
                # shares change rarely; store first row per month +
                # rows where shares differ from previous
                slim, last = [], None
                for r in rows:
                    v = tuple(r.get(k) for k in keep)
                    month = str(r["date"])[:7]
                    if last is None or v[1:] != last[1:] or \
                            month != str(last[0])[:7]:
                        slim.append(dict(zip(keep, v)))
                        last = v
                cache[key] = slim
                print(f"  [{i+1}/{len(todo)}] {key}: "
                      f"{len(rows)} -> {len(slim)} rows")
            except Exception as ex:            # noqa: BLE001
                print(f"  [{i+1}/{len(todo)}] {key}: FAIL {ex}")
            time.sleep(PACE_S)
        if (i + 1) % 3 == 0:
            _save(cache)
    _save(cache)
    print("done;", sum(1 for k in cache if k.startswith("sh|")),
          "share series,",
          sum(1 for k in cache if k.startswith("px|")),
          "price series cached")


def sanity():
    cache = _load()
    sh = {k: v for k, v in cache.items() if k.startswith("sh|")}
    print(f"{len(sh)} share series")
    ok = 0
    for k, rows in list(sh.items())[:2000]:
        if rows and rows[0]["date"] <= "2015-06-30":
            ok += 1
    print(f"{ok} reach 2015-H1")
    t = cache.get("sh|2330")
    if t:
        first = [r for r in t if r["date"] <= "2015-06-05"][-1]
        v = first["NumberOfSharesIssued"]
        print("2330 shares mid-2015:", v,
              "(expected ~25.93B)", "OK" if
              abs(v - 25.93e9) / 25.93e9 < 0.01 else "MISMATCH")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "probe"
    if cmd == "probe":
        probe()
    elif cmd == "fetch":
        lim = None
        if "--limit" in sys.argv:
            lim = sys.argv[sys.argv.index("--limit") + 1]
        fetch(lim)
    elif cmd == "sanity":
        sanity()
