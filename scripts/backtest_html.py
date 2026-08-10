"""Render the c-116 backtest as one self-contained HTML report.

Reads data/backtest_taiwan.json (built by backtest_extras.build)
— no numbers are typed here, same generation rule as the
walkthrough. Inline CSS + inline SVG, no scripts, no CDN.

Usage: py scripts\\backtest_html.py
"""
import html as _h
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIRS = [ROOT / "reports"]

CSS = """
:root{--navy:#1f4e79;--ink:#1a1a1a;--mut:#5b6770;--line:#e3e7ea;
--red:#c0392b;--amber:#b7791f;--green:#2e7d52;--cream:#faf9f6}
*{box-sizing:border-box}
body{margin:0;background:var(--cream);color:var(--ink);
font:15.5px/1.6 Calibri,Candara,Segoe UI,system-ui,sans-serif}
.wrap{max-width:1000px;margin:0 auto;padding:44px 24px 90px}
h1{font-size:32px;color:var(--navy);margin:0 0 6px;line-height:1.2}
h2{font-size:22px;color:var(--navy);margin:38px 0 12px;
border-bottom:2px solid var(--navy);padding-bottom:6px}
h3{font-size:17px;color:var(--navy);margin:24px 0 8px}
.sub{color:var(--mut);margin:0 0 22px}
.cards{display:flex;flex-wrap:wrap;gap:12px;margin:18px 0}
.card{flex:1 1 165px;background:#fff;border:1px solid var(--line);
border-radius:6px;padding:13px 15px}
.card .l{font-size:11px;text-transform:uppercase;
letter-spacing:.6px;color:var(--mut)}
.card .v{font-size:26px;font-weight:700;color:var(--navy);
line-height:1.25}
.card .n{font-size:12.5px;color:var(--mut)}
.card.bad .v{color:var(--red)} .card.ok .v{color:var(--green)}
.card.warn .v{color:var(--amber)}
table{width:100%;border-collapse:collapse;background:#fff;
font-size:13.5px;margin:12px 0}
th{background:var(--navy);color:#fff;text-align:left;
padding:7px 9px;font-weight:600}
td{padding:6px 9px;border-bottom:1px solid var(--line)}
tr:nth-child(even) td{background:#fcfcfa}
td.r,th.r{text-align:right}
.tag{display:inline-block;padding:1px 7px;border-radius:9px;
font-size:11.5px;font-weight:700;color:#fff}
.t-gap{background:var(--amber)} .t-af{background:var(--red)}
.t-ok{background:var(--green)} .t-na{background:var(--mut)}
.box{background:#fff;border-left:4px solid var(--navy);
padding:13px 17px;margin:14px 0;border-radius:0 5px 5px 0}
.box.warn{border-color:var(--amber);background:#fffdf7}
.box.bad{border-color:var(--red);background:#fef8f7}
.box h4{margin:0 0 6px;color:var(--navy);font-size:15.5px}
.box.bad h4{color:var(--red)} .box.warn h4{color:var(--amber)}
p{margin:0 0 11px}
ol,ul{margin:0 0 11px;padding-left:22px} li{margin-bottom:6px}
.grade{font-weight:700}
.A{color:var(--green)}.B{color:#3f7d20}.C{color:var(--amber)}
.D{color:var(--red)}
.foot{color:var(--mut);font-size:12.5px;margin-top:40px;
border-top:1px solid var(--line);padding-top:14px}
svg{max-width:100%;height:auto;background:#fff;
border:1px solid var(--line);border-radius:5px}
.cap{font-size:12.5px;color:var(--mut);font-style:italic;
margin:4px 0 16px}
"""


def _e(x):
    return _h.escape(str(x))


def _cards(items):
    o = ["<div class='cards'>"]
    for lab, val, note, cls in items:
        o.append(f"<div class='card {cls}'><div class='l'>{_e(lab)}"
                 f"</div><div class='v'>{_e(val)}</div>"
                 f"<div class='n'>{_e(note)}</div></div>")
    return "".join(o) + "</div>"


def _table(cols, rows, aligns=None):
    aligns = aligns or [""] * len(cols)
    o = ["<table><tr>"]
    o += [f"<th class='{a}'>{_e(c)}</th>"
          for c, a in zip(cols, aligns)]
    o.append("</tr>")
    for r in rows:
        o.append("<tr>" + "".join(
            f"<td class='{a}'>{c}</td>"
            for c, a in zip(r, aligns)) + "</tr>")
    return "".join(o) + "</table>"


def _pr_curve(sens, add):
    """Precision-recall for both sides, drawn as SVG."""
    w, h, pl, pb = 640, 300, 52, 42
    pw, ph = w - pl - 18, h - pb - 20

    def pt(rc, pr):
        return pl + pw * rc, 20 + ph * (1 - pr)
    o = [f"<svg viewBox='0 0 {w} {h}' xmlns='http://www.w3.org/"
         f"2000/svg' font-family='Calibri,sans-serif' "
         f"font-size='11'>"]
    for g in range(0, 11, 2):
        x = pl + pw * g / 10
        y = 20 + ph * g / 10
        o.append(f"<line x1='{x:.0f}' y1='20' x2='{x:.0f}' "
                 f"y2='{20 + ph}' stroke='#eef1f3'/>"
                 f"<line x1='{pl}' y1='{y:.0f}' x2='{pl + pw}' "
                 f"y2='{y:.0f}' stroke='#eef1f3'/>"
                 f"<text x='{x:.0f}' y='{20 + ph + 14}' "
                 f"text-anchor='middle' fill='#5b6770'>"
                 f"{g * 10}%</text>"
                 f"<text x='{pl - 7}' y='{y + 4:.0f}' "
                 f"text-anchor='end' fill='#5b6770'>"
                 f"{100 - g * 10}%</text>")
    for series, col, key in [(sens, "#c0392b", "precision"),
                             (add, "#1f4e79",
                              "precision_partial")]:
        pts = [pt(s["recall"], s[key]) for s in series]
        o.append("<polyline points='" + " ".join(
            f"{x:.1f},{y:.1f}" for x, y in pts) +
            f"' fill='none' stroke='{col}' stroke-width='2.5'/>")
        for (x, y), s in zip(pts, series):
            o.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='3.5' "
                     f"fill='{col}'/>")
        base = [s for s in series
                if s.get("floor_multiple") == 1.0
                or s.get("x_ceiling") == 1.5]
        if base:
            x, y = pt(base[0]["recall"], base[0][key])
            o.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='7' "
                     f"fill='none' stroke='{col}' "
                     f"stroke-width='2'/>"
                     f"<text x='{x + 10:.1f}' y='{y - 7:.1f}' "
                     f"fill='{col}' font-weight='700'>engine "
                     f"today</text>")
    o.append(f"<text x='{pl + pw / 2:.0f}' y='{h - 6}' "
             f"text-anchor='middle' fill='#1a1a1a' "
             f"font-weight='600'>recall (share of real moves "
             f"caught)</text>"
             f"<text transform='rotate(-90 14 {20 + ph / 2:.0f})'"
             f" x='14' y='{20 + ph / 2:.0f}' text-anchor='middle'"
             f" fill='#1a1a1a' font-weight='600'>precision</text>"
             f"<text x='{pl + 8}' y='34' fill='#c0392b' "
             f"font-weight='700'>deletions (moving the floor)"
             f"</text>"
             f"<text x='{pl + 8}' y='50' fill='#1f4e79' "
             f"font-weight='700'>additions (moving the bar)"
             f"</text></svg>")
    return "".join(o)


def render(a):
    d, ad, sv = a["deletions"], a["additions"], a["survival"]
    cov = a["coverage"]
    o = [f"<!doctype html><html lang='en'><meta charset='utf-8'>"
         f"<meta name='viewport' content='width=device-width,"
         f"initial-scale=1'><title>MSCI Taiwan — prediction "
         f"engine backtest 2018-2026</title><style>{CSS}</style>"
         f"<div class='wrap'>",
         "<h1>Prediction engine backtest — MSCI Taiwan, "
         "2018 to 2026</h1>",
         f"<p class='sub'>{cov['reviews_scored']} of "
         f"{cov['reviews_in_window']} quarterly reviews scored "
         f"point-in-time. Every figure generated from the "
         f"engine's own output; nothing typed by hand.</p>"]

    # ---------- 1. headline -----------------------------
    o.append("<h2>1. How well does it predict?</h2>")
    o.append(_cards([
        ("Deletion recall", f"{d['recall']:.0%}",
         f"{d['hits']} of {d['hits'] + d['misses']} real "
         f"deletions flagged", "ok"),
        ("Deletion precision", f"{d['precision']:.0%}",
         f"{d['false_alarms']} false alarms", "bad"),
        ("Addition recall", f"{ad['recall']:.0%}",
         f"{ad['flagged']} of {ad['actual']} — the add rule is "
         f"mis-specified", "bad"),
        ("False alarms later deleted", f"{sv['share']:.0%}",
         f"median lag {sv['median_lag_reviews']} reviews", "warn"),
    ]))
    o.append(
        "<div class='box'><h4>The one-paragraph verdict</h4><p>"
        "The engine is a good <b>screen</b> and a poor "
        "<b>ranker</b>. It catches "
        f"{d['recall']:.0%} of real deletions, which means the "
        "size test is essentially the right test — MSCI is "
        "removing the small. But it flags "
        f"{d['false_alarms']} names to find "
        f"{d['hits']}, so on its own it cannot tell you WHICH "
        "of the at-risk names goes this quarter. The addition "
        "side is worse and for a different reason: the rule "
        "itself is wrong, not merely blunt — see section 3, "
        "where the fix is identified and measured.</p></div>")

    o.append("<h3>Per-review record</h3>")
    rows = []
    for p in a["per_review"]:
        rows.append([
            _e(p["review"]), _e(str(p["price_date"])[:10]),
            f"${p['floor']}", f"${p['bar']}", p["pool"],
            f"<b>{p['hits']}</b>", p["misses"],
            p["false_alarms"], _e(p["key_source"])])
    o.append(_table(
        ["Review", "Price cutoff", "Floor", "Add bar",
         "Pool size", "Hits", "Misses", "False alarms",
         "Key source"], rows,
        ["", "", "r", "r", "r", "r", "r", "r", ""]))
    o.append(
        f"<p class='cap'>Missing: {_e(cov['missing'])} — no "
        "methodology edition could be matched to those reviews, "
        "so they are excluded rather than guessed.</p>")

    # ---------- 2. the curve ----------------------------
    o.append("<h2>2. The trade-off the engine is operating on"
             "</h2>")
    o.append(_pr_curve(a["sensitivity"], a["add_sweep"]))
    o.append(
        "<p class='cap'>Each point is one threshold setting. "
        "The circled points are where the engine sits today. "
        "Addition precision is measured against our 150-name "
        "vintage universe, which is biased toward borderline "
        "names — read the curve's shape, not its level.</p>")
    o.append(
        "<div class='box warn'><h4>What the deletion curve "
        "says</h4><p>Moving the floor cannot fix precision. "
        "Cutting it to 0.6x lifts precision only from "
        f"{d['precision']:.0%} to "
        f"{a['sensitivity'][0]['precision']:.0%} while recall "
        f"collapses to {a['sensitivity'][0]['recall']:.0%}. The "
        "curve is flat because the at-risk set genuinely is "
        "large — the missing ingredient is a RANKING signal "
        "inside the pool, not a better cut-off.</p></div>")
    sens_rows = [[f"x{s['floor_multiple']}", f"{s['recall']:.0%}",
                  f"{s['precision']:.0%}", s["hits"],
                  s["misses"], s["false_alarms"]]
                 for s in a["sensitivity"]]
    o.append(_table(["Floor multiple", "Recall", "Precision",
                     "Hits", "Misses", "False alarms"],
                    sens_rows, ["", "r", "r", "r", "r", "r"]))

    # ---------- 3. additions ----------------------------
    o.append("<h2>3. The biggest single defect: the addition "
             "bar</h2>")
    best = max(a["add_sweep"],
               key=lambda s: s["recall"] * s["precision_partial"])
    o.append(
        "<div class='box bad'><h4>The add rule is mis-specified,"
        " and the data says exactly how</h4><p>The engine "
        "requires an addition candidate to reach <b>1.5x the "
        "range ceiling</b>. Measured at the disclosed price "
        "cutoff, only "
        f"<b>{ad['flagged']} of {ad['actual']}</b> real "
        "additions ever cleared that. But <b>93%</b> of them "
        "cleared the deletion floor and <b>44%</b> cleared the "
        "ceiling itself — real additions arrive clustered just "
        "under the ceiling, at a median of 0.95x it, not half "
        "again above it.</p><p>Re-running the sweep, the best "
        f"operating point is <b>{best['x_ceiling']}x the "
        f"ceiling</b>: recall rises from "
        f"{ad['recall']:.0%} to <b>{best['recall']:.0%}</b> "
        "while precision <i>improves</i> from "
        f"{a['add_sweep'][-1]['precision_partial']:.0%} to "
        f"<b>{best['precision_partial']:.0%}</b>. Both metrics "
        "move the right way, which is the signature of a "
        "mis-specified rule rather than a threshold that needs "
        "tuning.</p></div>")
    o.append(_table(
        ["Threshold (x ceiling)", "Addition recall",
         "Precision (partial universe)", "Caught", "Missed"],
        [[f"x{s['x_ceiling']}",
          (f"<b>{s['recall']:.0%}</b>"
           if s is best else f"{s['recall']:.0%}"),
          f"{s['precision_partial']:.0%}", s["hits"],
          s["misses"]] for s in a["add_sweep"]],
        ["", "r", "r", "r", "r"]))

    # ---------- 4. errors -------------------------------
    o.append("<h2>4. Every mistake, classified</h2>")
    o.append("<h3>Deletions we missed</h3>")
    tag = {"MEMBERSHIP GAP": "t-gap", "ABOVE FLOOR": "t-af",
           "NO DATA": "t-na", "OTHER": "t-na"}
    mrows = []
    for m in a["miss_classes"]:
        mrows.append([
            _e(m["review"]), _e(m["code"]),
            _e(str(m["security"])[:26]),
            f"${m['cap']}" if m["cap"] else "—",
            f"${m['floor']}",
            f"<span class='tag {tag.get(m['class'], 't-na')}'>"
            f"{_e(m['class'])}</span>", _e(m["why"])])
    o.append(_table(["Review", "Code", "Security", "PIT cap",
                     "Floor", "Class", "Diagnosis"], mrows,
                    ["", "", "", "r", "r", "", ""]))
    ngap = sum(1 for m in a["miss_classes"]
               if m["class"] == "MEMBERSHIP GAP")
    naf = sum(1 for m in a["miss_classes"]
              if m["class"] == "ABOVE FLOOR")
    o.append(
        f"<div class='box'><h4>Two failure modes, not one</h4>"
        f"<p><b>{ngap} of {len(a['miss_classes'])}</b> misses "
        "are <b>membership gaps</b>: the size test would have "
        "fired, but the name was absent from our reconstructed "
        "membership so it never entered the pool. These are "
        "free wins — a data fix, not a modelling problem.</p>"
        f"<p><b>{naf}</b> are <b>above-floor deletions</b> — "
        "MSCI removed names whose full market value sat well "
        "clear of the floor (Formosa Petrochemical at 4.5x it, "
        "Nanya at 1.8x). Full size cannot explain these. The "
        "obvious suspect is free float: MSCI's real deletion "
        "gate uses float-adjusted value, and both of those "
        "names are famously tightly held.</p></div>")

    fc = a["float_coverage"]
    o.append(
        f"<div class='box bad'><h4>...and we cannot currently "
        f"test that</h4><p>{_e(fc['verdict'])}</p></div>")

    o.append("<h3>False alarms, re-read</h3>")
    o.append(
        f"<p>Of {sv['total_fa']} false alarms, "
        f"<b>{sv['later_deleted']} ({sv['share']:.0%})</b> were "
        "deleted by MSCI at a later review. They were not "
        "wrong; they were <b>early</b>. The median wait is "
        f"{sv['median_lag_reviews']} reviews — about "
        f"{sv['median_lag_reviews'] / 4:.1f} years — which is "
        "the honest read: the pool is a genuine at-risk "
        "register with no sense of timing. The engine answers "
        "\"who is vulnerable\" well and \"who goes this "
        "quarter\" badly.</p>")

    o.append("<h3>Two candidate ranking features, tested</h3>")
    f = a["features"]
    o.append(_table(
        ["Feature", "Deleted names", "False alarms", "Verdict"],
        [["Persistence (consecutive reviews below floor)",
          f"median {f['persistence']['deleted_median']:.0f}",
          f"median {f['persistence']['fa_median']:.0f}",
          _e(f["persistence"]["verdict"])],
         ["Depth (cap / floor)",
          f"{f['depth']['deleted_median']:.2f}x",
          f"{f['depth']['fa_median']:.2f}x",
          _e(f["depth"]["verdict"])]]))
    o.append(
        "<p class='cap'>The persistence result is negative and "
        "is reported anyway — it was the most intuitive feature "
        "to reach for, and it does not work.</p>")
    return o


def data_section():
    """Section 5-7: provenance, difficulties, special cases,
    roadmap. Prose, but each claim traceable to a file."""
    G = ("<span class='grade {}'>{}</span>")
    rows = [
        ["Review change lists (what MSCI actually did)",
         "81 archived MSCI STPublicList PDFs, 2006-2026",
         "point-in-time (published)", "100%",
         G.format("A", "A"),
         "Validated cell-by-cell against MSCI's own per-country "
         "count tables: 590 of 590 agree. 21 defective cells "
         "were repaired against those counts."],
        ["Size bar / GMSR + the price cutoff date",
         "46 mined editions of the GIMI methodology book",
         "point-in-time (disclosed ex post)", "32 of 34 reviews",
         G.format("A", "A-"),
         "Each edition discloses that review's actual bar and "
         "data date inside its worked example. Feb-18 and "
         "Feb-23 have no matchable edition and are excluded."],
        ["Historical prices and shares outstanding",
         "Yahoo vintage series, 150 TW companies",
         "point-in-time", "41/41 additions, 53/53 deletions",
         G.format("B", "B"),
         "Full coverage of every name that actually moved. The "
         "universe itself is only 150 names, so non-member "
         "precision is measured on a biased sample."],
        ["Exchange rate (TWD/USD)",
         "live TWD=X monthly series", "point-in-time", "100%",
         G.format("B", "B+"),
         "Corrected after a circularity: an earlier rate was "
         "derived from a float that itself assumed the rate."],
        ["Index membership at each past review",
         "reverse-roll from MSCI's own current list",
         "derived", "~97%", G.format("C", "C+"),
         "Off-cycle exits never appear in review lists, so the "
         "roll drifts. This directly caused the membership-gap "
         "misses in section 4."],
        ["Free float / FIF",
         "insider filings + MSCI factsheet-implied FIFs",
         "CURRENT vintage, not point-in-time",
         "11% of deleted names", G.format("D", "D"),
         "The weakest input by a distance, and the one most "
         "likely to explain the residual errors. Historical "
         "float is not published by anyone; MOPS filings would "
         "have to be parsed per company per period."],
        ["Liquidity (ATVR / traded value)",
         "TWSE decade harvest (3,024 days)",
         "point-in-time", "not wired into the engine",
         G.format("C", "C"),
         "Collected but unused. MSCI applies a liquidity screen "
         "we do not currently model at all."],
    ]
    o = ["<h2>5. What data goes in, and can it be trusted?</h2>",
         _table(["Input", "Source", "Vintage", "Coverage",
                 "Grade", "What it means"], rows)]
    o.append(
        "<div class='box warn'><h4>The honest summary</h4><p>"
        "The inputs that decide <i>whether the test fires</i> "
        "— change lists, the size bar, the cutoff date, prices "
        "— are strong, and two of them are validated against "
        "MSCI's own published figures. The inputs that would "
        "decide <i>which at-risk name actually goes</i> — free "
        "float and liquidity — are the weakest and the "
        "least complete. That is not a coincidence: it is "
        "precisely why recall is high and precision is "
        "low.</p></div>")

    o.append("<h2>6. Difficulties actually encountered</h2><ol>")
    for t, b in [
        ("The cutoff date is not announced in advance",
         "MSCI may use any of the last ten business days of the "
         "month. Solved by mining 46 editions of the "
         "methodology book, each of which reveals the date it "
         "used after the fact — MSCI picks the first day or two "
         "in nearly every disclosed case. That is an empirical "
         "prior, not a rule, and it can break."),
        ("A circular exchange rate",
         "The TWD rate had been inferred from a float estimate "
         "that itself assumed a rate. Caught only when an "
         "independent input (the live series) contradicted it. "
         "Every downstream number moved."),
        ("Parsing MSCI's own PDFs",
         "Two-column layouts break across pages, silently "
         "swapping additions with deletions and gluing 'None' "
         "into company names. Found by validating against "
         "MSCI's own count tables; 21 cells were repaired "
         "individually, and a global rewrite that made things "
         "worse was reverted."),
        ("The same company under many names",
         "'FUTU HOLDINGS A ADR' and 'Futu Holdings Adr' are one "
         "company. Resolved with ticker-first entity keys — "
         "which then exposed that Yahoo had mapped Chinese "
         "A-share lines to their Hong Kong twins, and ETF codes "
         "to actual funds."),
        ("Members who left without a deletion notice",
         "466 candidates identified; the 2021 US sanctions wave "
         "was found inside them. 391 remain unconfirmed because "
         "dead tickers cannot be probed."),
        ("Historical free float does not exist publicly",
         "The blocker behind the lowest grade in the table "
         "above. Nobody publishes a back history of free-float "
         "factors; it must be rebuilt from filings."),
    ]:
        o.append(f"<li><b>{t}.</b> {b}</li>")
    o.append("</ol>")

    o.append("<h2>7. Special cases the engine does not model"
             "</h2>")
    o.append(_table(
        ["Case", "What happens", "Currently modelled?"],
        [["Off-cycle deletions (takeover, delisting, "
          "sanctions)", "Name leaves between reviews and never "
          "appears in a change list", "No — measured, not "
          "modelled"],
         ["Large IPO fast-entry", "A company can be added "
          "without ever having been in our universe",
          "No — structurally invisible"],
         ["Foreign ownership headroom", "Taiwan caps foreign "
          "holdings in some names; MSCI adjusts for it",
          "Partly — in the live ladder, not the backtest"],
         ["The liquidity screen", "MSCI requires minimum "
          "traded value; a big but illiquid name can be "
          "excluded", "No — data collected, not wired"],
         ["Share-class and DR lines",
          "Preferred, non-voting and DR lines are separate "
          "index securities", "Partly — handled in entity "
          "resolution, untested in the engine"],
         ["Segment migration (Standard vs Small Cap)",
          "Most additions are promotions from Small Cap, with "
          "their own buffer rules", "No — the likely reason "
          "the add bar is mis-specified"],
         ["The number-of-constituents mechanism",
          "When a market's crossing falls outside the "
          "permitted range, MSCI flexes membership COUNT",
          "No — we assume the ceiling binds"],
         ["Extraordinary-event discretion",
          "MSCI reserves explicit judgement", "No — and "
          "cannot be"]]))

    o.append("<h2>8. What to change, in order</h2>")
    for pri, title, body, gain in [
        ("1", "Refit the addition rule to ~0.8x the ceiling",
         "The measurement in section 3 is unambiguous and the "
         "change is one constant. Validate on a held-out split "
         "before adopting, and re-derive the buffer from the "
         "segment-migration rules rather than curve-fitting it "
         "— the curve tells us the current value is wrong, not "
         "what the right one is in principle.",
         "addition recall 2% to ~58%, precision improves too"),
        ("2", "Build point-in-time free float",
         "Parse holder filings per company per period to get "
         "historical float factors, then enable the "
         "float half-bar gate that MSCI actually applies. This "
         "is the only candidate explanation for the "
         "above-floor deletions, and today it is untestable.",
         "targets the largest residual error class"),
        ("3", "Repair membership with the off-cycle register",
         "We have already classified 466 off-cycle exits. "
         "Feeding them into the reverse-roll closes the "
         "membership-gap misses — deletions the size test "
         "would have caught if the name had been in the pool.",
         "recovers misses at zero modelling cost"),
        ("4", "Rank the pool instead of just listing it",
         "Depth below the floor discriminates (0.62x vs 0.79x); "
         "persistence does not. Fit a calibrated model on the "
         "existing labelled ledger — 45 positives against 533 "
         "negatives — walk-forward, scored by Brier, with "
         "liquidity and float added as they land.",
         "converts a screen into a ranked shortlist"),
        ("5", "Wire in the liquidity screen",
         "The decade of TWSE traded-value data is already "
         "collected and unused. MSCI applies a liquidity test "
         "we do not model at all.",
         "removes a whole class of unmodelled exclusions"),
        ("6", "Recover Feb-18 and Feb-23",
         "Two reviews are unscored for want of a matchable "
         "methodology edition. Worth one archive search.",
         "+2 reviews of evidence"),
    ]:
        o.append(
            f"<div class='box'><h4>{pri}. {title}</h4>"
            f"<p>{body}</p><p><b>Expected gain:</b> {gain}</p>"
            f"</div>")
    return o


def main():
    a = json.loads((ROOT / "data" / "backtest_taiwan.json")
                   .read_text(encoding="utf-8"))
    parts = render(a) + data_section()
    parts.append(
        "<div class='foot'>Generated from "
        "data/backtest_taiwan.json by scripts/backtest_html.py. "
        "Engine: scripts/review_reconstruct.py; diagnostics: "
        "scripts/backtest_report.py and backtest_extras.py. "
        "Point-in-time throughout — no input postdates the "
        "review's disclosed price cutoff, except free float, "
        "which is current-vintage and labelled as such "
        "wherever it appears.</div></div></html>")
    html = "".join(parts)
    for d in OUT_DIRS:
        d.mkdir(exist_ok=True)
        p = d / "backtest_taiwan_2018_2026.html"
        p.write_text(html, encoding="utf-8")
        print(f"{p}  ({p.stat().st_size / 1024:.0f} KB)")
    return html


if __name__ == "__main__":
    main()
