# AI Rebalance-Interest Monitor — Design (interview answer + implementation)

*Session 6l. The answer to: "build an AI-based tool to monitor interest in
index rebalance names ahead of the event, with a PT desk's tools (CLSA)."
Free-data core implemented in `agents/rebalance_monitor.py` + Page 2
expander; this doc is the full desk architecture.*

---

## 1. Frame the objective first (say this before any architecture)

"Interest" = who is accumulating ahead of the effective date — the
crowding that determines whether my client should pre-position, split, or
take the close. The output is a **daily ranked monitor with alerts**, not
a price forecast. That framing keeps the tool on the right side of the
agency line: it informs execution strategy, it is not an alpha signal we
trade against clients.

## 2. Data layers (what a CLSA-class desk actually has)

| Layer | Source | Cadence |
|---|---|---|
| Candidates | Rulebook screener (MSCI GMSR/buffers, FTSE ranks) — implemented | per review |
| Market data | Internal tick store (kdb+) → bars, auction prints, close-share | real-time |
| Official positioning | JP 0.2% shorts (daily), TW margin/SBL (daily), KR register, HK SFC weekly, FINRA | daily-weekly |
| Desk-internal | Own client flow by segment, PB securities-lending book, crossing interest/IOIs | real-time |
| Text | News, index-provider notices, sell-side research, (compliance-gated) client chat | streaming |
| History | Event library: every past event's features + realized outcome — implemented | per event |

## 3. Features (per candidate-day)

Implemented from bars anyone has: 5d/20d abnormal volume ratio; 10-day
price drift in units of own volatility (direction-signed); range
expansion; plus injectable feeds: short-balance delta (official regimes)
and news/chat mention count (NLP layer). Desk adds: close-auction share
shift, borrow utilization, own-flow imbalance by client type.

## 4. The AI layer — two stages, gated (the differentiating answer)

**Stage 1 — transparent composite.** Weighted score 0–100 with explicit
per-feature reasons. The dealer can challenge every number; day one it
works with zero training data.

**Stage 2 — learned weights.** Ridge regression on the event library
(features at T−k → realized event-day volume multiple), chronological
split, and the house rule: learned weights ship **only** if they beat the
static composite — given the *same* calibration freedom — on test MAE
with a DM gate at p<0.10. Otherwise static ships and the tool says so.
Implemented and tested both ways: on a synthetic library where the true
drivers differ from the static weights, the model learns them (news 0.46
vs static 0.10) and passes the gate; on noise, the gate ships static.

**NLP extension (desk):** LLM classification of news/notices/chat into
per-name mention counts and stance — feeding the `news` feature, not
replacing the score. Chat data is compliance-gated; client-identifying
information never enters the model. Label upgrades: realized close
dislocation and post-event reversal, both already measured by the event
study, so every completed event enriches the training set automatically.

## 5. Surface + governance

Daily ranked monitor (HOT/WARM/quiet) → transition alerts that fire once
per escalation (cockpit pattern, no re-paging) → acknowledgments into the
audit log with the rules/model version. Model governance: versioned
weights, the gate report stored with each version, quarterly re-fit
aligned to the QBR cycle. Information barriers: the tool reads aggregated
flow, never client-attributable positions; output informs client
execution advice, not prop positioning.

## 6. The 30-second interview version

"Candidates come from the rulebook screener. Each name gets a daily
interest score from features in three buckets — tape (abnormal volume,
drift, range), official positioning (Asia's short-disclosure regimes are
excellent — Taiwan daily SBL, Japan same-day 0.2% positions), and text
(NLP mention counts from news and notices). The score starts as a
transparent weighted composite the desk can challenge; the AI part is
learning the weights from our own event library — and the learned model
only ships if it beats the transparent baseline under a Diebold-Mariano
gate. Surface is a ranked monitor with fire-once escalation alerts that
land in the audit trail. I've built the full loop in my project on free
data: screener → features → gated learning → monitor → alerts — the desk
version swaps in the tick store, the lending book, and a compliance-gated
chat NLP layer."
