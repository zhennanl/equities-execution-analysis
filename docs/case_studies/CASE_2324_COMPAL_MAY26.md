# Case Study — 2324 Compal, May-2026: the Deletion That Closed UP 9.6%

*Session 9i (2026-08-05). Four independent data series — daily
tape, 5-minute bars with the auction separated, foreign holdings,
securities-lending balances — all from held caches. The anatomy of
the modern tail risk: the squeeze that replaced the limit-lock.*

## Confirmed: it was a deletion

MSCI May-2026 review, announced 2026-05-12, effective at the
2026-05-29 close. Official deletions: 1102, 1402, 1504, **2324
Compal**, 2474, 2610, 2633. Confirmed against the print-verified
event key.

## The window — the squeeze started a week BEFORE effective day

| Date | Close | Volume | Move |
|---|---|---|---|
| May-13..20 | 31.3 → 27.6 | 40–120M | the EXPECTED deletion drift (down) |
| **May-21** | **30.35** | 114M | **+10.0% LIMIT-UP, mid-window** |
| May-22 | 31.50 | 200M | +3.8% |
| **May-25** | **34.65** | 280M | **+10.0% LIMIT-UP again** |
| May-26..28 | 33.4–33.5 | 117–239M | consolidation at the highs |

A catalyst repricing hit in the middle of the deletion window
(the tape cannot name it — a news-archive check can; what the
tape CAN say is that it was violent, real, and foreign-bought).
Baseline ADV was ~35M shares; window days ran 3–8× that.

## The positioning that made it combustible

- **Securities-lending balance: ~440 MILLION shares on loan**,
  flat through the entire window (≈ 13× ADV, ≈ 10% of all
  shares) — the standing short base, including index arbitrageurs
  running the classic pre-sell (window completion measured 2.04×
  expected flow, the highest of the event) plus pre-existing
  fundamental shorts.
- **Foreign holdings: +2.85pp INTO the deletion** (37.4% May-18 →
  40.3% May-27) — the wrong-way flag (H16's second leg): real
  buyers accumulating what the index was about to expel.
- At T-1 the model flagged exactly this name OVERCROWDED with
  wrong-way foreign — the only such compound flag of the event.

## Effective day, in 5-minute resolution

Prior close 33.50. **Gap open 35.00 (+4.5%)** — shorts already
paying up. Grind to 36.85 by late morning; drift 36.3–36.5 into
the final hour; last continuous trade **36.35**. Then the close:
**the auction matched 338.6 million shares — 49% of the day's
693M total (vs the 78% median for the other deletions) — at
36.70, ABOVE the last continuous price.** The entire forced
passive sale — every tracker's stake — hit one auction, and
demand (short covering + momentum + foreign bids) absorbed all
of it AND lifted the price. Day close +9.6%, pennies below the
10% limit (high 36.85 — technically not locked, verified OHLC).

## The aftermath — the covering avalanche, then the crack

| Date | Close | Move | SBL balance |
|---|---|---|---|
| May-29 (T) | 36.70 | +9.6% | 434M |
| Jun-01 | 40.35 | +9.9% | 382M (−52M) |
| Jun-02 | 44.35 | +9.9% | 226M (−156M) |
| Jun-03 | 47.05 | +6.1% | 213M |
| Jun-04 | 42.35 | **−10.0%** | 213M (covering done) |
| Jun-05 | 41.40 | −2.2% | 168M |

Roughly **270 million shares of shorts covered in four sessions**
— the +43% post-deletion melt-up — and the day the balance
stopped falling, the stock cracked limit-down. Foreign holdings
peaked at 42.0% on Jun-01 and were dumped to 38.4% by Jun-04:
the fast money exited into the top it created.

## Why a deletion produced a limit-up-class close — the mechanism

Deletion flow is the most ANTICIPATED flow in markets, so it gets
pre-sold: the arbitrage crowd shorts through the window intending
to buy back cheaply from the passive sellers at the print. That
works when nothing else moves. Here a mid-window catalyst flipped
the price against a ~10%-of-shares short base: the pre-sellers
became forced FUTURE BUYERS, and the mechanical passive sale at
the close — normally the pressure — became the squeeze's FEEDSTOCK:
the only large liquidity block available to cover into. Demand
exceeded even that block, so the print cleared UP. The playbook's
core measurement ("the print lands AGAINST the obligated side")
in its most extreme observed form.

## Desk lessons, each tied to a number

1. The compound signature (completion ≥ 1.5 AND wrong-way
   foreign — H16) flagged THIS name at T-1 and no other. It is
   the monitoring priority, not the generic crowding level.
2. Agency clients SELLING the deletion were handed a gift close
   (+9.6% vs the drift lows) — the advice "your flow will be
   absorbed; lean on the close" was right for the obligated side.
3. A guaranteed-close desk pre-hedged short into this name was
   the natural casualty — risk-transfer pricing must price the
   squeeze scenario, and the SBL balance (10% of shares, visible
   DAILY, free) was the tell sitting in plain sight.
4. The post-T pattern rewarded playbook patience twice: the
   deferred leg captured the melt-up, and the Jun-04 crack (the
   day covering stopped) marked the exit — SBL balances called
   the top in real time.
