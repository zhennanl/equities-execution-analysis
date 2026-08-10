"""Steps 1-6 of the announcement->effective framework (c-128).

Reads:  data/tw_event_windows.json      (price windows)
        data/t86_history.json           (foreign net buy)
        data/sbl_history.json           (borrow balance)
        data/margin_history.json        (margin/short)
        data/tw_member_fifs_weights.json (weights-inversion FIFs)
Writes: data/event_window_metrics.json

Per window: the price-path metrics, flow decomposition,
crowding scores, demand estimate and label of
docs/EVENT_WINDOW_FRAMEWORK.md. Aggregates: the four playbook
tables. Market adjustment uses 0050 (same source, same
calendar); windows before 0050 coverage fall back to raw with
a flag.

REGISTERED CONSTANTS (declared before the Aug-26 grading, per
the framework's honesty rule):
  TRACKING_AUM_USD_B = 180.0    # MSCI TW passive proxy; a
                                # DECLARED assumption graded
                                # against effective-day prints
  PRE_DRIFT_HI = 0.05           # 5% pre-window drift = high
  SQZ_BORROW_HI = 1.30          # borrow 30% above its day-25
                                # level = squeeze-elevated
  PROG caps at 1.5 (overshoot happens; recorded, not clipped
  silently — values >1 mean arbs bought MORE than passive
  demand, i.e. inventory for the close)

Usage: py scripts\\event_window_analyze.py
"""
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "event_window_metrics.json"

TRACKING_AUM_USD_B = 180.0
PRE_DRIFT_HI = 0.05
SQZ_BORROW_HI = 1.30
IDX_FLOAT_B = 3183.0


def _j(n):
    p = ROOT / "data" / n
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _series(px, key):
    return [r[key] for r in px]


def _idx(dts, day):
    """last index with date <= day."""
    out = None
    for i, d in enumerate(dts):
        if d <= day:
            out = i
    return out


def analyze_window(v, mkt_px, t86, sbl, margin, fifs, fx=32.4):
    px = v["px"]
    if len(px) < 10:
        return {"error": "too few price rows", "n": len(px)}
    dts = _series(px, "d")
    close = _series(px, "c")
    vol = _series(px, "v")
    i0 = _idx(dts, v["ann"])
    ie = _idx(dts, v["eff"])
    if i0 is None or ie is None or ie <= i0 + 1:
        return {"error": "window does not span ann->eff"}
    base = close[i0]

    def ret(a, b):
        return close[b] / close[a] - 1

    def mret(a, b):
        """same-date market return via 0050; None if missing."""
        if not mkt_px:
            return None
        da, db = dts[a], dts[b]
        ka, kb = mkt_px.get(da), mkt_px.get(db)
        return (kb / ka - 1) if ka and kb else None

    def adj(a, b):
        r = ret(a, b)
        m = mret(a, b)
        return r - m if m is not None else r

    adv = st.median([q for q in vol[max(0, i0 - 20):i0] if q]
                    or [1])
    # ---- step 1: demand -------------------------------
    code = v["code"]
    fif = fifs.get(code)
    fcap_usd = None
    demand_sh = demand_adv = None
    if fif and base:
        # float cap ~ FIF x shares... we lack shares here; use
        # weight route: float$ from weights file if present
        fcap_usd = fif.get("msci_float_b")
        if fcap_usd:
            w = fcap_usd / IDX_FLOAT_B
            demand_usd = w * TRACKING_AUM_USD_B * 1e9
            demand_sh = demand_usd * fx / base
            demand_adv = demand_sh / adv if adv else None
    # ---- step 2: flows --------------------------------
    keys = [d.replace("-", "") for d in dts]
    fnet = [(t86.get(k, {}).get(code) or {}).get("f")
            for k in keys]
    cumf = []
    run = 0.0
    for i, f in enumerate(fnet):
        if i > i0:
            run += (f or 0)
        cumf.append(run)
    prog_e = (cumf[ie] / demand_sh
              if demand_sh and v["action"] == "ADD" else None)
    prog_em1 = (cumf[ie - 1] / demand_sh
                if demand_sh and v["action"] == "ADD" else None)
    bor = [(sbl.get(k, {}).get(code) or [None, None])[1]
           for k in keys]
    b_pre = next((b for b in bor[max(0, i0 - 25):i0 + 1] if b),
                 None)
    b_0 = bor[i0] if bor[i0] else b_pre
    b_e = next((b for b in bor[ie::-1] if b), None)
    borrow_build_pre = (b_0 / b_pre if b_0 and b_pre else None)
    borrow_into_e = (b_e / b_0 if b_e and b_0 else None)
    # ---- step 3: price path ---------------------------
    m = {
        "gap1": adj(i0, min(i0 + 1, len(close) - 1)),
        "drift": adj(min(i0 + 1, ie - 1), ie - 1),
        "eff_day": adj(ie - 1, ie),
        "revert5": adj(ie, min(ie + 5, len(close) - 1)),
        "revert20": adj(ie, min(ie + 20, len(close) - 1)),
        "total_alpha": adj(i0, ie - 1),
        "pre_drift": adj(max(0, i0 - 25), i0),
        "vol_mult_eff": (vol[ie] / adv) if adv and vol[ie] else None,
        "vol_mult_win": (st.median([q for q in vol[i0 + 1:ie]
                                    if q]) / adv
                         if adv and any(vol[i0 + 1:ie]) else None),
    }
    g, d = m["gap1"], m["drift"]
    m["capture"] = (d / (g + d)) if (g + d) else None
    # ---- step 4: scores -------------------------------
    sgn = 1 if v["action"] == "ADD" else -1
    pre_directional = sgn * m["pre_drift"]
    PRE = min(1.0, max(0.0, pre_directional / PRE_DRIFT_HI / 2
                       + (0.5 if (borrow_build_pre or 1) >
                          SQZ_BORROW_HI and v["action"] == "DEL"
                          else 0)))
    SQZ = (min(1.0, max(0.0, ((borrow_build_pre or 1) - 1)
                        / (SQZ_BORROW_HI - 1)))
           if v["action"] == "DEL" else None)
    # ---- step 5: label --------------------------------
    tot = sgn * (g + d)
    if abs(g) < 0.01 and (m["vol_mult_win"] or 0) < 2:
        label = "QUIET"
    elif v["action"] == "DEL" and (SQZ or 0) > 0.6 \
            and sgn * d < 0:
        label = "SQUEEZE"
    elif PRE > 0.6 and (sgn * d) <= 0 and tot > 0:
        label = "FRONT-RUN-FADE"
    elif (sgn * d) > 0 and abs(m["revert5"]) < 0.5 * abs(tot or 1):
        label = "CLEAN-DRIFT"
    else:
        label = "MIXED"
    return {"rev": v["rev"], "code": code, "action": v["action"],
            "name": v["name"], "ann": v["ann"], "eff": v["eff"],
            "ann_src": v["ann_src"], "n_days": len(px),
            "adv": adv, "demand_adv_days": demand_adv,
            "progress_eff": prog_e, "progress_eff_minus1": prog_em1,
            "borrow_build_pre": borrow_build_pre,
            "borrow_into_eff": borrow_into_e,
            "PRE": round(PRE, 3),
            "SQZ": round(SQZ, 3) if SQZ is not None else None,
            "label": label,
            **{k: (round(x, 5) if isinstance(x, float) else x)
               for k, x in m.items()}}


def mkt_proxy():
    """0050 closes keyed by date, from its own harvested
    window union (fetched lazily by tw_event_window if absent
    — here we just read what exists)."""
    p = ROOT / "data" / "tw_mkt_proxy_0050.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main():
    W = _j("tw_event_windows.json").get("windows", {})
    # c-188: 2015 floor — see scripts/study_window.py
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "scripts"))
    from study_window import filter_windows, REASON
    _n0 = len(W)
    W = filter_windows(W)
    print(f"[study window] {_n0} -> {len(W)} windows. {REASON}")
    t86 = _j("t86_history.json")
    sbl = _j("sbl_history.json")
    margin = _j("margin_history.json")
    wf = _j("tw_member_fifs_weights.json")
    fifs = {r["code"]: r for r in wf.get("rows", [])}
    mp = mkt_proxy()
    res, skipped = [], []
    for k, v in W.items():
        if not v["px"]:
            skipped.append((k, "no price rows (TPEx?)"))
            continue
        a = analyze_window(v, mp, t86, sbl, margin, fifs)
        (skipped.append((k, a["error"])) if "error" in a
         else res.append(a))
    # ---- step 6: playbook aggregates -------------------
    def med(key, rows):
        xs = [r[key] for r in rows if r.get(key) is not None]
        return round(st.median(xs), 4) if xs else None
    agg = {}
    for act in ("ADD", "DEL"):
        rows = [r for r in res if r["action"] == act]
        agg[act] = {"n": len(rows),
                    **{k: med(k, rows) for k in
                       ("gap1", "drift", "eff_day", "revert5",
                        "revert20", "total_alpha", "pre_drift",
                        "capture", "vol_mult_eff",
                        "vol_mult_win", "PRE")}}
        from collections import Counter
        agg[act]["labels"] = dict(Counter(
            r["label"] for r in rows))
    out = {"constants": {"tracking_aum_usd_b": TRACKING_AUM_USD_B,
                         "pre_drift_hi": PRE_DRIFT_HI,
                         "sqz_borrow_hi": SQZ_BORROW_HI,
                         "note": "registered before Aug-26 "
                                 "grading"},
           "market_adjustment": ("0050" if mp else
                                 "NONE - raw returns (proxy "
                                 "not harvested yet)"),
           "n_analyzed": len(res), "skipped": skipped,
           "windows": res, "playbook": agg}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"{len(res)} windows analyzed, {len(skipped)} skipped")
    for act in ("ADD", "DEL"):
        a = agg[act]
        print(f"{act}: n={a['n']} gap1 {a['gap1']} drift "
              f"{a['drift']} eff {a['eff_day']} rev5 "
              f"{a['revert5']} | labels {a['labels']}")
    print(f"-> {OUT.name}")


if __name__ == "__main__":
    main()
