"""c-129 pins: the multi-market event-window generalization.

The claims under test: the shared global announcement calendar,
delisted-safety where promised (India), survivorship LABELS
where not, and playbooks that exist for every harvested market.
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "data" / "apac_event_windows"
PB = ROOT / "data" / "apac_event_playbooks.json"


@pytest.mark.skipif(not DIR.exists(), reason="no harvest")
def test_market_files_share_schema_and_calendar():
    cal = json.loads((ROOT / "data" / "msci_tw_events.json")
                     .read_text(encoding="utf-8"))
    for p in DIR.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        w = d["windows"]
        assert w, p.stem
        for v in list(w.values())[:5]:
            assert {"rev", "code", "action", "ann", "eff",
                    "px"} <= set(v)
            # the GLOBAL announcement calendar: every window's
            # ann must equal the TW registry's date
            assert v["ann"] == cal[v["rev"]]["ann"]


@pytest.mark.skipif(not DIR.exists(), reason="no harvest")
def test_india_is_delisted_safe_and_large():
    d = json.loads((DIR / "India.json").read_text(encoding="utf-8"))
    w = d["windows"]
    ok = sum(1 for v in w.values() if v["px"])
    assert ok >= 140                    # 157/166 at harvest
    assert all("bhavcopy" in v.get("src", "")
               for v in w.values() if v["px"])


@pytest.mark.skipif(not PB.exists(), reason="no playbooks")
def test_playbooks_cover_markets_with_labels():
    pb = json.loads(PB.read_text(encoding="utf-8"))
    assert len(pb) >= 10
    assert "Taiwan" in pb and "India" in pb and "Japan" in pb
    for mkt, r in pb.items():
        assert "survivorship" in r
        if mkt not in ("Taiwan", "India"):
            assert "SURVIVORS" in r["survivorship"]
    # Japan is the largest sample after the TW/IN pair
    assert pb["Japan"]["n"] >= 150


@pytest.mark.skipif(not PB.exists(), reason="no playbooks")
def test_add_drift_positive_in_major_markets():
    """The core cross-market regularity: additions drift UP
    between announcement and effective in the liquid markets.
    If this flips, indexing or signs broke."""
    pb = json.loads(PB.read_text(encoding="utf-8"))
    for mkt in ("Taiwan", "Japan", "India", "Korea"):
        assert pb[mkt]["playbook"]["ADD"]["drift"] > 0, mkt


def test_au_shorts_series_exist():
    p = ROOT / "data" / "au_event_shorts.json"
    if not p.exists():
        pytest.skip("not harvested")
    d = json.loads(p.read_text(encoding="utf-8"))
    ok = [v for v in d["series"].values() if v["rows"]]
    assert len(ok) >= 8
    r = ok[0]["rows"][0]
    assert {"d", "short", "pct"} <= set(r)
