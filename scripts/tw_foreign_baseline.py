#!/usr/bin/env python3
"""Foreign net buying through the rebalance window, vs normal.

    py scripts\\tw_foreign_baseline.py

THE QUESTION, c-357 (Bill): *"the amount of daily net buying by
foreign per stock for stocks that are part of index changes, on
the effective date, and how this stat differs from other normal
times"* — and, if possible, the whole window: before the
announcement, after the effective date.

WHAT ALREADY EXISTED, AND WHAT WAS MISSING. The addition study
already measures foreign flow per event in four phases — before
the announcement (its stored window is 20 sessions; c-368
recomputes this phase at 30 sessions from the raw file),
announcement to effective, the effective day itself, and the 10
sessions after — all in units of that name's own ADV. What it never had is the thing that
makes those numbers READABLE: a baseline. "+0.16x ADV on the
effective day" means nothing until you know what the same stock
draws on an ordinary Tuesday.

This file builds that baseline from the raw T86 harvest — 3,024
sessions of per-stock, per-day foreign net buying, 2015-2026 —
and re-expresses every phase as a multiple of the same stock's
own normal day.

────────────────────────────────────────────────────────────────
DESIGN DECISIONS, each of which moves the answer

1. THE BASELINE IS PER-STOCK AND PRE-EVENT. For each event, the
   baseline window is the 100 sessions ENDING 31 sessions before
   the announcement — clear of the event's own pre-drift window,
   and matched to the same regime rather than to a pooled
   all-history average. A stock's normal foreign traffic in 2016
   is not evidence about its normal traffic in 2025.

2. NORMAL IS |NET|, NOT NET. Signed daily foreign net on
   ordinary days medians to ~zero by construction — foreigners
   buy one day and sell the next. The scale of a normal day is
   the median ABSOLUTE net over ADV; that is the yardstick the
   effective-day flow is divided by. Signed medians are kept in
   the output for anyone who wants the drift.

3. PHASES ARE CONVERTED TO PER-SESSION RATES before comparison.
   The pre window is 30 sessions (c-368; was 20) and the post
   window 10; the effective day is one. Comparing a multi-week
   cumulation to a single day flatters the cumulation by the
   window length. Rates make the four
   phases and the baseline the same unit: flow per session, in
   ADV.

4. COVERAGE IS DECLARED, NOT PAPERED OVER. The T86 harvest is a
   ~130-name watch list, not the whole market, so an event's
   baseline exists only when its stock is covered on >=60 of the
   100 baseline sessions. Events failing that are counted and
   named in the output rather than silently pooled.

────────────────────────────────────────────────────────────────
WHAT THE NUMBERS SAY (values move with a re-harvest; the shape
is the finding)

On a normal day, a covered name's foreign net lands around
2-4% of its ADV in absolute size. On the effective day of its
OWN index event the median addition draws ~5-8x that; the median
deletion prints a multiple of that again on the sell side. The
pre-announcement and announcement-to-effective phases run
1-2x normal per session — elevated, but an order of magnitude
below the print. The flow is not smeared; it lands on the day
the benchmark moves, which is the same conclusion the volume
work reached from a different file.

WHAT THIS CANNOT SAY. T86 nets all foreign accounts to one
number — a tracker buying from a foreign hedge fund selling nets
toward zero, so the effective-day multiple UNDERSTATES gross
index demand. And the watch-list coverage means small adds are
under-represented; the coverage counts in the output say by how
much.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import statistics as stats

ROOT = pathlib.Path(__file__).resolve().parents[1]
T86 = ROOT / "data" / "t86_history.json"
STUDY = ROOT / "data" / "tw_addition_study.json"
OUT = ROOT / "data" / "tw_foreign_baseline.json"
DOC = ROOT / "docs" / "TW_FOREIGN_BASELINE.md"

BASE_SESSIONS = 100     # baseline window length
PRE_SESSIONS = 30       # c-368, Bill: pre phase widened from the
#                         study's 20 sessions to 30. The study's
#                         stored `foreign_pre_adv` is a 20-session
#                         sum, so the pre rate is RECOMPUTED here
#                         from the raw T86 file over the 30
#                         sessions before the announcement.
GAP_SESSIONS = PRE_SESSIONS + 1   # baseline ends clear of the
#                                   pre window (31 before ann)
MIN_COVER = 60          # baseline must cover at least this many


def _dist(xs):
    if not xs:
        return None
    xs = sorted(xs)

    def q(p):
        i = (len(xs) - 1) * p
        lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
        return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)
    return {"n": len(xs), "p10": q(.10), "p25": q(.25),
            "p50": q(.50), "p75": q(.75), "p90": q(.90),
            "mean": stats.fmean(xs)}


def main():
    for p in (T86, STUDY):
        if not p.exists():
            raise SystemExit(f"missing {p.name}")
    t86 = json.loads(T86.read_text(encoding="utf-8"))
    study = json.loads(STUDY.read_text(encoding="utf-8"))
    dates = sorted(t86)

    rows, skipped = [], {"no_flow_fields": 0, "thin_baseline": []}
    for e in study["events"]:
        if e.get("foreign_eff_adv") is None or not e.get("adv"):
            skipped["no_flow_fields"] += 1
            continue
        code = str(e["code"])
        ann = e["ann"].replace("-", "")
        # the baseline window: 100 sessions ending GAP_SESSIONS before ann
        before = [d for d in dates if d < ann]
        win = before[-(BASE_SESSIONS + GAP_SESSIONS):-GAP_SESSIONS] \
            if len(before) > BASE_SESSIONS + GAP_SESSIONS else []
        f = [t86[d][code]["f"] / e["adv"] for d in win
             if code in t86[d]]
        if len(f) < MIN_COVER:
            skipped["thin_baseline"].append(
                {"key": e["key"], "covered": len(f)})
            continue
        base_abs = stats.median(abs(x) for x in f)
        base_signed = stats.median(f)
        sess_mid = max(1, e.get("sessions_ann_to_eff") or 1)
        # c-368: the pre rate over the 30 T86 sessions before
        # the announcement, from the raw file — a true
        # per-session rate over the covered days, so a coverage
        # gap thins the sample instead of diluting the rate
        pre_win = before[-PRE_SESSIONS:]
        pre_f = [t86[d][code]["f"] / e["adv"] for d in pre_win
                 if code in t86[d]
                 and t86[d][code] and t86[d][code]["f"] is not None]
        r = {"key": e["key"], "code": code, "action": e["action"],
             "rev": e["rev"], "eff": e["eff"],
             "baseline_days": len(f),
             "baseline_abs_adv": round(base_abs, 5),
             "baseline_signed_adv": round(base_signed, 5),
             # per-session rates, all in ADV units
             "rate_pre": (sum(pre_f) / len(pre_f)) if pre_f
             else e["foreign_pre_adv"] / 20,
             "pre_sessions_covered": len(pre_f),
             "rate_mid": e["foreign_mid_adv"] / sess_mid,
             "rate_eff": e["foreign_eff_adv"],
             "rate_post": e["foreign_post_adv"] / 10,
             }
        # the headline: each phase as a multiple of the stock's
        # own normal day (absolute scale)
        for ph in ("pre", "mid", "eff", "post"):
            r[f"x_normal_{ph}"] = round(
                r[f"rate_{ph}"] / base_abs, 3) if base_abs else None
        rows.append(r)

    out = {"_what": "foreign net buying by phase of the rebalance "
                    "window, as a multiple of the same stock's own "
                    "normal day",
           "generated": dt.datetime.now().isoformat(timespec="seconds"),
           "method": {
               "baseline": f"median |daily foreign net| / ADV over "
                           f"the {BASE_SESSIONS} sessions ending "
                           f"{GAP_SESSIONS} before the announcement, "
                           f"per stock, requiring >= {MIN_COVER} "
                           f"covered sessions",
               "phases_per_session": f"pre = mean over covered "
                                     f"T86 sessions of the "
                                     f"{PRE_SESSIONS} before ann "
                                     f"(c-368), ann-to-eff "
                                     f"/sessions, effective day "
                                     f"/1, post /10",
               "netting_caveat": "T86 nets ALL foreign accounts to "
                                 "one number, so tracker buying "
                                 "netted against foreign selling "
                                 "UNDERSTATES gross index demand"},
           "coverage": {"events_used": len(rows),
                        "skipped": skipped},
           "sides": {}}
    for side in ("ADD", "DEL"):
        g = [r for r in rows if r["action"] == side]
        out["sides"][side] = {
            "n": len(g),
            "baseline_abs_adv": _dist(
                [r["baseline_abs_adv"] for r in g]),
            "rates_adv": {ph: _dist([r[f"rate_{ph}"] for r in g])
                          for ph in ("pre", "mid", "eff", "post")},
            "x_normal": {ph: _dist(
                [r[f"x_normal_{ph}"] for r in g
                 if r[f"x_normal_{ph}"] is not None])
                for ph in ("pre", "mid", "eff", "post")},
        }
    out["events"] = rows
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")

    d = ["# Foreign Flow vs a Normal Day", "",
         f"Generated {out['generated']} by "
         "`scripts/tw_foreign_baseline.py`.", "",
         f"Events used: {len(rows)} "
         f"(skipped {skipped['no_flow_fields']} without flow "
         f"fields, {len(skipped['thin_baseline'])} with thin "
         "baselines).", "",
         "| Side | Phase | median flow/session (ADV) | "
         "x a normal day |",
         "| --- | --- | ---: | ---: |"]
    for side in ("ADD", "DEL"):
        s_ = out["sides"][side]
        for ph, lab in (("pre", f"{PRE_SESSIONS} sessions "
                                f"before ann"),
                        ("mid", "announcement to effective"),
                        ("eff", "the effective day"),
                        ("post", "10 sessions after")):
            r_ = s_["rates_adv"][ph]
            x_ = s_["x_normal"][ph]
            d.append(f"| {side} | {lab} | {r_['p50']:+.3f} | "
                     f"{x_['p50']:+.1f}x |")
        d.append(f"| {side} | *normal day, absolute scale* | "
                 f"{s_['baseline_abs_adv']['p50']:.3f} | 1.0x |")
    d += ["",
          "Phases are per-session rates, so the four rows and "
          "the baseline share one unit. The T86 netting caveat "
          "applies: gross index demand is larger than any of "
          "these numbers.", ""]
    DOC.write_text("\n".join(d), encoding="utf-8")

    for side in ("ADD", "DEL"):
        s_ = out["sides"][side]
        print(f"{side}  n={s_['n']:3}  normal "
              f"{s_['baseline_abs_adv']['p50']:.3f} ADV/day   "
              + "  ".join(
                  f"{ph}={s_['x_normal'][ph]['p50']:+.1f}x"
                  for ph in ("pre", "mid", "eff", "post")))
    print(f"wrote {OUT.name}, {DOC.name}")


if __name__ == "__main__":
    main()
