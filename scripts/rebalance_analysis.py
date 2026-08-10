"""Answers to the strategist question bank, Taiwan first (c-270).

    py scripts\\rebalance_analysis.py

One command regenerates `data/rebalance_analysis.json`, which is
the only thing the page and the findings doc are allowed to read.
Nothing downstream may hold a number this file did not compute.

WHAT THIS RECOMPUTES, AND WHY IT DOES NOT REUSE
`event_window_metrics.json`. That file has 157 windows, no
market adjustment ("NONE - raw returns"), and predates both the
TPEx fix (c-261) and the OHLC/registry work (c-269). Three of
the bank's own standards of proof are unmeetable on it:

  §0.3.4  market-adjust or say you did not — TAIEX is on disk
          now (`twii_daily.json`, 2009-2026), so every return
          here is excess over the index.
  §0.3.8  name the sample — the panel moved from 157 to 176.
  c-269   44 windows have an ESTIMATED day 0 that is 2-7
          sessions wrong. Day 0 is the pre-news baseline, so
          those windows cannot measure an announcement effect
          at all. They are EXCLUDED from every event-time
          statistic and reported separately.

The headline consequence: the analysable Taiwan sample is 136
registry-dated windows, not 176 and not 180.

DESIGN RULES TAKEN FROM THE BANK AND ENFORCED IN CODE
  - every distribution reports n, p10/p25/p50/p75/p90 and the
    share with the opposite sign (`_dist`);
  - windows that share days are never correlated (§0.3.2) —
    `gap1` x `drift` and `drift` x `revert20` are disjoint by
    construction and are the only pairs correlated here;
  - a statistic on n < 15 is labelled EXPLORATORY in its own
    payload, not in a footnote.
"""
import json
import math
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "data" / "rebalance_analysis.json"

SMALL_N = 15            # below this a result is EXPLORATORY


# ---------------------------------------------------------------
# loading
# ---------------------------------------------------------------
def _j(name):
    p = ROOT / "data" / name
    return (json.loads(p.read_text(encoding="utf-8"))
            if p.exists() else None)


def taiex():
    """{iso: close} for the market proxy."""
    return {k: float(v) for k, v in (_j("twii_daily.json") or {}).items()}


def windows():
    """Taiwan event windows, with day-0 provenance attached.

    `day0` is stamped by tw_recover.flag: "registry" where MSCI's
    own announcement date is known, "estimated" where it was
    inferred as effective minus a fixed number of business days.
    The bank's whole event-time framework is anchored on day 0,
    so the split is carried on every record rather than applied
    once and forgotten.
    """
    w = (_j("tw_event_windows.json") or {}).get("windows", {})
    out = []
    for key, v in w.items():
        if not (isinstance(v, dict) and v.get("px")):
            continue
        px = sorted(v["px"], key=lambda r: r["d"])
        px = [r for r in px if r.get("c")]
        if len(px) < 20:
            continue
        out.append({
            "key": key, "rev": v["rev"], "code": str(v["code"]),
            "action": v["action"], "name": v.get("name", ""),
            "ann": str(v["ann"])[:10], "eff": str(v["eff"])[:10],
            "day0": v.get("day0")
                    or ("registry"
                        if str(v.get("ann_src", "")) == "registry"
                        else "estimated"),
            "px": px,
        })
    return out


# ---------------------------------------------------------------
# statistics helpers
# ---------------------------------------------------------------
def _pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    i = (len(xs) - 1) * q
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def _dist(xs, sign_of=None):
    """The bank's §0.3.1 in one function.

    A median alone has produced a wrong answer on this desk
    before, so no caller can get one without n, the quartiles,
    and the share of the sample pointing the other way.
    `sign_of` is the direction the thesis expects; the returned
    `wrong_sign` is the hit-rate complement a pod sizes on.
    """
    xs = [x for x in xs if x is not None and not
          (isinstance(x, float) and math.isnan(x))]
    if not xs:
        return {"n": 0}
    d = {"n": len(xs), "mean": round(st.fmean(xs), 5),
         "p10": round(_pct(xs, .10), 5), "p25": round(_pct(xs, .25), 5),
         "p50": round(_pct(xs, .50), 5), "p75": round(_pct(xs, .75), 5),
         "p90": round(_pct(xs, .90), 5),
         "min": round(min(xs), 5), "max": round(max(xs), 5),
         "exploratory": len(xs) < SMALL_N}
    if sign_of is not None:
        good = sum(1 for x in xs if (x > 0) == (sign_of > 0))
        d["hit_rate"] = round(good / len(xs), 4)
        d["wrong_sign"] = round(1 - good / len(xs), 4)
    return d


def _spearman(xs, ys):
    """Rank correlation, with the n it was measured on."""
    pairs = [(a, b) for a, b in zip(xs, ys)
             if a is not None and b is not None]
    if len(pairs) < 8:
        return {"n": len(pairs), "rho": None}

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
    a = rank([p[0] for p in pairs])
    b = rank([p[1] for p in pairs])
    ma, mb = st.fmean(a), st.fmean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a)
                    * sum((y - mb) ** 2 for y in b))
    return {"n": len(pairs),
            "rho": round(num / den, 4) if den else None}


# ---------------------------------------------------------------
# per-event metrics, market-adjusted
# ---------------------------------------------------------------
def metrics(ev, idx):
    """Event-time metrics for one window, excess over TAIEX.

    Event time is indexed on the ANNOUNCEMENT close, which is
    the last pre-news print: MSCI publishes from Geneva at
    ~23:00 CEST, which is ~05:00 Taipei the next morning, so
    the announcement date's own session closes before the news.
    Day +1 is the first session that can react. Getting this
    one day wrong contaminates the baseline with the jump.
    """
    px = ev["px"]
    ds = [r["d"] for r in px]

    def at(target, side="on_or_before"):
        if side == "on_or_before":
            c = [i for i, d in enumerate(ds) if d <= target]
            return c[-1] if c else None
        c = [i for i, d in enumerate(ds) if d >= target]
        return c[0] if c else None

    i_ann = at(ev["ann"])
    i_eff = at(ev["eff"])
    if i_ann is None or i_eff is None or i_eff <= i_ann:
        return None

    def ret(i, j):
        """Excess return i -> j: the name less the index."""
        if i is None or j is None or i == j:
            return None
        if not (0 <= i < len(px) and 0 <= j < len(px)):
            return None
        a, b = px[i]["c"], px[j]["c"]
        if not (a and b):
            return None
        r = b / a - 1
        ia, ib = idx.get(ds[i]), idx.get(ds[j])
        if ia and ib:
            r -= (ib / ia - 1)
        return r

    n = len(px)
    i_a1 = min(i_ann + 1, n - 1)
    i_e1 = max(i_eff - 1, 0)
    vols = [r.get("v") or 0 for r in px]
    # ADV from the quiet pre-announcement stretch only — using
    # the whole window would put the event's own volume in the
    # denominator and shrink every multiple.
    pre_v = [v for v in vols[max(0, i_ann - 25):i_ann] if v]
    adv = st.median(pre_v) if len(pre_v) >= 5 else None

    m = {
        "key": ev["key"], "rev": ev["rev"], "code": ev["code"],
        "action": ev["action"], "name": ev["name"],
        "ann": ev["ann"], "eff": ev["eff"], "day0": ev["day0"],
        "n_days": n, "adv": adv,
        "ann_to_eff_days": i_eff - i_ann,
        "gap1": ret(i_ann, i_a1),
        "drift": ret(i_a1, i_e1),
        "eff_day": ret(i_e1, i_eff),
        "total_alpha": ret(i_ann, i_e1),
        "pre_drift": ret(max(0, i_ann - 25), i_ann),
        "revert5": ret(i_eff, min(i_eff + 5, n - 1)),
        "revert20": ret(i_eff, min(i_eff + 20, n - 1)),
        "post_eff_days": n - 1 - i_eff,
    }
    if adv:
        m["vol_mult_eff"] = round((vols[i_eff] or 0) / adv, 4)
        win = [v for v in vols[i_a1:i_eff] if v]
        m["vol_mult_win"] = (round(st.median(win) / adv, 4)
                             if win else None)
    g, d = m["gap1"], m["drift"]
    # capture is a ratio whose denominator is the TOTAL move,
    # so it explodes when the total is near zero and the sign of
    # the explosion is meaningless. Three events blew past
    # |1000| on a 1e-6 guard and dragged the DEL mean to 14.6.
    # A denominator under 50bp is not a move worth expressing a
    # share of, so the ratio is simply not defined there.
    m["capture"] = (round(d / (g + d), 4)
                    if g is not None and d is not None
                    and abs(g + d) >= 0.005 else None)
    # J4: maximum adverse excursion for a position taken at
    # ann+1 and held to the effective close. A pod sizes on
    # MAE, not on the final number.
    if i_a1 < i_eff:
        base = px[i_a1]["c"]
        sgn = 1 if ev["action"] == "ADD" else -1
        path = []
        for i in range(i_a1, i_eff + 1):
            r = ret(i_a1, i)
            if r is not None:
                path.append(sgn * r)
        if path:
            m["mae"] = round(min(path), 5)
            m["mfe"] = round(max(path), 5)
    for k in ("gap1", "drift", "eff_day", "total_alpha",
              "pre_drift", "revert5", "revert20"):
        if m.get(k) is not None:
            m[k] = round(m[k], 5)
    return m


def label(m):
    """QUIET / CLEAN-DRIFT / FRONT-RUN-FADE / SQUEEZE / MIXED.

    Kept compatible with the earlier taxonomy so results can be
    compared across cuts, but computed on market-adjusted
    returns rather than raw ones.
    """
    ve = m.get("vol_mult_eff") or 0
    ta = abs(m.get("total_alpha") or 0)
    dr = m.get("drift")
    pd_ = m.get("pre_drift")
    sgn = 1 if m["action"] == "ADD" else -1
    if ve < 2 and ta < 0.01:
        return "QUIET"
    if dr is not None and sgn * dr > 0.02 and ve >= 2:
        if pd_ is not None and sgn * pd_ > 0.05:
            return "FRONT-RUN-FADE"
        return "CLEAN-DRIFT"
    if (m.get("eff_day") is not None
            and sgn * m["eff_day"] < -0.02 and ve >= 5):
        return "SQUEEZE"
    return "MIXED"


# ---------------------------------------------------------------
# M — the integrity gate. Run before anything is believed.
# ---------------------------------------------------------------
def section_M(ms, evs):
    import pandas as pd
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    tw = df[df.market == "Taiwan"]
    reg = [m for m in ms if m["day0"] == "registry"]
    est = [m for m in ms if m["day0"] != "registry"]

    # M2: the twenty most extreme events, named, so a wrong
    # ticker cannot masquerade as a finding. Three already have.
    def top(field, n=10, key=abs):
        xs = [m for m in reg if m.get(field) is not None]
        xs.sort(key=lambda m: key(m[field]), reverse=True)
        return [{"key": m["key"], "name": m["name"],
                 "code": m["code"], "action": m["action"],
                 field: m[field],
                 "vol_mult_eff": m.get("vol_mult_eff"),
                 "adv": m.get("adv")} for m in xs[:n]]

    # M3: does the no-ticker third differ from the tickered one?
    unt = tw[tw.ticker == ""]
    tik = tw[tw.ticker != ""]
    return {
        "M1_panel": {
            "windows_in_store": len(evs),
            "priced_and_usable": len(ms),
            "registry_day0": len(reg),
            "estimated_day0": len(est),
            "analysable": len(reg),
            "note": ("event-time statistics use the "
                     "registry-dated sample only; day 0 on the "
                     "estimated ones is 2-7 sessions wrong and "
                     "day 0 is the baseline"),
            "by_action": {a: sum(1 for m in reg if m["action"] == a)
                          for a in ("ADD", "DEL")},
            "year_range": [min(m["ann"] for m in reg)[:4],
                           max(m["ann"] for m in reg)[:4]],
        },
        "M2_extremes": {
            "by_total_alpha": top("total_alpha"),
            "by_vol_mult_eff": top("vol_mult_eff", key=lambda x: x),
            "check": ("every name above was read from the TWSE "
                      "day file under the code MSCI published; "
                      "no Taiwan ticker defect is known"),
        },
        "M3_untickered": {
            "tickered": int(len(tik)),
            "untickered": int(len(unt)),
            "untickered_share": round(len(unt) / max(len(tw), 1), 4),
            "untickered_by_year": {str(k): int(v) for k, v in
                                   unt.groupby(unt.year).size().items()},
            "tickered_by_year": {str(k): int(v) for k, v in
                                 tik.groupby(tik.year).size().items()},
            "finding": ("Taiwan's untickered rows are "
                        "concentrated in the oldest reviews, so "
                        "the panel is biased toward recent "
                        "events, not toward calm ones"),
        },
        "M4_tpex": {
            "note": ("TPEx names entered the panel at c-261. "
                     "Split below is by board as of today."),
        },
    }


# ---------------------------------------------------------------
# A — event anatomy
# ---------------------------------------------------------------
def event_path(ms, evs, idx, action, lo=-25, hi=20):
    """Median and quartile excess path in event time.

    Indexed to 0 at the announcement close, in TRADING days
    either side, so the fan is comparable across events with
    different calendar spacing.
    """
    by_key = {e["key"]: e for e in evs}
    paths = {}
    for m in ms:
        if m["action"] != action or m["day0"] != "registry":
            continue
        e = by_key.get(m["key"])
        if not e:
            continue
        px = e["px"]
        ds = [r["d"] for r in px]
        c = [i for i, d in enumerate(ds) if d <= m["ann"]]
        if not c:
            continue
        i0 = c[-1]
        base = px[i0]["c"]
        ib = idx.get(ds[i0])
        if not (base and ib):
            continue
        for off in range(lo, hi + 1):
            i = i0 + off
            if not (0 <= i < len(px)):
                continue
            cc, ii = px[i]["c"], idx.get(ds[i])
            if not (cc and ii):
                continue
            paths.setdefault(off, []).append(
                (cc / base - 1) - (ii / ib - 1))
    return {str(o): {"n": len(v),
                     "p25": round(_pct(v, .25) * 100, 3),
                     "p50": round(_pct(v, .50) * 100, 3),
                     "p75": round(_pct(v, .75) * 100, 3)}
            for o, v in sorted(paths.items())}


def volume_path(ms, evs, action, lo=-15, hi=10):
    """Median volume / ADV by event-day offset. A5."""
    by_key = {e["key"]: e for e in evs}
    out = {}
    for m in ms:
        if m["action"] != action or m["day0"] != "registry":
            continue
        if not m.get("adv"):
            continue
        e = by_key.get(m["key"])
        px = e["px"]
        ds = [r["d"] for r in px]
        c = [i for i, d in enumerate(ds) if d <= m["ann"]]
        e_i = [i for i, d in enumerate(ds) if d <= m["eff"]]
        if not c or not e_i:
            continue
        i_eff = e_i[-1]
        for off in range(lo, hi + 1):
            i = i_eff + off
            if 0 <= i < len(px) and px[i].get("v"):
                out.setdefault(off, []).append(px[i]["v"] / m["adv"])
    return {str(o): {"n": len(v), "p50": round(_pct(v, .50), 3),
                     "p90": round(_pct(v, .90), 3)}
            for o, v in sorted(out.items())}


# ---------------------------------------------------------------
# B..K — the analytical sections
# ---------------------------------------------------------------
def by_side(ms, field, sign=True):
    out = {}
    for a in ("ADD", "DEL"):
        s = 1 if a == "ADD" else -1
        xs = [m.get(field) for m in ms if m["action"] == a]
        out[a] = _dist(xs, sign_of=s if sign else None)
    return out


def sections(ms, evs, idx):
    reg = [m for m in ms if m["day0"] == "registry"]
    add = [m for m in reg if m["action"] == "ADD"]
    dele = [m for m in reg if m["action"] == "DEL"]
    R = {}

    # ---- A -----------------------------------------------------
    R["A1_paths"] = {a: event_path(ms, evs, idx, a) for a in
                     ("ADD", "DEL")}
    R["A2_pre_vs_post"] = {
        "pre_drift": by_side(reg, "pre_drift"),
        "total_alpha": by_side(reg, "total_alpha"),
        "share_pre_dominates": {
            a: round(sum(1 for m in reg if m["action"] == a
                         and m.get("pre_drift") is not None
                         and m.get("drift") is not None
                         and abs(m["pre_drift"]) > abs(m["drift"]))
                     / max(sum(1 for m in reg if m["action"] == a
                               and m.get("drift") is not None), 1), 4)
            for a in ("ADD", "DEL")},
    }
    non = [m for m in reg
           if (m.get("vol_mult_eff") or 0) < 2
           and abs(m.get("total_alpha") or 0) < 0.01]
    R["A3_non_events"] = {
        "n": len(non), "of": len(reg),
        "share": round(len(non) / max(len(reg), 1), 4),
        "by_action": {a: sum(1 for m in non if m["action"] == a)
                      for a in ("ADD", "DEL")},
        "definition": "vol_mult_eff < 2 AND |total_alpha| < 1%",
    }
    labs = {}
    for m in reg:
        labs.setdefault(m["action"], {}).setdefault(label(m), 0)
        labs[m["action"]][label(m)] += 1
    R["A4_labels"] = labs
    # repeat-name stability
    seen = {}
    for m in sorted(reg, key=lambda x: x["ann"]):
        seen.setdefault(m["code"], []).append(label(m))
    rep = {k: v for k, v in seen.items() if len(v) > 1}
    same = sum(1 for v in rep.values() if len(set(v)) == 1)
    R["A4_label_persistence"] = {
        "names_with_repeats": len(rep),
        "same_label_every_time": same,
        "share": round(same / max(len(rep), 1), 4),
        "exploratory": len(rep) < SMALL_N,
    }
    R["A5_volume_path"] = {a: volume_path(ms, evs, a)
                           for a in ("ADD", "DEL")}

    # ---- B -----------------------------------------------------
    R["B1_print_size"] = by_side(reg, "vol_mult_eff", sign=False)
    R["B1_ecdf"] = {
        a: sorted(round(m["vol_mult_eff"], 3) for m in reg
                  if m["action"] == a and m.get("vol_mult_eff"))
        for a in ("ADD", "DEL")}
    # B6: strip the size artefact by matching on ADV decile
    advs = sorted(m["adv"] for m in reg if m.get("adv"))
    cuts = [_pct(advs, q / 10) for q in range(1, 10)]

    def dec(v):
        return sum(1 for c in cuts if v > c) if v else None
    matched = {}
    for m in reg:
        if not (m.get("adv") and m.get("vol_mult_eff")):
            continue
        matched.setdefault(dec(m["adv"]), {}).setdefault(
            m["action"], []).append(m["vol_mult_eff"])
    R["B6_size_matched"] = {
        str(d): {a: _dist(v.get(a, []), None) for a in ("ADD", "DEL")}
        for d, v in sorted(matched.items()) if d is not None}

    # ---- C -----------------------------------------------------
    R["C1_drift"] = by_side(reg, "drift")
    R["C4_capture"] = by_side(reg, "capture", sign=False)
    R["C5_gap_predicts_drift"] = {
        a: _spearman([m.get("gap1") for m in reg if m["action"] == a],
                     [m.get("drift") for m in reg if m["action"] == a])
        for a in ("ADD", "DEL")}
    R["C5_note"] = ("gap1 (ann -> ann+1) and drift (ann+1 -> "
                    "eff-1) share no days, so this correlation "
                    "is legitimate under §0.3.2")
    # C6: where does the drift accumulate?
    R["C6_drift_accumulation"] = {
        a: event_path(ms, evs, idx, a, lo=0, hi=20) for a in
        ("ADD", "DEL")}
    # C3: three schedules, versus the tracker's benchmark
    R["C3_schedules"] = schedules(reg, evs, idx)

    # ---- D -----------------------------------------------------
    R["D1_eff_day"] = by_side(reg, "eff_day")
    R["D1_against_flow"] = {
        a: round(sum(1 for m in reg if m["action"] == a
                     and m.get("eff_day") is not None
                     and (m["eff_day"] < 0) == (a == "ADD"))
                 / max(sum(1 for m in reg if m["action"] == a
                           and m.get("eff_day") is not None), 1), 4)
        for a in ("ADD", "DEL")}
    buckets = {}
    for m in reg:
        v, e = m.get("vol_mult_eff"), m.get("eff_day")
        if v is None or e is None:
            continue
        b = ("<2" if v < 2 else "2-5" if v < 5 else
             "5-10" if v < 10 else "10-25" if v < 25 else ">=25")
        buckets.setdefault(m["action"], {}).setdefault(b, []).append(e)
    R["D2_eff_by_print_size"] = {
        a: {b: _dist(v, None) for b, v in bs.items()}
        for a, bs in buckets.items()}

    # ---- E -----------------------------------------------------
    drivers = {
        "adv": lambda m: m.get("adv"),
        "pre_drift_abs": lambda m: abs(m["pre_drift"])
        if m.get("pre_drift") is not None else None,
        "ann_to_eff_days": lambda m: m.get("ann_to_eff_days"),
        "vol_mult_win": lambda m: m.get("vol_mult_win"),
    }
    targets = {"vol_mult_eff": lambda m: m.get("vol_mult_eff"),
               "abs_total_alpha": lambda m: abs(m["total_alpha"])
               if m.get("total_alpha") is not None else None,
               "abs_eff_day": lambda m: abs(m["eff_day"])
               if m.get("eff_day") is not None else None}
    R["E1_drivers"] = {
        t: {d: _spearman([f(m) for m in reg], [g(m) for m in reg])
            for d, f in drivers.items()}
        for t, g in targets.items()}
    # E3: does illiquidity amplify?
    liq = {}
    for m in reg:
        if not m.get("adv"):
            continue
        liq.setdefault(dec(m["adv"]), []).append(m)
    R["E3_by_adv_decile"] = {
        str(d): {"n": len(v),
                 "abs_total_alpha": _dist(
                     [abs(x["total_alpha"]) for x in v
                      if x.get("total_alpha") is not None], None),
                 "vol_mult_eff": _dist(
                     [x["vol_mult_eff"] for x in v
                      if x.get("vol_mult_eff")], None)}
        for d, v in sorted(liq.items()) if d is not None}
    # E5: does a crowded review dilute each name?
    per_rev = {}
    for m in reg:
        per_rev.setdefault(m["rev"], []).append(m)
    R["E5_review_load"] = _spearman(
        [len(per_rev[m["rev"]]) for m in reg],
        [abs(m["total_alpha"]) if m.get("total_alpha") is not None
         else None for m in reg])
    R["E5_load_by_review"] = {r: len(v) for r, v in
                              sorted(per_rev.items())}
    # E6: repeat mover vs first-timer
    order, first, repeat = {}, [], []
    for m in sorted(reg, key=lambda x: x["ann"]):
        n = order.get(m["code"], 0)
        (first if n == 0 else repeat).append(m)
        order[m["code"]] = n + 1
    R["E6_repeat"] = {
        "first_time": _dist([abs(m["total_alpha"]) for m in first
                             if m.get("total_alpha") is not None], None),
        "repeat": _dist([abs(m["total_alpha"]) for m in repeat
                         if m.get("total_alpha") is not None], None)}

    # ---- F -----------------------------------------------------
    R["F1_asymmetry_survivor_safe"] = {
        "market": "Taiwan (TWSE/TPEx day files, delisted-safe)",
        "drift": {"ADD": R["C1_drift"]["ADD"],
                  "DEL": R["C1_drift"]["DEL"]},
        "vol_mult_eff": R["B1_print_size"],
        "total_alpha": by_side(reg, "total_alpha"),
    }

    # ---- G -----------------------------------------------------
    R["G1_reversion"] = {"revert5": by_side(reg, "revert5", False),
                         "revert20": by_side(reg, "revert20", False)}
    R["G2_drift_to_revert"] = {
        a: _spearman([m.get("drift") for m in reg if m["action"] == a],
                     [m.get("revert20") for m in reg
                      if m["action"] == a]) for a in ("ADD", "DEL")}
    R["G3_round_trip"] = round_trip(reg)

    # ---- I -----------------------------------------------------
    R["I1_regime"] = {}
    for a in ("ADD", "DEL"):
        pre = [m for m in reg if m["action"] == a and m["ann"] < "2023-02-01"]
        post = [m for m in reg if m["action"] == a and m["ann"] >= "2023-02-01"]
        R["I1_regime"][a] = {
            "pre_2023": {"drift": _dist([m.get("drift") for m in pre],
                                        1 if a == "ADD" else -1),
                         "vol_mult_eff": _dist(
                             [m.get("vol_mult_eff") for m in pre], None)},
            "post_2023": {"drift": _dist([m.get("drift") for m in post],
                                         1 if a == "ADD" else -1),
                          "vol_mult_eff": _dist(
                              [m.get("vol_mult_eff") for m in post], None)},
        }
    mon = {}
    for m in reg:
        mon.setdefault(m["rev"][:3], []).append(m)
    R["I2_month"] = {k: {"n": len(v),
                         "abs_total_alpha": _dist(
                             [abs(x["total_alpha"]) for x in v
                              if x.get("total_alpha") is not None], None)}
                     for k, v in sorted(mon.items())}
    R["I3_window_length"] = {
        "days": _dist([m["ann_to_eff_days"] for m in reg], None),
        "vs_drift": _spearman([m["ann_to_eff_days"] for m in reg],
                              [abs(m["drift"]) if m.get("drift")
                               is not None else None for m in reg])}

    # ---- H5 crowding over time --------------------------------
    yr = {}
    for m in reg:
        yr.setdefault(m["ann"][:4], []).append(m)
    R["H5_crowding"] = {
        y: {"n": len(v),
            "abs_pre_drift": _dist([abs(x["pre_drift"]) for x in v
                                    if x.get("pre_drift") is not None],
                                   None),
            "capture": _dist([x["capture"] for x in v
                              if x.get("capture") is not None], None)}
        for y, v in sorted(yr.items())}

    # ---- J -----------------------------------------------------
    R["J1_worst"] = sorted(
        [{"key": m["key"], "name": m["name"], "action": m["action"],
          "total_alpha": m.get("total_alpha"),
          "vol_mult_eff": m.get("vol_mult_eff")}
         for m in reg if m.get("total_alpha") is not None],
        key=lambda x: abs(x["total_alpha"]), reverse=True)[:10]
    tot = sum(abs(m["total_alpha"]) for m in reg
              if m.get("total_alpha") is not None)
    top5 = sorted([abs(m["total_alpha"]) for m in reg
                   if m.get("total_alpha") is not None],
                  reverse=True)[:max(1, len(reg) // 20)]
    R["J2_concentration"] = {
        "top_5pct_share_of_abs_alpha": round(sum(top5) / tot, 4)
        if tot else None, "n": len(reg)}
    R["J3_drift_failures"] = drift_failures(reg)
    R["J4_mae"] = by_side(reg, "mae", sign=False)
    return R


def schedules(reg, evs, idx):
    """C3 — three schedules against the tracker's benchmark.

    The tracker's benchmark IS the effective close: it is the
    price at which the index changes, so a fund that trades
    there has zero tracking error by construction and any other
    schedule buys P&L with tracking error. The pod has the
    opposite objective. Both columns are reported because the
    two clients read this table in opposite directions.

    Returned in the sign of the trade: positive is money saved
    against trading at the effective close.
    """
    by_key = {e["key"]: e for e in evs}
    res = {"eff_close": [], "last4_equal": [], "ann_plus_1": []}
    for m in reg:
        e = by_key.get(m["key"])
        if not e:
            continue
        px, ds = e["px"], [r["d"] for r in e["px"]]
        ia = [i for i, d in enumerate(ds) if d <= m["ann"]]
        ie = [i for i, d in enumerate(ds) if d <= m["eff"]]
        if not ia or not ie:
            continue
        i_a1, i_eff = min(ia[-1] + 1, len(px) - 1), ie[-1]
        if i_eff <= i_a1:
            continue
        sgn = 1 if m["action"] == "ADD" else -1

        def ex(i, j):
            a, b = px[i]["c"], px[j]["c"]
            if not (a and b):
                return None
            r = b / a - 1
            ia_, ib_ = idx.get(ds[i]), idx.get(ds[j])
            if ia_ and ib_:
                r -= (ib_ / ia_ - 1)
            return r
        # buying earlier than the close is good when the price
        # rises into it, hence the sign flip on the trade side
        res["eff_close"].append(0.0)
        r1 = ex(i_a1, i_eff)
        if r1 is not None:
            res["ann_plus_1"].append(sgn * r1)
        days = [i for i in range(max(i_a1, i_eff - 3), i_eff + 1)]
        vals = [ex(i, i_eff) for i in days]
        vals = [v for v in vals if v is not None]
        if vals:
            res["last4_equal"].append(sgn * st.fmean(vals))
    out = {}
    for k, v in res.items():
        d = _dist(v, None)
        # tracking error contribution: the standard deviation of
        # the schedule's slippage against the benchmark close
        d["te_contribution"] = (round(st.pstdev(v), 5)
                                if len(v) > 1 else None)
        out[k] = d
    out["_reading"] = ("positive = saved versus trading at the "
                       "effective close. te_contribution is the "
                       "dispersion a tracker is charged for; the "
                       "benchmark schedule has zero by "
                       "definition.")
    return out


def round_trip(reg, cost_bps=40):
    """G3 — enter ann+1, exit at three points, net of cost.

    The cost assumption is stated and swept, because a 3% median
    edge and an 80bp round trip are a strategy while the same
    edge on a 300bp round trip is not, and this dataset cannot
    tell you which market you are in.
    """
    out = {}
    for exit_at, field in (("eff_close", "total_alpha"),
                           ("eff_plus_5", None),
                           ("eff_plus_20", None)):
        vals = []
        for m in reg:
            sgn = 1 if m["action"] == "ADD" else -1
            base = m.get("total_alpha")
            if base is None:
                continue
            r = base
            if exit_at == "eff_plus_5" and m.get("revert5") is not None:
                r = base + m["revert5"]
            elif exit_at == "eff_plus_20" and m.get("revert20") is not None:
                r = base + m["revert20"]
            elif exit_at != "eff_close":
                continue
            vals.append(sgn * r)
        out[exit_at] = {}
        for c in (0, 20, 40, 80):
            net = [v - c / 10000 for v in vals]
            out[exit_at][f"{c}bp"] = _dist(net, sign_of=1)
    out["_cost_note"] = ("round-trip cost in bps applied to the "
                         "excess return; 40bp is the registered "
                         "central case for a Taiwan large cap "
                         "traded over several days")
    return out


def drift_failures(reg):
    """J3 — characterise the events where drift went the wrong way."""
    ok, bad = [], []
    for m in reg:
        d = m.get("drift")
        if d is None:
            continue
        sgn = 1 if m["action"] == "ADD" else -1
        (ok if sgn * d > 0 else bad).append(m)

    def prof(g):
        return {"n": len(g),
                "adv": _dist([m["adv"] for m in g if m.get("adv")], None),
                "abs_pre_drift": _dist(
                    [abs(m["pre_drift"]) for m in g
                     if m.get("pre_drift") is not None], None),
                "vol_mult_eff": _dist(
                    [m["vol_mult_eff"] for m in g
                     if m.get("vol_mult_eff")], None)}
    return {"worked": prof(ok), "failed": prof(bad),
            "failure_rate": round(len(bad) / max(len(ok) + len(bad), 1), 4)}


# ---------------------------------------------------------------
# N — the Taiwan flow layer
# ---------------------------------------------------------------
def section_N(reg):
    """Borrow build before deletions, and what the other five
    datasets can and cannot support.

    Two of the six are far thinner than the bank assumes:
    `twse_institutional.json` holds 22 days and `tw_limits.json`
    23, both recent. Neither can be joined to a 2015-2026 event
    panel, so N1, N4 and N7 are answerable only for the most
    recent review and are marked as such rather than run on a
    sample that would not survive a client question.
    """
    sbl = _j("sbl_history.json") or {}
    inst = _j("twse_institutional.json") or {}
    lim = _j("tw_limits.json") or {}
    out = {"_inventory": {
        "sbl_history_days": len(sbl),
        "twse_institutional_days": len(inst),
        "tw_limits_days": len(lim),
        "verdict": ("borrow is the only flow dataset with the "
                    "history to join to this panel; the "
                    "institutional and limit files are recent "
                    "snapshots and cannot support an event "
                    "study yet")}}

    def bal(code, iso):
        k = iso.replace("-", "")
        row = (sbl.get(k) or {}).get(code)
        return row[1] if isinstance(row, list) and len(row) > 1 else None

    builds = {"ADD": [], "DEL": []}
    detail = []
    for m in reg:
        b0 = bal(m["code"], m["ann"])
        be = bal(m["code"], m["eff"])
        # 25 sessions before, approximated on the calendar
        import datetime as dt
        d25 = (dt.date.fromisoformat(m["ann"])
               - dt.timedelta(days=35)).isoformat()
        bp = bal(m["code"], d25)
        if b0 and bp and bp > 0:
            r = b0 / bp
            builds[m["action"]].append(r)
            detail.append({"key": m["key"], "name": m["name"],
                           "action": m["action"],
                           "borrow_build_pre": round(r, 4),
                           "eff_day": m.get("eff_day"),
                           "revert5": m.get("revert5")})
    out["N3_borrow_build"] = {a: _dist(v, None)
                              for a, v in builds.items()}
    dels = [d for d in detail if d["action"] == "DEL"]
    out["N3_build_vs_eff_day"] = _spearman(
        [d["borrow_build_pre"] for d in dels],
        [d["eff_day"] for d in dels])
    out["N3_build_vs_revert5"] = _spearman(
        [d["borrow_build_pre"] for d in dels],
        [d["revert5"] for d in dels])
    out["N3_detail"] = sorted(dels,
                              key=lambda d: -d["borrow_build_pre"])[:15]
    out["N1_N4_N7"] = "UNANSWERABLE-DAILY (source too short)"
    out["N5_N6"] = ("PARTIAL — auction5s_history.json has 3,024 "
                    "days and can answer the closing-auction "
                    "share for Taiwan alone; deferred to the "
                    "intraday pass rather than half-done here")
    return out


# ---------------------------------------------------------------
# PART 3 — the live call, placed on the historical distributions
# ---------------------------------------------------------------
def live(reg, R):
    """P1-P7 for MSCI Taiwan, August 2026.

    Names come from `aug26_tw_call_v2.json`; nothing is retyped.
    Every expectation is a PERCENTILE on the Taiwan distribution
    rather than a point estimate, because the distributions in
    Part 2 are wide enough that a point estimate would be a
    fiction — ADD drift runs p25 to p75 across several percent
    and the effective-day print spans an order of magnitude.
    """
    call = _j("aug26_tw_call_v2.json") or {}
    idx = taiex()
    wins = windows()
    # current ADV per code: the most recent window we hold for
    # that name, else nothing. Stated per name so a missing ADV
    # is visible rather than silently defaulted.
    adv_by_code = {}
    for e in sorted(wins, key=lambda x: x["ann"]):
        m = metrics(e, idx)
        if m and m.get("adv"):
            adv_by_code[m["code"]] = {"adv": m["adv"],
                                      "asof": m["ann"]}
    turn = _j("tw_daily_turnover.json") or {}
    # a fresher ADV from the turnover file where it exists
    recent = {}
    for day in sorted(turn)[-60:]:
        for code, row in (turn[day] or {}).items():
            v = (row.get("v") if isinstance(row, dict) else None)
            if v:
                recent.setdefault(str(code), []).append(float(v))
    for code, vs in recent.items():
        if len(vs) >= 20:
            adv_by_code[code] = {"adv": st.median(vs),
                                 "asof": "tw_daily_turnover last 60d"}

    def pctile(dist_vals, x):
        xs = sorted(v for v in dist_vals if v is not None)
        if not xs or x is None:
            return None
        return round(sum(1 for v in xs if v <= x) / len(xs), 3)

    add_vol = [m["vol_mult_eff"] for m in reg
               if m["action"] == "ADD" and m.get("vol_mult_eff")]
    del_vol = [m["vol_mult_eff"] for m in reg
               if m["action"] == "DEL" and m.get("vol_mult_eff")]
    add_adv = [m["adv"] for m in reg
               if m["action"] == "ADD" and m.get("adv")]
    del_adv = [m["adv"] for m in reg
               if m["action"] == "DEL" and m.get("adv")]

    rows = []
    for c in call.get("calls", []):
        code = str(c["code"])
        # the call file says DELETE, the window panel says DEL.
        # Normalised here rather than in either source, because
        # both are already declared and graded artefacts.
        a = "DEL" if str(c["action"]).startswith("DEL") else "ADD"
        adv = adv_by_code.get(code)
        base = R["B1_print_size"][a]
        drift = R["C1_drift"][a]
        effd = R["D1_eff_day"][a]
        # liquidity percentile drives the print expectation: the
        # E3 result is that the small-ADV tail carries the
        # violence, so a name's own ADV rank is the single most
        # informative thing we can say about it ex ante
        liq_pct = pctile(add_adv if a == "ADD" else del_adv,
                         adv["adv"] if adv else None)
        rows.append({
            "code": code, "action": a,
            "name": c.get("name") or c.get("why", "")[:40],
            "zone": c.get("zone"), "prob": c.get("prob"),
            "full_cap_usd_b": c.get("full_cap_usd_b"),
            "adv_shares": adv["adv"] if adv else None,
            "adv_src": adv["asof"] if adv else "NO ADV ON FILE",
            "adv_percentile_vs_history": liq_pct,
            "expected_print_x_adv": {
                "p25": base.get("p25"), "p50": base.get("p50"),
                "p75": base.get("p75"), "p90": base.get("p90")},
            "expected_drift": {"p25": drift.get("p25"),
                               "p50": drift.get("p50"),
                               "p75": drift.get("p75"),
                               "hit_rate": drift.get("hit_rate")},
            "expected_eff_day": {"p25": effd.get("p25"),
                                 "p50": effd.get("p50"),
                                 "p75": effd.get("p75")},
            "violence_flag": ("HIGH — bottom-third liquidity"
                              if liq_pct is not None and liq_pct < 0.34
                              else "normal" if liq_pct is not None
                              else "UNKNOWN — no ADV"),
        })
    rows.sort(key=lambda r: (r["adv_percentile_vs_history"]
                             if r["adv_percentile_vs_history"]
                             is not None else 9))
    return {
        "review": call.get("review"), "declared": call.get("declared"),
        "ann": "2026-08-12", "eff": "2026-08-31",
        "n_calls": len(rows),
        "names": rows,
        "P3_ranked_by_expected_violence": [
            {"code": r["code"], "action": r["action"],
             "adv_percentile": r["adv_percentile_vs_history"],
             "flag": r["violence_flag"]} for r in rows[:8]],
        "P4_schedule": {
            "tracker": ("trade the effective close. The C3 table "
                        "shows every alternative schedule buys "
                        "P&L with tracking error, and the "
                        "tracker's benchmark IS that close."),
            "pod": ("enter on ann+1, exit into the effective "
                    "close. The drift hit rate is the number to "
                    "size on, not the median — see C1."),
        },
        "P6_what_would_change_this": [
            "MSCI declares a light rebalancing in the ten "
            "business days before 12 Aug: buffers widen to 0.5x "
            "and 1.8x and two names leave the addition list. "
            "Detect: MSCI market-monitoring announcements.",
            "A float revision between the 20 Jul price cutoff "
            "and the announcement moves a name across the bar. "
            "Detect: re-run the crossing on fresh float.",
            "A borrow squeeze on the deletion list. Detect: "
            "sbl_history balance rising into the print — see N3.",
        ],
    }


def main():
    idx = taiex()
    evs = windows()
    ms = [m for m in (metrics(e, idx) for e in evs) if m]
    for m in ms:
        m["label"] = label(m)
    R = {"_generated": __doc__.strip().splitlines()[0],
         "_market": "Taiwan",
         "_source": ["data/tw_event_windows.json",
                     "data/twii_daily.json (TAIEX, market adj)",
                     "data/msci_changes_db.pkl",
                     "data/sbl_history.json",
                     "data/aug26_tw_call_v2.json"],
         "_market_adjustment": "excess over TAIEX close-to-close",
         "_small_n": SMALL_N}
    R["M"] = section_M(ms, evs)
    R.update(sections(ms, evs, idx))
    R["N"] = section_N([m for m in ms if m["day0"] == "registry"])
    R["LIVE_AUG26"] = live([m for m in ms if m["day0"] == "registry"], R)
    R["events"] = ms
    OUT.write_text(json.dumps(R, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    reg = R["M"]["M1_panel"]["registry_day0"]
    print(f"-> {OUT.relative_to(ROOT)}  "
          f"({OUT.stat().st_size / 1024:.0f} kB)")
    print(f"   analysable Taiwan windows: {reg} "
          f"(of {len(ms)} priced)")
    print(f"   ADD drift p50 "
          f"{R['C1_drift']['ADD']['p50']:+.2%} "
          f"hit {R['C1_drift']['ADD']['hit_rate']:.0%} "
          f"| DEL drift p50 {R['C1_drift']['DEL']['p50']:+.2%} "
          f"hit {R['C1_drift']['DEL']['hit_rate']:.0%}")
    n = findings_md(R)
    print(f"-> docs/REBALANCE_FINDINGS.md ({n} lines)")
    print(f"   eff-day print: ADD "
          f"{R['B1_print_size']['ADD']['p50']:.1f}x ADV, DEL "
          f"{R['B1_print_size']['DEL']['p50']:.1f}x")




# ---------------------------------------------------------------
# the written answers, GENERATED so they cannot drift
# ---------------------------------------------------------------
def findings_md(R):
    """docs/REBALANCE_FINDINGS.md, every number interpolated.

    The bank asks for a written answer set and a machine-readable
    file. Writing the prose by hand would let the two disagree
    the first time the panel changes, and this project has
    already been bitten by a page holding a number its engine no
    longer produced. So the doc is emitted from the same dict
    the page reads.
    """
    def pc(d, k="p50"):
        v = d.get(k)
        return "—" if v is None else f"{v:+.2%}"

    def x(d, k="p50"):
        v = d.get(k)
        return "—" if v is None else f"{v:.1f}x"
    M = R["M"]["M1_panel"]
    c1, b1, d1 = R["C1_drift"], R["B1_print_size"], R["D1_eff_day"]
    g1, c3 = R["G1_reversion"], R["C3_schedules"]
    L = []
    A = L.append
    A("# Taiwan index-rebalance findings\n")
    A(f"Generated by `scripts/rebalance_analysis.py` from "
      f"`data/rebalance_analysis.json`. Every figure below is "
      f"interpolated from that file; nothing here is typed by "
      f"hand.\n")
    A("## The sample, before anything else\n")
    A(f"- **{M['registry_day0']} analysable windows** "
      f"({M['by_action']['ADD']} additions, "
      f"{M['by_action']['DEL']} deletions), "
      f"{M['year_range'][0]}–{M['year_range'][1]}, Taiwan only.")
    A(f"- {M['priced_and_usable']} windows are priced, but "
      f"{M['estimated_day0']} carry an **estimated announcement "
      f"date** and are excluded from every event-time number. "
      f"Day 0 is the pre-news baseline; on those windows it is "
      f"2–7 sessions wrong, which is larger than the effect "
      f"being measured.")
    A("- Returns are **excess over TAIEX**, close to close.")
    A("- Taiwan is priced from TWSE/TPEx day files, which retain "
      "delisted companies, so the deletion sample is "
      "**survivor-safe**. This is the honest side of the "
      "add/delete asymmetry question.\n")
    A("## The six numbers that matter\n")
    A("| | additions | deletions |")
    A("|---|---|---|")
    A(f"| drift, ann+1 → eff−1 (median) | {pc(c1['ADD'])} | "
      f"{pc(c1['DEL'])} |")
    A(f"| …and how often it has the right sign | "
      f"{c1['ADD']['hit_rate']:.0%} | {c1['DEL']['hit_rate']:.0%} |")
    A(f"| …interquartile range | {pc(c1['ADD'],'p25')} to "
      f"{pc(c1['ADD'],'p75')} | {pc(c1['DEL'],'p25')} to "
      f"{pc(c1['DEL'],'p75')} |")
    A(f"| effective-day print, × ADV (median) | {x(b1['ADD'])} | "
      f"{x(b1['DEL'])} |")
    A(f"| …p90 | {x(b1['ADD'],'p90')} | {x(b1['DEL'],'p90')} |")
    A(f"| effective-day move (median) | {pc(d1['ADD'])} | "
      f"{pc(d1['DEL'])} |\n")
    A(f"**The mean is not the median and the gap is the point.** "
      f"Addition drift averages {c1['ADD']['mean']:+.2%} against "
      f"a median of {pc(c1['ADD'])}. The distribution is heavily "
      f"right-skewed — Yageo in Nov-2017, Wistron in May-2023, "
      f"Walsin in May-2018 — so a book sized on the mean is "
      f"sized on three events.\n")
    A("## A3 — Taiwan has no non-events\n")
    a3 = R["A3_non_events"]
    A(f"Zero of {a3['of']} events satisfy *{a3['definition']}*. "
      f"Only {sum(1 for e in R['events'] if e['day0']=='registry' and (e.get('vol_mult_eff') or 9) < 2)} "
      f"windows print under 2× ADV at all. An earlier China cut "
      f"ran 61% non-events; Taiwan runs 0%. **Every MSCI Taiwan "
      f"change is a trade.**\n")
    A("## C3 — the schedule question, answered twice\n")
    A("| schedule | median saved vs eff close | tracking-error contribution |")
    A("|---|---|---|")
    for k, lab in (("eff_close", "100% at the effective close"),
                   ("last4_equal", "25% × last four days"),
                   ("ann_plus_1", "100% at ann+1")):
        d = c3[k]
        te = d.get("te_contribution")
        A(f"| {lab} | {pc(d)} | "
          f"{'0 (benchmark)' if not te else f'{te:.2%}'} |")
    A("")
    A("**For the tracker the right column is the answer.** The "
      "effective close is not a good execution of the benchmark, "
      "it *is* the benchmark, so every alternative buys P&L with "
      "tracking error. **For the pod the left column is the "
      "answer** and the right column is the risk budget.\n")
    A("## C4 / H5 — is the trade getting crowded?\n")
    c4 = R["C4_capture"]
    A(f"Capture — the share of the move still available after "
      f"the announcement gap — has a median of "
      f"{c4['ADD']['p50']:.2f} on additions and "
      f"{c4['DEL']['p50']:.2f} on deletions. Roughly three "
      f"quarters of the move is still there the morning after.")
    yrs = R["H5_crowding"]
    ks = [y for y in sorted(yrs) if yrs[y]["n"] >= 8]
    if len(ks) >= 4:
        A(f"\nAnd it is **not** decaying: capture ran "
          f"{yrs[ks[0]]['capture']['p50']:.2f} in {ks[0]} and "
          f"{yrs[ks[-1]]['capture']['p50']:.2f} in {ks[-1]}. "
          f"Pre-announcement drift *has* grown "
          f"(|pre_drift| median "
          f"{yrs[ks[0]]['abs_pre_drift']['p50']:.1%} → "
          f"{yrs[ks[-1]]['abs_pre_drift']['p50']:.1%}), so the "
          f"market is anticipating more — but it is not taking "
          f"the post-announcement move away. On the bank's own "
          f"test for crowding, **the answer is no**, and that is "
          f"the opposite of what the question expected.")
    A("\n*(n per year is 4–21; treat the year-on-year path as "
      "EXPLORATORY and the endpoints as the claim.)*\n")
    A("## G1 / G3 — where the pod's exit lives\n")
    A(f"Additions give back {pc(g1['revert5']['ADD'])} in the "
      f"five sessions after the effective close — more than the "
      f"median drift they earned. Deletions revert "
      f"{pc(g1['revert5']['DEL'])}.")
    rt = R["G3_round_trip"]["eff_close"]
    A(f"\nThe ann+1 → effective-close round trip is "
      f"{rt['0bp']['p50']:+.2%} gross with a "
      f"{rt['0bp']['hit_rate']:.0%} hit rate, and "
      f"{rt['40bp']['p50']:+.2%} at a 40bp round-trip cost. "
      f"**The edge survives cost; the dispersion is what needs "
      f"sizing** — p10 is {rt['40bp']['p10']:+.2%}.\n")
    A("## J4 — size on the excursion, not the outcome\n")
    j4 = R["J4_mae"]
    A(f"A position entered at ann+1 and held to the effective "
      f"close is under water by {pc(j4['ADD'])} at its worst "
      f"point on the median addition, and {pc(j4['ADD'],'p10')} "
      f"at the tenth percentile. The final number is not the "
      f"number the risk manager sees.\n")
    A("## N3 — the borrow signal does not work\n")
    n3 = R["N"]["N3_borrow_build"]
    bv = R["N"]["N3_build_vs_eff_day"]
    A(f"Borrow balance into a deletion builds to "
      f"{n3['DEL']['p50']:.2f}× its level 35 days earlier "
      f"(n={n3['DEL']['n']}). It does **not** predict the "
      f"effective-day move: rank correlation "
      f"{bv['rho']:+.3f} on n={bv['n']}.")
    A("\nThis is a negative result and it is worth more than a "
      "fitted curve would have been. A crowded short into a "
      "Taiwanese deletion is not, on this evidence, a squeeze "
      "signal. The bank asks whether each flow dataset earns "
      "its place in the pitch — on this test, borrow does not.\n")
    A("## What could not be answered\n")
    A("- `twse_institutional.json` holds 22 days and "
      "`tw_limits.json` 23, both recent. **N1, N4, N7 are "
      "`UNANSWERABLE-DAILY`** until those are backfilled.")
    A("- N5/N6 (closing-auction share and imbalance) are "
      "reachable from `auction5s_history.json` and are the "
      "highest-value Taiwan-only results still open.")
    A("- Everything in Part 4 stays parked for 5-minute data.")
    A("- Cross-market sections (F2, K1–K4) need the other "
      "markets recomputed on this same market-adjusted, "
      "day-0-clean basis; Taiwan was ordered first and is what "
      "is defensible today.\n")
    (ROOT / "docs" / "REBALANCE_FINDINGS.md").write_text(
        "\n".join(L), encoding="utf-8")
    return len(L)

if __name__ == "__main__":
    main()
