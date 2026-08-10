"""Securities sharing a ticker in the MSCI Index Review
Database (c-202).

Collapsing rows on the ticker is right for a rename and wrong
for two different issuers. Auditing all 25 colliding tickers
found 23 genuine renames, 2 that must stay separate, and one
defect affecting every single one: the merge kept whichever
spelling had more moves and DISCARDED the other, so 28 index
changes were missing from the histories the page displayed.
"""
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if "streamlit" not in sys.modules:
    _st = types.ModuleType("streamlit")
    _st.cache_data = lambda **k: (lambda f: f)
    sys.modules["streamlit"] = _st

from views import history_explorer as he            # noqa: E402


def test_history_steps_sort_chronologically():
    """Reviews are MonYY, so plain string order is wrong:
    Aug < Feb < May < Nov alphabetically."""
    steps = ["ADD Nov16", "DEL May18", "ADD Aug23",
             "ADD Feb26", "DEL Nov06"]
    assert sorted(set(steps), key=he._rev_key) == [
        "DEL Nov06", "ADD Nov16", "DEL May18", "ADD Aug23",
        "ADD Feb26"]


def test_alphabetical_order_would_have_been_wrong():
    steps = ["ADD Aug23", "DEL May18"]
    assert sorted(steps) != sorted(steps, key=he._rev_key)


def test_unparseable_step_does_not_explode():
    assert he._rev_key("member throughout") == (0, 0)
    assert he._rev_key(None) == (0, 0)


def test_every_non_merge_is_recorded_with_a_reason():
    """c-259: was `test_the_two_non_merges…`. There is one now,
    because the Anhui Gujing exemption was retired when the
    ticker behind it was corrected. The COUNT was never the
    contract — the contract is that any exemption states a
    citable reason."""
    assert ("India", "ENRIN") in he.NEVER_MERGE
    assert he.NEVER_MERGE, "an empty list should be deliberate"
    for k, why in he.NEVER_MERGE.items():
        assert len(why) > 40, f"{k} needs a citable reason"


def test_siemens_demerger_is_not_treated_as_a_rename():
    why = he.NEVER_MERGE[("India", "ENRIN")]
    assert "demerger" in why.lower() or "separate" in why.lower()


def test_a_fixed_defect_loses_its_exemption():
    """c-259. ("China", "000596") used to be exempted because
    the Anhui Gujing B row carried the A line's ticker. The
    ticker was corrected at source (B -> 200596.SZ), so the
    collision is gone and the exemption with it.

    The general rule matters more than this case: a display
    guard is a workaround for a data defect, and it must be
    removed when the defect is. Kept on, it quietly asserts a
    problem that no longer exists — and the next reader treats
    a clean dataset as dirty."""
    assert ("China", "000596") not in he.NEVER_MERGE
    import pandas as pd
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    a = df[df.security == "ANHUI GUJING A (HK-C)"].ticker
    b = df[df.security == "ANHUI GUJING DISTILLER B"].ticker
    assert set(a) == {"000596.SZ"} and set(b) == {"200596.SZ"}


def test_every_collision_in_the_db_is_classified():
    """The audit must cover the real data, not a sample."""
    try:
        import pandas as pd
        df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    except Exception:                              # noqa: BLE001
        pytest.skip("changes DB unavailable")
    g = df[df.ticker != ""].copy()
    g["root"] = (g.ticker.astype(str).str.split(".")
                 .str[0].str.upper())
    collisions = [(mk, root) for (mk, root), sub
                  in g.groupby(["market", "root"])
                  if sub.security.nunique() > 1]
    assert collisions, "expected some colliding tickers"
    # every NEVER_MERGE entry must correspond to a real
    # collision — a stale exception is worse than none
    for key in he.NEVER_MERGE:
        assert key in collisions, \
            f"{key} is exempted but no longer collides"
