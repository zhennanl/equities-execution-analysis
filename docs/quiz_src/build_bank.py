"""Generic bank builder: python3 build_bank.py <bank_module> <TITLE> <out_prefix> <outdir>
Regenerates <out_prefix>.md and <out_prefix>.html from the bank module."""
import json, sys, importlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

mod, title, prefix, outdir = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4])
_m = importlib.import_module(mod)
QUESTIONS = _m.QUESTIONS
INTRO = getattr(_m, "INTRO", "")            # optional markdown block after the header
TIER_LABELS = getattr(_m, "TIER_LABELS", None)
cats = list(dict.fromkeys(q["cat"] for q in QUESTIONS))

md = [f"# {title} (July 2026)", "",
      f"*{len(QUESTIONS)} questions with standard answers and practical-application",
      f"notes. Source of truth: `docs/quiz_src/{mod}.py` — edit there and re-run",
      f"`build_bank.py` to regenerate this file and `{prefix}.html` together.*", ""]
TIER = TIER_LABELS or {1: "Tier 1 · Fundamental", 2: "Tier 2 · Role-critical", 3: "Tier 3 · Good-to-know"}
md.append("**Categories:** " + " · ".join(f"{c} ({sum(1 for q in QUESTIONS if q['cat']==c)})" for c in cats))
md.append("")
if INTRO:
    md += [INTRO, ""]
md.append("**Tiers:** " + " · ".join(f"{TIER[t]} ({sum(1 for q in QUESTIONS if q.get('tier',2)==t)})" for t in (1,2,3))
          + " — study Tier 1 to fluency first, Tier 2 is where the interview lives, Tier 3 differentiates.")
md.append("")
n = 0
for c in cats:
    md += [f"## {c}", ""]
    for q in sorted([x for x in QUESTIONS if x["cat"] == c], key=lambda x: x.get("tier", 2)):
        n += 1
        md += [f"**Q{n}. {q['q']}**  \n*[{TIER[q.get('tier',2)]}]*", "",
               f"*Standard answer:* {q['a']}", "",
               f"*Practical application:* {q['p']}", ""]
(outdir / f"{prefix}.md").write_text("\n".join(md), encoding="utf-8")

TPL = Path(__file__).parent / "quiz_template.html"
html_doc = TPL.read_text(encoding="utf-8").replace("__DATA__", json.dumps(QUESTIONS)).replace("__TITLE__", title)
if TIER_LABELS:
    html_doc = html_doc.replace("{1:'T1 · Fundamental', 2:'T2 · Role-critical', 3:'T3 · Good-to-know'}",
                                json.dumps({str(k): v for k, v in TIER_LABELS.items()}).replace('"1"','1').replace('"2"','2').replace('"3"','3'))
(outdir / f"{prefix}.html").write_text(html_doc, encoding="utf-8")
print(f"{prefix}: {n} questions -> md + html")
