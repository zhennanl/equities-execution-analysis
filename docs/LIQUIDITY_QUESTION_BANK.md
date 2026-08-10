# The Liquidity Question Bank (c-134)

Self-generated questions on rebalance-window liquidity, written
from the index-strategist seat. Each carries WHY it matters and
its data status: [NOW] = answerable from current holdings,
[NEEDS: x] = requires the named acquisition. This bank is the
work queue for future autonomous sessions — questions get
answered in batches and their results appended to the
PERSONA_PLAYBOOK.

## A. Where does the liquidity actually come from?

Q1. On the effective day, whose selling absorbs the tracker's
buying in an add — arbs unwinding (foreign sellers who were
earlier buyers), domestic institutions, retail, or short
sellers initiating? Decompose effective-day volume by t86
counterparty classes + margin/short deltas. The answer defines
who the desk should be calling for the other side. [NOW]

Q2. What fraction of window volume in an add is NEW money vs
recycling — i.e., do the same shares turn over repeatedly
(day-trade churn) or does ownership genuinely migrate? Compare
cumulative |foreign net| against gross volume; high ratio =
migration, low = churn. Migration windows should revert less.
[NOW — daytrade_history sharpens it]

Q3. When an add and a large deletion share the same effective
day, does money visibly rotate between them (the natural
cross)? Correlate same-day foreign net of adds vs dels within
events. If rotation is real, the desk's crossing pitch has
data behind it. [NOW]

Q4. Is there measurable liquidity provision from the FUTURES
side — does TAIFEX single-stock-futures OI in the mover expand
during the window (synthetic positioning that never touches
the borrow market)? [NEEDS: taifex SSF OI series]

Q5. Do ETF creations in EWT/local trackers cluster on the
effective day or leak in earlier? The direct read of whether
"tracker demand at the close" is even true for the modern
structure. [NEEDS: etf_flows AJAX id]

## B. Timing: when inside the window does liquidity appear?

Q6. What does the daily-volume PROFILE of the window look like
— U-shaped (day-1 spike, dead middle, effective spike) or
monotone build? The middle-of-window liquidity hole, if it
exists, is where a client's early order pays the most impact.
[NOW]

Q7. Is E−1 systematically the second-most-liquid day (arbs
pre-positioning their exit), and does a WEAK E−1 volume
predict a violent effective close? [NOW]

Q8. Does liquidity ARRIVE EARLIER in recent eras — is the
whole event compressing toward the announcement as the trade
crowds? Compare volume-profile centroids by era. If yes, every
timing rule learned on 2015-2019 is slowly going stale. [NOW]

Q9. How much of effective-day volume prints IN the closing
auction vs continuous trading, per name — and has that share
grown since Taiwan's 2020 auction reform? [NEEDS: per-stock
close-auction volume history — the highest-value single
acquisition in this bank]

Q10. After the effective close, how many days until the name's
volume renormalizes to its pre-event ADV? The "hangover
length" tells opportunistic clients how long the exit door
stays open. [NOW]

## C. Name-level liquidity stress

Q11. For each historical add, what was demand-to-daily-float
turnover (expected tracker shares / free-float shares traded
daily), and is THAT ratio — rather than ADV multiples — the
better predictor of drift and dislocation? [NOW, floats from
weights inversion]

Q12. Do names with high retail ownership (TDCC small-bracket
share) behave differently as adds — more day-1 pop, less
persistent drift — than institutionally-held names? [NOW —
tdcc weekly brackets]

Q13. Is there a liquidity CLIFF: a demand/ADV threshold above
which impact stops being linear (the elasticity kink)? Fit
piecewise drift-vs-demand; the kink is the desk's capacity
warning line. [NOW, rough demand; better after AUM fit]

Q14. Do LOW-PRICE (penny-ish) adds — where retail lot-size
effects bite — show systematically different microstructure
than high-price adds? [NOW]

## D. The borrow market as a liquidity system

Q15. What is the borrow-market CAPACITY constraint on the del
trade: at what fraction of SBL supply does the borrow build
stall (shorts wanted to add but could not)? Stalls should
predict weaker downside drift — the trade was supply-capped,
not conviction-capped. [NOW — sbl balance vs limit fields]

Q16. After the effective day, how fast does the borrow UNWIND,
and does slow unwinding (stubborn shorts) predict continued
weakness vs fast unwinding predicting the bounce? [NOW]

Q17. Do margin-account shorts (retail) and SBL shorts
(institutional) take OPPOSITE sides at any point in the window
— and who wins? The retail-vs-institutional short battle is
directly measurable in Taiwan and nowhere else in APAC. [NOW]

Q18. Is there a detectable RECALL squeeze in dels that later
bounce: borrow falling while price still falls (forced covers
into weakness) vs borrow falling as price bounces (voluntary
profit-taking)? The sign of that correlation, name by name, is
the squeeze early-warning. [NOW]

## E. Spillovers and neighbors

Q19. When a name is added, do its CLOSEST PEERS (same sector,
correlated) show abnormal volume/flow the same days — sympathy
liquidity — and does fading the peer (which has no index flow)
capture the sentiment component cleanly? [NOW]

Q20. Does the DELETED name's sector absorb rotation from the
deletion (peers up on the del's flow days)? [NOW]

Q21. For dual-line names (TSM ADR premium as the proxy), does
the rebalance window distort the cross-listing spread — and is
that spread a cleaner crowding gauge than any single-line
indicator? [NEEDS: ADR series — one Yahoo call]

Q22. Do index-review windows measurably drain liquidity from
the REST of the market (market-wide volume ex-movers dips on
effective day as attention concentrates)? If so, unrelated
client orders should avoid effective days entirely — a
non-obvious, immediately actionable desk rule. [NOW]

## F. Feedback and information content

Q23. Does day-1..3 flow predict day-4+ FLOW (not just return)
— is there flow momentum, i.e., do institutions split orders
across the window so early footprints forecast later ones?
[NOW]

Q24. Is the SPEED of the borrow build (shares/day) more
informative than its level — fast builds = informed conviction,
slow grinds = passive hedging? [NOW]

Q25. When our own PREDICTION was consensus-obvious (deep
below-floor names) vs surprise (count-driven sweeps), do the
windows differ — is the surprise premium measurable? Join the
engine's ex-ante conviction to window outcomes. The direct
monetization test of the prediction engine. [NOW — the
marquee join of the two project halves]

Q26. Do REVERSED predictions (names the market expected but
MSCI skipped) show negative windows — the unwind of wrong
pre-positioning? Needs the market-consensus proxy: pre-ann
drift on non-events from the audit's false-alarm ledger. [NOW]

## G. Regime and structure over time

Q27. Has effective-day volume-multiple GROWN over eras (more
passive AUM) while drift SHRANK (more arb capital) — the
scissors that defines where this trade is going? [NOW]

Q28. Did Taiwan's March-2020 intraday-auction reform visibly
change window microstructure (day-1 gaps, effective-day
prints)? Split eras at the reform. [NOW]

Q29. Do NOVEMBER (formerly SAIR) windows still behave
differently from the other quarters even after the 2023 QCIR
unification — habit persistence in the arb community? [NOW]

Q30. Is there a TAIEX-VOLATILITY conditioning: in high-vol
regimes, does the same demand produce MORE dislocation
(risk-limited arbs) — the vol-scaled elasticity? [NOW]

## H. The desk's own mechanics

Q31. If a tracker splits its order x% early / (1−x)% at close,
what x minimized realized cost per historical window —
computed as an actual backtest over x, not a median argument?
Produces THE client table. [NOW]

Q32. For an agency desk crossing an add-buyer with an arb
seller at E−1: what discount to the close does the arb
historically accept (E−1 close vs E close spread distribution)
— the fair price of a guaranteed cross? [NOW]

Q33. What is the worst-case (p95) effective-day slippage a
tracker suffered per demand bucket — the number that sizes the
desk's risk disclosure, since clients remember tails, not
medians? [NOW]

Q34. On multi-name reviews, should a tracker STAGGER
executions across names (liquidity is name-specific) or does
same-day correlation of dislocations make diversification
illusory? Cross-name effective-day correlation per event.
[NOW]

## Working rules for answering

Batch by data status; NOW-questions first (24 of 34).
Every answer: n, era-split, and the honesty label. Negative
results ship. Each batch appends to PERSONA_PLAYBOOK and this
file gets its statuses updated — the bank is a living queue.
