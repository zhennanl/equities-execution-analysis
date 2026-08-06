# Multi-Market Denominator Design — the per-market 85% cutoff (c-78)

*How to compute, for each APAC market, the total free-float
investable market cap (the MIEU denominator) that the 85%
coverage walk needs. Design only — build follows the priority
order at the end.*

## Terminology fix first (so we compute the right thing)

The GMSR itself is GLOBAL and needs no per-market denominator:
it comes from the DM universe ranking (May-2026: $15.75B; EM
reference = half). What each MARKET needs is its own 85%
COVERAGE CUTOFF — the line where the cumulative free-float walk
crosses 85% of that market's investable total — which the GMSR
corridor (0.5–1.15× the reference) then disciplines. The
denominator is the market-local input; the corridor is the
global constraint. This doc designs the denominator.

## The three-layer architecture (generalizing what Taiwan proved)

**Layer A — factsheet inversion (DONE, all 10 markets).**
D_A = index float-cap ÷ 0.85. Zero extra data; already in
apac_factsheet_archive.json. Weakness: assumes the index sits
exactly at 85% coverage when banding lets it drift ~80–90% —
so D_A carries a ±6% structural band, not a point.

**Layer B — member-based (script EXISTS, runs pending).**
Sum the members' float-adjusted caps (member census: caps via
resolver, floats via the market's float source) and divide by
0.85. Same banding caveat, but it PRICES the numerator from
live data instead of trusting the factsheet's vintage — A and B
disagreeing flags stale factsheets or float errors.

**Layer C — full census (TW gold standard; the design target).**
Enumerate the market's investable universe, apply the GIMI
screens (size, float ≥ 0.15, ATVR, frequency), sum float ×
shares × price. This is measurement instead of inversion. Per
market it needs four inputs, and THIS is where markets genuinely
differ:

| Market | Universe list (official, free) | Shares | Float source (quality tier) | Universe size |
|---|---|---|---|---|
| Korea | KRX data portal day-files (all names, cap included) | KRX | DART large-holder filings (named) / yahoo | ~2,700 |
| India | NSE/BSE equity lists | exchange | promoter shareholding patterns — NAMED quarterly, v2-grade | ~2,000 liquid |
| Japan | JPX monthly listed-issues CSV | JPX/yahoo | EDINET large holders / yahoo est | ~3,900 |
| China | SSE+SZSE lists | exchange | exchanges publish TRADABLE shares (reform legacy — a shortcut TW never had), but MSCI further cuts Connect-ineligibility: two-stage float | ~5,300 |
| Australia | ASX listed-companies CSV | yahoo | yahoo est | ~2,000 |
| HongKong | HKEX list of securities | HKEX shares-in-issue | CCASS custody distribution as float hint + yahoo | ~2,600 |
| MY / ID / PH | Bursa / IDX / PSE lists | yahoo | yahoo est, default + band (weakest) | ~1,000 / ~900 / ~280 |

Engine: ONE census core (the mieu_census phases: universe →
fund → tape → floats → report) + per-market adapters (universe
provider, symbol resolver — already built for all 10 in the
member census, shares source, float source). The adapter is the
only market-specific code; the screens and the walk never fork.
Each market's float source keeps its market_profiles quality
tag; default-float exposure is reported (of_which_default_float)
exactly as TW's report does.

## Validation: triangulate, never trust one frame

Per market, the walk runs under D_A, D_B, and (where built) D_C.
The TW lesson generalizes: the three frames disagree by single-
digit percents and the cutline verdicts that matter must hold
under ALL available frames (frame-robust policy, already in the
registry). Acceptance per market: |D_C − D_A| ≤ ~6% (the banding
allowance) validates both; a bigger gap points at floats first
(check the default-float share), then at the universe screens.

## Priority order (value ÷ effort, not alphabetical)

1. **Korea** — EM corridor (where cutline trades live), official
   free day-files with caps, decent float path via DART.
2. **India** — EM corridor + the best float data in Asia
   (promoter patterns are named, quarterly, mandatory).
3. **Japan** — DM anchor: validates the corridor's DM end
   against the biggest universe; JPX lists are clean.
4. **China** — biggest and hardest; the tradable-shares
   shortcut helps but the Connect second stage means D_C_China
   carries a wider band. Do after the method is proven twice.
5. **AU / HK** — DM, deep floats, factsheet inversion is likely
   sufficient (Layer A/B agreement expected); census only if
   they disagree.
6. **MY / ID / PH** — smallest EM universes but weakest float
   data; Layer B + wide bands may be the honest end state
   (a census with default floats measures little).

## Effort estimate

Adapters reuse the member-census resolvers, so the marginal
build per market is the universe provider + shares source
(~half a day each), then unattended harvest time (yahoo-paced:
Korea/India ~2–3h, Japan ~4h, China ~6h+). Recommendation:
build Korea's adapter first as the template, validate D_C_KR
against D_A_KR, then stamp the pattern.

## Addendum (c-80): official per-stock float sources — the survey (Q47)

Researched: which markets publish a STANDARD float estimate for
ALL listed companies. Graded for census feasibility:

| Market | Official all-market float source | Grade |
|---|---|---|
| India | NSE/BSE mandatory QUARTERLY shareholding patterns (promoter vs public) — structured, free, bulk | **A** |
| Japan | JPX publishes TOPIX Free-Float Weight (FFW) per constituent (~all Prime/Standard names post-2022 reform); monthly component-weight files free, daily feed paid | **A-** |
| Korea | KRX computes free-float ratios for all listed (KOSPI FF weighting); data.krx portal serves them — POST-form scraping, menu TO_VERIFY | **B+** |
| China | Exchanges/CNINFO publish TRADABLE share counts (official, free); index-grade float needs a second stage stripping >5% strategic holders from top-10-holder filings (also public) | **B** |
| Taiwan | NO official per-stock float file (TAIEX is FULL-cap weighted; FTSE/MSCI floats are licensed) — hence our v2 named-insider method (validated 0.022) + implied top-10 FIFs. Already the best available | **B** |
| Philippines | PSE Public Ownership Reports — mandatory quarterly per company on PSE Edge, but document-level scraping | **B-** |
| Indonesia | IDX tracks float (15% listing rule, FF-weighted indices); a BULK per-stock file TO_VERIFY — may be in the monthly statistics | **C+** |
| Hong Kong | No official ratios; bounds only (25% public-float listing rule) + CCASS custody distribution as a proxy | **C** |
| Australia | Nothing official; vendor estimates or parsing ASIC substantial-holder notices | **C** |
| Malaysia | Nothing official; licensed index floats only; vendor estimates | **C** |

Consequence for the priority order: India and Japan RISE
(official float data removes the hardest census input entirely);
Korea holds; AU/HK/MY confirm as Layer-A/B markets where a
census would mostly re-discover vendor estimates. The corrected
walk (cutoff_walk_v2) + an A-grade float source = a
fully-measured cutoff for India and Japan at TW-level rigor
without inventing a float method.

## What this unlocks

Per-market cutoff corridors move from "implied, single-frame"
to "triangulated" — the same upgrade that took Taiwan's Aug-26
call from a guess to a frame-robust verdict. Combined with the
market_profiles activation path (float source and lambda refit
per market), this is the Step-1 half of taking a second market
live.
