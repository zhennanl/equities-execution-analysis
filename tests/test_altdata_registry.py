"""c-264: the alternative-data registry and probe.

The probe exists because this project twice wrote a fetcher
against an assumed format and read the resulting silence as
absence — TPEx's ROC-vs-Gregorian date (c-232/261), and the
lots-vs-shares volume underneath it. Both were one HTTP
request away from obvious.

These tests guard the discipline, not the endpoints: a
registry entry must say what it is FOR, at what granularity,
and anything needing a session must be flagged rather than
automated blind.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import altdata_probe as A                          # noqa: E402


def test_every_source_declares_a_data_type():
    """A source that does not fill one of the six types is a
    source nobody can say why they harvested."""
    for mkt, items in A.registry().items():
        for it in items:
            assert it.get("type") in A.TYPES, (mkt, it.get("id"))
            assert it.get("what"), (mkt, it.get("id"))
            assert it.get("url"), (mkt, it.get("id"))


def test_taiwan_covers_all_six_types():
    """Taiwan is the template in Part 6.2 — it only works as a
    template if it actually demonstrates all six."""
    tw = {i["type"] for i in A.registry()["Taiwan"]}
    assert tw == set(A.TYPES), sorted(set(A.TYPES) - tw)


def test_session_bound_sources_are_marked_manual():
    """CCASS and the KRX loader need a form or a session. An
    unmarked one would be probed with a bare GET, return
    something empty-looking, and be recorded as unavailable."""
    reg = A.registry()
    for mkt, sid in (("HongKong", "hkex_ccass"),
                     ("Korea", "krx_investor_by_issue")):
        it = next(i for i in reg[mkt] if i["id"] == sid)
        assert it.get("manual") is True, sid
        assert it.get("note"), f"{sid} must say how to do it"


def test_the_granularity_trap_is_written_down():
    """JPX investor-type flow is believed to be weekly and
    market-wide. Market-wide flow cannot answer a per-name
    event question, so the registry must warn rather than
    invite a harvest."""
    jp = next(i for i in A.registry()["Japan"]
              if i["id"] == "jpx_investor_type")
    assert jp["status"] == "RESEARCH"
    assert "GRANULARITY" in jp["note"].upper()


def test_the_probe_records_shape_and_never_parses_meaning():
    import inspect
    src = inspect.getsource(A)
    assert "def _shape" in src
    # it must surface an error STATUS, which is exactly what
    # TPEx returned for months while looking like no data
    assert '"stat"' in src
    for word in ("json object", "html", "text/csv"):
        assert word in src


def test_shape_detects_a_parameter_error_response():
    """The TPEx failure in one line: HTTP 200, valid JSON, and
    a stat field saying the request was wrong."""
    sh = A._shape('{"stat":"參數輸入錯誤"}',
                  "application/json")
    assert sh["kind"] == "json object"
    assert "stat" in sh


def test_shape_reads_html_headers_and_csv_lines():
    h = A._shape("<table><tr><th>Date</th><th>Volume</th></tr>"
                 "<tr><td>1</td><td>2</td></tr></table>", "")
    assert h["kind"] == "html"
    assert "Date" in h["headers"]
    c = A._shape("a,b,c\n1,2,3\n4,5,6", "text/csv")
    assert c["kind"] == "text/csv"
    assert len(c["first_lines"]) == 3


def test_the_question_bank_puts_taiwan_first():
    q = (ROOT / "docs" / "REBALANCE_QUESTION_BANK.md").read_text(
        encoding="utf-8")
    assert "Taiwan first, always" in q
    assert "## N. Taiwan alternative data" in q
    assert "PART 6 — THE ALTERNATIVE-DATA MANDATE" in q
    # the six types must be stated where the analyst will read
    # them, not only in the script
    assert "closing-auction microstructure" in q.lower()
    assert "granularity" in q.lower()
