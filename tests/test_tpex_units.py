"""c-261: the two TPEx bugs that read as "no data".

Eighteen live, well-known Taiwan OTC names — E Ink, Phison,
Aspeed, eMemory, Win Semiconductors, PharmaEssentia — returned
"0 days" for months. Neither cause was absence:

  1. the request sent the ROC year, so TPEx replied
     {"stat":"參數輸入錯誤"} every time and the harvester read
     the empty result as attrition;
  2. TPEx quotes volume in LOTS (成交張數) where TWSE quotes
     SHARES (成交股數), so a naive fix would have made every
     OTC name's volume 1,000x too small — in a dataset whose
     entire purpose is trade size against ADV.

The second is the one worth a permanent test. A missing window
announces itself; a volume that is off by a factor of a
thousand does not.
"""
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def _src():
    import tw_event_window as T
    return inspect.getsource(T.fetch_tpex)


def test_the_request_uses_the_gregorian_year():
    """AD in, ROC out. Sending the ROC year returns a parameter
    error, which looks exactly like a name that did not trade."""
    s = _src()
    assert "{mo[:4]}/{mo[4:6]}/01" in s
    assert "- 1911" not in s.split('"""')[-1], \
        "the REQUEST must not convert to ROC"
    # the RESPONSE is still ROC and must still be converted
    assert "1911 + int(p[0])" in s


def test_tpex_volume_is_converted_from_lots_to_shares():
    s = _src()
    assert "LOT = 1000" in s
    assert "v * LOT" in s


def test_a_bad_status_is_reported_not_swallowed():
    """Returning [] on a parameter error is what let this hide
    for months — an empty list reads as 'did not trade'."""
    s = _src()
    assert 'j.get("stat"' in s
    assert "continue" in s


def test_tpex_and_twse_volumes_share_one_unit():
    """The two boards land in the same field of the same file,
    so they must be in the same unit or every cross-board ADV
    comparison is wrong by a factor of a thousand."""
    import json
    p = ROOT / "data" / "tw_event_windows.json"
    if not p.exists():
        return
    W = json.loads(p.read_text(encoding="utf-8"))["windows"]
    vols = [r["v"] for w in W.values()
            for r in (w.get("px") or [])
            if r.get("v")]
    if len(vols) < 200:
        return
    vols.sort()
    med = vols[len(vols) // 2]
    # index movers in Taiwan trade in the hundreds of thousands
    # to millions of SHARES a day. A median in the thousands
    # would mean lots leaked through somewhere.
    assert med > 50_000, (
        f"median daily volume {med:,.0f} looks like LOTS, not "
        f"shares — a board is reporting in the wrong unit")
