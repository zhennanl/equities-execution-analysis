"""Re-request the 5-minute windows a retry can actually fix.

    py scripts\\ib_5m_retry.py            # show the plan
    py scripts\\ib_5m_retry.py run        # do it

WHAT THE GAP ACTUALLY IS. 2,042 of 2,181 windows are priced
(94%). The 139 empties are NOT one problem, and only one kind
is worth a re-request:

    69  venue_no_history   IB serves no 5m history for that
                           contract. Korea has 48 of them,
                           spread evenly from 2006 to 2025 —
                           so it is not an age limit. These
                           are mostly DELETIONS, and a name
                           deleted from an index is often
                           delisted soon after, which is
                           exactly when IB stops carrying it.
                           Retrying cannot conjure history
                           that the vendor does not hold.
    53  no contract found  the ticker resolves to nothing on
                           its primary exchange or a blank
                           search. Delisted or renamed. This
                           needs IDENTITY RESOLUTION against
                           an external source, not a retry —
                           and writing replacement codes from
                           memory is how a name once got
                           mapped to a US$100bn company in
                           this project.
     9  timeout            THE FIXABLE ONE.
     6  unexplained        also worth one more attempt.
     2  before_edge        the window predates IB's 5m floor.
     1  no_permission      an entitlement wall.

So the plan is 14 windows — Korea 9, India 5 — and this script
does exactly those. It is deliberately not a "re-run
everything": the other 125 would burn an hour of requests to
re-learn what the stored `empty_reason` already says.

A window is only retried if its effective date is at or after
the market's measured 5m edge. Requesting bars from before the
edge is guaranteed to come back empty, and doing it anyway is
how a retry script turns into a slow way of producing the same
answer.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
D = ROOT / "data" / "ib_5m"

RETRYABLE = {"timeout", "unexplained"}


def plan():
    """[(market, key, window)] worth another request."""
    out = []
    for f in sorted(D.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        edge = d.get("edge") or "0000-00-00"
        for k, v in (d.get("windows") or {}).items():
            if v.get("px"):
                continue
            if (v.get("empty_reason") or "") not in RETRYABLE:
                continue
            eff = v.get("eff") or ""
            if not eff or eff < edge:
                continue
            out.append((f.stem, k, v))
    return out


def show():
    p = plan()
    print(f"  {len(p)} window(s) worth a retry\n")
    print(f"  {'market':<10}{'window':<26}{'eff':<12}reason")
    for mkt, k, v in p:
        print(f"  {mkt:<10}{k:<26}{v.get('eff'):<12}"
              f"{v.get('empty_reason')}")
    if not p:
        print("  nothing retryable — every remaining empty is a "
              "vendor limit or an unresolved ticker")
    return p


def run():
    """Re-request each planned window through the existing
    harvester, so pacing, chunking and contract resolution stay
    in ONE place. This script decides WHAT to fetch and never
    how — duplicating the fetch logic is how two harvesters
    start disagreeing about a venue."""
    p = plan()
    if not p:
        show()
        return
    import ib_5m_events as H
    ib = H._connect()
    try:
        for mkt, key, v in p:
            print(f"  {mkt} {key} ...", flush=True)
            try:
                H.one_window(ib, mkt, key, v)
            except AttributeError:
                print("     ib_5m_events has no `one_window`; "
                      "run the market job instead:")
                print(f"     py scripts\\ib_5m_events.py run "
                      f"{mkt}")
                return
            except Exception as e:                 # noqa: BLE001
                print(f"     FAILED {type(e).__name__}: "
                      f"{str(e)[:70]}")
    finally:
        try:
            ib.disconnect()
        except Exception:                          # noqa: BLE001
            pass
    show()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run()
    else:
        show()
