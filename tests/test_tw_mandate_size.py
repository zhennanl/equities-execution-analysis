"""Guards for the mandate-size estimate (c-349).

WHAT CAN GO WRONG HERE, IN ORDER OF LIKELIHOOD.

1. A DIGIT TYPED WRONG OUT OF A PDF. Four figures were
   transcribed by hand from MSCI's earnings presentation. Both of
   MSCI's own totals — the three fee lines summing to reported
   ABF revenue, the three exposure buckets summing to reported
   ETF AUM — are published, so a transcription error breaks an
   identity rather than sitting there quietly. That is the whole
   reason the totals are carried in the file at all.

2. THE ANCHOR DRIFTS FROM THE DISCLOSURE (c-400). The estimate
   multiplies by MSCI's own disclosed non-ETF/ETF ratio (~1.77x
   from the ~USD 5tn stated on the Q2-26 call), cross-checked by
   the derived 0.45bp fee rate. If a later edit swaps in a
   number that is not MSCI's, or drops the floor variant that
   the old fee inversion still provides, the construction loses
   the property that every input has a document under it.

3. THE COVERAGE RATIO GETS USED AS A MULTIPLIER. It is the most
   tempting number in the file and it is the one that must not be
   multiplied by — the unnamed ETFs in MSCI's EM/All-Country
   bucket include single-country funds holding no Taiwan at all.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
SRC = ROOT / "data" / "tw_mandate_size.json"
DOC = ROOT / "docs" / "TW_MANDATE_SIZE.md"
AUM = ROOT / "data" / "tw_tracking_aum.json"

pytestmark = pytest.mark.skipif(
    not SRC.exists(), reason="run scripts/tw_mandate_size.py")


@pytest.fixture(scope="module")
def d():
    return json.loads(SRC.read_text(encoding="utf-8"))


def test_the_transcription_ties_to_msci_own_totals(d):
    """The two identities MSCI publishes. Neither is an
    assumption of ours, so a break means we mis-read a table."""
    m = d["msci_disclosure"]
    abf = (m["abf_etf_usd_m"] + m["abf_non_etf_indexed_usd_m"]
           + m["abf_futures_options_usd_m"])
    assert abs(abf - m["abf_total_usd_m"]) < 0.15, abf
    aum = (m["etf_aum_us_usd_b"] + m["etf_aum_em_ac_usd_b"]
           + m["etf_aum_dm_ex_us_usd_b"])
    assert abs(aum - m["etf_aum_total_usd_b"]) < 1.0, aum
    # and every figure carries the filing it came from
    for k in ("release", "presentation", "sec_8k"):
        assert m["sources"][k].startswith("https://"), k
    assert "msci.com" in m["sources"]["release"]
    assert m["as_of"] < m["filed"]


def test_the_derived_fee_rate_agrees_with_the_disclosed_one(d):
    """We invert a revenue line at a rate we compute ourselves,
    from revenue over average AUM. MSCI separately discloses a
    period-end basis point fee. The two are different
    calculations on the same business and must land close — if
    they diverge, the revenue line we picked up is not the one we
    think it is."""
    m, n = d["msci_disclosure"], d["non_etf_indexed"]
    bp = (m["abf_etf_usd_m"] * 4) / (m["etf_aum_avg_usd_b"] * 1e3) * 1e4
    assert abs(bp - n["etf_effective_bp_annualised"]) < 0.005
    assert abs(bp - m["etf_bp_fee_period_end"]) < 0.25, (
        bp, m["etf_bp_fee_period_end"])


def test_the_non_etf_pool_is_anchored_and_cross_checked(d):
    """c-400: THE ANCHOR IS THE DISCLOSED POOL, AND THE OLD
    FLOOR RIDES ALONG.

    MSCI stated ~USD 5tn of non-ETF indexed AUM on the Q2 2026
    call, so the estimate no longer prices the mandates at the
    ETF fee rate. Two things must stay true: the derived
    non-ETF rate (revenue / disclosed AUM) sits well BELOW the
    ETF rate — the mandates-pay-less relationship, now measured
    instead of assumed — and the old inversion survives intact
    as the floor variant."""
    n = d["non_etf_indexed"]
    m = d["msci_disclosure"]
    # the disclosed anchor and its multiplier
    assert n["non_etf_aum_disclosed_usd_b"] == \
        m["non_etf_aum_disclosed_usd_b"]
    assert abs(n["multiplier_disclosed"]
               - n["non_etf_aum_disclosed_usd_b"]
               / m["etf_aum_total_usd_b"]) < 1e-4
    assert 1.0 < n["multiplier_disclosed"] < 3.0
    # the cross-check: mandates pay a fraction of the ETF rate
    derived = (m["abf_non_etf_indexed_usd_m"] * 4
               / (n["non_etf_aum_disclosed_usd_b"] * 1e3) * 1e4)
    assert abs(derived - n["non_etf_bp_derived"]) < 0.005
    assert n["non_etf_bp_derived"] < 0.5 * \
        n["etf_effective_bp_annualised"]
    # the retired floor still ties, unchanged
    assert (n["etf_effective_bp_annualised"]
            >= m["etf_bp_fee_period_end"] - 0.25)
    implied = (m["abf_non_etf_indexed_usd_m"]
               * 4 / (n["etf_effective_bp_annualised"] / 1e4) / 1e3)
    assert abs(implied - n["non_etf_indexed_aum_floor_usd_b"]) < 0.5
    assert 0.2 < n["multiplier_floor"] < 0.6, n["multiplier_floor"]
    # the reason has to name the DIRECTION of the old error
    why = n["why_the_floor_was_a_floor"].lower()
    assert "fifth of the etf rate" in why
    assert "understated" in why
    # and the one assumption the anchor adds is stated
    assert "mirrors the etf mix" in n["assumption"].lower()


def test_the_taiwan_etfs_are_added_to_the_always_buys_pool(d):
    """THE CORRECTION c-349 MADE, AND WHY IT IS NOT A JUDGEMENT
    CALL.

    tw_tracking_aum.py's `case_promotion` counted the Standard EM
    and ACWI trackers and stopped, leaving out the ETFs on the
    MSCI Taiwan indexes themselves. But a stock entering MSCI
    Taiwan Standard enters the MSCI Taiwan Index and its capped
    variants at the same review — EWT buys it exactly as EEM
    does."""
    if not AUM.exists():
        pytest.skip("run scripts/tw_tracking_aum.py")
    T = json.loads(AUM.read_text(encoding="utf-8"))[
        "method1_bottom_up"]["totals"]
    tw = d["taiwan"]
    assert abs(tw["always_buys_named_etf_usd_b"]
               - (T["case_promotion"] + T["family"])) < 0.02
    assert tw["always_buys_named_etf_usd_b"] > T["case_promotion"]
    assert tw["always_buys_published_usd_b"] == T["case_promotion"]


def test_the_estimate_is_the_product_of_its_two_steps(d):
    """No third input sneaks in between the ETFs and the
    answer. c-400: the multiplier is 1 + the DISCLOSED ratio;
    the fee-inversion multiplier drives the floor variant."""
    tw, n = d["taiwan"], d["non_etf_indexed"]
    assert abs(tw["mandate_multiplier"]
               - (1 + n["multiplier_disclosed"])) < 1e-6
    assert abs(tw["floor_variant_multiplier"]
               - (1 + n["multiplier_floor"])) < 1e-6
    assert abs(tw["always_buys_named_etf_usd_b"]
               * tw["floor_variant_multiplier"]
               - tw["floor_variant_usd_b"]) < 0.1
    assert tw["floor_variant_usd_b"] < \
        tw["estimate_always_buys_usd_b"]
    assert abs(tw["always_buys_named_etf_usd_b"]
               * tw["mandate_multiplier"]
               - tw["estimate_always_buys_usd_b"]) < 0.1
    # the IMI case is strictly larger and uses the same multiplier
    assert (tw["estimate_if_new_to_imi_usd_b"]
            > tw["estimate_always_buys_usd_b"])
    assert abs((tw["always_buys_named_etf_usd_b"]
                + tw["imi_adds_if_new_usd_b"])
               * tw["mandate_multiplier"]
               - tw["estimate_if_new_to_imi_usd_b"]) < 0.1


def test_the_coverage_ratio_is_never_used_as_a_multiplier(d):
    """The trap. Named ETFs are ~56% of MSCI's disclosed
    EM/All-Country bucket, and grossing Taiwan up by 1.8x would
    credit it with money held by MSCI China, India, Korea and
    Brazil funds that cannot own a Taiwanese share.

    Asserted structurally — the estimate must equal the named
    ETFs times the mandate multiplier ALONE — and in the prose,
    so a reader is told why the obvious move was refused."""
    tw = d["taiwan"]
    assert 0.3 < tw["named_share_of_disclosed_bucket"] < 0.95
    implied_if_grossed = (tw["always_buys_named_etf_usd_b"]
                          * tw["mandate_multiplier"]
                          / tw["named_share_of_disclosed_bucket"])
    assert tw["estimate_always_buys_usd_b"] < implied_if_grossed
    for phrase in ("single-country", "no Taiwan", "China"):
        assert phrase in tw["coverage_note"], phrase


def test_the_doc_quotes_the_json_it_was_generated_from():
    """Same rule as every other write-up here: the prose is
    generated, so it cannot drift from the numbers."""
    if not DOC.exists():
        pytest.skip("run scripts/tw_mandate_size.py")
    d = json.loads(SRC.read_text(encoding="utf-8"))
    doc = DOC.read_text(encoding="utf-8")
    m, tw = d["msci_disclosure"], d["taiwan"]
    assert f"USD {m['etf_aum_total_usd_b']:,.0f}bn" in doc
    assert f"USD {m['etf_aum_em_ac_usd_b']:,.0f}bn" in doc
    assert f"USD {tw['estimate_always_buys_usd_b']:,.0f}bn" in doc
    assert m["as_of"] in doc and m["filed"] in doc


def test_the_script_refuses_to_run_without_its_input():
    """A mandate estimate with no fund list underneath it would
    still print a number, and that number would be zero times a
    multiplier. It must fail loudly instead."""
    import tw_mandate_size as M
    assert M.AUM.name == "tw_tracking_aum.json"
    src = pathlib.Path(M.__file__).read_text(encoding="utf-8")
    assert "raise SystemExit" in src
