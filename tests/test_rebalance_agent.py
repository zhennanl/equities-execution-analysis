"""Tests for the agent tool layer (deterministic parts only —
no API calls)."""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import agent_tools as at  # noqa: E402


def test_data_status_shape_and_phase():
    s = at.data_status()
    for k in ("phase", "day_offset", "shortlist",
              "ledger_days_pulled", "ledger_stale",
              "historical_windows"):
        assert k in s
    assert s["phase"] in ("PRE_ANNOUNCEMENT",
                          "ANNOUNCEMENT_TO_EFFECTIVE",
                          "POST_EFFECTIVE")
    assert s["historical_windows"] > 100


def test_snapshot_unknown_name_is_no_data():
    r = at.name_snapshot("9999")
    assert r["status"] == "NO_DATA"


def test_snapshot_shortlist_name_never_invents():
    # with <2 sessions the tool must say NO_DATA, not guess
    r = at.name_snapshot("2344")
    assert r["status"] in ("OK", "NO_DATA")
    if r["status"] == "NO_DATA":
        assert "need" in r


def test_crowding_read_routes_by_action():
    r = at.crowding_read("2615")           # DEL name
    if r.get("status") != "NO_DATA":
        assert r["bucket"] in ("light_short", "mid_short",
                               "crowded_short", "NO_DATA")


def test_result_block_library():
    assert "keys" in at.result_block("persona")
    bad = at.result_block("nope")
    assert bad["status"] == "NO_DATA"
    q6 = at.result_block("qa", "Q6_volume_profile")
    assert "0" in q6                       # eff-day bucket


def test_tools_registry_complete():
    assert {"data_status", "fetch_daily", "name_snapshot",
            "crowding_read", "find_analogs", "result_block",
            "save_note"} <= set(at.TOOLS)


def test_agent_module_parses_and_offline_exists():
    src = (ROOT / "scripts" / "rebalance_agent.py") \
        .read_text(encoding="utf-8")
    tree = ast.parse(src)
    fns = {n.name for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef)}
    assert {"daily", "ask", "offline", "run_agent"} <= fns
