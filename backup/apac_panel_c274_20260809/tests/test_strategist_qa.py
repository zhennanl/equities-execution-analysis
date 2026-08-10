"""The strategist panel, and the overlap trap (c-230).

The correlation in Q9 came back 0.35-0.44 in EVERY market on
the first run. That uniformity was the tell, not the finding:
`drift` runs day+1 to effective-1 and `early3` runs day+1 to
day+3, so drift CONTAINS early3 and the correlation is
arithmetic. Corrected to a non-overlapping `late_drift`, the
honest rho collapses to -0.34..0.22 — noise in every market.

A desk that had acted on the first version would have been
reading its own left-hand side.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import index_strategist_qa as Q                     # noqa: E402


def _panel():
    return Q.build()


def test_the_panel_loads_every_market():
    rows, by = _panel()
    assert len(rows) > 1500, len(rows)
    assert len(by) >= 10, sorted(by)
    assert {"Taiwan", "China", "Japan", "India"} <= set(by)


def test_early_and_late_windows_do_not_overlap():
    """THE REGRESSION. If these ever share a session again the
    Q9 correlation becomes arithmetic and stops meaning
    anything.

    c-274 REWROTE THIS TEST, and the reason is worth keeping.
    It used to assert that the literal string
    `ret(min(i0 + 3, ie - 1), ie - 1)` appeared in the source.
    That passed for the right reason once and then failed for
    the wrong one: a refactor that lifted the same two indices
    into named variables broke the assertion without changing
    a single computed number. A test that fails on a rename
    but would also pass on a genuinely overlapping window
    written a different way is guarding the spelling, not the
    property.

    So the property is measured instead. Build a window whose
    price rises only across sessions 1->3 and is flat
    afterwards: early3 must see the whole move and late_drift
    must see none of it. If the two ever share a session again,
    late_drift picks up part of the rise and this fails.
    """
    import datetime as _dt
    d0 = _dt.date(2024, 1, 1)
    px = []
    for i in range(41):
        # announcement close is index 20; the rise happens on
        # sessions 21, 22 and 23 and then the price is flat
        lvl = 100.0 if i <= 20 else (100.0 + min(i - 20, 3) * 5)
        px.append({"d": str(d0 + _dt.timedelta(days=i)),
                   "c": lvl, "v": 1000})
    v = {"market": "Taiwan", "action": "ADD", "code": "TEST",
         "rev": "May24", "ann": px[20]["d"], "eff": px[40]["d"],
         "px": px, "_ix": {}, "_ix_symbol": None}
    m = Q.metrics(v)
    assert m is not None
    # early3 runs day+1 -> day+3, so it starts AFTER the first
    # session of the rise: 115/105 - 1, not the full 15%.
    assert abs(m["early3"] - (115 / 105 - 1)) < 1e-9, m["early3"]
    assert abs(m["late_drift"]) < 1e-9, \
        f"late_drift saw {m['late_drift']:+.4%} of a move that " \
        f"finished before its window opened — the two legs " \
        f"overlap again"
    # and Q9 must be reading the non-overlapping one
    src = (ROOT / "scripts" / "index_strategist_qa.py").read_text(
        encoding="utf-8")
    assert 'r["fav_late"]' in src


def test_q9_reports_both_correlations():
    """The artifact column stays, labelled, because seeing 0.44
    next to 0.02 is what teaches the reader the difference."""
    _rows, by = _panel()
    _t, _w, tbl, _r = Q.q9_early_signal(by)
    assert tbl
    for r in tbl:
        assert "spearman_early3_vs_LATER_drift" in r
        assert "overlapping_window_rho_ARTIFACT" in r


def test_the_overlap_artifact_is_bigger_than_the_real_signal():
    """Not a law of nature — an observation about THIS panel,
    asserted so that if it ever stops being true somebody looks
    at why."""
    _rows, by = _panel()
    _t, _w, tbl, _r = Q.q9_early_signal(by)
    real = [abs(r["spearman_early3_vs_LATER_drift"]) for r in tbl
            if r["spearman_early3_vs_LATER_drift"] is not None]
    fake = [abs(r["overlapping_window_rho_ARTIFACT"]) for r in tbl
            if r["overlapping_window_rho_ARTIFACT"] is not None]
    assert max(fake) > max(real)
    assert sum(fake) / len(fake) > 2 * (sum(real) / len(real))


def test_survivorship_is_flagged_on_every_row_that_needs_it():
    """Ten of twelve markets are survivors-only. A deletion
    statistic without that flag is the most misleading number
    this panel can produce."""
    _rows, by = _panel()
    for fn in (Q.q3_reversal, Q.q8_asymmetry):
        _t, _w, tbl, _r = fn(by)
        assert tbl
        assert all("delisted_safe" in r for r in tbl)
    assert Q.DELISTED_SAFE == {"Taiwan", "India"}


def test_no_cell_is_built_from_fewer_than_four_events():
    _rows, by = _panel()
    for fn in (Q.q2_when_does_it_move, Q.q3_reversal,
               Q.q4_execution, Q.q5_frontrun):
        _t, _w, tbl, _r = fn(by)
        assert all(r["n"] >= 4 for r in tbl), fn.__name__
