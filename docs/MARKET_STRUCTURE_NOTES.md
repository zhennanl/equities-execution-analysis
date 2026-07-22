# Asian Market Microstructure — Current State in Words (mid-2026)

*Generated from `MARKET_STRUCTURE_NOTES` in `agents/market_structure.py`
(the single source of truth — edit there, re-export here).
Exported 2026-07-22. Companion: MICROSTRUCTURE_STUDY_GUIDE.md
for the measurement framework and sources; the quantitative
fingerprint lives in the Page-1 expander.*

---

## Japan (TSE)

Deep, quote-driven continuous market with special-quote renewals instead of hard halts. Closing auction at 15:30 since the Nov-2024 close reform (session extended, closing auction introduced). Off-exchange: ToSTNeT + PTS venues (Japannext/Cboe/ODX ~10% combined) — fragmentation real but primary-dominated. Tick-size program by price tier; T+2; shorts covered-only with the -10% uptick trigger. Lunch break splits the day; overnight gap risk material.

## Hong Kong (HKEX)

Single lit venue, no static price band — VCM cooling-offs per stock instead. CAS closing auction 16:00-16:10 with no-cancel and random-close phases. Per-stock board lots; stamp duty makes it structurally expensive; short selling on the designated list with tick rule and weekly SFC position disclosure. 2026 theme: HKD-RMB dual counters (RMB stamp duty now payable in RMB) staging toward Southbound RMB trading; Connect flow a dominant liquidity driver.

## China-A Shanghai

Retail-heavy order-driven market inside ±10% daily bands (±20% STAR), T+1 stock settlement (no same-day turnaround), effectively no shorting. Close = brief 14:57-15:00 call. Off-exchange crossing prohibited. 2025-26 regime shift: program-trading rules effective Jul-2025 (order-rate thresholds define HFT; reporting + fees) — quant flow slowing, front-loaded morning liquidity, Connect the foreign rail with SPSA pre-checks.

## China-A Shenzhen

As Shanghai but ChiNext ±20% bands and a younger, even more retail-tilted name mix; same T+1/no-short/program-trading regime.

## Taiwan (TWSE)

Continuous since 2020 (was batch-call), ±10% daily limits that DO lock (queue-vs-retreat is a daily dealer decision), 1000-share board lots with a separate odd-lot session, close call auction 13:25-13:30. Foreign investors dominate value traded; FINI framework, SBL-quota shorts, excellent free daily margin/SBL/foreign-ownership disclosure. TWD is a restricted currency — funding is part of microstructure here.

## Korea (KRX)

±30% bands with per-stock VIs and index sidecars. The 2026 story is fragmentation: Nextrade (Mar-2025, first ATS in 70 years) took ~10-15% share then stalled near 10% under the 15% volume cap — first real SOR decision in Korea, extended hours pulling some discovery off the primary close. Shorts resumed Mar-2025 under tightened rules (registration, systems audits). Retail share high; KOSDAQ especially.

## Singapore (SGX)

Small, institutional, MM/liquidity-provider supported; no lunch break; per-stock CB (±10% vs 5-min reference); 100-share lots. Liquidity thin outside index names — a capacity market, not a speed market.

## India (NSE)

Order-driven, deep retail + derivatives-led (index options volume world-leading); T+1 settled with optional T+0 for the top-500 (2026) — settlement innovation is the structural story, plus periodic F&O curbs. Stock bands 2-20% (no static band for F&O names); FPI limits bind in places. Closing session mechanics changing toward auction-based (watch item).

## Australia (ASX)

Primary + Cboe AU competition, staggered opening auction by alphabet, CSPA close ~16:10 (huge index/EOD concentration), no price bands (anomalous-order controls), covered shorts with ASIC reporting. CHESS replacement (again) the perennial settlement watch item.

## US

The fragmentation extreme for contrast: 16+ exchanges + ~40 ATSs, LULD bands + MWCB, Reg NMS routing, T+1 since May-2024, closing auctions at NYSE/Nasdaq are the world's largest prints. Everything the Asia books do differently is visible against this baseline.

---

*These are maintained qualitative notes, web-verified as of Jul-2026
(Nextrade share, China program-trading rules, India T+0 scope, HKEX
RMB counter). The drift tracker flags when a market's measured
fingerprint stops matching these words — that is the signal to
update this file.*