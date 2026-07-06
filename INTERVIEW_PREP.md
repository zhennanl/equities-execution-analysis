# Interview Prep — Agentic AI System for Equities Execution Analysis & Index Rebalancing

---

## 1. Motivation & Origin Story

**Use this when asked "tell me about this project" or "how did this come about?"**

I didn't start by deciding to build an execution-analysis tool. I started by researching a broader question: *how can agentic AI actually improve the investment research process*, not just make it faster to summarize a filing. That research turned up a few consistent, real findings:

1. **Decomposition + independent verification beats one big opaque call, especially for money-adjacent decisions.** The failure mode everyone worries about with LLMs isn't "it doesn't know the answer" — it's "it's persuasively wrong." Splitting a task into a generator step and a separate, independently-reasoned verifier/critic step (rather than trusting one model's single pass) is the difference between a tool you can actually rely on and a plausible-sounding toy. This is visible in how the banks are actually deploying this stuff: Goldman's GS AI Assistant is model-agnostic and audited, and Goldman's own Marquee platform is built as a multi-agent system with separate specialized data/analytics agents rather than one monolithic model doing everything.
2. **Specialization and composability let you upgrade one piece without breaking the rest.** A single model trying to do regime-detection, cost modeling, and risk-flagging all in one prompt is brittle — you can't test it, and improving one part risks silently degrading another. Treating each step as its own agent with a typed input/output means you can swap or upgrade one (say, the trend model) without touching the others, and you can unit-test each one in isolation. Morgan Stanley's advisor assistant is grounded on ~100,000 research documents specifically so the reasoning stays tethered to retrievable, checkable sources rather than free-floating generation — same instinct.
3. **The right division of labor is: deterministic math stays deterministic, agentic layer adds flexibility on top.** For anything touching real capital, the actual cost/impact numbers need to be exactly reproducible — you should be able to assert `total_cost_bps` to the cent in a test. What an agentic layer is genuinely good for is conditional routing, graceful degradation when data is missing, and turning structured quantitative output into a synthesized recommendation. I did not want to "replace the math with an LLM" — I wanted the orchestration and verification layer to be agentic while the P&L-relevant numbers stay boring, deterministic Python.

From there, the pivot to **execution analysis specifically** was deliberate, not incidental. Investment research (stock picking, thesis-building) is hard to demo credibly and hard to grade — "was the idea good" takes months to resolve. Execution cost analysis has a completely different shape that happens to line up perfectly with what I'd just learned about agentic design:

- It's a **pipeline of genuinely semi-independent analytical steps** — detect the market regime, simulate several execution strategies, compare realized costs, flag risks, recommend — which today mostly live across separate desks, spreadsheets, and vendor TCA tools. That's exactly the shape a multi-agent architecture is supposed to fit.
- It has an **unambiguous, immediately measurable ground truth**: basis points of slippage and market impact, not "was the stock pick right." That let me build honest tests (`assert total_cost_bps == X`) instead of hand-waving.
- It has a **deep, freely-available body of institutional and academic research** to calibrate against even without a paid market-data feed — Kyle (1985), Almgren-Chriss, Almgren et al.'s 2005 Citigroup-order study, Easley/López de Prado/O'Hara's VPIN work, Lo-MacKinlay's variance ratio test. That meant I could build something that's actually grounded in published methodology rather than invented heuristics, which is directly checkable in an interview.
- It's **directly on-point for GSET and CLSA** — this is the literal day-to-day of an execution desk, not a generic "AI stock picker" every other candidate might show up with.

---

## 2. Anticipated Interview Questions & Answers

### A. Elevator pitch / overview

**Q: Walk me through this project in two minutes.**
A: It's a Streamlit app with two analysis modes, both built on a multi-agent pipeline. Page 1 takes a ticker, order size (as % of ADV), and urgency, and runs it through nine agents: one fetches and cleans intraday/daily market data, one classifies the current market regime (volatility, volume shape, and trend via a formal variance-ratio test), one simulates eight different execution algorithms (VWAP, TWAP, POV, Implementation Shortfall, MOC, MOO, Liquidity-Seeking, Stealth) against that order, one compares them across the recent trading history and produces a sensitivity table, one turns that into a rule-based recommendation memo, one produces pre-trade cost estimates and post-trade TCA against multiple benchmarks, one checks the earnings calendar for overnight-gap risk, one independently estimates market microstructure metrics (Kyle's lambda, VPIN, a literature-calibrated impact cross-check), and a final critic agent independently reviews the recommendation and raises flags rather than silently overriding it. Page 2 is a separate event-study tool for index rebalancing — it estimates abnormal returns and volume around a stock's addition to or deletion from an index, using a market-model regression and known constituent-change data sources.

**Q: What's the single most interesting design decision in this project?**
A: Making the critic agent (Agent 8) *raise findings instead of auto-overriding the recommendation*. An automated system quietly overriding a trading decision based on a secondary check, with no visibility into why, would be worse than the problem it's solving. So the critic surfaces disagreements — "this pick has a fill rate below the qualification threshold," "there's an earnings print in 2 days and urgency is only Medium," "Kyle's lambda suggests the fixed impact model may be understating cost here" — as findings for a human to weigh, not silent corrections. That's a deliberate stance on what agentic autonomy should and shouldn't do in a money-adjacent workflow.

### B. Why "agentic" at all — the honest pushback question

**Q: Isn't this really just well-organized functions? What actually makes it "agentic"?**
A: Fair challenge, and I have an honest answer rather than an overclaimed one. As originally built, "Agent 1-6" was well-factored component-wise programming — each is a pure function, dataclass in/dataclass out, called in a fixed sequence, with Agent 5's "decision" being a static if/elif table. That's not autonomous reasoning. What I did next was deliberately add the pieces that make a system *more* genuinely multi-agent: (1) a shared `ExecutionContext` blackboard that every agent reads/writes instead of every downstream function importing upstream types by name — that's loose coupling; (2) an orchestrator that conditionally skips agents at runtime based on data actually available (e.g. it doesn't even attempt a spread estimate if there isn't enough daily history, rather than trying and catching a failure) — that's dynamic orchestration; (3) a critic agent that independently reviews the primary recommendation and can flag disagreement — that's the negotiation/verification pattern. I can also tell you what a *fully* agentic version would still need: true autonomy (an agent deciding its own action from open-ended goals, not a fixed sequence) and an LLM-backed synthesis layer that can handle edge cases the rule table can't enumerate. I chose not to put an LLM in the actual cost-calculation path, because that math needs to be deterministic and auditable — that's a considered trade-off, not a limitation I'm unaware of.

**Q: Where *would* you add real LLM reasoning if you extended this?**
A: On top of the deterministic quant agents, not inside them. A synthesis agent that reads all nine agents' structured output and can answer free-form follow-up questions ("why not POV here?"), or that handles regime combinations the fixed rule table never anticipated. The critic's *findings* are also a natural place — right now they're template strings; an LLM could reconcile several simultaneous findings into a single prioritized narrative. The one place I'd actively avoid it is the actual impact/cost math.

### C. Architecture deep dive

**Q: Describe the data flow / orchestration.**
A: `orchestrator.py`'s `run_pipeline()` takes market data and order parameters, builds an `ExecutionContext`, and runs agents 2 through 9 in dependency order, wrapping each in its own try/except so one agent failing (say, earnings data being unavailable for an obscure ticker) doesn't take down the whole pipeline — it just gets recorded in `ctx.errors` and everything else still runs. Agent 1 (market data) is deliberately *not* wrapped in the orchestrator — app.py calls it directly through a `@st.cache_data(ttl=300)`-decorated wrapper, so the network-bound fetch is what gets cached, not the whole pipeline; that way changing order size or urgency on an already-fetched ticker doesn't force a slow re-fetch.

**Q: What happens if an upstream agent fails?**
A: Downstream agents that depend on it are skipped, not force-run on missing data — e.g. Agent 5's memo is skipped if regime, simulation, or comparison data is missing, and that's recorded as `"skipped"` with a reason, distinct from `"failed"`. The context object treats a partial pipeline as first-class and inspectable rather than something that has to hard-stop the whole request.

### D. The execution algorithms themselves

**Q: What algorithms does it simulate, and how?**
A: VWAP (volume-proportional schedule based on a 5-day historical volume curve, deliberately excluding the simulated day itself to avoid look-ahead bias), TWAP (equal shares per bar), POV (participation-rate-capped, so it may not fill 100% — Low/Med/High map to 10/15/20% participation), and Implementation Shortfall, which I upgraded from an ad hoc exponential decay to an actual Almgren-Chriss optimal-execution trajectory parameterized by a risk-aversion term (kappa·T scaling with urgency). I also added MOC, MOO, a liquidity-seeking algo, and a stealth/low-footprint algo.

**Q: How do you compute cost?**
A: Slippage in bps is `(avg_exec_price − arrival_price) / arrival_price × 10,000`. Market impact uses a square-root law, `η × σ_daily × √(Q/ADV) × speed_factor × 10,000` with η=0.3, calibrated against the well-established square-root impact literature, with a per-algo speed factor (TWAP slowest at 0.85, up to Stealth/IS-High around 2.0) reflecting how aggressively each algo consumes liquidity. On top of that I added a proper Perold implementation-shortfall accounting for opportunity cost on unfilled shares, since a POV or Stealth algo that only fills 40% of an order at a great price is not actually "cheap" if the rest never got done.

**Q: Why did you feel the need for a *second*, independent impact model (Almgren et al. 2005)?**
A: Because a single fixed η=0.3 constant is a modeling assumption, not a fact, and I wanted a literature-anchored cross-check rather than just trusting my own constant. Almgren, Thum, Hauptmann & Li (2005) fit permanent and temporary impact separately to ~29,500 real Citigroup institutional orders — permanent impact is linear (α=1, γ=0.314), and temporary impact follows a concave power law with β=0.60, which is their finding that the classical square-root law's β=0.5 is rejected at 95% confidence in favor of a slightly steeper 3/5 power law. I report both models side by side in Pre-Trade Analytics; when they materially disagree, that disagreement is itself informative, and the critic agent flags it when Kyle's lambda also points that direction.

### E. Microstructure / order-flow toxicity (Agent 9) — likely the most technical questions

**Q: What is Kyle's lambda and how did you estimate it without an order book?**
A: Kyle's lambda (Kyle, 1985) is price impact per unit of signed order flow — the standard depth/liquidity metric in microstructure. Since I only have OHLCV bars, not tick-level trades, I classify each bar's volume into buy/sell fractions using Bulk Volume Classification (Easley, López de Prado & O'Hara, 2012) — essentially the normal CDF of the bar's standardized price change — and then regress *next-bar* returns on *this-bar's* net classified flow. I want to flag something I caught myself here: my first version regressed a bar's own return on that same bar's own BVC-derived flow, which is near-tautological since BVC's buy fraction is itself a function of that bar's own price change — it was producing suspiciously high R² (0.5-0.65). I re-derived it as a lagged, non-contemporaneous regression, which dropped R² to a much more realistic 0.6-6%, consistent with genuine microstructure regressions. That's a good example of catching my own methodological flaw by noticing a result was too good to be true.

**Q: What is VPIN and why does it matter?**
A: Volume-Synchronized Probability of Informed Trading (Easley/López de Prado/O'Hara) — an order-flow "toxicity" measure that reportedly spiked to historic levels in the hour before the May 2010 Flash Crash; a Berkeley Lab study for the SEC called it one of the strongest early-warning signals available. The canonical version buckets by fixed *volume* using tick data; I don't have tick data, so I implement a disclosed time-bar approximation using fixed-count 5-minute bars. I'm explicit in the docs that this is an approximation, not a canonical reading — I'd rather under-claim precision than over-claim it.

**Q: How do these feed back into the recommendation?**
A: They don't silently change Agent 5's pick — they're surfaced as critic notes: elevated VPIN prompts a note asking whether the chosen algo's participation pattern still makes sense if flow stays one-sided, and a statistically significant (|t|≥2) Kyle's lambda pointing to higher sensitivity than the fixed 0.3 constant assumes prompts a cross-check note against the Almgren estimate.

**Q: Have you looked into getting real order-book or tick data instead of approximating from OHLCV bars?**
A: Yes — I did a dedicated feasibility pass on this rather than just assuming it's impossible for free. Bottom line: genuine free order-book/tick data does exist, but only for US equities, and every option has a real trade-off. IEX Exchange publishes free, no-registration DEEP (order-book depth) and TOPS (top-of-book) data for every symbol it trades, going back a rolling 12 months, updated daily — that's real tick-by-tick data, not an approximation, and there are existing open-source Python parsers for its pcap format. The catch is IEX only carries about 3-6% of a given stock's consolidated volume, so it's a real order book, just a single-venue view. LOBSTER offers free, fully-reconstructed limit-order-book samples built from genuine NASDAQ ITCH data, but frozen to one specific day (June 21, 2012) for five fixed tickers (AAPL, AMZN, GOOG, INTC, MSFT) — great as a one-time ground-truth benchmark, not a live source. Databento gives $125 in free credit for real L3 data, which is generous but depletes with use, not a standing free tier. And I directly checked HKEX and JPX — both confirmed paid-only for tick/order-book data, so this entire upgrade path can only ever cover the US-ticker subset of the 14 markets this project supports; the Asian markets stay OHLCV-only no matter what. I haven't built the integration yet — this was a feasibility and cost/benefit investigation, and my plan if I did build it would be to use IEX HIST for live US-name validation and the LOBSTER 2012 sample as a fixed benchmark to quantify exactly how far my BVC/VPIN approximation is from the genuine reconstructed order book on that one day.

### F. Data & methodology honesty (this will come up — lean into it)

**Q: What are the limitations of using free yfinance data instead of a real feed?**
A: No order book/NBBO, no tick-level trade prints, no venue or dark-pool routing data, and no cross-sectional peer universe (so percentile rankings are read against a name's own history, not a peer set). Every metric I built on top of this is designed to *disclose* its approximation rather than silently present a proxy as the canonical figure — the VPIN reading says "time-bar approximation," the Corwin-Schultz spread estimate carries a reliability flag when the read looks implausible for a liquid name, and the pipeline gracefully skips (not force-runs) analyses when there isn't enough history for a stable estimate.

**Q: How do you know any of these numbers are actually right without a ground-truth feed?**
A: A few ways. First, internal consistency checks — e.g. an "arrival-benchmark consistency check" that verifies the reported arrival price actually matches across pre-trade and post-trade views. Second, structural sanity tests — I have a test asserting that fill rate degrades and impact rises *monotonically* as order size grows, which would catch a sign error or unit bug immediately. Third, cross-checking two independently-derived numbers against each other (my square-root model vs. Almgren's calibrated model; my own Kyle's lambda vs. the literature model) — agreement is reassuring, and disagreement is itself a signal I surface rather than hide.

### G. Index rebalancing event study (Page 2)

**Q: How does the event study work?**
A: Standard event-study methodology — an OLS market-model regression (`R_stock = α + β·R_index`) estimated over a T-70 to T-11 trading-day window, used to compute expected returns and therefore abnormal returns and cumulative abnormal returns (CAR) around the event date, plus abnormal volume and price indexed to 100 at the event. I extended it with a few things: closing-auction concentration analysis (rebalancing trades are disproportionately executed at the close), a post-event reversal metric (price often partially reverts after the flow-driven pop), a pre-announcement-vs-pre-effective drift decomposition (MSCI/FTSE-style changes are announced ahead of the effective date, and the price action in each window has a different character), a flow-to-trade estimator, and an event-day impact recalibration since impact models calibrated on normal days understate cost on a day when index funds are all trading the same name at once.

**Q: What was the trickiest bug here?**
A: A timezone bug — yfinance returns tz-aware DatetimeIndexes for Asian markets, and if you don't strip the timezone *before* reindexing the price series to build the indexed-to-100 chart, you get silent NaNs that make the price line look flat at 100 the whole time. Easy to miss because it doesn't throw an error, it just quietly produces a wrong-looking-but-plausible chart.

### H. Engineering practices

**Q: How did you test this?**
A: Each new agent module first gets a standalone live test against real tickers before being wired into the orchestrator (e.g. I tested Agent 9's Kyle's-lambda/VPIN/Almgren outputs across AAPL, a Taiwan name, and a Hong Kong name independently first). Then the full orchestrator pipeline gets tested end-to-end across multiple market/order combinations, checking that the trace shows no `"failed"` entries. Then the Streamlit UI itself gets smoke-tested headlessly with Streamlit's `AppTest` framework, asserting `not at.exception` and scraping the rendered text to confirm every new UI string actually appears. I also keep a regression suite (edge cases like a 0%-ADV order, boundary order sizes, lunch-break markets) that gets rerun after any change to a shared module.

**Q: Tell me about a bug you found and how you fixed it.**
A: Two good ones. The Kyle's-lambda circularity issue above is a methodology bug I caught by being suspicious of a too-good result. The other is more of an engineering-process one: while building this out I hit a recurring issue where a file I'd just edited would sometimes show a truncated version when I inspected it a different way — one instance left `agents/context.py`'s last method ending mid-statement (`return any(...)` cut down to `retu`), which is syntactically legal as a bare expression so it didn't fail compilation, but would have thrown a `NameError` the first time that method was called. I caught it in a final linting pass (`pyflakes` flagged the undefined name) rather than in production, which is exactly why I run a full static-analysis pass as a last verification step even when everything "compiles."

### I. Extensibility / next steps

**Q: What would you build next with more time or a real data feed?**
A: With a real feed: canonical tick-based VPIN and Kyle's lambda instead of the time-bar/BVC approximations, and a real order-book depth model instead of Corwin-Schultz's range-based spread proxy. Architecturally: concurrent execution of agents that don't actually depend on each other (regime and spread estimation both only need raw market data), and a persistent memory layer so pre-trade estimates for a given name are informed by that name's own realized-cost history across sessions, not just a fixed lookback window recomputed from scratch every run.

**Q: Why does this matter for a GSET / CLSA role specifically?**
A: Because it's built around the actual mental model of an execution desk — regime-aware algo selection, pre-trade cost estimation, post-trade TCA against multiple benchmarks, and a monitoring layer for order-flow toxicity — using the same academic foundations (Kyle, Almgren-Chriss, VPIN) that real desks use, rather than a generic "AI for finance" demo. It also shows I understand where the free-data ceiling is and how to build honestly around it, which is exactly the kind of judgment a desk would want before trusting a junior analyst's numbers.

### J. Quick facts to have ready

- Impact model: `η × σ_daily × √(Q/ADV) × speed_factor`, η=0.3
- Almgren et al. (2005): γ=0.314 (permanent, linear, α=1), η=0.142, β=0.60 (temporary, rejects β=0.5 square-root law at 95% CI), δ=0.25 (turnover liquidity factor), fit to ~29,500 real Citigroup orders, Dec 2001–Jun 2003
- Speed factors: TWAP 0.85, VWAP 0.90, POV 1.00, IS Low/Med/High 1.20/1.55/2.00
- POV participation rates: Low 10%, Med 15%, High 20%
- VPIN thresholds: <0.25 Low, 0.25-0.40 Normal, 0.40-0.60 Elevated, >0.60 High
- Lo-MacKinlay variance ratio: grid q=(2,4,8), q=4 heteroskedasticity-robust z* is headline stat, significance at |z*|≥1.96
- Event study estimation window: T-70 to T-11
- 14 markets supported (US + 13 Asia/Pac), 9 agents, 2 pages

---

## 3. Limitations of the Project

Be upfront about these if asked, or better, raise 1-2 unprompted — it reads as rigor, not weakness.

### A. Data feed limitations

- **Free yfinance OHLCV only** — no order book/NBBO, no tick-level trade prints, no venue/dark-pool routing data. Rate-limited (handled with a friendly retry message and a 0.3s inter-call delay, not a real fix).
- **Short history windows** — 5-min intraday bars are only fetched for a 5-day window per call; ADV is computed over a trailing 60 daily bars. Both are yfinance's practical retention limits, not a deliberate design choice.
- **`shares_outstanding` is best-effort** — fetched via the slower `.info` endpoint, which sometimes returns nothing; when it does, Agent 9's Almgren turnover-liquidity factor is silently omitted, not estimated or imputed.
- **Session-length assumptions were empirically discovered, not documented anywhere official** — e.g. Hong Kong and Japan's lunch breaks meant yfinance actually delivers fewer intraday bars than the exchange's posted hours implied, which was overstating annualized volatility by 8-10% until I caught it by checking live data. The "bars per day" constants are calibrated against what the feed currently delivers and could silently go stale if yfinance's delivery changes again.
- **No fundamentals beyond best-effort shares outstanding** — no float, short interest, options positioning, or broker/venue market-share data, all of which a real desk's toxicity/impact estimates would use.

### B. Modeling assumptions

- **Impact coefficients aren't fit to this project's own tickers.** The η=0.3 square-root constant is a literature-typical value, and the Almgren et al. (2005) coefficients were fit to Citigroup US institutional orders from 2001-2003 — both are applied uniformly across all 14 markets, including several Asian markets with materially different tick sizes, lot sizes, and retail participation shares. A real desk would recalibrate regionally.
- **Simulation is schedule-based, not a limit-order-book match.** Algorithms consume historical OHLCV bars on a schedule; they don't interact with a simulated book, don't face queue position or latency, and a simulated order's own modeled impact doesn't feed back into the price path used to fill the rest of that same order.
- **No fees.** No commissions, exchange/regulatory fees, stamp duty (relevant in HK/UK), borrow costs, or FX conversion costs are modeled.
- **VPIN, Kyle's lambda, and the spread estimate are all disclosed approximations** — time-bar BVC standing in for tick/quote-based classification, and Corwin-Schultz's high/low-range proxy standing in for an observed NBBO spread. Each carries an in-UI caveat rather than presenting itself as canonical.
- **Regime and toxicity thresholds are fixed constants** (|z*|≥1.96, VPIN bands, spread-reliability bands), not calibrated per ticker or market, and read against a name's own history rather than a peer set.
- **Post-trade reversion and impact-decomposition checks have no control group** — they're directional diagnostics, not causal measurement, since OHLCV data alone can't isolate impact the order caused from ordinary drift or news. The app says this explicitly in the UI rather than implying more precision than it has.

### C. Index rebalancing constituent data — fact-checked, not assumed

I verified this rather than just restating what I'd written in the project docs earlier, and it's a more precise (and more interesting) limitation than "data is limited":

- MSCI does publish free, public Index Review results, but the notice period is more nuanced than I'd originally described: the scheduled quarterly/semi-annual Index Review results are announced roughly **2-3 weeks (~20 days)** ahead of the effective date, while **unscheduled, ad hoc** additions/deletions (delistings, M&A, new listings added mid-quarter) get only about **2 days'** notice. There's no free bulk historical API — MSCI's own Index API is a paid, licensed product.
- S&P/Dow Jones and FTSE Russell historical constituent-change data (exact add/remove dates going back several years) exists through third-party APIs (EODHD, Financial Modeling Prep, Xignite, Twelve Data) — all paid, not free.
- iShares publishes free, current-day holdings CSVs per ETF, a reasonable free proxy for *today's* index composition — but reconstructing *historical* changes means either paying, or continuously scraping and archiving those daily snapshots yourself going forward (open-source tools like `talsan/ishares` and `etf-scraper` do exactly this, but only from whenever you start running them; they can't retroactively recover a change from before that).
- For the **S&P 500 and Nasdaq 100 specifically**, Wikipedia crowd-sources a reasonably complete, dated "index component changes" table — a genuinely workable free source for the two US benchmarks in the app. For the **Asian markets that are this project's actual focus** (Taiwan, Hong Kong, Japan, Korea, etc.), there's no equivalent free, complete, dated historical source; you'd have to pull individual exchange or index-provider press releases per event.
- **Net effect on this project:** `run_event_study()` takes the ticker and effective date as direct user inputs (a date picker defaulted to today), not from any live feed. There's no "tell me what's about to be added to the Hang Seng" capability anywhere in the app. Say this plainly if asked: **the event-study tool answers "what happened to this stock's price around this known date," not "which stocks are about to be rebalanced."** The honest next step would be paying for one of the APIs above, or building and continuously running a scraper against free per-exchange announcement pages — buildable, just not built.
- One more thing worth mentioning if asked about your QA process: while fact-checking this, I found (and fixed) a real bug in Page 2's index dropdown — it had drifted out of sync with the module's actual 19-entry index-proxy map, offering only 4 hardcoded choices, 3 of which didn't exactly match a dictionary key and would have silently fallen back to the Taiwan index as the market-model benchmark for Hang Seng/KOSPI/MSCI-labeled runs. It's fixed now (the dropdown is generated from the same dict the backend actually uses), but it's a good, concrete example to have ready if asked "how do you catch bugs" — verify against the actual code path, not the docs describing it.

---

## 4. Benefits of an Agentic Framework (standalone answer)

If asked directly "what are the actual, concrete benefits of building this agentically" — separate from the origin-story narrative in Section 1 — give this crisper, project-grounded version:

1. **Fault isolation and graceful degradation.** Every agent is wrapped independently in the orchestrator; one failing (earnings data missing for an obscure ticker, insufficient daily history for a spread estimate) doesn't take the whole analysis down — it's recorded and skipped, and everything else still runs. A monolithic script doing all of this inline would need far more defensive code at every step to get the same resilience.
2. **Independent verifiability, testability, and reuse.** Each agent has a typed input/output and can be built, unit-tested, and live-tested in complete isolation before ever touching the pipeline — that's literally how Agent 9 (microstructure) was validated against three live tickers before it was wired in. It also means one agent's output (Agent 1's market data) feeds nine different downstream consumers without any of them needing to know how it was fetched.
3. **A genuine negotiation/verification pattern, not just decomposition.** The critic agent is the clearest payoff: it doesn't re-derive the recommendation, it independently checks it against context the recommendation engine never sees (earnings calendar, VPIN, Kyle's lambda) and raises disagreement as a visible finding rather than silently trusting or silently overriding the primary pick. That's a materially more trustworthy pattern than one model producing one unchecked answer.
4. **Conditional, data-aware orchestration instead of a fixed script.** The orchestrator decides at runtime which agents are even worth attempting — e.g. it skips the spread estimate entirely below 22 days of daily history rather than trying and catching a failure — which keeps the pipeline from doing, or reporting, low-confidence work it already knows isn't reliable.
5. **Extensibility without cross-cutting rewrites.** Adding Agents 7, 8, and 9 to an already-working pipeline meant adding one field to the shared context and one call in the orchestrator each time — not touching Agents 1-6's code or app.py's existing rendering logic. That's the concrete payoff of the blackboard/shared-context pattern over explicit dataclass-threading.

Worth pairing with the honest caveat from Section 2B if pushed further: none of this required an LLM in the loop, and I don't think it should have — these benefits come from the *architecture* (decomposition, shared state, independent verification, conditional execution), which is a software-engineering pattern valuable whether or not any individual "agent" happens to be backed by a language model. Where an LLM would genuinely add something is a synthesis/reasoning layer *on top* of this structure — not inside the deterministic cost math.

---

## 5. Demo Script

**Framing at the start:** "Let me show you the execution simulator first — that's the core deliverable — then the index-rebalancing event study."

### Step-by-step (aim for 6-8 minutes; trim to the starred steps if you only have 3)

1. **★ Open Page 1, pick a live example.** Select a market (e.g. US or Taiwan for variety), enter a ticker, set order size to something that will actually bind (e.g. 15-20% ADV) and urgency to Medium, click Run. While it loads, narrate: "this is fetching real intraday and daily data from Yahoo Finance and running it through nine agents."

2. **★ Land on the Agent 5 recommendation memo (pinned at top).** Point out the primary algo pick, the one-line regime summary, and the risk flags. Say: "this is a rule-based decision layer, deliberately not an LLM — reproducible and testable."

3. **Show the Agent 2 regime section — click into the "Price Trend (Variance Ratio Test)" expander.** This is a good moment to mention you replaced a naive autocorrelation threshold with the Lo-MacKinlay variance-ratio test — shows methodological depth without being asked.

4. **Show the Agent 3/4 comparison table and sensitivity matrix.** Point out the multi-day cost comparison and how the sensitivity table shows cost rising with order size across all 8 algos.

5. **★ Scroll to Pre-Trade Analytics.** Show the Expected Cost Range (mention it's now an empirical P10/P50/P90 band, not just mean±std, "because impact-cost residuals are fat-tailed"), and the Almgren et al. (2005) cross-check metrics sitting right below it.

6. **★ Show the Market Microstructure & Liquidity section (Agent 9).** This is your strongest technical differentiator — walk through the Kyle's lambda metric and note, and the VPIN badge. Be ready to explain the sign of Kyle's lambda if it's negative (mean-reversion / bid-ask-bounce) vs positive (persistent impact).

7. **Scroll to Post-Trade TCA.** Show the multi-benchmark table (Arrival/VWAP/TWAP/Close) and the Impact Decomposition (permanent I / realized J / temporary K) — mention this reuses the same Almgren framework from pre-trade, applied after the fact.

8. **Show a Critic finding.** If one exists for this run (e.g. an earnings-date flag or a VPIN note), read it aloud — it's a good demonstration of the "verification agent doesn't silently override" design principle.

9. **★ Switch to Page 2 — Index Rebalancing.** Pick an index (e.g. Hang Seng or S&P 500) and a recently-added/removed constituent, run the event study. Show the CAR chart building around the event date, then flip to the Abnormal Volume tab, then Price Performance. Point out the closing-auction concentration and post-event reversal metrics in the summary table.

10. **Close with the code, if they want to go deeper.** Open `agents/orchestrator.py` and `agents/context.py` briefly to show the blackboard pattern and graceful partial-failure handling — takes 30 seconds and immediately signals real engineering practice, not just a UI.

### If asked to improvise live

- Change the order size slider from 5% to 25% ADV on the same ticker and re-run — narrate how fill rates degrade and impact rises, live, across the algos.
- Switch urgency from Low to High and show the primary algo recommendation flip to Implementation Shortfall, and the Almgren-Chriss trajectory note change (kappa·T scaling up).
- If they ask about a market you haven't tested, pick a random one from the 14 supported and run it live — the pipeline's graceful degradation (skips vs. failures) is designed to survive exactly this kind of put-on-the-spot moment.

### Fallback if the live Yahoo Finance fetch is rate-limited or slow

Mention it up front so it doesn't look like a bug: "there's a 300ms delay between calls and friendly rate-limit handling since this runs off free Yahoo Finance data — in a real desk build this would sit behind a paid feed." Have a ticker you've already run recently queued up (cached for 5 minutes via `@st.cache_data`) as a backup.
