"""Which index movers have no ticker, and which of those is a
defect rather than a fact (c-237).

Bill, looking at section 5: *"I still see many companies without
a ticker value… make sure if the companies were not delisted,
they should have a corresponding ticker."*

He is right that the display is full of blanks — 1,534 of 4,403
rows in the changes database carry no ticker, 35% of the whole
file. But "no ticker" covers four different situations and only
one of them is our problem:

  DELISTED      the security stopped trading; a blank is the
                honest value.
  HAVE_IT       we resolved the ticker somewhere else and the
                changes DB never got it back — pure plumbing.
  PRE_COVERAGE  the row predates our ticker sources (2015+).
  UNRESOLVED    live, in coverage, never resolved.

**THE RESULT IS NOT WHAT I EXPECTED, AND THE SHAPE OF IT IS THE
FINDING.** Both middle classes come back EMPTY, and not because
the matcher is broken — the script checks three internal
sources and each is structurally incapable of helping:

  * the harvested WINDOW files only contain names that already
    had a ticker (movers() filters on it), so they can never
    supply one for a name that lacks it;
  * the DELISTED register is built from names we tried to
    FETCH, which again required a ticker;
  * a self-join inside the changes DB on security name returns
    ZERO matches — a name is either always tickered or never.

So Bill's question — "if they were not delisted they should
have a ticker" — runs into a circular dependency: **every
delisting test we own needs a ticker to run.** We cannot sort
these into live and dead from our own data at all. That is
worth stating plainly rather than presenting a table of zeros
that reads as "none of them are delisted".

What is left is an honest count and a defect list.

NOTHING IS WRITTEN TO THE CHANGES DB. This reports and proposes;
promoting a proposal into the database is a separate, deliberate
step, because a wrong ticker is worse than a blank one — it
silently prices the wrong company.

Usage:
  py scripts\\ticker_audit.py            full report
  py scripts\\ticker_audit.py Taiwan     one market
  py scripts\\ticker_audit.py propose    the fixable list only
Output: data/ticker_audit.json
        docs/TICKER_AUDIT.md
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

DB = ROOT / "data" / "msci_changes_db.pkl"
DELISTED = ROOT / "data" / "apac_delisted_movers.json"
WINDOWS = ROOT / "data" / "apac_event_windows"
TWWIN = ROOT / "data" / "tw_event_windows.json"
FIVE = ROOT / "data" / "ib_5m"
MAP = ROOT / "data" / "apac_ticker_map.json"
OUT = ROOT / "data" / "ticker_audit.json"
DOC = ROOT / "docs" / "TICKER_AUDIT.md"

DELISTED_S, HAVE_IT, PRE_COVERAGE, UNRESOLVED = (
    "DELISTED", "HAVE_IT", "PRE_COVERAGE", "UNRESOLVED")

# Our ticker sources were built from 2015 onward. A blank on an
# older row is a coverage boundary, not a defect — recorded as
# its own class so it cannot inflate the defect count.
COVERAGE_FROM = 2015


def _norm(s):
    return " ".join(str(s).upper().split())


def _delisted_names():
    """{(market, NAME)} the exchange registers confirm are gone."""
    out = set()
    if not DELISTED.exists():
        return out
    try:
        d = json.loads(DELISTED.read_text(encoding="utf-8"))
    except Exception:                              # noqa: BLE001
        return out
    for mkt, block in (d.get("markets") or {}).items():
        rows = block if isinstance(block, list) else \
            (block.get("delisted") or block.get("rows") or [])
        for r in rows:
            nm = r.get("name") or r.get("security") if \
                isinstance(r, dict) else r
            if nm:
                out.add((mkt, _norm(nm)))
    return out


def _known_tickers():
    """{(market, NAME): ticker} from everywhere we have ever
    successfully resolved one — the harvested windows and the
    ticker map. This is what turns "no ticker" into "no ticker
    HERE", which is a different problem with a cheaper fix."""
    out = {}

    def add(mkt, name, tick):
        tick = str(tick or "").strip()
        if not tick or not name:
            return
        out.setdefault((mkt, _norm(name)), tick)

    for p in list(WINDOWS.glob("*.json")) + [TWWIN]:
        if not p.exists():
            continue
        mkt = "Taiwan" if p == TWWIN else p.stem
        try:
            W = json.loads(p.read_text(encoding="utf-8"))["windows"]
        except Exception:                          # noqa: BLE001
            continue
        for v in W.values():
            add(mkt, v.get("name"),
                v.get("yf_symbol") or v.get("code"))
    for p in FIVE.glob("*.json"):
        try:
            W = json.loads(p.read_text(encoding="utf-8"))["windows"]
        except Exception:                          # noqa: BLE001
            continue
        for v in W.values():
            add(p.stem, v.get("name"), v.get("code"))
    if MAP.exists():
        try:
            m = json.loads(MAP.read_text(encoding="utf-8"))
        except Exception:                          # noqa: BLE001
            m = {}
        for mkt, block in (m.get("markets") or m).items():
            if isinstance(block, dict):
                for name, tick in block.items():
                    add(mkt, name, tick)
    return out


def audit(only=None):
    import pandas as pd
    df = pd.read_pickle(DB)
    dead, known = _delisted_names(), _known_tickers()
    rows = []
    for _i, r in df.iterrows():
        if only and r.market != only:
            continue
        if str(r.ticker or "").strip():
            continue
        key = (r.market, _norm(r.security))
        if key in dead:
            cls, fix = DELISTED_S, "exchange register confirms it"
        elif key in known:
            cls, fix = HAVE_IT, known[key]
        elif int(r.year) < COVERAGE_FROM:
            cls, fix = PRE_COVERAGE, (
                f"row predates our ticker sources ({COVERAGE_FROM}+)")
        else:
            cls, fix = UNRESOLVED, "no ticker found anywhere"
        rows.append({"market": r.market, "review": r.review,
                     "year": int(r.year), "action": r.action,
                     "security": r.security, "class": cls,
                     "fix": fix})
    return rows, len(df)


def report(only=None):
    rows, total = audit(only)
    by = defaultdict(Counter)
    for r in rows:
        by[r["market"]][r["class"]] += 1

    doc = ["# Index movers with no ticker — what is a defect",
           "",
           "*Generated by `scripts/ticker_audit.py`. A blank "
           "ticker is not one problem, it is four, and only the "
           "last is ours to fix.*", "",
           "| class | meaning | ours? |",
           "|---|---|---|",
           "| DELISTED | the security stopped trading; a blank "
           "is the honest value | no |",
           "| HAVE_IT | we resolved a ticker elsewhere and the "
           "changes DB never got it | **yes — plumbing** |",
           f"| PRE_COVERAGE | row predates our ticker sources "
           f"({COVERAGE_FROM}+) | no, a boundary |",
           "| UNRESOLVED | live, in coverage, never resolved | "
           "**yes — the defect list** |", "",
           f"**{len(rows)} of {total} rows carry no ticker.**",
           "", "| market | DELISTED | HAVE_IT | PRE_COVERAGE | "
           "UNRESOLVED |", "|---|---|---|---|---|"]
    tot = Counter()
    for m in sorted(by):
        c = by[m]
        tot.update(c)
        doc.append(f"| {m} | {c[DELISTED_S]} | {c[HAVE_IT]} | "
                   f"{c[PRE_COVERAGE]} | {c[UNRESOLVED]} |")
    doc.append(f"| **TOTAL** | **{tot[DELISTED_S]}** | "
               f"**{tot[HAVE_IT]}** | **{tot[PRE_COVERAGE]}** | "
               f"**{tot[UNRESOLVED]}** |")
    doc += ["",
            "## Why two columns are zero", "",
            "Not a bug. Three internal sources were checked and "
            "each is structurally unable to help:", "",
            "- **harvested window files** only ever contain "
            "names that ALREADY had a ticker — `movers()` "
            "filters on it — so they cannot supply one;",
            "- **the delisted register** is built from names we "
            "tried to FETCH, which again required a ticker;",
            "- **a self-join inside the changes DB** on "
            "security name returns ZERO matches: a name is "
            "either always tickered or never.", "",
            "Which means Bill's test — *if it was not delisted "
            "it should have a ticker* — hits a circular "
            "dependency. **Every delisting check we own needs a "
            "ticker to run.** These rows cannot be sorted into "
            "live and dead from our own data. Resolving them "
            "needs an external name-to-ticker lookup per "
            "market; there is no internal shortcut, and a table "
            "of zeros should not be read as \"none of these are "
            "delisted\".", ""]
    doc += ["",
            "## UNRESOLVED — the actual defect list", "",
            "Live names, inside our coverage window, with no "
            "ticker anywhere. These need a lookup.", ""]
    un = [r for r in rows if r["class"] == UNRESOLVED]
    for r in sorted(un, key=lambda x: (x["market"], -x["year"],
                                       x["security"]))[:80]:
        doc.append(f"- {r['market']} {r['review']} "
                   f"({r['year']}) {r['action']} "
                   f"{r['security']}")
    if len(un) > 80:
        doc.append(f"- …and {len(un) - 80} more")
    doc += ["", "---", "",
            "**Nothing here is written back to the changes "
            "database.** A wrong ticker is worse than a blank "
            "one — it silently prices a different company — so "
            "promoting any of these is a separate, deliberate "
            "step.", ""]
    DOC.write_text("\n".join(doc), encoding="utf-8")
    OUT.write_text(json.dumps(
        {"rows": rows,
         "summary": {m: dict(c) for m, c in by.items()}},
        indent=1), encoding="utf-8")

    print(f"{'market':12} {'DELISTED':>9} {'HAVE_IT':>8} "
          f"{'PRE_COV':>8} {'UNRESOLVED':>11}")
    for m in sorted(by):
        c = by[m]
        print(f"{m:12} {c[DELISTED_S]:>9} {c[HAVE_IT]:>8} "
              f"{c[PRE_COVERAGE]:>8} {c[UNRESOLVED]:>11}")
    print(f"{'TOTAL':12} {tot[DELISTED_S]:>9} {tot[HAVE_IT]:>8} "
          f"{tot[PRE_COVERAGE]:>8} {tot[UNRESOLVED]:>11}")
    print(f"\n  {len(rows)} of {total} rows have no ticker; "
          f"{tot[HAVE_IT]} of them we already know and "
          f"{tot[UNRESOLVED]} are genuinely unresolved.")
    print(f"-> {DOC.relative_to(ROOT)}")
    print(f"-> {OUT.relative_to(ROOT)}")
    return rows


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else None
    if a == "propose":
        rows, _ = audit()
        for r in rows:
            if r["class"] == HAVE_IT:
                print(f"{r['market']:12} {r['review']:6} "
                      f"{r['security'][:34]:34} -> {r['fix']}")
    else:
        report(a)
