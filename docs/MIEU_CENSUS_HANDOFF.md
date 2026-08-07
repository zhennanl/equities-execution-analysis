# HANDOFF — MIEU Census Run (Market Investable Equity Universe, Taiwan)

*Written 2026-08-05 (T-6 before the Aug-11 announcement). This file
is self-contained: a fresh session (or Bill alone in a terminal)
can execute the run and interpret the result with no other
context.*

## The goal, in one paragraph

Compute MSCI's denominator EXACTLY as defined (GIMI §2.2, §2.3.5):
census every TWSE + TPEx common equity (~2,146 four-digit codes,
ETFs/warrants excluded), apply the investability screens (minimum
size ~US$0.2B, float ≥ 0.15, 12-month AND 3-month annualized
traded-value ratio ≥ 15%, 3-month trading frequency ≥ 70%), and
sum the passing securities' free float-adjusted capitalizations
(price × shares × float). Success test: the sum should land near
the factsheet-implied **US$3,745 billion** (July-31 vintage — the
number MSCI's own arithmetic implies). Our 150-name+modeled-body
estimate ran +11.4% high; the census replaces modeling with
measurement.

## Current state (already done — do NOT redo)

- `scripts/mieu_census.py` — complete, tested, RESUMABLE (atomic
  cache `data/mieu_cache.json`; re-running never loses progress)
- Universe phase done: 2,146 codes cached
- ~50 names already harvested in the pilot (fund + tape phases)
- Float methodology validated separately: named-insider approach,
  0.022 mean error vs MSCI's implied factors
  (data/tw_float_mops_v2.json)

## The run (Bill's machine, any terminal, ~75–90 min unattended)

```
cd C:\Users\Bill\Downloads\execution_analytics

:: Phase B+C — fundamentals + 12m tape, all 2,146 names (~60 min)
py scripts\mieu_census.py harvest

:: Phase D — insider floats for names above the size screen
:: (~400-600 names, ~10-15 min)
py scripts\mieu_census.py floats

:: Phase E — screens + the sum + comparison vs $3,745B
py scripts\mieu_census.py report
```

Notes: each phase is resumable — if anything interrupts (rate
limit, sleep, Ctrl-C), just run the same command again; it
continues where it stopped. Progress prints every 10 names. If
FinMind rate-limits (HTTP 402/429 messages), wait ~10 minutes and
rerun; a free registered token in env `FINMIND_TOKEN` raises the
limit (optional).

## Reading the report

`report` prints and saves `data/mieu_report.json`:

- `denominator_busd` — THE number: the census denominator
- `gap_vs_factsheet` — vs the implied $3,745B. Within ±5% =
  strong confirmation of both the census and the factsheet
  inversion; a larger gap means float estimates or screen
  parameters need review (`of_which_default_float_busd` shows how
  much rides on default floats — if that is large, run
  `floats` with a higher limit)
- `excluded` — how many names each screen removed (sanity: most
  of the ~2,146 fall to `min_size`; the pass set should be
  roughly 300–600 names)
- `n_pass`, `coverage` — completeness; report is honest on
  partial coverage but conclusions need fund/tape ≥ ~95%

## After the run — hand back to the analysis session

1. Commit: `git add -A` → commit "MIEU census data + report"
2. In the analysis chat, say: "MIEU census done — denominator X,
   gap Y%" (or just "census done, interpret it")
3. Follow-ups queued for that session: adopt the census
   denominator into the walk's frame trio (census / MSCI-implied /
   bottom-up — frame-robust policy stands), re-check the 2408
   Nanya shadow call under the census frame, record the result as
   the next Q&A entry in docs/INDEX_REVIEW_EXPLAINED_QA.md, and
   pin a test on the census report schema + gap bound.

## ADDED (c-62): the APAC member-caps runs (same pattern, 9 more markets)

Factsheets for all 10 markets are captured and parsed
(data/apac_factsheet_archive.json — counts match our membership
pipeline EXACTLY in all 10). The per-market member census
(caps + floats via Yahoo, TW-style reconciliation vs the
factsheet-implied denominator) runs per market:

```
py scripts\apac_member_census.py harvest Japan
py scripts\apac_member_census.py report Japan
:: repeat for: Australia HongKong Korea China India Malaysia
::             Indonesia Philippines
```

**UPDATED (c-95): full 13-market ladder run.** Membership now
covers all 13 (NZ/SG/TH added; counts match factsheets
exactly). Fixes in: TWD FX 32.5->29.5 (Q67), NZD/SGD/THB
added, fast_info fallback for .info gaps (SG banks), search
resolver for SG/NZ/TH mnemonics, periodic saves (resumable
mid-market). NZ already priced 5/5 from the session; SG 5/16
partial. Run each (order = smallest first; China last ~25min):

```
py scripts\apac_member_census.py harvest Singapore
py scripts\apac_member_census.py harvest Thailand
py scripts\apac_member_census.py harvest Malaysia
py scripts\apac_member_census.py harvest Indonesia
py scripts\apac_member_census.py harvest Philippines
py scripts\apac_member_census.py harvest HongKong
py scripts\apac_member_census.py harvest Australia
py scripts\apac_member_census.py harvest Korea
py scripts\apac_member_census.py harvest India
py scripts\apac_member_census.py harvest Japan
py scripts\apac_member_census.py harvest China
:: then per market:
py scripts\apac_member_census.py report <Market>
```

Reading each report: members-vs-factsheet within ±10-15%
validates; the bottom-of-ladder table IS that market's
delete-candidate region against its corridor (DM [8.21,
18.87], EM [4.10, 9.44] — Aug-26 scaled). Names failing to
price are listed per report — normal, stated.

Runtimes: most markets 2–10 min; China ~25 min (576 names).
Resumable per market. Pilot done: HongKong 22/25 priced,
members-vs-factsheet +10.9%. Known symbol quirks handled in-code
(HK Jardine lines via .SI, Malaysia mnemonics via the Yahoo
search resolver); a few residual unpriced names per market are
listed in each report — normal, stated. Read each report like the
TW one: members_vs_factsheet within ±10-15% validates; the bottom
ladder is the market's deletion-candidate region against its
corridor (DM markets: $8.2–18.9B; EM: $4.1–9.4B).

## ADDED (c-66): the SBL borrow-history run (2015 -> Apr-2026)

Closes the borrow-data gap the pattern study declared. Runs
against TWSE (NOT FinMind), so it can run in a SECOND terminal in
parallel with the census — no rate-limit collision:

```
py scripts\sbl_history_harvest.py harvest
```

~2,950 weekdays at polite pacing ≈ 1.5–2 h, fully resumable
(rerun the same command after any interruption); check progress
anytime with `py scripts\sbl_history_harvest.py status`. Output:
data/sbl_history.json — daily securities-lending sell quantity +
balance for the 150 tracked names, same shape as the live cache.
Pilot verified: Jan-2015 parses (TSMC balance 42.9M shares),
121/150 names present per day (rest listed later).

When it lands, tell the analysis session "SBL history done" —
queued follow-ups there: the decade borrow-panel test (the
user's borrow-rate hypothesis, properly powered at ~77 deletions
instead of n=7), CH1b standing-base refinement for the v2
liquidity engine, and H16's borrow leg backfilled. Note: borrow
FEE RATES remain a separate gap (FinMind's fee dataset is
paid-tier; the TWSE SBL fee endpoint is the queued
investigation) — balances alone unlock the main tests.

## ADDED (c-67): T86 — signed institutional flow, the top missing dataset (built; run after SBL)

TWSE's T86 gives, daily per stock since 2015, NET buy/sell split
by investor type — foreign, investment trusts, and DEALER PROP
DESKS (the signed arbitrage footprint we have never had). This
replaces holding-delta proxies with true signed flow and lets the
channel model attribute window accumulation to WHO traded.

**Run it in the same terminal as the SBL harvester, AFTER that
one finishes** (same TWSE host — sequential, not simultaneous):

```
py scripts\t86_history_harvest.py harvest
```

~2h, resumable, `status` shows progress. Pilot verified
(Jan-2015: TSMC foreign net +3.69M shares; era-tolerant parser
handles the 15-field 2015 format and the 18-field modern one).

## ADDED (c-68): the roadmap harvesters — BUILT (scripts/roadmap_harvest.py, one engine, four datasets)

Items 2–4 and 6 of the roadmap below are now implemented and
piloted. One script, subcommand per dataset; all probed live at
2015 AND 2026 dates before inclusion — field counts are stable
across the whole decade (margin 15, daytrade 5, blocks 5). Raw
rows stored per watch name (era-proof), resumable/atomic, same
politeness rules as SBL/T86.

**TWSE datasets — run in the SBL/T86 terminal, AFTER those
finish, ONE AT A TIME (same host):**

```
py scripts\roadmap_harvest.py margin      :: MI_MARGN, ~2h
py scripts\roadmap_harvest.py daytrade    :: TWTB4U,  ~1.7h
py scripts\roadmap_harvest.py blocks      :: BFIAUU,  ~1.7h
py scripts\roadmap_harvest.py status      :: progress, anytime
```

Suggested order: margin -> daytrade -> blocks (value order).
Pilots verified (Jan-2015 + Jun-2026): TSMC margin-long balance
20,527 lots / short 4,830 (2015 idx 5 / idx 11); TSMC day-trade
1.056M shares (idx 2, buy/sell values idx 3/4); blocks
trade-level rows (type/price/vol/value).

**ADDED (c-72) — auction5s (MI_5MINS): official market-wide
5-sec order/trade aggregates covering the 13:25–13:30 call
window, 2015+. Same TWSE host — joins the sequential queue:**

```
py scripts\roadmap_harvest.py auction5s   :: ~1.7h
```

Stores 13:00 reference + all rows from 13:20:00 (122/day):
order ARRIVAL into the auction and the size of the 13:30 cross,
market-level, for a decade. (Per-stock indicative paths remain
capture-forward — disclosed live since 2015-06-29 but never
publicly archived.)

**TAIFEX single-stock-futures OI — different host, safe anytime,
CAPTURE-FORWARD (OpenAPI serves current day only):**

```
py scripts\roadmap_harvest.py taifex      :: seconds; run daily
```

First capture done: 2,184 contract rows incl. ~2,138 SSF-like
contracts with OpenInterest. Two honest gaps, stated: (a) the
contract->underlying map (ZFF -> which stock) is a queued
analysis-time build (TAIFEX publishes the mapping table); (b)
HISTORICAL SSF OI (2017->now, needed to validate 2324 Compal
May-26) is NOT in the OpenAPI — it needs the taifex.com.tw
download forms (POST, date-ranged CSV) = still the queued
investigation from item 2. Daily capture starts the archive now
so Aug-11 -> Aug-31 window is covered regardless.

## The remaining missing-data roadmap (updated c-68)

1. **DONE (c-67) — T86 institutional flow** (signed, by type).
2. **PARTIAL (c-68) — TAIFEX SSF OI**: daily capture-forward
   live; historical backfill via download forms still open.
3. **DONE (c-68) — MI_MARGN margin balances** (retail leverage,
   both sides, 2015+).
4. **DONE (c-68) — day-trading per stock** (TWTB4U; CH3
   toll-collector capacity, 2015+). Note: it's day-trade VOLUME
   + values; the ratio = volume ÷ total volume computed at
   analysis time from the vintage tape.
5. **OPEN — SBL fee rates** (the PRICE of borrow). Probed:
   TWSE's TWT96U turns out to be SBL AVAILABLE-QUANTITY (useful,
   not fees); /exchangeReport/TWT96U is not a JSON endpoint.
   FinMind's fee dataset is paid-tier. Next probe: the TWSE SBL
   subsite's 成交明細 day-files (transaction-level, carries fee
   rate) — or evaluate FinMind sponsor tier. Balances alone
   (done, c-66) unlock the main tests.
6. **DONE (c-68) — block-trade backfill** (BFIAUU day-files,
   trade-level, 2015+).

Each followed the same proven pattern: probe the endpoint at
historical dates, verify field stability, clone the day-file
harvester (watch-name subset, resumable, atomic, polite pacing,
era-tolerant raw-row storage), pilot, pin a test, hand off the
full run.

## Roadmap additions (c-81, from the Step-2 data inventory, Q51)

7. **QFIIS foreign-holding day-file** — TWSE publishes per-stock
   foreign holding LEVELS + remaining room daily (T86 gives
   flow; this gives the level series, decade-deep). Prompt:
   "Probe TWSE MI_QFIIS day-file at 2015/2020/2026 dates; clone
   the roadmap harvester; validate levels against vintage
   foreign percentages."
8. **ETF PCF creation/redemption baskets** — local trackers
   (Yuanta 0050 family etc.) publish daily PCF files: DIRECT
   observation of local passive demand instead of inference.
   Prompt: "Locate PCF disclosure files for the major TW index
   trackers; capture-forward daily + probe for archives."
9. **Broker-branch day-files** (證券商買賣日報表, bsr.twse) —
   retail flow geography per stock; HEAVY (per-stock-per-day
   documents); only pursue if H18/H19 grade well.
10. **Odd-lot session data** (2020+) — retail micro-flow;
    cheap, modest value.
11. **TPEx institutional + SBL day-files (c-84 — a REAL gap
    found by user verification):** ~20 of the 150 watch names
    are TPEx-listed (incl. MSCI members 6488 GlobalWafers,
    8069 E Ink, 5274 ASPEED, 3105, 5347) and have NO T86/SBL
    coverage — TWSE endpoints are main-board only. TPEx's own
    institutional endpoint VERIFIED live (www.tpex.org.tw/www/
    zh-tw/insti/dailyTrade?type=Daily&sect=EW&date=YYYY/MM/DD
    &response=json; 927 rows/day now, 557 in 2019; 2019+
    confirmed, 2015-18 needs the legacy-format probe). TPEx SBL
    equivalent: probe needed. Prompt: "Clone the roadmap
    harvester for TPEx institutional daily (2019+ modern
    endpoint, probe legacy for 2015-18) and the TPEx SBL
    day-file; then re-run the anticipation clock and liquidity
    panel with the TPEx legs restored." Affected analyses to
    re-run once landed: anticipation clock (TPEx dels were
    silently dropped), liquidity panel CH1, event EDA.

## Difficulty assessment (the question that started this)

Entirely feasible with free data — the cost is breadth, not
access: ~2,146 × 2 FinMind calls + ~500 yfinance calls ≈ 75–90
polite minutes. Irreducible gaps vs MSCI's exact number, stated:
their private float factors (ours validated to 0.022 on graded
names), FIF rounding conventions, their unannounced price date,
and the exact global minimum-size figure (~$0.2B assumed;
immaterial at this boundary). Expected landing: within a few
percent of $3,745B.
