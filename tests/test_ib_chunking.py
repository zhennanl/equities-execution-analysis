"""Chunk tiling for the IB 5-minute harvester (c-197).

The clamp these guard is the fix for a real data loss: fixed
30-day chunks walked past IB's history floor, IB returned
nothing rather than truncating, and the loop broke — discarding
the entire pre-announcement stretch while the window still
advertised 14 days of it.
"""
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ib_5m_events as m                           # noqa: E402


def test_chunks_never_reach_before_the_start():
    a, b = dt.date(2023, 4, 27), dt.date(2023, 7, 15)
    for end, span in m._chunks(a, b, 30):
        assert end - dt.timedelta(days=span) >= a, \
            "a chunk asked for days before the window start — " \
            "IB serves nothing at all for such a request"


def test_chunks_cover_the_whole_window():
    a, b = dt.date(2023, 4, 27), dt.date(2023, 7, 15)
    ch = m._chunks(a, b, 30)
    assert ch[0][0] == b
    last_end, last_span = ch[-1]
    assert last_end - dt.timedelta(days=last_span) == a


def test_last_chunk_is_clamped_not_full_size():
    a, b = dt.date(2023, 4, 27), dt.date(2023, 7, 15)
    ch = m._chunks(a, b, 30)
    assert ch[-1][1] == 19, \
        "the tail chunk must shrink to the remaining days"


def test_bigger_chunks_mean_fewer_requests():
    a, b = dt.date(2023, 1, 1), dt.date(2023, 7, 15)
    assert len(m._chunks(a, b, 90)) < len(m._chunks(a, b, 30))


def test_single_day_window_still_yields_one_request():
    a = dt.date(2024, 3, 1)
    ch = m._chunks(a, a + dt.timedelta(days=1), 30)
    assert len(ch) == 1 and ch[0][1] == 1


def test_tuning_defaults_are_conservative_before_measurement():
    """Untuned runs must not assume speed we have not proven."""
    if m.PACE_FILE.exists():
        import pytest
        pytest.skip("pacing already measured on this machine")
    assert m._concurrency() == 1
    assert m._chunk_days() == m.CHUNK_DEFAULT
    assert m._pace() == m.PACE_DEFAULT


def test_fetch_all_runs_largest_first_but_probes_first():
    """c-258. Bill wants China's backlog first. c-226 ran
    smallest-first so the cheapest market doubled as the test
    of symbol resolution — that protection cannot simply be
    deleted, or a broken session burns the night on China
    before the end-of-market SHUTOUT rule fires. It moves to an
    explicit CANARY_MIN probe of the biggest market."""
    import inspect

    import ib_5m_events as M
    assert (inspect.signature(M.fetch_all)
            .parameters["order"].default == "largest")
    assert "cap" in inspect.signature(M.fetch).parameters
    src = inspect.getsource(M.fetch_all)
    assert 'reverse=(order == "largest")' in src
    assert "cap=CANARY_MIN" in src
    # the probe must be able to STOP the run, not merely report
    probe = src.split("PROBE")[1]
    assert "STOPPING BEFORE THE RUN" in probe
    assert probe.count("return") >= 2


def test_no_contract_does_not_look_like_a_broken_session():
    """c-260. The first probe stopped a 1,072-window run after
    five NO CONTRACT results, while that same market sat at
    247/260 windows with bars.

    "No contract" is IB ANSWERING — it resolved the request and
    said the symbol does not exist. A session that can return
    that answer works. Only silence, timeouts and entitlement
    refusals mean nothing downstream will succeed either."""
    import ib_5m_events as M
    B = M._session_looks_broken
    assert not B({"todo": 5, "got": 0,
                  "reasons": {"no_contract": 5}})
    assert not B({"todo": 5, "got": 0,
                  "reasons": {"no_contract": 3,
                              "venue_no_history": 2}})
    # ...but a systemic cause anywhere in the sample does stop
    assert B({"todo": 5, "got": 0, "reasons": {"timeout": 5}})
    assert B({"todo": 5, "got": 0,
              "reasons": {"no_permission": 5}})
    assert B({"todo": 5, "got": 0,
              "reasons": {"no_contract": 4, "timeout": 1}})
    assert B({"todo": 5, "got": 0, "fatal": "locked", })
    assert B({"todo": 5, "got": 0, "reasons": {}})   # silence
    assert not B({"todo": 5, "got": 2, "reasons": {}})


def test_the_probe_prefers_windows_nobody_has_tried():
    """c-260. `todo` is the RESIDUE, not the market — anything
    already fetched has been removed, so its head is weighted
    towards names that failed before. Sampling that and calling
    it representative is what produced the false alarm."""
    import inspect

    import ib_5m_events as M
    src = inspect.getsource(M.fetch)
    assert 'not in d["windows"]' in src
    assert "fresh or todo" in src.replace("(", "").replace(")", "")


def test_a_capped_fetch_is_real_work_not_a_sample():
    """The probe writes the same records as a full run, so the
    next run resumes from them — a throwaway probe would make
    the canary cost its pacing twice."""
    import inspect

    import ib_5m_events as M
    body = inspect.getsource(M.fetch)
    # c-260: the cap trims the WORK LIST, and the probe's
    # results are written to the same store the full run uses
    assert "[:cap]" in body
    assert 'f.write_text(json.dumps(d)' in body


def test_every_taiwan_job_tiles_cleanly():
    try:
        jobs = m.jobs("Taiwan")
    except Exception:                              # noqa: BLE001
        import pytest
        pytest.skip("changes DB unavailable")
    assert jobs
    for _rev, _code, _act, _name, a, b in jobs:
        ch = m._chunks(a, b)
        assert ch, "every window must produce at least one ask"
        for end, span in ch:
            assert span >= 1
            assert end - dt.timedelta(days=span) >= a
