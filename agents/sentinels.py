"""Layer-0 DATA SENTINELS — the desk's automated watchers (c-38).

Design contract (see docs/SENTINELS_GUIDE.md for the trader guide):
  - each sentinel FETCHES one data family, DIFFS it against the
    last-seen state, and emits ONE LINE: status + delta
  - statuses: OK (nothing changed), CHANGED (normal evolution,
    noted), ALERT (a trader should look today), DEGRADED (the data
    itself is broken/stale — distrust downstream artifacts)
  - sentinels NEVER judge or trade: they watch, diff, and report.
    Judgment lives in Layer 1+ and in the analyst.
  - state lives in data/sentinel_state.json (previous snapshots);
    every run writes data/sentinel_report.json for the UI

Run:  python -m agents.sentinels            (all)
      python -m agents.sentinels members    (one)
Daily scheduling (Windows):
      schtasks /create /tn "sentinels" /tr "py -m agents.sentinels"
               /sc daily /st 08:00
"""
import datetime as dt
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data" / "sentinel_state.json"
REPORT = ROOT / "data" / "sentinel_report.json"
API = "https://api.finmindtrade.com/api/v4/data"

ANN, EFF = dt.date(2026, 8, 11), dt.date(2026, 8, 31)

# artifact -> the data files it was built from (staleness sentinel)
ARTIFACT_DEPS = {
    "data/funnel_tw.json": ["data/aug26_cap_refresh.json",
                            "data/ewt_members.json"],
    "data/universe_workbench_tw.json": [
        "data/aug26_cap_refresh.json"],
    "data/ladder_aug26_tw.json": ["data/ewt_members.json",
                                  "data/tw_membership_sources.json"],
    "data/tday_cards_aug26.json": ["data/aug26_cap_refresh.json"],
}


def _load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def _save_state(s):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(s))
    tmp.replace(STATE)


def _r(name, status, delta, details=None):
    return {"sentinel": name, "status": status, "delta": delta,
            "details": details or {},
            "ts": dt.datetime.now().isoformat(timespec="seconds")}


# ── S1: shorts freshness (wraps the existing guarantee) ──────────
def s_shorts(state):
    try:
        from agents.data_freshness import (ensure_fresh_shorts,
                                           freshness_line)
        fr = ensure_fresh_shorts()
        st = "DEGRADED" if fr["status"] == "DEGRADED" else "OK"
        return _r("shorts", st, freshness_line(fr))
    except Exception as e:                     # noqa: BLE001
        return _r("shorts", "DEGRADED", f"freshness check failed: {e}")


# ── S2: membership across all tracked funds ──────────────────────
def s_members(state):
    """Refetch fund holdings, diff vs last-seen membership. A name
    LEAVING funds mid-quarter = corporate-event candidate (the
    Inotera/4551 class) — this is the alert that used to require
    archaeology."""
    try:
        import importlib
        m = importlib.import_module("scripts.apac_members_harvest")
        prev = state.get("members", {})
        cur, deltas, alerts = {}, [], []
        comp_cache = {}
        for tag, (pid, slug) in m.COMPOSITES.items():
            comp_cache[tag] = m._fetch_csv(pid, slug)
            time.sleep(0.8)
        for mkt, (fund, pid, slug, comp, loc) in m.MARKETS.items():
            rows = m._fetch_csv(pid, slug)
            anchor, _ = m._equity_rows(rows)
            cross, _ = m._equity_rows(comp_cache[comp],
                                      location=loc)
            names = sorted(set(anchor)
                           | set(cross)) if mkt in m.IMI_ANCHORS \
                else sorted(set(anchor) | set(cross))
            cur[mkt] = names
            if mkt in prev:
                gone = sorted(set(prev[mkt]) - set(names))
                new = sorted(set(names) - set(prev[mkt]))
                if gone or new:
                    deltas.append(f"{mkt}: +{new} -{gone}")
                    # mid-quarter exits are corporate-event flags
                    if gone and not _near_effective():
                        alerts.append(
                            f"{mkt}: {gone} left tracking funds "
                            "MID-QUARTER — corporate-event "
                            "candidate (check M&A/suspension)")
            time.sleep(0.8)
        state["members"] = cur
        if alerts:
            return _r("members", "ALERT", "; ".join(alerts),
                      {"deltas": deltas})
        if deltas:
            return _r("members", "CHANGED", "; ".join(deltas))
        return _r("members", "OK",
                  f"{len(cur)} markets, no membership drift")
    except Exception as e:                     # noqa: BLE001
        return _r("members", "DEGRADED", f"fetch failed: {e}")


def _near_effective(days=5):
    return abs((dt.date.today() - EFF).days) <= days


# ── S3: ladder caps (bottom of the TW member ladder) ─────────────
def s_ladder(state):
    """Re-price the pool region daily; report entries/exits vs the
    stored ladder pool."""
    try:
        import requests
        lad = json.loads((ROOT / "data" / "ladder_aug26_tw.json")
                         .read_text())
        gmsr = lad["gmsr_usd_b"] * 1e9
        pool_prev = {r["code"] for r in lad["delete_pool"]}
        watch = sorted({r["code"] for r in lad["ladder_bottom"]}
                       | pool_prev)
        moves, pool_now = [], set()
        for c in watch:
            try:
                p = requests.get(API, params={
                    "dataset": "TaiwanStockPrice", "data_id": c,
                    "start_date": str(dt.date.today()
                                      - dt.timedelta(days=7)),
                    "end_date": str(dt.date.today())},
                    timeout=25).json().get("data", [])
                time.sleep(0.5)
                if not p:
                    continue
                old = next(r for r in lad["ladder_bottom"] +
                           lad["delete_pool"] if r["code"] == c)
                cap = old["cap_usd"] * (p[-1]["close"]
                                        / _last_close_at(c,
                                                         old["asof"],
                                                         p))
                if cap < 1.15 * gmsr:
                    pool_now.add(c)
            except Exception:                  # noqa: BLE001
                continue
        entered = sorted(pool_now - pool_prev)
        left = sorted(pool_prev - pool_now)
        if entered or left:
            return _r("ladder", "ALERT" if entered else "CHANGED",
                      f"pool entries {entered} / exits {left}",
                      {"pool_now": sorted(pool_now)})
        return _r("ladder", "OK",
                  f"pool stable ({len(pool_prev)} names)")
    except Exception as e:                     # noqa: BLE001
        return _r("ladder", "DEGRADED", f"{e}")


def _last_close_at(code, asof, rows):
    for r in rows:
        if r["date"] == asof:
            return r["close"]
    return rows[0]["close"]


# ── S4: calendar / deadlines ─────────────────────────────────────
def s_calendar(state):
    today = dt.date.today()
    ta, te = (ANN - today).days, (EFF - today).days
    msgs, status = [f"T-{ta} to announcement (Aug-11, Asia reads "
                    f"Aug-12); T-{te} to effective (Aug-31)"], "OK"
    try:
        cards = json.loads((ROOT / "data" / "tday_cards_aug26.json")
                           .read_text())
        for c in cards.get("cards", []):
            msb = c.get("must_start_by")
            if not msb or len(str(msb)) < 10:
                continue
            d = dt.date.fromisoformat(str(msb)[:10])
            if 0 <= (d - today).days <= 2:
                msgs.append(f"{c.get('ticker')}: must-start-by "
                            f"{msb} is within 2 days")
                status = "ALERT"
    except Exception:                          # noqa: BLE001
        pass
    if ta in (1, 0):
        status = "ALERT"
        msgs.append("ANNOUNCEMENT IMMINENT — finalization protocol "
                    "(same-morning caps+crowding refresh, lock, "
                    "commit)")
    return _r("calendar", status, "; ".join(msgs))


# ── S5: FX ───────────────────────────────────────────────────────
def s_fx(state):
    try:
        import requests
        rows = requests.get(API, params={
            "dataset": "TaiwanExchangeRate", "data_id": "USD",
            "start_date": str(dt.date.today()
                              - dt.timedelta(days=10)),
            "end_date": str(dt.date.today())},
            timeout=25).json().get("data", [])
        if not rows:
            raise RuntimeError("no FX rows")
        spot = float(rows[-1].get("spot_sell")
                     or rows[-1].get("cash_sell"))
        drift = abs(spot / 32.5 - 1)
        st = "CHANGED" if drift > 0.02 else "OK"
        extra = ("; caps translation drifting — re-pin FX"
                 if st != "OK" else "")
        return _r("fx", st,
                  f"TWD {spot:.2f} vs pinned 32.5 "
                  f"({drift:+.1%} drift{extra})")
    except Exception as e:                     # noqa: BLE001
        return _r("fx", "DEGRADED", f"{e}")


# ── S6: artifact staleness ───────────────────────────────────────
def s_artifacts(state):
    stale = []
    for art, deps in ARTIFACT_DEPS.items():
        ap = ROOT / art
        if not ap.exists():
            continue
        amt = ap.stat().st_mtime
        for d in deps:
            dp = ROOT / d
            if dp.exists() and dp.stat().st_mtime > amt + 60:
                stale.append(f"{Path(art).name} predates "
                             f"{Path(d).name}")
    if stale:
        return _r("artifacts", "ALERT",
                  "; ".join(stale) + " — regenerate before quoting")
    return _r("artifacts", "OK",
              f"{len(ARTIFACT_DEPS)} artifacts current vs sources")


SENTINELS = {"shorts": s_shorts, "members": s_members,
             "ladder": s_ladder, "calendar": s_calendar,
             "fx": s_fx, "artifacts": s_artifacts}


TTL_H = {"members": 4, "ladder": 4, "shorts": 0, "calendar": 0,
         "fx": 1, "artifacts": 0}


def run(only=None, force=False):
    state = _load_state()
    last = state.setdefault("_last_results", {})
    results = []
    for name, fn in SENTINELS.items():
        if only and name != only:
            continue
        prev = last.get(name)
        ttl = TTL_H.get(name, 0)
        if (not force and not only and prev and ttl and
                (dt.datetime.now()
                 - dt.datetime.fromisoformat(prev["ts"]))
                .total_seconds() < ttl * 3600):
            r = dict(prev)
            r["delta"] += f" (cached, ttl {ttl}h)"
            results.append(r)
            continue
        r = fn(state)
        last[name] = r
        results.append(r)
    _save_state(state)
    worst = ("DEGRADED" if any(r["status"] == "DEGRADED"
                               for r in results)
             else "ALERT" if any(r["status"] == "ALERT"
                                 for r in results)
             else "CHANGED" if any(r["status"] == "CHANGED"
                                   for r in results) else "OK")
    report = {"generated": dt.datetime.now()
              .isoformat(timespec="seconds"),
              "overall": worst, "results": results}
    if not only:
        tmp = REPORT.with_suffix(".tmp")
        tmp.write_text(json.dumps(report, indent=1))
        tmp.replace(REPORT)
    return report


if __name__ == "__main__":
    import sys
    only = sys.argv[1] if len(sys.argv) > 1 else None
    rep = run(only)
    print(f"OVERALL: {rep['overall']}")
    for r in rep["results"]:
        print(f"  [{r['status']:8s}] {r['sentinel']:10s} "
              f"{r['delta']}")
