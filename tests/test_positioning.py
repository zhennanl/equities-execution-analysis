"""Positioning check (agents/positioning.py)."""
from types import SimpleNamespace

import numpy as np
import pytest

from agents.positioning import (positioning_footprint,
                                positioning_sources_table,
                                short_interest_snapshot)


def _es(ab_pre, car_pre, adv=1_000_000.0):
    """Event window rel -len..+2 with given pre-effective ab_vol/car."""
    n_pre = len(ab_pre)
    rel = np.arange(-n_pre, 3)
    ab = np.concatenate([ab_pre, [5.0, 1.0, 1.0]])
    car = np.concatenate([car_pre, [car_pre[-1]] * 3])
    return SimpleNamespace(rel_days=rel, ab_vol=ab, car=car,
                           est_avg_volume=adv)


def test_heavy_footprint_with_drift():
    # 5 pre days at 2x volume -> 5 ADV-days excess; CAR drifts +4%
    es = _es([2.0] * 6, list(np.linspace(0, 0.04, 6)))
    f = positioning_footprint(es)
    assert f.available and f.verdict == "HEAVY"
    assert f.excess_adv_days == pytest.approx(6.0)
    assert f.est_prepositioned_shares == pytest.approx(3_000_000.0)  # 50% share
    assert f.car_drift == pytest.approx(0.04)


def test_excess_volume_without_drift_downgrades():
    es = _es([2.0] * 6, [0.0] * 6)                 # volume but no drift
    f = positioning_footprint(es)
    assert f.verdict == "MODERATE"                 # not HEAVY without confirm
    assert "does NOT corroborate" in f.detail


def test_quiet_tape_is_light():
    es = _es([1.05] * 6, list(np.linspace(0, 0.005, 6)))
    f = positioning_footprint(es)
    assert f.verdict == "LIGHT"
    assert f.excess_adv_days == pytest.approx(0.3, abs=0.01)


def test_announcement_rel_narrows_window():
    ab = [3.0, 3.0, 1.0, 1.0, 2.0, 2.0]            # early spike unrelated
    es = _es(ab, list(np.linspace(0, 0.03, 6)))
    full = positioning_footprint(es)
    narrow = positioning_footprint(es, announcement_rel=-2)
    assert narrow.excess_adv_days < full.excess_adv_days
    assert narrow.window == "T-2..T-1"


def test_short_window_unavailable():
    es = SimpleNamespace(rel_days=np.array([-1, 0, 1]),
                         ab_vol=np.ones(3), car=np.zeros(3),
                         est_avg_volume=1e6)
    assert not positioning_footprint(es).available


def test_sources_table_covers_key_markets():
    df = positioning_sources_table()
    mkts = set(df["Market"])
    for m in ("Japan (TSE)", "Taiwan (TWSE)", "Korea (KRX)",
              "Hong Kong (HKEX)", "US"):
        assert m in mkts
    assert df["Access"].str.contains("free").sum() >= 10
    assert (df["Access"].str.contains("NOT public")).any()   # honesty row


def test_short_interest_snapshot_with_injected_info():
    info = {"sharesShort": 1_100_000, "sharesShortPriorMonth": 900_000,
            "shortRatio": 2.5, "shortPercentOfFloat": 0.031}
    s = short_interest_snapshot("TEST", info_fn=lambda t: info)
    assert s["available"] and s["chg_mom"] == pytest.approx(0.222, abs=1e-3)
    assert "BUILDING" in s["signal"]


def test_short_interest_snapshot_non_us_degrades():
    s = short_interest_snapshot("2330.TW", info_fn=lambda t: {})
    assert not s["available"] and "per-market official sources" in s["reason"]
