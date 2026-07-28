# MSCI Aug-2026 QIR — Pre-Registration Draft (run 2026-07-28)

*Announcement Aug 12, effective Sep 1. This is the PRE-run: caps
fetched live today, QIR rules applied, positioning overlay attached.
Protocol: refresh caps and FINALIZE by Aug 11, commit before the
announcement (git timestamp = proof), grade after. Script:
`scripts/run_qir_aug2026.py` (chunked cache
data/qir_universe_cache.json).*

## How this run embodies the three differentiators

1. **Graded public track record** — every call below inherits the
   scoreboard (adds 11/11; coverage deletes 14/14; the misses
   documented next to them). This document itself will be graded and
   the scorecard appended, as with the TW50 pitch pack.
2. **Honest probabilistic structure** — calls carry margins vs
   threshold; markets WITHOUT a validated universe get an explicit
   NO-CALL instead of a fabricated list (see below). QIR's stricter
   1.8x add hurdle is applied, not the SAIR rules.
3. **Positioning overlay** — the short-ledger read says which calls
   the street already trades (consensus vs unpriced), from OUR daily
   archive, running since Jul 22 and now extended to today's new
   candidates.

## Calls — markets with validated boundary universes

### Taiwan (28 real names + modeled tail; GMSR $5.5B, QIR add ≥ $10.0B)

| Call | Ticker | Margin | Note |
|---|---|---|---|
| ADD | 3443 GUC | 2.7x GMSR | June TW50 add; well clear of 1.8x hurdle |
| ADD | 8046 Nan Ya PCB | 3.5x | largest margin of the four |
| ADD | 4958 Zhen Ding | 2.6x | |
| ADD | 3665 BizLink | 2.4x | |
| DELETE | 9910 Feng Tay | 0.38x GMSR | coverage rule; country-segment check at finalization |

The four adds are the June TW50 AI-supply-chain cohort clearing MSCI's
stricter QIR hurdle — a **story clients can act on**: the same names,
second index event, tracker AUM this time is MSCI-linked (foreign
flow, not domestic trusts — opposite reading grid per the 7e
identification).

### Korea (13 real names + tail; GMSR $4.3B)

No adds — nothing clears the 1.8x hurdle; **Rainbow Robotics again
below** (consistent with its May float-block, our kept false
positive). DELETE candidate: 011170 Lotte Chemical (0.41x GMSR).

### Japan (19 real names + tail; GMSR $3.9B)

ADD candidates: 285A Kioxia (flagged: yfinance cap looks inflated —
**data-quality caveat, verify before finalizing**), 3659 Nexon, 4755
Rakuten (~3x GMSR each). No deletes among covered boundary names.

## Positioning overlay (Taiwan, short ledger through Jul 22)

| Predicted add | Short balance, 30-session change | Read |
|---|---|---|
| BizLink | **+116%** | street positioned / consensus |
| GUC | +67% | positioned |
| Nan Ya PCB | −26% | June-event shorts still unwinding — UNPRICED for the MSCI leg |
| Zhen Ding | −37% | unwinding — UNPRICED |

*Caveat: the 30-session window spans the June TW50 event, so these
trajectories mix June unwind with August pre-positioning; the daily
forward fetch (KEEP list extended today with 9910/3231/2379/6669)
gives clean pre-announcement trajectories by Aug 12. The differentiated
claim as of today: the street is treating BizLink/GUC as the MSCI
trade already, while NanYaPCB/ZhenDing carry no such positioning — if
the adds are right, the latter two have the larger event-day moves
ahead of them.*

## NO-CALL registry (the honesty line)

China, Hong Kong, Singapore, India, Thailand, Malaysia, Indonesia,
Philippines: **no validated boundary universe file yet → no call.**
Fabricating lists for these markets would be indistinguishable from
the confident-everything previews we criticize. Coverage grows
universe-by-universe (validator-passed), not headline-by-headline.

## Data caveats (all fixable before Aug 11)

Boundary universes + modeled tails (the graded May/June methodology);
caps in local ccy converted at static FX (32.5/1385/155); yfinance
float fields clamped where >1.0; 285A cap outlier flagged; ADV proxied
at 0.4% of cap; segment-migration (SmallCap) legs not yet netted.

## Grading criteria (declared now)

Adds: named-call hit rate + false positives, HIGH threshold = margin
≥ 2x hurdle. Deletes: hit rate with the country-segment rule applied
at finalization. Positioning: do UNPRICED adds show larger T-day
moves than CONSENSUS adds (the overlay's testable claim)? Scorecard
appended to this file after Sep 1.

---

## Addendum (7t) — the eight NO-CALL markets: what CAN be said honestly

Per-name calls still require validated membership (see NO-CALL
registry). Two upgrades shipped:

**1. Market-level QIR skew screen (data-grounded, run 2026-07-28).**
6-month country returns via country-ETF prices — direction of likely
change pressure under the coverage mechanism (relative decliners slip
below coverage cutoffs; risers challenge the 1.8x hurdle):

| Market | 6m return | QIR skew |
|---|---|---|
| Indonesia | −28.3% | DELETION-skewed — strongest deletion pressure of the eight |
| China | −14.5% | DELETION-skewed |
| Thailand | +13.4% | ADD-skewed |
| Singapore | +12.4% | ADD-skewed |
| India | −5.0% | balanced |
| Malaysia | −4.6% | balanced |
| Hong Kong | −1.7% | balanced |
| Philippines | −1.7% | balanced |

*Confidence: LOW by construction — this is directional pressure, not
names. It IS however honestly falsifiable: Aug 12 outcomes should show
more deletions in Indonesia/China than in Thailand/Singapore. Graded
with the rest.*

**2. NO-CALL → call conversion pipeline (scripts/ingest_holdings.py).**
iShares country-ETF holdings CSVs (browser-downloadable in seconds;
sandbox-blocked) drop into data/holdings/ → validated membership +
weight-ranked DELETION WATCH ZONE per market (holdings weights are
float-cap-proportional, so weight rank is the at-risk rank). Add-side
stays NO-CALL until candidate lists exist. Eight files ≈ ten manual
minutes to convert five NO-CALLs into deletion-side coverage before
Aug 12.

---

## Addendum (7w) — post-May-review update: corrections, rationale, probabilities

**Correction found by the May cross-check (recorded, not hidden):** the
9910 Feng Tay DELETE call was INVALID — Feng Tay was already deleted at
the Feb-2026 QIR (our own Feb truth set). The universe file carried
stale membership; corrected (member=0), rerun: Taiwan now has **no
deletion call** among covered names. This is the universe-error class
striking OUR OWN live draft — caught because grading against the
official May list is part of the process. Membership cross-check vs
the May public list is now a mandatory finalization step (Aug 11).

**Updated calls with per-name rationale and probability estimates**
(probabilities from the graded record: HIGH-margin adds 11/12
precision → Laplace-shrunk ~85%/call; coverage deletes 14/14 →
~85-90% when membership verified; unverified-membership candidates
discounted):

| Call | Name | Why the engine flags it | P(correct) |
|---|---|---|---|
| ADD TW | 8046 Nan Ya PCB | full cap $19.4B = 3.5x GMSR, far above the 1.8x QIR hurdle ($10.0B); float 0.6+; May migration left it the largest eligible non-member | **~85%** |
| ADD TW | 3443 GUC | $15.1B = 2.7x; AI-ASIC rerating did the work; crowding +67% says street agrees | **~85%** |
| ADD TW | 4958 Zhen Ding | $14.2B = 2.6x; passes min-FF-cap (float 0.69) | **~85%** |
| ADD TW | 3665 BizLink | $13.3B = 2.4x, the thinnest of the four but still >2x; street most positioned (+116%) | **~80%** (smallest margin) |
| DELETE KR | 011170 Lotte Chemical | $1.7B = 0.41x GMSR, below the 0.5x coverage floor; NOT deleted in May (verified vs official list); petrochemical downcycle did the shrinking | **~75%** (KR Feb membership unverified; segment-rule check at finalization) |
| WATCH JP | 285A Kioxia | ~3x+ hurdle IF non-member — but cap outlier flag AND membership unverified (Dec-24 IPO may already be in) | conditional only — verify before any call |
| WATCH JP | 3659 Nexon / 4755 Rakuten | ~3x hurdle IF non-members; deletion-history verification pending | conditional only |

**Portfolio expectation:** of the 5 committed calls, expect ~4.1
correct (sum of probabilities). The honest average-success answer for
this engine class: **HIGH-margin adds ~85% per call, verified coverage
deletions ~85-90%, rank-boundary deletions ~50-60% (never committed as
calls), everything else NO-CALL.** Small-n caveat: these rates rest on
5 graded reviews / 26 committed calls; the Laplace shrinkage is the
honest adjustment, and Aug 12 adds the next sample.
