"""Step-4 execution insights — deterministic grading behavior."""
import pandas as pd

from agents.execution_insights import (discretion_counterfactual,
                                       render_debrief, reversal_grade,
                                       tca_vs_estimate, update_priors)


def test_tca_sign_convention_and_verdicts():
    """Positive bps = cost: buy above close costs, sell below close
    costs; the vs-estimate delta drives the verdict."""
    lines = pd.DataFrame([
        # sell 0.9992 of close = -8 bps price = +8 bps cost vs 12 est
        {"ticker": "A", "side": "Sell", "qty_shares": 100,
         "avg_px": 99.92, "close_px": 100.0, "est_cost_bps": 12.0},
        # buy at 1.005 of close = 50 bps cost vs 10 est -> WORSE
        {"ticker": "B", "side": "Buy", "qty_shares": 100,
         "avg_px": 100.50, "close_px": 100.0, "est_cost_bps": 10.0},
        # sell ABOVE close = negative cost -> BETTER
        {"ticker": "C", "side": "Sell", "qty_shares": 100,
         "avg_px": 100.30, "close_px": 100.0, "est_cost_bps": 10.0},
    ])
    t = tca_vs_estimate(lines)
    assert abs(t.iloc[0]["realized_bps"] - 8.0) < 0.1
    assert t.iloc[0]["verdict"] == "WITHIN estimate"
    assert t.iloc[1]["verdict"] == "WORSE than estimate"
    assert t.iloc[2]["realized_bps"] < 0
    assert t.iloc[2]["verdict"] == "BETTER than estimate"
    assert "portfolio_realized_bps" in t.attrs


def test_counterfactual_worked_and_hypothetical():
    d = pd.DataFrame([
        # sell worked 30% ahead of a -100 bps fall -> +30 gain CORRECT
        {"ticker": "A", "side": "Sell", "decision": "WORK AHEAD 30%",
         "worked_frac": 0.3, "pre_close_drift_bps": -100.0},
        # sell worked ahead of a +100 rise -> -30 INCORRECT
        {"ticker": "B", "side": "Sell", "decision": "WORK AHEAD 30%",
         "worked_frac": 0.3, "pre_close_drift_bps": 100.0},
        # buy pre-positioned ahead of a rise -> CORRECT
        {"ticker": "C", "side": "Buy", "decision": "PRE-POSITION",
         "worked_frac": 0.3, "pre_close_drift_bps": 100.0},
        # WAIT graded hypothetically: price fell -> working would
        # have helped a sell
        {"ticker": "D", "side": "Sell",
         "decision": "WAIT — MOC the full order",
         "worked_frac": 0.0, "pre_close_drift_bps": -100.0},
        # MOC ONLY, price rose into close -> staying was right (sell)
        {"ticker": "E", "side": "Sell", "decision": "MOC ONLY",
         "worked_frac": 0.0, "pre_close_drift_bps": 100.0},
    ])
    cf = discretion_counterfactual(d)
    assert list(cf["verdict"]) == [
        "CORRECT", "INCORRECT", "CORRECT",
        "WORKING WOULD HAVE HELPED", "staying MOC was right"]
    assert cf.iloc[0]["cf_gain_bps"] == 30.0


def test_reversal_grade_and_hit_rate_excludes_no_data():
    n = pd.DataFrame([
        # HIGH crowd delete, -500 T move, +200 bounce -> AGREE
        {"ticker": "A", "crowding_band": "HIGH",
         "t_move_bps": -500.0, "post_reversal_bps": 200.0},
        # HIGH crowd, no bounce -> DISAGREE
        {"ticker": "B", "crowding_band": "HIGH",
         "t_move_bps": -500.0, "post_reversal_bps": -20.0},
        # LOW crowd, modest reversal -> AGREE
        {"ticker": "C", "crowding_band": "LOW",
         "t_move_bps": -300.0, "post_reversal_bps": 30.0},
        # NO DATA -> ungraded, excluded from hit rate
        {"ticker": "D", "crowding_band": "NO",
         "t_move_bps": -300.0, "post_reversal_bps": 300.0},
    ])
    r = reversal_grade(n)
    assert list(r["grade"]) == ["AGREE", "DISAGREE", "AGREE", "AGREE"]
    assert r.attrs["hit_rate"] == "2/3"
    assert "ungraded" in r.iloc[3]["expected"]


def test_update_priors_before_after():
    cache = {"events": [{"t_mult": 10.0, "auction_share": 0.3,
                         "reversal_frac": 0.5},
                        {"t_mult": 20.0, "auction_share": 0.4,
                         "reversal_frac": 0.6}]}
    out = update_priors(cache, [{"provider": "MSCI", "side": "Sell",
                                 "t_mult": 30.0,
                                 "auction_share": None,
                                 "reversal_frac": 0.7}])
    tm = out[out["prior"] == "t_mult"].iloc[0]
    assert tm["before_median"] == 15.0 and tm["after_median"] == 20.0
    assert tm["n_after"] == 3
    aus = out[out["prior"] == "auction_share"].iloc[0]
    assert aus["n_after"] == 2          # None not appended to stats
    assert len(cache["events"]) == 3    # event joined the library


def test_render_debrief_sections():
    tca = tca_vs_estimate(pd.DataFrame([
        {"ticker": "A", "side": "Sell", "qty_shares": 100,
         "avg_px": 99.9, "close_px": 100.0, "est_cost_bps": 10.0}]))
    cf = discretion_counterfactual(pd.DataFrame([
        {"ticker": "A", "side": "Sell", "decision": "MOC ONLY",
         "worked_frac": 0.0, "pre_close_drift_bps": 50.0}]))
    rev = reversal_grade(pd.DataFrame([
        {"ticker": "A", "crowding_band": "LOW",
         "t_move_bps": -100.0, "post_reversal_bps": 10.0}]))
    pri = update_priors({"events": []},
                        [{"t_mult": 16.0, "auction_share": 0.3,
                          "reversal_frac": 0.5}])
    md = render_debrief(tca, cf, rev, pri, "T", "2026-07-28", "n")
    for s in ("4.2 TCA", "4.4a Discretion", "4.4b Reversal",
              "4.5 Priors", "hit rate", "Misses ship"):
        assert s in md
