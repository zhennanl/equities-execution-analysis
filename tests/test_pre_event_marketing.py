"""Step-1 pre-event marketing generator."""
import pandas as pd

from agents.pre_event_marketing import (EVENTS, boundary_watch,
                                        days_to, render_marketing_md)


def test_events_registry_sanity():
    for name, e in EVENTS.items():
        assert e["provider"] in ("MSCI", "FTSE")
        assert e["engine"] in ("live", "reference", "pit")
        assert pd.Timestamp(e["ann"]) < pd.Timestamp(e["eff"])
        assert e["markets"] and e["note"]
    aug = EVENTS["MSCI Aug-2026 QIR (Asia)"]
    assert aug["review"] == "QIR" and len(aug["markets"]) == 8


def test_days_to():
    assert days_to("2026-08-12", today="2026-07-28") == 15
    assert days_to("2026-07-28", today="2026-07-28") == 0


def _universe():
    return pd.DataFrame([
        # members: 0.55x (near floor, at risk) and 3x (safe)
        {"ticker": "NEAR.TW", "member": 1, "full_mktcap_usd": 5.5e9},
        {"ticker": "SAFE.TW", "member": 1, "full_mktcap_usd": 30e9},
        # non-members: 1.6x (near 1.8x hurdle, at risk) and 0.3x
        {"ticker": "CLOSE.TW", "member": 0, "full_mktcap_usd": 16e9},
        {"ticker": "FAR.TW", "member": 0, "full_mktcap_usd": 3e9},
        {"ticker": "TAIL0", "member": 1, "full_mktcap_usd": 8e9},
    ])


def test_boundary_watch_distances_and_risk():
    b = boundary_watch(_universe(), gmsr=10e9, add_thr=18e9, n=2)
    assert "TAIL0" not in set(b["ticker"])          # tails excluded
    near = b[b["ticker"] == "NEAR.TW"].iloc[0]
    assert near["side"] == "member"
    assert near["at_risk"]                          # +10% above floor
    assert "+10% above floor" == near["distance"]
    close = b[b["ticker"] == "CLOSE.TW"].iloc[0]
    assert close["at_risk"]                         # -11% vs hurdle
    far = b[b["ticker"] == "FAR.TW"].iloc[0]
    assert not far["at_risk"]


def test_render_marketing_md_honesty_content():
    calls = pd.DataFrame()          # zero-call market
    res = [{"market": "Taiwan", "gmsr_usd": 10e9,
            "add_threshold_usd": 18e9, "calls": calls,
            "violations": [],
            "history": {"MSCI Sell": {"available": True, "n": 8,
                                      "median": 16.0, "min": 7.1,
                                      "max": 38.1},
                        "MSCI Buy": {"available": False}},
            "track_record": pd.DataFrame([{"claim": "adds",
                                           "record": "17/17"}])}]
    b = {"Taiwan": boundary_watch(_universe(), 10e9, 18e9, n=2)}
    md = render_marketing_md("MSCI Aug-2026 QIR (Asia)",
                             EVENTS["MSCI Aug-2026 QIR (Asia)"],
                             res, b, {"NEAR": "HIGH (+40%/9obs)"},
                             "2026-07-28")
    assert "No calls." in md                        # zero-call stated
    assert "Boundary watch" in md
    assert "HIGH (+40%/9obs)" in md                 # crowding joined
    assert "no measured events" in md               # absent class
    assert "honesty box" in md.lower()
    assert "NO-CALL" in md and "17/17" in md
    assert "T-15" in md                             # countdown at prep


def test_pit_universe_uses_pre_may_membership():
    """2324.TW (Compal) was DELETED in May: pre-May member=1, and
    post-May member=0 — the PIT frame must not know the future."""
    from scripts.run_full_review_asia import (pit_universe,
                                              post_may_universe)
    pit = pit_universe("Taiwan")
    post = post_may_universe("Taiwan")
    assert int(pit.loc[pit["ticker"] == "2324.TW", "member"].iloc[0]) == 1
    assert int(post.loc[post["ticker"] == "2324.TW", "member"].iloc[0]) == 0


def test_pit_screen_migration_deletes_taiwan():
    """The graded config: count-anchored tails + segment-migration
    rule -> the seven actual TW deletions all flag."""
    from scripts.pit_may2026_asia import ACTUAL
    from scripts.run_full_review_asia import pit_screen, pit_universe
    u = pit_universe("Taiwan")
    s = pit_screen("Taiwan", u)
    dels = set(s["deletes"]["ticker"])
    assert ACTUAL["Taiwan"]["dels"] <= dels          # 7/7 recall
    assert set(s["adds"]["ticker"]) == {"6223.TWO"}  # MPI only
    assert s["gmsr"] > 0 and s["add_thr"] > s["gmsr"]


def test_grade_predictions_math():
    from agents.pre_event_marketing import grade_predictions
    calls = pd.DataFrame([
        {"call": "ADD", "ticker": "A"},
        {"call": "DELETE", "ticker": "B"},
        {"call": "DELETE", "ticker": "C"},   # false flag
        {"call": "BLOCKED", "ticker": "Z"}])
    res = [{"market": "Taiwan", "calls": calls}]
    g = grade_predictions(res, {"Taiwan": {"adds": {"A"},
                                           "dels": {"B", "D"}}})
    r = g.iloc[0]
    assert r["adds"] == "1/1" and r["deletes"] == "1/2"
    assert r["del_false+"] == 1
    assert "D" in r["missed"] and "C" in r["false_flags"]


def test_methodology_covers_all_layers():
    from agents.pre_event_marketing import METHODOLOGY
    for k in ("prediction", "crowding", "flows", "probabilities"):
        assert len(METHODOLOGY[k]) > 100
    assert "Feng Tay" in METHODOLOGY["prediction"]
    assert "EXITING" in METHODOLOGY["crowding"]
    assert "5" in METHODOLOGY["flows"]
