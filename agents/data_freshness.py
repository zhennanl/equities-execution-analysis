"""Data-freshness guarantee — live analytics never run on silently
stale data.

Session 9i, built from a caught failure: the Aug pack served a
crowding read as-of Jul-22 because the cache hadn't been pulled since
the previous session, and the eight missing sessions CHANGED the
read (1101's build had paused; 1326 had started building). The as-of
stamp exposed it; this module prevents it.

Contract:
  * Every LIVE run calls ensure_fresh_shorts() before reading the
    short cache; it fetches every missing trading day up to the most
    recent one the exchange has published.
  * FULL-DAY storage: refresh stores ALL codes for each day, not a
    watch subset — this kills the code-set-gap class (1504/1402 had
    only 8 obs because an older fetch stored 11 codes).
  * Holidays / not-yet-published days go to a no-data ledger so they
    are not refetched forever; freshness tolerance is 1 business day
    (TWT93U publishes after the close).
  * Network failure NEVER crashes the tool: it returns status
    DEGRADED and the pack renders the warning — stale data may be
    served, but never silently.
  * PIT / as-of runs are EXEMPT by design (a backtest must not see
    the present); callers pass live=False.
  * A TTL (default 4h) stops UI reruns from hammering the exchange.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "event_data_cache.json"
TOLERANCE_BDAYS = 1
TTL_SECONDS = 4 * 3600


def _expected_latest(today: str | None = None) -> str:
    t = pd.Timestamp(today) if today else pd.Timestamp.now()
    d = t.normalize()
    while d.weekday() >= 5:
        d -= pd.Timedelta(days=1)
    return d.strftime("%Y%m%d")


def _stale_bdays(latest: str, expected: str) -> int:
    if latest >= expected:
        return 0
    return len(pd.bdate_range(pd.Timestamp(latest)
                              + pd.Timedelta(days=1),
                              pd.Timestamp(expected)))


def ensure_fresh_shorts(cache_path: Path = CACHE,
                        fetch_fn=None, today: str | None = None,
                        ttl: int = TTL_SECONDS) -> dict:
    """Refresh the TW short cache to the most recent published
    trading day. Returns a freshness report the caller MUST surface:
    {status: FRESH|REFRESHED|DEGRADED, latest, expected,
     fetched_days, failed_days, stale_bdays, note}."""
    if fetch_fn is None:
        from agents.event_data import fetch_twse_short_balance
        fetch_fn = fetch_twse_short_balance
    cache = (json.loads(cache_path.read_text())
             if cache_path.exists() else {"short": {}})
    meta = cache.setdefault("_meta", {})
    short = cache.setdefault("short", {})
    expected = _expected_latest(today)
    latest = max(short) if short else "00000000"
    no_data = set(meta.get("no_data_days", []))

    # TTL: if we checked very recently, accept the cache as-is
    if (time.time() - meta.get("last_check_ts", 0) < ttl
            and _stale_bdays(latest, expected) <= TOLERANCE_BDAYS):
        return {"status": "FRESH", "latest": latest,
                "expected": expected, "fetched_days": [],
                "failed_days": [], "stale_bdays": 0,
                "note": f"checked within TTL ({ttl // 3600}h)"}

    todo = [d.strftime("%Y%m%d") for d in
            pd.bdate_range(pd.Timestamp(latest)
                           + pd.Timedelta(days=1),
                           pd.Timestamp(expected))] \
        if latest < expected else []
    todo = [d for d in todo if d not in no_data]
    fetched, failed = [], []
    for d in todo:
        try:
            df = fetch_fn(d)
        except Exception:                              # noqa: BLE001
            failed.append(d)
            continue
        if df is None or not len(df):
            no_data.add(d)             # holiday / not yet published
            continue
        # FULL-DAY storage — every code, no watch-subset gaps
        day = {}
        for _, r in df.iterrows():
            m = r.get("margin_short_bal") or 0.0
            s = r.get("sbl_bal") or 0.0
            day[str(r["ticker"])] = [float(m), float(s)]
        short[d] = day
        fetched.append(d)
    meta["no_data_days"] = sorted(no_data)[-30:]
    meta["last_check_ts"] = time.time()
    cache_path.write_text(json.dumps(cache))
    latest2 = max(short) if short else "00000000"
    stale = _stale_bdays(latest2, expected)
    if failed and stale > TOLERANCE_BDAYS:
        status = "DEGRADED"
        note = (f"network failures on {failed}; serving data "
                f"{stale} business days stale — reads may be "
                "outdated, treat with caution")
    elif fetched:
        status = "REFRESHED"
        note = f"fetched {len(fetched)} day(s): {fetched}"
    else:
        status = "FRESH"
        note = "cache already current (or expected day not yet " \
               "published — tolerance 1 bday)"
    return {"status": status, "latest": latest2,
            "expected": expected, "fetched_days": fetched,
            "failed_days": failed, "stale_bdays": stale,
            "note": note}


def freshness_line(report: dict) -> str:
    """One-line banner for packs/UI — always rendered on live runs."""
    icon = {"FRESH": "OK", "REFRESHED": "OK (auto-refreshed)",
            "DEGRADED": "WARNING — STALE DATA"}[report["status"]]
    return (f"DATA FRESHNESS [{icon}]: shorts latest {report['latest']}"
            f" vs expected {report['expected']} "
            f"({report['stale_bdays']} bdays stale). {report['note']}")
