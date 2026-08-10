"""The interactive APAC Rebalance Panel (c-275).

This page is the one exception to the site's "views do no
arithmetic" rule, so the things that rule protected have to be
protected some other way. Three of them:

  * the two panel pages must AGREE, since they summarise the
    same events by different routes;
  * the defaults must be the ones asked for — Taiwan, Feb-2015
    to May-2026 — because a default is what most readers will
    ever see;
  * the percentile has to be a real percentile, not a nearest-
    rank approximation that quietly disagrees with the
    generator's.

The frozen v1 page keeps its own test file. This one does not
touch it.
"""
import json
import sys
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
warnings.filterwarnings("ignore")

SRC = ROOT / "data" / "apac_panel_events.json"

APP = """
import sys
sys.path.insert(0, ".")
from views import apac_panel
apac_panel.render()
"""


@pytest.fixture(scope="module")
def at():
    # c-290: another test's streamlit stub makes streamlit.testing
    # unimportable, and only in a full-suite run. See
    # conftest.real_streamlit.
    from conftest import real_streamlit
    real_streamlit()
    pytest.importorskip("streamlit")
    if not SRC.exists():
        pytest.skip("events file not built")
    from streamlit.testing.v1 import AppTest
    a = AppTest.from_string(APP, default_timeout=300)
    a.run()
    return a


@pytest.fixture(scope="module")
def data():
    if not SRC.exists():
        pytest.skip("events file not built")
    return json.loads(SRC.read_text(encoding="utf-8"))


def test_page_renders_without_exceptions(at):
    assert not at.exception, [str(e.value)[:400]
                              for e in at.exception]


def test_every_section_reaches_the_screen(at):
    md = " ".join(str(m.value) for m in at.markdown)
    # c-285: six. Days to Trade and Direction Hit Rate were
    # removed; Volume Around the Effective Date stayed.
    assert md.count("class='dsect") == 6, md.count("class='dsect")


def test_every_chart_carries_its_own_controls(at):
    """One shared filter bar would mean a reader comparing two
    charts loses the first to set up the second. Five since
    c-285 — every section but the dataset description."""
    assert len(_markets(at)) == 5, len(_markets(at))
    assert len(at.select_slider) == 5, len(at.select_slider)
    # four charts show a distribution and carry a statistic
    # menu; the liquidity share is a share of a count and does
    # not.
    assert len(at.multiselect) == 4, len(at.multiselect)


def _markets(at):
    """Only the market pickers. c-277 added a Side picker to two
    sections, so `at.selectbox` is no longer all one thing —
    which is exactly how these two tests broke, by asserting
    "every selectbox defaults to Taiwan" about a control whose
    options are Both / Additions / Deletions."""
    return [s for s in at.selectbox if s.label == "Market"]


def test_the_default_market_is_taiwan_everywhere(at):
    """Not the pooled panel. Pooling puts China's 1,275 events
    against New Zealand's 13 and calls the result APAC."""
    picks = _markets(at)
    assert len(picks) == 5, len(picks)
    for s in picks:
        assert s.value == "Taiwan", s.value


def test_all_markets_is_offered_and_leads_the_list(at):
    for s in _markets(at):
        assert s.options[0] == "All Markets", s.options[:2]


def test_the_default_review_range_is_feb2015_to_may2026(at, data):
    lab = data["review_labels"]
    for s in at.select_slider:
        lo, hi = s.value
        assert lab[str(lo)] == "Feb-2015", lab[str(lo)]
        assert lab[str(hi)] == "May-2026", lab[str(hi)]


def test_the_percentile_is_offered_only_where_it_earns_it(at):
    """c-277 removed the 90th percentile everywhere; c-279 puts
    it back on effective-day risk ALONE.

    That is not indecision, it is the statistic finding its one
    home. On print size or the share clearing a volume
    threshold the tail is a distraction. On the move a desk
    carries into the close it is the number you quote to a
    client — the median is the day you plan for, the 90th is
    the day that breaks the schedule.

    Pinned per menu, so a percentile cannot quietly spread back
    across the page.
    """
    opts = [m.options for m in at.multiselect]
    assert ["Median", "Mean"] in opts, opts
    assert ["Median", "Mean", "90th percentile"] in opts, opts
    # and it is ON by default where it exists, since a tail
    # nobody switches on is a tail nobody sees
    risk = [m for m in at.multiselect
            if "90th percentile" in m.options][0]
    assert "90th percentile" in risk.value, risk.value


def test_the_liquidity_threshold_is_an_input_not_a_constant(at):
    """c-277, Bill: *"we limit to twice normal? Can we give the
    user's an option to set the multiple?"* Two was a
    convention, never a finding, and where the line sits moves
    the answer a long way — on the default selection 94% of
    events reach 2x ADV and 79% reach 5x."""
    thr = [n for n in at.number_input
           if "Threshold" in str(n.label)]
    assert len(thr) == 1, [str(n.label) for n in at.number_input]
    assert thr[0].value == 2.0


def test_every_chart_states_the_adv_window(at):
    """c-277, Bill: *"add a note about how many days of ADV we
    calculated, from which period."*

    One string under every chart, not a paraphrase per section:
    the denominator is the same everywhere and a reader who
    meets it on section 2 must meet the identical wording on
    section 6. Both halves of the definition are asserted —
    it is a MEDIAN, and it ENDS BEFORE the announcement, which
    is what stops the event's own volume inflating its own
    benchmark."""
    md = " ".join(str(m.value) for m in at.markdown)
    n = md.count("Note: ADV = median daily volume over the 20 "
                 "sessions ending the day before the "
                 "announcement")
    assert n >= 3, f"ADV note appears {n} times"


def test_the_effective_day_chart_splits_by_side(at):
    """c-277. Pooling additions and deletions averaged a forced
    buyer and a forced seller into a number describing
    neither."""
    sides = [s for s in at.selectbox if s.label == "Side"]
    # three since c-285: the rebalance window, the volume path
    # and effective-day risk. Same reason each time — an
    # addition and a deletion are different trades, and
    # averaging them describes neither.
    assert len(sides) == 3, len(sides)
    for sd in sides:
        assert sd.options == ["Both", "Additions", "Deletions"]
        assert sd.value == "Both"


def test_x_axis_ticks_carry_the_year_only_and_once(at):
    """c-277: *"Standardize the x-axis label to include only
    year."* Four reviews a year means the naive version prints
    2015 four times running, so the label lands on the first
    review of each year and is blank on the other three."""
    from views import apac_panel as P
    got = P._year_ticks(["Feb-2015", "May-2015", "Aug-2015",
                         "Nov-2015", "Feb-2016", "May-2016"])
    assert got == ["2015", "", "", "", "2016", ""], got


def test_the_removed_furniture_stays_removed(at):
    """The status strip and the four stat cards between them
    used a screen of vertical space above the first chart to
    say the sample size twice."""
    md = " ".join(str(m.value) for m in at.markdown)
    for gone in ("Tier 1 — no positioning data", "Name-events",
                 "Largest sample", "Delisted-safe",
                 "Bars show", "Above 5x normal volume"):
        assert gone not in md, gone


def test_the_median_matches_the_taiwan_engine():
    """THE SITE HAS TWO PERCENTILE DEFINITIONS, and this test
    exists to pin which one the new page uses.

    Found by writing this test, not before:

      scripts/index_strategist_qa._pct   NEAREST-RANK. Rounds
          to a real datapoint: int(round(p * (n-1))).
      scripts/rebalance_analysis._pct    LINEAR INTERPOLATION,
          the numpy/Excel default.

    They agree only when p*(n-1) lands on a whole number. On
    the panel's own p90 cells they part company by up to
    2.30 percentage points — Singapore additions read 2.18%
    nearest-rank against 4.48% interpolated, on n=6. Small
    samples are where it bites, which is exactly where this
    page lets a reader go by narrowing the review range.

    The new page follows the INTERPOLATED definition, because
    that is what a reader typing "37th percentile" into a box
    means and what every other tool would return. The frozen v1
    page keeps nearest-rank; it is not edited to match, so its
    p90 and this page's p90 can legitimately differ on a thin
    cell.
    """
    import index_strategist_qa as Q
    import rebalance_analysis as RA
    from views import apac_panel as P
    xs = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0]
    for p in (.10, .25, .5, .75, .90):
        assert abs(P._q(xs, p) - RA._pct(xs, p)) < 1e-12, p
    # and the divergence from v1 is real, not imagined — if
    # this ever stops being true someone changed a definition
    assert P._q(xs, .25) != Q._pct(xs, .25)


def test_median_and_mean_are_not_the_same_function():
    """Sounds trivial. It is the whole reason Bill asked for the
    mean: these distributions have long tails and the two
    disagree, and a copy-paste that made Mean call the median
    would look completely plausible on screen."""
    from views import apac_panel as P
    xs = [1.0, 1.0, 1.0, 1.0, 100.0]
    assert P._stat(xs, "Median", 50) == 1.0
    assert abs(P._stat(xs, "Mean", 50) - 20.8) < 1e-9


def test_empty_selections_do_not_raise():
    """A reader can pick New Zealand and a two-review range,
    which is four events or none. That must say so, not crash
    or draw an empty axis as though it meant zero."""
    from views import apac_panel as P
    assert P._stat([], "Median", 50) is None
    assert P._stat([None, None], "Mean", 50) is None
    assert P._q([], .5) is None


def test_the_events_feed_carries_no_aggregates(data):
    """The file is rows. If a future change starts shipping
    precomputed cells in here too, the page has two sources for
    one number and they will drift."""
    assert "events" in data and data["events"]
    assert len(data["events"]) == data["n_events"]
    banned = {"median", "p90", "mean", "rows", "questions"}
    assert not (banned & set(data)), banned & set(data)


def test_the_frozen_v1_page_is_still_wired_up():
    """The duplicate is the point of the exercise. If the route
    disappears, the copy is only a file on disk."""
    # c-303, Bill took the v1 route off the site. The test keeps
    # its POINT rather than its old assertion: the frozen copy
    # exists so the pre-redesign page is never one edit from
    # gone, and that is a claim about the FILE and its tests, not
    # about a nav entry. app.py is asserted to still name it, so
    # a reader finds out where it went.
    src = (ROOT / "app.py").read_text(encoding="utf-8")
    assert (ROOT / "views" / "apac_strategist.py").exists(), \
        "the frozen v1 panel was deleted, not just unrouted"
    assert (ROOT / "tests" /
            "test_apac_strategist_page.py").exists(), \
        "the frozen panel lost the test that freezes it"
    assert "apac_strategist" in src, \
        "app.py no longer says where the v1 panel went"
    assert "apac_panel" in src
    # c-277 renamed the live page to say DAILY DATA, because
    # that is the whole limitation of it — daily bars only, so
    # the closing auction is one number rather than a window.
    # The nav label is asserted here so the rename and the route
    # cannot drift apart: app.py routes on endswith("Daily
    # Data"), and a label edit that forgot the route would fall
    # through to the default page with no error.
    assert "Index Rebalance Daily Data" in src
    assert 'endswith("Daily Data")' in src
    # c-303: the ordering check used "Announcement → Effective"
    # as its right-hand anchor, and that page is off the site.
    # The claim worth keeping is that the daily panel sits after
    # the two pages that explain the review, not that it
    # precedes one particular later page.
    i = src.index('st.sidebar.radio("Page"')
    order = src[i:i + 500]
    assert order.index("Predict MSCI Index Changes") < \
        order.index("Daily Data")


def test_the_dead_hover_card_was_removed_not_orphaned():
    """c-279. Section 2 became a dot chart, so the HTML bar
    chart it hung on is gone and the hover card had nothing to
    sit on.

    The card is DELETED rather than left defined-but-unused.
    130 lines of CSS and geometry that nothing calls is not an
    asset in reserve, it is a thing that rots quietly until
    someone edits it believing it ships. It survives where it
    belongs — history_explorer still uses the pattern for the
    chart it was built for.
    """
    from views import apac_panel as P
    from views import history_explorer as H
    assert not hasattr(P, "POP_CSS")
    assert not hasattr(P, "_bar_pop")
    assert ".pop{display:none;position:absolute" in H.POP_CSS


def test_the_year_axis_passes_only_labelled_ticks():
    """c-279, Bill: *"the year label for graph in this section
    is misaligned."*

    It was, and the cause was not styling. The old version gave
    plotly EVERY category as a tickval with blank text for
    three in four, and plotly then spaced and rotated the whole
    set as though all of them carried text — so the year that
    did print drifted off the bar it named. Passing only the
    ticks that have a label lets plotly place each on its own
    category.
    """
    from views import apac_panel as P
    ax = P._year_axis(["Feb-2015", "May-2015", "Aug-2015",
                       "Nov-2015", "Feb-2016"])
    assert ax["tickvals"] == ["Feb-2015", "Feb-2016"], ax
    assert ax["ticktext"] == ["2015", "2016"], ax
    assert ax["tickangle"] == 0
    # a market axis is not a time axis and keeps every label
    ax = P._year_axis(["Taiwan", "Korea"], on=False)
    assert ax["ticktext"] == ["Taiwan", "Korea"]


def test_section_three_reports_the_share_that_clears(at):
    """c-279, Bill: *"change it to successful achieve volume
    over threshold. So the percentage should be 1-current
    number."* Same data, complementary framing — and the one
    that is a capacity statement rather than a statement about
    what did not happen.
    """
    md = " ".join(str(m.value) for m in at.markdown)
    assert "traded at or above" in md
    assert "Trade Above Normal Liquidity" in md
    # the red banding is gone with it
    assert "Red marks periods" not in md
    assert "printed under" not in md


def test_the_rebalance_window_is_the_first_section(at):
    """c-280, Bill: the cumulative-return chart from the
    Announcement -> Effective page, rebuilt on all APAC data and
    moved here as section 1."""
    md = " ".join(str(m.value) for m in at.markdown)
    assert "Index Rebalance Daily Data" in md
    # c-287: the dataset description leads now, and the
    # rebalance window follows it. A reader meets what the data
    # IS before the first chart drawn from it.
    i = md.index("Data Review")
    for later in ("The Rebalance Window", "How Big Is the Print",
                  "Effective-Day Risk"):
        assert md.index(later) > i, later


def test_day_zero_is_the_pre_news_baseline_and_reads_zero():
    """The chart is anchored on the ANNOUNCEMENT CLOSE, which is
    the last price set with nobody knowing — MSCI publishes from
    Geneva before the Asian open. Anchoring one session later
    would fold the jump into the baseline and flatten the move
    the chart exists to show. Zero at day 0 is what proves the
    anchor is where it is claimed to be."""
    import json
    import pandas as pd
    from views import apac_panel as P
    d = json.loads(SRC.read_text(encoding="utf-8"))
    df = pd.DataFrame(d["events"])
    off = d["path_offsets"]
    ys, _ns = P._path_series(df, off, "Median")
    assert abs(ys[off.index(0)]) < 1e-9, ys[off.index(0)]
    assert off[0] == -20 and off[-1] == 40


def test_the_path_ties_to_the_independently_stored_metric():
    """THE REAL CHECK. `path` is built by walking the daily
    bars; `gap1` is computed by `metrics()` from the same window
    by a different route. Day 1 of the path and the gap1 median
    must therefore be the same number — and they are, to three
    decimals, on both sides of Taiwan.

    If they ever diverge, one of the two is reading the wrong
    baseline session, which is the failure this whole anchoring
    argument is about.

    TOLERANCE. `path` is stored rounded to 3 decimal places of
    a percentage, so two values that agree exactly before
    storage can differ by up to 5e-4pp after it. The observed
    gap is 2.1e-4pp. The tolerance is set to the storage
    granularity rather than to something loose enough to pass —
    a wrong baseline session would be off by whole percent, not
    by a rounding step.
    """
    import json
    import statistics as st
    import pandas as pd
    from views import apac_panel as P
    d = json.loads(SRC.read_text(encoding="utf-8"))
    df = pd.DataFrame(d["events"])
    off = d["path_offsets"]
    tw = df[(df.market == "Taiwan") & (df["ord"] >= 201502)]
    for act in ("ADD", "DEL"):
        g = tw[tw.action == act]
        ys, _ = P._path_series(g, off, "Median")
        gap = st.median([v for v in g["gap1"]
                         if v is not None and v == v])
        assert abs(ys[off.index(1)] - gap * 100) < 2e-3, act


def test_thin_offsets_are_left_blank_not_plotted():
    """Windows are ragged at the right — every event reaches day
    +20 but only 1,771 of 2,175 reach day +40. Without a floor
    the line keeps going and quietly becomes the median of
    whichever markets happen to have the longest windows."""
    import json
    import pandas as pd
    from views import apac_panel as P
    d = json.loads(SRC.read_text(encoding="utf-8"))
    df = pd.DataFrame(d["events"])
    off = d["path_offsets"]
    tw = df[(df.market == "Taiwan") & (df.action == "ADD")]
    ys, ns = P._path_series(tw, off, "Median")
    for y, n in zip(ys, ns):
        if n < P.MIN_N_AT_OFFSET:
            assert y is None, (n, y)
        else:
            assert y is not None, n


def test_the_liquidity_chart_is_bars_again(at):
    """c-280, Bill asked for it back, and he is right: the other
    charts plot a LEVEL that moves continuously, this plots a
    SHARE of a count. A line joining two shares implies the
    value between them meant something."""
    src = (ROOT / "views" / "apac_panel.py").read_text(
        encoding="utf-8")
    i = src.index("How Many Stocks Trade Above Normal")
    j = src.index("Effective-Day Risk")
    assert "fig.add_bar(" in src[i:j], "liquidity chart is not bars"


def test_the_fill_walk_still_works_though_its_section_is_gone():
    """c-281. The fill is walked against each event's OWN volume
    curve, not a flat ADV assumption.

    That is not a refinement, it is the difference between a
    usable answer and a wrong one: Taiwan runs about 12x ADV on
    the effective day and about 2x the session after, so a flat
    model understates what the print absorbs and overstates
    every session that follows it.

    Hand-checked against one event: code 2615 trades
    7.16 / 2.41 / 0.99 / 0.82 x ADV over eff..eff+3, so at 20%
    participation it absorbs 1.43 / 0.48 / 0.20 / 0.16 ADV-days
    — 2.27 of a 5-day order in four sessions.
    """
    from views import apac_panel as P
    vp = [7.156, 2.413, 0.989, 0.821] + [0.8] * 40
    assert P.sessions_to_fill(vp, 0, 1.0, 0.20) == 1
    assert P.sessions_to_fill(vp, 0, 2.0, 0.20) == 3
    # a flat 1x-ADV model would need 5 sessions for a 1-day
    # order at 20%; the real effective day does it in one
    flat = [1.0] * 44
    assert P.sessions_to_fill(flat, 0, 1.0, 0.20) == 5
    # and an order past the horizon is None, not a big number
    assert P.sessions_to_fill(flat, 0, 100.0, 0.20) is None


def test_unfilled_orders_are_censored_not_dropped():
    """THE BUG THIS TEST EXISTS FOR, caught by hand-checking the
    section rather than by writing it.

    Events that never fill inside the horizon return None. The
    first version dropped them and took the median of the rest,
    which always flatters: on Taiwan at 20 days and 20%
    participation, the survivors-only median read 20 sessions
    on 15 of 136 events. The honest answer is "beyond 30".

    A median tolerates right-censoring as long as under half
    the sample is censored — the censored values are all larger
    than every observed one, so they sit at the top of the
    order and only matter if they reach the middle.
    """
    from views import apac_panel as P
    # 3 filled, 1 censored: the median is the 2nd of 4, still
    # inside the observed values
    # [2, 4, 6, >30]: the median of four is the mean of the
    # 2nd and 3rd, so 5 — the censored value never enters it
    med, cens = P.censored_median([2, 4, 6], 1)
    assert not cens and abs(med - 5.0) < 1e-9, (med, cens)
    # half censored: the median is past the horizon
    med, cens = P.censored_median([2, 4], 2)
    assert med is None and cens
    # majority censored, likewise
    med, cens = P.censored_median([2], 9)
    assert med is None and cens
    assert P.censored_median([], 0) == (None, False)


def test_the_deleted_sections_stay_deleted(at):
    """c-285 removed Days to Trade and Direction Hit Rate.

    `sessions_to_fill` and `censored_median` are LEFT on the
    module: the censoring argument they encode is the most
    reusable thing this page produced, and their tests still
    run. A helper with a passing test is not dead weight; an
    unreferenced 200-line section would have been."""
    md = " ".join(str(m.value) for m in at.markdown)
    for gone in ("Days to Trade", "Direction Hit Rate",
                 "Order (days of ADV)", "Participation (%)"):
        assert gone not in md, gone
    from views import apac_panel as P
    assert callable(P.sessions_to_fill)
    assert callable(P.censored_median)


def test_the_volume_path_ties_to_the_stored_print_multiple():
    """`vpath` is walked from the daily bars; `t_mult` is
    computed by metrics() from the same window by another route.
    At the effective offset they are the same number, so if they
    ever part, one of the two has the wrong session."""
    import json
    d = json.loads(SRC.read_text(encoding="utf-8"))
    off = d["path_offsets"]
    i0 = off.index(0)
    worst, n = 0.0, 0
    for e in d["events"]:
        if not (e.get("vpath") and e.get("t_mult")
                and e.get("eff_off") is not None):
            continue
        j = i0 + int(e["eff_off"])
        if not (0 <= j < len(off)) or e["vpath"][j] is None:
            continue
        n += 1
        worst = max(worst, abs(e["vpath"][j] - e["t_mult"]))
    assert n > 2000, n
    # vpath is stored to 3dp, so 5e-4 is the storage granularity
    assert worst <= 5e-4, worst


def test_the_page_title_leads_the_page(at):
    """c-281, Bill: the title sat lower than every other page's.
    It was emitted after the data load, a stylesheet later than
    its siblings. css() then title, first."""
    src = (ROOT / "views" / "apac_panel.py").read_text(
        encoding="utf-8")
    i = src.index("def render():")
    head = src[i:i + 1200]
    assert head.index("design.css()") < head.index("_frame(")
    assert head.index("st.markdown(\"# Index Rebalance") < \
        head.index("_frame(")


def test_unadjusted_corporate_actions_are_flagged_and_dropped(data):
    """c-284, from Bill asking whether Aug25|6919 was an outlier
    or bad data.

    Bad data, and not alone. Caliway closed at 1,215 on
    2025-07-11, was suspended, and reopened at 133.50 on
    2025-07-21 — a 10-for-1 split. TWSE day files and NSE
    bhavcopy publish UNADJUSTED prices, so the split reads as a
    -89% session and the event's path opens at +923%.

    Taiwan has a 10% daily price limit, so a session outside
    roughly +/-11% there is arithmetically impossible without a
    capital change. The threshold sits well beyond any market's
    limit: nearly doubling, or more than halving, in a session.

    They are FLAGGED IN THE FILE and dropped by the page, not
    repaired. Repairing means inventing an adjustment factor
    from the ratio, and the ratio is contaminated by whatever
    the price did while the stock was suspended.
    """
    from views import apac_panel as P
    assert data["n_price_break"] >= 9, data["n_price_break"]
    flagged = {(b["market"], b["rev"], b["code"])
               for b in data["price_breaks"]}
    assert ("Taiwan", "Aug25", "6919") in flagged
    # every flagged event names the two dates, so the call can
    # be checked against the exchange rather than trusted
    for b in data["price_breaks"]:
        assert b["detail"] and "->" in b["detail"], b
    # and none of them reaches the page
    df, _d = P._frame()
    got = {(r.market, r.rev, str(r.code)) for r in df.itertuples()}
    assert not (flagged & got), flagged & got


def test_no_surviving_path_opens_beyond_a_plausible_move(data):
    """The property the flag protects. With the splits gone, no
    Taiwan path should start hundreds of percent from its own
    baseline — day -20 is twenty sessions of ordinary trading
    before anyone knew anything."""
    from views import apac_panel as P
    df, d = P._frame()
    off = d["path_offsets"]
    i = off.index(-20)
    worst = 0.0
    for r in df.itertuples():
        if isinstance(r.path, list) and r.path[i] is not None:
            worst = max(worst, abs(r.path[i]))
    assert worst < 200, worst


def test_the_review_axis_is_time_not_categories():
    """c-284, Bill: *"the spacing between each label is not
    equally divided."*

    The cause was the axis TYPE. A categorical axis spaces its
    slots evenly and knows nothing about time, so a year with
    four reviews in the panel takes twice the width of a year
    with two and the year labels land wherever those slots fall.
    A numeric decimal-year axis is evenly spaced because time
    is, and a missing review shows as a gap instead of being
    closed up.
    """
    from views import apac_panel as P
    groups = [("Feb-2015", None), ("May-2015", None),
              ("Nov-2015", None), ("Feb-2016", None)]
    xs, ax = P._time_x(groups, "Taiwan")
    # c-310: month ticks off again (c-309 put them on). The tick
    # style is a preference and has now moved both ways, so it is
    # asserted loosely — year-only today. The x VALUES below are
    # the real subject: they are what makes the spacing true to
    # time, and they have not changed through either request.
    assert ax["tickmode"] == "linear" and ax["dtick"] == 1
    assert abs(xs[0] - 2015.0833) < 1e-3, xs
    assert abs(xs[1] - 2015.3333) < 1e-3, xs
    # Aug-2015 is missing from the panel, so Nov must sit where
    # November is, not where the third slot would be
    assert abs(xs[2] - 2015.8333) < 1e-3, xs
    assert abs(xs[3] - 2016.0833) < 1e-3, xs
    # a market axis is a cross-section and stays categorical
    xs, ax = P._time_x([("Taiwan", None), ("Korea", None)], ALL_)
    assert ax["tickmode"] == "array"
    assert xs == ["Taiwan", "Korea"]


ALL_ = "__ALL__"


def test_the_review_hover_names_the_month_not_a_decimal_year():
    """c-313, Bill: *"we accidentally removed the month label in
    the hover."*

    THE FAILURE MODE, which is why this is a test and not just a
    copy fix. c-284 turned the review axis NUMERIC — x is a
    decimal year, Feb-2015 -> 2015.0833 — so every hovertemplate
    reading `%{x}` silently stopped printing "Feb-15" and started
    printing 2015.0833333. Nothing raised, and the tick styling
    was reworked twice afterwards (c-309, c-310) without either
    pass noticing, because a tooltip is invisible to every other
    test on this page.

    `_dots` is the shared builder behind section 3, so testing it
    covers the one that is reusable; sections 5 and 6 build their
    traces inline and are covered by the source check below.
    """
    from views import apac_panel as P
    fig = P._dots([2015.0833, 2015.3333],
                  [("Median", [1.0, 2.0], [7, 9])],
                  "multiple of ADV", fmt=".1f",
                  labels=["Feb-2015", "May-2015"])
    tr = fig.data[0]
    assert "%{x}" not in tr.hovertemplate, tr.hovertemplate
    assert "%{customdata[0]}" in tr.hovertemplate
    # the label AND n both survive — a fix that dropped n to make
    # room for the label would pass a "no %{x}" test alone
    assert list(tr.customdata[0]) == ["Feb-2015", 7]
    assert list(tr.customdata[1]) == ["May-2015", 9]
    # a categorical axis is untouched: there %{x} IS the label
    plain = P._dots(["Taiwan", "Korea"],
                    [("Median", [1.0, 2.0], [7, 9])], "y")
    assert "%{x}" in plain.data[0].hovertemplate


def test_sections_five_and_six_carry_the_label_in_customdata():
    """The inline traces, same invariant as `_dots` above.

    Both sections build their x from `_time_x`, so both are on
    the numeric review axis and neither may read `%{x}`.
    """
    src = (ROOT / "views" / "apac_panel.py").read_text(
        encoding="utf-8")
    i = src.index("How Many Stocks Trade Above Normal")
    j = src.index("Effective-Day Risk")
    for name, block in (("section 5", src[i:j]),
                        ("section 6", src[j:])):
        k = block.index("hovertemplate=")
        head = block[k:k + 200]
        assert "%{x}" not in head, (name, head)
        assert "customdata" in head, (name, head)


def test_a_discontinuous_series_is_drawn_as_pinned_width_bars():
    """c-285, Bill asked what chart type suits a discontinuous
    dataset.

    Bars, with the width pinned to the sampling interval. A line
    draws a segment between two reviews and so asserts a value
    for every day in between, when the series only exists four
    times a year. Bars carry the opposite claim — this value
    belongs to THIS interval and nowhere else.

    The width has to be EXPLICIT on a numeric time axis.
    Plotly sizes bars from the smallest gap it can find, so one
    missing review would make every bar on the chart narrower;
    pinning to just under a quarter means a bar always occupies
    its own quarter and a missing review shows as white space.
    """
    src = (ROOT / "views" / "apac_panel.py").read_text(
        encoding="utf-8")
    i = src.index("How Many Stocks Trade Above Normal")
    j = src.index("Effective-Day Risk")
    block = src[i:j]
    assert "fig.add_bar(" in block, "not bars"
    assert "width = 0.22" in block, "bar width not pinned"
    assert "bargap=0" in block


def test_section_one_states_the_baseline_without_the_lecture(at):
    """c-285. Bill cut the caveat to two sentences. The one
    thing it must still carry is WHERE the baseline is, since
    every number on the chart is relative to it."""
    md = " ".join(str(m.value) for m in at.markdown)
    # c-287: "close" -> "day" throughout this section
    assert "Day 0 is the announcement day" in md
    assert "where cumulative return indexed at 0" in md
    assert "Day 0 is the announcement close" not in md
    assert "dashed line represents the effective date" in md
    # the removed lecture stays removed
    assert "last price set with nobody knowing" not in md


def test_every_legend_names_the_statistic(at):
    """c-289, reversing c-285/c-287.

    The statistic was stripped from these legends as
    duplication of the control above them. That was wrong once
    TWO statistics can be drawn at the same time — a solid line
    and a dotted one need naming, and "Additions" twice is
    worse than "Additions — median" and "Additions — mean".

    Asserted on the SOURCE of each section rather than the
    rendered page, because a legend entry only appears when its
    series is drawn and the default selection does not draw
    every one.
    """
    src = (ROOT / "views" / "apac_panel.py").read_text(
        encoding="utf-8")
    # each section runs from its own heading to the next one
    heads = ["Data Review", "The Rebalance Window",
             "How Big Is the Print",
             "Volume Around the Effective Date",
             "How Many Stocks Trade Above Normal",
             "Effective-Day Risk"]
    # match on the heading TEXT, not on a reconstructed
    # `design.sect(n, "...")` literal — the call wraps across
    # lines for the longer titles, so the literal is not in the
    # source in one piece
    pos = [src.index(f'"{h}') for h in heads]
    pos.append(len(src))
    for name in ("The Rebalance Window",
                 "Volume Around the Effective Date",
                 "Effective-Day Risk"):
        i = heads.index(name)
        block = src[pos[i]:pos[i + 1]]
        assert 'name=f"{slab} — {k.lower()}"' in block, name


def test_the_summary_notes_sit_under_their_axis(at):
    """c-289. A line summarising the whole chart belongs
    centred beneath it; left-aligned it reads as a caption on
    the first bar."""
    md = " ".join(str(m.value) for m in at.markdown)
    assert md.count("text-align:center") >= 3
    assert "number of data points =" in md
    assert "of this selection traded at or above" in md


def test_the_risk_chart_says_it_is_an_absolute_value(at):
    """c-289. Without this the reader cannot tell |move| from a
    signed return — and a median of SIGNED effective-day
    returns would sit near zero, because additions rise and
    deletions fall, making the print look harmless."""
    # c-293: Bill cut the note to one line, so the assertion
    # drops to the claim that survives. The wording changed;
    # the thing that must not vanish did not.
    md = " ".join(str(m.value) for m in at.markdown)
    assert "absolute value" in md
