"""Harvest daily OHLC for newly recovered tickers (c-263).

There is deliberately very little here, and that is the point.
`apac_event_days.py` already harvests every row in the changes
database that carries a ticker, keyed `review|code`. A ticker
recovered into `security_ticker_map.json` and rebuilt into the
database is therefore just another row it has not fetched yet.
Writing a second harvester would mean two code paths producing
the same file, drifting apart, and the project has already paid
for that mistake once — TWSE and TPEx were one board short for
years because a second path was never taught the first path's
rules.

So this does three things a plain re-run cannot:

  1 tells you WHICH markets actually gained rows, so you do not
    re-run twelve markets to fetch nineteen windows;
  2 warns about ADR lines, which are recovered as US symbols
    and trade on a US calendar — the same issuer, a different
    session, and a different "effective day close";
  3 reports the before/after so a recovery that added tickers
    but no PRICES is visible rather than silently counted as a
    win. A recovered ticker for a delisted company outside
    Taiwan and India buys nothing, because the price source
    carries live listings only.

Usage
  py scripts\\recovered_harvest.py            what to run
  py scripts\\recovered_harvest.py run        run it
  py scripts\\recovered_harvest.py verify     before/after
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
STATE = ROOT / "data" / "recovered_harvest_state.json"
DELISTED_SAFE = {"Taiwan", "India"}


def _pending():
    """Rows with a ticker and no priced window, by market."""
    from apac_event_days import movers, _windows_for
    out = {}
    for m in sorted({r["market"] for r in _rows()}):
        try:
            mv = movers(m)
        except Exception:                          # noqa: BLE001
            continue
        w = _windows_for(m)
        miss = [(rev, t, a, n) for rev, t, a, n in mv
                if not (w.get(f"{rev}|{str(t).split('.')[0]}")
                        or {}).get("px")]
        if miss:
            out[m] = miss
    return out


def _rows():
    import pandas as pd
    d = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    d = d[(d.year >= 2015)
          & (d.ticker.astype(str).str.strip() != "")]
    return d.to_dict("records")


def _adr_warning():
    p = ROOT / "data" / "foreign_lines.json"
    if not p.exists():
        return []
    try:
        return sorted(json.loads(p.read_text(encoding="utf-8")))
    except Exception:                              # noqa: BLE001
        return []


def plan():
    pend = _pending()
    if not pend:
        print("nothing pending — every tickered row has a "
              "priced window")
        return {}
    print("markets with unpriced rows:\n")
    for m, rows in sorted(pend.items(),
                          key=lambda x: -len(x[1])):
        safe = " (delisted-safe source)" if m in DELISTED_SAFE \
            else " (survivors-only source — a recovered ticker " \
                 "for a dead name will still return nothing)"
        print(f"  {m:12s} {len(rows):4d} rows{safe}")
    print("\nrun:")
    for m in sorted(pend, key=lambda m: -len(pend[m])):
        print(f"  py scripts\\apac_event_days.py yf {m}")
    adr = _adr_warning()
    if adr:
        print(f"\n{len(adr)} recovered ADR line(s). These trade "
              f"on a US calendar:")
        for k in adr[:10]:
            print(f"    {k}")
        print("  Their effective-day close is a US close, hours "
              "after the Asian one.\n  Do not pool them with "
              "local lines in an event study without saying so.")
    return pend


def snapshot():
    from apac_event_days import movers, _windows_for
    snap = {}
    for m in sorted({r["market"] for r in _rows()}):
        try:
            mv = movers(m)
        except Exception:                          # noqa: BLE001
            continue
        w = _windows_for(m)
        keys = {f"{rev}|{str(t).split('.')[0]}"
                for rev, t, _a, _n in mv}
        snap[m] = {"movers": len(keys),
                   "priced": sum(1 for k in keys
                                 if (w.get(k) or {}).get("px"))}
    return snap


def run():
    pend = plan()
    if not pend:
        return
    before = snapshot()
    STATE.write_text(json.dumps(before, indent=1),
                     encoding="utf-8")
    for m in sorted(pend, key=lambda m: -len(pend[m])):
        print(f"\n{'=' * 52}\n{m}\n{'=' * 52}", flush=True)
        subprocess.run([sys.executable,
                        str(ROOT / "scripts" /
                            "apac_event_days.py"), "yf", m],
                       cwd=str(ROOT))
    verify()


def verify():
    after = snapshot()
    before = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() \
        else {}
    print(f"\n{'market':12} {'priced before':>14} "
          f"{'after':>7} {'gained':>8}")
    tb = ta = 0
    for m in sorted(after):
        b = (before.get(m) or {}).get("priced", 0)
        a = after[m]["priced"]
        tb, ta = tb + b, ta + a
        if a != b or after[m]["priced"] < after[m]["movers"]:
            print(f"{m:12} {b:>14} {a:>7} {a - b:>+8}")
    print(f"{'TOTAL':12} {tb:>14} {ta:>7} {ta - tb:>+8}")
    stuck = [m for m in after
             if after[m]["priced"] < after[m]["movers"]
             and (before.get(m) or {}).get("priced", 0)
             == after[m]["priced"]]
    if stuck:
        print("\nrecovered a ticker but no prices — expected "
              "for delisted names outside Taiwan/India:")
        for m in stuck:
            print(f"    {m}: "
                  f"{after[m]['movers'] - after[m]['priced']} "
                  f"still unpriced")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    {"plan": plan, "run": run, "verify": verify}.get(cmd, plan)()
