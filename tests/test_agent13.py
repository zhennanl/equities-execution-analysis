"""Agent 13 — venue routing / SOR statistical simulation.

Anchors (docs/HANDOFF_2026-07-08.md §6): on a US schedule with half-spread 2.0,
Cost-optimized routes materially to dark and beats Lit-only (0% dark); a
single-venue market (Taiwan) routes 100% to the primary."""
import numpy as np
import pandas as pd
import pytest

from agents.agent13_venue_router import (
    route_order, compare_policies, venues_for, VenueProfile,
)


def _us_schedule(n=20, shares_per_bar=1000.0):
    idx = pd.date_range("2026-06-15 09:30", periods=n, freq="5min")
    return pd.DataFrame({"time": idx,
                         "shares_traded": np.full(n, shares_per_bar),
                         "price": np.full(n, 100.0)})


def _bar_volumes(n=20, vol=100_000.0):
    return np.full(n, vol)


def test_cost_optimized_uses_dark_and_beats_lit_only():
    sched, vols = _us_schedule(), _bar_volumes()
    cmp = compare_policies(sched, vols, "US", half_spread_bps=2.0)
    row = {r["Policy"]: r for _, r in cmp.iterrows()}
    assert row["Lit-only"]["% dark"] == 0.0
    assert row["Cost-optimized"]["% dark"] > 0.0
    assert (row["Cost-optimized"]["Blended routing cost (bps)"]
            < row["Lit-only"]["Blended routing cost (bps)"])


def test_expected_venue_cost_formula():
    # spread_capture*half + fee + adverse_selection
    v = VenueProfile("x", "lit", fee_bps=0.25, volume_share=0.2, fill_prob=1.0,
                     spread_capture=1.0, adverse_selection_bps=0.1)
    assert v.expected_cost_bps(2.0) == pytest.approx(2.35)


def test_lit_only_excludes_dark_venues():
    vs = venues_for("US", allow_dark=False)
    assert all(v.kind != "dark" for v in vs)


def test_single_venue_market_routes_100pct_primary():
    sched, vols = _us_schedule(), _bar_volumes()
    r = route_order(sched, vols, "Taiwan (TWSE)", policy="Cost-optimized")
    assert len(r.venue_summary) == 1
    assert r.venue_summary.iloc[0]["% of order"] == pytest.approx(100.0)
    assert any("single-venue" in n for n in r.notes)


def test_high_half_spread_is_capped_with_note():
    sched, vols = _us_schedule(), _bar_volumes()
    r = route_order(sched, vols, "US", half_spread_bps=99.0)
    assert r.half_spread_bps == 15.0                      # ROUTING_SPREAD_CAP_BPS
    assert any("capped" in n for n in r.notes)


def test_all_scheduled_shares_are_routed():
    sched, vols = _us_schedule(), _bar_volumes()
    r = route_order(sched, vols, "US", policy="Cost-optimized", half_spread_bps=2.0)
    assert r.routed_shares == pytest.approx(sched["shares_traded"].sum(), rel=1e-6)


# ---------------------------------------------------------------- Shield

def test_shield_routes_all_shares_and_uses_more_dark():
    sched, vols = _us_schedule(), _bar_volumes()
    cmp = compare_policies(sched, vols, "US", half_spread_bps=2.0)
    row = {r["Policy"]: r for _, r in cmp.iterrows()}
    assert "Shield (dark-patient)" in row
    # carry-forward re-pings dark, so the dark share must exceed the
    # same-bar-sweep Cost-optimized policy
    assert row["Shield (dark-patient)"]["% dark"] > row["Cost-optimized"]["% dark"]
    r = route_order(sched, vols, "US", policy="Shield (dark-patient)",
                    half_spread_bps=2.0)
    assert r.routed_shares == pytest.approx(sched["shares_traded"].sum(), rel=1e-6)
    assert any("Shield" in n for n in r.notes)


def test_shield_saves_cost_vs_cost_optimized_on_wide_spread():
    # More midpoint fills = less spread crossed; on a wide-spread tape the
    # blended cost must not exceed Cost-optimized.
    sched, vols = _us_schedule(), _bar_volumes()
    cmp = compare_policies(sched, vols, "US", half_spread_bps=10.0)
    row = {r["Policy"]: r for _, r in cmp.iterrows()}
    assert (row["Shield (dark-patient)"]["Blended routing cost (bps)"]
            <= row["Cost-optimized"]["Blended routing cost (bps)"])
