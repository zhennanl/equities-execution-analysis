"""Per-event rows for the interactive APAC panel (c-275).

    py scripts\\apac_panel_events.py

WHY A SECOND FILE RATHER THAN AN EDIT.

`index_strategist_qa.py` publishes pre-aggregated cells and the
page that reads it is forbidden from doing arithmetic — there
is a test enforcing that, and the reason is good: a view that
computes will eventually disagree with the document generated
from the same numbers.

The interactive panel cannot live under that rule. Bill wants a
market picker, a date range and a user-defined percentile on
every chart, and no amount of precomputation covers "the 37th
percentile of Korean deletions between Feb-2019 and Aug-2023".
That is a cross-product with a free parameter in it.

So the contract changes rather than bends:

  * the OLD page keeps its rule, its generator and its test,
    untouched;
  * the NEW page reads THIS file, which publishes one row per
    name-event and no aggregates at all, and does its own
    filtering and quantiles.

Nothing here recomputes a metric. `metrics()` is imported from
the original generator, so both pages measure the same thing
the same way and a fix to one is a fix to both.

Output: data/apac_panel_events.json
"""
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "data" / "apac_panel_events.json"

# The fields the page actually plots. Everything else that
# `metrics()` produces is dropped here rather than shipped —
# the file is read on every page load, so an unused column is a
# cost paid by the reader.
KEEP = ("market", "action", "rev", "code", "ann", "eff",
        "gap1", "drift", "eff_day", "rev5", "rev20",
        "pre_drift", "total", "t_mult", "vol_win",
        "cost_linear", "cost_day1", "cost_late5", "cost_3070",
        "fav_early3", "fav_late", "delisted_safe")

_MON = {"Feb": 2, "May": 5, "Aug": 8, "Nov": 11}

# c-280: the CUMULATIVE PATH, in event time.
#
# The page's first chart is the announcement-to-effective
# return path for every event, benchmarked at day 0. That needs
# the daily series, which the scalar metrics do not carry — so
# each row gains a fixed-length array of cumulative % returns
# indexed from PATH_LO to PATH_HI sessions off the announcement
# close, and the offset at which its effective date falls.
#
# Day 0 is the ANNOUNCEMENT CLOSE and is the baseline, worth
# nothing by construction. MSCI publishes from Geneva before
# the Asian open, so that close is the last pre-news price;
# anchoring on the following session would fold the jump into
# the baseline and flatten the very move the chart is for.
#
# The range is measured, not guessed: across the panel the
# announcement-to-effective gap runs 5 to 17 sessions and the
# longest window reaches 40 sessions past the announcement.
PATH_LO, PATH_HI = -20, 40
PATH_OFFSETS = list(range(PATH_LO, PATH_HI + 1))


def rev_ord(rev):
    """'Aug26' -> 202608, so a review sorts and range-filters as
    a number. Reviews are the panel's natural time axis — every
    event in one review shares its dates — so the date control
    on the page moves in reviews, not in days."""
    r = str(rev)
    if len(r) < 5 or r[:3] not in _MON:
        return None
    try:
        return 2000 + int(r[3:5]), _MON[r[:3]]
    except ValueError:
        return None


# c-284: UNADJUSTED CORPORATE ACTIONS.
#
# Bill asked whether Aug25|6919 was an outlier or bad data. It
# is bad data, and not alone. Caliway closed at 1,215 on
# 2025-07-11, was suspended, and reopened at 133.50 on
# 2025-07-21 — a 10-for-1 split. TWSE day files and NSE
# bhavcopy both publish UNADJUSTED prices, so the split reads
# as a -89% session and the event's path opens at +923%.
#
# Taiwan has a 10% daily price limit, so any session outside
# roughly +/-11% there is arithmetically impossible without a
# capital change. Other markets have wider limits, so the
# threshold is set well beyond any of them: a session that
# nearly doubles or more than halves is a corporate action, not
# a price.
#
# Eleven events in 2,175 trip it — India 7, China 3, Taiwan 1 —
# and they are flagged rather than silently repaired. Repairing
# would mean inventing an adjustment factor from the ratio
# itself, which is circular: the ratio is contaminated by
# whatever the price did during the suspension.
BREAK_HI, BREAK_LO = 1.8, 0.55


def price_break(v):
    """(True, detail) if the window contains a session that no
    price limit allows. Detail names the two dates so the call
    can be checked against the exchange rather than trusted."""
    px = [r for r in sorted(v["px"], key=lambda r: r["d"])
          if r.get("c")]
    for a, b in zip(px, px[1:]):
        if not (a["c"] and b["c"]):
            continue
        r = b["c"] / a["c"]
        if r >= BREAK_HI or r <= BREAK_LO:
            return True, (f"{a['d']} {a['c']:g} -> {b['d']} "
                          f"{b['c']:g} (x{r:.3f})")
    return False, None


def path_of(v):
    """(price path, volume path, effective offset).

    Both paths are None at any offset the window does not
    reach, so a short window contributes to the offsets it has
    and nothing else — the alternative, padding with the last
    known value, invents a flat stretch that never traded.

    c-281 adds the VOLUME path: each session's volume as a
    multiple of the same ADV every other number on the page
    uses. It answers a question the price path cannot — after
    the index has repriced, does liquidity stay up or snap
    back? That decides whether a residual can be worked out
    over a week or has to go into the close.
    """
    px = [r for r in sorted(v["px"], key=lambda r: r["d"])
          if r.get("c")]
    if len(px) < 12:
        return None, None, None
    dts = [r["d"] for r in px]
    ann, eff = str(v["ann"])[:10], str(v["eff"])[:10]
    ia = [i for i, d in enumerate(dts) if d <= ann]
    ie = [i for i, d in enumerate(dts) if d <= eff]
    if not (ia and ie):
        return None, None, None
    i0, base = ia[-1], px[ia[-1]]["c"]
    if not base or base <= 0:
        return None, None, None
    # the SAME ADV definition as metrics(): median volume over
    # the 20 sessions ending the day before the announcement.
    # Recomputed here rather than imported so the two cannot
    # silently diverge on a future edit — and asserted equal in
    # the tests.
    pre = [r.get("v") or 0 for r in px[max(0, i0 - 20):i0]]
    pre = [q for q in pre if q]
    adv = statistics.median(pre) if pre else 0
    out, vout = [], []
    for k in PATH_OFFSETS:
        j = i0 + k
        ok = 0 <= j < len(px)
        out.append(round(100 * (px[j]["c"] / base - 1), 3)
                   if ok else None)
        q = (px[j].get("v") or 0) if ok else 0
        vout.append(round(q / adv, 3) if (ok and adv and q)
                    else None)
    return out, vout, ie[-1] - i0


def main():
    import index_strategist_qa as Q
    windows = Q._load()
    rows = [m for m in (Q.metrics(v) for v in windows) if m]
    # key the paths by the same identity `metrics` produces, so
    # a row and its path cannot be mismatched by ordering
    paths, breaks = {}, {}
    for v in windows:
        k = (v["market"], str(v.get("rev")), str(v.get("code")))
        brk, detail = price_break(v)
        breaks[k] = (brk, detail)
        pa, vp, eo = path_of(v)
        if pa is not None:
            paths[k] = (pa, vp, eo)

    out, skipped = [], 0
    for m in rows:
        o = rev_ord(m.get("rev"))
        if o is None:
            skipped += 1
            continue
        r = {k: m.get(k) for k in KEEP}
        r["y"], r["m"] = o
        r["ord"] = o[0] * 100 + o[1]
        k = (m["market"], str(m.get("rev")), str(m.get("code")))
        pa = paths.get(k)
        (r["path"], r["vpath"],
         r["eff_off"]) = pa if pa else (None, None, None)
        r["price_break"], r["break_detail"] = breaks.get(
            k, (False, None))
        out.append(r)
    out.sort(key=lambda r: (r["ord"], r["market"], r["action"]))

    revs = sorted({r["ord"] for r in out})
    payload = {
        "_what": "one row per name-event. NO aggregates — the "
                 "page computes its own, because the percentile "
                 "is a user input.",
        "_source": "scripts/apac_panel_events.py, metrics() "
                   "imported from index_strategist_qa.py",
        "n_events": len(out),
        "markets": sorted({r["market"] for r in out}),
        "reviews": revs,
        "review_labels": {
            str(o): f"{[k for k, v in _MON.items() if v == o % 100][0]}"
                    f"-{o // 100}" for o in revs},
        "delisted_safe": sorted(Q.DELISTED_SAFE),
        "path_offsets": PATH_OFFSETS,
        "n_with_path": sum(1 for r in out if r.get("path")),
        "n_with_vpath": sum(1 for r in out if r.get("vpath")),
        "n_price_break": sum(1 for r in out if r["price_break"]),
        "price_breaks": [
            {"market": r["market"], "rev": r["rev"],
             "code": r["code"], "detail": r["break_detail"]}
            for r in out if r["price_break"]],
        "events": out,
    }
    OUT.write_text(json.dumps(payload, separators=(",", ":")),
                   encoding="utf-8")
    mb = OUT.stat().st_size / 1e6
    print(f"  {len(out):,} events, {len(payload['markets'])} "
          f"markets, {len(revs)} reviews")
    if skipped:
        print(f"  {skipped} dropped for an unparseable review tag")
    print(f"  {payload['review_labels'][str(revs[0])]} .. "
          f"{payload['review_labels'][str(revs[-1])]}")
    print(f"-> {OUT.relative_to(ROOT)}  ({mb:.1f} MB)")


if __name__ == "__main__":
    main()
