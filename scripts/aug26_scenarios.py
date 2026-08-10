#!/usr/bin/env python3
"""What the four called Taiwan additions do, IF MSCI adds them.

    py scripts\\aug26_scenarios.py

THE CONDITIONAL IS THE WHOLE FRAME. This file assumes the
addition happens and asks only what the price and the print do
afterwards. Whether MSCI actually adds them is the walkthrough's
question and it is carried separately, at 62/62/62/37 per cent.
Multiplying the two is the reader's job and the file says so
rather than doing it silently.

WHAT IS FORECAST AND WHAT IS NOT.

  FORECAST, with a name-level adjustment:
    the effective-day print in days of ADV. Two drivers survive
    Bonferroni correction on 100 tests — pre-event volatility and
    ADV, both NEGATIVE against the print multiple — so an
    illiquid, quiet name prints a bigger multiple of its own ADV.
    That is a real, measured, cross-sectional relationship.

  NOT FORECAST, and deliberately left unconditional:
    the drift and the reversion. The out-of-sample test in
    tw_addition_study.py fits six rules on 34 pre-2023 additions
    and scores them on 18 post-2023 ones. The best is the
    announcement gap at +0.30 lift — and it selects 7 events,
    carries a binomial p of 0.108, and is the maximum of six
    draws. Nothing survives. So every price scenario below is the
    UNCONDITIONAL historical distribution, positioned by
    percentile, and any per-name differentiation on price would
    be invention.

THE ONE THING THAT IS GENUINELY UNUSUAL ABOUT THIS REVIEW, and
it is not in the base rates. A typical Taiwanese addition arrives
having already risen: pre-announcement excess drift runs +6.96%
at the median and is positive 73% of the time. These four have
run -5% to -34% over the same 25-session lookback. Three of the
four sit below the 10th percentile of the historical
distribution. The panel has almost no precedent for adding names
after a fall of this size, so the base rates are being applied to
a setup the sample barely contains — which is stated here as a
limit on the forecast rather than smoothed into it.

THE PRICE DATA STOPS BEFORE THE ANNOUNCEMENT. The last close we
hold is 2026-07-31; MSCI announces on 2026-08-12. Eight sessions
of run-in are invisible, and the run-in is exactly where the
pre-announcement drift would show up. Every pre-drift figure
below therefore ENDS EIGHT SESSIONS EARLY and cannot be the last
word on positioning.
"""
from __future__ import annotations

import datetime as dt
import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "aug26_scenarios.json"
EXPECTED = ROOT / "data" / "aug26_expected_outcomes.json"

# The index's own free-float value, from the MSCI Taiwan
# factsheet that the walkthrough's cutoff derivation already
# uses. Weight = a name's float cap over this.
INDEX_FLOAT_USD_B = 3183.0
# Tracking AUM.
#
# c-327 CORRECTION TO MY OWN COMMENT. This used to say "the
# registered figure", which overstates it. Traced: the number
# originates in scripts/event_window_analyze.py as
# `TRACKING_AUM_USD_B = 180.0  # MSCI TW passive proxy`, a
# hand-set constant. The question bank then refers to "the
# registered $180bn" — but that is the bank describing what this
# project already used, not an external source. The citation is
# circular and there is no measurement behind it.
#
# c-329 SOURCING ATTEMPT, and the label is the real error.
# Bill asked whether the figure can be sourced. It cannot, as
# written — full working in docs/TRACKING_AUM_PROVENANCE.md.
# MSCI publishes no AUM at country or index level anywhere
# public. Bottom-up, every ETF on an MSCI Taiwan index totals
# about USD 13bn (EWT USD 11.2bn on the 25/50 variant plus small
# UCITS and TW-domiciled funds); the UNCAPPED standard index this
# project's weights are struck on carries about USD 0.08bn.
#
# So 180 is not "assets tracking MSCI Taiwan". What it is a
# plausible midpoint for is INDEXED TAIWAN EXPOSURE ACROSS ALL
# MSCI INDEXES — Taiwan is 26.63% of MSCI EM (31 Jul 2026, now
# the largest country weight) and IEMG plus EEM alone hold about
# USD 52bn of Taiwan, before EIMI and every non-US EM tracker.
# That is the money that actually has to buy a new MSCI Taiwan
# constituent, so the quantity is right and the name on it was
# wrong.
#
# NOT re-set here on purpose. Changing the number and the label
# in one commit would make the sensitivity below incomparable
# with every result already written up.
#
# It is DECLARED rather than derived, and it is the only input in
# this file of which that is true. What defends it is not
# provenance but two things downstream:
#   1. the 0.5x/1x/2x sensitivity below, which shows it moves the
#      LEVEL and not the ranking;
#   2. the independent check in `demand_validation` — foreign net
#      buying measured from TWSE day files put historical
#      additions at 1.04 ADV days against the 0.8-1.3 this model
#      produces, and that measurement shares neither the AUM nor
#      the index-value assumption.
# Replacing it with a sourced figure is a real improvement and
# nobody should mistake it for one that has been made.
AUM_USD_B = 180.0
AUM_SENSITIVITY = (0.5, 1.0, 2.0)

ANNOUNCE = "2026-08-12"
EFFECTIVE = "2026-08-31"


def _j(name):
    p = ROOT / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def percentile_of(value, sample):
    """Where `value` falls in `sample`, 0..1. None if unusable."""
    xs = sorted(x for x in sample if x is not None and x == x)
    if not xs or value is None:
        return None
    below = sum(1 for x in xs if x < value)
    return below / len(xs)


def band_from(dist, sgn=1):
    """Turn a described distribution into five labelled outcomes.

    The bands are percentile buckets of the SAME distribution the
    study measured, so the probabilities are frequencies rather
    than opinions: p10-p25 happened 15% of the time because that
    is what a percentile is. What a reader may disagree with is
    whether this review resembles the sample — which is the point
    the docstring above makes and this function cannot fix.
    """
    return [
        {"band": "bear tail", "prob": 0.10,
         "at_or_below": dist.get("p10")},
        {"band": "bear", "prob": 0.15,
         "from": dist.get("p10"), "to": dist.get("p25")},
        {"band": "base", "prob": 0.50,
         "from": dist.get("p25"), "to": dist.get("p75"),
         "median": dist.get("p50")},
        {"band": "bull", "prob": 0.15,
         "from": dist.get("p75"), "to": dist.get("p90")},
        {"band": "bull tail", "prob": 0.10,
         "at_or_above": dist.get("p90")},
    ]


def main():
    study = _j("tw_addition_study.json")
    if not study:
        raise SystemExit("run scripts/tw_addition_study.py first")
    call = _j("aug26_tw_call_v2.json") or {}
    # c-322: the ±5% band the pages carry on the derived cutoff.
    # Emitted here so a page never has to re-derive a threshold
    # it is only displaying — the frame lives in one file.
    BAND = 0.05
    bar = float(call.get("addition_bar_usd_b") or 0)
    floor_ = float(call.get("incumbent_floor_usd_b") or 0)
    uni = (_j("tw_mieu_universe.json") or {}).get("universe") or {}
    vint = _j("tw_vintage_cache.json") or {}
    twii = {k: float(v) for k, v in (_j("twii_daily.json") or {}).items()
            if v == v}
    names = _j("yahoo_names.json") or {}
    fx = _j("fx_twd_history.json") or {}
    screen = _j("tw_extreme_price_screen.json") or {}

    add = [r for r in study["events"] if r["action"] == "ADD"]
    A = study["anatomy"]["ADD"]

    # USD/TWD at the most recent date we hold
    rate = None
    if isinstance(fx, dict) and fx:
        k = max(fx)
        try:
            rate = float(fx[k])
        except Exception:                            # noqa: BLE001
            rate = None
    rate = rate or 30.0

    rows = {}
    for c in call.get("calls", []):
        if c.get("action") != "ADD":
            continue
        code = str(c["code"])
        u = uni.get(code) or {}
        px = [(x["date"], float(x["close"]), float(x.get(
            "Trading_Volume") or 0))
            for x in (vint.get(f"px|{code}") or [])
            if x.get("close")]
        if not px:
            continue
        px.sort()
        dates = [x[0] for x in px]
        last = px[-1]
        adv = st.median([x[2] for x in px[-21:-1] if x[2]])
        # 25-session excess over TAIEX, the same lookback the
        # study uses for pre_drift
        j = max(0, len(px) - 26)
        pre = None
        if twii.get(dates[-1]) and twii.get(dates[j]):
            pre = ((last[1] / px[j][1] - 1)
                   - (twii[dates[-1]] / twii[dates[j]] - 1))
        prevol = st.pstdev([px[k + 1][1] / px[k][1] - 1
                            for k in range(len(px) - 22, len(px) - 2)])

        weight = (u.get("fcap") or 0) / INDEX_FLOAT_USD_B
        demand_usd_b = weight * AUM_USD_B
        demand_shares = (demand_usd_b * 1e9 * rate) / last[1]
        demand_days = demand_shares / adv if adv else None

        # PRINT SIZE, the one forecast with a name-level lean.
        # Both surviving drivers point the same way — quiet and
        # illiquid prints bigger — so the name is positioned by
        # its percentile on each and the two are averaged. This is
        # a rank statement, not a fitted line: the study measured
        # rho, not a slope, and a slope would be claiming more
        # than was tested.
        p_vol = percentile_of(prevol, [r["prevol"] for r in add])
        p_adv = percentile_of(adv, [r["adv"] for r in add])
        lean = None
        if p_vol is not None and p_adv is not None:
            # both correlate NEGATIVELY with the print multiple,
            # so a high percentile on either means a smaller print
            lean = 1.0 - st.mean([p_vol, p_adv])
        vm = A["vol_mult_eff"]
        print_expect = None
        if lean is not None:
            lo, mid, hi = vm["p25"], vm["p50"], vm["p75"]
            print_expect = (lo + (hi - lo) * lean if lean <= 1 else hi)

        cap_now = u.get("cap")
        rows[code] = {
            # CARRIED = the verdict survives the band. A name that
            # clears the addition bar by less than the band is
            # reported but not stood behind, and the page's
            # headline table shows only the carried ones.
            "carried": bool(cap_now and bar
                            and cap_now >= bar * (1 + BAND)),
            "clears_bar_by": ((cap_now / bar - 1)
                              if cap_now and bar else None),
            "name": (names.get(f"{code}.TW")
                     or names.get(f"{code}.TWO") or ""),
            "prob_of_addition": c.get("prob"),
            "zone": c.get("zone"),
            "last_close_twd": last[1],
            "last_close_date": last[0],
            "adv_shares": adv,
            "full_cap_usd_b": u.get("cap"),
            "float_cap_usd_b": u.get("fcap"),
            "fif": u.get("ff"),
            "fif_source": u.get("src"),
            "index_weight_pct": weight * 100,
            "demand_usd_m": demand_usd_b * 1000,
            "demand_shares": demand_shares,
            "demand_adv_days": demand_days,
            "demand_sensitivity": {
                f"{m:g}x": (demand_shares * m / adv) if adv else None
                for m in AUM_SENSITIVITY},
            "pre_ann_excess_25d": pre,
            "pre_ann_percentile": percentile_of(
                pre, [r["pre_drift"] for r in add]),
            "prevol": prevol,
            "prevol_percentile": p_vol,
            "adv_percentile": p_adv,
            "print_lean": lean,
            "expected_print_x_adv": print_expect,
            "extreme_price_screen": (
                (screen.get("names") or {}).get(code, {}).get("verdict")),
        }

    # rank by how violent the history says each will be
    ranked = sorted(rows.items(),
                    key=lambda kv: -(kv[1]["expected_print_x_adv"] or 0))
    for i, (code, r) in enumerate(ranked, 1):
        r["violence_rank"] = i

    out = {
        "_what": "Aug-2026 MSCI Taiwan additions — conditional "
                 "scenarios given inclusion",
        "conditional_on": "MSCI adding the name; the probability "
                          "of that is carried separately per name "
                          "and is NOT multiplied in here",
        "generated": dt.date.today().isoformat(),
        "announce": ANNOUNCE, "effective": EFFECTIVE,
        "thresholds": {
            "cutoff_usd_b": call.get("cutoff_usd_b"),
            "addition_bar_usd_b": bar,
            "incumbent_floor_usd_b": floor_,
            "band": BAND,
            "why": "the cutoff is derived from an 85% coverage "
                   "walk over an estimated float stack, not "
                   "published by MSCI, so every threshold carries "
                   "a +-5% band and a verdict that flips inside "
                   "it is reported rather than carried"},
        "assumptions": {
            "index_float_value_usd_b": INDEX_FLOAT_USD_B,
            "tracking_aum_usd_b": AUM_USD_B,
            "usd_twd": rate,
            "price_data_ends": max(
                (r["last_close_date"] for r in rows.values()),
                default=None),
            "sessions_unobserved_before_announcement": 8},
        "history": {
            "n_additions": A["n"],
            "sample": study["sample"]["first_review"] + "-"
                      + study["sample"]["last_review"],
            "drift": A["drift"], "eff_day": A["eff_day"],
            "revert5": A["revert5"], "revert20": A["revert20"],
            "vol_mult_eff": A["vol_mult_eff"],
            "pre_drift": A["pre_drift"],
            "max_drawdown_in_drift": A["max_drawdown_in_drift"]},
        "scenarios": {
            "announcement_to_effective": {
                "measure": "market-adjusted return, ann+1 close to "
                           "eff-1 close",
                "bands": band_from(A["drift"]),
                "right_sign_share": A["drift"].get("right_sign_share"),
                "worst_point_median": A["max_drawdown_in_drift"]["p50"],
                "worst_point_p10": A["max_drawdown_in_drift"]["p10"]},
            "effective_day": {
                "measure": "market-adjusted return, eff-1 close to "
                           "eff close",
                "bands": band_from(A["eff_day"]),
                "right_sign_share": A["eff_day"].get(
                    "right_sign_share")},
            "post_effective_5": {
                "measure": "market-adjusted return, eff close to +5",
                "bands": band_from(A["revert5"])},
            "post_effective_20": {
                "measure": "market-adjusted return, eff close to +20",
                "bands": band_from(A["revert20"])}},
        # THE DEMAND MODEL, CHECKED AGAINST SOMETHING IT DOES NOT
        # DEPEND ON. `demand_adv_days` is weight x AUM / ADV, and
        # both the index float value and the $180bn are
        # assumptions. The study measures, from TWSE institutional
        # day files, how much foreign stock ACTUALLY moved into a
        # historical addition between 20 sessions before the
        # announcement and the effective close. If the two land in
        # the same place the assumption set is doing no harm; if
        # they do not, the demand column is decoration.
        "demand_validation": {
            "model_range_adv_days": [
                min((r["demand_adv_days"] for r in rows.values()
                     if r["demand_adv_days"]), default=None),
                max((r["demand_adv_days"] for r in rows.values()
                     if r["demand_adv_days"]), default=None)],
            "measured_cumulative_adv_days":
                study["foreign_flow"]["ADD"]["cumulative_to_effective"],
            "note": "the measured figure is foreign net only and "
                    "covers ann-20 to the effective close; the "
                    "model figure is the passive requirement. They "
                    "are different quantities and agreement is "
                    "evidence the AUM assumption is the right "
                    "order of magnitude, not proof of its level."},
        "flow_context": study["foreign_flow"]["ADD"],
        "schedules": study["schedules"]["ADD"],
        "volume_normalises_sessions": study["volume_normalises"]["ADD"],
        "out_of_sample_verdict": study["out_of_sample"]["verdict"],
        "names": rows,
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")

    # ── PRE-REGISTRATION (P7) ───────────────────────────────────
    # Written BEFORE the print. A prediction that is not written
    # down before the event is not a prediction.
    exp = {"_what": "pre-registered expected outcomes, Aug-2026 "
                    "MSCI Taiwan additions",
           "registered": dt.date.today().isoformat(),
           "announce": ANNOUNCE, "effective": EFFECTIVE,
           "conditional_on": "the name is actually added",
           "grade_on": "1 September 2026, against "
                       "market-adjusted (TAIEX) returns",
           "method": "unconditional historical percentiles for "
                     "price; percentile-leaned base rate for the "
                     "print size",
           "names": {c: {
               "drift_ann1_to_eff1": {
                   "p25": A["drift"]["p25"], "p50": A["drift"]["p50"],
                   "p75": A["drift"]["p75"]},
               "eff_day": {"p25": A["eff_day"]["p25"],
                           "p50": A["eff_day"]["p50"],
                           "p75": A["eff_day"]["p75"]},
               "revert20": {"p25": A["revert20"]["p25"],
                            "p50": A["revert20"]["p50"],
                            "p75": A["revert20"]["p75"]},
               "print_x_adv_point": r["expected_print_x_adv"],
               "print_x_adv_band": [A["vol_mult_eff"]["p10"],
                                    A["vol_mult_eff"]["p90"]],
               "demand_adv_days": r["demand_adv_days"]}
               for c, r in rows.items()}}
    EXPECTED.write_text(json.dumps(exp, indent=1), encoding="utf-8")

    print(f"-> {OUT.relative_to(ROOT)}")
    print(f"-> {EXPECTED.relative_to(ROOT)}  (pre-registered)")
    print(f"\nhistory: {A['n']} additions, "
          f"{out['history']['sample']}")
    print(f"assumptions: index float USD {INDEX_FLOAT_USD_B:,.0f}bn, "
          f"tracking AUM USD {AUM_USD_B:,.0f}bn, USD/TWD {rate:.2f}")
    print(f"\n{'code':<6}{'name':<22}{'wt %':>7}{'demand':>9}"
          f"{'ADVd':>7}{'print':>8}{'pre-25d':>9}{'pctile':>8}")
    for code, r in ranked:
        print(f"{code:<6}{str(r['name'])[:20]:<22}"
              f"{r['index_weight_pct']:>7.3f}"
              f"{r['demand_usd_m']:>8.0f}m"
              f"{r['demand_adv_days']:>7.2f}"
              f"{r['expected_print_x_adv']:>7.1f}x"
              f"{r['pre_ann_excess_25d']:>+9.1%}"
              f"{r['pre_ann_percentile']:>8.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
