# Interviewer-Specific Prep — APAC ES Markets, Client Context & Behavioral (July 2026)

*20 questions with standard answers and practical-application
notes. Source of truth: `docs/quiz_src/interviewer_questions.py` — edit there and re-run
`build_bank.py` to regenerate this file and `INTERVIEWER_PREP_BANK.html` together.*

**Categories:** Markets: China & HK (4) · Markets: Japan (4) · Markets: APAC breadth (4) · Wheel & TCA advisory (3) · Client situations (behavioral) (5)

## Reading the interviewer

Zhejiang University economics/finance → Goldman Hong Kong (analyst, 2012–14)
→ Tokyo (analyst then associate, 2014–17) → senior APAC Execution Solutions.
What that path implies: **China/Hong Kong depth by origin and client base;
Japan depth by lived experience** — she was on the desk in Tokyo through the
2014–15 TSE tick-size program, the formative microstructure event of that
market's decade. Twelve-plus years in one franchise means she has owned the
same client relationships across multiple market-structure regimes; expect
questions that test whether your knowledge is textbook or operational. If
you share a Mandarin exchange at the start, let HER initiate it.

## Her week: five client conversations (the context behind her questions)

**1. The quarterly wheel review (global asset manager).** Client's algo wheel
demoted GS from #2 to #4 this quarter. Her call: acknowledge the raw number
without defensiveness, then walk the flow-mix decomposition — "your PM desk
sent us 2.3x the average order size this quarter; here is the like-for-like
comparison" — and close with what's being fixed regardless ("we've proposed a
spec change to the small-cap dark logic; here's the A/B timeline"). The skill
is defending WITHOUT excuse-making: both ranks shown, one commitment made.
*Her likely interview probe from this life: "our algo ranks fourth on a
client's wheel — walk me through your investigation."*

**2. China access advisory (US long-only entering A-shares).** Nothing in the
client's US playbook transfers cleanly: ±10% price limits (20% on
ChiNext/STAR), T+1 — no same-day round trip, sells pre-checked against
custody (SPSA), Connect holiday calendars that close the pipe while both
markets are open, a heavy-open volume profile, lunch break, and a 3-minute
closing call auction. Her job is translating those into algo-parameter
consequences: front-loaded curves, limit-aware urgency, auction strategy.
*Probe: "a US client asks what breaks when they bring their US VWAP habits
to Shanghai — what do you tell them?"*

**3. The Japan close deep-dive (quant fund unhappy with MOC results).** Japan
changed in Nov 2024: hours extended to 15:30 with a NEW closing auction
session. Her conversation: how the close's information/liquidity profile
shifted, what happened to the old 14:55–15:00 patterns, PTS (Japannext/Cboe
Alpha) interaction, and how the algo's close participation logic adapted.
*Probe: "what did the 2024 TSE close reform change for execution, and how
would you MEASURE whether an algo adapted well?"*

**4. The customization request (hedge fund wants bespoke behavior).** Client
wants lower dark participation in small caps and a custom urgency ladder.
Her workflow: scope it as a spec (exact parameter, exact scope), estimate
the effect ex-ante from history, then insist on a measurement plan — "we'll
run it as an A/B against the default for eight weeks; at your flow, that
detects ~3 bps" — managing the client's impatience with sample-size honesty.
*Probe: "a client asks for a customization you suspect hurts them — what do
you do?" (behavioral, below).*

**5. The market-event color call (rebalance day / rule change).** MSCI
effective day, a Korea short-sale regime change, a Taiwan limit-lock episode:
she sends the note BEFORE clients ask — what happened to spreads/depth/close
volumes, what the algos did, what clients should change tomorrow. Proactive
color is how ES creates relationship value between reviews.
*Probe: "Korea just changed a market rule — what's your process from
headline to client note?"*


**Tiers:** T1 · Highly likely (her home turf) (8) · T2 · Likely (8) · T3 · Possible (4) — study Tier 1 to fluency first, Tier 2 is where the interview lives, Tier 3 differentiates.

## Markets: China & HK

**Q1. What actually breaks when a US institution brings US execution habits to A-shares via Stock Connect?**  
*[T1 · Highly likely (her home turf)]*

*Standard answer:* Almost everything load-bearing. T+1 means no same-day round trip — an 'oops' buy can't be unwound today. Sells are pre-trade checked against segregated custody (SPSA), so shares must be in place before the order, not at settlement. Price limits (main board ±10%, ChiNext/STAR ±20%, ST names ±5%) censor the day's distribution — stops and 'wait for better levels' logic behaves differently when the market can pin. The volume profile is heavily front-loaded versus a US U-shape, with a hard lunch (11:30–13:00) and a 3-minute closing call (14:57–15:00) rather than a deep continuous close. Connect adds its own layer: holiday-calendar mismatches close the pipe while both markets trade, and northbound flow is visible in aggregate. Practical translation: reshape curves to the local profile, make urgency limit-aware, and treat the tiny close differently from a US MOC.

*Practical application:* Vignette 2 verbatim — her most likely China question, and the answer format she uses with clients: rule → consequence → parameter change.

**Q2. Walk through Hong Kong's closing auction (CAS) and VCM — mechanics and execution implications.**  
*[T1 · Highly likely (her home turf)]*

*Standard answer:* CAS (reintroduced 2016 after the 2009 suspension): 16:00–16:08/16:10 with staged order entry, a two-stage price funnel (first ±5% of reference, then constrained within best bid/ask), random-time close to blunt gaming, and at-auction plus at-auction-limit order types. Implications: it's the reference print for benchmarks and rebalances, deep on index days; the funnel makes extreme dislocations rarer than a free-form call. VCM: per-stock ±10% versus the price 5 minutes ago triggers a 5-minute cooling-off (trading continues inside a band) — it's a speed bump, not a halt; algos must recognize the band state and not fight it. Also worth volunteering: 0.1% stamp each side (cut back from 0.13% in Nov 2023) dominates HK explicit costs and changes maker/taker calculus versus the US.

*Practical application:* She traded through the CAS reintroduction era. Knowing WHY the funnel exists (the 2009 gaming history) is the operational-vs-textbook tell.

**Q3. Why is the A-share intraday volume curve shaped so differently from the US, and what does it do to VWAP algo design?**  
*[T2 · Likely]*

*Standard answer:* Mechanics drive it: a 9:15–9:25 opening call (with a no-cancel window 9:20–9:25) concentrates price discovery, retail participation is heaviest early, the lunch break splits the day into two sessions with a mini-open at 13:00, and the close is a 3-minute call rather than a liquidity magnet — so volume is front-loaded with a modest afternoon rebuild, not U-shaped. VWAP design consequences: curves must be estimated per-market (a US curve mis-schedules badly), the lunch boundary needs explicit handling (no fills, gap risk across it), and completion targets should not lean on a deep close that doesn't exist. Limit days distort everything — curves conditioned on limit proximity are the sophisticated version.

*Practical application:* Connects microstructure to algo design — exactly the 'product evolution' third of her JD.

**Q4. A client asks about shorting China A — what's the honest advisory answer?**  
*[T3 · Possible]*

*Standard answer:* Practically unavailable at institutional scale. Onshore, securities lending runs through the margin-trading list with limited borrow, and the regulatory posture has tightened repeatedly (lending supply was further restricted in 2024). Through Connect, southbound-style borrowing mechanics for northbound shorts exist on paper with tight constraints and have never been material. So the honest answer: express short views via index futures (with basis risk), H-share pairs where dual-listed, or accept the constraint. Advisory framing matters — clients respect 'this door is effectively closed, here are the three real alternatives' far more than a mechanics tour of a door nobody gets through.

*Practical application:* Tests advisory judgment: the right answer is a recommendation, not a regulation recital.

## Markets: Japan

**Q5. What did the November 2024 TSE reform change about the close, and how would you measure whether an algo adapted well?**  
*[T1 · Highly likely (her home turf)]*

*Standard answer:* Trading extended to 15:30 (from 15:00) and TSE introduced a closing auction session — a structural change to where the day's terminal liquidity lives and how closing prices form. Measurement design, which is the real question: compare close-benchmark orders pre/post reform on (1) tracking to the official close, (2) share of fills in the auction versus the final continuous minutes, (3) dislocation of the auction print versus 15:25 mid, and (4) reversion after the print — with the pre/post comparison controlled for volatility regime, since the reform didn't arrive on identical markets. The honest caveat: early post-reform months mix learning effects (everyone's algos adapting) with the mechanism change itself — a reason to keep re-measuring rather than concluding once.

*Practical application:* Vignette 3. She lived the OLD close for years — showing you know the reform AND how to evaluate adaptation is the strongest Japan answer available.

**Q6. Explain Japan's price limit and special-quote mechanism — how does it differ from a hard halt, and what should an algo do?**  
*[T1 · Highly likely (her home turf)]*

*Standard answer:* Daily price limits set a hard band from the previous close, but intraday TSE uses special quotes rather than immediate halts: when order imbalance would move price beyond a renewal threshold, the exchange displays an indicative special quote and walks it in steps over minutes, seeking matchable levels — a controlled slow-down rather than a stop. Distinct from LULD-style pauses: liquidity discovery continues visibly. Algo behavior: recognize the special-quote state (prints stall, indicative moves in steps), stop treating the indicative as a fillable price, pause momentum-sensitive logic, and re-evaluate schedules — chasing a walking special quote is paying the mechanism. At the daily limit itself, resting at the limit queue is the only expression left — Taiwan-style lock dynamics apply.

*Practical application:* Deep Tokyo-desk knowledge; the 'don't chase the walking quote' line marks operational understanding.

**Q7. The 2014–15 tick-size program: what changed and what were the execution consequences?**  
*[T2 · Likely]*

*Standard answer:* TSE cut tick sizes for TOPIX100 names in phases (Jan 2014, Jul 2014, refinements into 2015), moving the most liquid names to sub-yen ticks. Consequences: quoted spreads compressed toward the new ticks in tick-constrained names; queue value collapsed (shorter queues, less reward to resting early), shifting the passive/aggressive balance; effective-vs-quoted spread capture changed for passive strategies; and part of the PTS value proposition (finer pricing off-exchange) was absorbed by the primary. It's also the canonical natural experiment for 'what happens to depth when ticks shrink' — depth thinned at the touch while total near-touch depth reorganized. If asked why it matters NOW: same debate as the US 2024 sub-penny reform — the Japanese evidence is the reference case.

*Practical application:* She was in Tokyo during exactly this. Connecting it to the US tick reform shows you think across markets — her daily mode.

**Q8. Where does off-exchange liquidity live in Japan, and when do you use ToSTNeT?**  
*[T3 · Possible]*

*Standard answer:* PTSs — Japannext and Cboe Alpha — provide lit alternative venues (finer ticks historically, extended hours), with dark liquidity comparatively thinner than the US; margin-trading rules once limited PTS shorting, since relaxed. ToSTNeT is TSE's off-auction facility: single-price and negotiated crossings, standard for blocks, buybacks, and basket crossings at reference prices (e.g., ToSTNeT-1 crossing at last). Use ToSTNeT when size wants a reference-price transfer without walking the book — classic for transitions and internal crosses; use PTS routing for incremental price improvement in liquid names. Volunteer the SOR angle: best-ex in Japan means primary + PTS integration, and auction sessions remain primary-only.

*Practical application:* Rounds out the Japan map; 'ToSTNeT for baskets at reference' is program-trading vocabulary she'll recognize instantly.

## Markets: APAC breadth

**Q9. Design volume curves for an APAC multi-market VWAP — what breaks the one-curve-fits-all assumption?**  
*[T1 · Highly likely (her home turf)]*

*Standard answer:* Session structure first: lunch breaks (Japan, China, HK, Taiwan-none, Korea-none, SG-none — know which), so curves need explicit two-session shapes with mini-opens after lunch. Close mechanics vary from deep auction magnets (Japan post-2024, HK CAS, Korea) to 3-minute calls (China) to Taiwan's 13:30 early close — terminal mass differs by multiples. Opens: China/Korea front-load far more than HK. Then regime effects: rebalance days reshape everything toward the close; limit days (TW/CN/KR) censor and redistribute volume. Engineering answer: per-market empirical curves, re-estimated on rolling windows, with event-day overrides — and a monitoring stat (realized-vs-curve tracking error) so drift gets caught rather than assumed away.

*Practical application:* Pan-APAC scheduling is her product's daily reality; the monitoring-stat close shows production thinking.

**Q10. What's genuinely different about MEASURING TCA in APAC versus the US?**  
*[T2 · Likely]*

*Standard answer:* Four structural differences. (1) No consolidated tape — 'the market price' is the primary book plus fragmented alternatives you assemble yourself; benchmark construction is a choice to disclose. (2) Auctions carry a larger share of the day in several markets, so slippage decompositions need auction/continuous splits or they blur mechanisms. (3) Price limits (TW/CN/KR) CENSOR return and cost distributions — a locked stock's 'cost' is undefined against an untradeable benchmark, and naive averages over censored days are biased; you model or flag censoring explicitly. (4) Explicit costs vary wildly (HK/UK-style stamp vs clean markets) and belong side-by-side with implicit costs or cross-market comparisons mislead. Plus the mundane one: time-zone-correct sessionization, or your 'daily' stats straddle two trading days.

*Practical application:* The censoring point is a statistician's observation about HER geography — likely the single most impressive sentence available in this interview.

**Q11. Korea just resumed short selling (March 2025) with new institutional requirements — what's your process from headline to client note?**  
*[T2 · Likely]*

*Standard answer:* Process over content: (1) primary sources first — KRX/FSC notices, not press summaries; extract the operative rules (covered-only, internal system/audit requirements, position reporting, penalties). (2) Translate to client impact by client type: quant funds care about borrow, locate workflow, and whether systems certification gates their access; long-onlys mostly care about market-quality effects. (3) Form the measurable hypotheses — spreads, borrow utilization, index-arb basis normalization — and set up the before/after measurement rather than asserting effects. (4) Ship a short note: what changed, who's affected, what we're watching, what we'll report next. The discipline is separating rule-facts from predicted effects, and dating the predictions so you can be held to them.

*Practical application:* Vignette 5 as a process answer — ES seniors hire people whose first instinct is primary sources + measurement design.

**Q12. A client executes a pan-Asia basket. How do you think about sequencing across time zones?**  
*[T3 · Possible]*

*Standard answer:* The wave logic: markets close in sequence — Tokyo/Taipei early afternoon HK time, then China/HK/SEA, then India, with Australia opening earliest — so the program works earliest-close-first, sizing each market's tranche against ITS close capacity rather than treating the basket as one pool. Cross-effects to manage: information leakage from early-market prints into correlated later markets (finish Japan quietly before India wakes), FX cutoffs for funding (especially T+1 US legs and restricted currencies), and holiday asymmetries that strand a leg. Residual risk that can't complete in wave one rolls to the next session with explicit overnight-gap accounting. The deliverable clients value is the wave plan itself: which names, which close, what carries.

*Practical application:* Program-trading coordination in her coverage universe; 'size against each close's capacity' is the senior phrasing.

## Wheel & TCA advisory

**Q13. Our algo ranks fourth on a client's wheel this quarter, down from second. Walk me through your investigation.**  
*[T1 · Highly likely (her home turf)]*

*Standard answer:* First, respect the number — never open with excuses. Then three-layer decomposition: (1) Flow mix — did our share of hard flow rise? Compare our orders' size/spread/volatility/urgency distribution versus peers' allocation this quarter; wheels rank flow as much as engines. (2) Conditional performance — re-rank on a like-for-like basis (regression with condition controls, or matched strata); if we're second conditionally, the story is mix and the client conversation is about allocation fairness, shown with BOTH ranks. (3) If we're genuinely worse conditionally: localize it — which market, size bucket, time-of-day, venue? A real degradation is usually concentrated (a venue change, a parameter drift, one market's close), and that localization IS the spec proposal. Close the loop with the client: here's what we found, here's the fix, here's when you'll see it re-measured.

*Practical application:* Her JD's first line as a scenario. The three-layer structure (mix → conditional → localize) is the professional standard she'll recognize.

**Q14. A client's wheel uses raw average slippage with no conditioning. Do you tell them their methodology is wrong?**  
*[T2 · Likely]*

*Standard answer:* Not in those words — their wheel, their rules, and criticizing a client's framework head-on loses the room. The move: add information, don't subtract legitimacy. 'Raw averages are a fair headline; here's a companion view that holds order difficulty constant — on like-for-like flow the ranking looks like this.' If the conditional view flatters us, the client now has a reason to care about methodology; if it doesn't, we've earned credibility for honesty. Longer game: offer to help them evolve the wheel (stratified buckets, minimum-sample rules, outlier policies) as a service — brokers who improve a client's measurement become advisors rather than vendors, which is the entire ES relationship model.

*Practical application:* Client-management judgment layered on statistics — the answer she'd give herself, which is the point.

**Q15. What belongs in a deep-dive TCA review deck for a sophisticated client, and what do you leave out?**  
*[T2 · Likely]*

*Standard answer:* In: the executive page (period costs vs expected, versus prior period, with the mix-shift explanation); attribution that reconciles (delay/trading/opportunity/explicit — components summing to the total); distributional honesty (medians and tails, not just means — clients remember their worst orders); condition context (their flow got harder/easier); two or three SPECIFIC findings with recommendations tied to parameters ('your 4pm orders pay 6 bps more; shift the cutoff'); and what changed since last review's commitments — closing the loop is what makes reviews compounding rather than episodic. Out: methodology tourism, unactionable metrics, anything you can't defend under one 'how is that computed?' — and never a chart whose caveat you'd only mention if asked.

*Practical application:* The deliverable of her week. 'Components that reconcile' + 'closing last review's loop' are the two credibility markers.

## Client situations (behavioral)

**Q16. You discover an error in analysis already sent to a client. What do you do?**  
*[T1 · Highly likely (her home turf)]*

*Standard answer:* Correct fast, in person, with the fix attached. Verify the error and its direction/magnitude first — one hour of checking, not a week of hoping — then tell the coverage team and call the client before they find it: 'we found an error in Tuesday's review; the corrected number is X, the conclusion changes/doesn't change, and here's the process fix so it can't recur.' The instinct to soften or bury is the career-ending one: clients forgive corrected errors and never forgive discovered cover-ups; compliance-sensitive contexts make speed a duty, not a courtesy. Personal experience: my platform's regression suite exists because I once shipped in-sample thresholds under time pressure at Invesco — the process fix (pin every number, label every validation) is the durable apology.

*Practical application:* Integrity question — the answer is speed + ownership + systemic fix, with your real story as evidence you mean it.

**Q17. A client demands a customization you believe will hurt their execution. Walk me through it.**  
*[T1 · Highly likely (her home turf)]*

*Standard answer:* Steel-man them first — clients often optimize something invisible to TCA (workflow, internal reporting, risk appetite), so I'd ask what outcome they're targeting before opining. If I still believe it hurts: quantify, don't editorialize — 'here's the historical estimate: this setting costs your flow ~4 bps against the objective YOU stated' — and propose the experiment: run it as a measured pilot on a slice, revisit with data in eight weeks. Then, crucially: if they insist, implement it well and measure it honestly — it's their execution and our advice, in that order; the record of 'we advised, we measured, we reported' is both the relationship's integrity and, frankly, its best-ex documentation. Most such disputes end with the data; the ones that don't were never about the data.

*Practical application:* Vignette 4's hard version. 'Their execution, our advice, in that order' is the line that shows you understand agency.

**Q18. Sales pressures you to soften a negative finding before a client meeting. What do you do?**  
*[T2 · Likely]*

*Standard answer:* The numbers don't move; the framing can. I'd hear the concern — sales owns the relationship and may know context I don't — then offer the legitimate version: lead with what improved, size the negative finding fairly (n, confidence, materiality), pair it with the remediation plan. What I won't do is change a number, drop a material finding, or bury it in an appendix — beyond ethics, it's tactically wrong: sophisticated clients re-run our math, and one discovered omission costs more than ten honest bad quarters. If we're at an impasse, escalate jointly rather than freelance — 'let's take it to the desk head together' resolves it without making sales the enemy. In this seat, credibility is the product; you can't discount it for one meeting.

*Practical application:* 'Credibility is the product' — likely the most senior-sounding sentence a candidate can say in an ES interview.

**Q19. How would you build a relationship with a client who barely gives us flow and is loyal to another broker?**  
*[T2 · Likely]*

*Standard answer:* Earn a slot with analysis they can't get from the incumbent, not with generic coverage. Concretely: find the one thing our data can say about THEIR situation — a market-structure note relevant to their footprint (say, they trade Taiwan small caps: a limit-lock risk study), or an honest wheel-methodology suggestion that helps them measure everyone better, including our competitor. Ask for feedback, not flow — 'was this useful, what would make it useful' — and deliver twice more on whatever they answer. Flow follows demonstrated usefulness plus low switching friction: offer a measured pilot (a wheel slice) where we're accountable to numbers from day one. And patience: displacement is quarters, not meetings; the failure mode is pitching product before proving insight.

*Practical application:* Business-development judgment for an analyst seat: insight-first, measured-pilot close, honest time horizon.

**Q20. A client calls angry during market hours about a large order that's performing badly RIGHT NOW. Handle it.**  
*[T3 · Possible]*

*Standard answer:* Triage before theory. First minute: acknowledge and get the facts — order, benchmark, expectation gap — while pulling it up live; no defensiveness, no instant diagnosis. If something is genuinely wrong (parameter mis-set, algo misbehaving near a limit state): say so, fix it, confirm the fix, full post-mortem later — action beats explanation intraday. If the algo is behaving correctly in an ugly tape: explain in one breath what it's doing and why ('it's slowed because spreads tripled; forcing completion now costs ~X bps — want urgency raised anyway?') and give them the DECISION with its price, because it's their order. Either way, commit to the same-day follow-up with the full picture. Clients remember who was calm and honest at 2pm, not who was eloquent the next morning.

*Practical application:* Intraday composure question. 'Give them the decision with its price' is exactly how good ES people share control with clients.
