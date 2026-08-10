"""Drop harvested windows whose ticker is no longer the one we
would fetch (c-259).

A window file is keyed `review|code`. When a ticker correction
lands (see `ticker_corrections.py`) the old key stops matching
any row in the changes database, and three things go wrong if
it is left in place:

  1. it still holds PRICES — for the wrong company — and any
     reader that keys off `review|code` without re-deriving the
     code from the database will happily use them;
  2. it inflates the harvested count, so coverage looks better
     than it is;
  3. the corrected row shows as "missing", which is correct,
     but the pair together reads as "we lost a window" rather
     than "we replaced a wrong one".

This removes ONLY keys that no longer correspond to any
current review x ticker pair. A window that is simply empty is
left alone — absence is a result, and this is not a cleaner.

Usage:  py scripts\\window_orphans.py          # report
        py scripts\\window_orphans.py apply
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
DIR = ROOT / "data" / "apac_event_windows"


def _wanted(market):
    """{review|code} we would fetch today."""
    from apac_event_days import movers
    out = set()
    for rev, tick, *_ in movers(market):
        code = str(tick).split(".")[0]
        out.add(f"{rev}|{code}")
        out.add(f"{rev}|{tick}")
    return out


def run(apply=False):
    total = 0
    for p in sorted(DIR.glob("*.json")):
        mkt = p.stem
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:                          # noqa: BLE001
            continue
        want = _wanted(mkt)
        orphans = [k for k in d.get("windows", {})
                   if k not in want]
        if not orphans:
            continue
        total += len(orphans)
        print(f"{mkt}: {len(orphans)} orphaned window(s)")
        for k in orphans[:12]:
            w = d["windows"][k]
            n = len(w.get("rows") or w.get("px") or [])
            print(f"    {k:22s} {n:4d} rows — "
                  f"{w.get('name', '')[:34]}")
        if len(orphans) > 12:
            print(f"    ... and {len(orphans) - 12} more")
        if apply:
            for k in orphans:
                d["windows"].pop(k, None)
            p.write_text(json.dumps(d), encoding="utf-8")
    if not total:
        print("no orphaned windows")
    elif apply:
        print(f"\nremoved {total} orphaned window(s)")
    else:
        print(f"\n{total} orphaned — re-run with `apply` to "
              f"remove, then re-fetch the affected markets")
    return total


if __name__ == "__main__":
    run(apply="apply" in sys.argv[1:])
