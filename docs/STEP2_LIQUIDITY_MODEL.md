# Step 2 — Liquidity-Supply Forecast (ann → eff): Who Will Supply the Close?

*Session 9i (2026-08-05). Code: agents/liquidity_forecast.py; May-26
PIT demo: data/liquidity_forecast_may26.json. The interview lessons
(flow-completion + wrong-way risk) implemented as one model.*

## The framing, in a PT trader's terms

On the effective date the passive complex MUST print ~16× ADV
(deletes) / ~8× (adds) at the close. That liquidity is supplied
mostly by arbitrageurs who accumulated inventory during the window
and unwind INTO the print. So "how will the close trade?" is an
INVENTORY-ACCUMULATION measurement problem, and the inventory is
observable daily, PIT, from free data:

    crowding_ratio = accumulated pre-positioning / expected passive flow

## Observables (Taiwan; all daily, all PIT at T-1)

| Leg | Measures | Source |
|---|---|---|
| Flow completion (primary) | cum abnormal volume since ann ÷ expected flow (class-prior T-mult × 60d baseline ADV) | vintage price/volume cache |
| Borrow build | SBL balance Δ ÷ expected flow — deletes' institutional channel (short the window, buy the print) | TWT93U cache (event_data_cache) |
| Foreign flow | foreign-holding Δpp × shares ÷ expected flow, with a direction-consistency flag (foreigners should SELL into deletes) | FinMind Shareholding rows |
| Retail shorts | margin short-sale balance Δ ÷ expected flow | FinMind MarginPurchaseShortSale |

## Scenario map → client advice (declared BEFORE the demo ran)

| Scenario | ratio | Advice |
|---|---|---|
| UNDERSUPPLIED | < 0.3 | thin close — your flow moves the print; start early, spread window + close; demanding size at T pays a large toll |
| BUILDING | 0.3–0.7 | normal pace; standard MOC participation; monitor daily |
| WELL-SUPPLIED | 0.7–1.2 | inventory ≈ demand; lean on the close, minimal pre-hedge |
| OVERCROWDED | > 1.2 | inventory EXCEEDS passive demand (the Apple case) — print can land AGAINST the obligated side, T+1 reversal likely; cap MOC, split pre-close/T+1, consider fading |

## May-2026 PIT demo (frame frozen at T-1 = May-28; graded after)

| Name | Side | Completion | Foreign (dir ok?) | SBL Δ | PIT scenario | Realized T-mult | T+3 move |
|---|---|---|---|---|---|---|---|
| 1102 | del | 0.39 | −1.78pp ✓ | +0.06 | BUILDING | 21.7× | +0.6% |
| **2474** | del | **1.70** | −2.56pp ✓ | −0.01 | **OVERCROWDED** | 24.8× | **+26.3%** |
| 2610 | del | 0.17 | −0.08pp ✓ | 0.00 | UNDERSUPPLIED | 9.9× | +4.5% |
| **2324** | del | **2.04** | **+2.85pp ✗** | 0.00 | **OVERCROWDED** | 19.9× | **+28.2%** |
| 1402 | del | 1.65 | −0.93pp ✓ | n/a | OVERCROWDED | 22.8× | +6.4% |
| 2633 | del | 0.91 | −1.14pp ✓ | +0.14 | WELL-SUPPLIED | 41.7× | +3.6% |
| 1504 | del | 0.49 | −0.19pp ✓ | n/a | BUILDING | 18.4× | +10.7% |
| 6223 | add | 0.31 | +0.42pp ✓ | n/a | BUILDING | 5.9× | −1.0% |

**Reading:** the two names the PIT frame called OVERCROWDED with the
most extreme completion (2474 at 1.70, 2324 at 2.04 — 2324 also the
only wrong-direction foreign flag: foreigners BUYING into a delete)
were exactly the two monster T+1..3 reversals (+26%, +28%). The one
UNDERSUPPLIED call (2610) printed the smallest multiple of any
delete (9.9× vs 18–42×). 2324's +28.2% cross-checks the post-event
pack's independently computed +2,820bps — arithmetic reconciled.

## Honesty box

- n = 8 names, one event. The scenario thresholds (0.3/0.7/1.2)
  were declared before the demo ran and have NOT been tuned on it;
  they are registry-v4 candidates for calibration on the decade
  replay (46 reviews of vintage volumes/foreign flow now in hand).
- Expected-flow priors (16×/8×) are pre-May measured class medians —
  PIT-legal for this frame; per-name error in the prior propagates
  1:1 into the ratio. Realized multiples ran 10–42×: the prior is
  the model's weakest input, stated.
- SBL coverage is partial (cache built around the then-watchlist:
  1402/1504/6223 missing); retail margin shorts are tiny in TW —
  the volume-completion leg is the workhorse.
- 2610's small print despite UNDERSUPPLIED read is consistent but
  one observation — no victory lap on n=1 cells.

## ML framing (the path from rules to calibration)

Per name-event: features = completion trajectory (level, slope,
acceleration), SBL/foreign legs, direction consistency, prior
crowding regime; targets = realized print multiple, close-vs-VWAP
gap sign, T+1..3 reversal. The decade vintage caches make ~150 TW
name-events buildable — enough for event-clustered logistic
calibration of the scenario boundaries, with Aug-2026 as the
standing OOS event. Until then the model ships as declared rules —
same discipline as every other layer.

## Aug-2026 live use

Run daily from Aug-12 announcement on the actual change list:
completion updates each close, scenarios move UNDERSUPPLIED →
BUILDING → (hopefully not) OVERCROWDED, and the client note writes
itself from the advice column. This is the desk product: not a
point forecast of the print, but a daily-updating read of WHO is
supplying the close and what that means for how to trade it.
