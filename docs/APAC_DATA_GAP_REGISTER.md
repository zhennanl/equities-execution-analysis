# APAC data gap register — what the Taiwan playbook needs, and where to get it

*c-230. Written for the question "we have the daily data; what
is still missing before the other markets can run the Taiwan
analysis?" Sources are primary — exchange and regulator pages —
and every row is marked VERIFIED (a page was loaded that says
it) or UNVERIFIED (plausible, not confirmed). An unverified row
that reads as verified is worse than an admitted gap.*

---

## 1. What the Taiwan playbook actually requires

From `docs/EVENT_WINDOW_FRAMEWORK.md`, the analysis splits into
three tiers by input. This is the whole map:

| Tier | Input | What it buys | Portable today? |
|---|---|---|---|
| **1** | daily OHLCV + ann/eff dates | gap1, drift, eff_day, rev5/20, pre_drift, capture, T-multiple, ADV-days, execution counterfactuals, labels | **YES — all 12 markets, 2,078 name-events** |
| **1.5** | + index weights / float / tracking AUM | expected passive demand, demand-in-ADV-days, the λ=0.093 forced-shares model, completion | partly — floats exist for some markets (`data/apac_fif_inverted.json`) |
| **2** | + per-stock positioning (borrow, short balance, foreign/institutional net) | crowding_ratio, PRE/PROG/SQZ, CH1/CH2/CH3 supply channels, anticipation clock, squeeze risk, wrong-way flag | **NO — Taiwan only** |
| **3** | + intraday (5-min or finer) | auction share, dislocation bps, pressure bps, PM drift, T+1 auction reversion | **NO — Taiwan 2023-05+, rest pending the IB harvest** |

**The honest summary: we have Tier 1 everywhere and Tier 2
nowhere except Taiwan.** Tier 2 is where the Taiwan edge lives
— it is the difference between describing what happened and
forecasting who will supply the close.

---

## 2. Tier 2 retrieval register

Two legs matter: a **borrow/short** measure (is the crowd
already positioned?) and a **flow** measure (who is trading it,
and are they on the right side?). The critical distinction in
column 4 is **census vs threshold**: a threshold regime only
reports positions above a size, so it systematically
understates diffuse crowding — exactly the state that precedes
an orderly print.

| Market | Short / borrow | Cadence | Census? | Foreign / institutional flow | Access | V |
|---|---|---|---|---|---|---|
| **Australia** | ASIC daily aggregate short positions per stock | daily, T+4 | **CENSUS** | none found | open CSV, one URL pattern, ≥2010 | ✅ |
| **Hong Kong** | HKEX daily short-selling turnover per stock; SFC weekly reportable short positions | daily / weekly | census (turnover) / threshold (positions) | **CCASS per-participant daily holdings**, 12 months free | open, plain-text daily files | ✅ |
| **India** | NSE Clearing SLBS daily open positions (borrow census, ≥2016); NSE daily short-selling flow | daily | **CENSUS** | aggregate FII/DII only — **no per-stock** | `nsearchives.nseindia.com` open with a browser UA | ✅ |
| **Thailand** | SET outstanding short positions per security | daily, history ~Apr-2024 | census | **NVDR trading by stock** — a genuine per-stock foreign proxy | pages load; `set.or.th/api/*` 403 | ✅ |
| **Korea** | KRX short position by issue; short-selling transaction by issue | daily | **threshold** (0.01% / KRW1bn) | **KRX trading by investor, per issue** — the best attribution in Asia | severe: JSON API returns LOGOUT from datacentre IPs; the free Open API carries **no** short data | ✅ |
| **Japan** | JPX outstanding short positions | daily | **threshold, ≥0.5%** | investor-type series is **market aggregate only** | open; archive ~1 year on the page | ✅ |
| **Japan** | JPX end-of-week margin balances by issue | weekly | **CENSUS** | — | open | ✅ |
| **China A** | SSE 融资融券 per-stock margin + lending balance | daily | census of the margin-eligible universe | Stock Connect northbound holdings went **QUARTERLY** in 2024 | SSE: one JSONP call with a Referer. SZSE: blocked, unresolved | ✅ / ⚠️ |
| **Malaysia** | Bursa daily per-stock RSS short volume | daily | census of reported short volume | aggregate only | open; the net-short PDF is bot-blocked | ✅ / ⚠️ |
| **Singapore** | MAS SPRS weekly aggregated | weekly | **threshold** (0.2% / S$2m) | none found | `api.sgx.com` 403 | ✅ |
| **Indonesia** | none — short selling repeatedly deferred | — | — | IDX stock summary carries per-stock foreign buy/sell | Cloudflare-blocked | ⚠️ |
| **New Zealand** | **none** | — | — | **none** — NZX states it does not maintain foreign-holding lists | n/a | ✅ |

### Two structural warnings before anyone builds on this

**China's northbound flow went quarterly in 2024.** Any A-share
foreign-flow series spanning that change is not comparable
across our panel. This is a disclosure change, not a data-access
problem, and no budget fixes it.

**Only Australia, Hong Kong, India and Thailand offer a census
short/borrow measure.** Japan, Korea and Singapore are threshold
regimes. A threshold series will read "uncrowded" precisely when
crowding is spread across many holders below the reporting bar —
which is the failure mode that matters, because it is silent.

---

## 3. Ranked: cheapest path to a Taiwan-style crowding read

Ordered by analytical value per unit of engineering.

1. **Australia** — one CSV URL pattern, census, 16 years. Short
   leg only, but it is the cleanest retrieval in the region and
   `data/au_event_shorts.json` already proves the path works.
2. **Hong Kong** — both legs, all open URLs, plain-text daily
   files. The CCASS participant view is an ownership X-ray
   nobody else publishes.
3. **India** — SLB open positions is a real borrow census; the
   foreign leg does not exist per stock, so it is half a
   Taiwan.
4. **Thailand** — the only market besides Taiwan with per-stock
   short **and** per-stock foreign. Costs an anti-bot layer and
   the short history only reaches ~2024.
5. **Korea** — the highest analytical ceiling in the region and
   a pure engineering cost. 102 name-events in our panel makes
   it worth the session/IP work.
6. **Japan** — weekly margin census is workable as the crowding
   level; no foreign leg; short truncated at 0.5%.
7. **Malaysia** — cheap daily per-stock short volume, aggregate
   flow only.
8. **China A** — SSE margin is one call, but northbound went
   quarterly and SZSE access is unresolved. 1,237 name-events
   makes this the largest prize and the least tractable.
9. **Singapore** — threshold-truncated and API-blocked.
10. **Indonesia** — no short interest at all; foreign flow needs
    a headless browser.
11. **New Zealand** — data-dark. Do not spend.

---

## 4. What this changes about the analysis we can publish

Everything in `docs/INDEX_STRATEGIST_QA_APAC.md` is Tier 1 and
stands on its own. What we **cannot** do for any market except
Taiwan, and should stop implying we can:

* say whether a print will be orderly or violent BEFORE it
  happens (needs completion / crowding — Tier 2)
* attribute a reversal to wrong-way positioning (needs signed
  flow — Tier 2)
* measure how much of the print went through the auction
  (Tier 3)
* run the anticipation clock — when pre-positioning starts
  (needs borrow build — Tier 2)

Tier 1 answers "how big, how violent, when does it move, does
it revert, which schedule won". That is a real product. It is
descriptive and historical, and the forecasting layer is the
part that is missing.

---

## 5. Survivorship — the gap that is not about access

Ten of twelve priced markets come from Yahoo, which lists the
living. **Their deletion rows are biased toward names that
survived being deleted.** Taiwan and India come from exchange
day-files and keep the dead.

This is a data gap of a different kind: it is not that we
cannot reach the data, it is that the free source cannot
represent the population. It matters most in exactly the place
the desk cares most — deletions, where the tail is a name that
kept falling. Fixing it means an exchange day-file harvester
per market (as we built for Taiwan and India), not a new
endpoint.

Priority if this gets funded: **Japan and China**, which carry
147 and 436 deletion-side name-events respectively on a
survivors-only basis — the two largest biased samples we hold.
Korea is third at 60.
