"""Guards for the Taiwan case study page and doc (c-290).

THE BUG THESE EXIST TO CATCH. Twice on this project a page has
shipped stating a number that the data no longer supported: card
4 of the walkthrough read "$0B" for several revisions because a
default formatted cleanly instead of raising, and a whole panel
section vanished because a positional slice cut at a marker that
had come to belong to somewhere else. Both were invisible to a
reader and both would have been caught by asserting that what
reaches the screen matches what is in the JSON.

The page and the doc BOTH hard-code "p<0.0001" in prose, because
"p = 0.00005" reads as false precision on a permutation test
whose floor is 1/(trials+1). That phrasing is only honest while
the p-value actually sits below 1e-4, so it is pinned here. If a
re-run pushes it above, these fail rather than letting the page
misstate its own headline.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
# c-316: `import tw_limit_moves` below relied on some OTHER test
# module having put scripts/ on the path first, so this file
# passed in a full run and failed when run alone. A test that
# only works in company is not a test.
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
SRC = ROOT / "data" / "tw_case_study.json"
DOC = ROOT / "docs" / "TW_CASE_STUDY.md"

pytestmark = pytest.mark.skipif(
    not SRC.exists(), reason="run scripts/tw_case_study.py first")


@pytest.fixture(scope="module")
def d():
    return json.loads(SRC.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def screen():
    """Render the page once and return everything it wrote.

    c-289 lesson: a section can stop reaching the screen without
    raising, so the assertion has to be on rendered output, not
    on the source file.
    """
    # c-290: another test's streamlit stub makes streamlit.testing
    # unimportable, and only in a full-suite run. See
    # conftest.real_streamlit.
    from conftest import real_streamlit
    real_streamlit()
    from streamlit.testing.v1 import AppTest
    h = ROOT / "tests" / "_tw_case_harness.py"
    h.write_text(
        f"import sys; sys.path.insert(0, {str(ROOT)!r})\n"
        "from views import tw_case_study\n"
        "tw_case_study.render()\n", encoding="utf-8")
    try:
        at = AppTest.from_file(str(h), default_timeout=300).run()
        assert not at.exception, [e.value for e in at.exception]
        return " ".join(m.value for m in at.markdown)
    finally:
        h.unlink(missing_ok=True)


# c-323, Bill: the page is SIX Taiwan-only sections. The nine
# daily-panel sections were removed, the two 5-second prose
# blocks with them, and the intraday charts lead.
#
# NOTHING WAS DELETED FROM THE PROJECT. Every removed section is
# still generated and still tested — the guards for those numbers
# live in test_tw_addition_study.py, test_tw_auction_microstructure
# .py and the doc assertions below, and the write-ups are in
# docs/TW_CASE_STUDY.md and docs/TW_ADDITION_STUDY.md. This file
# asserts what is ON THE PAGE, which is a different question from
# what the project knows.
SECTIONS = ["Data Review",
            "Where the Volume Actually Prints",
            "Volume Profile on the Effective Day",
            "Market on Close vs VWAP",
            "How Much Volume the Close Can Absorb",
            # c-326: the pre-positioning read sits between the
            # history and the sizing — it is the bridge from
            # "what usually happens" to "what is happening now".
            "Market Positioning Before Announcement Day",
            # c-357: the flow-vs-normal study sits between the
            # positioning read and the sizing — it is what makes
            # the sizing's denominator concrete. A normal day's
            # foreign traffic is the yardstick the order lands
            # against.
            "Foreign Flow Through the Rebalance Window",
            "How Big Is the Market on Close Order"]


GONE = ["How Big Is the Order, in Closes",
        "August 2026, If They Are Added",
        "Has Anyone Already Bought Them",
        "How Much the Taiwanese Close Can Absorb",
        "The Shape of the Effective Day",
        "Borrow Builds on Both Sides",
        "Who Is Actually on the Other Side",
        "What This Study Joins",
        "Borrow Predicts Size, Not Direction",
        "Right Sign, Weak Evidence",
        "Show Up in the Auction",
        "Getting More Crowded",
        "When the Print Cannot Clear",
        "What an Addition Actually Does",
        "When to Execute, and for Whom",
        "What Does Not Predict an Addition",
        "The Review Type Is a Capacity Input",
        "What the 5-Second File Cannot Tell You"]


@pytest.mark.parametrize("s", SECTIONS)
def test_every_section_reaches_the_screen(screen, s):
    assert s in screen


@pytest.mark.parametrize("s", GONE)
def test_the_removed_sections_stay_removed(screen, s):
    """A section that creeps back is a section nobody decided to
    bring back."""
    assert s not in screen


def test_the_page_section_count_is_pinned(screen):
    import re
    n = len(re.findall(r"class='n'>Section", screen))
    assert n == len(SECTIONS), n


def test_no_other_market_is_named_on_the_page(screen):
    """c-323, Bill: *"I want to analyze Taiwan market alone."*
    The intraday sections used to be cross-market bar charts, so
    a stray market name is the tell that one was not rebuilt.

    Japan, Korea and Australia may still appear in the PROSE
    explaining why this page is Taiwan-only — that is the point
    being made — so the check is that no other market appears as
    a DATA LABEL, which is what a chart axis would produce."""
    import re
    labels = re.findall(r"<td[^>]*>([A-Z][a-z]+(?: Kong)?)</td>",
                        screen)
    for bad in ("Japan", "Korea", "Australia", "China", "India",
                "Singapore", "Hong Kong"):
        assert bad not in labels, f"{bad} is a data label"


def test_headline_p_stays_below_the_prose_claim(d):
    """Page and doc both say 'p<0.0001' in words."""
    p = d["H_borrow"]["DEL_predicts"]["t_mult"]["p"]
    assert p < 1e-4, (
        f"t_mult p is now {p:.6f}; the prose in "
        f"views/tw_case_study.py and docs/TW_CASE_STUDY.md "
        f"says 'p<0.0001' and would be misstating it")


def test_the_headline_is_size_not_direction(d):
    """The whole page is organised around borrow explaining the
    print's SIZE and not its DIRECTION. If that ever flips, the
    narrative is wrong everywhere, not just in one caveat."""
    P = d["H_borrow"]["DEL_predicts"]
    assert P["t_mult"]["spearman"] > 0.4
    assert P["eff_day"]["p"] > 0.05, (
        "borrow now predicts the effective-day RETURN — the "
        "page's central claim needs rewriting, not patching")


def test_multiple_comparisons_accounting_is_coherent(d):
    mc = d["multiple_comparisons"]
    assert mc["tests_run"] > 0
    assert set(mc["survives_bonferroni"]) <= set(
        mc["nominally_significant"])
    thr = mc["bonferroni_threshold"]
    assert thr == pytest.approx(0.05 / mc["tests_run"])
    for r in mc["ranked"]:
        hard = r["test"] in mc["survives_bonferroni"]
        assert hard == (r["p"] < thr)
    # the count must cover the tests the page actually shows
    assert mc["tests_run"] >= 15


def test_page_never_prints_a_none_as_a_number(screen):
    """c-328: the substring form of this test was WRONG, and it
    took writing the word "provenance" to expose it — "prove-nan-ce"
    contains "nan", so the page failed for a sentence that had no
    number in it at all. A guard that fires on English prose is a
    guard people learn to route around.

    The failure mode being caught is a missing value FORMATTED as
    though it were a measurement, and those arrive as standalone
    tokens ("nan", "None"), never inside a word. So the tokens are
    matched at word boundaries. "$0B" and "+0.00%" stay literal —
    they are already unambiguous."""
    import re
    for bad in ("None", "nan"):
        m = re.search(rf"\b{bad}\b", screen)
        assert not m, (f"page rendered {bad!r}: "
                       f"...{screen[max(0, m.start()-70):m.end()+40]}...")
    for bad in ("$0B", "+0.00%"):
        assert bad not in screen, f"page rendered {bad!r}"


def test_sample_arithmetic_ties(d):
    s = d["sample"]
    assert s["additions"] + s["deletions"] == s["registry_dated"]
    assert (s["priced_windows"] - s["price_breaks_excluded"]
            == s["analysable"])
    assert s["registry_dated"] + s["estimated_day0_excluded"] \
        == s["analysable"]
    for k in ("with_borrow", "with_intraday"):
        assert s[k] <= s["registry_dated"]


def test_doc_quotes_the_json_it_was_generated_from(d):
    assert DOC.exists(), "run scripts/tw_case_study.py"
    t = DOC.read_text(encoding="utf-8")
    P = d["H_borrow"]["DEL_predicts"]
    assert f"{P['t_mult']['spearman']:+.3f}" in t
    assert f"{d['sample']['registry_dated']}" in t
    for side in ("ADD", "DEL"):
        b = d["H_borrow"][side]["build_days_of_adv"]
        assert f"{b['p50']:+.2f}" in t
    # the limits section is the part most likely to be quietly
    # dropped in an edit, and it is the honest half of the study
    for phrase in ("22 days", "borrowable", "2023",
                   "not an auction print"):
        assert phrase in t


def test_borrow_builds_on_both_sides(d):
    """Section 3's claim: additions build MORE OFTEN than
    deletions. It is the counter-intuitive half of the study and
    the one a careless re-run would reverse."""
    H = d["H_borrow"]
    assert H["ADD"]["share_building"] > H["DEL"]["share_building"]
    assert (H["DEL"]["build_days_of_adv"]["p50"]
            > H["ADD"]["build_days_of_adv"]["p50"])


# ── the price-limit section (c-311) ──────────────────────────────────

LIM = ROOT / "data" / "tw_limit_moves.json"


@pytest.fixture(scope="module")
def lim():
    if not LIM.exists():
        pytest.skip("run scripts/tw_limit_moves.py")
    return json.loads(LIM.read_text(encoding="utf-8"))


def test_the_limit_regime_change_is_honoured(lim):
    """TWSE went 7% -> 10% on 2015-06-01. A detector fixed at 10%
    reports ZERO locked prints for everything before that and
    looks like a clean result — which is why the regimes are
    counted separately and both are non-empty."""
    import tw_limit_moves as M
    assert M.limit_for("2015-05-29") == 0.07
    assert M.limit_for("2015-06-01") == 0.10
    r = lim["by_regime"]
    assert r["limit_7pct"]["prints"] > 0
    assert r["limit_10pct"]["prints"] > 0
    # the finding: widening the cap all but removed the event
    assert r["limit_7pct"]["rate"] > r["limit_10pct"]["rate"] * 5


def test_no_locked_print_exceeds_its_own_limit(lim):
    """A close beyond the cap is impossible. If one appears it is
    an unadjusted corporate action, not a limit move, and it
    would inflate every path in the section."""
    for r in lim["events"]:
        assert abs(r["eff_day_ret"]) <= r["limit_pct"] + 0.005, r


def test_locked_events_are_reported_with_their_clustering(lim):
    """Six of the eight share one date. Reporting eight without
    the episode count would present one crowded print as six
    independent observations."""
    s = lim["sample"]
    assert s["locked_episodes"] < s["locked"], (
        "clustering is no longer recorded")
    assert len(s["locked_dates"]) == s["locked_episodes"]


def test_intraday_touch_is_declared_unmeasurable(lim):
    """Every effective-date bar is close-only. The file must say
    so rather than let a reader assume the count includes names
    that hit the cap and recovered."""
    assert "close-only" in lim["_not_measurable"]
    for r in lim["events"]:
        assert "touched_up" not in r, "touched was inferred"


def test_the_peer_set_is_a_hundred_and_says_what_it_is(screen):
    """c-335, Bill: *"Instead of using 130, just mention 100
    everywhere."*

    THE HONEST WAY TO PUT 100 ON A PAGE IS TO MEASURE 100. The old
    peer set was 130 because that is what the T86 harvest happens
    to carry — the 150-name watch list this project picked in
    2015, minus the 20 TPEx names T86 never publishes. That number
    described a harvesting decision, not a comparison group, so
    relabelling it 100 would have been a caption that disagreed
    with its own data.

    tw_prepositioning.py now ranks on market cap and keeps the top
    100, excluding the candidates themselves — a name cannot be
    its own control."""
    import json as _json
    src = ROOT / "data" / "tw_prepositioning.json"
    if not src.exists():
        pytest.skip("run scripts/tw_prepositioning.py")
    d = _json.loads(src.read_text(encoding="utf-8"))
    for w in d["windows"].values():
        assert w["peer_set_n"] == 100, w["peer_set_n"]
        # the candidates must not be inside their own control
        assert not (set(w["names"]) & set(w.get("peer_codes", ())))
    # c-341 reworded the subtitle to drop the count, so the
    # count is pinned where it is DEFINED — the note under the
    # chart — rather than in a subtitle Bill keeps editing.
    assert "100 largest companies listed on the TWSE" in screen
    # "130" alone is not a safe token — Winbond's close is TWD
    # 130.0 and appears in the derivation. Check the phrasings
    # that would carry the old peer count.
    for stale in ("130 large caps", "130 names", "130 large TWSE",
                  "{130}"):
        assert stale not in screen, stale


def test_the_derivation_is_one_dropdown_per_name(screen):
    """c-347, Bill: the four-step chain moves out of a paragraph
    and into a dropdown per name, in the shape the Predict page
    already uses for the size ladder.

    WHY PER NAME. The old block worked the largest order only, so
    every other bar on the chart was a number the reader had to
    take on trust. Three dropdowns cost nothing closed and remove
    the trust step. All four steps must survive, because a
    derivation missing its middle is worse than none — it looks
    checked."""
    for step in ("Index weight", "Money that must buy", "Shares",
                 "Against the stock's own volume"):
        assert step in screen, step
    # the inputs the chain rests on have to be visible, or the
    # arithmetic is unverifiable from the page
    assert "USD/TWD" in screen
    assert "free-float value" in screen
    assert (ROOT / "docs" / "TRACKING_AUM_PROVENANCE.md").exists()
    assert (ROOT / "docs" / "TW_POSITIONING_ROUND2.md").exists()


def test_one_calculation_dropdown_per_sized_name():
    """The dropdowns are the derivation now, so their COUNT is
    the guard: three sized names, three sets of working, plus the
    one for the mandate they are all priced off (c-349). An
    expander label is not markdown, so it needs its own render
    rather than the shared `screen` string."""
    from conftest import real_streamlit
    real_streamlit()
    from streamlit.testing.v1 import AppTest
    h = ROOT / "tests" / "_tw_case_expanders.py"
    h.write_text(
        f"import sys; sys.path.insert(0, {str(ROOT)!r})\n"
        "from views import tw_case_study\n"
        "tw_case_study.render()\n", encoding="utf-8")
    try:
        at = AppTest.from_file(str(h), default_timeout=300).run()
        assert not at.exception, [e.value for e in at.exception]
        labs = [e.label for e in at.expander]
    finally:
        h.unlink(missing_ok=True)
    calc = [x for x in labs if x.startswith("Calculation")]
    per_name = [x for x in calc if "of ADV" in x]
    assert len(per_name) == 3, labs
    # the mandate working leads, because it is the multiplier
    # every per-name bar rests on
    assert calc[0].endswith("why it is a floor"), calc
    assert "mandate" in calc[0]


def test_the_demand_is_priced_off_a_sourced_number(screen):
    """THE POINT OF c-347 AND c-349, AND THE ONE THAT MATTERS
    MOST ON THIS PAGE.

    Every demand figure used to be `weight x 180bn`, and the 180
    was typed into scripts/event_window_analyze.py as a "passive
    proxy" with nothing under it. It is now built from documents:
    named fund assets for the ETFs, and MSCI's own SEC-filed fee
    disclosure for the mandates that have no ticker.

    This fails if the page drifts back to a figure nobody can
    name the funds or the filing behind."""
    import re
    md = ROOT / "data" / "tw_mandate_size.json"
    if not md.exists():
        pytest.skip("run scripts/tw_mandate_size.py")
    M = json.loads(md.read_text(encoding="utf-8"))
    basis = M["taiwan"]["estimate_always_buys_usd_b"]
    assert f"USD {basis:.0f}bn" in screen, "the basis is not shown"
    # the unsourced constant must not be driving anything
    assert "180bn" not in screen
    assert "assets tracking the index" not in screen
    # the headline orders are well under one day's volume — a
    # card reading >100% of ADV means the page has quietly gone
    # back to the old multiplier
    got = re.findall(r"(?:Largest|Smallest) order</div>"
                     r"<div class='v'>(\d+)% of ADV", screen)
    assert len(got) == 2, got
    assert all(0 < int(x) < 100 for x in got), got
    assert int(got[0]) > int(got[1]), got


def test_the_mandate_estimate_shows_its_filing(screen):
    """c-349, Bill: *"make it more conservative, but can show
    evidence to back up our claim."*

    The claim is a number about other people's money, so the
    evidence has to be a document with a date, not market colour.
    All four MSCI figures the estimate rests on must be on the
    page with the quarter they come from, and the link has to be
    to MSCI's own investor relations site rather than to
    somebody's summary of it."""
    md = ROOT / "data" / "tw_mandate_size.json"
    if not md.exists():
        pytest.skip("run scripts/tw_mandate_size.py")
    M = json.loads(md.read_text(encoding="utf-8"))
    D = M["msci_disclosure"]
    for v in (D["etf_aum_total_usd_b"], D["etf_aum_em_ac_usd_b"]):
        assert f"USD {v:,.0f}bn" in screen, v
    for v in (D["abf_etf_usd_m"],
              D["abf_non_etf_indexed_usd_m"]):
        assert f"USD {v:,.1f}m" in screen, v
    assert D["as_of"] in screen and D["filed"] in screen
    assert "ir.msci.com" in screen


def test_the_estimate_is_labelled_a_floor(screen):
    """A FLOOR IS ONLY HONEST IF IT IS CALLED ONE.

    c-351 cut the two paragraphs that argued the case on the page
    — the fee-rate direction and the coverage-ratio trap. Both
    reasons still exist and are still tested, in
    test_tw_mandate_size.py and in docs/TW_MANDATE_SIZE.md; what
    the page keeps is the WORD, because a number presented as an
    estimate invites a reader to treat it as a midpoint and this
    one is not."""
    md = ROOT / "data" / "tw_mandate_size.json"
    if not md.exists():
        pytest.skip("run scripts/tw_mandate_size.py")
    tw = json.loads(md.read_text(encoding="utf-8"))["taiwan"]
    assert "FLOOR" in screen or "floor" in screen
    assert f"USD {tw['estimate_always_buys_usd_b']:.0f}bn" in screen
    # the argument survives off-page, where it is generated
    doc = (ROOT / "docs" / "TW_MANDATE_SIZE.md").read_text(
        encoding="utf-8")
    assert "single-country" in doc and "no Taiwan" in doc
    assert "LESS per dollar" in doc


def test_the_multiplier_shows_its_own_division(screen):
    """c-351, Bill: *"we need to show how we derive 0.33x of the
    ETF pool."*

    The inversion produced USD 941bn and the page then asserted
    0.33x, which is a second calculation the reader was asked to
    take on faith. Both divisions are now on screen."""
    md = ROOT / "data" / "tw_mandate_size.json"
    if not md.exists():
        pytest.skip("run scripts/tw_mandate_size.py")
    M = json.loads(md.read_text(encoding="utf-8"))
    n, D = M["non_etf_indexed"], M["msci_disclosure"]
    # the inversion
    assert f"{n['non_etf_indexed_aum_floor_usd_b']:,.0f}bn" in screen
    assert f"{n['etf_effective_bp_annualised']:.2f}bp" in screen
    # and the ratio it is turned into
    assert f"{D['etf_aum_total_usd_b']:,.0f}bn = " \
           f"{n['multiplier_floor']:.2f}\u00d7" in screen


def test_the_mandate_arithmetic_ties_on_the_page(screen):
    """The three steps shown must multiply to the number the
    chart is drawn from. Re-derived here from the JSON with no
    reference to the view, because a derivation that does not
    reconcile is worse than none."""
    md = ROOT / "data" / "tw_mandate_size.json"
    au = ROOT / "data" / "tw_tracking_aum.json"
    if not (md.exists() and au.exists()):
        pytest.skip("run the AUM and mandate scripts")
    M = json.loads(md.read_text(encoding="utf-8"))
    T = json.loads(au.read_text(encoding="utf-8"))[
        "method1_bottom_up"]["totals"]
    tw, nef = M["taiwan"], M["non_etf_indexed"]
    D = M["msci_disclosure"]
    # step 1 — the named ETFs, including the Taiwan-dedicated
    # funds that tw_tracking_aum.py had left out
    assert abs(tw["always_buys_named_etf_usd_b"]
               - (T["case_promotion"] + T["family"])) < 0.02
    assert tw["always_buys_named_etf_usd_b"] > T["case_promotion"]
    # step 2 — the fee-rate inversion
    bp = D["abf_etf_usd_m"] * 4 / (D["etf_aum_avg_usd_b"] * 1e3) * 1e4
    assert abs(bp - nef["etf_effective_bp_annualised"]) < 0.005
    implied = D["abf_non_etf_indexed_usd_m"] * 4 / (bp / 1e4) / 1e3
    assert abs(implied
               - nef["non_etf_indexed_aum_floor_usd_b"]) < 0.5
    # the realised rate must sit near MSCI's own disclosed one,
    # or the transcription is wrong somewhere
    assert abs(bp - D["etf_bp_fee_period_end"]) < 0.25
    # step 3 — and the product is what the page says
    assert abs(tw["always_buys_named_etf_usd_b"]
               * tw["mandate_multiplier"]
               - tw["estimate_always_buys_usd_b"]) < 0.1
    assert f"USD {tw['estimate_always_buys_usd_b']:.0f}bn" in screen


def test_the_imi_case_is_off_the_page_but_not_out_of_the_project(
        screen):
    """c-350, Bill: the IMI paragraph comes off all three
    per-name dropdowns.

    It was the same 90 words repeated verbatim three times for a
    distinction that does not vary by name, and the dropdown
    exists to show THAT name's working. Removing it is an editing
    call, not a retraction — so this asserts both halves: it is
    gone from the page, and it is still generated, still tested
    and still written up. The day someone needs to know whether
    IEMG has to buy, the answer is in the file, not lost with a
    paragraph."""
    assert "new to the IMI" not in screen
    assert "MPI Corp" not in screen
    assert "Hon Precision" not in screen
    doc = ROOT / "docs" / "TW_MANDATE_SIZE.md"
    assert doc.exists()
    md = ROOT / "data" / "tw_mandate_size.json"
    if not md.exists():
        pytest.skip("run scripts/tw_mandate_size.py")
    tw = json.loads(md.read_text(encoding="utf-8"))["taiwan"]
    assert tw["estimate_if_new_to_imi_usd_b"] > 0
    assert f"{tw['estimate_if_new_to_imi_usd_b']:,.0f}bn" in \
        doc.read_text(encoding="utf-8")


def test_the_dropdowns_stay_at_four_steps(screen):
    """What the per-name working must still contain after the
    cut: the chain, and nothing decorative. Four steps in, four
    steps out."""
    for step in ("Index weight", "Money that must buy", "Shares",
                 "Against the stock's own volume"):
        assert step in screen, step
    # and the two paragraphs that were cut stay cut
    assert "What that is at the close" not in screen
    assert "ordinary closing auction" not in screen


def test_the_chart_and_its_dropdowns_cannot_disagree(screen, d):
    """The bar is drawn from a weight-times-floor recomputation;
    the dropdown prints the same chain step by step. If those two
    ever came from different code paths the page could show a bar
    and a derivation that do not multiply to each other, which is
    exactly the failure this file was opened for.

    Checked by re-deriving in the test from the JSON, with no
    reference to the view."""
    pb = ROOT / "data" / "tw_tracker_playbook.json"
    sc = ROOT / "data" / "aug26_scenarios.json"
    au = ROOT / "data" / "tw_tracking_aum.json"
    if not (pb.exists() and sc.exists() and au.exists()):
        pytest.skip("run the playbook, scenarios and AUM scripts")
    P = json.loads(pb.read_text(encoding="utf-8"))
    S = json.loads(sc.read_text(encoding="utf-8"))
    md = ROOT / "data" / "tw_mandate_size.json"
    if not md.exists():
        pytest.skip("run scripts/tw_mandate_size.py")
    floor = json.loads(md.read_text(encoding="utf-8"))[
        "taiwan"]["estimate_always_buys_usd_b"]
    A = S["assumptions"]
    sized = sorted([kv for kv in P["names"].items()
                    if kv[1].get("capacity_rank")],
                   key=lambda kv: kv[1]["capacity_rank"])
    assert len(sized) == 3
    for code, r in sized:
        usd_m = r["index_weight_pct"] / 100 * floor * 1000
        sh = usd_m * 1e6 * A["usd_twd"] / S["names"][code][
            "last_close_twd"]
        pct = sh / r["adv_shares"]
        # the scaled playbook figure and the re-derivation agree
        assert abs(pct - r["demand_adv_days"] * floor
                   / A["tracking_aum_usd_b"]) < 1e-9
        assert f"{pct:.1%} of ADV" in screen, (code, pct)
        assert f"{sh / 1e6:,.1f}m shares" in screen, code
