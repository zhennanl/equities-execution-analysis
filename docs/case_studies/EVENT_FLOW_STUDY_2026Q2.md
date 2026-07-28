# How Asia Index Rebalance Events Actually Traded — 2026 Q2, Real Data

*Session 7c. 21 real event-names across three 2026-Q2 review cycles (MSCI
Taiwan + Korea May SAIR; FTSE Taiwan 50 + China A50 June), fetched from
live market data, measured with `agents/event_flow_study.py`, and graded
for execution quality against the actual rebalance-day tape. Cache:
`data/event_flow_study.json` (re-runnable via
`scripts/fetch_event_flow.py`).*

---

## 1. How the flow built and printed (real, measured)

| Provider × side | n | T-day volume multiple | Pre-positioning (excess ADV-days A→T−1) | CAR drift into T | T-day return |
|---|---|---|---|---|---|
| **MSCI Sell** (Standard deletions) | 8 | **16.0× [7.1..38.1]** | **4.8 [0.2..23.9]** | **−4.3%** [−14..+7.6] | +2.1% |
| **FTSE Sell** (TW50/A50 deletions) | 6 | 5.5× [1.6..17.4] | 1.4 | +0.5% | +3.2% |
| **FTSE Buy** (TW50/A50 additions) | 7 | 1.4× [0.9..2.1] | 0.6 | +2.2% | +0.5% |

**Reading the table like a desk:**
- **MSCI Standard deletions are the crowded prints** — median 16× normal
  volume on T (THSR hit 38×), with ~5 ADV-days of excess volume already
  traded between announcement and T−1 and a median −4.3% drift: the
  pressure largely REALIZED BEFORE the effective date, and the close
  printed near the trough.
- **FTSE tradable-index events are milder** — deletions 5.5×, and the
  additions barely registered (1.4×) partly because the 2026 AI names'
  baseline volumes were already elevated (denominator inflation —
  disclosed) and A50 flow partially routes via futures/creation baskets.
- **Real close-auction concentration** (5-min bars, effective day):
  ordinary names ~3% in the closing bar (TSMC), the deleted China Steel
  6% / 12% in the last 3 bars — visible but modest at bar granularity
  (the TWSE 13:25–13:30 call sits inside the last bar; bar-level share
  understates the auction print itself — disclosed).

## 2. Execution quality vs the actual tape

Realized S1–S4 costs on each name's true path (η=0 — the tape already
contains the crowd's impact), graded against our ex-ante 6z rule
(adds→S3, deletes→S1):

| Group | Realized-best mix | Flat-rule median regret | Hit rate |
|---|---|---|---|
| FTSE Buy | **S4 6/7**, S3 1/7 | 754 bps | 14% |
| FTSE Sell | S1 3/6, S4 2, S3 1 | 177 bps | 50% |
| MSCI Sell | **S3 6/8**, S4 2/8 | 382 bps | 0% |

Two ex-ante mistakes, both now understood:
1. **Deletions: don't sell the trough.** The 6z rule said "sellers ride
   the pressure — 100% MOC." True for FTSE's milder prints; WRONG for
   MSCI deletions, where the pressure had already realized into T
   (−4.3% drift) and the effective close was near the low — names
   *bounced* after, so partial-MOC + post-effective completion (S3) sold
   the recovery. The Chen-Noronha-Singal deletion-reversal asymmetry,
   rediscovered by the grading loop.
2. **Additions in a momentum tape: waiting cost real money.** Every
   2026-Q2 add kept rallying; announcement-anchored buying (S4) won 6/7
   and S3's post-effective purchases paid up day after day (GigaDevice
   regret 2,773 bps). This is regime-dependent — one AI-bull quarter —
   and S4 carries the highest tracking, so it applies only within the
   client's tolerance.

## 3. The metrics that guide trading (the deliverable)

1. **Provider × side → expected T-multiple** (MOC sizing): MSCI Standard
   deletion ≈ 16×, FTSE tradable deletion ≈ 5×, additions ≈ 1.5×. The
   auction can absorb enormous deletion size on MSCI days; add-side MOC
   capacity is far smaller than folklore suggests.
2. **CAR drift into T → the sell-side strategy switch**: pressure already
   realized (drift ≤ −3%, or MSCI Standard deletion) ⇒ do NOT dump at the
   close; split with post-effective completion. Mild prints ⇒ S1 rides
   the crowd.
3. **Pre-excess ADV-days → how much the arb already did** (5 ADV-days on
   MSCI deletes = the crowding happened before you arrived).
4. **Momentum regime (pre-event drift ≥ +5%) → shift add-side weight
   earlier**, tracking tolerance permitting.
5. **Close-bar share** as the real (not folklore) auction-capacity input.

Encoded as `refined_rule(side, provider, drift)` — re-graded on the same
21 events: **median regret 355 → 0 bps** (MSCI sells 382→0 with 75% hit
rate; FTSE buys 754→0 with 57%). **In-sample by construction** — fitted
and graded on the same quarter; the honest claim is direction, not level,
and the validation date is the next review cycle (Aug/Sep 2026), where
the rule runs frozen.

## 4. Honest boundaries

n=21 names from ONE quarter of a momentum bull market — the add-side
finding especially is regime-conditional. Grading uses the stylized
S1–S4 schedules (50/50 splits), not continuous optimization. η=0 realized
costs exclude our own hypothetical impact (a real tracker's flow IS part
of these prints). Announcement rel-days approximated per cycle. A50's
effective-open convention mapped to the prior close (disclosed).
Denominator inflation on T-multiples where baseline volume was already
event-elevated. All raw metrics per name preserved in the cache for
re-analysis.

## 5. What this closes

The loop the desk actually runs, now demonstrated end-to-end on real
data: **predict the changes (5 graded backtests) → size the flow
(index_flow) → study how past events traded (this) → derive conditioned
execution rules (refined_rule) → grade execution quality against the
actual tape (grading loop) → freeze and validate next cycle.** Every
piece is code, every claim carries its sample size, and the biggest
number in the study — 2,773 bps of regret from buying an AI runner too
late — is an argument about regimes, not a promise.


---

## Addendum (session 7d) — positioning trajectories: A-day to T-day, day by day

New functions: `positioning_trajectory` (per-name daily build curve with
shape classification) and `aggregate_trajectories` (median build curve on
a normalized announcement→effective clock). Run on the same 20 real
event-names (NanYaPCB excluded: no excess volume in window).

### The build curves (median fraction of event-window excess volume traded)

| Group | n | by 25% of window | by 50% | by 75% | by 90% | T-day share | Shape mix |
|---|---|---|---|---|---|---|---|
| **MSCI Sell** | 8 | 4% | 4% | 14% | 22% | **78%** | 6 back-loaded, 2 steady |
| **FTSE TW50/A50 Sell** | 6 | 6% | 18% | 33% | 42% | 64% | 3 back-loaded, 3 steady |
| **FTSE Buy** | 6 | 28% | 48% | 60% | 72% | 28% | 3 front-loaded, 2 back, 1 steady |

Sharpest single split: **A50 additions were half-done 9–11 trading days
before the effective date** (T-day share 0–23%) while **MSCI deletions
printed 78% of their event volume ON the effective day** (SK Biopharm
99%, Compermed 100%).

### The finding that reconciles the whole study

**MSCI deletions: volume back-loaded, price front-loaded.** By 90% of
the window only ~22% of excess volume had traded — yet the median CAR
drift into T was −4.3%. The mechanism, now measured from two independent
angles: *arbitrage moved the price early on thin volume; the trackers
printed the mass at T into an already-depressed close; the overshoot
bounced.* That's exactly why S3 beat S1 for these names — and the
positioning trajectory is the ex-ante tell: when the price has moved but
the volume hasn't, the print will be crowded AND mispriced.

### Trading translation (what the trajectory adds to the toolkit)

- **MSCI deletion profile** (price early / volume at T): the T-print is
  deep — size MOC generously — but it prints at the trough; complete the
  residual after (S3). Watch metric: drift-without-volume divergence.
- **A50 addition profile** (everything early): the event has largely
  traded before T — do not plan around a closing print that isn't
  coming; trade WITH the early flow window (the S4 result restated in
  volume terms).
- **TW50 profile** (intermediate): genuine T-day auction events with
  moderate pre-build — the classic frontier trade-off applies.
- The **shape classifier** (FRONT/STEADY/BACK + half-build day + T-day
  share) is now a standing per-event diagnostic: run it live during the
  A→T window of the NEXT review and compare against these templates to
  see which regime you're in while there is still time to adapt.

Honest boundaries: same 20-name/one-quarter sample; volume-based build
cannot attribute WHO (arb vs tracker vs noise) — the price/volume
divergence is inference, not identification; A50 effective-open
convention as before.


---

## Addendum (session 7e) — the WHO limitation, solved with real investor data

The 7d limitation: volume-based build curves cannot attribute WHO. For
Taiwan, attribution needs no inference — TWSE publishes **daily
per-stock institutional flows** (foreign investors / investment trusts /
dealers). New module `agents/investor_flow.py` (fetcher + parser +
`handoff_metrics`); 22 trading days cached across both event windows
(`data/twse_institutional.json`, one API call per day covers all stocks).

### FTSE Taiwan 50, June 18 — the arb→tracker handoff, measured: 8/8

Domestic investment trusts ARE the tracker complex (0050/006208). On the
effective day, for **every one of the 8 event names**, trusts traded the
index direction while foreigners took the other side:

| Name | Side | T-day trusts | T-day foreign | Handoff |
|---|---|---|---|---|
| GUC / BizLink / NanYaPCB / ZhenDing (adds) | Buy | **+2.1M / +3.9M / +4.8M / +19.7M** | −2.5M / −4.4M / −5.8M / −18.1M | ✓✓✓✓ |
| ChinaSteel / FormosaPl / Hotai / Compermed (deletes) | Sell | **−286M / −107M / −7.1M / −24.9M** | +320M / +142M / +7.7M / +25.5M | ✓✓✓✓ |

And the pre-window shows the arb setup: foreigners were net SHORT the
deletions before T (ChinaSteel −17.9M pre-T) and covered into the
tracker's print — short early, buy the crowded close from the tracker,
textbook and now measured.

### The flow simulation, independently validated

Our 6z simulation predicted TSMC's reweight trim at **−$440M** (on the
$70B lower-bound AUM). The real June-18 data: **investment trusts net
sold 7.27M TSMC shares ≈ $580M** — right order, right day, right
direction, right investor type. The reweight leg ("the flow nobody talks
about") is real and now measured.

### MSCI May 29 — and the residual limitation, honestly stated

Foreign flow (which CONTAINS the MSCI trackers) sold heavily pre-T
(AsiaCement −62M, THSR −62M, ChinaAirlines −41M shares) and was small/
positive ON T despite 16–38× volume prints — because MSCI events net out
INSIDE the foreign category: foreign trackers selling vs foreign arbs
short-covering cancel in the net. Within-category attribution needs the
borrow/SBL data (also published daily by TWSE — the next layer, same
pattern). One true anomaly kept: Compal's deletion was absorbed by
foreign BUYING throughout (+71M pre, +77M on T) — matching its outlier
positive drift in the price study; flagged, not explained.

### What this closes and what remains

Closed: WHO, for domestic-tracker events (FTSE TW50) — handoff 8/8, and
the tracker leg of the flow simulation graded against reality. Remaining:
within-foreign netting for MSCI events (fix: daily SBL short-balance
overlay, same fetch pattern); Korea/Japan analogues (KRX investor-type
data exists; JPX weekly only); one-quarter sample as before.

Trading translation: the handoff is the mechanism behind both refined
rules — for adds, the tracker WILL be there at T buying from whoever
pre-positioned (the print is a liquidity event you can plan around);
for MSCI-style deletions, the visible net flow understates the two-way
crowding, which is exactly why the print is deep AND mispriced.


---

## Addendum (session 7f) — investor-flow attribution extended to other markets

`agents/investor_flow.py` is now a **multi-market registry**
(`INVESTOR_FLOW_COVERAGE`) with three implemented fetchers and honest
status labels for the rest:

| Market | Dataset | Granularity | Status |
|---|---|---|---|
| Taiwan (TWSE) | T86 daily foreign/trust/dealer | per-stock daily | **implemented** |
| Taiwan (TPEx) | Same trio for OTC names | per-stock daily | **implemented** |
| Korea (KRX) | Foreign + institution nets (KRX data; Naver mirror for research — desk uses KRX/KOSCOM feed, disclosed) | per-stock daily | **implemented** |
| Japan (TSE) | Investor-type flows | market-wide, WEEKLY only | aggregate only |
| Japan (TSE) | Short positions ≥0.2% | per-holder daily | protocol (short side) |
| Hong Kong | CCASS participant shareholding | per-stock **per-participant** daily | protocol |
| China-A | Northbound Connect holdings via CCASS | per-stock daily | protocol |
| Indonesia | Foreign vs domestic | per-stock daily | roadmap |
| Thailand / India | Investor-type / FII-DII | market-wide daily (+deals) | aggregate only |

### Korea — the three MSCI deletions (May 29, full 15-day window)

| Name | pre-T foreign | pre-T institution | T-day foreign | T-day institution |
|---|---|---|---|---|
| Hanjin KAL | +3.3k | −60.3k | **+10.0k** | −8.5k |
| HD Marine | +16.0k | −54.1k | **+10.7k** | −17.4k |
| SK Biopharm | +14.2k | −15.6k | **−34.2k** | −36.4k |

Two of three deletions show **positive foreign nets on the deletion
print** — the within-foreign netting signature from Taiwan replicating in
Korea (foreign trackers selling vs foreign arbs covering cancel inside
the category), with SK Biopharm the clean tracker-sell case (both
foreign and institutions selling into its 99%-back-loaded print).
Cross-market replication of the netting signature is itself a finding:
it is a property of MSCI events, not of Taiwanese data.

### MPI on TPEx — the missing add, finally attributed

MPI (6223, TPEx-listed — invisible to all our earlier TWSE-based
analysis) on its MSCI-add effective day, May 29: **investment trusts
+26,014 vs foreign −26,033 — an almost share-for-share handoff print**,
the same signature as all eight TW50 names. Post-event (Jun 1) trusts
dumped −243k — post-inclusion domestic profit-taking, flagged not
explained.

### Integration state

The framework now attributes investor-type flow in the three markets
where per-stock daily data exists and says plainly where it doesn't
(Japan's weekly aggregates cannot do this analysis — a data-boundary
fact worth stating in an interview). HK/China CCASS participant-level
data is the identified next fetcher: per-BROKER granularity would
upgrade attribution beyond investor type to custodian flow — the closest
public data gets to a desk's own view.
