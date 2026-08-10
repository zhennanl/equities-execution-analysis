# Taiwan Market Analysis — The Living Reference

*Started session 8u (2026-07-29). Taiwan is this project's deepest
market: the full lifecycle has been run end-to-end on it, its data
infrastructure is the richest we have built, and the retrospective
engine is about to sweep a decade of its reviews. This file is the
single home for everything Taiwan-specific — background stories,
data infrastructure, mechanics, measured numbers, and the case-study
index. Sections are added as work lands.*

---

## 1. Why the lookback starts at 2015 — the background story

### How the boundary was found

When we set out to run the index-review framework retrospectively,
the question was not "how far back does data exist?" but "how far
back does EVERY layer of the analysis exist simultaneously?" A
five-layer replication — predictions, flows, crowding, auction
microstructure, grading — is only as deep as its shallowest input.
So we probed each pillar at successively older dates, live, against
TWSE's official endpoints:

| Pillar | Endpoint | Probed depth | Constraint type |
|---|---|---|---|
| Outcome lists (answer keys) | MSCI/FTSE public announcements | 10+ years | never binding |
| Daily quotes, all stocks | MI_INDEX (ALLBUT0999) | 2023 verified, ~2004+ by design | not binding |
| Market/auction stats | MI_5MINS / MI_5MINS_INDEX | file from **2004-10-15**; but **5-SECOND grid only from 2014-12-29** (c-228) | **binds auction PATH studies at 2014-12-29** — the real 2015 boundary |
| Short balances (margin + SBL) | TWT93U | **PUBLISHED FROM 2005-07-01 by TWSE (c-226)**; we harvest from 2015 by choice | binds nothing — the binding layer is our float/share VINTAGE |
| Foreign per-stock net flows | TWT38U | **PUBLISHED FROM 2004-12-17 by TWSE (c-226)**; harvested from 2015 by choice | as above |
| Per-name intraday | (none free, historical) | 60-day wall | forward archive only |

The crowding layer binds everything. TWT93U — the daily per-stock
margin-short and SBL balance file our entire positioning read is
built on — serves data from 2015; so does TWT38U's foreign-flow
file. Everything the framework does with positioning (crowding
bands, the CONSENSUS/UNPRICED overlay, the EXITING tag, the
discretion matrix, the reversal grading) therefore cannot reach
further back than the short ledger does.

**THE AUCTION LAYER IS THE REAL 2015 BOUNDARY (c-228).** TWSE
serves MI_5MINS from 2004-10-15, but the `notes` field returned WITH
every response says the RESOLUTION changed four times:

| period | grid |
|---|---|
| before 2011-01-16 | every **minute** |
| 2011-01-16 .. 2014-02-23 | every **15 seconds** |
| 2014-02-24 .. 2014-12-28 | every **10 seconds** |
| **from 2014-12-29** | every **5 seconds** |

Source: the `notes` array of
https://www.twse.com.tw/en/exchangeReport/MI_5MINS?response=json&date=20050415
(page start date: https://www.twse.com.tw/zh/trading/historical/mi-5mins.html
— 「本資訊自民國93年10月15日起開始提供」).

The closing call runs 13:25-13:30. Five minutes on a 1-minute grid is
FIVE points; on a 5-second grid it is sixty. The indicative path
through the auction — the object of an auction study — exists only
from **2014-12-29**. The auction SHARE (final print minus the last
continuous row) survives a coarser grid and reaches 2004.

So: 5-second auction studies are 2015-bound in the way that matters,
and every conclusion drawn from an auction PATH must be dated
2014-12-29 or later.

### Why 2015 — CORRECTED at c-226

**The regulatory backstory below is WRONG and is kept only so the
correction has something to point at.** TWSE publishes the start date on each report page itself:

* TWT93U 融券借券賣出餘額 — 「本資訊自民國94年7月1日起開始提供」
  = **2005-07-01**
  https://www.twse.com.tw/zh/trading/margin/twt93u.html
* TWT38U 外資及陸資買賣超彙總表 — 「本資訊自民國93年12月17日起
  開始提供」 = **2004-12-17**
  https://www.twse.com.tw/zh/trading/foreign/twt38u.html

Both files predate our start by a decade. 2015 is where WE start,
for the good reason that it matches the MSCI key archive — not
where the exchange starts. Do not repeat the paragraph that
follows.

### (SUPERSEDED) Why 2015 specifically — the regulatory backstory

The date is not an accident of server retention. Taiwan's modern
short-sale data regime is a product of the mid-2010s liberalization
wave: the TWSE progressively relaxed short-sale restrictions
(uptick-rule scope, SBL quota expansion) and widened day-trading
eligibility through 2013-2014, and the disclosure infrastructure
that publishes daily per-stock short balances in today's format
dates from that period. Before it, short interest existed but was
not published at this granularity and cadence — so the pre-2015
positioning read is not merely unfetched, it is UNRECORDED in the
form our engine consumes. No institutional data purchase fixes
that; the desk's own history is the only deeper source, and only
for its own flow.

### The precise honesty qualifications

**2015 is verified-at, not proven-first.** We probed 2015-05-15 and
it served (895 names); we have not binary-searched the true floor,
which may sit somewhat earlier. The claim we stand behind is "the
full stack runs from 2015"; the claim we do not make is "it cannot
run from 2013."
*(Session 9i re-probe: the floor IS deeper — TWT93U served
2015-01-05 (885 rows), 2014-12-15 (884), 2014-06-16 (870), and
TWT38U OK on all three. 2015 remains the working convention —
aligned with the MSCI key archive and the regulatory-regime story —
with verified margin beneath it.)*

**Partial stacks go deeper, and that is useful.** Analyses that need
only daily data — T-day volume multiples, front-run drift, reversal
fractions, flow validation — run to ~2005: the event LIBRARY can
grow far past 2015 even though the crowding-conditioned analyses
cannot. Market-wide auction studies (value share of the print, the
index auction gap, book-withdrawal behavior) run from 2012 at
15-second resolution and from 2014-12-29 at 5-second — see the
c-228 table below. Only
the complete predict-position-execute-grade replication is
2015-bound.

**What 2015 buys us.** Roughly 40 MSCI/FTSE review cycles at full
fidelity: enough to re-estimate every prior the packs quote —
T-multiples per side and liquidity tier, the crowding-vs-reversal
relationship that calibrates the discretion matrix, auction-share
uplifts, false-flag base rates at the cutline — on samples in the
hundreds instead of n=8. That is the difference between "measured
on the events we watched" and "estimated on a decade," and it is
the direct payoff of finding where the boundary sits and why.

---

## 2. Data infrastructure (to be extended)

The official TWSE backfill layer (`scripts/backfill_tw_history.py`;
incremental caches in `data/tw_history/`): all-stock daily quotes,
short balances, foreign flows — plus the 5-second market archive
(`MI_5MINS`, `MI_5MINS_INDEX`) and the live crowding/TPEx fetchers.
Full source map and probe log: AUCTION_STUDY_2026.md,
REPRO_FEB2026_TW.md.

## 3. Market mechanics (to be extended)

Close: 13:25-13:30 call auction, indicative price/volume broadcast
every ~5s (best transparency in Asia), ±10% daily bands (LOCK RISK
class), order-rest from 13:25. Measured event behavior: ~25-30%
close-auction share on normal days, 24.9%-of-market-value print on
the May-29 effective day, −41 bps index auction gap, ~14% book
withdrawal vs ~24% baseline. Reference: CLOSING_AUCTIONS_ASIA.md,
TW_AUCTION_DEEP_DIVE_MAY29.md.

## 4. Case-study index (to be extended)

- LIFECYCLE_E2E_MAY2026_TW.md — the capstone Steps 1-4 chain
- PIT_MAY2026_TAIWAN.md / PIT_MAY2026_ALL_ASIA.md — prediction
  replication (TW 7/7 + MPI)
- WINDOW_REPLAY_MAY2026.md — the daily loop (2 flips, both correct)
- TW_AUCTION_DEEP_DIVE_MAY29.md — the auction, characterized
- REPRO_FEB2026_TW.md — first retrospective run on official data
- EXECUTION_INSIGHTS_DEMO_MAY2026.md — Step-4 grading
- PITCH_PACK_TW50_Jun2026.md — the graded FTSE pitch

## 4b. MSCI vs FTSE — which index matters more for Taiwan

**For an international PT desk: MSCI, by a wide margin.** The
evidence is our own measurements, not opinion:

- **Flow per event:** MSCI deletions print median **16x ADV (max
  38x)**; FTSE-class events ~2-5x (June TW50 adds ran 1.0-2.3x
  daily multiples even while dominating their auctions). The May-26
  MSCI effective day put **25% of the whole market's value through
  one print** and moved the TAIEX **−41 bps inside the auction** —
  no TW50 review does that.
- **Why:** MSCI Taiwan sits inside MSCI EM (~18-20% country
  weight), EM Asia, ACWI, and country funds — a stack of GLOBAL
  passive AUM. The TW50 is tracked by the domestic 0050/006208
  retail-ETF complex and local pensions.
- **Whose flow:** MSCI flow is foreign-institutional — the client
  base an international desk serves, and the channel TWT38U
  watches. TW50 flow executes largely through domestic brokers
  (the routing principle: flow reaches an international desk in
  proportion to foreign ownership of the tracking AUM).

**But the TW50 earns its second place, three ways:** (1) the
retail ETF boom made 0050 enormous — TW50 reviews move real money
quarterly (measured: 44-71% auction shares on the June adds);
(2) the **TSMC reweight leg** — the 30% single-stock cap forces
quarterly TSMC flow (TSMC printed 55% auction share on Jun 18: the
"control" that wasn't); (3) TW50 changes often PREVIEW MSCI
changes (the June AI-quartet -> Aug MSCI story).

**Precision note:** "FTSE" in Taiwan is two things — FTSE GEIS
(global, foreign-tracked, smaller than MSCI here) and the
co-branded FTSE TWSE Taiwan 50 (domestic). Priority order for the
desk: **MSCI >> TW50 > FTSE GEIS** — the same order as our data
infrastructure: MSCI keys solved to 2015, TW50 collection queued,
GEIS behind both.

## 4c. Replicating the Taiwan pillars elsewhere with CLSA data

*(Session 8z. Question: with institutional access, do Taiwan's four
data pillars generalize — and does the analysis therefore
replicate? Answer: three pillars solve and UPGRADE; one is
structural. Full table: APAC_DATA_AVAILABILITY.md coda.)*

- **Daily shorts → SOLVED, UPGRADED.** Securities-finance data
  (Markit/S3-class, standard on any prime/SBL desk): daily borrow
  quantity, utilization, and **FEES** per stock, all markets, years
  deep. Fees are a PRICE signal for crowding — strictly richer than
  Taiwan's quantity-only TWT93U.
- **Auction archive → SOLVED, UPGRADED.** Commercial tick history
  (LSEG/BMLL/exchange data shops): every auction print with
  condition codes and imbalance feeds, per name, decades. The
  violence curve grows from 17 points to thousands.
- **Per-stock foreign flow → STRUCTURAL, money can't buy it.**
  TWT38U exists because Taiwan's ID regime RECORDS it. Analogs
  exist where structure does: Korea (ID regime), Thailand (NVDR),
  China (Connect), HK (CCASS custody). Japan/Singapore/Australia
  never record it — weekly aggregates at best; no vendor sells
  what markets don't capture.
- **Ownership brackets → partial.** CCASS is HK's genuine TDCC
  analog; fund-holdings databases are the coarser proxy elsewhere.

**Replication verdict:** with desk data the full five-layer Taiwan
study replicates COMPLETELY in Korea, Hong Kong, and China; near-
completely in Japan (flow pillar degrades to weekly aggregates —
stated, and borrow FEES partially substitute as the positioning
signal); elsewhere prediction/flows/auction replicate fully and
positioning runs on securities-finance data. Methods transfer
unchanged — the free-data builds are the running proof, so on the
desk replication is data onboarding, not a research project.

## 4d. China A vs Taiwan — the detailed comparison (session 9i)

*(Expands the APAC ranking's one-liner: "China A, score 8 — the only
market that beats Taiwan on a pillar; crowding pillar economically
thin." Every claim below ties to a probe or measurement in this
project.)*

### The data pillars, head to head

| Pillar | Taiwan | China A | Verdict |
|---|---|---|---|
| Per-name intraday history | The one TW weakness: free walls (yfinance 60d); 5s MARKET archive but not per-name bars | **Years of per-name 5-MINUTE bars via Baostock, official-grade** — our CN auction/violence work ran on it | **CN wins — the only pillar anywhere that beats TW** |
| Daily shorts / borrow | TWT93U: daily SBL balance + quota per name, 2015+ | No real analog: short supply via 融资融券 margin-lending is thin, borrow scarce/expensive, disclosure aggregate | TW wins decisively |
| Per-stock foreign flow | TWT38U daily per-name foreign net, 2015+ (ID regime records it) | Northbound Connect: per-name HOLDINGS via HKEX/CCASS snapshots (level, not daily net flow; coverage = Connect-eligible only) | TW wins; CN partial |
| Auction transparency | Indicative price/volume broadcast every 5s, 13:25-13:30, archived 2012+ | Close call 14:57-15:00 (SZSE since 2006, SSE since 2018-08); real-time virtual match price exists on terminals but NO public deep archive found in our probes | TW wins |
| All-stock daily official | MI_INDEX/STOCK_DAY to 2016+ (value/vol = exact VWAP) | Baostock daily deep, official-grade, incl. amount (exact VWAP equally computable) | Tie |
| Ownership structure | TDCC brackets weekly | Top-10 holders quarterly, fund holdings semi-annual; CCASS for Connect custody | TW wins |

### Market structure differences that change execution

- **Session & close**: TW 09:00-13:30, single close call with a
  five-minute broadcast window — the whole day funnels into one
  transparent print. CN 09:30-11:30/13:00-15:00 with a 3-minute
  close call — shorter, less broadcast, and the lunch break splits
  liquidity. TW's close is ~25% of the day's value on event days
  (measured May-29); CN close concentration is structurally lower.
- **Bands**: both ±10% mainboard, but CN runs ±20% on ChiNext/STAR
  and ±5% ST names — band-lock physics vary by board. TW is uniform
  ±10% with the tick-rounding rules we've encoded exactly.
- **Settlement/turnover regime**: CN A-shares are T+1 for shares (no
  same-day round trip) with stamp 0.05% on sells; TW allows day
  trading (with restrictions) and taxes sells 0.30%. T+1 dampens
  intraday mean-reversion capital in CN.
- **Who's on the tape**: both retail-heavy, but CN more so at the
  margin (retail ~60% of turnover vs TW's high-but-declining retail
  share, foreign ~40% of TW HOLDINGS). The consequence we measured:
  **only ~25% of CN MSCI name-events print materially (T-mult >= 2;
  excluded median ~1.1)** versus TW event prints of 5-38x. At
  10-20% inclusion factors, MSCI flow rarely dominates an A-share
  tape that trades enormous baseline volume.
- **Access**: TW is an ID market (foreign-investor registration,
  the reason TWT38U exists); CN is quota-free Connect for eligible
  names (eligibility = our alias-bridge master) plus QFII for the
  rest. Both create desk-sellable access advisory; CN's
  eligibility-churn adds a monitoring product TW lacks.

### Index-event physics, measured

- **TW**: the event dominates the tape. FTSE ~5x prints, MSCI
  16-38x deletes; window drift +329bps adds; auction shares 44-71%;
  the per-name execution edge (class-conditional playbooks,
  limit-lock cases 6919/2344) is large and sellable.
- **CN**: decade adds GRIND UP like TW (drift +391, LINEAR −234 —
  the 9h revision that demoted the May-2026 pop-decay to a
  hypothesis), deletes ~flat; but the per-name edge is THIN outside
  the big inclusion waves because the prints are small. The 2019-21
  inclusion-factor step-ups were the golden era; today the CN edge
  is more portfolio-level (cohort timing) than name-level.
- **Crowding mechanism differs structurally**: TW crowding =
  measurable SHORT BUILDS into deletes (TWT93U daily) — arbs
  pre-position and their covering sets the print (case 6919). CN
  crowding can't run through shorts (borrow thin, expensive) — it
  runs through LONG unwinds, margin-balance swings, and index
  futures basis. That's why the pillar is "economically thin":
  not just unmeasurable, but the MECHANISM our TW discretion
  matrix keys on (short-build bands) barely operates. A CN
  discretion matrix would need different inputs: northbound
  holding deltas, margin balances, futures basis — all coarser.

### What this means for a PT desk

Taiwan is where per-name event execution judgment is worth the most
and is most measurable — the desk sells auction quality, discretion,
and graded predictions. China A is where the desk sells ACCESS AND
SCALE — Connect mechanics, eligibility monitoring, T+1/settlement
choreography, RMB FX handling, and portfolio-level event timing —
while per-name heroics matter less because the tape swallows the
flow. Same lifecycle, same engines, different product emphasis: the
TW demo leads with the discretion matrix; the CN demo should lead
with the materiality screen ("which 25% of this cohort will actually
print — concentrate attention there") — itself a finding only our
decade panel can support.

## 5. The retrospective sweep (first slice complete)

**First slice run (session 8u): 2025-2026, 4 MSCI events** —
BACKTEST_TW_2025_2026.md. Delivered: a validated event-print
detector for answer-key reconstruction (recall 4/4+7/7, precision
rules iterated honestly incl. one out-of-sample rejection); the
REVIEW-CADENCE rule (migration sweeps are SAIR business — 10 false
QIR deletions -> 0); and the HAZARD finding (Nov-25 flag cohort:
6/9 deleted at the next SAIR, 3/9 persistent cutline residents —
deletion calls are formally hazard-ranked now). Full logic
decomposition: PREDICTION_LOGIC_LAYERS.md (L0-L9).

**THE ANSWER-KEY PROBLEM IS SOLVED FOR MSCI (session 8v).**
Archaeology via the Wayback CDX index found MSCI's own archives
still serving, with uniform naming:

- **Full Standard-index public lists** (the per-country change
  tables our ledger parser reads natively):
  `msci.com/eqb/gimi/stdindex/MSCI_{Feb|May|Aug|Nov}{YY}_STPublicList.pdf`
  — **all 44 quarters 2015-2025 downloaded, 44/44 parse clean**:
  123 Taiwan changes (56 adds, 67 deletes) now keyed, and every
  OTHER country's sections came with them. CDX shows the class
  reaches back to 2003.
- **Review press releases** (counts + largest names):
  `app2.msci.com/eqb/pressreleases/archive/MSCI_{season}{YY}_QIRPR.pdf`,
  2005-2025, all 44 of 2015-2025 downloaded.
- Cache: `data/msci_archive/` (88 PDFs + txt);
  fetcher: `scripts/fetch_msci_archive.py`.

**FTSE: SOLVED (session 8x)** — the browser-assisted path worked
same-day: the Chrome extension rendered TIP's client-side archive,
revealed numeric SSR detail pages, and the sandbox enumerated all
~460 → **41 keyed events, 100 TW50 changes, 2016-11→2026-06, with
reserve lists and per-event sources** (data/ftse_tw50_changes.json;
case study FTSE_TW50_KEYS.md; validated against our measured June
prints and holiday-shifted eff dates). Remaining gap: 7 pre-TIP
quarters 2015-2016Q3 — **four recovery routes probed same session,
all dead ends, recorded:** (1) TWSE press-release archive: the
search UI reaches 2000 but this content class isn't carried there
(only ETF marketing matched); (2) old ftse.com Constituents.jsp:
Wayback snapshots bracket every 2015 quarter BUT the page 302'd to
PageNotFound from Feb-2015 onward — dead before our window;
(3) Yuanta 0050 holdings: the 2015 site was an SPA; its archived
api/Composition endpoint has one useless HTML-wrapped snapshot;
(4) TWSE monthly-journal page: client-side shell. **Viable paths
left (browser-led, bounded):** the 證交資料月刊 PDF archive
(publications section navigation) and 2015 financial-press coverage
of the four reviews. Impact note: MSCI's 2015 keys EXIST (incl.
Taiwan's 17-deletion year), so 2015 backtesting proceeds on the
dominant provider regardless — FTSE 2015 only completes the
rank-game series. The original
evaluation below is kept for the record:

*(superseded evaluation, session 8w)* Why FTSE resists what MSCI yielded:

1. **No uniform document archive.** MSCI kept one document class
   (STPublicList) at guessable URLs on a still-live legacy server
   for 20+ years. FTSE publishes review results as CMS news pages
   with per-event dynamic URLs — nothing to enumerate.
2. **Dynamic pages defeat both live fetch and Wayback.** The TW50
   constituent pages are .jsp/JS-rendered; probed live, TIP's news
   list loads client-side (the SSR payload carries only CSS — the
   API endpoint is hidden in the JS bundle), and the primary old
   research.ftserussell.com constituents URL shows ZERO Wayback
   snapshots (crawlers archive the shell, not the data).
3. **Snapshot-diff reconstruction is cadence-limited.** Even where
   snapshots exist, membership-by-diff needs at least quarterly
   coverage 2015-2026; observed coverage is sparse and the CDX
   queries themselves time out intermittently.

**Ranked collection paths (none pure-sandbox):**
- **Browser-assisted (best):** a Claude-in-Chrome session on
  taiwanindex.com.tw + ftserussell.com renders the JS, walks the
  news archives, and exports the quarterly review announcements —
  est. under an hour, gets official text.
- **TWSE monthly publications** (證交資料月刊) record TW50 review
  outcomes — library/manual work, complete but slow.
- **Wayback factsheet diffs** — monthly TW50 factsheets are
  archived but list top-10 only: insufficient for full lists.
- **Event-print detection** at FTSE thresholds — REJECTED earlier
  (2-5x prints sit inside news-day noise).

**Priority note:** FTSE keys validate the rank-buffer game but do
not gate the retro program — MSCI's 44 fully-keyed events across
all countries carry it. FTSE collection is queued as a
browser-session job, not a blocker.

**Remaining gates to full-fidelity 2015 backtests:** universe
breadth (share counts beyond 16 names) and share-drift-aware caps
— the keys are no longer the constraint.

## 6. The ex-post MSCI review 2015-2026 + the official re-grade (session 9i)

*(User challenge: "review every TW quarterly review ex-post, explain
each change, improve the engine." Full change list:
MSCI_APAC_CHANGES_2015_2026.md. Driver classifier:
scripts/tw_expost_msci.py.)*

### 6a. The official re-grade of the 2025 backtest

The 2025 backtest predated the archive solve and used
detector-reconstructed keys. Against the OFFICIAL lists:

- **Nov-25 SAIR truth was 6 adds / 7 deletions — the detector found
  2 of 13** (its NT$4B value floor was tuned on Standard giants;
  these were $1.5-4B mid-caps: Acer, AUO, MSI, Silergy, Synnex,
  Voltronic, WPG). Detector limits now stated: it reconstructs
  LARGE-print events only.
- **The engine's 9 Nov-25 flags overlapped the 7 actual Nov-25
  deletions ZERO times** — every true deletion sat below the
  15-name universe floor. Breadth is confirmed as THE binding TW
  constraint (same class as the China OUTSIDE_LOW finding).
- **The hazard rule SURVIVES official grading**: 6 of the 9 flags
  were officially deleted at May-26 (1102, 1402, 2324, 2474, 2610,
  2633); the 3 survivors are the usual cutline residents
  (1101/1326/2207). ~2/3-per-SAIR conversion stands on truth.
- **First observed quick reversal: TECO 1504 — ADDED Nov-25,
  DELETED May-26.** L5's churn buffer only spans one review, so it
  would not have blocked this; recorded as the first counterexample
  to "the provider doesn't reverse itself" (n=1, two-review gap).

### 6b. Driver classification, 2025-26 cohort (29 changes)

Mechanical rule: ret_3m into announcement (unadjusted STOCK_DAY
closes; capital-action contamination flagged).

| Driver | n | Reading |
|---|---|---|
| ADD: MOMENTUM (+30..+107% in 3m) | 6/7 | TW adds are RE-RATING events — the add candidates announce themselves on the tape months early (Bizlink +56, Chroma +52, King Yuan +88, TECO +107) |
| ADD: unreliable | 1 | 6919 shows -81.5% "return" into its OWN addition = unadjusted capital action; flagged, not asserted |
| DEL: STALE (flat, no price signal) | 9/20 | **~45% of deletions are coverage-arithmetic** — migration/FF cleanups that price momentum CANNOT predict; only the ladder sees them |
| DEL: DRIFT (-3..-15%) | 6/20 | slow bleeds toward the boundary |
| DEL: DECLINE (<-15%) | 5/20 | fast converters (MSI -30, Silergy -31, Feng Tay -24, China Air -17, Synnex -16) |

**Engine implications, implemented:** (1) deletion calls now carry a
HAZARD-VELOCITY tag (DECLINE/DRIFT/STALE from ret_3m when supplied)
— DECLINE names are the fast converters inside the watch zone;
(2) the STALE finding VALIDATES the ladder-first design — momentum
screens alone would miss half of deletions; (3) add-side: the
momentum signature (6/7) means a +30%-in-3m mid-cap screen is a
legitimate CANDIDATE-DISCOVERY tool for the breadth gap (flag
fast risers for share-count acquisition before they cross 1.8x).

### 6c. Aug-2026 TW: the boundary answer to "I don't believe zero"

TW Aug-QIR decade base rate: 7/11 years had changes (median ~2
names), 4/11 quiet — so quiet is possible but not the modal
outcome. At REFRESHED caps (Aug-4): no member sits near the 0.5x
floor (nearest: 1101 at 1.09x GMSR — double the floor) and no
VISIBLE non-member is near the 1.8x bar (best: 2324 at 1.01x,
needing +80%). Verdict, stated precisely: **zero calls at the
observable margin, with the observable margin covering only ~15
named stocks — and the Nov-25 re-grade proves TW changes
systematically originate below that floor.** The honest Aug-11
posture is therefore: no calls, plus a declared blind band
($1.5-8B mid-caps) where the decade says ~2 changes typically
live, plus the momentum-riser discovery screen (6b) as the
mitigation. Not "no changes expected" — "no changes VISIBLE, here
is exactly where we cannot see, and here is what history says
lives there."
