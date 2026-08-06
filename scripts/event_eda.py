"""Event EDA — exploratory analysis of one review event from the
decade caches (c-82).

Default event: MSCI 2026-05 SAIR (ann 2026-05-12, eff
2026-05-29, 7 deletions, 0 adds). Repeatable for ANY event in
the registry: py scripts\\event_eda.py "MSCI 2026-05 SAIR"

DESCRIPTIVE ONLY — this shows the data, it does not grade
hypotheses (v5 grading has its own protocol). Charts normalize
by each name's baseline ADV (mean volume, 30 trading days
ending the day before announcement) so names are comparable.

Data sources (all local): tw_vintage_cache (px/vol/shares),
sbl_history (borrow bal), t86_history (signed institutional
flow: f = foreign net, t = total net; domestic = t - f,
labeled combined), margin_history (retail long/short bal, raw
idx 5/11, lots x1000), daytrade_history (raw idx 2, shares),
blocks_history (trade rows, vol raw idx 3), auction_expost
(T-day print anatomy), tw_float_mops_v2 (floats), LAM=0.093.

Output: reports/event_eda_<eff>.html (self-contained, plotly
CDN) + reports/event_eda_<eff>.json (the numbers behind it).
Playbook: docs/EVENT_EDA_PLAYBOOK.md
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LAM = 0.093
BASE_DAYS = 30
PRE, POST = 15, 10           # context trading days around window


def _j(name):
    return json.loads((ROOT / "data" / name).read_text())


def _num(x):
    try:
        return float(str(x).replace(",", ""))
    except Exception:                          # noqa: BLE001
        return 0.0


def load_event(key):
    from agents.time_machine import MSCI_TW
    ev = MSCI_TW[key]
    return (ev["ann_date"].replace("/", "-"), ev["effective"],
            {c: "ADD" for c in ev["adds"]}
            | {c: "DEL" for c in ev["dels"]})


def build_panel(key="MSCI 2026-05 SAIR"):
    ann, eff, names = load_event(key)
    vint = _j("tw_vintage_cache.json")
    sbl = _j("sbl_history.json")
    # history now runs to today (c-82 END fix); the live cache
    # ("short", same shape but only the 18-name watch subset)
    # fills only days the history lacks — HISTORY WINS on
    # overlap (130 names/day beats 18)
    try:
        for d, v in _j("event_data_cache.json")["short"].items():
            if not sbl.get(d):
                sbl[d] = v
    except Exception:                          # noqa: BLE001
        pass
    t86 = _j("t86_history.json")
    marg = _j("margin_history.json")
    dt = _j("daytrade_history.json")
    blk = _j("blocks_history.json")
    floats = {r["code"]: (r["float_v2"], "v2")
              for r in _j("tw_float_mops_v2.json")["rows"]}
    # fallback for ex-members (v2 covers current members only):
    # live yfinance insider fetch would be another harvest — use
    # DEFAULT 0.55 explicitly labeled EST in the output
    DEFAULT_FF = 0.55
    try:
        expost = {r["code"]: r for r in
                  _j("auction_expost.json")["rows"]
                  if r["eff"] == eff}
    except Exception:                          # noqa: BLE001
        expost = {}
    panel = {}
    for code, side in names.items():
        px = sorted((r["date"], r["close"], r["Trading_Volume"])
                    for r in vint.get(f"px|{code}", []))
        days = [d for d, _, _ in px]
        if ann not in days:
            ann_i = next((i for i, d in enumerate(days)
                          if d >= ann), None)
        else:
            ann_i = days.index(ann)
        eff_i = next((i for i, d in enumerate(days)
                      if d >= eff), None)
        if ann_i is None or eff_i is None:
            continue
        lo, hi = max(0, ann_i - PRE), min(len(px), eff_i + POST)
        adv = (sum(v for _, _, v in px[ann_i - BASE_DAYS:ann_i])
               / BASE_DAYS) if ann_i >= BASE_DAYS else None
        shares = sorted((r["date"], r["NumberOfSharesIssued"])
                        for r in vint.get(f"sh|{code}", []))
        sh_at = next((s for d, s in reversed(shares)
                      if d <= ann), None)
        ff, ff_src = floats.get(code, (DEFAULT_FF, "default"))
        forced = (LAM * ff * sh_at) if (ff and sh_at) else None
        rows = []
        for i in range(lo, hi):
            d, close, vol = px[i]
            k = d.replace("-", "")
            s = sbl.get(k, {}).get(code)
            t = t86.get(k, {}).get(code)
            m = marg.get(k, {}).get(code)
            dtr = dt.get(k, {}).get(code)
            b = blk.get(k, {}).get(code, [])
            rows.append({
                "date": d, "close": close, "vol": vol,
                "vol_x_adv": vol / adv if adv else None,
                "sbl_bal": s[1] if s else None,
                "for_net": t["f"] if t else None,
                "dom_net": (t["t"] - t["f"]) if t and
                t["f"] is not None and t["t"] is not None
                else None,
                "marg_long": _num(m["raw"][5]) * 1000
                if m else None,
                "marg_short": _num(m["raw"][11]) * 1000
                if m else None,
                "dt_vol": _num(dtr["raw"][2])
                if dtr and dtr["nf"] == 5 else 0.0,
                "blk_vol": sum(_num(x["raw"][3]) for x in b),
            })
        panel[code] = {"side": side, "adv": adv,
                       "float_shares": ff * sh_at
                       if ff and sh_at else None,
                       "ff_src": ff_src,
                       "forced_est": forced,
                       "ann": ann, "eff": eff, "rows": rows,
                       "expost": expost.get(code)}
    return ann, eff, panel


def render(key="MSCI 2026-05 SAIR"):
    import plotly.graph_objects as go
    ann, eff, panel = build_panel(key)
    figs = []

    def fig(title, ytitle):
        f = go.Figure()
        f.update_layout(title=title, yaxis_title=ytitle,
                        height=420, hovermode="x unified",
                        legend_orientation="h")
        f.add_vline(x=ann, line_dash="dash", line_color="gray")
        f.add_vline(x=eff, line_dash="dash", line_color="black")
        return f

    f1 = fig("Price indexed to announcement (dashed=ann, "
             "solid=eff close)", "close / close_at_ann")
    f2 = fig("Daily volume as multiple of baseline ADV",
             "x ADV")
    f3 = fig("SBL borrow balance, days-of-ADV", "bal / ADV")
    f4 = fig("Cumulative FOREIGN net flow from announcement, "
             "days-of-ADV", "cum / ADV")
    f5 = fig("Cumulative DOMESTIC-institutional net (total - "
             "foreign, combined), days-of-ADV", "cum / ADV")
    f6 = fig("Margin balances (retail): long solid, short "
             "dotted, % of float", "% float")
    f7 = fig("Day-trade share of volume", "day-trade vol / vol")
    f8 = fig("Block volume in window, days-of-ADV", "blk / ADV")
    for code, p in panel.items():
        rows, adv = p["rows"], p["adv"]
        x = [r["date"] for r in rows]
        pann = next((r["close"] for r in rows
                     if r["date"] >= ann), None)
        f1.add_scatter(x=x, y=[r["close"] / pann for r in rows],
                       name=f"{code} {p['side']}")
        f2.add_scatter(x=x, y=[r["vol_x_adv"] for r in rows],
                       name=code)
        if adv:
            f3.add_scatter(x=x, y=[(r["sbl_bal"] or 0) / adv
                                   for r in rows], name=code)
            cum = 0.0
            ys = []
            for r in rows:
                if r["date"] >= ann and r["for_net"]:
                    cum += r["for_net"]
                ys.append(cum / adv)
            f4.add_scatter(x=x, y=ys, name=code)
            cum = 0.0
            ys = []
            for r in rows:
                if r["date"] >= ann and r["dom_net"]:
                    cum += r["dom_net"]
                ys.append(cum / adv)
            f5.add_scatter(x=x, y=ys, name=code)
            f8.add_scatter(x=x, y=[r["blk_vol"] / adv
                                   for r in rows], name=code)
        fl = p["float_shares"]
        if fl:
            f6.add_scatter(x=x, y=[100 * (r["marg_long"] or 0)
                                   / fl for r in rows],
                           name=f"{code} L")
            f6.add_scatter(x=x, y=[100 * (r["marg_short"] or 0)
                                   / fl for r in rows],
                           name=f"{code} S", line_dash="dot")
        f7.add_scatter(x=x, y=[(r["dt_vol"] / r["vol"])
                               if r["vol"] else None
                               for r in rows], name=code)
    figs = [f1, f2, f3, f4, f5, f6, f7, f8]

    # summary table
    head = ("name side | ADV | float(M sh) | forced est (x ADV) "
            "| T-day vol (x ADV) | print disl bps | T+1 revert")
    lines = []
    for code, p in panel.items():
        t_row = next((r for r in p["rows"]
                      if r["date"] >= eff), None)
        e = p["expost"] or {}
        lines.append(
            f"{code} {p['side']} | "
            f"{p['adv'] / 1e6:.1f}M | "
            + (f"{p['float_shares'] / 1e6:.0f}"
               if p["float_shares"] else "n/a") + " | "
            + (f"{p['forced_est'] / p['adv']:.1f}"
               + ("*" if p["ff_src"] == "default" else "")
               if p["forced_est"] and p["adv"] else "n/a")
            + " | "
            + (f"{t_row['vol_x_adv']:.1f}" if t_row and
               t_row["vol_x_adv"] else "n/a") + " | "
            + (f"{e.get('pressure_bps'):+.0f}"
               if e.get("pressure_bps") is not None else "n/a")
            + " | "
            + (f"{e.get('t1_revert_bps'):+.0f}"
               if e.get("t1_revert_bps") is not None else "n/a"))

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    tag = eff.replace("-", "")
    html = ["<html><head><meta charset='utf-8'>"
            f"<title>Event EDA {key}</title></head><body>"
            f"<h1>Event EDA — {key}</h1>"
            f"<p>ann {ann} | eff {eff} | names: "
            + ", ".join(f"{c}({p['side']})"
                        for c, p in panel.items())
            + "</p><p><b>DESCRIPTIVE ONLY</b> — normalized by "
            "each name's 30d pre-announcement ADV; forced est = "
            "lambda 0.093 x float shares; domestic net = total "
            "minus foreign (combined trusts+dealers, layout-"
            "safe). Vertical lines: dashed = announcement, "
            "solid = effective close.</p>"
            "<pre>" + head + "\n" + "\n".join(lines) + "</pre>"]
    for i, f in enumerate(figs):
        html.append(f.to_html(full_html=False,
                              include_plotlyjs="cdn"
                              if i == 0 else False))
    html.append("</body></html>")
    (out / f"event_eda_{tag}.html").write_text(
        "\n".join(html), encoding="utf-8")
    (out / f"event_eda_{tag}.json").write_text(json.dumps(
        {"event": key, "ann": ann, "eff": eff,
         "summary": lines,
         "panel": {c: {k: v for k, v in p.items()
                       if k != "rows"} for c, p in
                   panel.items()}}, indent=1, default=str))
    print(f"written: reports/event_eda_{tag}.html "
          f"({len(panel)} names)")
    for ln in [head] + lines:
        print(" ", ln)


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1
           else "MSCI 2026-05 SAIR")
