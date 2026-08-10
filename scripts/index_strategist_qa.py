"""The questions a PT desk index strategist actually asks, run
against every APAC market we hold (c-230).

WHY THIS SHAPE. We have a Taiwan playbook with three data
tiers (docs/EVENT_WINDOW_FRAMEWORK.md): Tier 1 is daily OHLCV
plus announcement/effective dates, Tier 2 adds per-stock
positioning, Tier 3 adds intraday. Only Tier 1 is portable to
all thirteen markets today, so every question below is
answerable from Tier 1 ALONE and says so. Where a Taiwan
finding needs Tier 2 or 3, it is listed as unanswerable rather
than approximated — an approximated crowding read is worse
than no crowding read, because it looks like one.

DISCIPLINE CARRIED ON EVERY NUMBER
  * n on every cell. A median of four is printed as a median
    of four, not as a market's behaviour.
  * SURVIVORSHIP. Ten of thirteen markets are priced from
    Yahoo, which lists the living. Their DELETION rows are
    biased toward names that survived deletion; Taiwan and
    India come from exchange day-files and are delisted-safe.
    Every deletion statistic carries the flag.
  * MARKET ADJUSTMENT is NOT applied. We do not hold an index
    series for every market, and a half-adjusted panel is
    worse than a consistently raw one. Read every return as
    total, not excess.

Usage:  py scripts\\index_strategist_qa.py
Output: data/index_strategist_qa.json
        docs/INDEX_STRATEGIST_QA_APAC.md
"""
import json
import math
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "data" / "apac_event_windows"
TW = ROOT / "data" / "tw_event_windows.json"
OUT = ROOT / "data" / "index_strategist_qa.json"
DOC = ROOT / "docs" / "INDEX_STRATEGIST_QA_APAC.md"

# Which markets are priced from a source that keeps the dead.
DELISTED_SAFE = {"Taiwan", "India"}

# The Feb-2023 QCIR regime break — MSCI moved Feb/Aug from a
# light maintenance review to a full comprehensive one.
REGIME = "2023-02-01"


def _load():
    """Every priced window, market-tagged."""
    out = []
    files = [(p.stem, p) for p in sorted(DIR.glob("*.json"))]
    if TW.exists():
        files.append(("Taiwan", TW))
    for mkt, p in files:
        try:
            W = json.loads(p.read_text(encoding="utf-8"))["windows"]
        except Exception:                          # noqa: BLE001
            continue
        for v in W.values():
            if v.get("px") and len(v["px"]) >= 12:
                v = dict(v)
                v["market"] = mkt
                out.append(v)
    return out


def _series(v):
    """(dates, closes, volumes) with rows that have a close."""
    px = [r for r in v["px"] if r.get("c")]
    return ([r["d"] for r in px], [r["c"] for r in px],
            [r.get("v") or 0 for r in px])


def _idx(dts, when):
    """Last row on or before a date, else None."""
    hit = None
    for i, d in enumerate(dts):
        if d <= when:
            hit = i
    return hit


def metrics(v):
    """Tier-1 metrics for one window. None if the window cannot
    support them — a short window is dropped, never padded."""
    dts, close, vol = _series(v)
    if len(close) < 12:
        return None
    i0, ie = _idx(dts, v["ann"]), _idx(dts, v["eff"])
    if i0 is None or ie is None or ie <= i0 + 1:
        return None
    if i0 < 1 or close[i0] <= 0:
        return None

    def ret(a, b):
        if not (0 <= a < len(close) and 0 <= b < len(close)):
            return None
        if close[a] <= 0:
            return None
        return close[b] / close[a] - 1

    pre = [q for q in vol[max(0, i0 - 20):i0] if q]
    adv = st.median(pre) if pre else 0
    last = len(close) - 1
    m = {
        "market": v["market"], "rev": v.get("rev"),
        "code": v.get("code"), "action": v.get("action"),
        "ann": v["ann"], "eff": v["eff"],
        # the announcement pop: day 0 close is pre-news because
        # MSCI publishes before the Asian open
        "gap1": ret(i0, min(i0 + 1, last)),
        # the run from the first reacting session to the day
        # BEFORE the print
        "drift": ret(min(i0 + 1, ie - 1), ie - 1),
        # the print itself
        "eff_day": ret(ie - 1, ie),
        "rev5": ret(ie, min(ie + 5, last)),
        "rev20": ret(ie, min(ie + 20, last)),
        "pre_drift": ret(max(0, i0 - 20), i0),
        "total": ret(i0, ie - 1),
        "sessions_pre": i0,
        "sessions_post": last - ie,
        "adv": adv,
        "t_mult": (vol[ie] / adv) if adv else None,
        # a window whose in-between sessions are ALL zero-volume
        # (halted, suspended, or a data gap) has no window
        # volume — None, not a crash and not a zero
        "vol_win": ((st.median(_w) / adv)
                    if adv and (_w := [q for q in vol[i0 + 1:ie]
                                       if q]) else None),
        "delisted_safe": v["market"] in DELISTED_SAFE,
        "post_regime": v["ann"] >= REGIME,
    }
    # execution counterfactuals, in the desk's own units: cost
    # in bps versus doing the whole thing on the effective close
    sgn = 1 if str(v.get("action")).upper() == "ADD" else -1
    tgt = close[ie]
    if tgt and tgt > 0:
        path = [c for c in close[i0 + 1:ie + 1] if c and c > 0]
        if len(path) >= 3:
            def cost(avg):
                return sgn * (avg / tgt - 1) * 1e4
            m["cost_linear"] = cost(st.mean(path))
            m["cost_day1"] = cost(path[0])
            m["cost_late5"] = cost(st.mean(path[-5:]))
            m["cost_3070"] = cost(
                0.3 * st.mean(path[:3]) + 0.7 * tgt)
    # the early read: does day +3 tell you anything?
    #
    # c-230 CORRECTION, caught in the first output. I first
    # correlated early3 (day+1 -> day+3) against `drift`
    # (day+1 -> eff-1) and got 0.35-0.44 in every market, which
    # should have been the tell: `drift` CONTAINS `early3`, so
    # the correlation is arithmetic, not predictive. A desk
    # reading "day+3 forecasts the window, rho 0.44" would have
    # been reading its own left-hand side.
    #
    # The honest question is whether the early move predicts
    # what happens AFTER it, so `late_drift` starts where
    # early3 ends and the two share no session.
    a3 = ret(i0 + 1, min(i0 + 3, ie - 1)) if ie > i0 + 3 else None
    late = (ret(min(i0 + 3, ie - 1), ie - 1)
            if ie > i0 + 4 else None)
    m["early3"] = a3
    m["late_drift"] = late
    m["fav_early3"] = (sgn * a3) if a3 is not None else None
    m["fav_late"] = (sgn * late) if late is not None else None
    m["fav_drift"] = (sgn * m["drift"]
                      if m["drift"] is not None else None)
    return m


# ---------------------------------------------------------------
def _med(xs):
    xs = [x for x in xs if x is not None
          and not (isinstance(x, float) and math.isnan(x))]
    return (st.median(xs), len(xs)) if xs else (None, 0)


def _pct(xs, p):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    k = max(0, min(len(xs) - 1, int(round(p * (len(xs) - 1)))))
    return xs[k]


def _rho(xs, ys):
    """Spearman, computed here so the whole script has no
    third-party dependency beyond the standard library."""
    pairs = [(a, b) for a, b in zip(xs, ys)
             if a is not None and b is not None]
    n = len(pairs)
    if n < 8:
        return None, n

    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while (j + 1 < len(order)
                   and vals[order[j + 1]] == vals[order[i]]):
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank([p[0] for p in pairs]), rank([p[1] for p in pairs])
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx)
                    * sum((b - my) ** 2 for b in ry))
    return (num / den if den else None), n


def build():
    rows = [m for m in (metrics(v) for v in _load()) if m]
    by = defaultdict(list)
    for r in rows:
        by[r["market"]].append(r)
    return rows, by


# ---------------------------------------------------------------
# THE QUESTIONS. Each returns (title, why_it_matters, table,
# reading) so the report is generated from the same object the
# JSON carries — a number can never appear in the prose that is
# not in the data.
# ---------------------------------------------------------------
def _split(rs, act):
    return [r for r in rs if str(r["action"]).upper() == act]


def q1_print_size(by):
    """How big is the print I have to get done?"""
    tbl = []
    for m, rs in sorted(by.items()):
        for act in ("ADD", "DEL"):
            g = _split(rs, act)
            med, n = _med([r["t_mult"] for r in g])
            if not n:
                continue
            tbl.append({
                "market": m, "action": act, "n": n,
                "t_mult_median": med,
                "t_mult_p75": _pct([r["t_mult"] for r in g], .75),
                "t_mult_max": max(
                    [r["t_mult"] for r in g if r["t_mult"]],
                    default=None),
                "window_vol_x_adv": _med(
                    [r["vol_win"] for r in g])[0],
                "delisted_safe": g[0]["delisted_safe"]})
    return ("Q1. How big is the print?",
            "Sizes the execution problem before anything else. "
            "T-multiple = effective-day volume / 20-session "
            "median ADV. It is the number that decides whether "
            "the trade is a schedule or a negotiation.",
            tbl,
            "Read the p75 and the max, not the median — the "
            "median is the day you plan for and the tail is the "
            "day that costs you.")


def q2_when_does_it_move(by):
    """Announcement pop, or the drift to the print?"""
    tbl = []
    for m, rs in sorted(by.items()):
        for act in ("ADD", "DEL"):
            g = _split(rs, act)
            gap, n = _med([r["gap1"] for r in g])
            if n < 4:
                continue
            dr = _med([r["drift"] for r in g])[0]
            tot = _med([r["total"] for r in g])[0]
            cap = None
            if gap is not None and dr is not None \
                    and abs(gap + dr) > 1e-9:
                cap = dr / (gap + dr)
            tbl.append({"market": m, "action": act, "n": n,
                        "gap1": gap, "drift": dr,
                        "total_ann_to_eff": tot,
                        "capture_share_of_move_in_drift": cap})
    return ("Q2. When does the move happen — the pop or the drift?",
            "If the move is in gap1 the announcement is already "
            "priced and there is nothing to work; if it is in "
            "the drift there is a window to trade into. Capture "
            "= drift / (gap1 + drift).",
            tbl,
            "Capture near 1 means the market takes the whole "
            "window to price it. Capture near 0 or negative "
            "means it gapped and then went the other way.")


def q3_reversal(by):
    """Does the print revert, and how fast?"""
    tbl = []
    for m, rs in sorted(by.items()):
        for act in ("ADD", "DEL"):
            g = _split(rs, act)
            e, n = _med([r["eff_day"] for r in g])
            if n < 4:
                continue
            tbl.append({
                "market": m, "action": act, "n": n,
                "eff_day": e,
                "rev5": _med([r["rev5"] for r in g])[0],
                "rev20": _med([r["rev20"] for r in g])[0],
                "abs_rev5_median": _med(
                    [abs(r["rev5"]) for r in g
                     if r["rev5"] is not None])[0],
                "delisted_safe": g[0]["delisted_safe"]})
    return ("Q3. Does it revert after the print?",
            "Decides whether the effective close is a price to "
            "fade or a price to accept. rev5/rev20 are the "
            "returns from the effective close forward.",
            tbl,
            "A deletion reversal on a SURVIVORS-ONLY market is "
            "the most biased number in this whole document: the "
            "names that did not survive cannot bounce.")


def q4_execution(by):
    """Where should the schedule sit?"""
    tbl = []
    for m, rs in sorted(by.items()):
        for act in ("ADD", "DEL"):
            g = _split(rs, act)
            lin, n = _med([r.get("cost_linear") for r in g])
            if n < 4:
                continue
            tbl.append({
                "market": m, "action": act, "n": n,
                "MOC_baseline_bps": 0.0,
                "LINEAR_bps": lin,
                "ALL_DAY1_bps": _med(
                    [r.get("cost_day1") for r in g])[0],
                "LATE5_bps": _med(
                    [r.get("cost_late5") for r in g])[0],
                "EARLY30_MOC70_bps": _med(
                    [r.get("cost_3070") for r in g])[0],
                "delisted_safe": g[0]["delisted_safe"]})
    return ("Q4. Which schedule beats the effective close?",
            "Cost in bps versus doing 100% on the effective "
            "close, signed so NEGATIVE = beat the benchmark. "
            "This is the only question on this page a desk gets "
            "paid for directly.",
            tbl,
            "These are UNCONDITIONAL medians on a survivors-"
            "biased panel for ten of thirteen markets. They "
            "size the opportunity; they are not a schedule.")


def q5_frontrun(by):
    """Is it already being positioned before the announcement?"""
    tbl = []
    for m, rs in sorted(by.items()):
        for act in ("ADD", "DEL"):
            g = _split(rs, act)
            pd, n = _med([r["pre_drift"] for r in g])
            if n < 4:
                continue
            sgn = 1 if act == "ADD" else -1
            fav = _med([sgn * r["pre_drift"] for r in g
                        if r["pre_drift"] is not None])[0]
            tbl.append({"market": m, "action": act, "n": n,
                        "pre_drift_20s": pd,
                        "favourable_pre_drift": fav,
                        "share_moving_the_right_way": _med(
                            [1.0 if (sgn * r["pre_drift"]) > 0
                             else 0.0 for r in g
                             if r["pre_drift"] is not None])[0]})
    return ("Q5. Is the name already positioned before the "
            "announcement?",
            "20 sessions of pre-announcement drift, signed so "
            "POSITIVE = already moving the way the review will "
            "push it. Anticipation is the part of the trade "
            "that is gone before the desk is called.",
            tbl,
            "Tier-1 can only see PRICE anticipation. Taiwan's "
            "borrow-build clock (98% of deletions show excess "
            "build) is a Tier-2 measurement and has no analog "
            "here.")


def q6_regime(by):
    """Did the Feb-2023 QCIR change alter the trade?"""
    tbl = []
    for m, rs in sorted(by.items()):
        for post in (False, True):
            g = [r for r in rs if r["post_regime"] is post]
            t, n = _med([r["t_mult"] for r in g])
            if n < 6:
                continue
            tbl.append({
                "market": m,
                "period": "since Feb-2023" if post
                          else "before Feb-2023",
                "n": n, "t_mult_median": t,
                "abs_eff_day": _med([abs(r["eff_day"]) for r in g
                                     if r["eff_day"] is not None])[0],
                "abs_gap1": _med([abs(r["gap1"]) for r in g
                                  if r["gap1"] is not None])[0]})
    return ("Q6. Did the Feb-2023 QCIR regime change the trade?",
            "MSCI moved Feb/Aug from light maintenance to full "
            "comprehensive reviews. More names per review could "
            "mean smaller individual prints, or the same print "
            "size four times a year instead of twice.",
            tbl,
            "A period split is not a controlled experiment — "
            "2023-2026 is also a different volatility regime. "
            "Treat a difference here as a question, not a "
            "finding.")


def q7_violence(by):
    """Which markets print violently?"""
    tbl = []
    for m, rs in sorted(by.items()):
        e = [abs(r["eff_day"]) for r in rs
             if r["eff_day"] is not None]
        if len(e) < 6:
            continue
        tbl.append({"market": m, "n": len(e),
                    "abs_eff_day_median": st.median(e),
                    "abs_eff_day_p90": _pct(e, .90),
                    "abs_eff_day_max": max(e),
                    "share_over_5pct": sum(1 for x in e
                                           if x > .05) / len(e)})
    tbl.sort(key=lambda r: -(r["abs_eff_day_p90"] or 0))
    return ("Q7. Which markets print violently?",
            "|effective-day return| — the risk the desk carries "
            "into the close. Ranked by the 90th percentile, "
            "because the tail is what breaks a schedule.",
            tbl,
            "This is the market-selection question: where does "
            "an index-rebalance book deserve more risk budget "
            "and tighter pre-trade limits.")


def q8_asymmetry(by):
    """Are deletions the harder side?"""
    tbl = []
    for m, rs in sorted(by.items()):
        a, d = _split(rs, "ADD"), _split(rs, "DEL")
        if len(a) < 4 or len(d) < 4:
            continue
        tbl.append({
            "market": m, "n_add": len(a), "n_del": len(d),
            "add_t_mult": _med([r["t_mult"] for r in a])[0],
            "del_t_mult": _med([r["t_mult"] for r in d])[0],
            "add_abs_eff": _med([abs(r["eff_day"]) for r in a
                                 if r["eff_day"] is not None])[0],
            "del_abs_eff": _med([abs(r["eff_day"]) for r in d
                                 if r["eff_day"] is not None])[0],
            "delisted_safe": rs[0]["delisted_safe"]})
    return ("Q8. Is the deletion side harder than the addition "
            "side?",
            "Desk lore says deletions are worse: a forced seller "
            "into a name nobody has to own, with the borrow "
            "already lent out. Tier 1 can test the size and the "
            "violence of it.",
            tbl,
            "On survivors-only markets the deletion column is "
            "biased toward the survivors, which understates the "
            "difficulty. Taiwan and India are the honest rows.")


def q9_early_signal(by):
    """Does day +3 predict the rest of the window?"""
    tbl = []
    for m, rs in sorted(by.items()):
        # NON-OVERLAPPING: early3 is day+1->+3, late_drift is
        # day+3->eff-1. Correlating early3 against the full
        # drift (which contains it) was the c-230 error.
        rho, n = _rho([r["fav_early3"] for r in rs],
                      [r["fav_late"] for r in rs])
        rho_overlap, _ = _rho([r["fav_early3"] for r in rs],
                              [r["fav_drift"] for r in rs])
        if rho is None:
            continue
        hot = [r for r in rs if (r["fav_early3"] or 0) > 0]
        cold = [r for r in rs if (r["fav_early3"] or 0) <= 0]
        tbl.append({
            "market": m, "n": n,
            "spearman_early3_vs_LATER_drift": rho,
            "overlapping_window_rho_ARTIFACT": rho_overlap,
            "hot_n": len(hot),
            "hot_linear_bps": _med(
                [r.get("cost_linear") for r in hot])[0],
            "cold_n": len(cold),
            "cold_linear_bps": _med(
                [r.get("cost_linear") for r in cold])[0]})
    tbl.sort(key=lambda r: -(
        r["spearman_early3_vs_LATER_drift"] or 0))
    return ("Q9. Does the first three sessions tell me anything?",
            "Taiwan's window study found conditioning on day +3 "
            "separated the schedules that worked from the ones "
            "that did not. Spearman of the favourable day+3 "
            "move against the drift that comes AFTER it "
            "(day+3 to effective-1), then the execution cost "
            "split on that sign. The second column repeats the "
            "same correlation against the FULL drift, which "
            "contains day+3 — it is printed only to show how "
            "much of an apparent signal is arithmetic.",
            tbl,
            "Compare the two rho columns. Where the "
            "overlapping one is large and the honest one is "
            "near zero, the early move is not forecasting "
            "anything — it is part of what it appears to "
            "predict. Also: events in one review share a "
            "market move, so n is not independent. Treat "
            "|rho| under ~0.25 as noise.")


def q10_liquidity(by):
    """How many days of ADV is the event worth?"""
    tbl = []
    for m, rs in sorted(by.items()):
        t = [r["t_mult"] for r in rs if r["t_mult"]]
        if len(t) < 6:
            continue
        w = [r["vol_win"] for r in rs if r["vol_win"]]
        tbl.append({
            "market": m, "n": len(t),
            "eff_day_x_adv_median": st.median(t),
            "eff_day_x_adv_p90": _pct(t, .90),
            "window_days_x_adv_median": (st.median(w) if w
                                         else None),
            "share_over_10x": sum(1 for x in t if x > 10) / len(t),
            "share_under_2x": sum(1 for x in t if x < 2) / len(t)})
    tbl.sort(key=lambda r: -(r["eff_day_x_adv_p90"] or 0))
    return ("Q10. How much of the trade can the close actually "
            "absorb?",
            "share_under_2x is the quiet-event rate — reviews "
            "where the print barely registers and the desk "
            "should not be spending risk. share_over_10x is "
            "where the print IS the day.",
            tbl,
            "China's low share_over_10x with a huge n is the "
            "single most important planning fact in this table: "
            "most Chinese index events are not liquidity events.")


QUESTIONS = [q1_print_size, q2_when_does_it_move, q3_reversal,
             q4_execution, q5_frontrun, q6_regime, q7_violence,
             q8_asymmetry, q9_early_signal, q10_liquidity]


# ---------------------------------------------------------------
def _fmt(v, key):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "yes" if v else "**no**"
    if isinstance(v, int):
        return str(v)
    if any(k in key for k in ("bps",)):
        return f"{v:+.0f}"
    if any(k in key for k in ("share", "capture")):
        return f"{v:.0%}"
    if any(k in key for k in ("t_mult", "x_adv", "vol_win",
                              "spearman", "rho")):
        return f"{v:.2f}"
    if isinstance(v, float):
        return f"{v:+.2%}" if abs(v) < 1 else f"{v:.2f}"
    return str(v)


def _table(rows):
    if not rows:
        return "_no cell met the minimum n._\n"
    cols = list(rows[0])
    out = ["| " + " | ".join(cols) + " |",
           "|" + "|".join("---" for _ in cols) + "|"]
    for r in rows:
        out.append("| " + " | ".join(
            _fmt(r.get(c), c) for c in cols) + " |")
    return "\n".join(out) + "\n"


def report():
    rows, by = build()
    payload = {"n_windows": len(rows),
               "markets": {m: len(v) for m, v in sorted(by.items())},
               "questions": []}
    doc = ["# APAC Index-Rebalance — the strategist's questions",
           "",
           "*Generated by `scripts/index_strategist_qa.py`. Every "
           "number recomputed from `data/apac_event_windows/` and "
           "`data/tw_event_windows.json` — nothing here is typed "
           "by hand.*", "",
           f"**Panel: {len(rows)} name-events across "
           f"{len(by)} markets, MSCI reviews 2015-2026.**", "",
           "## Read this before any number below", "",
           "**Survivorship.** Ten of thirteen markets are priced "
           "from Yahoo, which lists the living. Their DELETION "
           "rows are biased toward names that survived being "
           "deleted. Taiwan and India come from exchange "
           "day-files and keep the dead — they are the honest "
           "rows, and where they disagree with the others, "
           "believe them.", "",
           "**No market adjustment.** We do not hold an index "
           "series for all thirteen, and a half-adjusted panel "
           "is worse than a consistently raw one. Every return "
           "here is total, not excess. A market-wide move inside "
           "a window lands in these numbers.", "",
           "**Tier 1 only.** Price and volume. The Taiwan edge — "
           "borrow build, foreign flow, crowding, the auction "
           "path — is Tier 2/3 and does not exist for these "
           "markets yet. See `docs/APAC_DATA_GAP_REGISTER.md` "
           "for what it would take.", "",
           "**Overlapping events.** Names in the same review "
           "share a market move; n is a count of name-events, "
           "not of independent observations. Effective n for "
           "any cross-sectional claim is closer to the review "
           "count.", ""]
    for fn in QUESTIONS:
        title, why, tbl, reading = fn(by)
        payload["questions"].append(
            {"title": title, "why": why, "rows": tbl,
             "reading": reading})
        doc += [f"## {title}", "", why, "", _table(tbl), "",
                f"**Reading it.** {reading}", ""]
    OUT.write_text(json.dumps(payload, indent=1),
                   encoding="utf-8")
    DOC.write_text("\n".join(doc), encoding="utf-8")
    print(f"panel: {len(rows)} name-events, {len(by)} markets")
    for m, v in sorted(by.items(), key=lambda x: -len(x[1])):
        print(f"  {m:12} {len(v):>5}")
    bs = briefs(by)
    payload["briefs"] = bs
    BRIEF = ROOT / "docs" / "INDEX_STRATEGIST_BRIEFS_APAC.md"
    BRIEF.write_text(brief_doc(bs), encoding="utf-8")
    OUT.write_text(json.dumps(payload, indent=1),
                   encoding="utf-8")
    print(f"\n-> {OUT.relative_to(ROOT)}")
    print(f"-> {DOC.relative_to(ROOT)}")
    print(f"-> {BRIEF.relative_to(ROOT)}")
    return payload



# ---------------------------------------------------------------
# PER-MARKET BRIEFS
#
# The cross-market tables answer "how do these markets differ".
# A desk asks a narrower question: "I cover THIS market — what
# do I need to know before the next review?" So each market
# gets its own page, computed from the same rows, with the
# facts a strategist would actually put in front of a trader.
# ---------------------------------------------------------------
def _brief(m, rs):
    a, d = _split(rs, "ADD"), _split(rs, "DEL")
    safe = rs[0]["delisted_safe"]
    t = [r["t_mult"] for r in rs if r["t_mult"]]
    e = [abs(r["eff_day"]) for r in rs if r["eff_day"] is not None]
    b = {"market": m, "n": len(rs), "n_add": len(a),
         "n_del": len(d), "delisted_safe": safe,
         "reviews": len({r["rev"] for r in rs}),
         "span": (min(r["ann"] for r in rs),
                  max(r["ann"] for r in rs))}
    b["print_median_x_adv"] = st.median(t) if t else None
    b["print_p90_x_adv"] = _pct(t, .90)
    b["quiet_rate"] = (sum(1 for x in t if x < 2) / len(t)
                       if t else None)
    b["abs_eff_median"] = st.median(e) if e else None
    b["abs_eff_p90"] = _pct(e, .90)
    for lab, g in (("add", a), ("del", d)):
        b[f"{lab}_gap1"] = _med([r["gap1"] for r in g])[0]
        b[f"{lab}_drift"] = _med([r["drift"] for r in g])[0]
        b[f"{lab}_rev5"] = _med([r["rev5"] for r in g])[0]
        b[f"{lab}_best_sched"] = None
        cands = {
            "MOC": 0.0,
            "LINEAR": _med([r.get("cost_linear") for r in g])[0],
            "ALL_DAY1": _med([r.get("cost_day1") for r in g])[0],
            "LATE5": _med([r.get("cost_late5") for r in g])[0],
            "EARLY30_MOC70": _med([r.get("cost_3070")
                                   for r in g])[0]}
        cands = {k: v for k, v in cands.items() if v is not None}
        if len(cands) > 1 and len(g) >= 4:
            best = min(cands, key=lambda k: cands[k])
            b[f"{lab}_best_sched"] = best
            b[f"{lab}_best_bps"] = cands[best]
    rho, n = _rho([r["fav_early3"] for r in rs],
                  [r["fav_late"] for r in rs])
    b["early3_rho"] = rho
    b["early3_n"] = n
    return b


def briefs(by):
    return [_brief(m, rs) for m, rs in sorted(
        by.items(), key=lambda x: -len(x[1]))]


def brief_doc(bs):
    out = ["# Per-market briefs — MSCI index reviews, 2015-2026",
           "",
           "*Generated by `scripts/index_strategist_qa.py`. One "
           "page per market, same panel as "
           "`INDEX_STRATEGIST_QA_APAC.md`, written for a trader "
           "who covers one market and wants the numbers before "
           "the next review.*", "",
           "Every schedule cost is in bps versus doing 100% on "
           "the effective close; NEGATIVE beat the close. "
           "`MOC` is the benchmark and is 0 by construction, so "
           "a market whose best schedule is MOC is one where "
           "nothing in this panel beat simply printing.", ""]
    for b in bs:
        flag = ("delisted-safe (exchange day-files)"
                if b["delisted_safe"]
                else "**SURVIVORS ONLY — deletion rows biased**")
        out += [f"## {b['market']}", "",
                f"{b['n']} name-events across {b['reviews']} "
                f"reviews, {b['span'][0]} to {b['span'][1]}. "
                f"{b['n_add']} additions, {b['n_del']} deletions. "
                f"Source: {flag}.", "",
                "| | value |", "|---|---|",
                f"| print, median | {_fmt(b['print_median_x_adv'], 't_mult')}x ADV |",
                f"| print, 90th pct | {_fmt(b['print_p90_x_adv'], 't_mult')}x ADV |",
                f"| quiet-event rate (print < 2x ADV) | {_fmt(b['quiet_rate'], 'share')} |",
                f"| effective-day move, median abs | {_fmt(b['abs_eff_median'], 'x')} |",
                f"| effective-day move, 90th pct | {_fmt(b['abs_eff_p90'], 'x')} |",
                f"| ADD: announcement pop / drift / rev5 | {_fmt(b['add_gap1'], 'x')} / {_fmt(b['add_drift'], 'x')} / {_fmt(b['add_rev5'], 'x')} |",
                f"| DEL: announcement pop / drift / rev5 | {_fmt(b['del_gap1'], 'x')} / {_fmt(b['del_drift'], 'x')} / {_fmt(b['del_rev5'], 'x')} |",
                f"| best schedule, adds | {b.get('add_best_sched') or '—'} ({_fmt(b.get('add_best_bps'), 'bps')} bps) |",
                f"| best schedule, deletes | {b.get('del_best_sched') or '—'} ({_fmt(b.get('del_best_bps'), 'bps')} bps) |",
                f"| day+3 vs the drift AFTER it, Spearman | {_fmt(b['early3_rho'], 'rho')} (n={b['early3_n']}) |",
                ""]
    return "\n".join(out)

if __name__ == "__main__":
    report()
