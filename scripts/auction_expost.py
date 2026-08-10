"""Ex-post close-auction review (c-71) — what the auction DID,
per name-event, from data already on disk (IB 5m bars, 2023+).

For every event name on its effective day:
  last_cont      last continuous 5m close before the 13:25 call
  auction_px     official close (the auction print)
  disl_bps       auction vs last continuous, raw signed
  pressure_bps   disl oriented WITH the forced flow (+ = the
                 auction moved the way trackers were pushing;
                 - = the print came back through the last price)
  auction_share  13:25+ volume / day volume
  pm_drift_bps   13:00 -> last_cont (pressure building before
                 the call, oriented with the flow)
  t1_revert_bps  T+1 close vs auction, oriented so + = the
                 dislocation DECAYED (favorable to a contrarian
                 fill at the print)

DESCRIPTIVE / TCA ONLY: no hypothesis in Registry v5 covers
these columns; any pattern noticed here goes to a v6 registry
and waits for the next data vintage (protocol rule 8). This is
the ex-post half of the auction work — the ex-ante half (5-sec
indicative path) starts with the Aug-31 live capture and has NO
history (disclosure regime only exists since Mar-2020; the feed
is not publicly archived).

Usage: py scripts\\auction_expost.py
Output: data/auction_expost.json + printed summary
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


_VC = None


def _t1_close(code, eff):
    """Next close after eff from the vintage cache; None if the
    series ends at eff (recent events)."""
    global _VC
    if _VC is None:
        _VC = json.loads((ROOT / "data" /
                          "tw_vintage_cache.json").read_text(encoding="utf-8"))
    ser = _VC.get(f"px|{code}")
    if not ser:
        return None
    nxt = sorted((r["date"], r["close"]) for r in ser
                 if r["date"] > eff)
    return nxt[0][1] if nxt else None


_SD = None


def _official_close(code, day):
    """Cached clone of tday_execution_studies._official_close
    (that one reloads stock_day.json per call)."""
    global _SD
    if _SD is None:
        _SD = json.loads((ROOT / "data" / "tw_history" /
                          "stock_day.json").read_text(encoding="utf-8"))
    for m in _SD.get(code, {}):
        for r in _SD[code][m]:
            if r[0] == day:
                return float(r[6])
    return None


def build():
    from scripts.ib_harvest import IB_FLOOR, _ib_event_set
    from scripts.tday_execution_studies import _ib_day, _load_ib
    ib = _load_ib()
    rows = []
    for event, prov, eff, names in _ib_event_set():
        if eff < IB_FLOOR:
            continue
        day = eff
        for code, side in names.items():
            got = _ib_day(ib, code, day)
            if not got:
                continue
            cont, auc_vol, last_cont = got
            close = _official_close(code, day) or None
            if not close or not last_cont:
                continue
            sgn = 1.0 if side == "Buy" else -1.0
            disl = (close - last_cont) / last_cont * 1e4
            bar13 = [c for t, _, c, _ in cont if t <= "13:00"]
            pm = ((last_cont - bar13[-1]) / bar13[-1] * 1e4
                  if bar13 else None)
            cvol = sum(b[3] for b in cont)
            t1 = _t1_close(code, eff)
            t1rev = (-(t1 - close) / close * 1e4 * sgn
                     if t1 else None)
            rows.append({
                "event": event, "prov": prov, "eff": eff,
                "code": code, "side": side,
                "last_cont": last_cont, "auction_px": close,
                "disl_bps": round(disl, 1),
                "pressure_bps": round(disl * sgn, 1),
                "pm_drift_bps": (round(pm * sgn, 1)
                                 if pm is not None else None),
                "auction_share": (round(auc_vol /
                                        (auc_vol + cvol), 3)
                                  if auc_vol + cvol else None),
                "t1_revert_bps": (round(t1rev, 1)
                                  if t1rev is not None else None),
            })
    return rows


def summarize(rows):
    import numpy as np
    out = {"n": len(rows),
           "n_events": len({r["event"] for r in rows})}
    for side in ("Buy", "Sell"):
        sub = [r for r in rows if r["side"] == side]
        if not sub:
            continue
        pr = [r["pressure_bps"] for r in sub]
        rv = [r["t1_revert_bps"] for r in sub
              if r["t1_revert_bps"] is not None]
        sh = [r["auction_share"] for r in sub
              if r["auction_share"] is not None]
        out[side] = {
            "n": len(sub),
            "median_pressure_bps": float(np.median(pr)),
            "median_abs_disl_bps": float(np.median(
                [abs(p) for p in pr])),
            "pct_pressed_with_flow": float(np.mean(
                [p > 0 for p in pr])),
            "median_t1_revert_bps": (float(np.median(rv))
                                     if rv else None),
            "pct_decayed_t1": (float(np.mean([v > 0 for v in rv]))
                               if rv else None),
            "median_auction_share": (float(np.median(sh))
                                     if sh else None),
        }
    return out


if __name__ == "__main__":
    rows = build()
    summ = summarize(rows)
    out = {"desc": __doc__.split("\n")[0], "summary": summ,
           "rows": rows}
    (ROOT / "data" / "auction_expost.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(summ, indent=2))
    print(f"rows written: {len(rows)}")
