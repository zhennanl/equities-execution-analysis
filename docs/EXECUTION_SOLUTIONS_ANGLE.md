# The Execution Solutions Angle — Mapping the Platform to an APAC ES Role

*2026-07-08. The interviewer's role: execution advisory & solutions coverage
for APAC electronic trading — (1) improving algo-performance RANKINGS for a
diverse client base, (2) deep-dive TCA, algo customization, APAC
microstructure color, (3) algo product evolution via spec proposals + data
analysis. This doc maps each responsibility to the platform, names the
enhancements built for the meeting, and scripts the demo path.*

---

## 1. Bullet 1 — "Improving ranking of algo performance"

**Her reality:** clients run algo wheels; brokers live and die by their rank.
The structural unfairness of raw wheel rankings is that the broker who
receives the hardest flow (biggest orders, worst conditions, most urgent
mandates) ranks worst even with the best engine. The ES job is (a) proving
that with data, and (b) fixing the engine where the underperformance is real.

**What the platform had:** an N-arm wheel (Friedman + Nemenyi league table)
and A/B-with-controls in the fitted cost model.

**Built for this meeting — `condition_adjusted_ranking` (agents/algo_wheel.py):**
raw rank vs condition-adjusted rank side by side, adjustment inherited from
the cost-model regression (strategy dummies holding size, volatility,
participation, spread fixed), with Δ-rank movers named and dummy-t
separability at 5%. Pinned by a test in which the better engine receives
systematically harder flow: raw rank last, adjusted rank first — the exact
ranking-defense conversation, reproduced synthetically. UI: Cost Model
section, "Condition-Adjusted Ranking — the wheel-defense view."

**The line for the room:** "Raw wheel rankings measure the flow you were
given as much as the engine you built. This view separates the two — it's
the number I'd bring to a client whose wheel demoted us after a quarter of
oversized orders, and equally the number that tells our own desk when the
underperformance is real and a spec change is owed."

## 2. Bullet 2 — Deep-dive TCA, algo customization, APAC microstructure color

**Deep-dive TCA (already at depth):** Perold IS attribution reconciling
±0.1bp with modeled impact honestly held out as a memo; markout curves;
reversion + permanent/temporary split; multi-benchmark tables; percentile vs
own history; predicted-vs-realized tracked by the run library.

**Algo customization (framing + existing hooks):** the order ticket IS the
customization surface (urgency→participation mapping, caps, windows, limit
behavior, auction gating); Agent 14's S2/S3 fractions are strategy
parameterization; the conditional playbook renders a client-specific
parameter recommendation with displayed evidence. The natural extension
(spec'd, not built): a "customization memo" generator — client profile
(benchmark, urgency mix, order-size distribution) → recommended parameter
set → evidence pack.

**APAC microstructure color (the differentiator vs US-centric candidates):**
15 markets with lunch sessions, price-limit bands (CN/KR/TW/VN/TH/ID),
closing-auction mechanics (HK CAS, VN ATC), board lots and odd-lot
handling, short-sale regimes (China-A margin-list reality, Korea's Mar-2025
resumption rules, TW SBL quotas), T+n settlement, circuit-breaker
structures — plus the Taiwan limit-up empirical work (2×4 lock/retreat
taxonomy, T+1 continuation, threshold detection) from the original project,
with the limit-up hazard surface as the named next build.

## 3. Bullet 3 — Algo product evolution (spec proposals + data analysis)

**The platform is itself the artifact type she ships:** the gap register and
design docs are spec proposals with evidence sections; the cost model and
wheel are the data-analysis engines that justify them. **Worked example to
cite in the room:** "Auction-aware POV for price-limit markets" — spec: POV
that reads the live volume re-forecast, detects limit-approach via the
hazard thresholds, and shifts residual size to the next session's auction
when lock probability spikes; evidence base: the TWSE limit study + the
platform's auction-concentration and volume-re-forecast analytics; success
metric: avoided worst-decile prints on limit-band names, measured by the
same IS attribution that would ship with it.

## 4. Demo path for the meeting (10 minutes)

1. Page 1 on a Taiwan name: verdict banner → wheel league table → **the
   condition-adjusted ranking** (the centerpiece — say the wheel-defense
   line). [4 min]
2. IS attribution waterfall + markouts ("this is the deep-dive TCA
   conversation, reconciled to a tenth of a bp"). [2 min]
3. Page 3 session board + regulation reference ("the APAC color, encoded and
   testable"). [1.5 min]
4. Page 2 VEDL: crowding score + expected-move + playbook ("advisory output
   a salesperson can hand a client"). [2.5 min]

**Anticipated pushbacks:** "Your panel is simulated" → the regression spec
is identical on client fills; simulation is what makes the ranking test
reproducible here. "Adjusted rankings can be gamed by control choice" →
controls are the four standard cost drivers, disclosed, with R²/n/SEs on
screen; the honest answer is you show BOTH ranks, never only the adjusted.
