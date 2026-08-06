# Step 1-2 Standardization Across Markets (c-74)

*How the prediction engine's Step 1 (which changes) and Step 2
(effective-date liquidity) generalize from Taiwan to the 10-market
APAC set — standardizing what the methodology makes identical,
fencing what markets make genuinely different. Registry:
`agents/market_profiles.py` (importable, tested, self-reporting:
`py agents\market_profiles.py`).*

## The design rule

One question decides where every piece of logic lives: **does
this vary because of the INDEX METHODOLOGY or because of the
MARKET?** GIMI is one rulebook applied everywhere — so coverage
targets, corridors, buffers, float/ATVR/room gates, and the
frame-robustness policy are UNIVERSAL (one code path, zero
per-market forks). Everything downstream of a local exchange or
regulator varies — so it lives in a PROFILE with a status tag,
and the pipeline reads the tag instead of assuming.

## What is now standardized (the shared core)

Already running identically in all 10 markets: factsheet
inversion (implied denominator — counts matched 10/10),
DM/EM corridor arithmetic, membership anchoring (ETF anchor +
composite reconciliation), member-caps census (one script, one
resolver with per-market symbol quirks), and the verdict
frame-check policy. The lambda flow model's FORM is universal
(forced = λ × float shares — AUM arithmetic, price cancels);
only the parameter is market-local.

## The status-tag honesty contract

Every non-universal stage carries one tag, and the run inherits
it: `fitted/validated` (measured on that market's own data),
`UNCALIBRATED` (method transfers, parameter must be refit —
NEVER borrowed from Taiwan), `NOT_INTEGRATED` (data exists,
unwired), `NOT_OBSERVABLE` (no public data in that market),
`DOES_NOT_TRANSFER` (structural difference in kind — tool must
refuse to run), `TO_VERIFY` (desk-knowledge fact awaiting
rulebook confirmation before the market goes live). Blocked or
uncalibrated stages produce NO numbers. This is the
anti-overgeneralization mechanism: silence instead of a wrong
number wearing Taiwan's calibration.

## The genuine-differences register (do NOT generalize these)

- **India has no closing auction.** The close is a last-30-min
  VWAP — "the print" is not a point, MOC-at-the-cross does not
  exist, and every auction analytic (dislocation, cross size,
  auction leg) is DOES_NOT_TRANSFER. Execution there means
  participating a window. This is the sharpest counterexample
  to any "closing auctions are universal" assumption.
- **Korea's short-sale bans** (2020-03→2021-05, 2023-11→
  2025-03): CH1 borrow-channel history is regime-broken; any
  pre-positioning study must era-flag or the ban periods will
  masquerade as "no borrow supply".
- **Japan's close moved** 15:00→15:30 on 2024-11-05: close-
  volume history spans two regimes.
- **China**: access via Connect (quota + eligibility gates),
  float dominated by state holdings (LOW_CONFIDENCE floats),
  borrow effectively unobservable, and the 2018-19 inclusion
  tranches were pre-announced (the review announcement was not
  the information event — v3 flag stands).
- **Price-limit geometry differs in kind**: TW ±10% symmetric,
  KR ±30%, CN dual-band by board, JP value-based, HK/AU none,
  ID asymmetric era-dependent auto-rejection. Limit-lock
  analytics (the 2324 family) must read the profile's band, not
  assume Taiwan's.
- **Access regimes decide whether the foreign-room gate is a
  gate**: active in TW/KR/CN/IN/PH; vacuous in JP/AU/HK/MY.

## What "activating a market" now means (the upgrade path)

A market goes live by upgrading tags, in value order:
1. refit λ on its own event history (UNCALIBRATED → fitted) —
   needs its liquidity panel (adds/deletes, window volumes);
2. upgrade the float source (India first: promoter filings are
   NAMED quarterly disclosures — a v2-grade source waiting);
3. wire the borrow channel where it exists (JP JSF, KR KRX, AU
   ASIC — each NOT_INTEGRATED, none TW-shaped);
4. verify every TO_VERIFY against the exchange rulebook;
5. only then let Step-2 scenarios grade that market's events.

Until each upgrade happens, the run for that market prints the
stage as blocked — which is itself the deliverable: an honest
capability matrix per market, generated from one registry,
instead of ten hand-maintained documents that drift.

## Test

`test_market_profiles` pins: registry ↔ factsheet-pipeline
consistency (markets + DM/EM tiers), schema completeness, TW as
the only fitted λ, India's auction block, Korea's era flags.
