# APAC Free-Data Availability for Index-Rebalance Study — Ranked vs Taiwan

*Session 8y (2026-07-29). Every LIVE/DEAD claim below was probed
this week from this environment (session refs in brackets); the
rest are structural facts about what each exchange publishes.
Scoring pillars = what made Taiwan the gold standard:*

*P1 official all-stock daily quotes (historical) · P2 short/
positioning balances (per-stock, cadence, depth) · P3 auction/
microstructure archive · P4 flow attribution (who traded) ·
P5 per-name intraday history (free) · P6 access friction from a
plain client.*

## The benchmark: Taiwan (score 10)

MI_INDEX all-stock daily (decades) · TWT93U margin+SBL daily w/
quota (2015+) · MI_5MINS/MI_5MINS_INDEX 5-second market+index
stats (2012+) — the only public 5s archive in Asia · TWT38U
foreign per-stock daily (2015+) + TDCC ownership brackets weekly ·
TPEx mirror for OTC · keyless official APIs throughout. Weak spot:
per-name intraday history (60d walls) — the one pillar where
Taiwan is NOT best in class.

## The ranking

| # | Market | Score | P1 | P2 | P3 | P4 | P5 | P6 | The one-line verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **China A** | **8** | ✓ | margin/融券 daily (exchange-published; sandbox-walled) | auction visible in bars (14:57-15:00 = last 5m bar) | northbound holdings per stock daily (HKEX) | **baostock 5-min, YEARS — beats Taiwan** [8q] | walls from abroad, open domestically | **Most Taiwan-like; per-name auction study already ran on it** |
| 2 | **Japan** | **7.5** | ✓ JPX | daily disclosed shorts >=0.5% (2013+, floor-not-census) [8g] + weekly margin | itayose book live; no archive | weekly by investor type (aggregate only) | J-Quants ¥5.5k/mo (official, cheap) | low | The disclosure regime is rich; intraday is cheap-not-free |
| 3 | **Hong Kong** | **7** | ✓ | SFC weekly per-stock (2012+) [8g] + HKEX daily short TURNOVER | CAS live-only | **CCASS per-participant DAILY holdings [probed 8y] — custody-level attribution nobody else publishes** + Connect flows | none free (31d walls) [8q] | low-mid (ASP forms) | Weekly-cadence Taiwan with a unique custody X-ray |
| 4 | **Australia** | **6** | ✓ ASX | **ASIC daily per-stock short positions, YEARS, open CSV** | no archive | weekly gross only | paid | low | Best short data outside TW/JP; index events smaller for our program |
| 5 | **India** | **6** | **official bhavcopy + DELIVERY qty, 2015+ verified [8y]** | none (structural — no short-balance product) [8g] | none pre-Aug-2026; CAS arrives Aug 3 | FII/DII daily (aggregate), delivery % per stock | paid | mid (cookies) | Deep daily archives, missing exactly the positioning pillar |
| 6 | **Korea** | **5.5 (8 with a key)** | ✓ | KRX daily per-stock short balance EXISTS — login-gated [8g] | none public | **per-stock daily flows by investor type — Asia's best attribution, gated** | account-gated | HIGH | The high-ceiling gated door: one free KRX/KIS registration ≈ Taiwan-tier |
| 7 | **Thailand** | **4** | ✓ SET | daily short-sale reports | none | NVDR daily per stock (foreign proxy — underrated) | none | mid | NVDR flow is a hidden gem; rest is thin |
| 8 | **Singapore** | **3.5** | ✓ | weekly short interest + daily SS turnover | none | none per stock | none | mid | Clean but shallow; few index events |
| 9 | **Malaysia** | **3** | ✓ | RSS/IDSS daily lists (403 from sandbox) [8g] | none | monthly aggregate | none | HIGH | Data exists behind walls; thin anyway |
| 10 | **Indonesia** | **2.5** | ✓ | none (shorting restricted) [8g] | none | foreign net per stock daily (in daily summaries) | none | mid | One good pillar (foreign flow), little else |
| 11 | **Vietnam** | **2** | ✓ HOSE | none | none | foreign room/flows daily | none | mid | Frontier-grade |

## The conclusion the ranking forces

**Nobody matches Taiwan's breadth-times-openness.** Taiwan is the
only market where all of (daily shorts + 5-second auction archive +
per-stock foreign flow + ownership brackets) are keyless and
decade-deep. But three markets get close enough to replicate the
five-layer study:

1. **China A** — the only market that BEATS Taiwan on a pillar
   (per-name intraday, years deep via baostock): the per-name
   auction/violence studies replicate fully; the crowding pillar is
   the weak one (margin shorts are economically thin).
2. **Japan** — replicates the crowding pillar best (daily disclosed
   shorts since 2013) and everything else at small cost.
3. **Hong Kong** — weekly-cadence crowding plus the CCASS custody
   X-ray, which enables a study Taiwan can't do: WHICH brokers'
   books absorbed the rebalance flow.
4. **Korea** is the option: one registration converts it from #6
   to Taiwan-tier — the highest ROI single action on this list.

**Program implication:** the retrospective sweep generalizes in
order TW → CN-A → JP → HK; Korea joins when a key exists; India
joins on the flow/delivery pillars now and the auction pillar after
the Aug-2026 CAS accumulates history.

## Coda — the same four pillars WITH institutional access (session 8z)

| Taiwan pillar | Institutional replacement | Markets covered | Verdict |
|---|---|---|---|
| Daily short balances (TWT93U) | **Securities-finance data (Markit/S3-class): daily borrow quantity, utilization, FEES per stock, deep history** — richer than any exchange file (fees = the crowding price signal our free data never had) | ALL markets | **SOLVED, upgraded** |
| 5-second auction archive (MI_5MINS) | **Tick history (LSEG Tick History / BMLL / exchange data shops)**: every auction print with condition codes, order-book states, imbalance feeds where published — decades deep | ALL markets | **SOLVED, upgraded** (per-name, not just market-wide) |
| Per-stock foreign flow (TWT38U) | NOT a vendor product — it exists only where the MARKET STRUCTURE records it: investor-ID regimes (KR, TW), NVDR (TH), Connect northbound (CN), custody disclosure (HK CCASS) | KR/TH/CN/HK yes; **JP/SG/AU: unrecorded — weekly aggregates at best; no budget fixes absent disclosure** | **STRUCTURAL — the one pillar money can't buy** |
| Ownership brackets (TDCC) | Custody/registry analogs where they exist (CCASS HK); fund-holdings databases (vendor) as coarser proxy | HK genuine; elsewhere proxy-grade | Partial |

**The replication verdict:** with desk data, the full five-layer
Taiwan study replicates COMPLETELY in Korea, Hong Kong, and China,
and near-completely in Japan (flow-attribution pillar drops to
weekly aggregates — a stated degradation, not a blocker, since
securities-finance fees partially substitute as the positioning
signal). Everywhere else the prediction/flows/auction layers
replicate and the positioning layer runs on borrow-fee data instead
of flow attribution. The methods transfer unchanged — that was the
design invariant, and the free-data builds are the proof the
pipelines already run end-to-end.
