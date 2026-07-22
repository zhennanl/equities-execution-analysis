"""Generate BOTH quiz artifacts from questions.py (single source of truth).
Re-run after editing questions: python3 build_quiz.py <outdir>"""
import json, sys, html
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from questions import QUESTIONS

outdir = Path(sys.argv[1])
cats = list(dict.fromkeys(q["cat"] for q in QUESTIONS))

# ── 1. Markdown study doc ──────────────────────────────────────────────────
md = ["# GSET Quant Execution Consultant — Study Quiz (v1.0, July 2026)", "",
      "*31 scenario questions with standard answers, mapped to the JD's",
      "responsibilities. Each carries a **Practical application** note — how the",
      "knowledge is used on the desk. Source of truth for the interactive tool",
      "(`QUANT_CONSULTANT_QUIZ.html`): edit `questions.py` in the build script",
      "and regenerate both. Study method: read the question, answer ALOUD before",
      "revealing; the interactive version tracks your self-scoring.*", ""]
md.append("**Categories:** " + " · ".join(f"{c} ({sum(1 for q in QUESTIONS if q['cat']==c)})" for c in cats))
md.append("")
n = 0
for c in cats:
    md += [f"## {c}", ""]
    for q in [x for x in QUESTIONS if x["cat"] == c]:
        n += 1
        md += [f"**Q{n}. {q['q']}**", "",
               f"*Standard answer:* {q['a']}", "",
               f"*Practical application:* {q['p']}", ""]
(outdir / "QUANT_CONSULTANT_QUIZ.md").write_text("\n".join(md), encoding="utf-8")

# ── 2. Interactive HTML (self-contained, in-memory scoring only) ──────────
data = json.dumps(QUESTIONS)
html_doc = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>GSET Quant Consultant Quiz</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
 body{font-family:Arial,Helvetica,sans-serif;margin:0;background:#f3f5f9;color:#1a2233}
 header{background:#1F3864;color:#fff;padding:16px 24px}
 header h1{margin:0;font-size:20px} header p{margin:4px 0 0;font-size:13px;opacity:.85}
 .wrap{max-width:860px;margin:0 auto;padding:16px 24px 60px}
 .filters{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}
 .filters button{border:1px solid #1F3864;background:#fff;color:#1F3864;border-radius:16px;
   padding:6px 14px;font-size:13px;cursor:pointer}
 .filters button.on{background:#1F3864;color:#fff}
 .score{font-size:13px;color:#444;margin:6px 0 14px}
 .card{background:#fff;border:1px solid #d8deea;border-radius:10px;padding:16px 18px;margin:12px 0;
   box-shadow:0 1px 2px rgba(20,40,80,.06)}
 .cat{font-size:11px;letter-spacing:.4px;text-transform:uppercase;color:#2E5395;font-weight:700}
 .q{font-size:15px;font-weight:700;margin:6px 0 10px}
 .ans{display:none;border-top:1px solid #e5e9f2;padding-top:10px;font-size:14px;line-height:1.5}
 .ans .lbl{font-weight:700;color:#1F3864}
 .prac{margin-top:8px;font-size:13px;color:#555;font-style:italic}
 .btns{margin-top:10px;display:flex;gap:8px}
 .btns button{border:none;border-radius:6px;padding:7px 14px;font-size:13px;cursor:pointer}
 .reveal{background:#1F3864;color:#fff}
 .got{background:#dcfce7;color:#14532d;display:none}
 .again{background:#fee2e2;color:#7f1d1d;display:none}
 .card.done-got{border-left:5px solid #22c55e}
 .card.done-again{border-left:5px solid #ef4444}
 .foot{font-size:12px;color:#777;margin-top:24px}
</style></head><body>
<header><h1>GSET Quant Execution Consultant — Study Quiz</h1>
<p>Answer aloud before revealing. Self-score honestly — "review again" cards are the study list. Scores reset on reload (by design: retest cold).</p></header>
<div class="wrap">
 <div class="filters" id="filters"></div>
 <div class="score" id="score"></div>
 <div id="cards"></div>
 <div class="foot">Source of truth: QUANT_CONSULTANT_QUIZ.md / questions.py — regenerate both when the platform or your understanding evolves. v1.0 · July 2026.</div>
</div>
<script>
const QS = __DATA__;
const cats = [...new Set(QS.map(q=>q.cat))];
let active = new Set(cats);
const state = QS.map(()=>({revealed:false, mark:null}));
function render(){
  const f = document.getElementById('filters');
  f.innerHTML = '';
  const allBtn = document.createElement('button');
  allBtn.textContent = 'All (' + QS.length + ')';
  allBtn.className = active.size===cats.length ? 'on' : '';
  allBtn.onclick = ()=>{active = new Set(cats); render();};
  f.appendChild(allBtn);
  cats.forEach(c=>{
    const b = document.createElement('button');
    b.textContent = c + ' (' + QS.filter(q=>q.cat===c).length + ')';
    b.className = (active.size===1 && active.has(c)) ? 'on' : '';
    b.onclick = ()=>{active = new Set([c]); render();};
    f.appendChild(b);
  });
  const got = state.filter(s=>s.mark==='got').length;
  const again = state.filter(s=>s.mark==='again').length;
  document.getElementById('score').textContent =
    'Progress: ' + got + ' solid · ' + again + ' to review · ' + (QS.length-got-again) + ' unseen';
  const holder = document.getElementById('cards');
  holder.innerHTML = '';
  QS.forEach((q,i)=>{
    if(!active.has(q.cat)) return;
    const st = state[i];
    const card = document.createElement('div');
    card.className = 'card' + (st.mark ? ' done-'+st.mark : '');
    card.innerHTML = '<div class="cat">'+q.cat+'</div><div class="q">Q'+(i+1)+'. '+q.q+'</div>'+
      '<div class="ans" style="display:'+(st.revealed?'block':'none')+'">'+
      '<span class="lbl">Standard answer: </span>'+q.a+
      '<div class="prac">Practical application: '+q.p+'</div></div>'+
      '<div class="btns">'+
      '<button class="reveal">'+(st.revealed?'Hide':'Reveal answer')+'</button>'+
      '<button class="got" style="display:'+(st.revealed?'inline-block':'none')+'">Got it</button>'+
      '<button class="again" style="display:'+(st.revealed?'inline-block':'none')+'">Review again</button>'+
      '</div>';
    card.querySelector('.reveal').onclick = ()=>{st.revealed=!st.revealed; render();};
    card.querySelector('.got').onclick = ()=>{st.mark='got'; render();};
    card.querySelector('.again').onclick = ()=>{st.mark='again'; render();};
    holder.appendChild(card);
  });
}
render();
</script></body></html>"""
html_doc = html_doc.replace("__DATA__", data)
(outdir / "QUANT_CONSULTANT_QUIZ.html").write_text(html_doc, encoding="utf-8")
print(f"wrote {n} questions -> md + html in {outdir}")
