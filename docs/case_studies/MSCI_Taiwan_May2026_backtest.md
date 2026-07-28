# Backtest — Reconstitution Engine vs the Actual MSCI Taiwan May 2026 SAIR

*Session 6v. The prediction engine (`agents/reconstitution.py`) run on a
pre-announcement reconstruction of the MSCI Taiwan universe and graded
against MSCI's actual May 12, 2026 announcement (effective May 29).*

## The truth set (actual outcome, from MSCI/press coverage)

- **Added to MSCI Taiwan Standard (1):** MPI Corp (6223) — probe-card /
  AI-test runner.
- **Deleted (7, all migrated to Small Cap):** Asia Cement (1102), Catcher
  (2474), China Airlines (2610), Compal (2324), Far Eastern New Century
  (1402), Taiwan High Speed Rail (2633), Teco (1504).
- **Watched but NOT added (controls):** Winbond (2344), Nanya Tech (2408)
  — press noted liquidity/attention-rule concerns kept them out.

## Setup

Universe reconstructed as of ~May 1 2026 (pre-announcement): 37 named
Taiwan Standard members + 3 non-member candidates/controls + a 300-name
modeled small/mid tail (the full-universe lesson from the Japan case
study). Caps/floats APPROXIMATE (±30%, TWD≈30). SAIR rules.

## Scorecard

| | Original engine (global GMSR only) | Upgraded engine (+ country-segment rule) |
|---|---|---|
| Adds | **1/1** — MPI predicted at 1.74× GMSR | 1/1 |
| Add false positives | 0 (Winbond & Nanya Tech correctly excluded) | 0 |
| Deletions | **0/7** — all seven sat at $4.6–6.5B full cap, far above the $2.7B global floor | **7/7**, zero named false flags |

## The finding (this is the report's core)

**The engine's add logic worked as designed; its deletion logic tested a
mechanism MSCI didn't use.** The seven deletions were not
global-minimum-size failures — every one was comfortably above the 0.5×
GMSR floor. They were **country size-segment migrations**: names that
fell below Taiwan's ~85% cumulative free-float coverage cutoff moved
Standard → Small Cap. This was listed in the engine's disclosed
omissions ("country-level minimum size interplay… NOT modeled") — the
backtest converted a disclosed limitation into a measured 0/7, and the
fix into a measured 7/7.

**The fix, now in the engine:** `MSCIRules(country_coverage=0.85,
country_buffer=0.05)` flags members below the country FF-coverage cutoff
as migration deletions (default off; tested; the Taiwan backtest run
uses buffer 0 for grading).

## Honest caveats on the 7/7

- **Partial circularity:** the reconstruction places the seven deleted
  names at the bottom of the member list by FF cap — faithful to reality
  (that is why MSCI migrated them), but it means the 7/7 validates the
  *mechanism*, not the engine's ability to rank borderline names from
  noisy data. With ±30% cap error, borderline names (Chailease at ~$4.5B
  FF) could flip either way.
- **No buffer in the graded run:** MSCI applies buffer zones to limit
  turnover; a production run tunes `country_buffer` on past reviews.
- **Membership and caps unverified at single-name precision** — the desk
  version reconciles against MSCI's official public lists.

## What a desk does with this

Run the screener ~6 weeks before each review on live caps → publish the
candidate list internally (the radar) → on announcement day, diff
prediction vs official (the reconciler) → feed hits/misses back into
parameter tuning (buffer, coverage) exactly as this backtest did. The
May-2026 Taiwan cycle: prediction would have flagged MPI ~and the
migration seven with weeks of runway to plan the event trades — the
crowding/frontier machinery (Page 2) prices what to do with that runway.

## Interview one-liner

"I backtested my reconstitution engine on the actual May-2026 MSCI
Taiwan review: adds 1/1 with clean controls, deletions 0/7 — because the
deletions were country-segment migrations, a mechanism I had documented
as not modeled. I implemented the country-coverage rule, re-ran, got
7/7, and kept both numbers in the report — the 0/7 is the more valuable
half, because it shows the engine fails exactly where its documentation
says it will."


---

## Fixing the caveat (session 6w)

The circularity/noise caveat was addressed four ways — two measured now,
two as protocol:

### Fix 1 — Monte-Carlo perturbation (measured)

`robustness_check` (now in `agents/reconstitution.py`) perturbs every cap
by lognormal noise and every float by clipped normal noise, re-runs the
engine per draw (400 draws), and reports the metric distribution:

| Cap error | Add recall (share perfect) | Delete recall mean (p10) | Delete precision mean |
|---|---|---|---|
| ±10% | 1.00 (100%) | 0.98 (0.86) | 0.85 |
| ±20% | 0.97 (97%) | 0.95 (0.86) | 0.75 |
| ±30% | 0.85 (85%) | 0.94 (0.86) | 0.66 |

**Refined claim:** the 7/7 deletion *recall* is robust to the stated
measurement error (even the worst decile catches 6/7 at ±30%); the
zero-false-flag *precision* was partly a gift of the reconstruction —
at ±30% noise, precision degrades to ~0.66. Report the recall with
confidence; report the precision with the distribution.

### Fix 2 — Out-of-sample test on the February 2026 QIR (measured)

Same parameters, untuned, on a review NOT used to design the rule
(truth set: add HongJing; delete Eclat / Cheng Shin / Nien Made /
Feng Tay): **adds 1/1, deletions 4/4** — and 9 named "false flags", of
which **7 were the exact names MSCI deleted three months later in May**.
The no-buffer rule wasn't wrong; it was early. Buffer calibration on the
February event:

| country_buffer | Feb recall | May names flagged early | true false flags |
|---|---|---|---|
| 0% | 4/4 | 7/7 | NanYa, Chailease |
| 2% | 4/4 | 7/7 | — |
| 5% | 4/4 | 6/7 | — |
| 8% | 4/4 | 4/7 | — |

The buffer is the knob trading single-review precision against
early-warning coverage — at ~2% (on this approximate data), the rule is
simultaneously precise for February and a complete early-warning list
for May. A desk tunes this on more review cycles; the parameter's
MEANING is now demonstrated, not asserted.

### Fix 3 — real as-of data (protocol)

`scripts/run_msci_japan_screener.py`'s fetch pattern applied to Taiwan
with caps reconstructed from price history as of the pre-announcement
date (close × current shares outstanding — share-count drift disclosed).
Removes the hand-built-universe objection entirely; run locally.

### Fix 4 — pre-registration (protocol, the definitive one)

Before the August 12 QIR announcement: run the screener on live data,
commit the prediction file to git (the commit timestamp is the
tamper-proof seal), grade publicly after the announcement. No
reconstruction, no hindsight, no circularity — the strongest evidence a
solo project can produce, and the exact prediction→reconcile loop a desk
runs.
