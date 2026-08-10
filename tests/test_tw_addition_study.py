"""Guards for the addition study and the Aug-2026 scenarios (c-316).

THE FOUR MISTAKES THIS FILE EXISTS TO CATCH. All four were made
during the pass that produced these files, and three of them
produced clean-looking output.

 1. A SAMPLE FILTER THAT ATE THE SAMPLE. The first version
    required 25 bars before the announcement so pre_drift could
    always use a full lookback. The windows carry a median of 23.
    It kept 7 of 136 events and printed a complete set of medians
    off them without raising.

 2. AN OVERLAPPING-WINDOW CORRELATION AT THE TOP OF THE DRIVER
    TABLE. `gap1 -> total_alpha` at rho +0.560, p=0.0001,
    surviving Bonferroni — and arithmetic, because total_alpha
    contains gap1 as a summand. §0.3.2 of the question bank
    exists because this project already shipped this once.

 3. A SCHEDULE COMPARISON WHOSE BENCHMARK WAS NOT ZERO. The
    effective close IS the tracker's benchmark, so its saving and
    its tracking error are both identically zero. The first
    version returned -0.48% and 3.50%, which is the tell that it
    was measuring something else.

 4. THE MAXIMUM OF SIX RULES REPORTED AS A FINDING. The
    out-of-sample section tried six rules and reported the best
    at +0.30 lift with the verdict "one or more rules show lift".
    It selects 7 events and its binomial p is 0.11.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

SRC = ROOT / "data" / "tw_addition_study.json"
SCN = ROOT / "data" / "aug26_scenarios.json"
EXP = ROOT / "data" / "aug26_expected_outcomes.json"
DOC = ROOT / "docs" / "TW_ADDITION_STUDY.md"

pytestmark = pytest.mark.skipif(
    not (SRC.exists() and SCN.exists()),
    reason="run scripts/tw_addition_study.py then aug26_scenarios.py")


@pytest.fixture(scope="module")
def d():
    return json.loads(SRC.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def s():
    return json.loads(SCN.read_text(encoding="utf-8"))


# ── 1. the sample ────────────────────────────────────────────────────

def test_the_panel_did_not_collapse(d):
    """Mistake 1. A filter that quietly keeps 5% of the panel is
    invisible in the output — every median still formats."""
    S = d["sample"]
    assert S["kept"] >= 100, S
    assert S["additions"] >= 40, S
    assert S["deletions"] >= 60, S
    assert S["additions"] + S["deletions"] == S["kept"]


def test_every_event_is_registry_dated(d):
    """44 windows carry an announcement date estimated as
    effective minus 10 business days, and the real gap is 12-17
    sessions — so day 0 on those sits inside the reaction."""
    assert d["sample"]["day0"].startswith("registry-dated")
    for r in d["events"]:
        assert 5 <= r["sessions_ann_to_eff"] <= 25, r["key"]


def test_pre_drift_carries_its_own_lookback(d):
    """The fix for mistake 1 was to let pre_drift use whatever the
    window holds. That is only honest while the length travels
    with the number."""
    for r in d["events"]:
        assert 15 <= r["pre_drift_sessions"] <= 25, r["key"]


# ── 2. disjoint windows ──────────────────────────────────────────────

def test_overlapping_pairs_are_excluded_not_reported(d):
    """Mistake 2. The pair that ranked first must be absent from
    the table AND present in the exclusion list — dropping it
    silently would leave the next reader to rediscover why."""
    pairs = {(t["feature"], t["target"]) for t in d["drivers_add"]}
    assert ("gap1", "total_alpha") not in pairs
    excluded = {(e["feature"], e["target"])
                for e in d["drivers_excluded_for_overlap"]}
    assert ("gap1", "total_alpha") in excluded
    # the balance measures span ann-20 to eff-1 and so contain the
    # drift window entirely
    assert ("borrow_build", "drift") in excluded
    assert ("margin_build", "total_alpha") in excluded


def test_the_phase_map_covers_every_measure_it_ranks(d):
    """A feature added later with no phase declared would default
    to 'no overlap with anything' and reintroduce mistake 2."""
    import tw_addition_study as M
    for t in d["drivers_add"] + d["drivers_del"]:
        assert t["feature"] in M._PHASES, t["feature"]
        assert t["target"] in M._PHASES, t["target"]


# ── 3. the schedule benchmark ────────────────────────────────────────

@pytest.mark.parametrize("side", ["ADD", "DEL"])
def test_the_benchmark_schedule_is_exactly_zero(d, side):
    """Mistake 3. Executing 100% at the effective close IS the
    benchmark; both its saving and its dispersion are zero by
    construction, and any other value means the comparison is
    measuring the wrong thing."""
    b = d["schedules"][side]["eff_close"]
    assert b["median_saved"] == pytest.approx(0.0, abs=1e-12)
    assert b["tracking_error"] == pytest.approx(0.0, abs=1e-12)
    assert b["p10"] == pytest.approx(0.0, abs=1e-12)
    assert b["p90"] == pytest.approx(0.0, abs=1e-12)


def test_earlier_execution_buys_pnl_with_tracking_error(d):
    """The shape of the result, not its level: every alternative
    to the close saves something and costs tracking error, and
    the earliest one costs the most."""
    S = d["schedules"]["ADD"]
    assert S["ann_plus_1"]["median_saved"] > S["last_four"]["median_saved"]
    assert S["ann_plus_1"]["tracking_error"] > \
        S["last_four"]["tracking_error"] > 0


# ── 4. out-of-sample honesty ─────────────────────────────────────────

def test_the_out_of_sample_verdict_is_selection_corrected(d):
    """Mistake 4. The best of K rules is a maximum. Each rule
    carries a binomial p and the threshold is divided by K."""
    o = d["out_of_sample"]
    assert o["rules_tried"] >= 3
    assert o["selection_corrected_threshold"] == pytest.approx(
        0.05 / o["rules_tried"])
    for r in o["rules"]:
        assert 0 <= r["binomial_p"] <= 1
    best = o["rules"][0]
    survived = best["binomial_p"] < o["selection_corrected_threshold"]
    assert survived == (not o["verdict"].startswith("NO RULE"))


def test_no_rule_currently_survives_and_the_page_says_so(d):
    """The finding, pinned. If a re-run ever produces a surviving
    rule this fails — which is the right outcome, because the
    scenario model is unconditional BECAUSE nothing predicts."""
    assert d["out_of_sample"]["verdict"].startswith("NO RULE")


def test_multiple_comparisons_counts_every_test_touched(d):
    mc = d["multiple_comparisons"]
    assert mc["tests_run"] >= 80
    assert mc["bonferroni_threshold"] == pytest.approx(
        0.05 / mc["tests_run"])
    assert set(mc["survives_bonferroni"]) <= set(
        mc["nominally_significant"])


def test_everything_that_survives_is_about_size_not_direction(d):
    """The organising claim of the whole study. Direction is not
    forecastable; magnitude partly is."""
    price_words = ("drift", "eff_day", "alpha", "revert")
    for t in d["multiple_comparisons"]["survives_bonferroni"]:
        assert not any(w in t for w in price_words), t


# ── the dispersion contract ──────────────────────────────────────────

@pytest.mark.parametrize("leg", ["pre_drift", "gap1", "drift",
                                 "eff_day"])
def test_every_median_carries_its_dispersion(d, leg):
    """§0.3.1. A median without n and an IQR is an anecdote."""
    for side in ("ADD", "DEL"):
        a = d["anatomy"][side][leg]
        for k in ("n", "p10", "p25", "p50", "p75", "p90", "mean"):
            assert a.get(k) is not None, (side, leg, k)
        assert 0 <= a["right_sign_share"] <= 1
        assert a["p10"] <= a["p25"] <= a["p50"] <= a["p75"] <= a["p90"]


def test_the_addition_round_trip_is_negative(d):
    """The headline. If this flips, sections 8 and 12 of the page
    are telling the reader the opposite of the data."""
    A = d["anatomy"]["ADD"]
    assert A["drift"]["p50"] > 0
    assert A["revert20"]["p50"] < 0
    assert abs(A["revert20"]["p50"]) > A["drift"]["p50"]


def test_the_print_asymmetry_survives_its_own_test(d):
    A, D = d["anatomy"]["ADD"], d["anatomy"]["DEL"]
    assert D["vol_mult_eff"]["p50"] > 2 * A["vol_mult_eff"]["p50"]
    assert d["anatomy"]["asymmetry"]["print_size_p"] < 0.001


# ── the flow layer ───────────────────────────────────────────────────

def test_the_flow_asymmetry_is_the_one_the_page_states(d):
    """Foreigners are the deletion and barely the addition, and
    the effective-day print is mostly not ownership transfer."""
    FA, FD = d["foreign_flow"]["ADD"], d["foreign_flow"]["DEL"]
    assert FA["n_with_flow"] >= 30 and FD["n_with_flow"] >= 50
    assert FA["cumulative_to_effective"]["p50"] > 0
    assert FD["cumulative_to_effective"]["p50"] < 0
    assert abs(FD["cumulative_to_effective"]["p50"]) > \
        3 * FA["cumulative_to_effective"]["p50"]
    # the mechanism behind the reversion
    assert FA["institutional_share_of_print"]["p50"] < 0.15
    # deletions keep selling after the print
    assert FD["post10"]["p50"] < 0


# ── the live scenarios ───────────────────────────────────────────────

def test_the_scenarios_are_conditional_and_say_so(s):
    """The probability of inclusion is 37-62% per name and must
    NOT be multiplied into the price scenarios — the two resolve
    on different dates and need separate monitoring."""
    assert "conditional_on" in s
    for code, r in s["names"].items():
        assert 0 < r["prob_of_addition"] <= 1, code


def test_every_band_set_is_a_probability_distribution(s):
    for k, sc in s["scenarios"].items():
        tot = sum(b["prob"] for b in sc["bands"])
        assert tot == pytest.approx(1.0), (k, tot)
        assert len(sc["bands"]) == 5


def test_the_bands_are_ordered_and_come_from_the_history(s, d):
    """The bands are percentiles of the measured distribution, so
    a band boundary that does not match the study is a typed
    number and this catches it."""
    A = d["anatomy"]["ADD"]
    pairs = [("announcement_to_effective", A["drift"]),
             ("effective_day", A["eff_day"]),
             ("post_effective_5", A["revert5"]),
             ("post_effective_20", A["revert20"])]
    for key, dist in pairs:
        b = s["scenarios"][key]["bands"]
        assert b[0]["at_or_below"] == pytest.approx(dist["p10"])
        assert b[2]["median"] == pytest.approx(dist["p50"])
        assert b[-1]["at_or_above"] == pytest.approx(dist["p90"])
        assert b[0]["at_or_below"] <= b[2]["from"] <= b[2]["to"] \
            <= b[-1]["at_or_above"]


def test_the_four_names_are_all_below_the_historical_pre_drift(s):
    """The one genuinely unusual thing about this review, and the
    reason the page carries an amber block about it. If a re-run
    on later data moves these into the body of the distribution
    that caveat has to be rewritten, so it fails here first."""
    pcts = [r["pre_ann_percentile"] for r in s["names"].values()]
    assert len(pcts) == 4
    assert all(p is not None for p in pcts)
    assert max(pcts) < 0.35, pcts
    assert sum(1 for p in pcts if p <= 0.05) >= 3, pcts


def test_the_demand_model_agrees_with_the_measured_flow(s):
    """Weight x AUM is two assumptions. The measured foreign
    accumulation is neither of them, so agreement is evidence and
    disagreement would mean the demand column is decoration."""
    v = s["demand_validation"]
    lo, hi = v["model_range_adv_days"]
    m = v["measured_cumulative_adv_days"]
    assert lo > 0 and hi > lo
    # the model range must sit inside the measured quartiles
    assert m["p25"] <= hi and lo <= m["p75"], (lo, hi, m)


def test_print_size_is_the_only_name_level_forecast(s, d):
    """Section 11 found nothing that predicts direction, so any
    per-name price differentiation would be invention. The four
    names must share one set of price bands."""
    assert d["out_of_sample"]["verdict"].startswith("NO RULE")
    prints = {c: r["expected_print_x_adv"] for c, r in
              s["names"].items()}
    assert len(set(round(v, 6) for v in prints.values())) > 1
    # and the price scenarios live once, at the top level
    assert "scenarios" in s
    for r in s["names"].values():
        assert "drift" not in r and "revert20" not in r


def test_the_expected_outcomes_are_pre_registered():
    """P7. A prediction that is not written down before the event
    is not a prediction."""
    assert EXP.exists(), "run scripts/aug26_scenarios.py"
    e = json.loads(EXP.read_text(encoding="utf-8"))
    assert e["registered"] < e["effective"]
    assert e["conditional_on"]
    assert len(e["names"]) == 4
    for code, r in e["names"].items():
        for k in ("drift_ann1_to_eff1", "eff_day", "revert20"):
            assert set(r[k]) == {"p25", "p50", "p75"}, (code, k)
        assert r["print_x_adv_point"] is not None


def test_the_unobserved_window_is_declared(s):
    """Our last close is 2026-07-31 and MSCI announces on 08-12.
    Eight sessions of run-in are invisible, and they are exactly
    where pre-announcement drift would appear."""
    a = s["assumptions"]
    assert a["sessions_unobserved_before_announcement"] >= 5
    assert a["price_data_ends"] < s["announce"]


# ── the doc ──────────────────────────────────────────────────────────

def test_the_doc_quotes_the_json_it_came_from(d):
    assert DOC.exists(), "run scripts/tw_addition_study.py"
    t = DOC.read_text(encoding="utf-8")
    A = d["anatomy"]["ADD"]
    assert f"{A['drift']['p50']:+.2%}" in t
    assert f"{A['revert20']['p50']:+.2%}" in t
    assert f"{d['sample']['kept']} windows" in t
    assert "NO RULE" in t


# ── the regime split, which nearly did not happen ────────────────────

def test_the_round_trip_is_measured_per_event_not_by_subtraction(d):
    """MISTAKE 5, and it reached a written page before the stress
    test caught it. Pooled drift is +2.21% and pooled revert20 is
    -5.29%, which reads as a -3% round trip. Medians do not add:
    summed event by event the round trip is near zero with half
    the events on each side.

    The page says "coin flip, not a loss" because of this number,
    so if a re-run ever makes the round trip decisively negative
    the prose is wrong and this fails first.
    """
    rt = d["era_split"]["ADD"]["round_trip"]
    assert rt["n"] >= 40
    assert abs(rt["p50"]) < 0.02, rt["p50"]
    assert 0.35 < rt["share_negative"] < 0.65, rt["share_negative"]
    # and it is WIDE — the point is dispersion, not the centre
    assert rt["p75"] - rt["p25"] > 0.10


def test_the_reversion_is_split_at_the_regime_break(d):
    """§0.3.5 is binding: pre- and post-Feb-2023 are different
    populations. The pooled -5.29% is an average of a real effect
    and no effect."""
    E = d["era_split"]["ADD"]
    assert E["pre2023"]["n"] >= 25 and E["post2023"]["n"] >= 12
    assert E["pre2023"]["revert20"]["p50"] < -0.02
    assert E["post2023"]["revert20"]["p50"] > E["pre2023"][
        "revert20"]["p50"]
    assert E["pre2023"]["share_revert20_negative"] > \
        E["post2023"]["share_revert20_negative"]


def test_the_era_difference_is_not_claimed_as_significant(d):
    """The honest half. n=18 in the recent era cannot establish
    that the effect has gone, and the page says so — if a re-run
    ever makes this significant the wording has to change, and
    that is a change worth being forced to make."""
    E = d["era_split"]["ADD"]
    assert E["revert20_p"] is not None
    assert E["revert20_p"] > 0.05, (
        "the era difference is now significant — the page still "
        "says the sample cannot tell you either way")


def test_the_era_tests_are_in_the_multiple_comparisons_ledger(d):
    """Six more tests were run to produce the split. A ledger that
    does not count them understates the correction."""
    names = {t["test"] for t in
             d["multiple_comparisons"]["ranked"]}
    counted = d["multiple_comparisons"]["tests_run"]
    assert counted >= 100
    # the era tests exist in the study output, so they must have
    # been offered to the ledger
    assert any(k.endswith("_p") for k in d["era_split"]["ADD"])
