"""The ticker matcher must refuse more than it accepts (c-239).

A wrong ticker is worse than a blank one: a blank is visibly
missing, a wrong one silently prices a different company and
every downstream number stays plausible. These tests pin the
refusals, not the matches.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ticker_fill as F                            # noqa: E402


def test_exact_name_matches():
    got, conf, _ = F.match_one(
        "TAIWAN SEMICONDUCTOR", [("2330", "TAIWAN SEMICONDUCTOR")])
    assert got == "2330" and conf == 1.0


def test_msci_abbreviations_are_expanded():
    """MSCI writes 'CHINA MERCH BK'; the exchange writes
    'CHINA MERCHANTS BANK'. Same company."""
    got, _c, _w = F.match_one(
        "CHINA MERCHANTS BK CO",
        [("600036", "CHINA MERCHANTS BANK")])
    assert got == "600036"


def test_share_classes_must_agree():
    """THE MOST IMPORTANT TEST HERE. These are two securities
    with different prices, and a fuzzy matcher with no class
    check maps one onto the other."""
    got, _c, why = F.match_one(
        "SAMSUNG ELEC PREF", [("005930", "SAMSUNG ELECTRONICS")])
    assert got is None, why
    got, _c, _w = F.match_one(
        "SAMSUNG ELEC", [("005930", "SAMSUNG ELECTRONICS")])
    assert got == "005930"


def test_a_close_runner_up_is_refused():
    """A near-tie is where being wrong is most likely and least
    visible, so it is not resolved at all."""
    got, _c, why = F.match_one(
        "CHINA CONSTRUCTION",
        [("939", "CHINA CONSTRUCTION BANK"),
         ("601668", "CHINA CONSTRUCTION ENGINEERING")])
    assert got is None
    assert "AMBIGUOUS" in why or "too close" in why


def test_unrelated_names_are_never_matched():
    """From the live queue: the best candidate for MACQUARIE
    OFFICE TRUST scored 0.435 and was MAGELLAN FINANCIAL GROUP.
    A threshold set by optimism rather than evidence would have
    written it."""
    got, conf, _w = F.match_one(
        "MACQUARIE OFFICE TRUST",
        [("MFG", "MAGELLAN FINANCIAL GROUP"),
         ("SIG", "SIGMA HEALTHCARE")])
    assert got is None
    assert conf < 0.7


def test_ambiguous_exact_matches_are_refused():
    got, _c, why = F.match_one(
        "ACME", [("A1", "ACME"), ("A2", "ACME")])
    assert got is None and "AMBIGUOUS" in why


def test_the_script_never_writes_the_changes_db():
    src = (ROOT / "scripts" / "ticker_fill.py").read_text(
        encoding="utf-8")
    assert "to_pickle" not in src
    assert "OVERLAY" in src
