#!/usr/bin/env python3
"""The Aug-2026 Taiwan walk, as a standalone HTML page.

    py scripts\\tw_walk_html.py

WHY A NEW GENERATOR RATHER THAN A RE-RUN OF walk_display.py. That
script opens with

    CEIL, FLOOR, ADDBAR = 9.44, 6.29, 14.16

and those three numbers are the SUPERSEDED frame. They were taken
off the ceiling of the global EM range instead of Taiwan's own
Market Size-Segment Cutoff, and the addition bar used the 1.8x
light-rebalancing multiple. The correct buffers hang off the
cutoff: 2/3 x 7.22 = 4.81 and 1.5 x 7.22 = 10.83. Re-running the
old script would have produced a fresh-looking file carrying the
old error — which is exactly how a corrected number gets
un-corrected.

It also walked a different universe: 890 screened names against a
$3,979.5B denominator, reaching 85% at rank 61. The frame of
record inverts the published factsheet instead — $3,183B of index
free-float value over 85% coverage implies a $3,744.7B investable
market, and the walk over the 398 screened names reaches it at
rank 69, whose FULL cap of $7.22B is the cutoff.

NOTHING HERE IS TYPED. The crossing comes from
walkthrough_story._crossing(), which is the same function the site
renders from and the same one the tests reproduce — so this page
and the app cannot disagree. If the universe file is rebuilt, both
move together.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

OUT = ROOT / "reports" / "tw_walk_aug26.html"

CSS = """
body{font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;
     color:#2b2724;background:#fbf9f6;margin:0;padding:28px 32px}
h1{font:600 25px/1.25 Georgia,serif;margin:0 0 4px}
.sub{color:#8a7f76;font-size:13px;margin:0 0 22px}
.k{display:flex;flex-wrap:wrap;gap:0;border-top:1px solid #e8ddd1;
   border-bottom:1px solid #e8ddd1;margin:0 0 22px}
.k div{padding:11px 26px 11px 0;margin-right:26px}
.k .lab{font-size:10.5px;letter-spacing:1.1px;text-transform:uppercase;
        color:#a89c92}
.k .val{font:600 19px/1.2 Georgia,serif;font-variant-numeric:tabular-nums}
.k .note{font-size:11.5px;color:#8a7f76}
table{border-collapse:collapse;font-size:12.5px;width:100%;
      font-variant-numeric:tabular-nums}
th{text-align:right;font-size:10.5px;letter-spacing:.9px;
   text-transform:uppercase;color:#a89c92;border-bottom:1px solid #e8ddd1;
   padding:7px 9px;position:sticky;top:0;background:#fbf9f6}
/* left-aligned: code, name, FIF source, zone. The FIF-source
   column pushed zone from 9 to 10 — a positional selector that
   silently stops matching is exactly how a column ends up
   right-aligned against a wall of text. */
th:nth-child(2),th:nth-child(3),th:nth-child(7),
th:nth-child(10){text-align:left}
td{border-bottom:1px solid #f2ebe2;padding:5px 9px;text-align:right}
td:nth-child(2),td:nth-child(3),td:nth-child(7),
td:nth-child(10){text-align:left}
tr.cross td{background:#fdf0cf;font-weight:700}
tr.add td{background:#e6f2ea}
tr.del td{background:#fbe4e1}
.z{font-size:11px;color:#8a7f76}
.cap{color:#8a7f76;font-size:12px;margin:16px 0 0;max-width:70ch}
"""


# c-304, Bill: *"specify the source of FIF. Is it implied from
# MSCI's index weight? Or from Yahoo finance."* The universe file
# already records it per name — it was simply not carried onto
# the page. It matters because the four are not equally good: the
# first two are inverted from MSCI's own published numbers and are
# effectively measured, the third is a third-party estimate, and a
# name sitting within a few per cent of a threshold can cross it
# on the difference alone.
FIF_SRC = {
    "factsheet-implied": ("MSCI factsheet",
                          "float cap read off a published top-ten"),
    "msci-weights-inversion": ("MSCI weights",
                               "inverted from the index weight"),
    "tdcc-calibrated": ("TDCC",
                        "Taiwan depository holdings, scaled"),
    "yahoo": ("Yahoo", "third-party estimate"),
}


def _fif_label(src):
    return FIF_SRC.get(str(src), (str(src or "—"), ""))


def _j(name):
    p = ROOT / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _names():
    try:
        f = ROOT / "data" / "yahoo_names.json"
        return json.loads(
            f.read_bytes().decode("utf-8", errors="replace"))
    except Exception:                              # noqa: BLE001
        return {}


def build():
    from walkthrough_story import _crossing, story

    cr = _crossing()
    if not cr:
        raise SystemExit("no crossing — is tw_mieu_universe.json "
                         "built?")
    s = story("Taiwan", "Aug26")
    k = s["keys"]
    cut, floor, bar = k["cutoff"], k["floor"], k["bar"]
    mfc = k.get("min_float_cap")

    uni = (_j("tw_mieu_universe.json") or {}).get("universe") or {}
    call = _j("aug26_tw_call_v2.json") or {}
    called = {str(c["code"]): c for c in call.get("calls", [])}
    nm = _names()

    rows = sorted(({"code": c, **v} for c, v in uni.items()),
                  key=lambda r: -r["cap"])
    target = cr["target_busd"]
    cum = 0.0
    body = []
    for i, r in enumerate(rows, 1):
        cum += r["fcap"]
        cls = []
        zone = []
        if i == cr["crossing_rank"]:
            cls.append("cross")
            zone.append("CROSSING — sets the cutoff")
        if r["cap"] >= bar:
            zone.append("above the addition bar")
        elif r["cap"] < floor:
            zone.append("below the deletion floor")
        else:
            zone.append("in the buffer")
        c = called.get(r["code"])
        if c:
            cls.append("add" if c["action"] == "ADD" else "del")
            zone.append(f"CALLED {c['action']} "
                        f"{int(round(c['prob'] * 100))}%")
        name = (nm.get(f"{r['code']}.TW")
                or nm.get(f"{r['code']}.TWO") or "")
        body.append(
            f"<tr class='{' '.join(cls)}'>"
            f"<td>{i}</td><td>{html.escape(r['code'])}</td>"
            f"<td>{html.escape(str(name)[:34])}</td>"
            f"<td>{r['cap']:,.2f}</td><td>{r['fcap']:,.2f}</td>"
            f"<td>{r['ff']:.3f}</td>"
            f"<td class='z' title='{html.escape(_fif_label(r.get('src'))[1])}'>"
            f"{html.escape(_fif_label(r.get('src'))[0])}</td>"
            f"<td>{cum / target * cr['coverage'] * 100:,.2f}</td>"
            f"<td>{r['cap'] / cut:,.2f}</td>"
            f"<td class='z'>{html.escape(' · '.join(zone))}</td>"
            f"</tr>")

    measured = sum(1 for r in rows if str(r.get("src")) in
                   ("factsheet-implied", "msci-weights-inversion"))

    def cell(lab, val, note):
        return (f"<div><div class='lab'>{lab}</div>"
                f"<div class='val'>{val}</div>"
                f"<div class='note'>{note}</div></div>")

    keys = "".join([
        cell("Market Size-Segment Cutoff", f"${cut}B",
             f"rank {cr['crossing_rank']} of {cr['screened']}"),
        cell("Deletion floor", f"${floor}B", "2/3 × cutoff"),
        cell("Addition bar", f"${bar}B", "1.5 × cutoff"),
        cell("Min free-float cap", f"${mfc}B" if mfc else "—",
             "0.5 × cutoff"),
        cell("Implied investable market",
             f"${cr['implied_universe_busd']:,.1f}B",
             f"${cr['target_busd']:,.0f}B index ÷ "
             f"{cr['coverage']:.0%}"),
        cell("Screened universe", f"{cr['screened']}",
             f"priced {cr['priced']}"),
        cell("FIF measured vs estimated",
             f"{measured}&#8202;/&#8202;{len(rows)}",
             "MSCI factsheet or weights; rest estimated"),
    ])

    return f"""<!doctype html><html><head><meta charset='utf-8'>
<title>The Walk — MSCI Taiwan, August 2026</title>
<style>{CSS}</style></head><body>
<h1>The Walk — MSCI Taiwan, August 2026</h1>
<p class='sub'>Every screened company in full-market-cap order,
cumulating free-float value until 85&#37; of the investable market
is covered. The last company added to reach 85&#37; &mdash; its
full market cap &mdash; becomes the cutoff. Generated {dt.date.today().isoformat()} from
data/tw_mieu_universe.json — no figure on this page is typed.</p>
<div class='k'>{keys}</div>
<table><thead><tr>
<th>rank</th><th>code</th><th>name</th><th>full &#36;B</th>
<th>float &#36;B</th><th>FIF</th><th>FIF source</th>
<th>cum cov &#37;</th>
<th>× cutoff</th><th>zone</th>
</tr></thead><tbody>{''.join(body)}</tbody></table>
<p class='cap'><b>Buffers hang off the cutoff, not off the global
range.</b> An earlier version of this page used 6.29 and 14.16,
taken from the ceiling of the global EM size range with the 1.8×
light-rebalancing multiple. Both were wrong: GIMI &#167;3.1.5.1
defines the buffers as 2/3 of and 1.5 times the Market
Size-Segment Cutoff, which is this market's own number.</p>
<p class='cap'><b>The FIF column is not one number from one
place.</b> <i>MSCI factsheet</i> is a float cap read straight off a
published top-ten and <i>MSCI weights</i> is inverted from the
index weight — both are effectively MSCI's own figure. <i>TDCC</i>
is Taiwan depository holdings scaled to that overlap. <i>Yahoo</i>
is a third-party estimate and carries the most error. Hover any
cell for the definition.</p>
<p class='cap'><b>Which source a name has changes how much to
trust its position.</b> Most of the universe is on the estimated
tier, so a company sitting within a few per cent of the cutoff,
the floor or the addition bar can cross it on float error alone —
and the four called additions all sit far enough above the bar
that the tier does not decide them.</p>
</body></html>"""


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"-> {OUT.relative_to(ROOT)}  "
          f"({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
