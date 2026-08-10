"""THE WALK — how the threshold line is actually derived (c-122).

A rank-by-rank rendering of GIMI §2.3.3 on the full Taiwan
universe, so the cutoff stops being an assertion and becomes
something you can read off a table.

WHAT THE WALK SHOWS, in the rulebook's own order:
  1. start from every listed TW company (TWSE + TPEx) priced on
     the review's Price Cutoff Date
  2. apply the Equity Universe screens (§2.2.3 full cap >=
     $537M; §2.2.4 float cap >= 50% of that) -> the Market
     Investable Equity Universe
  3. sort by FULL market cap, descending  (§2.3.3)
  4. walk down cumulating FLOAT-ADJUSTED cap
  5. the company where cumulative coverage first reaches 85%
     DEFINES the Market Size-Segment Cutoff, and its RANK is
     the Segment Number of Companies
  6. buffers hang off that cutoff: delete below 2/3x, Small-Cap
     migration above 1.5x, float gate at 50% (§3.1.5.1,
     §2.3.6.1)

FLOAT STACK, tiered by measured accuracy (spec §3c):
  factsheet-implied (top 10, exact)  >  Yahoo (2.7% median)
  >  TDCC bracket-15 proxy (16.3%, complete)
Every row carries the source that produced its float, so the
walk doubles as a data-provenance audit.

Usage:  py scripts\\tw_walk_display.py [YYYYMMDD]
Output: reports/tw_walk_<date>.html   (standalone, not wired
        into the site)
"""
import html as _h
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNI = ROOT / "data" / "tw_universe_pit.json"
EU_MIN = 0.537                       # §2.2.3, May-26 value
COVERAGE = 0.85                      # §2.3.1 Standard target

FACTSHEET_TOP10 = {                  # Jul-31-2026 factsheet
    "2330": 1848.51, "2454": 158.78, "2308": 98.86,
    "2317": 94.71, "3711": 57.28, "2303": 42.38,
    "2383": 42.09, "2881": 33.81, "2891": 33.59,
    "2345": 33.20}
NAMES = {"2330": "TSMC", "2454": "MediaTek", "2308": "Delta",
         "2317": "Hon Hai", "3711": "ASE", "2303": "UMC",
         "2383": "Elite Material", "2881": "Fubon",
         "2891": "CTBC", "2345": "Accton",
         "2834": "Taiwan Business Bank", "2408": "Nanya Tech",
         "6505": "Formosa Petrochemical", "6223": "MPI Corp"}


def float_stack(u, date):
    """Tiered float, best source first. Returns
    {code: (ff, source), calibration_dict}.

    Tier 3 is CALIBRATED, not raw. On the names where Yahoo and
    TDCC both exist, TDCC runs systematically below Yahoo —
    bracket 15 counts large domestic institutions as strategic
    when MSCI counts them as float. The ratio is measured on
    that overlap and applied to the rest, so the tail is
    corrected by evidence rather than by a chosen constant."""
    import statistics as st
    R31 = u["dates"].get("20260731", {}).get("rows", {})
    imp = {c: FACTSHEET_TOP10[c] / R31[c]["cap_usd_b"]
           for c in FACTSHEET_TOP10
           if c in R31 and R31[c].get("cap_usd_b")}
    yp = ROOT / "data" / "tw_float_yahoo.json"
    yahoo = json.loads(yp.read_text(encoding="utf-8")) if yp.exists() else {}
    rows = u["dates"][date]["rows"]
    pair = [(yahoo[c], rows[c]["ff"]) for c in yahoo
            if yahoo.get(c) and c in rows
            and rows[c].get("ff") is not None]
    k = (st.median(y / t for y, t in pair if t)
         if len(pair) >= 20 else 1.0)
    cal = {"n_overlap": len(pair), "tdcc_scale": round(k, 4),
           "yahoo_median": (round(st.median(y for y, _ in pair), 3)
                            if pair else None),
           "tdcc_median": (round(st.median(t for _, t in pair), 3)
                           if pair else None)}
    # c-139: tier 1b — MSCI's OWN member FIFs recovered by the
    # weights inversion (60 mapped members, on MSCI's rounding
    # grid). Strictly better than Yahoo for those names
    # (median |yahoo - MSCI| = 2.3pp on the overlap).
    wp = ROOT / "data" / "tw_member_fifs_weights.json"
    mfif = {}
    if wp.exists():
        mfif = {r["code"]: r["fif_weights"]
                for r in json.loads(wp.read_text(encoding="utf-8"))["rows"]}
    out = {}
    for c, r in rows.items():
        if c in imp:
            out[c] = (round(imp[c], 4), "factsheet-implied")
        elif c in mfif:
            out[c] = (mfif[c], "msci-weights-inversion")
        elif yahoo.get(c):
            out[c] = (yahoo[c], "yahoo")
        elif r.get("ff") is not None:
            out[c] = (round(min(1.0, r["ff"] * k), 4),
                      "tdcc-calibrated")
        else:
            out[c] = (0.55, "default 0.55")
    return out, cal


def walk(date="20260420"):
    u = json.loads(UNI.read_text(encoding="utf-8"))
    if date not in u["dates"]:
        raise SystemExit(f"{date} not harvested")
    rows = u["dates"][date]["rows"]
    ff, cal = float_stack(u, date)
    listed = len(rows)
    # ---- step 2: the Equity Universe screens --------------
    scr, drop_size, drop_float = {}, 0, 0
    for c, r in rows.items():
        cap = r.get("cap_usd_b") or 0
        f = ff[c][0]
        if cap < EU_MIN:
            drop_size += 1
            continue
        if cap * f < 0.5 * EU_MIN:
            drop_float += 1
            continue
        scr[c] = r
    # ---- steps 3-5: sort, cumulate, find the crossing -----
    srt = sorted(scr.items(), key=lambda x: -x[1]["cap_usd_b"])
    tot = sum(r["cap_usd_b"] * ff[c][0] for c, r in srt)
    walkrows, run, cross = [], 0.0, None
    for i, (c, r) in enumerate(srt, 1):
        f, src = ff[c]
        fc = r["cap_usd_b"] * f
        run += fc
        cov = run / tot
        if cross is None and cov >= COVERAGE:
            cross = {"rank": i, "code": c,
                     "cutoff": r["cap_usd_b"], "cov": cov}
        walkrows.append({
            "rank": i, "code": c, "name": NAMES.get(c, ""),
            "mkt": r["mkt"], "full": r["cap_usd_b"], "ff": f,
            "src": src, "fcap": fc, "cov": cov})
    return {"date": date, "fx": u["dates"][date]["fx"],
            "calibration": cal,
            "listed": listed, "drop_size": drop_size,
            "drop_float": drop_float, "screened": len(scr),
            "universe_float": tot, "crossing": cross,
            "rows": walkrows,
            "tdcc_asof": u.get("tdcc_asof")}


CSS = """
:root{--navy:#1f4e79;--mut:#5b6770;--line:#e3e7ea;--cream:#faf9f6}
body{margin:0;background:var(--cream);color:#1a1a1a;
font:14px/1.55 Calibri,Candara,Segoe UI,system-ui,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:40px 22px 80px}
h1{color:var(--navy);font-size:29px;margin:0 0 4px}
h2{color:var(--navy);font-size:20px;margin:34px 0 10px;
border-bottom:2px solid var(--navy);padding-bottom:5px}
.sub{color:var(--mut);margin:0 0 20px}
.steps{background:#fff;border:1px solid var(--line);
border-radius:6px;padding:6px 8px;margin:16px 0}
.step{display:flex;gap:12px;padding:9px 10px;
border-bottom:1px solid var(--line)}
.step:last-child{border:0}
.step .no{flex:0 0 26px;height:26px;line-height:26px;
text-align:center;background:var(--navy);color:#fff;
border-radius:50%;font-weight:700;font-size:13px}
.step .tx{flex:1}
.step .vl{flex:0 0 210px;text-align:right;font-weight:700;
color:var(--navy)}
.cite{color:var(--mut);font-size:12.5px}
table{border-collapse:collapse;font:12.5px/1.4 Consolas,
monospace;width:100%;background:#fff;margin:10px 0}
th{background:var(--navy);color:#fff;padding:6px 8px;
text-align:right;position:sticky;top:0}
th:nth-child(2),th:nth-child(3),th:nth-child(8){text-align:left}
td{padding:4px 8px;border-bottom:1px solid #eef1f3;
text-align:right}
td.l{text-align:left}
tr.cross td{background:#ffe08a;font-weight:700;
border-top:2px solid #b7791f;border-bottom:2px solid #b7791f}
tr.above td{background:#f7fbff}
.src-factsheet{color:#2e7d52;font-weight:700}
.src-yahoo{color:#1f4e79}
.src-tdcc{color:#b7791f}
.src-default{color:#c0392b;font-weight:700}
.box{background:#fff;border-left:4px solid var(--navy);
padding:12px 16px;margin:14px 0;border-radius:0 5px 5px 0}
.box.warn{border-color:#b7791f;background:#fffdf7}
.box h4{margin:0 0 6px;color:var(--navy)}
.zone{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}
.z{flex:1 1 190px;background:#fff;border:1px solid var(--line);
border-radius:5px;padding:11px 13px}
.z .l{font-size:11px;text-transform:uppercase;color:var(--mut);
letter-spacing:.5px}
.z .v{font-size:22px;font-weight:700;color:var(--navy)}
.z .n{font-size:12px;color:var(--mut)}
.cap{font-size:12.5px;color:var(--mut);font-style:italic}
.scroll{max-height:640px;overflow:auto;border:1px solid var(--line);
border-radius:5px}
"""


def render(w, target=None):
    c = w["crossing"]
    cut = c["cutoff"]
    e = _h.escape
    o = [f"<!doctype html><html lang='en'><meta charset='utf-8'>"
         f"<title>The walk — Taiwan {w['date']}</title>"
         f"<style>{CSS}</style><div class='wrap'>",
         f"<h1>The walk — how the threshold line is derived</h1>",
         f"<p class='sub'>MSCI Taiwan, price cutoff "
         f"<b>{w['date'][:4]}-{w['date'][4:6]}-{w['date'][6:]}</b>, "
         f"FX {w['fx']} TWD/USD. Every company listed in Taiwan, "
         f"walked in the rulebook's own order.</p>"]

    # ---- the six steps ---------------------------------
    o.append("<h2>The six steps</h2><div class='steps'>")
    for n, tx, cite, val in [
        (1, "Start from every listed company, priced on the "
            "cutoff date", "TWSE MI_INDEX + TPEx otc",
         f"{w['listed']:,} companies"),
        (2, "Drop those below the Equity Universe Minimum Size "
            "(full market cap)", "§2.2.3 — USD 537M",
         f"−{w['drop_size']:,}"),
        (3, "Drop those whose FLOAT cap is under half that",
         "§2.2.4 — USD 268.5M",
         f"−{w['drop_float']:,}"),
        (4, "What remains is the Market Investable Equity "
            "Universe", "the denominator for everything below",
         f"<b>{w['screened']:,} companies</b><br>"
         f"float ${w['universe_float']:,.0f}B"),
        (5, "Sort by FULL market cap, walk down cumulating "
            "FLOAT-adjusted cap", "§2.3.3",
         "see the table"),
        (6, "The company where coverage first reaches 85% "
            "defines the cutoff; its rank is the Segment "
            "Number of Companies", "§2.3.1 (85%±5%), §2.3.3",
         f"rank <b>{c['rank']}</b> · "
         f"<b>${cut:,.2f}B</b>"),
    ]:
        o.append(f"<div class='step'><div class='no'>{n}</div>"
                 f"<div class='tx'>{e(tx)}<br>"
                 f"<span class='cite'>{e(cite)}</span></div>"
                 f"<div class='vl'>{val}</div></div>")
    o.append("</div>")

    # ---- what the cutoff implies -----------------------
    o.append("<h2>What that one number then decides</h2>")
    o.append("<div class='zone'>")
    for lab, v, note in [
        ("Market Size-Segment Cutoff", f"${cut:,.2f}B",
         f"full cap of rank {c['rank']} ({e(c['code'])})"),
        ("Deletion floor — 2/3 ×", f"${2 / 3 * cut:,.2f}B",
         "§3.1.5.1 lower buffer"),
        ("Small-Cap migration — 1.5 ×", f"${1.5 * cut:,.2f}B",
         "§3.1.5.1 upper buffer"),
        ("Float gate — 50% ×", f"${0.5 * cut:,.2f}B",
         "§2.3.6.1 (existing: ⅔ of it)"),
    ]:
        o.append(f"<div class='z'><div class='l'>{e(lab)}</div>"
                 f"<div class='v'>{v}</div>"
                 f"<div class='n'>{e(note)}</div></div>")
    o.append("</div>")

    if target:
        o.append(
            "<div class='box warn'><h4>Scored against MSCI's "
            "published answer</h4><p>For this review MSCI ended "
            f"with <b>{target['n']} constituents</b> and the "
            f"smallest of them measured <b>${target['cutoff']}B"
            f"</b> full cap on this date — so the true Segment "
            f"Number of Companies is {target['n']} and the true "
            f"cutoff is about ${target['cutoff']}B.</p>"
            f"<p>This walk lands at rank <b>{c['rank']}</b> "
            f"(<b>{c['rank'] - target['n']:+d}</b>) and "
            f"<b>${cut:,.2f}B</b>.</p>"
            "<p>The two gaps have different causes and it is "
            "worth separating them. The <b>rank</b> is set by "
            "the float estimates, and it is now close. The "
            "<b>dollar cutoff</b> is still high because our "
            "universe contains companies MSCI excludes — we "
            "have applied only the two size screens (§2.2.3, "
            "§2.2.4), not the liquidity/ATVR test, the "
            "ineligible-securities list, or the foreign-room "
            "floor. Every name MSCI drops that we keep pushes "
            "our rank-N company higher up the cap ladder. "
            "Prices, shares, foreign holdings and FX are "
            "exchange data, and the top-10 floats tie to the "
            "factsheet exactly, so neither gap is coming from "
            "there.</p></div>")

    # ---- provenance -------------------------------------
    from collections import Counter
    cnt = Counter(r["src"] for r in w["rows"])
    fcap = Counter()
    for r in w["rows"]:
        fcap[r["src"]] += r["fcap"]
    o.append("<h2>Where each float number came from</h2>"
             "<table><tr><th class='l'>source</th>"
             "<th>companies</th><th>share of universe float</th>"
             "<th class='l'>measured accuracy vs MSCI</th></tr>")
    k = w["calibration"]
    acc = {"factsheet-implied": "exact — it is MSCI's own number",
           "yahoo": "2.7% median absolute error (top-10 test)",
           "tdcc-calibrated":
               f"raw proxy x{k['tdcc_scale']}, the ratio measured "
               f"on {k['n_overlap']} names where Yahoo also exists",
           "default 0.55": "unmeasured — a placeholder"}
    for s, n in cnt.most_common():
        o.append(f"<tr><td class='l'><span class='src-"
                 f"{s.split('-')[0].split()[0]}'>{e(s)}</span>"
                 f"</td><td>{n:,}</td>"
                 f"<td>{100 * fcap[s] / w['universe_float']:.1f}%"
                 f"</td><td class='l'>{e(acc.get(s, ''))}</td>"
                 f"</tr>")
    o.append("</table><p class='cap'>The tiering is deliberate: "
             "float error at the top of the ladder moves the "
             "crossing hard, while tail error averages out "
             "across hundreds of names — so the expensive, "
             "accurate sources are spent where they matter.</p>")

    # ---- the walk ---------------------------------------
    o.append("<h2>The walk itself</h2>"
             "<p class='cap'>Sorted by full market cap. The "
             "highlighted row is where cumulative float "
             "coverage first crosses 85% — that row IS the "
             "cutoff. Rows are shown to rank "
             f"{min(len(w['rows']), c['rank'] + 40)}.</p>"
             "<div class='scroll'><table><tr><th>rank</th>"
             "<th class='l'>code</th><th class='l'>name</th>"
             "<th>full $B</th><th>ff</th><th>float $B</th>"
             "<th>cum cov %</th><th class='l'>float source</th>"
             "</tr>")
    for r in w["rows"][:c["rank"] + 40]:
        cls = ("cross" if r["rank"] == c["rank"]
               else "above" if r["rank"] < c["rank"] else "")
        sc = r["src"].split("-")[0].split()[0]
        o.append(
            f"<tr class='{cls}'><td>{r['rank']}</td>"
            f"<td class='l'>{e(r['code'])}</td>"
            f"<td class='l'>{e(r['name'])}</td>"
            f"<td>{r['full']:,.2f}</td><td>{r['ff']:.3f}</td>"
            f"<td>{r['fcap']:,.2f}</td>"
            f"<td>{100 * r['cov']:.2f}</td>"
            f"<td class='l'><span class='src-{sc}'>"
            f"{e(r['src'])}</span></td></tr>")
    o.append("</table></div>")

    o.append(
        "<div class='box'><h4>Reading the walk</h4><p>Notice "
        "how little of the work the small companies do. The "
        "first row alone carries about half the market's float, "
        "so an error in ONE large-cap float factor moves the "
        "crossing by several ranks — while being wrong about a "
        "hundred tail names barely moves it at all. That "
        "asymmetry is why the float sources are tiered rather "
        "than uniform, and it is the single most important "
        "thing this table shows.</p></div>")
    o.append(
        f"<p class='cap'>TDCC dispersion as of "
        f"{e(str(w.get('tdcc_asof')))} — the float proxy "
        "post-dates the price date; float moves slowly. Prices, "
        "shares outstanding, foreign holdings and the foreign "
        "ownership limit are all dated to the price cutoff "
        "itself.</p></div></html>")
    return "".join(o)


def main(date="20260420"):
    w = walk(date)
    target = ({"n": 77, "cutoff": 5.19}
              if date == "20260420" else None)
    html = render(w, target)
    d = ROOT / "reports"
    d.mkdir(exist_ok=True)
    p = d / f"tw_walk_{date}.html"
    p.write_text(html, encoding="utf-8")
    c = w["crossing"]
    print(f"{w['listed']:,} listed -> {w['screened']:,} screened "
          f"| universe float ${w['universe_float']:,.0f}B")
    print(f"85% crossing: rank {c['rank']} = {c['code']} at "
          f"${c['cutoff']:,.2f}B  (target rank 77, $5.19B)")
    print(f"-> {p}  ({p.stat().st_size / 1024:.0f} KB)")
    return p


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "20260420")
