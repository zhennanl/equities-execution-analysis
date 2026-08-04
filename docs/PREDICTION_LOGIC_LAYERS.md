# The Prediction Logic, Layer by Layer — How Every Call Is Formed

*Session 8u. The complete decomposition of the index-review
prediction engine. Every layer lists: the RULE, its INPUT, its
ORIGIN (which mistake or graded run built it — nothing here was
designed in an armchair), and its FAILURE MODE (what it still gets
wrong, honestly). Layers execute in order; a name must survive
every gate above it to become a call.*

---

## L0 — Universe construction (count-anchored)

**Rule:** the market's investable ladder = real named securities
(caps, floats, ADV) + synthetic tail names, with TOTAL membership
pinned to the provider's PUBLISHED constituent count. The tail fills
the unobserved middle so the coverage boundary lands where the real
index's size puts it.
**Input:** real-name data (official quotes x share counts, or PIT
price reconstruction); published constituent counts (factsheets).
**Origin:** iteration 4 of the all-Asia May replication — guessing
tail cutoffs (iteration 2) REGRESSED two markets; count-anchoring
took the run from 55% -> 65% in one step.
**Failure mode:** universe BREADTH — changes below the real-name
floor are invisible (Aug/Nov-2025: 2395, 8033 ungradable). Fix is
data (more share counts), not rules.

## L1 — Eligibility screens

**Rule:** minimum free float 0.15; real ATVR (annualized traded
value / float cap) liquidity floor; A-shares carry the 20% inclusion
factor in MEMBER RANKING ONLY (it sets weight, never eligibility).
**Input:** float estimates, real volumes.
**Origin:** the placeholder atvr=1.0 silently disabled the liquidity
screen for two iterations (caught, fixed — real volumes activated
it); the inclusion-factor scope error broke A-share adds 8->4 before
being corrected to ranking-only.
**Failure mode:** float VINTAGE (third-party, current-dated) and
provider FIF discretion (Indonesia deletions at floats 0.20-0.29 —
structurally invisible; the pre-declared 0.20 watch line does NOT
move to catch them).

## L2 — The ladder and the GMSR

**Rule:** sort eligible names by full cap; walk down accumulating
FREE-FLOAT cap until 85% cumulative coverage — the last cap in is
the GMSR ("the magic line"). Every threshold is a multiple of it.
**Input:** L0's universe after L1's screens.
**Origin:** direct GIMI methodology replication; validated by 17/17
adds at PIT across 8 markets.
**Failure mode:** dual-line splits (whole-company cap assigned to
one H-line: 0177/2799 misses — fixable with per-line shares).

## L3 — The thresholds

**Rule:** ADD: non-member full cap >= 1.15x GMSR (SAIR) or 1.8x
(QIR), AND float-cap sanity vs the add threshold. DELETE FLOOR:
member < 0.5x GMSR. WATCH bands at +-15%.
**Input:** L2's GMSR.
**Origin:** provider methodology; the QIR-vs-SAIR multiple split is
why the Aug pack's zero adds is credible (1.8x is a high bar).
**Failure mode:** price moves between vintage and announcement
(Rainbow Robotics class — float-blocked adds are watch-listed, not
called).

## L4 — The review-cadence rule (NEW, backtest iteration 4)

**Rule:** the deep country-coverage MIGRATION sweep (members beyond
85%+2% cumulative coverage -> Standard->SmallCap deletion) runs at
SAIRs ONLY. QIRs execute extreme breaches only (the 0.5x floor and
screen failures).
**Input:** review type.
**Origin:** the 2025 backtest — applying migration at the Aug-2025
QIR vintage produced 10 false deletions; with the cadence rule, 0.
Cross-checked: the Feb-26 QIR's real deletions were all sub-floor
(Feng Tay 0.38x), consistent.
**Failure mode:** none observed yet; graded on two QIRs.

## L5 — Churn buffers

**Rule:** names DELETED at the immediately preceding review are
excluded from add candidacy; names ADDED are excluded from deletion
candidacy — the provider does not reverse itself on unchanged
fundamentals.
**Input:** the prior review's official change list.
**Origin:** the Aug-2026 Asia pack's first run "re-added" Nestlé
Malaysia and "re-deleted" China's May adds — 18 spurious flags
silenced.
**Failure mode:** genuine quick reversals (rare; none observed).

## L6 — Corporate-action & fast-entry radar

**Rule:** a member under publicly announced takeover/privatization
before the review -> deletion call regardless of size; large new
listings -> fast-entry ADD candidates outside the size ladder.
**Input:** Reg-Watch circulars (LLM-extracted, human-gated);
new-listing detection (a name with volume history < baseline window
is a listing, not a data error).
**Origin:** Toyota Industries — unfetchable by caps, public by
tender announcement; 7769 in the Nov-25 backtest (new-listing print)
confirmed the fast-entry class needs its own detector.
**Failure mode:** notice coverage (8/12 feeds anti-bot from sandbox;
desk feeds close it).

## L7 — The membership verification gate (the Feng Tay rule)

**Rule:** NO CALL SHIPS ON UNVERIFIED MEMBERSHIP. Membership is
replayed from official change-list ledgers through a state machine;
STALE_MEMBER / STALE_NONMEMBER are blocking violations; an empty
alias map counts as UNVERIFIED (not as "no problems found");
unverified calls that ship anyway carry a x0.75 probability
discount. Markets without validated universes get NO-CALL, never a
fabricated list.
**Input:** official change lists, alias maps, fund-holdings
baselines where available.
**Origin:** the two worst errors the project ever made — the Feng
Tay DELETE call on a name deleted two reviews earlier, and the
AI-quartet ADD calls on names that were already members. Both were
membership-state errors, not rule errors; when this engine is wrong
it is almost never the tape measure, it is the list of kids.
**Failure mode:** ledgers replay deltas but cannot establish base
state — the residual gap holdings files close.

## L8 — The probability layer

**Rule:** every call carries a Laplace-shrunk probability from the
GRADED record: HIGH-margin adds ~85%; verified deletes ~80%;
unverified x0.75; cutline residents 45-60%. Never gut feel, never
round numbers chosen for confidence.
**Input:** the case-study library's hit/miss counts.
**Origin:** the user's requirement that predictions be honest
probabilistic tags, not confident lists — the differentiation the
pitch is built on.
**Failure mode:** small n (being fixed by the retrospective sweep).

## L9 — Deletion output as a HAZARD, not a date (NEW, backtest)

**Rule:** a coverage breach is a hazard-ranked WATCH ZONE entry, not
a dated call: MSCI batches boundary cleanups. Measured on the
Nov-2025 flag cohort: ~2/3 of flagged members converted at the next
SAIR; ~1/3 are persistent cutline residents (the same three names
every run flags).
**Input:** L2-L4 breach flags tracked across consecutive reviews.
**Origin:** the 2025 backtest's central finding — the Nov "false
positives" were EARLY, not wrong; 6 of 9 became May deletions.
**Failure mode:** the conversion rate is measured on one cohort so
far; the 2015 sweep grows it.

---

## The shape of the whole

Layers L0-L4 are the PROVIDER'S arithmetic, replicated. L5-L6 are
the provider's BEHAVIOR, learned from graded mistakes. L7 is
self-protection against our own data. L8-L9 are the honest
packaging that turns rule output into a product a desk can defend:
probabilities from a public record, hazards instead of false
precision. Every layer exists because something specific went wrong
without it — the engine is its own error history, compiled.
