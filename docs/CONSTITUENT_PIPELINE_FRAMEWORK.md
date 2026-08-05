# Constituent Pipeline Framework — Free Public Reconstruction of MSCI Country Membership

*Session 9i (2026-08-05). Generalizes the Taiwan pipeline (three-fund
unanimity, May-26/Nov-25 delete pools validated 7/7 + 7/7) to every
APAC review market. Everything here was executed and verified live —
observed counts below are from the actual harvest, not documentation
promises. Data: `data/apac_members.json`
(scripts/apac_members_harvest.py); TW deep sources:
`data/tw_membership_sources.json`.*

## 1. The principle

MSCI licenses constituent lists, but index-tracking funds must
PUBLISH their holdings — so membership is observable for free from
the funds themselves, triangulated:

- **PRIMARY anchor** — the single-country iShares MSCI ETF. These
  track 25/50-capped variants (US RIC tax rule): capping changes
  WEIGHTS, never MEMBERSHIP, so the holding list ≈ the Standard
  index membership.
- **CROSS-CHECK** — the composite subset. By the building-block
  principle (composites are unions of country Standard indexes),
  EEM's holdings filtered to `Location = Taiwan` is a SECOND
  observation of MSCI Taiwan membership from a different fund.
  EM markets cross-check against EEM; DM markets against EFA.
- **THIRD source (market-specific, optional)** — a locally-listed
  MSCI tracker from an INDEPENDENT manager (e.g. Yuanta 006203 for
  TW via MoneyDJ quarterly disclosure). Breaks the
  both-funds-are-BlackRock caveat.
- **CONSISTENCY ARBITER** — the official review change lists
  (STPublicList archive): membership must reconcile with the
  add/delete history and the factsheet count. TW proof: pre-May
  count 83 − 7 deletes + 1 add = 77 = the three-fund unanimous set.

## 2. Source table (verified live 2026-08-05)

| Market | Anchor fund (product id) | Variant | Composite / Location | Observed: anchor / composite / confirmed |
|---|---|---|---|---|
| Japan | EWJ (239665) | Standard 25/50 | EFA / "Japan" | 168 / 168 / **168 — perfect** |
| Australia | EWA (239607) | Standard 25/50 | EFA / "Australia" | 47 / 47 / **47 — perfect** |
| Hong Kong | EWH (239657) | Standard 25/50 | EFA / "Hong Kong" | 25 / 25 / **25 — perfect** |
| Korea | EWY (239681) | Standard 25/50 | EEM / "Korea (South)" | 78 / 77 / 77 (1 anchor-only) |
| Taiwan | EWT (239686) | Standard 25/50 | EEM / "Taiwan" | 79 / 77 / 77 (+ Yuanta 006203 unanimous) |
| China | MCHI (239619) | Standard 25/50 | EEM / "China" | 573 / 574 / 571 (5 diffs — CA churn, normal at this breadth) |
| India | INDA (239659) | Standard 25/50 | EEM / "India" | 165 / 165 / **165 — perfect** |
| Malaysia | EWM (239669) | Standard 25/50 | EEM / "Malaysia" | 21 / 21 / **21 — perfect** |
| Indonesia | EIDO (239661) | **IMI** (superset!) | EEM / "Indonesia" | 66 IMI / **11 Standard** (composite is primary) |
| Philippines | EPHE (239675) | **IMI** (superset!) | EEM / "Philippines" | 34 IMI / **10 Standard** (composite is primary) |

CSV endpoint pattern (all funds):
`https://www.ishares.com/us/products/<product_id>/<slug>/latest-holdings.csv`

## 3. The recipe, step by step

1. **Fetch the anchor CSV**; validate the fund NAME in row 1 (we
   found three wrong product-id guesses this way — the header check
   is mandatory, not optional).
2. **Parse equity rows only** (`Asset Class == "Equity"`), keep
   ticker + name as published. Ticker conventions differ: numeric
   for JP/TW/KR/HK/CN lines, alpha for AU/IN/MY/ID/PH.
3. **Fetch the composite** (EEM or EFA) once, slice by `Location`.
   Location strings are NOT obvious — Korea is `"Korea (South)"`;
   always print the Location histogram before assuming.
4. **Tier the names**: CONFIRMED (both funds) / LIKELY (one fund) /
   FLAGGED (change-history says member, no fund holds — TW's 4551).
5. **Reconcile the count** against the MSCI factsheet, remembering
   the factsheet may be one review stale (the 83-vs-77 lesson:
   pre-review count − deletes + adds must equal the fund count).
6. **Reverse-roll to any PIT date** through the official change
   lists (add after date → not yet member; delete after → still
   member). Requires the market's alias bridge (TW: 135/136
   print-verified; JP: 166/181; CN: built; KR/IN: queued).
7. **Refresh cadence**: iShares CSVs update daily with ~1-2 day
   lag; before an announcement the list is current because reviews
   only change membership at effective dates — the exception is
   corporate events (M&A exits mid-quarter), which the fund
   reflects immediately and the change lists never mention: treat
   fund-vs-history divergences as corporate-event candidates, not
   errors.

## 4. Known traps (all hit and solved during the build)

- Wrong product id serves a DIFFERENT fund with a 200 status —
  validate the name header every fetch.
- Some responses are gzip — use compressed fetch.
- EIDO/EPHE track IMI (Standard + Small Cap): their lists are
  SUPERSETS. For these, the composite subset IS the Standard
  membership; the IMI extra names are the Small-Cap set (useful
  separately for IMI-tracker flow logic).
- Same-manager correlation: EEM/EFA/anchor are all BlackRock —
  add a local independent fund per market where stakes are high
  (TW: Yuanta 006203; JP candidates: Nomura/Daiwa MSCI trackers;
  KR: Kodex MSCI Korea; IN: local MSCI trackers are rare — UTI
  Nifty is FTSE/Nifty, not usable).
- Local-fund disclosure is often QUARTERLY (TW: full list at
  quarter-end, top-5 monthly) — date-align before diffing.
- A-share lines in MCHI/EEM carry exchange-suffixed or local codes;
  keep raw and map through the existing CN alias machinery.

## 5. The pre-announcement delete pool (the goal)

For each market, one day before the announcement:

1. Members = CONFIRMED ∪ LIKELY ∪ FLAGGED (inclusive by design —
   anchor imperfections may WIDEN the pool, never silently narrow
   it).
2. Cap each member (current caps for the live event: price × shares
   via yfinance/FinMind; PIT vintage caps where held — TW solved
   via FinMind; JP/KR/IN vintage sources queued: J-Quants, KRX,
   NSE archives).
3. Ladder ascending; pool = members below ~1.15× the market's GMSR
   estimate (buffer-band edge, generous on purpose).
4. Attach the measured features: 12-month cap glide (deleted names
   median −22% in TW EDA), foreign-flow direction (−4.1pp median
   into TW deletes), hazard velocity, time-in-zone.

Validation standard before any market's pool is trusted: replay the
last two reviews with known keys and require every official deletion
inside the pool (TW: May-26 7/7 EXACT bottom-7; Nov-25 7/7 in
bottom-8 — the historical 0/7 breadth failure, structurally fixed).

## 6. What this unlocks per market

Same as TW: PIT workbench frames, delete-pool validation, the
retention classifier's training negatives (cutline survivors), and
live Aug-2026 pools for every market in the review — including the
markets where our named universes were previously boundary-only
(the China OUTSIDE_LOW self-flag was breadth, same as TW's).
