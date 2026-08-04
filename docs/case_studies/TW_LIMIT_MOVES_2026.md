# Taiwan limit-up/limit-down — incidence and two print-day case studies

*Session 9h. Data: official TWSE daily files (MI_INDEX ALLBUT0999),
~1,080 common stocks/day (4-digit codes, ETFs excluded). Limit prices
computed EXACTLY per the tick table (up-limit = prev x 1.1 floored to
tick; down-limit = prev x 0.9 ceiled to tick) — both case-study locks
verify to the tick (109.0 = floor(99.1x1.1); 110.0 = ceil(122x0.9)).
Reproduce: `python scripts/limit_moves_tw.py`.*

## 1. Incidence — July-2026 baseline (19 sessions)

| Metric | Daily average | Range |
|---|---|---|
| Touched limit-up | **2.96%** of stocks (~32 names) | 0.3% – 6.3% |
| Locked limit-up at close | **2.01%** (~22 names) | 0.2% – 5.2% |
| Touched limit-down | **2.17%** | 0.1% – **9.3%** (Jul-17) |
| Locked at close with EMPTY book | ~95% of locked-up closes show zero ask |

The tape is lumpy, not uniform: limit-downs cluster violently on
market-stress days (Jul-17: 101 names touched down, 79 locked; Jul-28:
66 touched), while limit-ups run steadier. A locked close is almost
always a truly frozen book — the last-ask column is empty on ~95% of
locked-up closes, so "locked at close" ≈ "no seller remained".

## 2. Index print days vs baseline

| Day | Event | Touch-up % | Lock-up % | Touch-down % |
|---|---|---|---|---|
| 2026-02-26 | MSCI QIR print | 4.95 | 3.83 | 0.65 |
| 2026-03-20 | FTSE print | 5.05 | 2.81 | 0.65 |
| 2026-05-29 | MSCI SAIR print | 5.74 | 3.89 | 0.19 |
| 2026-06-18 | FTSE print | 6.39 | **5.28** | 0.19 |
| July baseline avg | — | 2.96 | 2.01 | 2.17 |

All four 2026 print days ran ~1.7–2.2x baseline on limit-up incidence
(market-wide, not only event names). n=4 days — elevated but within
the range of strong ordinary up-days; treat as a prior, not a law.

## 3. Case study A — 6919 (康霈*): DELETED, and locked LIMIT-UP into
## its own deletion print (2026-06-18)

The window (announcement 2026-06-05 at 96.0):

| Date | Close | Volume | Note |
|---|---|---|---|
| 06-05 | 96.0 | 4.3M | announcement (deletion) |
| 06-08 → 06-11 | 91.5 → **88.2** | 3-5.5M | deletion pressure, −8% |
| 06-12 → 06-17 | 92.7 → 99.1 | 3-5M | full recovery INTO the print |
| **06-18 (T)** | **109.0 = limit-up, locked** | **53.9M (~13x)** | deletion print at the CAP |

A deleted stock printed **+13.5% above announcement-day close, at the
exact +10% cap, with zero asks remaining**, on 13x volume. The passive
deletion SELL was on the right side of the lock: at a locked limit-up
the excess is buy demand, so sell orders fill completely — the tracker
sold its entire block at the best price of the whole window. Working
the sale early (06-08/06-11 at 88-92) would have cost **~1,700-1,900
bps** vs the print. This is the FTSE-delete recovers-into-print
pattern (decade median +57 bps for early selling) in its most extreme
form: the pre-positioned short crowd had to buy back, and the only
liquidity event big enough to cover in was the deletion print itself —
a squeeze INTO deletion.

## 4. Case study B — 2344 (華邦電): ADDED, and locked LIMIT-DOWN into
## its own add print (2026-03-20)

The window (announcement 2026-03-06 at 106.5):

| Date | Close | Volume | Note |
|---|---|---|---|
| 03-06 | 106.5 | 123M | announcement (add) |
| 03-09 → 03-18 | 101 → **128** | 160-296M | add momentum, +20% |
| 03-19 | 122.0 | 198M | fade begins |
| **03-20 (T)** | **110.0 = limit-down, locked** | **338M** | add print at the FLOOR |

The mirror image: an ADDED stock crashed to the exact −10% floor on
its inclusion day, on the heaviest volume of the window. The
pre-positioned long crowd (+20% run-up) unwound into the passive buy
— and dumped MORE than the trackers needed, pinning the floor. Again
the index flow sat on the right side of the lock: at locked
limit-down the excess is sell supply, so the tracker's MOC BUY filled
completely at 110.0 — **14% below the T-2 price**. Pre-positioning
alongside the crowd (buying 03-16/03-18 at 117-128) would have been
the worst trade of the window.

## 5. Lessons (both cases, one mechanism)

1. **The print price is set by the crowd's exit, not by the index
   flow's direction.** Deletion + crowded shorts → squeeze UP; add +
   crowded longs → dump DOWN. The naive signs (deletes fall, adds
   rise on T) invert exactly when pre-positioning is heavy — the
   crowding-violence link, now with two locked-limit exhibits.
2. **Print-day locks tend to FAVOR the obligated flow.** In both
   cases the passive order was the liquidity the crowd desperately
   needed, and the band capped the price in the passive side's
   favor. Fill risk at a print-day lock belongs to the crowd's side
   of the book, not the tracker's.
3. **Mid-window locks remain the dangerous kind** (schedule slips,
   can't work the order — the planner's LOCK RISK flag), and the
   run-sheet contingency should distinguish them from print-day
   locks, which are usually resolution, not risk, for the basket.
4. For the discretion matrix these are the extreme validations of
   the existing rules: crowded delete → the WORK-AHEAD rationale is
   about being out before the squeeze forms, and crowded add → NO
   pre-positioning (2344 is what being crowd-adjacent costs).
5. Baseline numbers for the planner's priors: ~2-3% of the tape
   touches a band on an ordinary day; ~2x that on print days;
   locked closes are real locks (empty books ~95%).
