"""Case-study runner — offline parser smoke (network path runs locally)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


def test_parser_accepts_documented_example():
    from run_case_study import build_parser
    a = build_parser().parse_args(
        ["SMCI", "US", "S&P 500", "2024-03-18", "--announced", "2024-03-01"])
    assert a.ticker == "SMCI" and a.window == 10 and a.announced == "2024-03-01"
