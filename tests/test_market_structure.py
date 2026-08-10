"""Market-structure fingerprint & drift (agents/market_structure.py)."""
import numpy as np
import pandas as pd
import pytest

from agents.market_structure import (structure_fingerprint, describe_fingerprint,
                                     structure_drift, record_fingerprint,
                                     MARKET_STRUCTURE_NOTES,
                                     StructureFingerprint)


def _md(close_frac=0.15, u_mult=3.0, n_days=5, bars=66, seed=2):
    """Synthetic MarketData with planted structure: U-shaped volume with a
    close-auction spike and noisy prices."""
    from agents.agent1_market_data import MarketData
    rng = np.random.RandomState(seed)
    frames = []
    for d in pd.bdate_range("2026-06-01", periods=n_days):
        idx = pd.date_range(d + pd.Timedelta(hours=9, minutes=30),
                            periods=bars, freq="5min")
        c = 100 * np.exp(np.cumsum(rng.randn(bars) * 0.001))
        k = bars // 6
        v = np.full(bars, 1000.0)
        v[:k] *= u_mult
        v[-k:] *= u_mult
        v[-1] = v.sum() * close_frac / (1 - close_frac)   # close spike
        frames.append(pd.DataFrame({"Open": c, "High": c * 1.001,
                                    "Low": c * 0.999, "Close": c,
                                    "Volume": v}, index=idx))
    intra = pd.concat(frames)
    nd = 40
    dc = 100 * np.exp(np.cumsum(rng.randn(nd) * 0.012))
    daily = pd.DataFrame({"Open": dc * (1 + rng.randn(nd) * 0.006),
                          "High": dc * 1.02, "Low": dc * 0.98, "Close": dc,
                          "Volume": np.full(nd, 5e6)},
                         index=pd.bdate_range("2026-04-06", periods=nd))
    return MarketData(ticker="SYN", market="Taiwan (TWSE)", intraday=intra,
                      daily=daily, adv_shares=5e6, adv_usd=5e8,
                      current_price=float(dc[-1]), realized_vol_ann=0.2,
                      vol_profile=pd.DataFrame(), shares_outstanding=None,
                      rv_intraday_ann=None, vol_note="")


def test_fingerprint_recovers_planted_structure():
    fp = structure_fingerprint(_md(close_frac=0.15, u_mult=3.0))
    assert fp.available
    assert fp.close_share == pytest.approx(0.15, abs=0.02)
    assert fp.u_shape > 1.8
    assert fp.variance_ratio is not None and fp.variance_ratio > 0
    assert fp.autocorr_1 is not None
    assert 0 <= fp.overnight_var_share <= 1


def test_words_reflect_the_numbers():
    hot = structure_fingerprint(_md(close_frac=0.18))
    assert "auction-dominated" in hot.words
    quiet = structure_fingerprint(_md(close_frac=0.02, u_mult=1.0))
    assert "spread through the day" in quiet.words


def test_short_history_unavailable():
    md = _md(n_days=1)
    md.daily = md.daily.iloc[:10]
    assert not structure_fingerprint(md).available


def test_drift_flags_structural_moves_only():
    a = {"close_share": 0.10, "u_shape": 2.0, "roll_spread_bps": 10.0,
         "variance_ratio": 1.0, "autocorr_1": -0.02,
         "overnight_var_share": 0.30, "amihud_bps_per_musd": 2.0}
    b = dict(a, close_share=0.16, roll_spread_bps=15.0)   # +6pp, +50%
    hits = structure_drift(a, b)
    assert any("close_share" in h for h in hits)
    assert any("roll_spread_bps" in h for h in hits)
    assert not any("u_shape" in h for h in hits)          # unchanged
    assert structure_drift(a, a) == []


def test_record_fingerprint_roundtrip(tmp_path):
    fp = structure_fingerprint(_md())
    p = tmp_path / "lib.json"
    record_fingerprint(fp, p)
    record_fingerprint(fp, p)
    import json
    lib = json.loads(p.read_text(encoding="utf-8"))
    assert len(lib) == 2 and lib[0]["market"] == "Taiwan (TWSE)"
    assert "words" not in lib[0]                          # numbers only stored


def test_notes_cover_platform_asia_markets():
    for m in ("Japan (TSE)", "Hong Kong (HKEX)", "China-A Shanghai",
              "Taiwan (TWSE)", "Korea (KRX)", "India (NSE)"):
        assert m in MARKET_STRUCTURE_NOTES
        assert len(MARKET_STRUCTURE_NOTES[m]) > 100
    assert "Nextrade" in MARKET_STRUCTURE_NOTES["Korea (KRX)"]
    assert "program-trading rules" in MARKET_STRUCTURE_NOTES["China-A Shanghai"]
