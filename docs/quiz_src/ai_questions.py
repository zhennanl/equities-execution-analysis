# AI-at-GS prep bank. Tiers: 1 = very likely once you raise AI, 2 = likely, 3 = stretch.
TIER_LABELS = {1: "T1 · Very likely once you raise AI", 2: "T2 · Likely", 3: "T3 · Stretch / differentiator"}

INTRO = """## The Goldman AI landscape (researched July 2026 — cite naturally, don't recite)

**1. GS AI Platform + GS AI Assistant (firmwide).** Goldman built an internal,
model-agnostic platform — the GS AI Assistant runs on it and can route to
OpenAI (GPT-4o family, o3-mini), Google Gemini models, Anthropic Claude, and
open-source models. Piloted to ~10,000 employees from January 2025, launched
firmwide June 2025 (CIO Marco Argenti: the first generative AI tool at that
scale in the firm). Uses: summarization, data analysis, drafting, translation.
The design tell: **model-agnostic + inside the firm's walls + auditable** —
governance first, capability second.

**2. Devin and the "hybrid workforce" (July 2025).** GS became the first major
bank to pilot Cognition's autonomous coding agent across its ~12,000-person
engineering org — hundreds of instances, tasked with legacy code, refactoring,
debugging, reported 3–4x productivity vs prior AI tools, under continuous
human supervision. Argenti's framing: engineers will "describe problems
coherently, turn them into prompts, and supervise the work of those agents."
**The skill being hired for is shifting toward specification and supervision**
— which is precisely what a tested, pinned analytics codebase enables.

**3. GSET and execution AI.** Public materials describe the algo suite and
SOR as data-driven: venue selection from historical execution statistics,
strategies blending historical analysis with real-time market information,
dynamic liquidity-seeking (Sonar) across displayed and non-displayed venues.
Atlas — the equities platform rebuild — is explicitly about modularity and
faster iteration, i.e., the substrate that lets ML-driven features ship.
Realistic read for the interview: **execution AI at a bank is mostly
supervised ML on well-defined subproblems** (venue ranking, volume/fill
prediction, anomaly detection) — not end-to-end black-box trading.

**4. The governance posture.** Everything public points one way: internal
platforms, model choice flexibility, human supervision, audit trails. When
you talk about your own AI work, mirror that posture — it's also the honest
posture.

## Positioning YOUR AI strength (the 60-second version)

"My platform is agentic in the architectural sense: specialist agents with
typed interfaces, an orchestrator that degrades gracefully, and a critic that
reviews recommendations and raises flags without silently overriding. I
deliberately kept LLMs OUT of the cost path — every P&L-relevant number is
deterministic and pinned by 181 regression tests — because in a money-adjacent
workflow the reasoning layer can be probabilistic but the numbers cannot.
Where I'd add LLMs is exactly where Goldman has: narration over computed
facts, retrieval over documented methodology, and supervised code generation
against a test suite that catches drift. That's the same hybrid-workforce
stance the firm's Devin pilot takes: agents do the work, humans own the
judgment, tests own the truth."
"""

QUESTIONS = [
dict(tier=1, cat="Your project's AI", q="You call your platform 'agentic AI' — what's actually agentic about it, and where is the AI?",
a="Honest decomposition, because overclaiming dies fast in this room: the agents are specialist components with typed inputs/outputs on a shared context — what makes it agentic rather than well-factored functions is (1) dynamic orchestration: the pipeline skips or degrades per-agent based on data availability at runtime, recorded and inspectable; (2) independent verification: a critic agent reviews the primary recommendation and raises findings without overriding; (3) composability: any agent upgrades without touching the others, each unit-tested. There's deliberately NO LLM in the cost path — impact, TCA, and attribution are deterministic and pinned by tests. The LLM layer I'd add sits on top: narrating computed results, answering free-form questions by citing them, reconciling critic findings into prose. I'd rather defend that boundary than pretend the math is neural.",
p="The certain question. The honest architecture answer plus the 'where LLMs belong' extension shows judgment, not just enthusiasm."),
dict(tier=1, cat="AI in Execution Solutions", q="Where would you actually apply AI in THIS team's work?",
a="Ranked by value-to-risk: (1) TCA review drafting — LLM turns the computed attribution into client-ready narrative from structured facts only; consultants edit, clients get consistency; the numbers never originate in the model. (2) Client Q&A over methodology — retrieval-grounded answers citing the team's documented definitions ('how is your PWP computed?') — kills repetitive load. (3) Anomaly triage on TCA dashboards — supervised models flag which of ten thousand daily order-outcomes deserve human eyes; a ranking problem, not a judgment problem. (4) Prediction subproblems where ML already earns its keep: intraday volume forecasting, fill-probability models feeding SOR logic. (5) Devin-style code assistance for the team's own tooling, guarded by regression tests. What I would NOT automate: final client-facing numbers without human sign-off, and anything compliance attests to.",
p="Her JD mapped to AI use-cases with the guardrail stated per item — the answer of someone who'd ship responsibly."),
dict(tier=1, cat="Risk & governance", q="What are the risks of using LLMs in client-facing analytics, and how do you control them?",
a="The core risk is confident fabrication — of numbers, methodology claims, or citations — in a context where one wrong number to a client costs more than a thousand drafts save. Controls, in order: (1) architecture — LLMs never compute; they narrate values passed in as structured data, so a hallucinated number can't exist, only a mis-narrated one; (2) grounding — methodology answers retrieve from documented sources and cite or refuse; (3) evaluation — a golden set of input→expected-output pairs run like regression tests on every prompt/model change; (4) human ownership — a named person signs anything a client sees; (5) auditability — log prompt, context, model version per output, which is also the compliance requirement. Then the quieter risks: data leakage into external models (why GS built an internal platform) and consistency drift across model updates (why model-agnostic routing with eval gates matters).",
p="Table stakes for raising AI at a bank. The 'narrate, never compute' architecture line is the one to land."),
dict(tier=1, cat="ML vs statistics", q="When do you use machine learning versus classical statistics in execution analytics?",
a="Split by the question's job. ATTRIBUTION and advice — 'why was this expensive, what should the client change' — stays classical: small pre-specified regressions with robust errors, because clients and compliance need coefficients you can defend under 'how is that computed', and because execution effects are small relative to noise, where flexible models mostly fit noise. PREDICTION at scale — volume curves, fill probabilities, venue ranking — earns ML: rich features, huge n, and nobody needs to testify about a gradient-boosted tree's third split; you validate it walk-forward and monitor drift instead. The bridge discipline: even prediction models get a classical baseline first (a regression or empirical curve), because 'beats the naive baseline out-of-sample by X, Diebold-Mariano significant' is the only ML claim worth making. Interpretability isn't decoration in this seat — it's the product.",
p="Probably her sharpest technical AI question — this split (testify vs predict) is the professional answer."),
dict(tier=1, cat="GS AI landscape", q="What do you know about how Goldman uses AI today?",
a="Three visible layers. Firmwide: the GS AI Assistant, launched across the firm in mid-2025 on the internal GS AI Platform — deliberately model-agnostic (GPT, Gemini, Claude, open-source behind one governed interface) for summarization, analysis, drafting. Engineering: the Devin pilot — first major bank to deploy an autonomous coding agent at scale, hundreds of instances on legacy and refactoring work under supervision, with Argenti's 'hybrid workforce' framing: humans specify and supervise, agents execute. Trading: GSET's suite is data-driven in the ML sense — venue selection from historical execution stats, strategies conditioning on real-time state, Sonar's liquidity seeking — with Atlas as the modular platform that lets those features iterate. The through-line I take from it: internal, governed, supervised, model-flexible — capability inside guardrails. My own project follows the same posture, which is not a coincidence; I studied how the banks were deploying before designing it.",
p="The homework answer — 90 seconds, three layers, ends by connecting to his project's design philosophy."),
dict(tier=2, cat="Validation", q="How would you validate an ML model that predicts intraday volume before it feeds a scheduler?",
a="Like a forecasting product, not a Kaggle entry. Baselines first: rolling historical curve and yesterday's-curve — the model must beat both out-of-sample or it ships nothing. Temporal validation only — walk-forward by day, never random splits (leakage). Metrics matched to the consumer: bucket-level MAE weighted by how the scheduler uses each bucket, plus Diebold-Mariano against the baseline so 'better' is a tested claim. Regime slicing: performance on high-vol days, rebalance days, half-days — a model that wins on average and fails on event days is worse than the baseline for an execution desk. Then production honesty: monitoring with drift alerts, a fallback to the empirical curve on anomaly, and a re-training cadence with eval gates. The scheduler consuming it should also degrade gracefully — my volume re-forecast does exactly this: model where confident, curve where not.",
p="The validation-discipline question; the event-day slicing point is what separates desk-ready from notebook-ready."),
dict(tier=2, cat="AI in Execution Solutions", q="Would you let an LLM write the commentary in a client's TCA review?",
a="Yes — with an architecture, not a vibe. The pipeline: analytics compute the facts into a structured payload (numbers, comparisons, flags); the LLM drafts narrative FROM that payload under a template contract (every claim must reference a payload field — no free facts); a consultant reviews and owns it; and an eval harness checks drafts against a golden set for fabrication and tone drift on every model change. What you get: consistency across hundreds of client packs, consultants spending review time on judgment rather than prose, and faster turnaround. What you never do: let it touch the numbers, or send unreviewed output externally. The precedent inside the firm is exactly this shape — the GS Assistant drafts and summarizes under human ownership; extending that to TCA packs is an incremental step, not a leap.",
p="A concrete yes-with-architecture beats both naive yes and reflexive no — and it's implementable, which she'll notice."),
dict(tier=2, cat="ML depth", q="Reinforcement learning for trade execution — real or hype?",
a="Real lineage, oversold packaging. Optimal execution IS a control problem, so RL is a natural formalism, and there's serious research (and some production child-order logic) using it. The honest obstacles: (1) the environment isn't a simulator you can trust — fills you didn't do are counterfactual, and a backtest tape doesn't push back, so sim-to-real gap is the whole problem; (2) sample efficiency — regime-diverse market data is scarce at the episode level; (3) reward mis-specification quietly optimizes the wrong thing (fill rate vs true cost). What production systems mostly run instead: supervised models for the predictable pieces (volume, fill probability, venue quality) feeding rule-based or bandit-style decision layers — bandits being the defensible middle ground for venue selection since exploration is cheap per child order. My one-liner: RL is the right THEORY of execution; supervised-plus-bandits is the right ENGINEERING, today.",
p="Differentiator answer — respects the research, names the sim-to-real problem, lands on what desks actually run."),
dict(tier=2, cat="Your project's AI", q="Your critic agent raises flags but never overrides. Why not let it fix things automatically?",
a="Because in a money-adjacent workflow, a silent automated override is worse than the error it prevents. Three reasons. Accountability: someone must own the recommendation; an override chain blurs it exactly when a client asks 'why did the system do that'. Information: a flag PLUS the original recommendation carries more decision content than a silently swapped answer — the human sees the disagreement, which is often the interesting signal (my critic flagging that two impact models diverge IS the finding). Failure containment: critics have false positives too; auto-override means critic bugs become production behavior with no human circuit-breaker. This mirrors how the firm deploys — Devin works under supervision, the Assistant drafts for humans who own the output. Autonomy is a dial, and for anything touching client money the dial stops at 'recommend and flag'.",
p="His signature design decision defended in her risk language — accountability, information, containment."),
dict(tier=2, cat="Hybrid workforce", q="Coding agents like Devin — what actually changes for a quant/analytics team?",
a="The bottleneck moves from writing code to specifying and verifying it. Argenti's framing is right: the valuable skills become describing problems precisely (a spec is a prompt with acceptance criteria) and supervising output — which concretely means TESTS. An agent refactoring a TCA library is safe exactly in proportion to the regression suite around it: my platform's 181 pinned anchors are what would let an agent touch the cost math without silent drift — the tests are the supervision. Second-order changes: legacy migration and boilerplate get cheap (the Devin task profile), so small teams ship platform-grade tooling; code review shifts toward design and correctness-of-spec; and the risk shifts from typos to confidently-wrong architecture, which only domain review catches. The people who benefit most are those who already write testable, specified analytics — that's the muscle I've been building deliberately.",
p="Connects the firm's own pilot to his test-driven practice — 'the tests are the supervision' is the keeper line."),
dict(tier=3, cat="ML depth", q="RAG vs fine-tuning vs prompting — how do you choose?",
a="Prompting first, always — it's free, fast, and reversible; most tasks die or succeed right there. RAG when the answer must be GROUNDED in specific, changing, citable content — methodology docs, market-structure notes, client agreements — because retrieval gives you provenance ('per section 3 of our TCA methodology…') and updates without retraining; this is the right pattern for client-facing Q&A at a bank. Fine-tuning when the need is form at scale rather than facts — house style, structured output formats, domain shorthand — accepting the costs: training data curation, eval burden per model refresh, and governance review. The anti-pattern to name: fine-tuning to inject knowledge — facts belong in retrieval where they're auditable and updatable, not baked into weights where they're neither.",
p="Crisp decision rule + the anti-pattern; thirty seconds, done."),
dict(tier=3, cat="Risk & governance", q="How would you evaluate an LLM feature before shipping it to the team or clients?",
a="Like any model, plus fabrication-specific checks. Define the task metric first (for TCA drafting: factual fidelity to the payload, completeness of required sections, tone). Build a golden set — real historical inputs with reviewed-correct outputs — and score candidates against it automatically; add adversarial cases (missing data, contradictory inputs, edge markets) because failure modes live there. Measure fabrication explicitly: any claim not traceable to input is a defect, counted, with a release threshold near zero for client-facing use. Then regression discipline: the eval runs on every prompt change and every model-version change — model updates are silent regressions waiting to happen, which is exactly why a model-agnostic platform needs eval gates per route. Ship behind human review, log everything, revisit the eval set as usage reveals new failure classes. It's the same culture as my 181-test suite, applied to a stochastic component.",
p="Evals-as-regression-tests — maps his existing discipline onto the new component class."),
dict(tier=3, cat="Limits", q="What can't current AI do in execution analytics?",
a="Four honest limits. Causal inference from observational tape — no model reads off 'what would this order have cost via the other route' from data that doesn't contain the counterfactual; that needs experiments, which is why A/B design stays central. Small-sample regime judgment — a genuinely new market structure (a rule change, a new close mechanism) has no training data; the first months belong to human reasoning and careful measurement. Accountability — a model can't sit across from a client or a regulator and own a number; the sign-off chain is human by construction, not by temporary limitation. And guaranteed correctness — stochastic components bound error rates, they don't eliminate them, which is why the deterministic/probabilistic boundary in a system's design is the design decision. None of these are reasons not to deploy AI; they're the map of where humans stay load-bearing — the hybrid-workforce point, taken seriously.",
p="Ending an AI-strength pitch with its limits is the credibility move — especially with a senior practitioner."),
dict(tier=3, cat="Curveball", q="Doesn't AI eventually replace exactly the analyst job you're applying for?",
a="Parts of it, and I'm applying anyway — because the parts it replaces are the parts I'd automate myself in year one: report drafting, repetitive Q&A, dashboard triage. What remains is the actual seat: judgment under ambiguity (is this result real or regime noise), client trust (a person who owns the number and can defend it live), experiment design (deciding what to measure), and translation between quant truth and client action. The firm's own framing agrees — hybrid workforce, humans supervising agents — and the practical version of that is: analysts who wield AI displace analysts who don't, long before AI displaces the seat. I'd rather be the one building the automation and banking the freed hours for the client work that compounds. My whole platform is that thesis, executed.",
p="Confident, specific, aligned with the firm's stated view — and it closes on his differentiator."),
]
