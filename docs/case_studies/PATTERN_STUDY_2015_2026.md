# Pattern Study — Window Features vs Effective-Date Outcomes, 2015–2026

*Session 9i (2026-08-05, autopilot). 133 name-events (77 deletions
/ 56 additions, 31 events) — features frozen at T-1, outcomes on
and after the effective date. Methods: Spearman correlations with
EVENT-CLUSTERED permutation p-values (2,000 block permutations),
quartile contrasts, depth-2 trees with leave-one-EVENT-out
cross-validation. Data: data/pattern_study_tw.json. EXPLORATORY —
registered, not adopted, except where replicating adopted
results.*

## Finding 1 — REPLICATED: positioning predicts the PRINT'S SIZE

Completion → effective-day volume multiple: rho +0.347,
clustered permutation p = 0.002 (the only significant test of
nine), quartile spread 13.0× → 28.5×. Second independent method
confirming the adopted volume forecaster: how much the market
pre-positions tells you how BIG the close will be.

## Finding 2 — THE HONEST NULL: mean returns at the print are unpredictable from daily window features

Every test of window features against the effective-day RETURN
or the T+3 move came back null: foreign flow (rho +0.06,
p=0.73), completion (−0.08, p=0.51), window drift (+0.08,
p=0.66), volatility shift (−0.06, p=0.76); quartile spreads all
under 2.5 percentage points. The machine-learning pass makes the
null decisive: leave-one-event-out sign prediction scored
0.52–0.56 against a 0.66 base rate — BELOW always-guessing the
majority class. The hypothesized pattern class ("stocks with
heavy window positioning decline significantly more at the
print, on average") DOES NOT EXIST in this data at the mean.

**The economic reading, which is the real lesson:** rebalance
flow is the most anticipated flow in markets, and the price at
the print is — on average — efficiently arbitraged. The window
tells you the SIZE of the event (finding 1), not the direction
of the print. Where returns ARE predictable, our earlier graded
work shows the edge lives in TAILS and STRUCTURE, not means:
the compound squeeze signature (H16 — 17.8% mean vs 4.6% base,
n=2), the microstructure toll cells (the gap lands against the
obligated side), and the post-print reversal path — none of
which a mean-regression on daily features can see.

## Finding 3 — registered weak signal (H17, NOT adopted)

Foreign-outflow intensity vs the T+3 bounce (deletions): rho
−0.200, p=0.21, quartile spread −2.3pp — directionally "the
harder foreigners sold the window, the bigger the post-print
bounce" (the H16 family's continuous cousin). Registered as H17
in the variable-lab registry v4: ADOPT if |rho| ≥ 0.25 with
clustered p ≤ 0.05 as events accumulate; graded from Aug-2026.

## The borrow-rate hypothesis — honestly deferred

Securities-lending HISTORY exists in our caches only from
April-2026, so "high borrow in the window → bigger decline"
is testable today on a single cross-section (May-26, n=7 — where
the v2 regrade showed standing-borrow names printing CLEAN, the
opposite of the hypothesis, on an anecdote's worth of data).
The capture-forward SBL archive and a margin-short historical
proxy fetch are the two paths to a real test; both queued.

## What this changes in practice

Nothing gets un-built and one temptation gets blocked: the
pinned null forbids future versions from claiming mean-return
predictability off daily window features without beating this
study's clustered bar. The desk story is unchanged and now
better-founded: predict the SIZE (adopted, twice-confirmed),
respect the efficiency of the average print, harvest the tails
(H16/H17) and the structure (tolls, reversals) — and say so to
clients in exactly those words.
