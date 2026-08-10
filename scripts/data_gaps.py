"""Every missing datapoint, classified by whether one more
fetch can recover it (c-232).

WHY THIS EXISTS. Bill wants to run the harvest ONE more time
and then close the book: whatever is still missing after that
run is excluded from the analysis. That decision needs a list
that separates three things a coverage count cannot:

  RETRY      — never attempted, or failed for a reason that a
               re-run can plausibly fix (timeout, a symbol our
               code got wrong). Worth the request.
  NEEDS_CODE — the data exists and our harvester cannot reach
               it because of something we have not written yet.
               A re-run of the SAME code will not help; this is
               the class that is invisible in a coverage table
               and is the reason this script exists.
  STRUCTURAL — measured venue floor, missing entitlement,
               excluded market, or a security that stopped
               trading. No re-run and no code change recovers
               it. This is the honest exclusion list.

The distinction that matters most is the middle one. A window
that has failed three times looks identical to a window whose
market we never wrote a harvester for, and only one of those is
worth Bill's evening.

Usage:
  py scripts\\data_gaps.py            full report
  py scripts\\data_gaps.py plan       just the commands to run
  py scripts\\data_gaps.py freeze     after the final run:
                                      write the exclusion list
Output: data/data_gaps.json
        docs/DATA_GAPS.md
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

FIVE = ROOT / "data" / "ib_5m"
DAILY = ROOT / "data" / "apac_event_windows"
TWD = ROOT / "data" / "tw_event_windows.json"
OUT = ROOT / "data" / "data_gaps.json"
DOC = ROOT / "docs" / "DATA_GAPS.md"

RETRY, NEEDS_CODE, STRUCTURAL = "RETRY", "NEEDS_CODE", "STRUCTURAL"

# Shenzhen and Shanghai code prefixes. Used to catch a ticker
# whose SUFFIX disagrees with its NUMBER — the number is the
# fact, the suffix is decoration (the c-225 lesson).
SZ_PRE = ("000", "001", "002", "003", "300", "301")
SH_PRE = ("600", "601", "603", "605", "688", "689")


def _load(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))["windows"]
    except Exception:                              # noqa: BLE001
        return {}


def _reason(w):
    """Normalise a stored failure into one label."""
    if w is None:
        return "never_attempted"
    s = str(w.get("stopped_early") or w.get("note")
            or w.get("parse_error") or "").lower()
    if "permission" in s:
        return "no_permission"
    if "timeout" in s or "cancelled" in s or "reported no error" in s:
        return "timeout"
    if "no contract" in s or "no security definition" in s:
        return "no_contract"
    if "no data" in s or "hmds" in s:
        return "venue_no_history"
    if w.get("confirmed_delisted"):
        return "confirmed_delisted"
    if not s:
        return "empty_no_reason"
    return "unexplained"


# ---------------------------------------------------------------
# 5-MINUTE
# ---------------------------------------------------------------
def five_minute():
    import ib_5m_events as M
    rows = []
    for m in M.EXCH:
        if not M._edge_for(m):
            continue
        W = _load(FIVE / f"{m}.json")
        for rev, tick, act, name, _a, _b in M.jobs(m):
            w = W.get(f"{rev}|{tick}")
            if w and w.get("px"):
                continue
            why = _reason(w)
            venue = M._probe_venue(m, str(tick))
            # a measured floor is a FACT about IB's archive, and
            # jobs() should already have dropped these — if one
            # survives, it is because the event sits after the
            # floor and the name still returned nothing
            edge = M._edge_for_code(m, str(tick))
            if why == "no_permission":
                cls, fix = STRUCTURAL, (
                    f"{venue} is not entitled on this account")
            elif why == "venue_no_history" and venue in (
                    "KRX_KOSDAQ",):
                cls, fix = STRUCTURAL, (
                    f"{venue} 5m history begins {edge} — measured, "
                    f"all three probes agreeing")
            elif why == "venue_no_history":
                cls, fix = STRUCTURAL, (
                    "contract resolved, IB served no bars for "
                    "this period — a listing younger than its "
                    "window, or a board floor we have measured")
            elif why in ("timeout", "empty_no_reason",
                         "unexplained"):
                cls, fix = RETRY, (
                    "transient — the request failed, IB did not "
                    "say the data is absent")
            elif why == "no_contract":
                cls, fix = RETRY, (
                    "symbol did not resolve; c-222/c-229 added "
                    "suffix-stripping, an ADR fallback, IB's own "
                    "search and the 9-char NSE truncation")
            else:
                cls, fix = RETRY, "never requested"
            rows.append({"dataset": "5m", "market": m, "rev": rev,
                         "code": str(tick), "action": act,
                         "name": str(name)[:40], "venue": venue,
                         "reason": why, "class": cls, "fix": fix,
                         "tries": (w or {}).get("tries", 0)})
    return rows


# ---------------------------------------------------------------
# DAILY
# ---------------------------------------------------------------
def _tw_board(code):
    p = ROOT / "data" / "tw_mieu_universe.json"
    if not p.exists():
        return None
    try:
        return ((json.loads(p.read_text(encoding="utf-8"))["universe"]
                 .get(str(code)) or {}).get("mkt"))
    except Exception:                              # noqa: BLE001
        return None


def daily():
    import apac_event_days as A
    import markets as K
    rows = []
    for m in sorted(set(A.YF_MARKETS) | set(A.ELSEWHERE)
                    | {"India"}):
        W = A._windows_for(m)
        for rev, tick, act, name in A.movers(m):
            code = str(tick).split(".")[0]
            w = W.get(f"{rev}|{code}")
            if w and w.get("px"):
                continue
            why = _reason(w)
            cls, fix = RETRY, "never requested"
            if not K.is_active(m):
                cls, fix = STRUCTURAL, (
                    f"{m} excluded centrally — "
                    f"{K.why_excluded(m) or 'no data source'}")
            elif m == "Taiwan" and _tw_board(code) == "tpex":
                # THE FINDING. 139 priced Taiwan windows are all
                # TWSE and not one is TPEx: the daily harvester
                # reads STOCK_DAY, which is the TWSE day-file.
                # TPEx publishes its own. This is not a failed
                # fetch, it is a harvester that was only ever
                # written for one of Taiwan's two boards.
                cls, fix = RETRY, (
                    "TPEx-listed. tw_event_window.py read TWSE "
                    "STOCK_DAY only until c-232; it now tries "
                    "the TPEx day-file first for OTC codes and "
                    "re-asks empty windows")
            elif why == "confirmed_delisted":
                cls, fix = STRUCTURAL, (
                    "the exchange register confirms the security "
                    "is gone; a survivors-only source cannot "
                    "price it")
            elif m == "China" and _suffix_wrong(str(tick)):
                cls, fix = NEEDS_CODE, (
                    f"ticker {tick} carries a suffix its NUMBER "
                    f"contradicts; _china_yf trusts the suffix")
            elif w and w.get("tried_symbols"):
                cls, fix = RETRY, (
                    "tried " + ", ".join(
                        str(x) for x in w["tried_symbols"][:3])
                    + " — a predecessor or alternate line may "
                      "exist that we have not mapped")
            rows.append({"dataset": "daily", "market": m,
                         "rev": rev, "code": code, "action": act,
                         "name": str(name)[:40],
                         "venue": _tw_board(code) or "",
                         "reason": why, "class": cls, "fix": fix,
                         "tries": (w or {}).get("tries", 0)})
    return rows


def _suffix_wrong(tick):
    t = str(tick)
    base, suf = t.split(".")[0], t[-3:]
    if suf not in (".SS", ".SZ") or not base.isdigit() \
            or len(base) != 6:
        return False
    want = ".SS" if base[:3] in SH_PRE else \
           ".SZ" if base[:3] in SZ_PRE else None
    return bool(want) and want != suf


# ---------------------------------------------------------------
def report(rows=None):
    """Write both artifacts. `rows` may be handed in.

    c-274, found while profiling the suite. `five_minute() +
    daily()` walks every job list in the repo and parses ~14MB
    of window JSON — about 27 seconds. The test file knew that
    and built a module-scoped fixture to pay it once, with a
    docstring saying so. Then the last test took the cached
    rows and called `report()`, whose first line rebuilt them
    from scratch, so the fixture cached the work and the one
    test that most needed the cache went around it. 27s of
    setup plus 27s of call made this one file a third of the
    entire suite's runtime.

    Accepting `rows` costs one parameter and lets a caller that
    already has them say so.
    """
    if rows is None:
        rows = five_minute() + daily()
    by = defaultdict(lambda: defaultdict(Counter))
    for r in rows:
        by[r["dataset"]][r["market"]][r["class"]] += 1

    doc = ["# Missing trading data — what one more run can fix",
           "",
           "*Generated by `scripts/data_gaps.py`. Every row is a "
           "datapoint we asked for and do not have, classified "
           "by whether re-running the harvester can recover "
           "it.*", "",
           "| class | meaning | worth another fetch? |",
           "|---|---|---|",
           "| **RETRY** | never attempted, or failed for a "
           "reason a re-run can fix | **yes** |",
           "| **NEEDS_CODE** | the data exists; our harvester "
           "cannot reach it yet | no — write the code first |",
           "| **STRUCTURAL** | measured floor, missing "
           "entitlement, excluded market, dead security | "
           "**no — exclude and say so** |", ""]

    for ds in ("5m", "daily"):
        tot = Counter()
        doc += [f"## {ds}", "",
                "| market | RETRY | NEEDS_CODE | STRUCTURAL |",
                "|---|---|---|---|"]
        for m in sorted(by[ds]):
            c = by[ds][m]
            tot.update(c)
            doc.append(f"| {m} | {c[RETRY]} | {c[NEEDS_CODE]} "
                       f"| {c[STRUCTURAL]} |")
        doc.append(f"| **TOTAL** | **{tot[RETRY]}** | "
                   f"**{tot[NEEDS_CODE]}** | "
                   f"**{tot[STRUCTURAL]}** |")
        doc.append("")

    # the NEEDS_CODE detail, because it is the actionable half
    nc = [r for r in rows if r["class"] == NEEDS_CODE]
    doc += ["## What needs code, not another request", ""]
    if nc:
        seen = {}
        for r in nc:
            seen.setdefault((r["dataset"], r["market"],
                             r["fix"]), []).append(r)
        for (ds, m, fix), g in sorted(seen.items()):
            doc.append(f"- **{m} / {ds} — {len(g)} windows.** "
                       f"{fix}")
    else:
        doc.append("_none_")
    doc.append("")

    # the structural detail, grouped by reason
    doc += ["## What is gone for good", "",
            "These are the honest exclusions. Every one of them "
            "should be stated wherever the affected market is "
            "analysed.", ""]
    st = defaultdict(list)
    for r in rows:
        if r["class"] == STRUCTURAL:
            st[(r["dataset"], r["market"], r["fix"])].append(r)
    for (ds, m, fix), g in sorted(st.items()):
        doc.append(f"- **{m} / {ds} — {len(g)} windows.** {fix}")
    doc.append("")

    doc += ["## The run", "",
            "```", *plan_lines(rows), "```", "",
            "After that run, `py scripts\\data_gaps.py freeze` "
            "writes `data/data_gaps_final.json` — the list the "
            "analysis excludes, with the reason attached to "
            "each row so no future reader has to guess whether "
            "a hole was a limit or an oversight.", ""]

    DOC.write_text("\n".join(doc), encoding="utf-8")
    OUT.write_text(json.dumps(
        {"rows": rows,
         "summary": {ds: {m: dict(c) for m, c in mm.items()}
                     for ds, mm in by.items()}}, indent=1),
        encoding="utf-8")

    print(f"{'dataset':7} {'market':11} {'RETRY':>6} "
          f"{'NEEDS_CODE':>11} {'STRUCTURAL':>11}")
    for ds in ("5m", "daily"):
        for m in sorted(by[ds]):
            c = by[ds][m]
            print(f"{ds:7} {m:11} {c[RETRY]:>6} "
                  f"{c[NEEDS_CODE]:>11} {c[STRUCTURAL]:>11}")
    print(f"\n-> {DOC.relative_to(ROOT)}")
    print(f"-> {OUT.relative_to(ROOT)}")
    print("\nRUN THIS:")
    for ln in plan_lines(rows):
        print("  " + ln)
    return rows


def plan_lines(rows=None):
    rows = rows if rows is not None else (five_minute() + daily())
    out, seen = [], set()
    five = sorted({r["market"] for r in rows
                   if r["dataset"] == "5m"
                   and r["class"] == RETRY})
    if five:
        out.append("py scripts\\ib_5m_events.py fetch"
                   f"   :: {', '.join(five)}")
    # c-232: Taiwan daily is NOT a Yahoo market — it has its own
    # delisted-safe TWSE/TPEx harvester, and sending it through
    # `yf Taiwan` would quietly harvest the wrong thing.
    if any(r["dataset"] == "daily" and r["market"] == "Taiwan"
           and r["class"] in (RETRY, NEEDS_CODE) for r in rows):
        out.append("py scripts\\tw_event_window.py harvest"
                   "   :: now covers TPEx (c-232)")
    day = sorted({r["market"] for r in rows
                  if r["dataset"] == "daily"
                  and r["class"] == RETRY
                  and r["market"] not in ("India", "Taiwan")})
    for m in day:
        if m not in seen:
            out.append(f"py scripts\\apac_event_days.py yf {m}")
            seen.add(m)
    if any(r["dataset"] == "daily" and r["market"] == "India"
           and r["class"] == RETRY for r in rows):
        out.append("py scripts\\apac_event_days.py in")
    if not out:
        out.append(":: nothing left that a re-run can recover")
    return out


def freeze():
    """After the final run: the exclusion list, with reasons."""
    rows = five_minute() + daily()
    final = ROOT / "data" / "data_gaps_final.json"
    import datetime as dt
    payload = {
        "frozen": dt.date.today().isoformat(),
        "note": "Datapoints excluded from the analysis. A row "
                "here is a STATED limitation, not an oversight "
                "— quote it wherever the market is used.",
        "excluded": rows}
    final.write_text(json.dumps(payload, indent=1),
                     encoding="utf-8")
    c = Counter(r["class"] for r in rows)
    print(f"frozen {len(rows)} excluded datapoints: {dict(c)}")
    if c[RETRY]:
        print(f"  ! {c[RETRY]} are still marked RETRY — they "
              f"were never given their last attempt. Run the "
              f"plan first, or they are being abandoned "
              f"untested.")
    print(f"-> {final.relative_to(ROOT)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "plan":
        for ln in plan_lines():
            print(ln)
    elif cmd == "freeze":
        freeze()
    else:
        report()
