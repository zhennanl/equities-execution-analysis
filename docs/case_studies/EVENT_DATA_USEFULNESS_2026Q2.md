# How Useful Is Each Public Dataset? — Graded on the Most Recent MSCI & FTSE Rebalances

*Session 7h. Implements the priority queue of
EVENT_POSITIONING_DATA_BY_PHASE.md (new module `agents/event_data.py`,
7 tests; chunked cached fetch `scripts/fetch_event_data.py` →
`data/event_data_cache.json`, 44 trading days Apr 27–Jun 30 2026,
18 names) and grades each dataset against the two most recent completed
reviews: **MSCI May 2026 SAIR** (Taiwan deletions, ann May 12 →
eff May 29) and **FTSE TWSE Taiwan 50 June 2026** (ann Jun 5 →
eff Jun 18). Controls = the false-flagged survivors from our own
backtests (TaiwanCement, FCFC, WanHai) + TSMC.*

## What was implemented

| Dataset | Function | Status |
|---|---|---|
| TWSE short balances (margin 融券 + SBL 借券賣出), daily, per stock | `fetch_twse_short_balance` / `phase_deltas` | IMPLEMENTED, 44 days cached |
| TWSE block-trade tape | `fetch_twse_block_trades` / `block_prints` | IMPLEMENTED, 44 days cached |
| TDCC weekly shareholding distribution | `fetch_tdcc_distribution` / `tdcc_concentration` | IMPLEMENTED — **latest-week snapshot only** (open data serves one week; the archive must be built forward by scheduled fetches) |
| TWSE indicative closing auction (13:25–13:30 simulated price/vol) | `parse_auction_snapshot` | PARSER ONLY — live feed, no historical archive exists, so it cannot be graded on past events |
| ETF units outstanding / futures basis & OI | — | PROTOCOL (no stable free API from sandbox; desk sources named in `EVENT_DATA_COVERAGE`) |

## Result 1 — Pre-announcement short build: a CROWDING gauge, not a truth signal

Total-short change over the ~2 weeks before each announcement
(% of window-start balance; base sizes vary hugely — GUC's base is
0.8M sh vs Compal's 441M — so percentages, not levels, and read with
that caveat):

| Name | Outcome | Pre-ann build |
|---|---|---|
| China Steel | TW50 delete | **+85%** |
| Hotai | TW50 delete | +12% |
| Formosa Plastics | TW50 delete | +10% |
| Compermed | TW50 delete | −12% (borrow-constrained special) |
| **TaiwanCement** | **NOT deleted (false-flag control)** | **+52%** |
| 5 MSCI-TW deletes | deleted | **−6% to +3% (flat)** |

Two honest findings. **(a) FTSE:** shorts built hard into the
*consensus candidate list* — including TaiwanCement, which was NOT
deleted. So pre-announcement short build predicts what the street
expects, not what the provider does; its execution value is as a
**crowding gauge** (a heavily pre-shorted candidate has less T-day
pressure left), not as a prediction improvement. **(b) MSCI:** deletes
showed NO pre-announcement short build even though prices front-ran
−4.3% (the 7d finding) — the MSCI front-running was **long-seller
driven** (foreign holders reducing), invisible in short data. Provider
asymmetry again, now on a third dataset.

## Result 2 — A→T trajectory: SBL decomposes the within-foreign netting (the 7e fix, delivered)

A→T short build in deletes is **SBL-led, not margin-led** (institutional,
not retail): THSR +12.7M sh SBL vs ~0 margin; China Steel +80M sh SBL vs
−10k margin. And the THSR daily overlay against T86 foreign nets does
exactly what session 7e wanted:

| Late A→T window (THSR) | Foreign net/day | New SBL shorts/day |
|---|---|---|
| May 25–28 | −9 to −14M sh | +1.3 to +2.2M sh |

→ Of the foreign selling into T, **only ~15–20% was new shorting; ~80%
was long selling** (trackers + long arb). The within-foreign netting
limitation is no longer a limitation — it's a measured split.

## Result 3 — Post-T unwind: the cleanest signal in the whole study (9/9)

| Group | Post-T total-short change |
|---|---|
| 5 MSCI-TW deletes | **−57% to −84%** |
| 4 TW50 deletes | −12% to −66% |
| Controls | mixed (+24%, +3%, −13%, −76% FCFC*) |

Every deletion unwound, hard. This is (a) ex-post proof the arb crowd
was there, (b) the **timing clock for S3's completion leg** — sell the
bounce while borrow is still being returned. And a settlement-mechanics
gem: THSR's SBL cliff came at **T+2** (Jun 2: −26.9M sh returned with
foreign net ≈ 0) — arbs covered ON the T print and the ledger shows it
two days later, exactly on the settlement cycle. (*FCFC control unwound
too — Formosa-group co-movement; noted, not explained away.)

## Result 4 — Block tape: thin in single names, but a backdoor ETF-creation proxy

Event names printed almost nothing in blocks during their windows
(0–2 prints, ≤NT$0.7B — these events cleared on-exchange). But **0050
itself printed NT$50B of paired-trade blocks in the 10-day TW50
window** — in-kind creation/redemption baskets crossing the tape. The
block tape thus partially substitutes for the protocol-status ETF-units
feed: primary-market ETF activity is visible here for free.

## Result 5 — TDCC & auction feed: forward tools, honestly labeled

TDCC snapshot (Jul 17) works end-to-end (China Steel large-holder 51.7%,
THSR 86.4%) but cannot be graded on May/June events — one snapshot, no
history. Same for the indicative auction. Both are **wired for the
Aug 12 QIR**, not for backtests. No usefulness claim is made for them
beyond pipeline-proven.

## Usefulness scorecard (for predicting changes / executing them)

| Dataset | Predict the change? | Execute the trade? |
|---|---|---|
| Short balances pre-ann | **LOW–MED** — tracks consensus incl. its errors (FTSE); blind for MSCI | MED — crowding gauge |
| SBL A→T trajectory | n/a (change already known) | **HIGH** — sizes the arb crowd, splits foreign flow |
| Short unwind post-T | n/a | **HIGH** — 9/9, S3 completion clock, T+2 settlement signature |
| Block tape | LOW (these events) | MED — via 0050 creation proxy |
| TDCC weekly | untested (no history) | forward tool, archive starts now |
| Indicative auction | n/a | live-only; cockpit integration designed |

**Bottom line for the desk:** these data don't improve *prediction* much
— our rules engine plus universe quality still carry that. They
transform *execution*: the SBL ledger tells you how crowded the trade
is before T, splits arb from tracker inside the foreign bucket, and
times the post-T completion leg. The one standing attribution
limitation from 7e is closed.

*Method notes: all percentages relative to window-start balances;
Taiwan only (Korea short balances = next fetcher, same pattern);
scheduled forward fetches of TDCC + TWT93U start the archive that makes
Phase-0 tests properly testable at the Aug 12 QIR — which remains the
pre-registered live test.*

---

## Addendum (session 7i) — the findings, converted into machinery

Each 7h finding now has a function, a test, and a real-data
demonstration. New code: improvement layer in `agents/event_data.py`
(+8 tests, suite 347), crowding hook in
`agents/index_flow.recommend_execution`, `forward` archive mode in
`scripts/fetch_event_data.py`.

### Prediction improvements

**1. Crowding overlay (`crowding_overlay`) — model call x street
positioning.** Cross-classifies every candidate into CONSENSUS /
UNPRICED / STREET-ONLY. Run on the REAL June TW50 review with our own
round-2 model flags:

| Ticker | Our flag | Pre-ann build | Read | Outcome |
|---|---|---|---|---|
| 2002 China Steel | NO | **+85%** | **STREET-ONLY: re-check** | **deleted — our miss, catchable ex ante** |
| 1101 TaiwanCem | yes | +52% | CONSENSUS | not deleted (shared false flag) |
| 6919 / 1326 / 2615 | yes | −12/−20/−22% | UNPRICED | mixed |

The STREET-ONLY cell is the payoff: our round-2 backtest missed China
Steel, and the short ledger was screaming +85% BEFORE the announcement.
The overlay turns the street's positioning into a free second opinion on
our universe file — exactly where all our deletion misses have come
from. (One event, in-sample observation; mechanism stated, Aug 12 is
the live test.) MSCI overlay: all five deletes UNPRICED — consistent
with 7h finding (b): short data is structurally blind on MSCI, so the
overlay is a FTSE-family tool.

**2. Drift composition (`drift_composition`) — the MSCI tell,
formalized.** New-shorts vs long-selling split of A→T foreign flow:
THSR 0.19, AsiaCem 0.19, ChinaAir 0.00 — all LONG_SELLER_LED, and
Compal's guard fired correctly (foreign was net BUYING its delete —
flagged unavailable, not mislabeled). Feeds the provider-asymmetry into
`refined_rule`'s drift input with WHO attached.

### Execution improvements

**3. Crowding-adjusted strategy frontier.**
`recommend_execution(..., crowding={ticker: band})` reruns the
S1–S4 frontier on a crowding-adjusted path
(HIGH: pressure ×0.6, reversal 0.65 — v1 heuristics in
`CROWDING_PATH_ADJ`, marked for event-library calibration). Real
effect at 7.3 ADV-days:

| Side | Baseline pick | HIGH-crowding pick |
|---|---|---|
| Buy | S3 post-effective (541 bps) | **S2 pre-position (338 bps)** — pressure part-spent, pre-positioning now optimal within tolerance |
| Sell | S1 MOC (−259 bps) | S1 holds, but its edge collapses to −64 bps while S3 = −149 → the case for negotiating tracking flexibility (to capture the covering bounce) triples |

Locked by `test_crowding_flips_buy_strategy`.

**4. Completion clock (`completion_clock`) — the S3 leg timer.** Judges
only after T+2 (the THSR settlement signature is now a coded guard).
Real dispersion as-of Jun 30: China Steel **UNWINDING (0.64)** — keep
selling into the covering bid — vs Formosa/Hotai MOSTLY_DONE. The
MSCI names finished long ago. This is a daily-updatable timer, not a
one-off study.

**5. ETF creation proxy (`etf_creation_proxy`)** — 0050 paired blocks
as the free primary-market gauge (NT$50B in the June window), marking
tracker AUM to market until the issuer-units feed (PROTOCOL) exists.

### Infrastructure

**6. `fetch_event_data.py forward`** — daily append of short/block data
+ date-keyed TDCC weekly archive. Started today; by Aug 12 the Phase-0
crowding test runs on a real pre-announcement archive instead of a
reconstruction. The QIR pre-registration now includes the overlay
output alongside the prediction commit.

### Honest boundaries

CROWDING_PATH_ADJ multipliers are v1 heuristics shaped by two graded
events, not fitted parameters; the China Steel catch is one event
(the mechanism — universe errors are visible in street positioning —
is the claim, not a hit rate); crowding bands use %-of-base thresholds
that are noisy on small bases (GUC); Taiwan-only until the KRX short
fetcher lands. All picks re-derive from the frontier — no strategy was
hand-overridden anywhere in this layer.
