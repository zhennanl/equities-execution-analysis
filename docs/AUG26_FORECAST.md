# MSCI Taiwan, August 2026 — how the called names should trade

*Written 2026-08-10. Base rates from `data/tw_case_study.json` (57
registry-dated Taiwan additions, excess over TAIEX). Current positioning
from `scripts/aug26_forecast.py`. Every number below is a median with its
quartiles, because the quartiles are wider than the medians and pretending
otherwise would be the main way to be wrong.*

## The situation

MSCI has **not** announced the August 2026 review yet. Taiwan's August
announcements land Aug 7–12 (2017: 10th, 2020: 12th, 2021: 11th, 2023:
10th, 2024: 12th, 2025: 7th) with the print at month-end. So the
announcement is **one to three sessions away**, and the median
announcement-to-effective gap is **13 business days** — putting the print
around **Aug 26–31**.

We called four additions on 2026-08-09 off 31 July data: **2408, 8046,
2344, 8299**. Nothing is confirmed.

**The dominant uncertainty is not how these names trade — it is whether
they are on the list at all.** Our own call puts three at p≈0.62 and 8299
at p≈0.37. Everything below is conditional on inclusion, and the section
on a miss matters more than the rest.

> **CORRECTION, 2026-08-10 (later same day).** The positioning table
> below is measured to **31 July** and is now known to be misleading for
> at least one name. A direct probe of 1–7 August shows **8299 rallied
> 1,640 → 2,020, +23% in five sessions** — the opposite of the −20.7%
> that its row reports, and inside exactly the window the table could not
> see. Any name may have moved similarly. Treat the table as a 31 July
> snapshot, not as current positioning, until
> `py scripts\tw_live_topup.py prices` has been run. The conclusion drawn
> from it — "nobody is positioned, so the market may be telling us these
> names are not going in" — is the part most likely to be wrong, and for
> 8299 it now looks actively wrong.

## The finding that should worry us

Historical additions drift UP into the announcement. Our four are doing
the opposite, and not marginally.

| | 20-day excess vs TAIEX | foreign net buy | borrow build | volume |
|---|---|---|---|---|
| **historical ADD** (n=57 / 43) | **+4.8%** (p25 −1.6%, p75 +14.5%) | **+0.53** days ADV, 60% buying | +0.31 days ADV, 91% building | elevated |
| 2408 | −4.1% | −0.59 | +0.46 | 0.64× |
| 8046 | −14.5% | −0.98 | +0.06 | 0.94× |
| 2344 | −21.7% | −0.33 | −0.08 | 0.56× |
| 8299 | −20.7% | n/a (TPEx) | n/a | 0.56× |

**All four sit below the 25th percentile of the historical
pre-announcement drift.** Seventy per cent of past additions were up into
the announcement; every one of ours is down, three by more than 14%.
Foreigners are net *sellers* of all three we can see, where the template
says they are buyers in 60% of cases. Volume is *below* normal in all
four, where pre-positioning would show up as above.

There are two readings and the data cannot separate them.

**Reading A — nobody is positioned, so the surprise is bigger.** No
front-running means more left to do after the news. On this reading the
announcement gap and the print should be at the *high* end of the
historical range, and the usual pre-announcement drift simply never
happened.

**Reading B — the market is right and we are wrong.** These names have
de-rated hard. The most likely single explanation for "no one is
positioned for an addition" is that it is not going to be an addition.

I lean weakly toward B being the larger risk, for one reason: our call's
own probabilities are ~0.62, so it is not a high-conviction list to begin
with, and the positioning data is independent evidence pointing the same
way. But this is a judgement, not a measurement — I have no base rate for
"names the market ignored that got added anyway."

## Phase 1 — now to announcement (1–3 sessions)

Expect **nothing**. The pre-announcement drift has already not happened,
and there is no mechanism that turns it on in the last two days. Volume
below 1× ADV says no one is building.

The one thing worth watching is the **borrow book on 2408** (+0.46 days
of ADV, the only one of the four building). Per the case study, borrow
predicts the *size* of the print (rho +0.63, p<0.0001) and not its
direction (rho +0.07, p=0.55) — so read that as "if 2408 is added, expect
a larger-than-median print", not as a directional signal.

## Phase 2 — announcement to effective (~13 sessions)

**If added**, the historical template:

| leg | p25 | median | p75 | hit rate |
|---|---|---|---|---|
| announcement day (gap1) | −1.7% | **+1.1%** | +4.1% | 58% |
| announcement → effective drift | −3.2% | **+1.5%** | +15.7% | 61% |
| total announcement → effective | −3.0% | **+2.8%** | +18.3% | 63% |

Read the hit rates before the medians. **A 58% announcement-day hit rate
is close to a coin flip**, and the p25 is negative — roughly two additions
in five fall on the news. The median +1.1% is real but it is not a trade
you size aggressively, and the interquartile range is six percentage
points wide on a one-day move.

The drift leg is where the money historically is (+1.5% median, and a p75
of +15.7% that says the right tail is fat), and foreigners are the ones
doing it: **+0.51 days of ADV bought between announcement and print**, 67%
of events.

Given our names show *negative* pre-drift, if they are added I would
expect the drift leg to carry more of the total than usual — the capture
ratio (0.76 median) should run higher, because there is no pre-positioning
to unwind.

## Phase 3 — the print, and after

**The effective day is an auction event, not a day.** Taiwan puts a
median **64% of the effective day's volume into the closing bar** (p25
56%, p75 76%) — about **9× a normal close** — and the close still prints
within **−0.16%** of the day's own VWAP. Total effective-day volume runs
**6.4× ADV** (p25 3.0×, p75 10.0×).

The practical read: the auction absorbs a very large order without
dislocating. If you have to trade this, the close is where the liquidity
is, and working the session to avoid the auction is likely the more
expensive choice.

Effective-day return is a **+0.6% median on a 58% hit rate** — noise.

**Then it reverses, and this is the most reliable leg in the whole
study:**

| horizon | p25 | median | p75 |
|---|---|---|---|
| +1 session | −4.9% | **−2.5%** | +0.3% |
| +5 sessions | −9.8% | **−4.1%** | +0.5% |
| +20 sessions | −10.7% | **−3.6%** | +2.4% |

Foreign buying **stops dead at the print** — +0.20 days of ADV on the
effective day itself, then **−0.02 over the next five sessions with only
42% of events showing any buying at all**. That is the mechanism: the
tracker bid is a one-day event, and once it is gone the name is left
carrying whatever the arbs need to unwind.

The reversion is larger than the entire announcement-to-effective gain
(−4.1% at five days against +2.8% total into the print). **On these
numbers the addition is a better short after the print than it is a long
before it** — though see the limits: this is 57 events, the quartiles
straddle zero at the top end, and none of it is transaction-cost adjusted.

## If a name is NOT added

We have no direct base rate for this, and it is the single biggest hole in
this note. What we can say structurally: a name that never drifted up has
little to give back, so the downside on a miss is probably smaller for
these four than it would be for a typical candidate that had already run
15%. That is a genuine, if small, consolation of the odd positioning.

## What would change my mind

- **Foreign net buy turning positive in 2408/8046/2344 before the
  announcement.** That would move me toward Reading A and materially
  raise confidence in the call.
- **Volume lifting above ~1.5× ADV** with no news — the signature of arbs
  building.
- **Borrow building across all three**, not just 2408.

## Limits worth stating

- **Our price series ended 31 July; TAIEX ran to 7 August** — and the
  blind window turned out to contain a +23% move in 8299. The cause was
  `tw_vintage_harvest.py`, which hard-codes `END = "2026-08-01"` and
  skips any series already cached, so it can bootstrap a name but never
  top one up. Fixed by `scripts/tw_live_topup.py prices`. **Run it before
  reading the positioning table above.**
- **8299 is TPEx-listed**, so it is in neither the T86 institutional file
  nor the borrow book — we were blind on positioning for the name our own
  call is least sure of (p≈0.37). Now covered:
  `scripts\tw_live_topup.py flows` pulls institutional flow and
  securities lending for TWSE *and* TPEx names from FinMind, whose
  investor categories are named rather than positional. Lending is stored
  as raw new-lending volume and is labelled unverified until
  `calibrate` establishes whether the units are shares or lots.
- **57 events, quartiles straddling zero on every leg except reversion.**
  These are weak central tendencies, not laws.
- **The intraday numbers are n=16** additions from 2023 onward. Directional
  at best.
- **No transaction costs anywhere.** A −4% five-day reversion in a name
  trading 6× ADV on the print is not a −4% return to anyone who has to
  cross a spread to get it.
- **Correlation, not mechanism.** Nothing here identifies why.
