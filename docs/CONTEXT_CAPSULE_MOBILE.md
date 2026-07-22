# Context Capsule — paste this as the first message in a new mobile chat

**Who I am:** Bill Luo — UNC CS+Statistics, HKU MFin, CFA L3 passed. Former
Invesco trading intern (built a Taiwan limit-up/down study around index
rebalancing: locked-vs-retreat taxonomy, +2% T+1 dip-buy finding, intraday
lock-prediction thresholds). Interviewing for **GSET Quantitative Execution
Consultant / Execution Solutions** at Goldman Sachs.

**Interview state:** Round 1 done. Feedback: **round 2 is heavily
statistics-focused.** Likely interviewer: senior APAC Execution Solutions
(Zhejiang econ → GS Hong Kong 2012–14 → Tokyo 2014–17 → now). Her JD:
improve algo-performance rankings for clients, deep-dive TCA + algo
customization + APAC microstructure color, contribute to algo product
evolution.

**My flagship asset:** a 3-page execution-analytics platform I built
(June 2026–now): execution algo simulator (8 algos, order ticket/compliance,
live session with volume re-forecast), index-rebalancing analysis (market-
model event study with Brown-Warner inference bands, crowding score,
expected-move calculator, S1–S4 strategy frontier, trader pack), and an
Asia program-trading desk (session board, market regs, program blotter,
wave plan, recon). Statistics stack I can demo live: OLS with HC1/Newey-West
+ diagnostics, A/B-with-controls, condition-adjusted algo ranking (the
"wheel-defense view"), Friedman+Nemenyi algo wheel, Perold IS attribution
reconciling ±0.1bp, markout curves, event-study inference. All pinned by a
**181-test regression suite**. Design stance: no LLM in the cost path;
deterministic math, agentic orchestration, critic-flags-never-overrides.

**Key rehearsed items:** the power worked example (~1,760 paired orders to
detect 2bps at σ_d=30); 3-layer multiplicity (Nemenyi within / BH across /
no peeking); clustered-by-day SEs as the usually-binding correction; the
Invesco self-critique (raw means, event-clustered, no market adjustment —
and the fixes I built since); the censoring point (Asia price limits censor
TCA distributions); "their execution, our advice, in that order";
"credibility is the product".

**Prep materials on my PC** (Downloads\execution_analytics\docs\): 5
question banks (scenario quiz 31, technical 96 tiered, behavioral 17,
interviewer-specific 20, AI-at-GS 14), statistics-first roadmap v2
(docx/pdf), questions-for-her sheet, stats-review handoff
(HANDOFF_STATS_REVIEW.md — full drill plan), demo video script.

**What I want from this chat:** [pick one] — drill statistics per the
handoff plan / rehearse behavioral answers / mock-interview me / review a
specific concept.
