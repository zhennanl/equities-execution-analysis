# How Index Reviews Pick Stocks — and What Our Numbers Mean
## A plain-language explainer for the desk

*Session 9i. Purpose: Bill explains the analysis to PT traders
without jargon walls. Every term below states WHAT it is, HOW we
compute it, and WHY a trader should care. Numbers quoted are our
own measurements.*

---

## Part 1 — How MSCI decides who's in and who's out

**The height line at the amusement park.** Imagine MSCI wants its
Taiwan index to contain "the companies that together make up 85% of
the investable market." It lines up every listed company from
biggest to smallest and walks down the line, adding up their
investable value (more on "investable" below), until it reaches 85%
of the total. The size of the LAST company that made it in becomes
the height line — we call it the **GMSR** (the "magic line"). For
Taiwan right now that line sits around **$4-5B** of company value.

**The two doors.** MSCI doesn't churn the index every time someone
grows or shrinks a little — that would force funds to trade
constantly. So there are two doors with buffers:
- **The entry door is HIGH**: an outsider must be clearly bigger
  than the line to get in — 1.15x the line at the big May/November
  reviews, and a much stricter **1.8x** at the small February/
  August reviews. (That's why Feb/Aug reviews are usually quiet —
  our count: Taiwan had changes in only 7 of 11 August reviews,
  usually 1-2 names.)
- **The exit door is LOW**: a member isn't kicked out until it
  shrinks below **half** the line (0.5x). Between half-the-line and
  the line, a member lives on borrowed time — we call that the
  **watch zone**.

**"Investable" value — the float haircut.** MSCI doesn't count
value that can never be bought: founding-family stakes, government
holdings, cross-holdings. A $10B company where the family holds 70%
counts as $3B investable. That haircut is the **free float**, and
getting it slightly wrong is behind most prediction misses — ours
included.

**The housecleaning rhythm.** The deep cleanup — sweeping out
members that drifted below the coverage line — happens at the
May/November reviews only. Our decade count: **~79% of all Taiwan
deletions happened at May/Nov reviews.** February/August mostly
execute only the extreme cases (below half-the-line). And
deletions are BATCHED: a name flagged in the watch zone converts to
an actual deletion about **2 out of 3 times at the next big
review** — which is why we publish deletion calls as probabilities
("hazards"), not certainties.

**Why our engine can predict this at all.** Everything above is
arithmetic on public numbers — prices, share counts, floats. We
rebuild MSCI's ladder ourselves and check who's near the doors.
When we were graded on the May-2026 review we called 17 of 17
additions correctly across Asia. Where we miss, it's almost always
a DATA gap (a float number MSCI sees and we don't; a company below
the size range our data covers), not a logic gap — and we say so
in the pack rather than bluffing.

## Part 2 — The analytics, term by term

**Crowding factor** — *are other traders already positioned for
this change?*
- HOW: Taiwan publishes, daily, how many shares of each stock are
  sold short (borrowed and sold by people betting on a fall). We
  take today's short balance and compare it with ~30 trading days
  ago. Up more than +25% = **HIGH** crowding; +5-25% = MED; less =
  LOW. If a big build has already been unwound 15%+ off its peak,
  we tag it **EXITING** — the crowd came and left.
- WHY IT MATTERS: the measured surprise is that crowding predicts
  HOW the effective-day close behaves, not just risk. Crowded
  deletes kept FALLING into the close (+149 bps more favorable
  drift remained — the crowd's selling pressure persists), and the
  day the crowd must exit sets the print: our 6919 case locked
  LIMIT-UP on its own deletion day because trapped shorts had to
  buy back. Live example: 1101's shorts are up ~32% over 30
  sessions — the street is positioning for its deletion.

**T-multiple (print multiple)** — *how big is the effective-day
volume vs normal?* Measured MSCI deletions in Taiwan trade a median
**16x** their ordinary daily volume on the effective day (worst
case 38x). One number tells a client "this is not a normal day."

**Auction share** — *how much of the day happens in the single
closing print?* Taiwan ends with one giant matched auction at
13:30. For deletions, that print IS the day: median **60-72%** of
all daily volume in one transaction (extreme: 1102 at 91%).
For additions it's the opposite — the hot momentum names trade so
much all day that the index buy is a minority even of the close
(median ~10-50%). Practical reading: on a delete, OUR order is the
auction — footprint management is everything; on an add, we're one
buyer among many.

**Gap band** — *how far can the closing print land from the last
traded price?* Measured: **~123 bps typical, ±82** — and
DIRECTION IS NOT PREDICTABLE (we tested share-vs-gap three times,
n=17/85/86: no relationship — we quote a band, never a guess).

**ADV-days** — *how many normal days of volume is this order?*
Order size ÷ average daily volume. Under 1 = one close can absorb
it (MOC). 1-3 = work some, close the rest. Over 3 = multi-day plan
with a hard "must start by" date.

**Auction footprint** — *what fraction of the expected closing
print would our flow be?* Expected flow ÷ (expected T-day volume x
auction share). Over 100% means the flow physically cannot clear in
one print at historical sizes — multi-day working or a bigger-than-
usual print, planned in advance either way.

**The shortlist probability** — when we predict "no change," we
still list the nearest candidates with probabilities: (chance ANY
change happens at this review type, from 11 years of history) x
(how visible the candidate universe is to our data) x (how close
this name is to the door). And we put the leftover probability on a
line called BELOW-FLOOR — the honest admission that some changes
come from parts of the market our data doesn't cover (13 of 21
recent Taiwan changes did).

## Part 3 — The one-breath versions

- *Index selection*: "Line everyone up by size, draw the line at
  85% coverage, high door in, low door out, big cleanups only in
  May and November."
- *Crowding*: "Daily short-selling balances tell us if the street
  is already positioned — and the crowd's exit, not the index flow,
  usually sets the closing price."
- *Our edge claim*: "Every number is computed from public data with
  the formula on the page, every prediction is graded afterward,
  and the misses ship with the hits."
