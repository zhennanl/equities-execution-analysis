"""Agent 11 — live alert engine (pure threshold function build_live_alerts)."""
from agents.agent11_live_snapshot import build_live_alerts


def _sev_by_rule(alerts):
    return {a.rule: a.severity for a in alerts}


def test_behind_pace_fires_high_when_far_behind():
    # 50% elapsed, only 10% filled => 40 pts behind => HIGH (> 2*10)
    alerts = build_live_alerts(filled_shares=100, order_shares=1000,
                               elapsed_frac=0.5, algo_name="VWAP")
    assert _sev_by_rule(alerts).get("Completion pace") == "HIGH"


def test_pace_alert_suppressed_for_auction_and_frontloaded_algos():
    for algo in ("MOC", "MOO", "IS"):
        alerts = build_live_alerts(filled_shares=0, order_shares=1000,
                                   elapsed_frac=0.9, algo_name=algo)
        assert "Completion pace" not in _sev_by_rule(alerts)


def test_on_pace_order_has_no_pace_alert():
    alerts = build_live_alerts(filled_shares=520, order_shares=1000,
                               elapsed_frac=0.5, algo_name="VWAP")
    assert "Completion pace" not in _sev_by_rule(alerts)


def test_participation_breach_is_high():
    alerts = build_live_alerts(filled_shares=500, order_shares=1000,
                               elapsed_frac=0.5, algo_name="POV",
                               last_bar_participation_pct=18.0, cap_pct=15.0)
    assert _sev_by_rule(alerts).get("Participation breach") == "HIGH"


def test_limit_through_market_alert():
    alerts = build_live_alerts(filled_shares=500, order_shares=1000,
                               elapsed_frac=0.5, algo_name="VWAP",
                               limit_price=100.0, current_price=101.5)
    assert "Limit through market" in _sev_by_rule(alerts)


def test_vpin_high_vs_elevated_severity():
    hi = build_live_alerts(filled_shares=500, order_shares=1000, elapsed_frac=0.5,
                           algo_name="VWAP", vpin_label="High")
    el = build_live_alerts(filled_shares=500, order_shares=1000, elapsed_frac=0.5,
                           algo_name="VWAP", vpin_label="Elevated")
    assert _sev_by_rule(hi).get("Order-flow toxicity") == "MEDIUM"
    assert _sev_by_rule(el).get("Order-flow toxicity") == "INFO"


def test_benchmark_slippage_thresholds():
    hi = build_live_alerts(filled_shares=500, order_shares=1000, elapsed_frac=0.5,
                           algo_name="VWAP", slip_vs_benchmark_bps=60.0)
    med = build_live_alerts(filled_shares=500, order_shares=1000, elapsed_frac=0.5,
                            algo_name="VWAP", slip_vs_benchmark_bps=30.0)
    lo = build_live_alerts(filled_shares=500, order_shares=1000, elapsed_frac=0.5,
                           algo_name="VWAP", slip_vs_benchmark_bps=10.0)
    assert _sev_by_rule(hi).get("Benchmark slippage") == "HIGH"
    assert _sev_by_rule(med).get("Benchmark slippage") == "MEDIUM"
    assert "Benchmark slippage" not in _sev_by_rule(lo)


def test_reconsider_emits_info_recheck():
    alerts = build_live_alerts(filled_shares=500, order_shares=1000,
                               elapsed_frac=0.5, algo_name="VWAP",
                               reconsider=True)
    assert _sev_by_rule(alerts).get("Strategy re-check") == "INFO"


def test_clean_state_has_no_alerts():
    alerts = build_live_alerts(filled_shares=500, order_shares=1000,
                               elapsed_frac=0.5, algo_name="VWAP")
    assert alerts == []
