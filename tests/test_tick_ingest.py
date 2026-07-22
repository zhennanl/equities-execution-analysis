"""Tick-file ingester (agents/tick_ingest.py) — LOBSTER/Binance/CSV to the
MarketData contract, with q-xbar-identical bar semantics."""
import numpy as np
import pandas as pd
import pytest

from agents.tick_ingest import (load_lobster, load_binance_trades,
                                load_csv_trades, trades_to_bars,
                                trades_to_daily, market_data_from_trades,
                                to_kdb_csv)


# ── fixtures: tiny synthetic files ─────────────────────────────────────────

@pytest.fixture
def lobster_file(tmp_path):
    # time_s, type, order_id, size, price(x10000), direction — no header.
    # types: 1=submit, 3=cancel, 4=exec visible, 5=exec hidden
    rows = [
        (34200.10, 1, 11, 100, 1_001_000, 1),     # submit  (ignored)
        (34200.50, 4, 11, 100, 1_001_000, 1),     # exec @ 100.10
        (34260.00, 5,  0,  50, 1_002_500, -1),    # hidden exec @ 100.25
        (34500.00, 3, 12, 200, 1_000_000, 1),     # cancel  (ignored)
        (34799.90, 4, 13, 300, 1_000_500, -1),    # exec @ 100.05
    ]
    p = tmp_path / "AAPL_message_10.csv"
    pd.DataFrame(rows).to_csv(p, header=False, index=False)
    return p


@pytest.fixture
def binance_file(tmp_path):
    # trades format, 7 cols, no header, epoch ms
    base = 1_750_000_000_000                       # ms — 2025-06-15-ish
    rows = [(i, 100.0 + i, 0.5 + i, 50.0, base + i * 60_000, True, True)
            for i in range(10)]
    p = tmp_path / "BTCUSDT-trades-2025-06.csv"
    pd.DataFrame(rows).to_csv(p, header=False, index=False)
    return p


# ── parsers ────────────────────────────────────────────────────────────────

def test_lobster_keeps_only_executions_and_scales_price(lobster_file):
    t = load_lobster(lobster_file, "AAPL", "2012-06-21")
    assert len(t) == 3                              # types 4/5 only
    assert t["price"].tolist() == [100.10, 100.25, 100.05]
    assert t["sym"].unique().tolist() == ["AAPL"]
    assert t["time"].iloc[0] == pd.Timedelta(seconds=34200.5)
    assert (t["date"] == pd.Timestamp("2012-06-21")).all()


def test_binance_headerless_ms_epoch(binance_file):
    t = load_binance_trades(binance_file, "BTCUSDT")
    assert len(t) == 10
    assert t["price"].iloc[0] == 100.0 and t["size"].iloc[0] == 0.5
    assert t["date"].nunique() == 1                # all within one hour
    assert t["time"].is_monotonic_increasing


def test_binance_microsecond_epoch_detected(tmp_path):
    base = 1_750_000_000_000_000                   # us
    rows = [(1, 50.0, 2.0, 100.0, base, False, True)]
    p = tmp_path / "t.csv"
    pd.DataFrame(rows).to_csv(p, header=False, index=False)
    t = load_binance_trades(p, "X")
    assert t["date"].iloc[0].year == 2025          # not year 57k


def test_generic_csv_with_mapping(tmp_path):
    df = pd.DataFrame({"ts": ["2026-07-01 09:30:00", "2026-07-01 09:31:00"],
                       "px": [10.0, 10.1], "quantity": [100, 200]})
    p = tmp_path / "g.csv"; df.to_csv(p, index=False)
    t = load_csv_trades(p, "SYN", "ts", "px", "quantity")
    assert len(t) == 2 and t["size"].sum() == 300


# ── bar semantics (must match q's xbar) ────────────────────────────────────

def test_trades_to_bars_xbar_semantics(lobster_file):
    t = load_lobster(lobster_file, "AAPL", "2012-06-21")
    bars = trades_to_bars(t, bar_minutes=5)
    # 34200s=09:30:00.5, 34260s=09:31 -> same 09:30 bar; 34799.9s=09:39:59.9 -> 09:35 bar
    assert len(bars) == 2
    b0 = bars.iloc[0]
    assert bars.index[0] == pd.Timestamp("2012-06-21 09:30")
    assert b0["Open"] == 100.10 and b0["Close"] == 100.25
    assert b0["High"] == 100.25 and b0["Volume"] == 150
    assert bars.index[1] == pd.Timestamp("2012-06-21 09:35")


def test_trades_to_daily(lobster_file):
    d = trades_to_daily(load_lobster(lobster_file, "AAPL", "2012-06-21"))
    assert len(d) == 1 and d["Volume"].iloc[0] == 450


# ── assembly ───────────────────────────────────────────────────────────────

def test_market_data_from_trades_contract(lobster_file):
    md = market_data_from_trades(
        load_lobster(lobster_file, "AAPL", "2012-06-21"), "US")
    assert md.ticker == "AAPL"
    assert "tick file" in md.vol_note and "thin" in md.vol_note
    assert md.vol_profile["volume_pct"].sum() == pytest.approx(1.0)
    assert md.adv_shares == 450                    # one day, disclosed thin


def test_external_daily_context_suppresses_thin_warning(lobster_file, tmp_path):
    from tests.conftest import make_daily
    md = market_data_from_trades(
        load_lobster(lobster_file, "AAPL", "2012-06-21"), "US",
        daily=make_daily(60))
    assert "thin" not in md.vol_note
    assert md.adv_shares == pytest.approx(1_000_000.0)


def test_multi_sym_frame_rejected(lobster_file):
    t = load_lobster(lobster_file, "AAPL", "2012-06-21")
    t.loc[1, "sym"] = "MSFT"
    with pytest.raises(ValueError, match="syms"):
        market_data_from_trades(t, "US")


# ── kdb export ─────────────────────────────────────────────────────────────

def test_to_kdb_csv_roundtrip(lobster_file, tmp_path):
    t = load_lobster(lobster_file, "AAPL", "2012-06-21")
    out = tmp_path / "trades.csv"
    snippet = to_kdb_csv(t, out)
    assert "DSTFF" in snippet and "trades.csv" in snippet
    back = pd.read_csv(out)
    assert list(back.columns) == ["date", "sym", "time", "price", "size"]
    assert back["date"].iloc[0] == "2012.06.21"    # q date literal format
    assert back["time"].iloc[0] == "09:30:00.500"  # q time literal format
