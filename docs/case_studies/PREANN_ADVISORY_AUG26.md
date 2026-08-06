# Pre-Announcement Advisory — Aug-2026 (T-6): the Three Questions, Answered Per Name

*Session 9i (2026-08-05). Once Step 1 finalizes the candidate
list, the three advisory questions (which changes / what the
close looks like / deviate from MOC?) become computable PER NAME
before the announcement. Data: data/preann_advisory_aug26.json
(λ-model forced flow, TWSE borrow balances fetched live, foreign
trends, squeeze precursors).*

## Q1 — Which changes are coming (the finalized list)

Adds: **2408 Nanya — SHADOW CALL, STRONG** (frame-robust
1.71–2.84× the bar, all gates pass on real floats); 2344/8046
frame-sensitive (declared, not called). Deletes: the pool
(deepest 6919 0.73×, 2834/2609 0.81×, 1101 0.84×, …), CADENCE-
GATED: August is quarterly, sweep not armed — pool = November
watchlist carrying ~2/3 eventual conversion; blind band declared.

## Q2 — What the close will look like (per name, computed T-6)

**Print forecasts are RANGES, built from four methods** (c-61 —
point estimates on a fat-tailed quantity are false precision):

- **M1 Structural band** — λ-quartiles × float-days. The passive-
  ownership ratio fitted on 77 historical deletions is not one
  number but a distribution (p25 0.074 / median 0.093 / p75
  0.117); the band carries that fit uncertainty. (The λ-model is
  our measured version of academic Benchmarking Intensity; the
  shares÷ADV "days-to-trade" convention is the institutional
  standard in rebalance planning.)
- **M2 Matched peers** — historical deletions with float-days
  within 0.5–2× of this name: their realized print quartiles.
  Pure empiricism, no model. (For additions, class peers are
  reported as CONTEXT only — historical adds were far less liquid
  names and would import their illiquidity into the range.)
- **M3 Scenario overlay** — the structural median scaled by the
  decade panel's crowding multipliers (quiet 0.64× / base 1.0× /
  crowded 1.64×). The scenario RESOLVES during the window via the
  Step-2 daily tracker — this is where "allow for different
  possible scenarios" lives operationally.
- **M4 Holdings floor (cross-check)** — observable fund-holding
  quantities × the May-2026 auction calibration (0.77–1.25),
  where holdings are visible.

Ensemble range = the union of method bands. Aug-2026 results:

| Name | Side | PRINT RANGE (×ADV) | M1 band | M2 peers | M3 quiet/base/crowded |
|---|---|---|---|---|---|
| 2408 | add | **1.0–1.8×** | 0.9/1.1/1.4 | context only | 0.7/1.1/1.8 |
| 6919 | del | 10.9–23.4× | 10.9/13.8/17.3 | 12.9/18.6/23.4 | 8.8/13.8/22.6 |
| 2834 | del | **15.7–34.9×** | 16.9/21.3/26.8 | 15.7/22.7/27.6 | 13.6/21.3/34.9 |
| 1101 | del | **15.0–31.5×** | 15.2/19.2/24.1 | 15.0/22.3/26.8 | 12.3/19.2/31.5 |
| 2609 | del | 7.4–15.8× | 7.4/9.4/11.8 | 7.8/12.7/15.8 | 6.0/9.4/15.4 |
| 5871 | del | 8.6–18.8× | 8.6/10.8/13.6 | 10.5/14.2/18.8 | 6.9/10.8/17.7 |

How a trader reads it: the LOW end is a quiet, well-telegraphed
print; the HIGH end is the crowded scenario; the methods agreeing
tightly (2609) means high confidence, methods diverging (3529:
structural 6× vs peers 10.5×) means the name trades unlike its
size class — flagged, not averaged away.

| Name | Side | Forced flow (λ·float) | Expected print | Standing borrow | Foreign 12m | Squeeze precursor |
|---|---|---|---|---|---|---|
| 2408 | add | 131M sh | **1.1× ADV** | 0.7 ADV-days | +2.5pp | no |
| 2344 | add | 289M sh | 1.4× | 0.7 | +3.7pp | no |
| 6919 | del | 97M sh | 13.8× | 1.4 | +3.8pp | **yes** |
| 2834 | del | 847M sh | **21.4×** | 7.4 | +0.8pp | no |
| 2609 | del | 261M sh | 9.4× | 2.7 | **+5.5pp** | **yes** |
| 1101 | del | 603M sh | **19.2×** | **18.7 ADV-days** | −4.0pp | **yes** |
| 3529 | del | 5M sh | 5.9× | n/a | +6.0pp | **yes** |
| 5871 | del | 122M sh | 10.8× | 8.5 | +3.0pp | **yes** |
| 3533 | del | 8M sh | 6.1× | 0.9 | **+10.4pp** | **yes** |

Readings worth a client call: **2408's inclusion trade is
EASY** — the rally that qualified it exploded its ADV to 118M
shares, so the entire forced buy is ~1.1 normal days: minimal
impact expected, auction share likely modest (add range 30–50%).
**1101 is pre-positioned to the gills BEFORE any announcement**:
586M shares on loan = 18.7 ADV-days, foreigners −4pp — the market
is structurally short the perennial cutline name; if deleted, the
print is heavy (19×) but heavily pre-sold; if RETAINED (as it was
in May), the standing short is squeeze fuel. **2609/3529/3533
carry the Compal signature precursor** — foreign accumulation
INTO deletion candidates (+5.5/+6.0/+10.4pp): if any is deleted
in November, watch H16 from announcement day one.

## Q3 — Should a flexible client deviate from MOC? (the decision framework)

Pre-announcement the advice is CONDITIONAL — finalized by the
window data itself: (1) TRACKERS: never deviate — the close is
the benchmark (and for 2408-class easy adds, the close will be
clean). (2) FLEXIBLE clients: deviation pays only in identified
cells — decade evidence: playbook splits beat all-MOC on average
(−112bps) with the gains concentrated where Step-2 flags
OVERCROWDED, and the deferred leg pays when the compound
signature (completion ≥1.5 + wrong-way foreign, H16) fires — the
Compal case (+590bps class). UNDERSUPPLIED names (thin
pre-positioning) argue the opposite deviation: start early,
spread. Rule of engagement: the card ships conditional at
announcement ("IF the window shows X by T-3, split Y"), and the
Step-2 daily tracker migrates it. (3) The desk's own
guaranteed-close book (where offered): the squeeze-precursor
column IS the risk-pricing input — 1101's 18.7 ADV-days of
borrow is visible, free, daily.

## The general recipe (any event, any market)

Step 1 list → per name: λ-model forced flow (shares × float ×
λ ÷ ADV), auction-share prior by side, standing borrow in
ADV-days, foreign 12-month trend, squeeze-precursor flag →
archetype-conditional advice, finalized by the Step-2 tracker
from announcement day. Everything above ran from held caches +
one live TWSE day-file; the sentinel watchlist now needs the
candidate names added so borrow series accumulate daily.
