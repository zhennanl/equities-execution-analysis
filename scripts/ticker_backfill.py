"""Ticker map for the changes database (c-102).

Resolves every unique (market, security-name) in
msci_changes_db to a local ticker, three tiers:
  A. current member lists (apac_members.json names) — exact/
     fuzzy on normalized names (instant, ~11% — mostly recent)
  B. the TW event registry codes (already joined in the DB)
  C. Yahoo search backfill (this script's main job) — cleaned
     name + market suffix filter; RESUMABLE cache; unresolved
     stored as null and retried only with --retry-null

Cache: data/security_ticker_map.json  {"MKT|NORMNAME": ticker}
After running, rebuild the DB (py scripts\\changes_db.py build)
to join the map into the 'ticker' column.

Usage:
  py scripts\\ticker_backfill.py run [--limit N]
  py scripts\\ticker_backfill.py status
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "data" / "security_ticker_map.json"

SUFFIX = {"Taiwan": (".TW", ".TWO"), "Japan": (".T",),
          "Korea": (".KS", ".KQ"), "HongKong": (".HK",),
          "Australia": (".AX",), "India": (".NS", ".BO"),
          "Malaysia": (".KL",), "Indonesia": (".JK",),
          "Philippines": (".PS",), "Singapore": (".SI",),
          "Thailand": (".BK",), "NewZealand": (".NZ",),
          "China": (".SS", ".SZ", ".HK")}


def norm(s):
    s = re.sub(r"[^A-Z0-9 ]", " ", str(s).upper())
    return re.sub(r"\s+", " ", s).strip()


def clean_for_search(name):
    """Strip MSCI listing-class suffixes that confuse search."""
    s = re.sub(r"\s*\((HK-C|C|A|B|P|F)\)\s*$", "", str(name))
    s = re.sub(r"\s+(A|B|H)$", "", s)
    return s.strip()


def tier_a():
    mem = json.loads((ROOT / "data" / "apac_members.json")
                     .read_text())["markets"]
    out = {}
    for mkt, v in mem.items():
        for tick, nm in (v.get("names") or {}).items():
            if nm:
                out.setdefault(f"{mkt}|{norm(nm)}", tick)
    return out


def run(limit=None, retry_null=False):
    import difflib

    import pandas as pd
    import requests
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    cache = json.loads(MAP.read_text()) if MAP.exists() else {}
    ta = tier_a()
    mem = json.loads((ROOT / "data" / "apac_members.json")
                     .read_text())["markets"]
    todo = []
    for mkt, g in df.groupby("market"):
        namesd = {norm(v): k for k, v in
                  (mem.get(mkt, {}).get("names") or {}).items()
                  if v}
        keys = list(namesd)
        for s in g.security.unique():
            key = f"{mkt}|{norm(s)}"
            if key in cache and (cache[key] or not retry_null):
                continue
            # tier A first (free)
            if key in ta:
                cache[key] = ta[key]
                continue
            # fuzzy only among names sharing the first token
            # (difflib over full lists was the bottleneck)
            tok = norm(s).split(" ")[0]
            cand = [k for k in keys if k.startswith(tok)]
            m = difflib.get_close_matches(norm(s), cand, n=1,
                                          cutoff=0.87)
            if m:
                cache[key] = namesd[m[0]]
                continue
            todo.append((mkt, s, key))
    MAP.write_text(json.dumps(cache))        # persist tier A
    print(f"tier A/fuzzy done; {len(todo)} need Yahoo search")
    if limit:
        todo = todo[:int(limit)]
    ok = 0
    for i, (mkt, s, key) in enumerate(todo):
        try:
            j = requests.get(
                "https://query1.finance.yahoo.com/v1/finance/"
                "search", params={"q": clean_for_search(s),
                                  "quotesCount": 6},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15).json()
            got = None
            for q in j.get("quotes", []):
                sym = q.get("symbol", "")
                if any(sym.endswith(x) for x in SUFFIX[mkt]):
                    got = sym
                    break
            cache[key] = got
            ok += bool(got)
        except Exception:                      # noqa: BLE001
            pass                               # not cached: retry
        if (i + 1) % 10 == 0:
            MAP.write_text(json.dumps(cache))
            print(f"  {i+1}/{len(todo)} (resolved {ok})")
        time.sleep(0.5)
    MAP.write_text(json.dumps(cache))
    res = sum(1 for v in cache.values() if v)
    print(f"map: {res}/{len(cache)} resolved "
          f"({res/max(len(cache),1):.0%}); rerun until stable, "
          "then: py scripts\\changes_db.py build")


def status():
    cache = json.loads(MAP.read_text()) if MAP.exists() else {}
    res = sum(1 for v in cache.values() if v)
    print(f"{res}/{len(cache)} resolved"
          if cache else "not started")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    lim = (sys.argv[sys.argv.index("--limit") + 1]
           if "--limit" in sys.argv else None)
    if cmd == "run":
        run(lim, retry_null="--retry-null" in sys.argv)
    else:
        status()
