# APAC FIF recovery + the local-tracker survey (c-144)

## Part 1 — FIF for every MSCI country index

### The method upgrade: grid-snap calibration
Taiwan's inversion needed the index float cap at the weights'
own date (Jun-1). Other markets publish factsheets at Jul-31
only — a two-month mismatch that would contaminate every FIF.
Solution: drop the index float cap entirely.

    FIF_i = c_m x (weight_i / full_cap_i)

c_m is unknown (it equals IndexFloatCap/100), but Appendix VI
forces every FIF onto a **2.5% rounding grid**. So choose c_m
to minimize total distance to that grid.

**Control test (Taiwan, truth known):** grid-snap recovered
c = 33.27 vs the true 33.314 — 0.13% — and FIFs to a median
error of 0.0010 across 77 members, *without ever being told
the index float cap*. The grid is a strong enough fingerprint
to calibrate on.

It is also a per-market QC: if recovered FIFs do NOT cluster
on the grid, the inputs are wrong (bad dates, bad ticker map)
and the market is reported FAILED rather than published.

### Results so far
| Market | Method | n | On-grid | Verdict |
|---|---|---|---|---|
| Taiwan | weights inversion (index float cap known) | 77/77 | 100% | PUBLISHED (c-140) |
| New Zealand | factsheet-implied — the whole 5-member index IS the top-10 list | 5/5 | 100% | PUBLISHED |
| Singapore | grid-snap inversion | 8/16 | 100% | PASS (partial map) |
| Others (10) | grid-snap inversion | — | — | HARVEST PENDING |

New Zealand FIFs (Jul-31): FPH 1.00, Auckland Airport 1.00,
Infratil 0.90, Contact Energy 0.875, Meridian 0.50 — Meridian
is ~51% Crown-owned, so a 0.50 FIF is exactly right.
Singapore FIFs (Jun-1): DBS 0.649, UOB 0.653, SingTel 0.404,
Keppel 0.70, SIA 0.425, CapitaLand Inv 0.419, Wilmar 0.229,
Sembcorp 0.448 — all on grid; the Temasek-held names land
where their known stakes imply.

### What blocks the remaining 10 markets
Not method — throughput. Full caps need shares outstanding
per name (Yahoo `get_info`, throttled ~60 calls/session), and
the remaining membership is ~1,130 names. The harvester is
resumable and cached:

    py scripts\apac_fif_inversion.py market Philippines
    py scripts\apac_fif_inversion.py market Indonesia
    ... (re-run any market to continue where it stopped)

Second gap: name->ticker mapping. 8/16 in Singapore is a
mapping shortfall (OCBC, Sea ADR, ST Engineering unmatched;
CapitaLand REIT tickers need Yahoo forms C38U.SI / A17U.SI).
Each market needs an OVERRIDES pass like Taiwan's 17-name fix.

**A bug worth recording:** the first run used epoch windows
from 2025, so it priced full caps a year early. Caught by
New Zealand returning FIFs above 1.0 — impossible values are
the cheapest detector there is. Purged the stale cache and
re-ran; NZ then landed 5/5 on the grid.

## Part 2 — Locally-domiciled uncapped trackers

Foreign-listed trackers are capped by regulation (US RIC
25/50; UCITS 20/35) — see QA Q78/Q79 — so their weights
cannot be inverted. Only LOCAL funds escape both regimes.

| Market | Local plain-index tracker | Ticker | Uncapped? | Holdings |
|---|---|---|---|---|
| Taiwan | Yuanta MSCI Taiwan (元大摩臺) | 006203.TW | YES — TSMC 55.9% | Daily, T-1, scraped ✓ |
| Korea | Samsung KODEX MSCI Korea | 156080.KS | YES — replicates MSCI Korea | Daily (KRX/Samsung AM) |
| India | Kotak MSCI India ETF | NSE-listed | YES — tracks MSCI India | Daily (Kotak MF) |
| Japan | none confirmed tracking MSCI Japan locally | — | n/a | JPX lists TOPIX/Nikkei trackers instead |
| Australia | iShares MSCI Australia is UCITS (SAUS), not ASX-local | — | capped | — |
| Singapore | iShares MSCI Singapore (I19.SI) — local listing, but the US-style capped family | I19 | verify | Daily |
| HK / MY / TH / ID / PH / NZ | none found | — | — | — |

**Why the pattern:** a local plain-index tracker exists only
where domestic demand for "the foreign benchmark" is large
enough to fund a product — Taiwan, Korea, India. Elsewhere
local investors buy the local benchmark (TOPIX, ASX 200,
STI), so no fund reproduces MSCI weights.

**How to use them:** as a FRESHNESS overlay, never as the FIF
source. The MSCI constituents tool is ~2 months delayed;
these funds publish daily. Per GIMI §3.2.3 an above-threshold
corporate event moves the index — and therefore the fund —
the day it happens, so a jump in a local tracker's holdings
between MSCI publications is the earliest public signal that
a FIF/NOS change has been implemented. Below-threshold
changes never appear, because MSCI itself defers them.

**Validated for Taiwan (Q82):** 006203 weights vs Jun-1 MSCI
weights price-rolled to Jul-31 — median |diff| 0.022pp across
77 names. No implemented FIF change through Aug-7.

**Next (registered, not built):** run the same two-line check
on KODEX MSCI Korea and Kotak MSCI India before the Aug
review, to confirm no corporate event has moved a FIF in
those markets since the Jun-1 vintage.

## Part 3 — Scope check: member FIFs are NOT a prediction (c-146)

Bill asked to run the method across APAC and predict the
Aug-2026 changes. The honest boundary:

**What the inversion gives us: FIFs for CURRENT MEMBERS
only.** It inverts published index weights — a company with
no weight has no equation. That covers the DELETION side
(members falling below the size floor or the float gate,
exactly how Wan Hai was caught in Taiwan) and nothing else.

**What ADDITIONS need, per market:**
1. the full domestic listed universe with full caps (to find
   the 85% coverage crossing and the market cutoff);
2. floats for NON-members — precisely the names the inversion
   cannot reach;
3. ATVR liquidity, foreign room, listing age.
For Taiwan that took a dedicated PIT harvester off TWSE bulk
day-files. No equivalent exists for the other 12 markets, and
the Aug announcement is 2026-08-11.

**Therefore:** APAC coverage this cycle = member-side
(deletion) screening where FIFs recover cleanly; Taiwan
remains the only full add+delete prediction. Building the
other universes is a post-Aug project, market by market,
starting with the ones whose exchanges publish bulk
day-files (KR/IN/JP).

### Per-market data reality (c-146 venue probe, verified live)
| Market | Yahoo prices | Constituent weights | FIF route |
|---|---|---|---|
| Taiwan | .TW ✓ | ✓ | DONE 77/77 |
| New Zealand | .NZ ✓ | none | factsheet — DONE 5/5 |
| Singapore | .SI ✓ | ✓ | 8/16, mapping debt |
| AU / HK / IN / ID / JP / KR / MY / TH / CN | ✓ | ✓ | ready to run |
| **Philippines** | **NONE** | ✓ | **BLOCKED** |

**Philippines diagnosis (Bill's terminal run):** not a code
bug — Yahoo has no Philippine coverage at all. Every .PS
symbol (AC, BDO, SM, ALI, ICT) resolves to the empty "YHD"
venue with null price and null currency; .PH does not exist.
This matches the earlier registered finding ("PH Yahoo has
nothing"). The script now says so explicitly
(status NO_PRICE_SOURCE) instead of a bare INSUFFICIENT, and
reports how many names failed on price vs shares.
PH alternatives: PSE EDGE per-company disclosures (scrape),
investing.com, or a paid feed — registered, not built. PH is
2 names short on the ticker map as well (ICTSI, Meralco B).

## Part 4 — The harvester, hardened for a terminal run (c-148)

The code existed (`scripts/apac_fif_inversion.py`) but was
not fit for an unattended run. Four fixes, three of which
came from real failures:

1. **Progress + throttle backoff.** Every name now prints
   `[i/n] SYMBOL shares=ok px=ok`. After 5 and 10 consecutive
   share failures it pauses 60s; after 18 it stops with
   THROTTLED and tells you to re-run — the cache resumes.
2. **Resume bug (real).** Failed share lookups were being
   CACHED as null, so a re-run skipped exactly the names that
   had failed — the opposite of resumable. Failures are no
   longer cached.
3. **Grid-snap was landing on a WRONG MULTIPLE (real).**
   Indonesia exposed it: state-owned banks came out at 0.775
   and GOTO at 1.617 (impossible). With 10-20 names the 2.5%
   grid is too dense to pin the constant — many multiples fit.
   FIF > 1.02 is now infeasible, not merely penalised.
4. **The real fix — anchor on a published number.** Rather
   than inferring the constant from the grid, roll the
   PUBLISHED Jul-31 index float cap back to the weights' date
   using the membership's own float-cap-weighted USD return:

       IdxCap(Jun-1) = IdxCap(Jul-31) / R,  c = IdxCap/100

   Grid-snap is now a VALIDATION, not the calibration.
   Indonesia after the fix, checked against known ownership:
   Astra 0.398 (Jardine owns 50.1%), Barito Pacific 0.201
   (Prajogo ~71%), United Tractors 0.341 (Astra 59.5%),
   BBCA 0.394 (Djarum ~55%), Charoen Pokphand 0.368 (parent
   ~55%). Every one lands where the public ownership implies.
   Taiwan control unaffected (still recovers 33.27 vs 33.314).

**Correction to Part 1:** the Singapore FIFs published there
(DBS 0.649, SingTel 0.404...) came from the degenerate
grid-snap and are superseded by the anchored run — DBS 0.718,
OCBC 0.720, UOB 0.723, SingTel 0.448, SIA 0.470, Wilmar
0.253, CapitaLand Inv 0.463, Sembcorp 0.496. Coverage also
rose 8/16 -> 13/16 once the OVERRIDES table was seeded
(OCBC O39, ST Engineering S63, CICT C38U, CLAR A17U, plus the
US lines SE and GRAB).

### Commands for Bill's terminal
    py scripts\apac_fif_inversion.py status        # coverage
    py scripts\apac_fif_inversion.py all           # every
    py scripts\apac_fif_inversion.py all Korea Japan
    py scripts\apac_fif_inversion.py market India  # one
Re-run any command until `status` shows PASS everywhere; each
pass continues from the cache. Skip Philippines (no Yahoo
data). Expect several passes for China (576 names) and
Japan/India (~165 each) because of the get_info throttle.
