"""Multi-market event-window analysis (c-129) — the TW
framework applied to every harvested APAC market.

Price-path metrics + labels per window (framework steps 0, 3,
5, 6); flow overlays only where flow data exists (TW: t86/SBL;
AU: ASIC shorts -> SQZ). Per-market playbooks + the
cross-market comparison table.

Coverage discipline: each market carries its measured coverage
and its survivorship status — India/Taiwan are delisted-safe
(day-files); Yahoo markets are SURVIVORS-ONLY and their DEL
rows are biased toward names that lived (stated on every
output, incl. the page).

Usage:  py scripts\\apac_event_analyze.py
Output: data/apac_event_playbooks.json
"""
import json
import statistics as st
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "data" / "apac_event_windows"
OUT = ROOT / "data" / "apac_event_playbooks.json"


def _metrics(v):
    px = v["px"]
    if len(px) < 10:
        return None
    dts = [r["d"] for r in px]
    close = [r["c"] for r in px]
    vol = [r["v"] for r in px]
    i0 = None
    for i, d in enumerate(dts):
        if d <= v["ann"]:
            i0 = i
    ie = None
    for i, d in enumerate(dts):
        if d <= v["eff"]:
            ie = i
    if i0 is None or ie is None or ie <= i0 + 1:
        return None

    def ret(a, b):
        return close[b] / close[a] - 1
    adv = st.median([q for q in vol[max(0, i0 - 20):i0] if q]
                    or [1])
    m = {"gap1": ret(i0, min(i0 + 1, len(close) - 1)),
         "drift": ret(min(i0 + 1, ie - 1), ie - 1),
         "eff_day": ret(ie - 1, ie),
         "revert5": ret(ie, min(ie + 5, len(close) - 1)),
         # c-195: 30 SESSIONS, not 25. Bill asked for a month
         # before the announcement; the harvester now fetches 45
         # calendar days (~31 sessions) precisely so this can be
         # a full trading month. pre_sessions records what was
         # actually available, because a window clipped by the
         # data floor computes a shorter drift under the same
         # name and would otherwise be silently incomparable.
         "pre_drift": ret(max(0, i0 - 30), i0),
         "pre_sessions": min(i0, 30),
         "pre_full": i0 >= 30,
         "total_alpha": ret(i0, ie - 1),
         "vol_mult_eff": (vol[ie] / adv
                          if adv and vol[ie] else None)}
    sgn = 1 if v["action"] == "ADD" else -1
    g, d = m["gap1"], m["drift"]
    tot = sgn * (g + d)
    if abs(g) < 0.01 and (m["vol_mult_eff"] or 0) < 2:
        lab = "QUIET"
    elif sgn * m["pre_drift"] > 0.05 and sgn * d <= 0 and tot > 0:
        lab = "FRONT-RUN-FADE"
    elif sgn * d > 0 and abs(m["revert5"]) < 0.5 * abs(tot or 1):
        lab = "CLEAN-DRIFT"
    else:
        lab = "MIXED"
    m["label"] = lab
    return m


def main():
    res = {}
    # Taiwan from its own (richer) pipeline
    twm = ROOT / "data" / "event_window_metrics.json"
    if twm.exists():
        tw = json.loads(twm.read_text(encoding="utf-8"))
        res["Taiwan"] = {
            "n": tw["n_analyzed"],
            "survivorship": "DELISTED-SAFE (TWSE day-files)",
            "flows": "t86 + SBL + margin (full)",
            "playbook": tw["playbook"]}
    for p in sorted(DIR.glob("*.json")):
        mkt = p.stem
        d = json.loads(p.read_text(encoding="utf-8"))
        rows = []
        for v in d["windows"].values():
            if not v.get("px"):
                continue
            m = _metrics(v)
            if m:
                rows.append({"action": v["action"], **m})
        if not rows:
            continue
        pb = {}
        for act in ("ADD", "DEL"):
            g = [r for r in rows if r["action"] == act]
            if not g:
                continue

            def med(k):
                xs = [r[k] for r in g if r.get(k) is not None]
                return round(st.median(xs), 4) if xs else None
            pb[act] = {"n": len(g),
                       **{k: med(k) for k in
                          ("gap1", "drift", "eff_day",
                           "revert5", "pre_drift",
                           "total_alpha", "vol_mult_eff")},
                       "labels": dict(Counter(r["label"]
                                              for r in g))}
        n_all = len(d["windows"])
        n_px = sum(1 for v in d["windows"].values()
                   if v.get("px"))
        src = next((v.get("src", "") for v in
                    d["windows"].values()), "")
        res[mkt] = {
            "n": len(rows), "coverage": f"{n_px}/{n_all}",
            "survivorship": ("DELISTED-SAFE (day-files)"
                             if "bhavcopy" in src else
                             "SURVIVORS ONLY (Yahoo) — DEL "
                             "side biased toward names that "
                             "lived"),
            "flows": ("ASIC daily shorts (harvested)"
                      if mkt == "Australia" else
                      "none yet (see terminal harvesters)"),
            "playbook": pb}
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"{'market':12} {'n':>4} {'ADD drift':>10} "
          f"{'DEL drift':>10} {'ADD rev5':>9} {'DEL rev5':>9}")
    for mkt, r in sorted(res.items()):
        pb = r["playbook"]
        ad = pb.get("ADD", {})
        dl = pb.get("DEL", {})
        print(f"{mkt:12} {r['n']:>4} "
              f"{str(ad.get('drift', '—')):>10} "
              f"{str(dl.get('drift', '—')):>10} "
              f"{str(ad.get('revert5', '—')):>9} "
              f"{str(dl.get('revert5', '—')):>9}")
    print(f"-> {OUT.name}")


if __name__ == "__main__":
    main()
