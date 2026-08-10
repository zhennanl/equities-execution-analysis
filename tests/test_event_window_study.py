"""c-128 pins: the announcement->effective framework.

What must never drift: the day-0 timing convention (one day of
error contaminates every baseline), the delisted-safe coverage
claims, the registered constants, and the honesty of the
skipped-windows ledger.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
W = ROOT / "data" / "tw_event_windows.json"
M = ROOT / "data" / "event_window_metrics.json"


def test_timing_convention_pinned():
    src = (ROOT / "scripts" / "tw_event_window.py").read_text(
        encoding="utf-8")
    assert "day0 = announcement-date Taipei close" in \
        json.loads(W.read_text(encoding="utf-8"))["convention"] if W.exists() \
        else "23:00 CET" in src
    assert "05:00" in src and "pre-news" in src.lower()


@pytest.mark.skipif(not W.exists(), reason="no windows")
def test_windows_shape_and_baseline():
    w = json.loads(W.read_text(encoding="utf-8"))["windows"]
    assert len(w) >= 20
    for v in list(w.values())[:10]:
        if not v["px"]:
            continue                    # TPEx pending, allowed
        dts = [r["d"] for r in v["px"]]
        assert dts == sorted(dts)
        # window must span pre-announcement to post-effective
        assert dts[0] < v["ann"] < v["eff"] <= dts[-1] or \
            v["eff"] <= dts[-1]
        assert all(r["c"] > 0 for r in v["px"])


@pytest.mark.skipif(not M.exists(), reason="no metrics")
def test_metrics_and_registered_constants():
    m = json.loads(M.read_text(encoding="utf-8"))
    c = m["constants"]
    assert c["tracking_aum_usd_b"] == 180.0
    assert "registered" in c["note"]
    assert m["n_analyzed"] >= 20
    # skipped windows are LISTED, not vanished
    assert isinstance(m["skipped"], list)
    for r in m["windows"][:10]:
        assert r["label"] in ("CLEAN-DRIFT", "FRONT-RUN-FADE",
                              "SQUEEZE", "QUIET", "MIXED")
        assert 0 <= r["PRE"] <= 1
    # both playbook sides present with medians
    for act in ("ADD", "DEL"):
        assert m["playbook"][act]["n"] > 0
        assert m["playbook"][act]["drift"] is not None


@pytest.mark.skipif(not M.exists(), reason="no metrics")
def test_del_drift_sign_sanity():
    """Deletions should drift DOWN into effective on median —
    if this flips, either the market changed or the window
    indexing broke; both deserve a loud failure."""
    m = json.loads(M.read_text(encoding="utf-8"))
    assert m["playbook"]["DEL"]["drift"] < 0
    assert m["playbook"]["ADD"]["drift"] > 0


def test_live_loop_declares_shortlist():
    from event_window_live import ANN, EFF, SHORTLIST
    assert ANN == "2026-08-11" and EFF == "2026-08-31"
    assert "2408" in SHORTLIST["ADD"]
    assert "2615" in SHORTLIST["DEL"]
    assert "6505" in SHORTLIST["BLOCKED"]


def test_hidden_pages_stay_hidden():
    src = (ROOT / "app.py").read_text(encoding="utf-8")
    radio = src.split('st.sidebar.radio("Page"')[1].split("])")[0]
    assert "Cutoff Framework" not in radio
    assert "Reconstruction (PIT)" not in radio
    # c-303, Bill took this page off the site too, so it joins
    # the hidden list rather than contradicting it. Same rule as
    # the others: the MODULE stays, with its tests, and app.py
    # still names it so a reader can find where it went.
    assert "Announcement → Effective" not in radio
    assert (ROOT / "views" / "event_window_study.py").exists()
    assert "event_window_study" in src
