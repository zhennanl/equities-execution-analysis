"""One display name must never stand for two securities (c-241).

Bill saw three rows reading "Hyundai Motor Company" with three
different tickers and asked why. They are three securities —
common, preferred 1, preferred 2 — and Yahoo returns the ISSUER
name for all three. The roster preferred Yahoo's spelling
because it was tidier; tidier and, there, false.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import name_collisions as N                        # noqa: E402


def test_padding_is_only_padding_within_one_code_family():
    """THE CORRECTION. My first rule stripped leading zeros and
    called any match "one security stored twice". China breaks
    it: 000598 is Shenzhen and 0598 is Hong Kong — two different
    companies. Merging them would invent a history, which is a
    worse error than the one I was fixing."""
    kind, _why = N.classify(["000598", "0598"], ["SOMETHING"])
    assert kind != "PADDING", kind
    kind, _why = N.classify(["0914", "914"], ["ANHUI CONCH"])
    assert kind == "PADDING"
    kind, _why = N.classify(["000001", "1"], ["X"])
    assert kind != "PADDING"


def test_dual_listings_are_never_merged():
    kind, _w = N.classify(["600585", "0914"], ["ANHUI CONCH"])
    assert kind == "DUAL_LISTING"


def test_share_classes_are_flagged():
    kind, _w = N.classify(
        ["005380", "005385"], ["HYUNDAI MOTOR S1 PREF"])
    assert kind == "SHARE_CLASS"


def test_the_roster_keeps_msci_names_when_yahoo_collides():
    """The page-side half of the fix."""
    src = (ROOT / "views" / "history_explorer.py").read_text(
        encoding="utf-8")
    assert "_collide" in src
    assert "yn not in _collide" in src
