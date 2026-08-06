"""The anticipation clock — WHEN does pre-positioning start,
relative to the announcement? (c-83)

For every MSCI TW deletion 2015-2026 (78 name-events, 34
reviews): SBL borrow balance from 120 trading days before the
announcement to 10 after, expressed as the CHANGE from that
name's own base period (the first 20 slots, -120..-101), in
ADV-days. LEFT-CENSORING CAVEAT: at BOTH lookbacks tried (-60,
-120) the detected start hugs the baseline edge — builds begin
before the window can see. At ~5 months out, "this-review
anticipation" and "chronic shorts riding a declining name"
blend; the clean index-specific reading is the CONTROL-ADJUSTED
LEVEL AT ANNOUNCEMENT (~4.5 ADV-days) and the near-zero
INCREMENT in the ann->eff window. Matched-decline controls =
declared refinement, not built.
Controls per event: all other watch names (non-adds/dels), same
transform, per-day median -> the market's ambient borrow drift.
The clock = deletion median minus control median.

Secondary panels: the addition borrow-FADE analog, and the
cumulative T86 foreign-net analog (real-money leg; NOTE shorts
do not print in T86 — borrow is the short leg's instrument).

DESCRIPTIVE CALIBRATION, not a hypothesis grade: the timing
curve informs when monitoring should switch on (registry v3 /
H11 family is the locked home for tradeable anticipation
claims). Start-day rule DECLARED in code: first relative day
where the deletion-minus-control median >= 0.25 ADV-days and
stays there for 5 consecutive trading days.

Usage: py scripts\\anticipation_clock.py
Output: data/anticipation_clock.json +
        reports/anticipation_clock.html
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REL_LO, REL_HI = -120, 10
BASE = range(0, 20)             # first 20 slots = -60..-41
THRESH, SUSTAIN = 0.25, 5


def _j(name):
    return json.loads((ROOT / "data" / name).read_text())


def curves():
    vint = _j("tw_vintage_cache.json")
    sbl = _j("sbl_history.json")
    t86 = _j("t86_history.json")
    events = _j("msci_tw_events.json")
    px_all = {}
    for k in vint:
        if k.startswith("px|"):
            code = k.split("|")[1]
            px_all[code] = sorted(
                (r["date"], r["Trading_Volume"])
                for r in vint[k])

    def one(code, ann):
        px = px_all.get(code)
        if not px:
            return None
        days = [d for d, _ in px]
        ai = next((i for i, d in enumerate(days) if d >= ann),
                  None)
        if ai is None or ai + REL_LO < 0 \
                or ai + REL_HI >= len(px):
            return None
        window = px[ai + REL_LO: ai + REL_HI + 1]
        adv = sum(v for _, v in window[:20]) / 20
        if not adv:
            return None
        bal, fnet, last = [], [], None
        for d, _ in window:
            k = d.replace("-", "")
            s = sbl.get(k, {}).get(code)
            if s is not None:
                last = s[1]
            bal.append(last)
            t = t86.get(k, {}).get(code)
            fnet.append(t["f"] if t and t["f"] is not None
                        else 0.0)
        if bal[0] is None or sum(x is None for x in bal) > 10:
            return None
        bal = [x if x is not None else 0.0 for x in bal]
        base = sum(bal[i] for i in BASE) / len(BASE)
        cum, cf = 0.0, []
        for i, f in enumerate(fnet):
            if i >= 20:                 # accumulate from -40
                cum += f
            cf.append(cum / adv)
        return ([(b - base) / adv for b in bal], cf)

    del_b, del_f, add_b = [], [], []
    ctrl_b, ctrl_f = [], []
    per_event = []
    for key in sorted(events):
        ev = events[key]
        ann = ev["ann"]
        dels = list(ev.get("dels", {}))
        adds = list(ev.get("adds", {}))
        ev_ctrl_b, ev_ctrl_f = [], []
        for code in px_all:
            if code in dels or code in adds:
                continue
            r = one(code, ann)
            if r:
                ev_ctrl_b.append(r[0])
                ev_ctrl_f.append(r[1])
        if ev_ctrl_b:
            import statistics as st
            ctrl_b.append([st.median(c[i] for c in ev_ctrl_b)
                           for i in range(len(ev_ctrl_b[0]))])
            ctrl_f.append([st.median(c[i] for c in ev_ctrl_f)
                           for i in range(len(ev_ctrl_f[0]))])
        for code in dels:
            r = one(code, ann)
            if r:
                del_b.append(r[0])
                del_f.append(r[1])
                per_event.append((key, code, ann))
        for code in adds:
            r = one(code, ann)
            if r:
                add_b.append(r[0])
    return del_b, del_f, add_b, ctrl_b, ctrl_f, per_event


def main():
    import statistics as st

    import plotly.graph_objects as go
    del_b, del_f, add_b, ctrl_b, ctrl_f, per_event = curves()
    n = len(del_b)
    rel = list(range(REL_LO, REL_HI + 1))

    def med(cs, i):
        return st.median(c[i] for c in cs)

    def q(cs, i, p):
        v = sorted(c[i] for c in cs)
        return v[int(p * (len(v) - 1))]

    m_del = [med(del_b, i) for i in range(len(rel))]
    lo_d = [q(del_b, i, 0.25) for i in range(len(rel))]
    hi_d = [q(del_b, i, 0.75) for i in range(len(rel))]
    m_ctl = [med(ctrl_b, i) for i in range(len(rel))]
    diff = [a - b for a, b in zip(m_del, m_ctl)]
    m_add = ([med(add_b, i) for i in range(len(rel))]
             if add_b else [])
    mf_del = [med(del_f, i) for i in range(len(rel))]
    mf_ctl = [med(ctrl_f, i) for i in range(len(rel))]

    start = None
    for i in range(len(rel) - SUSTAIN):
        if all(diff[j] >= THRESH
               for j in range(i, i + SUSTAIN)):
            start = rel[i]
            break

    # per-name start days (same rule on each curve minus ctrl)
    starts = []
    for c in del_b:
        d1 = [a - b for a, b in zip(c, m_ctl)]
        s = next((rel[i] for i in range(len(rel) - SUSTAIN)
                  if all(d1[j] >= THRESH
                         for j in range(i, i + SUSTAIN))), None)
        if s is not None:
            starts.append(s)

    out = {"n_del_curves": n, "n_add_curves": len(add_b),
           "n_events": len(ctrl_b),
           "rule": f"diff >= {THRESH} ADV-days sustained "
                   f"{SUSTAIN}d (DECLARED, descriptive)",
           "clock_start_rel_day": start,
           "per_name_start_median": (st.median(starts)
                                     if starts else None),
           "per_name_start_n": len(starts),
           "share_with_detectable_build": round(
               len(starts) / n, 2),
           "median_build_at_ann_advdays": m_del[rel.index(0)]
           - m_ctl[rel.index(0)],
           "median_build_at_eff_advdays": diff[-1],
           "rel": rel, "median_del": m_del,
           "median_ctrl": m_ctl, "diff": diff,
           "median_add": m_add, "f_del": mf_del,
           "f_ctrl": mf_ctl}
    (ROOT / "data" / "anticipation_clock.json").write_text(
        json.dumps(out, indent=1))

    f1 = go.Figure()
    f1.add_scatter(x=rel, y=hi_d, line_width=0,
                   showlegend=False)
    f1.add_scatter(x=rel, y=lo_d, fill="tonexty",
                   line_width=0, name="deletions IQR")
    f1.add_scatter(x=rel, y=m_del, name=f"deletions (n={n})",
                   line_color="crimson")
    f1.add_scatter(x=rel, y=m_ctl, name="controls",
                   line_color="gray")
    f1.add_vline(x=0, line_dash="dash")
    f1.update_layout(title="Borrow build vs announcement day "
                     "(0 = announcement; dashed)",
                     xaxis_title="trading days vs announcement",
                     yaxis_title="Δ borrow balance, ADV-days",
                     height=450)
    f2 = go.Figure()
    f2.add_scatter(x=rel, y=diff, name="del minus ctrl",
                   line_color="black")
    if m_add:
        f2.add_scatter(x=rel, y=m_add,
                       name=f"adds (n={len(add_b)})",
                       line_color="seagreen")
    f2.add_hline(y=THRESH, line_dash="dot")
    if start is not None:
        f2.add_vline(x=start, line_dash="dash",
                     line_color="crimson")
    f2.add_vline(x=0, line_dash="dash")
    f2.update_layout(title=f"THE CLOCK: excess deletion borrow "
                     f"build (start day = {start})",
                     xaxis_title="trading days vs announcement",
                     yaxis_title="ADV-days", height=450)
    f3 = go.Figure()
    f3.add_scatter(x=rel, y=mf_del, name="deletions",
                   line_color="crimson")
    f3.add_scatter(x=rel, y=mf_ctl, name="controls",
                   line_color="gray")
    f3.add_vline(x=0, line_dash="dash")
    f3.update_layout(title="Cumulative FOREIGN net flow from "
                     "day -40 (T86; the real-money leg — "
                     "shorts print in borrow, not here)",
                     xaxis_title="trading days vs announcement",
                     yaxis_title="cum foreign net, ADV-days",
                     height=450)
    rep = ROOT / "reports"
    rep.mkdir(exist_ok=True)
    html = ["<html><head><meta charset='utf-8'><title>"
            "Anticipation clock</title></head><body>"
            "<h1>The anticipation clock (TW deletions "
            "2015-2026)</h1>"
            f"<pre>{json.dumps({k: v for k, v in out.items() if not isinstance(v, list)}, indent=1)}</pre>"]
    for i, f in enumerate((f1, f2, f3)):
        html.append(f.to_html(full_html=False,
                              include_plotlyjs="cdn"
                              if i == 0 else False))
    html.append("</body></html>")
    (rep / "anticipation_clock.html").write_text(
        "\n".join(html), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items()
                      if not isinstance(v, list)}, indent=1))
    print("written: reports/anticipation_clock.html")


if __name__ == "__main__":
    main()
