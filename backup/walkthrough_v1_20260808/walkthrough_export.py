"""Standalone HTML export of the walkthrough (c-115).

Same story object the Streamlit page renders, written to ONE
self-contained file: inline CSS, inline SVG chart, no scripts,
no CDN, no app. Opens anywhere, prints cleanly, emails fine.

The chart is generated as SVG here rather than embedded plotly
so the file stays small and works offline forever.

Usage:
  py scripts\\walkthrough_export.py Taiwan May26
  py scripts\\walkthrough_export.py all        (every example)
Output: reports/walkthrough_<market>_<review>.html
"""
import html as _h
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

CSS = """
:root{--navy:#1f4e79;--ink:#1a1a1a;--mut:#5b6770;
--line:#e3e7ea;--red:#c0392b;--cream:#faf9f6}
*{box-sizing:border-box}
body{margin:0;background:var(--cream);color:var(--ink);
font:16px/1.65 Calibri,Candara,Segoe UI,system-ui,sans-serif}
.wrap{max-width:820px;margin:0 auto;padding:48px 24px 80px}
h1{font-size:34px;line-height:1.2;color:var(--navy);margin:0 0 8px}
h2{font-size:23px;color:var(--navy);margin:0 0 14px}
.sub{color:var(--mut);margin:0 0 6px}
.mode{border-left:4px solid var(--navy);background:#fff;
padding:12px 16px;margin:22px 0;border-radius:0 4px 4px 0}
.step{background:#fff;border:1px solid var(--line);
border-radius:6px;padding:26px 28px;margin:22px 0}
.n{display:inline-block;width:30px;height:30px;line-height:30px;
text-align:center;background:var(--navy);color:#fff;
border-radius:50%;font-weight:700;margin-right:10px;font-size:15px}
.nums{display:flex;flex-wrap:wrap;gap:14px;margin:0 0 20px}
.num{flex:1 1 150px;border:1px solid var(--line);
border-radius:4px;padding:10px 12px;background:#fcfcfa}
.num .l{font-size:11.5px;text-transform:uppercase;
letter-spacing:.5px;color:var(--mut)}
.num .v{font-size:21px;font-weight:700;color:var(--navy)}
.num .nt{font-size:12px;color:var(--mut);font-style:italic}
p{margin:0 0 13px}
details{margin:16px 0 0;border-top:1px solid var(--line);
padding-top:12px}
summary{cursor:pointer;font-weight:600;color:var(--navy);
font-size:14.5px}
details p{font-size:14.5px;color:#333;margin-top:10px}
.hon{margin:14px 0 0;padding:11px 14px;background:#f4f7fa;
border-radius:4px;font-size:14.5px}
.hon b{color:var(--navy)}
.foot{color:var(--mut);font-size:13px;margin-top:34px;
border-top:1px solid var(--line);padding-top:16px}
svg{max-width:100%;height:auto;display:block;margin:8px 0 4px}
.cap{font-size:13px;color:var(--mut);font-style:italic}
"""


def _chart(s, max_rows=26):
    """Horizontal size chart with the floor line drawn in —
    the static twin of the page's interactive lever."""
    k = s["keys"]
    floor = float(k["floor"])
    # the story lives at the BOTTOM of the size ladder — the
    # names near the floor, plus any MSCI actually moved. The
    # giants are irrelevant to the decision and would squash
    # the scale.
    cand = [u for u in s["universe"] if u["cap"] <= 60]
    moved = [u for u in cand if u.get("actual")]
    small = sorted(cand, key=lambda r: r["cap"])[:max_rows]
    seen, uni = set(), []
    for u in small + moved:
        if u["code"] not in seen:
            seen.add(u["code"])
            uni.append(u)
    if not uni:
        return ""
    uni = sorted(uni, key=lambda r: r["cap"])
    mx = max(max(u["cap"] for u in uni), floor) * 1.12
    rowh, padl, w = 20, 210, 760
    h = rowh * len(uni) + 46
    plot = w - padl - 20

    def x(v):
        return padl + plot * v / mx
    parts = [f'<svg viewBox="0 0 {w} {h}" '
             f'xmlns="http://www.w3.org/2000/svg" '
             f'font-family="Calibri,sans-serif" font-size="11">']
    for i, u in enumerate(uni):
        y = 10 + i * rowh
        below = u["cap"] < floor
        col = "#c0392b" if below else "#b9c2c8"
        nm = _h.escape(str(u["name"])[:30])
        mark = {"DEL": " ← removed", "ADD": " ← added"}.get(
            u.get("actual"), "")
        parts.append(
            f'<text x="{padl - 6}" y="{y + 11}" text-anchor="end" '
            f'fill="#1a1a1a">{nm}{mark}</text>'
            f'<rect x="{padl}" y="{y + 3}" '
            f'width="{max(x(u["cap"]) - padl, 1):.1f}" '
            f'height="{rowh - 7}" fill="{col}" rx="1"/>'
            f'<text x="{x(u["cap"]) + 5}" y="{y + 11}" '
            f'fill="#5b6770">${u["cap"]}B</text>')
    fx_ = x(floor)
    parts.append(
        f'<line x1="{fx_:.1f}" y1="4" x2="{fx_:.1f}" '
        f'y2="{h - 30}" stroke="#1f4e79" stroke-width="2.5"/>'
        f'<text x="{fx_ + 5}" y="{h - 18}" fill="#1f4e79" '
        f'font-weight="700">MSCI floor ${floor}B</text></svg>')
    return "".join(parts)


def to_html(s):
    k = s["keys"]
    live = s["mode"] == "live"
    mode = ("<b>Live mode.</b> The identical machine, pointed at "
            "a review MSCI has not announced. The call at the "
            "end was written down in advance and grades on "
            "Aug 11-12, 2026." if live else
            "<b>Learning mode.</b> This review has already been "
            "announced, so at the end you can see exactly how "
            "the method scored — including where it was "
            "wrong.")
    out = [f"<!doctype html><html lang='en'><meta charset='utf-8'>"
           f"<meta name='viewport' content='width=device-width,"
           f"initial-scale=1'><title>{_h.escape(s['title'])}"
           f"</title><style>{CSS}</style><div class='wrap'>",
           f"<h1>{_h.escape(s['title'])}</h1>",
           "<p class='sub'>A walkthrough of the point-in-time "
           "method, written to be followed with no finance "
           "background. Every number on this page was read from "
           "the prediction engine's own output — nothing "
           "here was typed by hand.</p>",
           f"<div class='mode'>{mode}</div>"]
    for stp in s["steps"]:
        out.append("<div class='step'><h2><span class='n'>"
                   f"{stp['n']}</span>{_h.escape(stp['title'])}"
                   "</h2>")
        if stp["numbers"]:
            out.append("<div class='nums'>")
            for n in stp["numbers"]:
                nt = (f"<div class='nt'>{_h.escape(str(n['note']))}"
                      "</div>" if n.get("note") else "")
                out.append(
                    f"<div class='num'><div class='l'>"
                    f"{_h.escape(str(n['label']))}</div>"
                    f"<div class='v'>{_h.escape(str(n['value']))}"
                    f"</div>{nt}</div>")
            out.append("</div>")
        for p in stp["plain"]:
            out.append(f"<p>{_h.escape(p)}</p>")
        if stp["n"] == 5:
            out.append(_chart(s))
            out.append(
                "<p class='cap'>Each bar is one company's size "
                "on the photograph day. The blue line is MSCI's "
                "floor; everything red of it is a deletion "
                "candidate. In the interactive version you can "
                "drag this line and watch the names change "
                "sides.</p>")
        if stp.get("desk"):
            out.append("<details><summary>For the desk — "
                       "rules, sources, error bars</summary><p>"
                       f"{_h.escape(stp['desk'])}</p></details>")
        if stp.get("honesty"):
            out.append("<div class='hon'><b>What this step can "
                       "get wrong:</b> "
                       f"{_h.escape(stp['honesty'])}</div>")
        out.append("</div>")
    out.append(
        "<div class='foot'>Generated from the engine output for "
        f"{_h.escape(s['market'])} {_h.escape(s['review'])} "
        f"(size bar ${k['gmsr_dm']}B, floor ${k['floor']}B, "
        f"bar ${k['bar']}B, photograph "
        f"{_h.escape(str(k['price_date'])[:10])}, FX {s['fx']}). "
        "Execution Analytics — a snapshot; re-export after "
        "the engine reruns.</div></div></html>")
    return "".join(out)


def write(market, review):
    from walkthrough_story import story
    s = story(market, review)
    d = ROOT / "reports"
    d.mkdir(exist_ok=True)
    p = d / f"walkthrough_{market}_{review}.html"
    p.write_text(to_html(s), encoding="utf-8")
    print(f"{p.relative_to(ROOT)}  ({p.stat().st_size / 1024:.0f} KB, "
          f"{len(s['steps'])} steps, {len(s['universe'])} companies)")
    return p


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        for m, r in [("Taiwan", "May26"), ("Taiwan", "Aug26")]:
            write(m, r)
    else:
        write(sys.argv[1] if len(sys.argv) > 1 else "Taiwan",
              sys.argv[2] if len(sys.argv) > 2 else "May26")
