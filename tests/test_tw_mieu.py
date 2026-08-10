"""c-123 pins: the full §2.2 screen chain (MIEU build).

The contract under test: every screen either fires with data or
is DECLARED not-evaluated — no screen silently passes for lack
of input. That is the difference between a universe built the
rulebook's way and a universe that merely looks like one.
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
M = ROOT / "data" / "tw_mieu_universe.json"


@pytest.mark.skipif(not M.exists(), reason="no MIEU build")
def test_screen_accounting_is_complete():
    m = json.loads(M.read_text(encoding="utf-8"))
    d = m["screens_dropped"]
    # size dominates by an order of magnitude — Taiwan has
    # ~1,500 listed companies below $537M
    assert d["size"] > 1000
    assert d["size"] > 10 * sum(v for k, v in d.items()
                                if k != "size")
    # the not-evaluated ledger must exist and be explicit
    ne = m["not_evaluated"]
    assert "financial_reporting" in ne
    assert "NOT_EVALUATED" in str(ne["financial_reporting"])


@pytest.mark.skipif(not M.exists(), reason="no MIEU build")
def test_universe_shape_and_crossing():
    m = json.loads(M.read_text(encoding="utf-8"))
    assert 350 <= m["mieu_n"] <= 550
    c = m["crossing"]
    # the crossing must sit in the neighbourhood of MSCI's
    # published answer (rank 77) — wide band on purpose; this
    # pins sanity, not success
    assert 50 <= c["rank"] <= 110
    assert 4.0 <= c["cutoff_usd_b"] <= 12.0
    # universe float within/near the factsheet-implied band
    assert 2500 <= m["universe_float_usd_b"] <= 4500


@pytest.mark.skipif(not M.exists(), reason="no MIEU build")
def test_walk_is_full_cap_sorted_and_float_cumulated():
    m = json.loads(M.read_text(encoding="utf-8"))
    caps = [v["cap"] for v in m["universe"].values()]
    assert caps == sorted(caps, reverse=True)
    for v in list(m["universe"].values())[:50]:
        assert abs(v["fcap"] - v["cap"] * v["ff"]) < 0.01


@pytest.mark.skipif(not M.exists(), reason="no MIEU build")
def test_float_sources_are_tiered():
    m = json.loads(M.read_text(encoding="utf-8"))
    srcs = {v["src"] for v in m["universe"].values()}
    assert "factsheet-implied" in srcs
    # calibration metadata must ride along
    assert m["float_calibration"]["n_overlap"] >= 20
    assert m["float_calibration"]["tdcc_scale"] > 1.0
