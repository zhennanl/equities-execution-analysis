# Asian Market Microstructure — Study Guide + Tracking Tool

*Session 6p. Companion to agents/market_structure.py (fingerprint + drift
tracker, Page 1 expander) and the MARKET_STRUCTURE_NOTES table.*

## 1. How to study it (the method)

1. **One market at a time, one page per market.** For each: sessions &
   auctions (with cutoffs), price limits & halts, lot/tick rules, short
   regime, settlement & currency, who trades (retail/foreign/institutional
   mix), venues (fragmentation or not), and what's CHANGING. The
   platform's MARKET_REG + AUCTION_CUTOFFS + LIMIT_BANDS + FX_NOTES tables
   are the skeleton — the study task is filling the "who trades" and
   "what's changing" rows.
2. **Primary sources over summaries:** exchange rulebooks/fee schedules
   (JPX, HKEX, TWSE, KRX, SGX, NSE publish everything), regulator
   consultations (SFC, FSC, SEBI, CSRC), index-provider methodology books.
   Secondary: exchange market-microstructure research pages (JPX working
   papers are excellent), broker market-structure primers, The TRADE Asia,
   KCMI for Korea.
3. **Measure, don't memorize.** Run the fingerprint on 2-3 names per
   market and reconcile the numbers with the written rules: TW close share
   should show the 13:25-13:30 call; Japan overnight variance share should
   be high (lunch + overnight gaps); China-A morning-loaded curve. When a
   number surprises you, that's the lesson.
4. **Track development quarterly:** snapshot fingerprints, run the drift
   detector, and read the exchange notices for that quarter (the B2
   regulatory-change monitor automates the reading at the desk). Structure
   is a moving target — Korea got an ATS in 2025; Japan moved its close in
   2024; China re-regulated program trading in 2025.

## 2. How we measure/characterize structure (the framework)

| Dimension | Metrics (implemented) | What it tells the dealer |
|---|---|---|
| Liquidity WHERE | close-bar share, U-shape coefficient, lunch dip | benchmark risk location; when the belly is thin |
| Liquidity COST | Roll effective spread (bps), Amihud (bps/$1M) | spread paid crossing; size capacity |
| PRICE FORMATION | 5-min variance ratio, lag-1 autocorr, overnight variance share | bounce vs momentum; how much discovery happens closed |
| CONSTRAINTS | bands, lots, short regime, settlement, currency (rule tables) | what you may do, not just what the tape does |

Drift thresholds (close share ±3pp, spread ±30%, VR ±0.15, overnight ±10pp,
Amihud ±50%) turn snapshots into a quarterly what-changed briefing.

## 3. Sources for the 2026 state notes

- [Korea Times — Nextrade launch](https://www.koreatimes.co.kr/economy/20250304/koreas-first-alternative-trading-system-ends-korea-exchanges-monopoly) · [Seoul Economic Daily — NXT ~10% share 2026](https://en.sedaily.com/news/2026/05/05/nxt-stalls-at-10-percent-market-share-despite-korean-stock) · [KCMI on multi-market Korea](https://www.kcmi.re.kr/en/publications/pub_detail_view?syear=2025&zcd=002001017&zno=1857&cno=6573)
- [AIMA — China programme-trading regulation](https://www.aima.org/journal/aima-journal---edition-142/article/evolvement-of-programme-trading-regulation-in-china.html) · [SSE voice pieces](https://english.sse.com.cn/news/newsrelease/voice/c/c_20250710_10784499.shtml)
- [HKEX dual-counter model](https://www.hkex.com.hk/Services/Trading/Securities/Overview/Trading-Mechanism/HKD-RMB-Dual-Counter-Model?sc_lang=en) · [RMB stamp duty 2026](https://financefeeds.com/hkex-clears-rmb-fee-barrier-as-hong-kong-prepares-dual-counter-stocks-for-stock-connect/)
- India T+0 top-500 optional (SEBI beta Mar-2024, expanded by 2026).
- JPX short-position and investor-type data pages; TSE Nov-2024 close reform materials.
