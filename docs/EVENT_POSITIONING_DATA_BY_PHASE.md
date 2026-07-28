# Public Data for Index-Event Positioning — By Phase

*Session 7g. Beyond investor-type flows: every public dataset that
illuminates positioning across the four phases of a rebalance event, what
each one tells the execution desk, and its status in the platform.
Companion to POSITIONING_DATA_SOURCES.md and EVENT_FLOW_STUDY_2026Q2.md.*

---

## Phase 0 — BEFORE the announcement (who is trading the prediction?)

The screener produces candidates weeks early; so does everyone else's.
These datasets show whether the street agrees:

1. **Securities-lending / short balances in deletion CANDIDATES**
   (TWSE SBL daily, JPX ≥0.2% positions same-day, KRX balances, HK SFC
   weekly). Borrow building in a name on our deletion watchlist =
   arbs shorting the prediction. The single best pre-announcement
   confirmation signal. *Status: sources mapped; SBL fetcher = next.*
2. **Margin-trading balances** (TWSE 融資/融券 daily per stock; Japan
   weekly 信用残高 per stock; Korea margin data). The retail/speculative
   side of the same bet — and in Taiwan, margin-short vs SBL-short
   separates retail arb from institutional arb. *Status: new.*
3. **TDCC shareholding distribution (Taiwan, WEEKLY, free)** — the
   under-used gem: per-stock holder counts by size bracket. Large-bracket
   concentration rising in an add candidate before announcement =
   accumulation by size, measured weekly. *Status: new — high value.*
4. **Index futures & basis** (TAIFEX, KRX, SGX A50/Nifty): futures OI
   building and basis richening into review dates = event exposure taken
   in derivatives before any stock prints. Explains why A50 cash adds
   showed tiny T-prints. *Status: new.*
5. **Single-stock derivatives** — options OI/skew where listed (HK, KR,
   US ADRs) and **Taiwan's warrant market** (retail positioning proxy,
   daily). *Status: new.*
6. **ETF shares outstanding / creation units** (0050 daily units, EWT/
   2823 etc.): tracker AUM moving BEFORE the event changes the flow-size
   input itself — our AUM estimate should be marked-to-market weekly in
   review season. *Status: partially wired (AUM inputs manual).*
7. **Provider consultations & press previews** — expectation formation:
   a candidate named in three broker previews is priced; one only our
   screener sees is not. Feeds the rebalance-interest monitor's news
   layer. *Status: monitor hook exists.*

## Phase A→T — after announcement, before effective (the build window)

8. **Short-balance TRAJECTORY in confirmed names** (daily SBL/JPX/KRX):
   the within-foreign netting problem from 7e is resolved HERE — borrow
   rising while foreign nets are flat = arb shorting against tracker
   buying, decomposed. *Status: the designated next fetcher.*
9. **Block-trade tape** (TWSE 鉅額交易 daily; A-share block-trade
   discounts; HK direct-business prints): pre-positioning done in size
   off the continuous tape — blocks in event names during the window are
   somebody moving early without footprint. *Status: new.*
10. **ETF creation acceleration** (daily units): trackers pre-funding
    the trade — creations before T mean the cash flow partly already
    happened (the A50-addition profile, explained). *Status: new.*
11. **Margin balance shifts** (daily) — retail joining/fading the move.
12. **Off-exchange / dark share** where published (FINRA ATS weekly per
    stock for US lines; limited in Asia). *Status: noted, US-only.*

## Phase T — the effective day (executing into the print)

13. **Indicative auction price & volume feeds** — TWSE broadcasts the
    simulated closing price/volume during 13:25–13:30; ASX/SGX publish
    auction imbalance/indicative prints; US MOC imbalance feeds. The
    real-time answer to "how big is the print and where is it clearing"
    — the single most actionable T-day dataset and a natural cockpit
    input. *Status: new — cockpit integration candidate.*
14. **Intraday venue mix / odd-lot session prints** (TW odd-lot,
    ToSTNeT prints in JP): where the non-auction residual is clearing.
15. **Real-time short-sale volume** (HKEX daily short turnover; TWSE
    intraday flags): who is hitting the print short.

## Phase T+ — after effective (did the crowd leave?)

16. **Short-balance UNWIND** (daily SBL returns): borrow falling after T
    = arb covering confirmed — the cleanest post-event validation of the
    handoff story, and the timing input for S3's completion leg (sell
    the bounce while arbs are still covering). *Status: next fetcher.*
17. **TDCC weekly redistribution**: whose hands did the shares end in —
    retail absorption after deletion prints predicts the bounce's
    durability. *Status: new.*
18. **ETF premium/discount + tracking difference** (published daily for
    0050 et al.): tracker execution stress on T shows up as NAV
    premium/discount spikes — the public print of how expensive the
    rebalance was for the trackers, i.e., OUR clients' benchmark pain,
    measurable. *Status: new — QBR-adjacent.*
19. **Investor-type flows post-T** (wired — 7e/7f): who kept trading.
20. **Fails / settlement stress** (US FTD; limited Asia): deletion names
    with borrow squeezes occasionally fail — a settlement-desk early
    warning.

## Priority queue (highest value ÷ effort, given what's already built)

1. **SBL/short-balance daily fetcher (TW → KR → JP)** — resolves the
   within-foreign netting (the one standing attribution limit) AND gives
   the Phase-0 confirmation signal and the T+ unwind clock. One dataset,
   three phases.
2. **Indicative auction feed (TWSE) into the cockpit** — turns T-day
   MOC sizing from a historical multiple into a live number.
3. **ETF units + premium/discount daily** — marks the AUM input to
   market and adds the tracker-stress gauge.
4. **TDCC weekly distribution** — the slow-moving accumulation X-ray.
5. **Block-trade tape** — the size-done-quietly ledger.

Everything above is free, official (or an official-data mirror), and
follows the established integration pattern: one fetcher, one canned-
payload parser test, one chunked cached script, honest status label in
the registry.

---

*Update (session 7h): the priority queue is implemented in
`agents/event_data.py` — short balances (TWT93U) and block tape
(BFIAUU) fetched and graded on the May SAIR + June TW50 events; TDCC
wired (latest-week-only limitation documented); indicative-auction
parser wired (live-only); ETF units / futures OI remain PROTOCOL.
Graded results: docs/case_studies/EVENT_DATA_USEFULNESS_2026Q2.md.*
