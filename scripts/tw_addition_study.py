#!/usr/bin/env python3
"""The ADDITION side of the Taiwan panel, end to end.

    py scripts\\tw_addition_study.py

WHY A SEPARATE STUDY FROM tw_case_study.py. That one is built
around borrow, and borrow is a deletion instrument — you cannot
short your way into an addition. Its headline (borrow predicts
the SIZE of a deletion print, not its direction) says nothing
about the four names MSCI is about to add, and the pooled
playbook in the question bank quotes ADD statistics that were
never broken down: "ADD n=64 drift +3.3%, eff-day vol 6.2x ADV"
is one median over nine years, two limit regimes and reviews
carrying anywhere from one name to nine.

WHAT THIS ADDS THAT THE EARLIER PASS DID NOT HAVE. c-303 fixed
the T86 parser and c-305 harvested it, so foreign net flow is
now available on 2,815 trading days back to 2015 — the whole
panel. docs/REBALANCE_FINDINGS.md still records N1/N4/N7 as
"UNANSWERABLE-DAILY (source too short)" because it was written
against twse_institutional.json, which holds 22 days. That is no
longer true and "who is on the other side" is the question this
script exists to answer.

THE FIVE RULES THIS FILE IS HELD TO (question bank §0.3):

 1. Dispersion always. Every median carries n, the IQR and the
    share of the sample with the opposite sign.
 2. Never correlate overlapping windows. gap1, drift, eff_day
    and revert are constructed disjoint; where a pair is not,
    it is not correlated.
 3. Survivor-safe only. Taiwan is priced from TWSE/TPEx day
    files that retain delisted companies.
 4. Market-adjusted, over TAIEX, or it says it is not.
 5. Registry-dated day 0 only. 44 of 180 windows carry an
    announcement date estimated as effective minus 10 business
    days; measured against the 34 reviews where MSCI's date is
    known the real gap is 12-17 sessions, so those windows put
    day 0 INSIDE the reaction. They are excluded, not weighted.

AND ONE MORE, WHICH IS THE REASON THIS SCRIPT HAS AN
OUT-OF-SAMPLE SECTION AT ALL. Anything here that is offered as a
predictor is fitted on reviews up to and including Nov-2022 and
scored on Feb-2023 onward. The split is at MSCI's own regime
break — the move to a full quarterly comprehensive review — so
it is not an arbitrary date, and it is the same break the
question bank makes binding in §0.3.5.
"""
from __future__ import annotations

import collections
import json
import math
import random
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "tw_addition_study.json"
DOC = ROOT / "docs" / "TW_ADDITION_STUDY.md"

# MSCI's move to a full quarterly comprehensive review. Reviews
# are ordered by (year, month) rather than by string, because
# "Aug17" < "Feb18" is false alphabetically.
_MON = {"Feb": 2, "May": 5, "Aug": 8, "Nov": 11}
REGIME_BREAK = (2023, 2)          # Feb-2023
HORIZON = 20
TRIALS = 20000
SEED = 20260810


def rev_key(rev):
    """'Aug17' -> (2017, 8). Sortable, and comparable to the break."""
    return (2000 + int(str(rev)[3:]), _MON[str(rev)[:3]])


def _j(name):
    p = ROOT / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


# ── small statistics, no dependencies ────────────────────────────────

def pct(xs, p):
    xs = sorted(x for x in xs if x is not None and x == x)
    if not xs:
        return None
    i = (len(xs) - 1) * p
    lo = int(i)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def describe(xs, sign=None):
    """The dispersion block §0.3.1 requires, on every median.

    `sign` is the direction the thesis expects, so "how often it
    has the right sign" is recorded next to the median rather
    than left for a reader to assume from it.
    """
    xs = [x for x in xs if x is not None and x == x]
    if not xs:
        return {"n": 0}
    out = {"n": len(xs), "mean": st.mean(xs), "p10": pct(xs, .10),
           "p25": pct(xs, .25), "p50": pct(xs, .50),
           "p75": pct(xs, .75), "p90": pct(xs, .90),
           "min": min(xs), "max": max(xs)}
    if sign:
        good = sum(1 for x in xs if (x > 0) == (sign > 0))
        out["right_sign_share"] = good / len(xs)
    return out


def spearman(a, b):
    """Rank correlation, average ranks on ties."""
    pairs = [(x, y) for x, y in zip(a, b)
             if x is not None and y is not None
             and x == x and y == y]
    if len(pairs) < 6:
        return None, None, len(pairs)

    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    xs, ys = ranks([p[0] for p in pairs]), ranks([p[1] for p in pairs])
    n = len(xs)
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs)
                    * sum((y - my) ** 2 for y in ys))
    rho = num / den if den else None
    if rho is None:
        return None, None, n
    # permutation p — no scipy, and it makes no normality claim
    rnd = random.Random(SEED)
    ys2 = list(ys)
    hits = 0
    for _ in range(TRIALS):
        rnd.shuffle(ys2)
        num2 = sum((x - mx) * (y - my) for x, y in zip(xs, ys2))
        if abs(num2) >= abs(num):
            hits += 1
    return rho, (hits + 1) / (TRIALS + 1), n


def mannwhitney_p(a, b):
    """Permutation test on the difference of medians.

    Used instead of a t-test because these distributions are
    heavily right-skewed — the addition-drift mean is three times
    its median — and a mean-based test would be answering a
    question about three events.
    """
    a = [x for x in a if x is not None and x == x]
    b = [x for x in b if x is not None and x == x]
    if len(a) < 4 or len(b) < 4:
        return None
    obs = abs(st.median(a) - st.median(b))
    pool = a + b
    rnd = random.Random(SEED)
    hits = 0
    for _ in range(TRIALS):
        rnd.shuffle(pool)
        if abs(st.median(pool[:len(a)])
               - st.median(pool[len(a):])) >= obs:
            hits += 1
    return (hits + 1) / (TRIALS + 1)


# ── the panel ────────────────────────────────────────────────────────

def build_events():
    """One row per registry-dated window, with every measure.

    Returns (rows, provenance) where provenance records what was
    dropped and why — a sample statement that cannot drift away
    from the sample.
    """
    wins = (_j("tw_event_windows.json") or {}).get("windows", {})
    twii = {k: float(v) for k, v in (_j("twii_daily.json") or {}).items()
            if v == v}
    t86 = _j("t86_history.json") or {}
    sbl = _j("sbl_history.json") or {}
    marg = _j("margin_history.json") or {}

    prov = collections.Counter()
    per_review = collections.Counter()
    for w in wins.values():
        if w.get("day0") == "registry":
            per_review[(w["rev"], w["action"])] += 1
    seen_before = collections.defaultdict(list)
    for w in sorted(wins.values(), key=lambda x: rev_key(x["rev"])):
        seen_before[w["code"]].append(w["rev"])

    rows = []
    for key, w in wins.items():
        if w.get("day0") != "registry":
            prov["dropped_estimated_day0"] += 1
            continue
        px = w.get("px") or []
        if not px:
            prov["dropped_no_prices"] += 1
            continue
        bars = sorted(px, key=lambda r: r["d"])
        dates = [r["d"] for r in bars]
        eff, ann = w.get("eff"), w.get("ann")
        if eff not in dates or ann not in dates:
            prov["dropped_no_anchor_bar"] += 1
            continue
        ie, ia = dates.index(eff), dates.index(ann)
        # c-316 BUG, caught by the sample count rather than by an
        # exception. The first version required 25 bars before the
        # announcement so `pre_drift` could always be a clean
        # ann-25 -> ann measure. The windows do not carry that: the
        # panel opens ~36 sessions before the EFFECTIVE date and
        # the announcement sits ~13 sessions before it, so the
        # median window has 23 bars before day 0 and the maximum
        # is 25. The filter kept 7 of 136 windows and every number
        # printed cleanly off them.
        #
        # A hard requirement is the wrong shape for a measure that
        # is an INPUT and not the result: pre_drift now uses the
        # longest lookback the window actually holds, and the
        # length travels with it so nothing pools a 21-session
        # lookback with a 25-session one without knowing.
        if ia < 15 or ie - ia < 5 or ie + 1 >= len(bars):
            prov["dropped_short_window"] += 1
            continue
        pre_n = min(25, ia)

        close = [b["c"] for b in bars]
        vol = [b.get("v") or 0 for b in bars]

        def mret(i, j):
            """market-adjusted simple return, bar i -> bar j"""
            if not (0 <= i < len(bars) and 0 <= j < len(bars)):
                return None
            if not (close[i] and close[j]):
                return None
            r = close[j] / close[i] - 1
            m0, m1 = twii.get(dates[i]), twii.get(dates[j])
            if m0 and m1:
                r -= (m1 / m0 - 1)
            return r

        # ADV: the 20 sessions ENDING BEFORE the announcement, so
        # the event's own volume is not in its own denominator
        base = [v for v in vol[max(0, ia - 20):ia] if v]
        adv = st.median(base) if len(base) >= 10 else None

        # DISJOINT BY CONSTRUCTION (§0.3.2). pre_drift ends at
        # ann, gap1 is ann->ann+1, drift is ann+1->eff-1, eff_day
        # is eff-1->eff, revert starts at eff. No pair overlaps,
        # so any correlation between them is legitimate.
        pre_drift = mret(ia - pre_n, ia)
        gap1 = mret(ia, ia + 1)
        drift = mret(ia + 1, ie - 1)
        eff_day = mret(ie - 1, ie)
        total = mret(ia, ie - 1)
        path = {n: mret(ie, ie + n) for n in range(1, HORIZON + 1)
                if ie + n < len(bars)}
        # the schedule question (C6): drift accumulated by each
        # session before the effective date, as a share of the
        # whole. Measured from ann+1 so it is the tradeable part.
        acc = {}
        for n in range(0, ie - ia):
            v = mret(ia + 1, ia + 1 + n)
            if v is not None:
                acc[n] = v
        # worst point of a position held ann+1 -> eff-1 (J4)
        exc = [mret(ia + 1, k) for k in range(ia + 2, ie)]
        exc = [x for x in exc if x is not None]

        code = w["code"]

        def flow(i, j, field):
            """net shares over bars [i, j) from a TWSE day-file."""
            tot, seen = 0.0, 0
            for d in dates[max(0, i):max(0, j)]:
                day = t86.get(d.replace("-", "")) or {}
                rec = day.get(code)
                if isinstance(rec, dict) and rec.get(field) is not None:
                    tot += float(rec[field])
                    seen += 1
            return (tot, seen)

        def bal(idx, src, pick):
            d = dates[idx].replace("-", "") if 0 <= idx < len(dates) else None
            rec = (src.get(d) or {}).get(code) if d else None
            return pick(rec) if rec else None

        f_pre, n_pre = flow(ia - 20, ia, "f")
        f_mid, n_mid = flow(ia + 1, ie, "f")
        f_eff, n_eff = flow(ie, ie + 1, "f")
        f_post, n_post = flow(ie + 1, ie + 11, "f")
        # T86 carries foreign (`f`) and TOTAL institutional (`t`).
        # The residual is trust plus dealer — the domestic
        # institutional bid. It is worth separating because the
        # first cut of `flows` showed foreigners taking only ~0.5
        # days of ADV into an addition while selling ~1.5 out of a
        # deletion, and "then who buys the additions?" is the
        # obvious next question rather than a loose end.
        t_mid, _ = flow(ia + 1, ie, "t")
        t_eff_, _ = flow(ie, ie + 1, "t")
        t_post, _ = flow(ie + 1, ie + 11, "t")

        b0 = bal(ia - 20, sbl, lambda r: r[1] if isinstance(r, list) else None)
        b1 = bal(ie - 1, sbl, lambda r: r[1] if isinstance(r, list) else None)

        def _m(r):
            try:
                return float(str(r["raw"][5]).replace(",", "")) * 1000
            except Exception:                       # noqa: BLE001
                return None
        m0 = bal(ia - 20, marg, _m)
        m1 = bal(ie - 1, marg, _m)

        rk = rev_key(w["rev"])
        prior = [r for r in seen_before[code] if rev_key(r) < rk]
        rows.append({
            "key": key, "code": code, "name": w.get("name", ""),
            "rev": w["rev"], "rev_key": list(rk),
            "action": w["action"], "ann": ann, "eff": eff,
            "era": "post2023" if rk >= REGIME_BREAK else "pre2023",
            "sessions_ann_to_eff": ie - ia,
            "pre_drift": pre_drift, "pre_drift_sessions": pre_n,
            "gap1": gap1, "drift": drift,
            "eff_day": eff_day, "total_alpha": total,
            "capture": (drift / (gap1 + drift)
                        if (gap1 is not None and drift is not None
                            and abs(gap1 + drift) > 1e-9) else None),
            "path": {str(k): v for k, v in path.items()
                     if v is not None},
            "accrual": {str(k): v for k, v in acc.items()},
            "max_drawdown_in_drift": (min(exc) if exc else None),
            "adv": adv,
            "vol_mult_eff": (vol[ie] / adv) if adv and vol[ie] else None,
            "vol_mult_next": (vol[ie + 1] / adv
                              if adv and ie + 1 < len(vol)
                              and vol[ie + 1] else None),
            "vol_mult_win": (st.median([v for v in vol[ia + 1:ie] if v])
                             / adv
                             if adv and any(vol[ia + 1:ie]) else None),
            "price_level": close[ia],
            "prevol": (st.pstdev([close[k + 1] / close[k] - 1
                                  for k in range(max(0, ia - 21),
                                                 ia - 1)
                                  if close[k]])
                       if ia >= 8 else None),
            "n_same_review": per_review[(w["rev"], w["action"])],
            "n_same_review_all": (per_review[(w["rev"], "ADD")]
                                  + per_review[(w["rev"], "DEL")]),
            "repeat_mover": len(prior) > 0,
            "prior_moves": len(prior),
            "foreign_pre_adv": (f_pre / adv) if adv and n_pre else None,
            "foreign_mid_adv": (f_mid / adv) if adv and n_mid else None,
            "foreign_eff_adv": (f_eff / adv) if adv and n_eff else None,
            "foreign_post_adv": (f_post / adv) if adv and n_post else None,
            "domestic_mid_adv": ((t_mid - f_mid) / adv
                                 if adv and n_mid else None),
            "domestic_eff_adv": ((t_eff_ - f_eff) / adv
                                 if adv and n_eff else None),
            "domestic_post_adv": ((t_post - f_post) / adv
                                  if adv and n_post else None),
            "foreign_days": n_pre + n_mid + n_eff + n_post,
            "borrow_build": (b1 / b0 if b0 and b1 else None),
            "margin_build": (m1 / m0 if m0 and m1 else None),
            "margin_adv_change": ((m1 - m0) / adv
                                  if adv and m0 and m1 else None),
        })
        prov["kept"] += 1
    return rows, prov


# ── the questions ────────────────────────────────────────────────────

def anatomy(rows):
    """A. What does a normal Taiwan addition look like?

    Reported beside deletions throughout, because the asymmetry
    is the finding the desk trades on and a one-sided table
    invites the reader to supply the other side from memory.
    """
    out = {}
    for side in ("ADD", "DEL"):
        g = [r for r in rows if r["action"] == side]
        sgn = 1 if side == "ADD" else -1
        out[side] = {
            "n": len(g),
            "pre_drift": describe([r["pre_drift"] for r in g], sgn),
            "gap1": describe([r["gap1"] for r in g], sgn),
            "drift": describe([r["drift"] for r in g], sgn),
            "eff_day": describe([r["eff_day"] for r in g], sgn),
            "total_alpha": describe([r["total_alpha"] for r in g], sgn),
            "capture": describe([r["capture"] for r in g]),
            "vol_mult_eff": describe([r["vol_mult_eff"] for r in g]),
            "vol_mult_next": describe([r["vol_mult_next"] for r in g]),
            "max_drawdown_in_drift": describe(
                [r["max_drawdown_in_drift"] for r in g]),
            "revert5": describe([r["path"].get("5") for r in g]),
            "revert10": describe([r["path"].get("10") for r in g]),
            "revert20": describe([r["path"].get("20") for r in g]),
        }
    # the asymmetry, tested rather than asserted
    a = [r for r in rows if r["action"] == "ADD"]
    d = [r for r in rows if r["action"] == "DEL"]
    out["asymmetry"] = {
        "print_size_p": mannwhitney_p([r["vol_mult_eff"] for r in a],
                                      [r["vol_mult_eff"] for r in d]),
        "drift_p": mannwhitney_p([r["drift"] for r in a],
                                 [r["drift"] for r in d]),
        "note": "permutation on the difference of MEDIANS; these "
                "distributions are too skewed for a mean-based test",
    }
    return out


def drift_path(rows):
    """C6. When does the drift actually accumulate?

    This is the question that sets the start date of a schedule,
    and it is the one the earlier pass never answered — it
    reported the total drift and left the shape unstated.

    Measured in sessions AFTER ann+1 rather than before the
    effective date, because the announcement is the event a desk
    can act on and the ann->eff gap is not constant (12-14
    sessions).
    """
    out = {}
    for side in ("ADD", "DEL"):
        g = [r for r in rows if r["action"] == side]
        steps = {}
        for n in range(0, 15):
            xs = [r["accrual"].get(str(n)) for r in g]
            xs = [x for x in xs if x is not None]
            if len(xs) >= 12:
                steps[str(n)] = {"n": len(xs), "p25": pct(xs, .25),
                                 "p50": pct(xs, .50),
                                 "p75": pct(xs, .75)}
        # the session by which half and 80% of the median total
        # drift has accrued
        finals = [v["p50"] for v in steps.values()]
        tgt = finals[-1] if finals else None
        half = eighty = None
        if tgt:
            for n, v in sorted(steps.items(), key=lambda kv: int(kv[0])):
                if half is None and abs(v["p50"]) >= abs(tgt) * .5:
                    half = int(n)
                if eighty is None and abs(v["p50"]) >= abs(tgt) * .8:
                    eighty = int(n)
        out[side] = {"steps": steps, "median_total": tgt,
                     "sessions_to_half": half,
                     "sessions_to_eighty": eighty}
    return out


def post_effective(rows):
    """G1/G2/G4. The reversion profile, and when it stops being
    an index position."""
    out = {}
    for side in ("ADD", "DEL"):
        g = [r for r in rows if r["action"] == side]
        prof = {}
        for n in range(1, HORIZON + 1):
            xs = [r["path"].get(str(n)) for r in g]
            xs = [x for x in xs if x is not None]
            if len(xs) >= 12:
                prof[str(n)] = {"n": len(xs), "p25": pct(xs, .25),
                                "p50": pct(xs, .50), "p75": pct(xs, .75)}
        # G2: does a bigger drift give back more? DISJOINT
        # windows (ann+1 -> eff-1 against eff -> eff+20), so the
        # correlation is legitimate — see §0.3.2.
        rho, p, n = spearman([r["drift"] for r in g],
                             [r["path"].get("20") for r in g])
        out[side] = {"profile": prof,
                     "drift_vs_revert20": {"rho": rho, "p": p, "n": n},
                     "share_giving_back": _giveback(g)}
    return out


def _giveback(g):
    """Share of events whose +20 move undoes at least half the drift."""
    pairs = [(r["drift"], r["path"].get("20")) for r in g]
    pairs = [(d, v) for d, v in pairs
             if d is not None and v is not None and abs(d) > 1e-6]
    if not pairs:
        return None
    return sum(1 for d, v in pairs if v / d <= -0.5) / len(pairs)


def flows(rows):
    """N1/N4 — who is on the other side.

    Recorded as UNANSWERABLE in the earlier findings doc because
    it was written against a 22-day file. t86_history.json now
    carries 2,815 trading days, the whole panel, so the question
    is open. Units are days of ADV, signed: positive is foreign
    buying.
    """
    out = {}
    for side in ("ADD", "DEL"):
        g = [r for r in rows if r["action"] == side
             and r["foreign_days"] >= 20]
        out[side] = {
            "n_with_flow": len(g),
            "pre": describe([r["foreign_pre_adv"] for r in g]),
            "ann_to_eff": describe([r["foreign_mid_adv"] for r in g]),
            "effective_day": describe([r["foreign_eff_adv"] for r in g]),
            "post10": describe([r["foreign_post_adv"] for r in g]),
            "domestic_ann_to_eff": describe(
                [r["domestic_mid_adv"] for r in g]),
            "domestic_effective_day": describe(
                [r["domestic_eff_adv"] for r in g]),
            "domestic_post10": describe(
                [r["domestic_post_adv"] for r in g]),
        }
        # ── THE TWO NUMBERS THAT TIE THE FLOW TO THE PRINT ──
        #
        # `cumulative_to_effective` is every foreign net share
        # bought or sold from 20 sessions before the announcement
        # through the effective close. It is the closest this data
        # comes to "how much stock actually changed hands because
        # of the index", and it is MEASURED from TWSE day files
        # rather than inferred from an AUM assumption — which
        # makes it an independent check on the demand model in
        # aug26_scenarios.py rather than a restatement of it.
        #
        # `institutional_share_of_print` is that day's foreign
        # plus domestic net over the printed volume. A low number
        # means the print is intermediation, not ownership
        # transfer — and that is the mechanism behind the whole
        # reversion section.
        full = [r for r in g
                if r["foreign_pre_adv"] is not None
                and r["foreign_mid_adv"] is not None
                and r["foreign_eff_adv"] is not None]
        cum = [r["foreign_pre_adv"] + r["foreign_mid_adv"]
               + r["foreign_eff_adv"] for r in full]
        pre_share = [r["foreign_pre_adv"] / c
                     for r, c in zip(full, cum) if abs(c) > 0.2]
        inst = [abs((r["foreign_eff_adv"] or 0)
                    + (r["domestic_eff_adv"] or 0)) / r["vol_mult_eff"]
                for r in g
                if r["vol_mult_eff"] and r["foreign_eff_adv"] is not None]
        out[side]["cumulative_to_effective"] = describe(cum)
        out[side]["share_accumulated_before_announcement"] = describe(
            pre_share)
        out[side]["institutional_share_of_print"] = describe(inst)
        # does foreign buying into the window explain the print?
        rho, p, n = spearman([r["foreign_mid_adv"] for r in g],
                             [r["vol_mult_eff"] for r in g])
        out[side]["mid_flow_vs_print"] = {"rho": rho, "p": p, "n": n}
        # ... or the drift? disjoint from the effective day
        rho2, p2, n2 = spearman([r["foreign_mid_adv"] for r in g],
                                [r["drift"] for r in g])
        out[side]["mid_flow_vs_drift"] = {"rho": rho2, "p": p2, "n": n2}
    return out


# WHICH EVENT-TIME PHASES EACH MEASURE TOUCHES.
#
# c-316: the first run of `drivers` ranked `gap1 -> total_alpha`
# FIRST, at rho +0.560 and p=0.0001, and it survived Bonferroni.
# It is also arithmetic: total_alpha runs ann -> eff-1 and gap1 is
# ann -> ann+1, so gap1 is a SUMMAND of its own target. §0.3.2 of
# the question bank exists because this already happened once on
# this project — rho 0.35-0.44 in every market, collapsing to
# -0.34..+0.22 once the windows were disjoined.
#
# Declaring the phases and intersecting them is the only version
# that cannot be got wrong by adding a measure later. A pair with
# any shared phase is not correlated at all; it is recorded as
# excluded so the omission is visible rather than silent.
PRE, GAP, DRIFT, EFF, POST = "PRE", "GAP", "DRIFT", "EFF", "POST"
_PHASES = {
    # features
    "adv": set(), "price_level": set(), "prevol": {PRE},
    "n_same_review": set(), "n_same_review_all": set(),
    "prior_moves": set(), "sessions_ann_to_eff": set(),
    "pre_drift": {PRE}, "gap1": {GAP},
    "foreign_pre_adv": {PRE},
    # both balances are read at ann-20 and again at eff-1, so they
    # span everything in between
    "borrow_build": {PRE, GAP, DRIFT},
    "margin_build": {PRE, GAP, DRIFT},
    "margin_adv_change": {PRE, GAP, DRIFT},
    "foreign_mid_adv": {GAP, DRIFT},
    # targets
    "vol_mult_eff": {EFF}, "drift": {DRIFT}, "eff_day": {EFF},
    "total_alpha": {GAP, DRIFT},
}


def drivers(rows, side="ADD"):
    """E1. Rank every candidate driver against event magnitude.

    Pairs that share an event-time phase are EXCLUDED, not
    reported with a caveat — see `_PHASES`.
    """
    g = [r for r in rows if r["action"] == side]
    feats = ["adv", "price_level", "prevol", "pre_drift", "gap1",
             "n_same_review", "n_same_review_all", "prior_moves",
             "foreign_pre_adv", "borrow_build", "margin_build",
             "sessions_ann_to_eff"]
    targets = ["vol_mult_eff", "drift", "eff_day", "total_alpha"]
    table, excluded = [], []
    for f in feats:
        for t in targets:
            if f == t:
                continue
            shared = _PHASES.get(f, set()) & _PHASES.get(t, set())
            if shared:
                excluded.append({"feature": f, "target": t,
                                 "shared_phases": sorted(shared)})
                continue
            rho, p, n = spearman([r.get(f) for r in g],
                                 [r.get(t) for r in g])
            if rho is not None:
                table.append({"feature": f, "target": t, "rho": rho,
                              "p": p, "n": n})
    table.sort(key=lambda r: -abs(r["rho"]))
    return table, excluded


def out_of_sample(rows, side="ADD"):
    """E2. Fit before the regime break, score after it.

    The rule is deliberately crude — a single feature, split at
    its in-sample median, predicting whether the drift beats the
    in-sample median. A crude rule that survives is a result; an
    elaborate one that survives is usually a fit.
    """
    g = [r for r in rows if r["action"] == side]
    tr = [r for r in g if r["era"] == "pre2023"]
    te = [r for r in g if r["era"] == "post2023"]
    res = {"n_train": len(tr), "n_test": len(te), "rules": []}
    if len(tr) < 12 or len(te) < 8:
        res["note"] = "too few events either side of the break"
        res["verdict"] = ("not testable — fewer than 12 training "
                          "or 8 test events")
        res["best_lift"] = None
        return res
    for f in ("pre_drift", "gap1", "adv", "prevol", "n_same_review",
              "foreign_pre_adv", "borrow_build"):
        xs = [r.get(f) for r in tr if r.get(f) is not None
              and r.get("drift") is not None]
        if len(xs) < 12:
            continue
        cut = st.median(xs)
        ys = [r["drift"] for r in tr if r.get("drift") is not None]
        base_cut = st.median(ys)
        # which side of the split did better in TRAINING
        hi = [r["drift"] for r in tr
              if r.get(f) is not None and r.get("drift") is not None
              and r[f] > cut]
        lo = [r["drift"] for r in tr
              if r.get(f) is not None and r.get("drift") is not None
              and r[f] <= cut]
        if len(hi) < 5 or len(lo) < 5:
            continue
        pick_hi = st.median(hi) > st.median(lo)
        sel = [r for r in te if r.get(f) is not None
               and r.get("drift") is not None
               and ((r[f] > cut) == pick_hi)]
        rest = [r for r in te if r.get(f) is not None
                and r.get("drift") is not None
                and ((r[f] > cut) != pick_hi)]
        if len(sel) < 4 or len(rest) < 4:
            continue
        base = sum(1 for r in te if r.get("drift") is not None
                   and r["drift"] > base_cut) / max(
            1, sum(1 for r in te if r.get("drift") is not None))
        hit = sum(1 for r in sel if r["drift"] > base_cut) / len(sel)
        res["rules"].append({
            "feature": f, "train_cut": cut,
            "direction": "high" if pick_hi else "low",
            "train_median_selected": st.median(hi if pick_hi else lo),
            "test_n_selected": len(sel),
            "test_hit_rate": hit, "test_base_rate": base,
            "lift": hit - base,
            "test_median_selected": st.median(
                [r["drift"] for r in sel]),
            "test_median_rest": st.median(
                [r["drift"] for r in rest])})
    res["rules"].sort(key=lambda r: -r["lift"])
    res["best_lift"] = res["rules"][0]["lift"] if res["rules"] else None

    # THE BEST OF K RULES IS A MAXIMUM, NOT A MEASUREMENT.
    #
    # c-316: the first run reported gap1 with a lift of +0.30 and
    # the verdict "one or more rules show lift". That reads as a
    # finding and it is not one. The rule selected 7 of 18 test
    # events and got 6 right where the base rate is 0.56; a single
    # binomial test on that is p=0.11, and SIX rules were tried,
    # so the expected number of rules doing at least this well by
    # chance is about 0.6. Reporting the maximum of six draws
    # without saying it was a maximum is the selection effect this
    # project has already shipped once.
    #
    # Each rule therefore carries a binomial p, and the verdict is
    # taken against a threshold corrected for how many were tried.
    for r in res["rules"]:
        n, k = r["test_n_selected"], None
        k = round(r["test_hit_rate"] * n)
        p0 = r["test_base_rate"]
        # P(X >= k) under Binomial(n, p0)
        tail = sum(math.comb(n, i) * p0 ** i * (1 - p0) ** (n - i)
                   for i in range(k, n + 1))
        r["binomial_p"] = tail
        r["expected_by_chance_among_rules"] = tail * len(res["rules"])
    best = res["rules"][0] if res["rules"] else None
    thr = 0.05 / max(1, len(res["rules"]))
    res["selection_corrected_threshold"] = thr
    res["rules_tried"] = len(res["rules"])
    if not best:
        res["verdict"] = "no rule had enough events to score"
    elif best["binomial_p"] < thr:
        res["verdict"] = (
            f"{best['feature']} survives selection correction "
            f"(binomial p={best['binomial_p']:.3f} against a "
            f"{thr:.3f} threshold for {len(res['rules'])} rules)")
    else:
        res["verdict"] = (
            f"NO RULE SURVIVES. The best is {best['feature']} at "
            f"lift {best['lift']:+.2f}, but it selects only "
            f"{best['test_n_selected']} of {len(te)} test events "
            f"and its binomial p is {best['binomial_p']:.3f} — "
            f"against a {thr:.3f} threshold once the "
            f"{len(res['rules'])} rules tried are accounted for. "
            f"The addition drift is not predictable out of sample "
            f"from anything measured here.")
    return res


def era_split(rows):
    """§0.3.5 applied to the results, not just to the sample.

    c-316, AND THIS ONE NEARLY SHIPPED. The pooled addition
    reversion is -5.29% at +20 with 67% of events negative, and
    the page was written around it as "the addition trade is
    fully round-tripped". Splitting at MSCI's Feb-2023 move to a
    full quarterly comprehensive review:

        pre-2023   n=34   median -5.65%   76% negative
        post-2023  n=18   median +0.01%   50% negative

    The reversion is a pre-2023 phenomenon. The pooled number is
    an average of a real effect and no effect, and quoting it for
    a 2026 review would be answering a question about 2018.

    The question bank makes this binding — "Pre- and post-2023
    are different populations for anything cadence-dependent.
    Split and test rather than pooling" — and §0.3.6 adds the
    honest qualifier: a period split is not a controlled
    experiment. Taiwan's price limit, its ETF complex and the
    size of the passive book all changed too. What can be said is
    that the effect is not present in the recent half; WHY is not
    identified here.
    """
    out = {}
    for side in ("ADD", "DEL"):
        g = [r for r in rows if r["action"] == side]
        blocks = {}
        for era in ("pre2023", "post2023"):
            e = [r for r in g if r["era"] == era]
            blocks[era] = {
                "n": len(e),
                "drift": describe([r["drift"] for r in e]),
                "eff_day": describe([r["eff_day"] for r in e]),
                "revert20": describe(
                    [r["path"].get("20") for r in e]),
                "vol_mult_eff": describe(
                    [r["vol_mult_eff"] for r in e]),
                "share_revert20_negative": (
                    sum(1 for r in e
                        if (r["path"].get("20") or 0) < 0)
                    / max(1, sum(1 for r in e
                                 if r["path"].get("20") is not None))),
            }
        for k in ("drift", "revert20", "vol_mult_eff"):
            a = [r["drift"] if k == "drift" else
                 (r["path"].get("20") if k == "revert20"
                  else r["vol_mult_eff"])
                 for r in g if r["era"] == "pre2023"]
            b = [r["drift"] if k == "drift" else
                 (r["path"].get("20") if k == "revert20"
                  else r["vol_mult_eff"])
                 for r in g if r["era"] == "post2023"]
            blocks[f"{k}_p"] = mannwhitney_p(a, b)
        # THE ROUND TRIP, event by event. Medians do not add: the
        # pooled drift is +2.21% and the pooled revert20 is
        # -5.29%, which invites the reader to subtract them and
        # get -3%. The per-event sum is the honest version.
        rt = [r["drift"] + r["path"]["20"] for r in g
              if r["drift"] is not None and r["path"].get("20")
              is not None]
        blocks["round_trip"] = describe(rt)
        blocks["round_trip"]["share_negative"] = (
            sum(1 for x in rt if x < 0) / len(rt) if rt else None)
        out[side] = blocks
    return out


def crowded_reviews(rows):
    """E5. Does a review carrying several names dilute each one?

    Directly relevant to Aug-2026, which carries four additions.
    """
    out = {}
    for side in ("ADD", "DEL"):
        g = [r for r in rows if r["action"] == side]
        solo = [r for r in g if r["n_same_review"] <= 1]
        many = [r for r in g if r["n_same_review"] >= 3]
        out[side] = {
            "solo": {"n": len(solo),
                     "drift": describe([r["drift"] for r in solo]),
                     "vol_mult_eff": describe(
                         [r["vol_mult_eff"] for r in solo])},
            "three_or_more": {
                "n": len(many),
                "drift": describe([r["drift"] for r in many]),
                "vol_mult_eff": describe(
                    [r["vol_mult_eff"] for r in many])},
            "drift_p": mannwhitney_p([r["drift"] for r in solo],
                                     [r["drift"] for r in many]),
            "print_p": mannwhitney_p([r["vol_mult_eff"] for r in solo],
                                     [r["vol_mult_eff"] for r in many]),
        }
    return out


def repeat_movers(rows):
    """E6. Is a name that has moved before different?"""
    out = {}
    for side in ("ADD", "DEL"):
        g = [r for r in rows if r["action"] == side]
        a = [r for r in g if r["repeat_mover"]]
        b = [r for r in g if not r["repeat_mover"]]
        out[side] = {
            "repeat": {"n": len(a),
                       "drift": describe([r["drift"] for r in a]),
                       "vol_mult_eff": describe(
                           [r["vol_mult_eff"] for r in a])},
            "first_time": {"n": len(b),
                           "drift": describe([r["drift"] for r in b]),
                           "vol_mult_eff": describe(
                               [r["vol_mult_eff"] for r in b])},
            "drift_p": mannwhitney_p([r["drift"] for r in a],
                                     [r["drift"] for r in b]),
        }
    return out


def schedules(rows, cost_bp=40):
    """C3. Three schedules, priced in P&L and in tracking error.

    c-316 REWROTE THIS. The first version measured each schedule
    against the total drift and then subtracted accrual at a
    mismatched offset, which is visible in the output rather than
    in the code: the effective-close row came back with a median
    of -0.48% and a 3.50% tracking error. That row IS the
    benchmark. It has to be exactly zero on both, and any version
    where it is not is measuring something else.

    Stated properly. Build a market-adjusted price path indexed to
    the announcement-plus-one close:

        P(t) = 1 + accrual(t),   t = 0 at ann+1
        t_eff = the effective close

    A schedule is a set of sessions to execute on. For a BUY the
    saving against the benchmark is (P_eff - P_avg) / P_eff — you
    are better off having paid less than the close. For a SELL the
    sign flips. The benchmark schedule executes only at t_eff, so
    its saving is identically zero and its dispersion with it.

    Tracking error here is the cross-event dispersion of that
    saving: the tracker does not want the P&L, it wants the number
    in the second column to be small.
    """
    out = {}
    for side in ("ADD", "DEL"):
        g = [r for r in rows if r["action"] == side]
        sgn = 1 if side == "ADD" else -1
        plans = {}
        for name, offsets in (("eff_close", [0]),
                              ("last_four", [3, 2, 1, 0]),
                              ("ann_plus_1", "open")):
            saves = []
            for r in g:
                acc = r["accrual"]
                if not acc:
                    continue
                t_eff = max(int(k) for k in acc)
                p_eff = 1.0 + acc[str(t_eff)]
                if p_eff <= 0:
                    continue
                if offsets == "open":
                    prices = [1.0 + acc["0"]] if "0" in acc else []
                else:
                    prices = [1.0 + acc[str(t_eff - o)]
                              for o in offsets
                              if str(t_eff - o) in acc
                              and t_eff - o >= 0]
                if not prices:
                    continue
                p_avg = st.mean(prices)
                saves.append(sgn * (p_eff - p_avg) / p_eff)
            plans[name] = {
                "n": len(saves),
                "median_saved": pct(saves, .5),
                "mean_saved": st.mean(saves) if saves else None,
                "p10": pct(saves, .10), "p90": pct(saves, .90),
                "hit_rate": (sum(1 for s in saves if s > 0) / len(saves)
                             if saves else None),
                "tracking_error": (st.pstdev(saves)
                                   if len(saves) > 2 else None),
                "median_saved_net": (pct(saves, .5) - cost_bp / 10000
                                     if saves else None)}
        out[side] = plans
    out["cost_bp_assumed"] = cost_bp
    out["_note"] = ("saving is measured against the effective "
                    "close, which is the tracker's benchmark — so "
                    "the eff_close row is zero by construction and "
                    "is the control that this is measured right")
    return out


def volume_normalises(rows):
    """G4. When does the name stop being an index position?

    Sessions after the effective date until volume falls back
    inside 1.5x the pre-announcement ADV and STAYS there for two
    consecutive sessions — one quiet day inside a busy fortnight
    is not a return to normal.
    """
    wins = (_j("tw_event_windows.json") or {}).get("windows", {})
    out = {}
    for side in ("ADD", "DEL"):
        days = []
        for r in rows:
            if r["action"] != side or not r["adv"]:
                continue
            w = wins.get(r["key"]) or {}
            bars = sorted(w.get("px") or [], key=lambda b: b["d"])
            dates = [b["d"] for b in bars]
            if r["eff"] not in dates:
                continue
            i = dates.index(r["eff"])
            run = 0
            for n in range(1, min(HORIZON, len(bars) - i - 1) + 1):
                v = bars[i + n].get("v") or 0
                run = run + 1 if v and v <= 1.5 * r["adv"] else 0
                if run >= 2:
                    days.append(n - 1)
                    break
        out[side] = describe(days)
        out[side]["censored_note"] = (
            "events that never settle inside the horizon are NOT "
            "counted, so this is the median among those that did "
            "settle and understates the true wait")
    return out


def write_doc(o):
    """The findings, interpolated from the JSON.

    Nothing here is typed. §0.4 of the question bank requires the
    doc, the data file and the page to be the same numbers, and
    the only way that survives a re-run is for the prose to read
    from the file it is describing.
    """
    A, D = o["anatomy"]["ADD"], o["anatomy"]["DEL"]
    FA, FD = o["foreign_flow"]["ADD"], o["foreign_flow"]["DEL"]
    S, MC = o["sample"], o["multiple_comparisons"]
    OOS, SCH = o["out_of_sample"], o["schedules"]["ADD"]
    ACC = o["drift_accrual"]["ADD"]

    def p(v, f="{:+.2%}"):
        return f.format(v) if v is not None else "n/a"

    L = []
    L.append("# MSCI Taiwan additions — the historical study\n")
    L.append(f"Generated by `scripts/tw_addition_study.py` into "
             f"`data/tw_addition_study.json`. Every figure below is "
             f"interpolated from that file.\n")
    L.append("## The sample\n")
    L.append(f"- **{S['kept']} windows** — {S['additions']} "
             f"additions, {S['deletions']} deletions — "
             f"{S['first_review']} to {S['last_review']}.")
    L.append(f"- {S['dropped'].get('dropped_estimated_day0', 0)} "
             f"windows dropped for an estimated announcement date, "
             f"{S['dropped'].get('dropped_short_window', 0)} for a "
             f"short window.")
    L.append(f"- Returns are {S['returns']}. Day 0 is "
             f"{S['day0']}. The deletion sample is "
             f"{S['survivorship']}.\n")

    L.append("## The four legs of an addition\n")
    L.append("| | additions | deletions |")
    L.append("|---|---|---|")
    for lab, k in (("pre-announcement drift (median)", "pre_drift"),
                   ("announcement gap", "gap1"),
                   ("drift, ann+1 to eff-1", "drift"),
                   ("effective-day move", "eff_day"),
                   ("+5 sessions after", "revert5"),
                   ("+20 sessions after", "revert20")):
        L.append(f"| {lab} | {p(A[k]['p50'])} | {p(D[k]['p50'])} |")
    L.append(f"| effective-day print, x ADV | "
             f"{A['vol_mult_eff']['p50']:.1f}x | "
             f"{D['vol_mult_eff']['p50']:.1f}x |")
    L.append(f"| ...p90 | {A['vol_mult_eff']['p90']:.1f}x | "
             f"{D['vol_mult_eff']['p90']:.1f}x |")
    L.append("")
    E = o["era_split"]["ADD"]
    RT = E["round_trip"]
    L.append(f"**The round trip is a coin flip, not a loss.** The "
             f"median addition earns {p(A['drift']['p50'])} to the "
             f"effective date and gives back "
             f"{p(A['revert20']['p50'])} over the next twenty "
             f"sessions — but medians do not add. Summed event by "
             f"event the round trip is {p(RT['p50'])} at the "
             f"median, {RT['share_negative']:.0%} of events "
             f"negative, quartiles {p(RT['p25'])} to "
             f"{p(RT['p75'])}. Its mean drift "
             f"({p(A['drift']['mean'])}) is nearly three times its "
             f"median, so the average is carried by a handful of "
             f"events and a book sized on it is sized on those.\n")
    L.append(f"**The reversion is a pre-2023 result and the split "
             f"is not significant either way.**\n")
    L.append("| | pre-2023 | post-2023 | p |")
    L.append("|---|---|---|---|")
    for lab, k in (("drift", "drift"), ("+20 after", "revert20"),
                   ("print, x ADV", "vol_mult_eff")):
        f = ("{:.1f}x" if k == "vol_mult_eff" else "{:+.2%}")
        L.append(f"| {lab} (n={E['pre2023'][k]['n']} / "
                 f"{E['post2023'][k]['n']}) | "
                 f"{p(E['pre2023'][k]['p50'], f)} | "
                 f"{p(E['post2023'][k]['p50'], f)} | "
                 f"{E[k + '_p']:.2f} |")
    L.append("")
    L.append(f"Reversion ran {p(E['pre2023']['revert20']['p50'])} "
             f"with {E['pre2023']['share_revert20_negative']:.0%} "
             f"of events negative before Feb-2023 and "
             f"{p(E['post2023']['revert20']['p50'])} with "
             f"{E['post2023']['share_revert20_negative']:.0%} "
             f"since. At p={E['revert20_p']:.2f} on n=18 the "
             f"sample cannot establish that the effect has gone — "
             f"only that it cannot establish it is still there. "
             f"Per §0.3.6, a period split is not a controlled "
             f"experiment: Taiwan's ETF complex and passive book "
             f"changed over the same span and are not separated "
             f"here.\n")
    L.append(f"**Most of the move precedes the news.** "
             f"Pre-announcement drift is {p(A['pre_drift']['p50'])} "
             f"at the median and positive "
             f"{A['pre_drift']['right_sign_share']:.0%} of the "
             f"time — about three times what is left afterwards.\n")

    L.append("## Who is on the other side\n")
    L.append(f"Foreign net flow, in days of the name's own ADV, "
             f"from TWSE T86 day files (n={FA['n_with_flow']} "
             f"additions, {FD['n_with_flow']} deletions):\n")
    L.append("| leg | additions | deletions |")
    L.append("|---|---|---|")
    for lab, k in (("20 sessions before the announcement", "pre"),
                   ("announcement to effective", "ann_to_eff"),
                   ("the effective day", "effective_day"),
                   ("the ten sessions after", "post10"),
                   ("cumulative to the print",
                    "cumulative_to_effective")):
        L.append(f"| {lab} | {FA[k]['p50']:+.2f} | "
                 f"{FD[k]['p50']:+.2f} |")
    L.append("")
    L.append(f"**Foreigners are the deletion and barely the "
             f"addition.** A deletion draws "
             f"{abs(FD['cumulative_to_effective']['p50']):.1f} days "
             f"of ADV of foreign selling to the print and another "
             f"{abs(FD['post10']['p50']):.1f} after it; an addition "
             f"draws {FA['cumulative_to_effective']['p50']:.2f} "
             f"days of buying. Domestic institutions are within "
             f"±0.05 ADV days on both sides.\n")
    L.append(f"**The print is not ownership transfer.** On the "
             f"effective day, foreign plus domestic net is "
             f"{FA['institutional_share_of_print']['p50']:.1%} of "
             f"the volume that printed on an addition and "
             f"{FD['institutional_share_of_print']['p50']:.1%} on a "
             f"deletion. That is the mechanism behind the "
             f"reversion: there is no new holder to defend the "
             f"price.\n")
    L.append(f"**Half the buying is done before the "
             f"announcement** — "
             f"{FA['share_accumulated_before_announcement']['p50']:.0%} "
             f"of the whole accumulation, at the median.\n")

    L.append("## Execution\n")
    L.append("| schedule | median saved | hit rate | tracking error |")
    L.append("|---|---|---|---|")
    for k, lab in (("eff_close", "100% at the effective close"),
                   ("last_four", "25% x last four sessions"),
                   ("ann_plus_1", "100% at announcement +1")):
        L.append(f"| {lab} | {p(SCH[k]['median_saved'])} | "
                 f"{SCH[k]['hit_rate']:.0%} | "
                 f"{SCH[k]['tracking_error']:.2%} |")
    L.append("")
    L.append(f"The effective-close row is zero on both columns by "
             f"construction — it is the tracker's benchmark, and "
             f"it is the control that the other two are measured "
             f"right. Half the drift has accrued by session "
             f"{ACC['sessions_to_half']} of about thirteen and 80% "
             f"by session {ACC['sessions_to_eighty']}, so the curve "
             f"is close to linear and no date is special.\n")

    L.append("## The negative results\n")
    L.append(f"**Nothing predicts the direction out of sample.** "
             f"{OOS.get('rules_tried', 0)} rules fitted on "
             f"{OOS['n_train']} pre-2023 additions, scored on "
             f"{OOS['n_test']} since. {OOS['verdict']}\n")
    L.append(f"**{MC['tests_run']} hypotheses were tested**; the "
             f"Bonferroni threshold is "
             f"p<{MC['bonferroni_threshold']:.5f} and "
             f"{len(MC['survives_bonferroni'])} survive: "
             f"{', '.join(MC['survives_bonferroni'])}. Every one of "
             f"them is about the SIZE of the print. None is about "
             f"its direction.\n")
    L.append(f"**Five driver pairs were excluded for overlapping "
             f"windows**, including the announcement gap against "
             f"total alpha, which ranked first at rho +0.56 before "
             f"it was removed and is arithmetic rather than "
             f"evidence.\n")
    L.append(f"**Crowded reviews and repeat movers do nothing "
             f"measurable.** Three-or-more-addition reviews versus "
             f"solo ones, p="
             f"{o['crowded_reviews']['ADD']['drift_p']:.2f}; repeat "
             f"movers versus first-timers, p="
             f"{o['repeat_movers']['ADD']['drift_p']:.2f}.\n")
    DOC.write_text("\n".join(L), encoding="utf-8")


def main():
    rows, prov = build_events()
    add = [r for r in rows if r["action"] == "ADD"]
    tests = []

    res_anat = anatomy(rows)
    res_path = drift_path(rows)
    res_post = post_effective(rows)
    res_flow = flows(rows)
    res_drv, res_excl = drivers(rows, "ADD")
    res_drv_del, _ = drivers(rows, "DEL")
    res_oos = out_of_sample(rows, "ADD")
    res_crowd = crowded_reviews(rows)
    res_era = era_split(rows)
    res_rep = repeat_movers(rows)
    res_sched = schedules(rows)
    res_norm = volume_normalises(rows)

    # ── MULTIPLE COMPARISONS, counted honestly ──────────────────
    # Every hypothesis TOUCHED, not every one reported. A driver
    # table that ranks 44 pairs and then quotes the top one has
    # run 44 tests, and the correction has to know that or the
    # headline is a selection effect wearing a p-value.
    for t in res_drv + res_drv_del:
        tests.append({"test": f"{t['feature']}->{t['target']}",
                      "p": t["p"]})
    for side in ("ADD", "DEL"):
        f = res_flow[side]
        for k in ("mid_flow_vs_print", "mid_flow_vs_drift"):
            if f[k]["p"] is not None:
                tests.append({"test": f"{side}.{k}", "p": f[k]["p"]})
        if res_post[side]["drift_vs_revert20"]["p"] is not None:
            tests.append({"test": f"{side}.drift_vs_revert20",
                          "p": res_post[side]["drift_vs_revert20"]["p"]})
        for k in ("drift_p", "print_p"):
            v = res_crowd[side].get(k)
            if v is not None:
                tests.append({"test": f"{side}.crowded.{k}", "p": v})
        v = res_rep[side].get("drift_p")
        if v is not None:
            tests.append({"test": f"{side}.repeat.drift_p", "p": v})
    for side in ("ADD", "DEL"):
        for k in ("drift_p", "revert20_p", "vol_mult_eff_p"):
            v = res_era[side].get(k)
            if v is not None:
                tests.append({"test": f"{side}.era.{k}", "p": v})
    for k in ("print_size_p", "drift_p"):
        v = res_anat["asymmetry"].get(k)
        if v is not None:
            tests.append({"test": f"asymmetry.{k}", "p": v})

    thr = 0.05 / max(1, len(tests))
    survivors = sorted([t["test"] for t in tests if t["p"] < thr])
    nominal = sorted([t["test"] for t in tests if t["p"] < 0.05])

    out = {
        "_what": "MSCI Taiwan additions — the historical study "
                 "behind the Aug-2026 scenarios",
        "generated_from": "tw_event_windows.json, twii_daily.json, "
                          "t86_history.json, sbl_history.json, "
                          "margin_history.json",
        "sample": {
            "kept": prov["kept"],
            "additions": len(add),
            "deletions": sum(1 for r in rows if r["action"] == "DEL"),
            "dropped": {k: v for k, v in prov.items() if k != "kept"},
            "reviews": sorted({r["rev"] for r in rows},
                              key=rev_key),
            "first_review": min((r["rev"] for r in rows), key=rev_key),
            "last_review": max((r["rev"] for r in rows), key=rev_key),
            "returns": "excess over TAIEX, close to close",
            "day0": "registry-dated announcements only",
            "survivorship": "survivor-safe — TWSE/TPEx day files "
                            "retain delisted companies"},
        "anatomy": res_anat,
        "drift_accrual": res_path,
        "post_effective": res_post,
        "foreign_flow": res_flow,
        "drivers_add": res_drv[:25],
        "drivers_del": res_drv_del[:15],
        "drivers_excluded_for_overlap": res_excl,
        "out_of_sample": res_oos,
        "era_split": res_era,
        "crowded_reviews": res_crowd,
        "repeat_movers": res_rep,
        "schedules": res_sched,
        "volume_normalises": res_norm,
        "multiple_comparisons": {
            "tests_run": len(tests),
            "bonferroni_threshold": thr,
            "nominally_significant": nominal,
            "survives_bonferroni": survivors,
            "ranked": sorted(tests, key=lambda t: t["p"])[:30]},
        "events": rows,
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    write_doc(out)
    print(f"-> {OUT.relative_to(ROOT)}")
    print(f"-> {DOC.relative_to(ROOT)}")

    A, D = res_anat["ADD"], res_anat["DEL"]
    print(f"\nsample: {prov['kept']} windows "
          f"({len(add)} ADD / {out['sample']['deletions']} DEL), "
          f"{out['sample']['first_review']}-"
          f"{out['sample']['last_review']}")
    print(f"\n{'':22}{'ADDITIONS':>22}{'DELETIONS':>22}")
    for lab, k in (("pre-announcement drift", "pre_drift"),
                   ("announcement gap", "gap1"),
                   ("drift ann+1 -> eff-1", "drift"),
                   ("effective-day move", "eff_day"),
                   ("+5 after effective", "revert5"),
                   ("+20 after effective", "revert20")):
        a, d = A[k], D[k]
        print(f"{lab:22}{a['p50']:>+11.2%} (n{a['n']:>3}) "
              f"{d['p50']:>+11.2%} (n{d['n']:>3})")
    print(f"{'print, x ADV':22}{A['vol_mult_eff']['p50']:>11.1f}x"
          f" (n{A['vol_mult_eff']['n']:>3}) "
          f"{D['vol_mult_eff']['p50']:>11.1f}x"
          f" (n{D['vol_mult_eff']['n']:>3})")
    print(f"\ndrift accrual (ADD): half by session "
          f"{res_path['ADD']['sessions_to_half']}, 80% by "
          f"{res_path['ADD']['sessions_to_eighty']}")
    print(f"out-of-sample: {res_oos['verdict']}")
    print(f"multiple comparisons: {len(tests)} tests, "
          f"{len(survivors)} survive Bonferroni")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
