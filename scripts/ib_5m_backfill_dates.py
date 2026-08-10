"""Backfill announcement/effective dates into the 5m windows.

    py scripts\\ib_5m_backfill_dates.py           # show
    py scripts\\ib_5m_backfill_dates.py apply     # write

WHY TAIWAN LOOKED LIKE FOUR EVENTS.

`ib_5m_analysis` reported Taiwan n=4 while the harvest had 47
priced windows. Nothing was wrong with the bars. 43 of those
windows carry no `eff` field, so the analysis could not locate
the print inside them and dropped every one.

The bars were fetched from a date span the harvester computed
and then did not store. That is the whole defect: a window
knows WHEN it starts and ends, and not what the dates MEAN.

The dates exist, keyed identically, in the daily event-window
files — `rev|code` on both sides, 43 of 43 matching. So this
copies them across rather than re-fetching 47 windows of bars
to recover two strings each.

NOTHING IS INVENTED. A 5m window only takes dates from the
daily window with the SAME key, and only if it has none. Where
the daily file has no entry, the 5m window keeps its gap and
stays out of the analysis — a missing date is better than a
guessed one, because the effective date is the anchor every
intraday measure is defined against.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "ib_5m"
DAILY = ROOT / "data" / "apac_event_windows"
TW = ROOT / "data" / "tw_event_windows.json"


def _daily(market):
    p = TW if market == "Taiwan" else DAILY / f"{market}.json"
    if not p.exists():
        return {}
    return (json.loads(p.read_text(encoding="utf-8"))
            .get("windows") or {})


def scan():
    plan = []
    for f in sorted(D.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        src = _daily(f.stem)
        fix = 0
        gap = 0
        for k, v in (d.get("windows") or {}).items():
            if not v.get("px") or v.get("eff"):
                continue
            gap += 1
            s = src.get(k)
            if s and s.get("eff"):
                fix += 1
        if gap:
            plan.append((f.stem, gap, fix))
    return plan


def show():
    plan = scan()
    print(f"  {'market':<12}{'priced, no eff':>16}"
          f"{'recoverable':>13}")
    for m, gap, fix in plan:
        print(f"  {m:<12}{gap:>16}{fix:>13}")
    if not plan:
        print("  every priced window already carries its dates")
    else:
        print(f"\n  total recoverable: "
              f"{sum(f for _m, _g, f in plan)}")
    return plan


def apply():
    total = 0
    for f in sorted(D.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        src = _daily(f.stem)
        n = 0
        for k, v in (d.get("windows") or {}).items():
            if not v.get("px") or v.get("eff"):
                continue
            s = src.get(k)
            if not (s and s.get("eff")):
                continue
            v["eff"] = str(s["eff"])[:10]
            if s.get("ann") and not v.get("ann"):
                v["ann"] = str(s["ann"])[:10]
            v["date_src"] = ("backfilled from the daily event "
                             "window, same rev|code key")
            n += 1
        if n:
            f.write_text(json.dumps(d, separators=(",", ":")),
                         encoding="utf-8")
            print(f"  {f.stem:<12}{n:>5} window(s) dated")
            total += n
    print(f"\n  {total} window(s) updated. Re-run "
          f"`py scripts\\ib_5m_analysis.py`.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "apply":
        apply()
    else:
        show()
