# AI on the PT Desk — JD Bullet by Bullet

*W5 deliverable (plan of 2026-07-28). For each JD responsibility: the
actual workflow, the tools a desk uses, where AI adds efficiency, what
this project already demonstrates, and what stays human. One section
per bullet; sections added as walked through.*

---

## Bullet 1 — "Execute program trades across Asia markets in coordination with sales traders, supporting basket execution and client-driven flows"

**The responsibility.** The dealer is the execution engine behind the
sales trader: the sales trader owns the relationship and conversation;
the dealer gets 50–300 lines across 5–10 markets done at or better than
benchmark without incident. Client-driven means the trigger is external
(index rebalance, transition, quant turnover, redemption) and arrives on
the client's timetable.

**Workflow and tools:**

| # | Stage | What happens | Tools |
|---|---|---|---|
| 1 | Inquiry (T-1 / morning) | Client → sales trader: size, line count, markets, benchmark; often a blind profile (buckets, no tickers) for quoting | Email, Bloomberg IB chat, Excel |
| 2 | Pre-trade | Normalize the (messy) file; expected cost, %ADV, liquidity buckets, risk decomposition; constraint sweep: restricted list, foreign-room, short-sell eligibility + locates, board lots, limit proximity | Pre-trade TCA, OMS validation, Excel |
| 3 | Quote & terms | Benchmark choice (MOC/arrival/VWAP), horizon, participation caps, cash-balance constraint, FX needs; agency = commission conversation | Chat/phone |
| 4 | Staging | OMS load: symbology, allocations, compliance pre-flight, locates, FX legs flagged | OMS (Fidessa/FlexTrade-class) |
| 5 | Execution | Slice via EMS/algos against schedule through the Asia open cascade; monitor BY EXCEPTION: run-rate, buy/sell balance, halts, limit bands, auction cutoffs; sales trader relays progress + mid-flight revisions | EMS + algo suite, internal monitors, chat |
| 6 | Wrap | Residuals into closes; fills vs benchmark per line + total; exec summary → sales trader → client; bookings; FX | OMS/Excel/email |
| 7 | Post-trade | T+1 TCA report, recon breaks, settlement watch | TCA, back-office recon |

**AI per stage → built evidence:**

| Stage | AI enhancement | Built in this project | Time/risk effect |
|---|---|---|---|
| Intake | LLM parses client messages → structured intent; automated file normalization + symbology resolution | `pt_ops.client_file_normalizer` (explicit-issues design) | 10–20 min/basket; kills the top error source |
| Pre-trade | Auto-generated pre-trade pack + client-language narrative | `desk_pack`, `basket_risk` (blind profile, no-ticker test), `agency_quote_sketch` | 30 min → minutes; sales trader forwards instead of rewrites |
| Staging | Automated compliance pre-flight; statistical fat-finger detection (price×qty outliers) | `pt_dealer` pre-flight (lot sizes, limit bands, short-sell rules) | pre-incident, not post-incident |
| Execution | Exception ranking across 200 lines; intraday run-rate re-forecast; auction countdowns; alert→acknowledge audit trail | `pt_dealer.attention_queue`, `flow_forecast` re-forecast, `auction_countdown`, `pt_automation` alerts+ack | capacity: one dealer runs ~2x the baskets |
| Wrap | Auto-drafted client recap + EOD note (dealer edits, not writes) | `pt_automation` EOD draft | 20–30 min at the most error-prone hour |
| Post-trade | Recon exception classifier; TCA narrative generation | `pt_ops` recon classifier, IS attribution | ops follow-ups start pre-triaged |

**What stays human:** the client conversation; discretion calls
mid-flight; error ownership; every acknowledgment the audit trail
requires a person to make (which is why alerts carry an ack step).

**Honest desk-gap note:** our versions run on public/simulated data and
canned baskets; the desk versions bind to the OMS/EMS and real client
files. The mechanism and the human-in-the-loop points are what carry
over unchanged (per DESK_DEPLOYMENT_PLAN.md).

---

## Bullet 2 — "Monitor intraday liquidity, volatility, and market conditions across regional exchanges to inform execution strategies"

**The responsibility.** Maintain a live model of ~10 exchanges while
baskets work; output = execution ADJUSTMENTS (speed/slow, venue/auction
mix, completion-feasibility recheck) and early warnings to the sales
trader when costs will deviate from pre-trade.

**Workflow (a scan cadence, not staring):** pre-open overnight recap
(US close, FX, futures, ADR-implied opens, day's calendar) → open
cascade with auctions watched → mid-morning / post-lunch checkpoints →
close cascade with countdowns. Tools: Bloomberg monitors/futures/FX,
EMS analytics + volume curves, internal tick-DB dashboards (kdb), chat
color from other desks.

**AI layers → built evidence:**

| Layer | AI enhancement | Built |
|---|---|---|
| Baseline deviation | run-rate vs historical intraday profile; spread/vol z-scores | flow_forecast L1–L6 + re-forecast; agent9; market_structure drift |
| Regime → strategy | classify conditions, map regime to algo choice (the step vendors skip) | agent2 regimes + condition-adjusted algo ranking |
| Exception surfacing | one ranked queue across markets/lines | pt_dealer.attention_queue |
| Anomaly attribution | join volume anomaly to calendar: expiry / index event / earnings / macro | event radar + agent7 (join = small new tool) |
| Narrative compression | auto-drafted pre-open brief + condition-change notes | pt_automation pre-open pack (LLM improves prose; templates carry facts) |
| Predictive checkpoints | intraday EOD-volume re-forecast (DM-gated); live TW indicative auction for MOC sizing | flow_forecast gates; event_data auction parser (live-only) |

**Differentiated proposal — basket-conditioned monitor:** weight
liquidity/vol deterioration by the WORKING BASKET's remaining notional
per name ("spreads doubled in names covering 40% of your residual
sells"). Vendors monitor the market; the dealer needs the market
conditioned on his residuals. File-in (residuals CSV), public-data
buildable.

**Honest assessment:** the most automatable bullet (continuous
baselining beats human scanning), but also the best-vendor-covered —
credible new value only in the basket-weighted view, the regime→algo
link, and calendar attribution. And intraday real-time is where public
data is weakest: our demos are EOD/delayed replays; mechanism and
thresholds transfer, plumbing does not.

---

## Bullet 3 — "Optimize trade execution to minimize market impact, slippage, and transaction costs"

**The responsibility.** The loop: pre-trade cost estimate → strategy/
algo choice → in-flight adjustment → post-trade TCA → feed lessons back.
Desk tools: pre-trade impact models, algo suite + wheel, vendor TCA.

**Tools we can create (→ built):**

| Tool | What it does | Status |
|---|---|---|
| Predicted-vs-realized learning loop | every run logged, model error tracked, calibration drifts surfaced | BUILT (run library) |
| Condition-adjusted algo ranking | which algo wins in WHICH regime, with real statistics (Friedman + Nemenyi, not averages) | BUILT |
| IS attribution + markout curves | decompose slippage: timing vs impact vs spread vs venue toxicity | BUILT |
| Counterfactual impact propagator | "what would strategy B have cost" with sensitivity bands | BUILT |
| Crowding-adjusted event frontier | index-event strategy picks conditioned on measured positioning | BUILT (7i) |
| Slippage narrative generator | attribution table → plain-language "why we missed by 4bps" for the client note | NEW, small |
| Participation-cap optimizer | given constraints, solve the cap that balances impact vs completion risk | NEW |

**Realistic institutional benefit: methodology HIGH, numbers LOW.** Any
serious desk has better-calibrated impact models than ours — they have
proprietary fills, we have public prints. What desks often DON'T have:
a disciplined feedback loop (TCA reports that nobody reconciles against
pre-trade predictions) and honest algo-wheel statistics. The learning-
loop design and the ranking methodology transfer intact; our
coefficients do not. The event-execution layer (crowding, completion
clock) is the one place our numbers are competitive, because the data
is public there for everyone.

---

## Bullet 4 — "Coordinate cross-market execution seamlessly across multiple jurisdictions and time zones"

**The responsibility.** One basket, eight market microstructures:
staggered opens/closes/lunches, holidays and half-days, FX cutoffs,
different auction mechanics — sequenced so the basket stays balanced
and nothing misses a window.

**Tools we can create (→ built):**

| Tool | What it does | Status |
|---|---|---|
| Cross-market timeline | all sessions/auctions/cutoffs on one HKT clock | BUILT (pt_dealer) |
| Holiday/half-day collision detector | basket spans a TW typhoon closure or HK half-day → flagged at intake | BUILT partially (pt_ops holiday-aware); extend to intake-time warnings |
| Cascade run-sheet generator | per-basket printable day plan: market order, cutoffs, auction allocations | NEW (bullet-1 proposal) |
| Exposure-path scheduler | keep executed net within band of the structural path across time zones | BUILT (pt_ops, path-vs-structural design) |
| FX cutoff scheduler | funding legs vs custodian/CLS cutoffs per currency | NEW, calendar-based |
| Handover note generator | session state → structured note for follow-the-sun or next-day continuation | NEW, small |

**Realistic institutional benefit: MEDIUM-HIGH — and the best
effort-to-value ratio of the eight.** This is coordination logic:
deterministic, fact-based, fully public inputs (calendars, session
times, cutoffs). Desks handle it today with experience plus
spreadsheets; codifying it removes a whole class of missed-window
errors. Low integration barrier (file-in/file-out), no proprietary
data needed, and mistakes here are visible and costly — exactly where
cheap automation pays.

---

## Bullet 5 — "Stay updated on market-specific regulations, including short-selling rules, lot sizes, and circuit breakers"

**The responsibility.** Rules change: Korea's short-sell regime,
Taiwan intraday-short windows, lot-size reforms, HK severe-weather
trading, limit-band adjustments. Dealers learn via compliance memos,
exchange circulars, and pain.

**Tools we can create (→ built):**

| Tool | What it does | Status |
|---|---|---|
| Rules-as-code registry | limit bands, lot sizes, auction cutoffs, short-sell rules per market, versioned with effective dates | BUILT (pt_dealer tables + rules_version) |
| Regulatory-notice triage | fetch exchange notice feeds (public), classify by relevance (short-sell / lots / auctions / fees), draft the diff to the rules table — HUMAN approves the change | **BUILT (session 7l)**: agents/reg_watch.py + Page 5 — 3 live feeds (TWSE/JPX/NSE), multilingual keyword engine + LLM hook, versioned registry wired into pt_dealer; first live digest caught NSE's CAS introduction |
| Empirical rule-change detector | structure drift catches what circulars miss: a tick/lot regime change shows up in the spread/size distributions | BUILT (market_structure drift) |

**Realistic institutional benefit: HIGH for the triage tool.** Even
large desks do this with humans reading circulars across 10 exchanges
in 4 languages. LLM triage with human sign-off is safe (no client
data, no order flow, public inputs, human gate) and directly
time-saving. Caveat stated plainly: compliance owns the golden rules
copy — our registry is a dealer-side convenience mirror, never the
authority.

---

## Bullet 6 — "Ensure adherence to regulatory requirements across all Asia jurisdictions during trade execution and reporting"

**The responsibility.** Distinct from #5: not knowing the rules but
ENFORCING them in flight (short-marking, uptick rules, foreign
ownership, order-to-trade behavior) and meeting reporting obligations
(short-position disclosure thresholds, substantial-shareholder rules,
trade reporting).

**Tools we can create (→ built):**

| Tool | What it does | Status |
|---|---|---|
| Compliance pre-flight | per-jurisdiction checks before staging, with explain-why-blocked output | BUILT (pt_dealer) |
| Reporting-threshold tracker | positions vs disclosure thresholds per market, days-to-file countdown | NEW — needs holdings data; demo on synthetic |
| Self-surveillance pre-audit | our own participation/cancel patterns checked against surveillance-style rules before the exchange asks | NEW |

**Realistic institutional benefit: LOW direct, HIGH indirect — the
honest floor of this whole exercise.** Compliance enforcement is bank
infrastructure with zero tolerance for shadow tools; nothing a new
hire builds gets deployed here. The transferable value is knowing WHAT
the checks are (interview signal), the explain-why-blocked UX pattern,
and arriving able to READ the compliance stack rather than build it.

---

## Bullet 7 — "Maintain accurate trade records and documentation for audit readiness and transparency"

**The responsibility.** Systems log orders and fills automatically; the
human burden is DECISION documentation — why this strategy, why the
deviation, who acknowledged which alert — plus client instructions and
error logs, retrievable years later.

**Tools we can create (→ built):**

| Tool | What it does | Status |
|---|---|---|
| Documentation-as-by-product | every recommendation surface auto-writes rationale + inputs + rules_version; using the tool IS the record | BUILT (best-ex store, audit packs, alert-ack trail) — make universal (W5.14) |
| One-command audit pack | basket → zip: decisions, alerts+acks, versions, fills, client comms | BUILT partially; extend to full thread |
| Best-ex narrative generator | structured records → the narrative auditors read; human signs | NEW, LLM-assisted, safe (internal data, human gate) |

**Realistic institutional benefit: MEDIUM-HIGH, as a design principle.**
Banks have record-keeping systems; the genuine gap is decision-level
rationale, which today is memory and chat scroll-back. The
"by-product, not chore" design transfers to any stack and is the kind
of thing a desk actually adopts because it costs the dealer nothing.

---

## Bullet 8 — "Support post-trade processes, including settlement, reconciliation, and resolving operational discrepancies"

**The responsibility.** Mixed settlement cycles (India T+1; TW/KR/JP/HK
T+2; China's special regime), fails management, recon breaks
(price/qty/fees/FX), corporate-action complications. Ops owns the
process; the dealer resolves trade-side breaks.

**Tools we can create (→ built):**

| Tool | What it does | Status |
|---|---|---|
| Holiday-aware settlement calendar + FX notes | per-market value dates, mismatch warnings at intake | BUILT (pt_ops) |
| Recon break triage classifier | auto-sort breaks by likely cause so humans start at the hard ones | BUILT (pattern); desk version learns from THEIR resolution history |
| Corporate-action collision checker | ex-dates/splits inside the basket window flagged at intake | NEW — public data, small build |
| Fails-risk flag | SBL/borrow data → deletion names with squeeze/fail risk post-event | NEW — links our event-data layer to ops |

**Realistic institutional benefit: MEDIUM.** Break triage is a textbook
ML fit (repetitive, labeled outcomes, human confirms) but needs their
break history to train — ours demonstrates the pattern. The
corporate-action checker and settlement calendar are public-data
buildable and immediately usable. Fails-risk from borrow data is a
genuinely novel link (nobody's recon tool watches SBL unwinds).

---

## Summary — where the project realistically benefits institutional traders

| Rank | Tool / layer | Benefit | Why |
|---|---|---|---|
| 1 | Regulatory-notice triage (B5) | HIGH | public inputs, human gate, real daily pain, no vendor covers it well |
| 2 | Cross-market coordination suite (B4) | MEDIUM-HIGH | deterministic calendar logic, zero integration barrier, visible errors prevented |
| 3 | Basket-conditioned monitor (B2) | MEDIUM-HIGH | vendors watch the market, not YOUR residuals; file-in/file-out |
| 4 | Learning loops: run library + algo-wheel stats (B3) | MEDIUM-HIGH | methodology desks lack; transfers intact |
| 5 | Documentation-as-by-product (B7) | MEDIUM-HIGH | design principle, costs the dealer nothing |
| 6 | Intake suite: normalizer, linter, revision differ (B1) | MEDIUM | universal pain; adoption path = personal tool first |
| 7 | Index-event execution layer (B3) | MEDIUM (HIGH in event weeks) | the one place our DATA competes, not just our methods |
| 8 | Recon triage + CA checker (B8) | MEDIUM | pattern proven; training data is theirs |
| 9 | Compliance enforcement (B6) | LOW direct | bank infrastructure; knowledge signal only |

**The honest bottom line.** The project's institutional benefit is
real but takes a specific form: not "deploy this code," but (a) four
or five file-in/file-out utilities a desk could adopt with near-zero
risk, (b) proven mechanisms and honest statistics for the layers that
must be rebuilt on desk data, and (c) a hire who has already mapped
every workflow and knows where automation pays. Anything that claims
more than that — especially around real-time plumbing, impact-model
calibration, or compliance — would be selling. The interview version:
"here is where my tools would help your desk tomorrow, here is where
they're mechanism-demos that need your data, and here is where I'd use
yours and not mine."
