"""MI_5MINS changes resolution four times (c-228).

Bill remembered a 2015 boundary in the auction data. He was
right and I had swept it away at c-226 by checking whether the
TWSE files EXIST and not what they CONTAIN.

TWSE serves MI_5MINS from 2004-10-15, but the `notes` field
returned with every response says the grid changed:

    before 2011-01-16 ....... every minute
    2011-01-16 .. 2014-02-23  every 15 seconds
    2014-02-24 .. 2014-12-28  every 10 seconds
    from 2014-12-29 ......... every 5 seconds

The closing call is five minutes long. On a 1-minute grid that
is five points; on a 5-second grid it is sixty. The indicative
PATH through the auction only exists from 2014-12-29.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from auction_study_2026 import mi5_resolution      # noqa: E402


def test_the_four_regimes_and_their_boundaries():
    assert mi5_resolution("20050415") == 60
    assert mi5_resolution("20110115") == 60
    assert mi5_resolution("20110116") == 15
    assert mi5_resolution("20140223") == 15
    assert mi5_resolution("20140224") == 10
    assert mi5_resolution("20141228") == 10
    assert mi5_resolution("20141229") == 5
    assert mi5_resolution("20260529") == 5


def test_the_5_second_grid_starts_at_the_end_of_2014():
    """THE BOUNDARY BILL REMEMBERED. Any conclusion drawn from
    an auction PATH has to be dated on or after this."""
    assert mi5_resolution("20141229") == 5
    assert mi5_resolution("20141226") > 5


def test_iso_dates_work_too():
    assert mi5_resolution("2014-12-29") == 5
    assert mi5_resolution("2010-06-01") == 60
