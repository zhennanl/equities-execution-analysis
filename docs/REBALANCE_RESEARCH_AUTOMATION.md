# Rebalancing Research → Automatable Trader Insights

*2026-07-08. Survey of the research streams on index rebalancing events
(academic + reputable public/practitioner) and an honest assessment of which
analyses this platform can automate on free data. Extends
`INDEX_REBALANCE_RESEARCH.md` (the evidence base behind S1–S4) with streams
NOT yet exploited, each mapped to a concrete feature. Companion:
`TRADER_WORKFLOW_DESIGN.md` (how insights reach the trader).*

---

## The research landscape, stream by stream

### A. Event-study measurement of the index effect
*Harris-Gurel 1986; Shleifer 1986; Lynch-Mendenhall 1997; Greenwood-Sammon
(JF 2025) — adds' abnormal returns fell from 7.4% (1990s) to <1% (2010s),
deletions to ~0.1%, driven by midcap migrations, better liquidity provision,
and predictability. S&P DJI's own research ("What Happened to the Index
Effect") reaches the same conclusion from the provider side.*

**Status: automated** (Page 2 event study + event library). **Extension —
"your own Greenwood-Sammon":** once the library holds enough events, chart
median CAR by year/market/provider to show the trader whether the effect is
alive *in their markets* (EM/MSCI effects remain stronger than US). The
platform's edge is per-market recency, not re-deriving the US average.

### B. Cost to indexers / the execution frontier
*Petajisto 2011 (21–28 bps annual S&P 500 drag, 38–77 bps Russell 2000);
Madhavan 2003 (pre-positioning cuts hundreds of bps with minimal extra
tracking error); Pegoraro-Sammon-Shim (optimal rebalancing with anticipatory
trading).*

**Status: automated** (Agent 14 S1–S4 frontier). **Extension — tracker drag
tally:** sum realized S1-minus-S2/S3 spreads across the library → "what the
close cost this quarter, per market" — the Petajisto number, localized.

### C. Predicting constituent changes BEFORE announcement
*Beneish-Whaley 1996 ("S&P game"); Chang-Hong-Liskovich 2015 (Russell banding
regression-discontinuity); Wei-Young 2017; the JF note "An Improved Method to
Predict Assignment of Stocks into Russell Indexes" — rank-based prediction
near cutoffs achieves high accuracy as reconstitution approaches, because
Russell's rules (and MSCI's GIMI cutoffs/buffer zones) are mechanical
functions of float-adjusted market cap.*

**Automatable: PARTIALLY — highest-value gap.** Feature: **candidate radar.**
Pull float-adjusted market caps (yfinance) for names near each index's
published cutoff ranks/buffers before review dates (Agent 12 already knows the
calendar); output a watchlist with distance-to-cutoff tiers. HONEST BOUNDARY:
MSCI's official FIFs and interim cutoffs are proprietary — the radar flags
candidates with approximate float, it does not replicate the provider's
determination. Trader insight: start monitoring crowding (stream D) in likely
adds *weeks* before the announcement, and pre-agree playbooks.

### D. Anticipatory arbitrage & crowding
*Greenwood-Sammon: predictability → pre-announcement drift; arXiv 2006.07456
measures crowding on Russell 3000 events 2005–2018; practitioner evidence
(Bloomberg 2023 "top hedge-fund trade… crushed by crowding"; the Dec-2024
Apollo S&P add lost money announcement→effective for arbitrageurs because the
trade was over-crowded; multi-manager capital cycles in and out fast).*

**Automatable: YES — best insight-per-effort available.** Feature: **crowding
score** per event from data already computed or free: (i) share of pre-event
move occurring BEFORE announcement (drift decomposition already computes the
complement); (ii) pre-announcement abnormal volume (event study already has
it); (iii) short-interest change into the event (free but ~2-week-lagged
exchange data; yfinance exposes shares-short fields). Insight rule the
library can validate per market: HIGH crowding → announcement pop already
spent, expect weaker A→T drift and LARGER post-effective reversal → favors
S3/patience; LOW crowding → the old playbook (S2/S4) still has room.

### E. Flows, elasticity, and expected-move calibration
*Gabaix-Koijen "Inelastic Markets Hypothesis" (flow multiplier ~5, range 3–8;
aggregate demand elasticity ~-0.2); Chang-Hong-Liskovich estimate single-name
elasticities from index flows; Wurgler-Zhuravskaya 2002 (arbitrage risk
determines who moves more).*

**Automatable: YES.** Feature: **expected-move calculator** — the platform
already computes flow-to-trade (weight × AUM) and per-event implied η; add the
inverse: predicted CAR band = multiplier × (flow / float market cap), with the
multiplier taken from the event library's own cross-section (implied
multiplier per recorded event) bracketed by the literature's 3–8. Trader
insight pre-event: "this flow should move the stock 2–4% into T; more than
that is crowding, less means capacity remains."

### F. Closing-auction microstructure
*Nasdaq NOII research (close prices move ~5.5 bps on imbalance dissemination);
BMLL auction analytics on Russell recon days (imbalance, dislocation,
post-auction stability); recon closes are 3×–27× normal but execution at the
close underperforms in the US/APAC-ex-Japan.*

**Automatable: PARTIALLY.** Real-time NOII/imbalance feeds are NOT free →
gap register. What IS free: **auction dislocation stats** from daily+5-minute
history — close vs last-continuous-print gap on T, and T+1 open reversion,
accumulated across library events per market. Trader insight: the typical
"cost of the print" and its overnight fade where they trade — feeding the
MOC-vs-limit decision in the playbook's T-day step.

### G. Adds vs deletes asymmetry
*Chen-Noronha-Singal 2004: deletion losses largely reverse (investor
recognition); Vijh 2022 revisits addition returns.*

**Automatable: TRIVIALLY.** Split every library statistic by Add/Delete and
by market; make playbook thresholds side-specific. The VEDL deletion's 72%
reversal vs the compressed US addition effect is exactly this asymmetry —
currently the platform pools sides.

### H. What changes after inclusion (beta, comovement, liquidity)
*Barberis-Shleifer-Wurgler 2005 (comovement jumps on inclusion); Hegde-
McDermott 2003 (liquidity improves); Vijh 1994.*

**Automatable: YES, cheaply — cross-module.** Compare estimation-window vs
post-event: rolling β (event study already fits β) and EDGE spread
(microstructure_analytics already implements it). Trader insights: hedge
ratios need updating immediately post-inclusion; spread compression post-add
makes S3-style completion cheaper than pre-event estimates assume.

### I. Implementation design: staggered/multi-day rebalances
*CRSP multi-tranche transitions; provider consultations on spreading recon
flow; "rebalance timing luck" (Hoffstein) on the asset-owner side.*

**Automatable: MODERATE.** Requires multi-day parent-order simulation =
existing backlog B7. Then: simulate the S-strategies across tranche
schedules; insight: how much of the auction-stress RED flags dissolve if the
program may span 2–3 closes.

### J. Provider methodology & calendar intelligence
*Ground rules documents (Russell banding since 2007, MSCI GIMI size/liquidity/
FIF screens, buffer zones), review calendars, provider white papers (LSEG
"Four Decades of Russell Reconstitution").*

**Status: partially automated** (Agent 12 calendars + live announcements).
Extension: encode each provider's *buffer-zone logic* as rules the candidate
radar (C) reuses; surface "methodology notes" per event (e.g. migration vs
fresh add — Greenwood-Sammon show migrations move far less).

---

## Prioritized build shortlist

| P | Feature | Streams | Effort | Free-data feasibility |
|---|---|---|---|---|
| 1 | Crowding score + side-split library medians | D, G | Small — inputs already computed | Full (short interest lagged) |
| 1 | Expected-move calculator (multiplier band) | E | Small — inverse of existing flow/η math | Full |
| 2 | Candidate radar (rank/buffer screens before reviews) | C, J | Medium — new screener + Agent-12 calendar hook | Approximate float only — disclose |
| 2 | Auction dislocation stats across library events | F | Medium — 5m data, 60-day retention limit | Recent events only |
| 3 | Post-inclusion β/EDGE-spread shift panel | H | Small–medium — reuses existing estimators | Full |
| 3 | Multi-day tranche simulation | I | Large — needs B7 | Full |

**Gap register additions (not feasible free):** real-time auction imbalance
(NOII/exchange feeds), official MSCI FIFs and interim review data, intraday
short-flow, futures overlay pricing.

**Method guardrails carried over:** every automated "insight" states its n,
its market mix, and whether the threshold came from this event, the library,
or the literature; single-event calibrations stay labelled order-of-magnitude;
prediction features must show their distance-to-cutoff assumptions, never a
bare probability.

## Sources

- [Greenwood & Sammon — The Disappearing Index Effect (JF 2025)](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13410) · [NBER w30748](https://www.nber.org/system/files/working_papers/w30748/w30748.pdf)
- [S&P DJI — What Happened to the Index Effect?](https://www.spglobal.com/spdji/en/documents/research/research-what-happened-to-the-index-effect.pdf)
- [Morningstar — The S&P 500 Bump That Doesn't Last](https://www.morningstar.com/funds/sp-500-bump-that-doesnt-last)
- [An Improved Method to Predict Assignment of Stocks into Russell Indexes (JF note)](https://afajof.org/wp-content/uploads/20191016-Note-for-JF.pdf)
- [Evidence of Crowding on Russell 3000 Reconstitution Events (arXiv)](https://arxiv.org/pdf/2006.07456)
- [Russell US Indexes Ground Rules (LSEG)](https://www.lseg.com/content/dam/ftse-russell/en_us/documents/ground-rules/russell-us-indexes-construction-and-methodology.pdf) · [Four Decades of Russell Reconstitution](https://www.lseg.com/content/dam/ftse-russell/en_us/documents/research/four-decades-russell-reconstitution.pdf)
- [MSCI Global Investable Market Indexes Methodology](https://www.msci.com/documents/10199/ab796822-b8bf-9122-5e67-cfb93af723c9)
- [Gabaix & Koijen — The Inelastic Markets Hypothesis (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3686935) · [NBER w28967](https://www.nber.org/papers/w28967)
- [Nasdaq — How Much Does the MOC Imbalance Matter?](https://www.nasdaq.com/articles/how-much-does-the-moc-imbalance-matter-2019-09-27) · [Nasdaq Closing Cross FAQ](https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf)
- [BMLL — Into the Close: U.S. Closing Auction Dynamics and the Russell Reconstitution](https://www.bmlltech.com/news/market-insight/into-the-close-unpacking-u-s-closing-auction-dynamics-and-the-impact-of-the-russell-reconstitution)
- [Bloomberg — Top Hedge-Fund Index Trading Strategy… Crushed by Crowding (2023)](https://www.bloomberg.com/news/articles/2023-05-26/top-hedge-fund-trade-exploiting-dumb-index-funds-crushed-by-crowding)
- [How Hedge Funds Systematically Profit… Index Rebalancing Arbitrage (practitioner, named trades incl. Apollo Dec-2024)](https://navnoorbawa.substack.com/p/how-hedge-funds-systematically-profit)
- [Candriam Index Arbitrage — The Hedge Fund Journal](https://thehedgefundjournal.com/candriam-index-arbitrage-absolute-return-equity-market-neutral/)
- [Eastspring — Navigating index rebalancing effects](https://www.eastspring.com/insights/deep-dives/navigating-index-rebalancing-effects-key-insights-for-smarter-execution)
- Classic references (full cites in `INDEX_REBALANCE_RESEARCH.md`): Harris-Gurel 1986; Shleifer 1986; Beneish-Whaley 1996; Lynch-Mendenhall 1997; Wurgler-Zhuravskaya 2002; Hegde-McDermott 2003; Madhavan 2003; Chen-Noronha-Singal 2004; Barberis-Shleifer-Wurgler 2005; Petajisto 2011; Chang-Hong-Liskovich 2015.
