# Event EDA Playbook — repeatable per-review exploratory analysis (c-82)

*How to reproduce the per-event data view for ANY review in the
registry. Module: scripts/event_eda.py. First output:
reports/event_eda_20260529.html (MSCI 2026-05 SAIR).*

## The command

```
py scripts\event_eda.py                        :: May-26 default
py scripts\event_eda.py "MSCI 2026-02 QIR"     :: any registry key
```

Output: reports/event_eda_<eff>.html (open in a browser; plotly
interactive) + a .json with the numbers behind it.

## What each step does (the repeatable procedure)

1. **Resolve the event** from agents/time_machine MSCI_TW:
   announcement date, effective date, adds/deletes. (May-26
   SAIR: ann 2026-05-12, eff 2026-05-29, 0 adds, 7 dels.)
2. **Set the clock per name** from the vintage price series:
   window = 15 trading days before announcement -> 10 after
   effective; baseline ADV = mean volume of the 30 trading days
   ending the day BEFORE announcement (PIT — never includes
   window days).
3. **Assemble the day-panel per name** from the decade caches:
   close/volume (vintage), SBL balance, T86 foreign net and
   domestic-institutional net (total minus foreign — combined
   trusts+dealers, the layout-safe extraction), margin
   long/short balances (raw idx 5/11, lots x1000), day-trade
   volume (raw idx 2; nf=2 stubs -> 0), block volume (sum of
   trade rows).
4. **Normalize** everything by baseline ADV (days-of-ADV) or by
   float shares (margin) so names are comparable.
5. **Estimate forced demand** = lambda 0.093 x float shares.
   Float tiers: v2 named-insider for current members; DEFAULT
   0.55 for ex-members, marked with * in the table (upgrade
   path: extend the insider harvest to event names PIT).
6. **Join the print anatomy** from auction_expost (pressure
   bps, T+1 revert) for the effective day.
7. **Render** 8 charts + the summary table to one HTML
   (dashed line = announcement, solid = effective close).

## Reading the May-2026 output (worked example)

- **Forced est vs realized T-day volume** track well for most
  names (1102: 18.7 est vs 21.1 realized; 1402: 19.6 vs 23.7;
  2633: 53.5 vs 41.4) — the lambda model's sanity visible in
  one column. 2324 realized 14.7 vs 4.7 est = the crowding
  case: the tape carried 3x the naive forced estimate (the
  squeeze; see CASE_2324).
- **Print pressure**: negative for 5 of 7 deletes = the close
  printed ABOVE the last continuous price (favorable to the
  forced seller) — the Q38 against-the-flow pattern, visible
  name by name.
- **T+1 revert**: 2324 +995 bps and 2474 +983 bps = the
  post-print bounce/crack anatomy from the case study.
- **SBL chart**: 2324's standing borrow base dwarfs the others
  (the 440M shares) — the borrow-visible channel in one look.

## Honesty rules for this artifact

DESCRIPTIVE ONLY — the EDA shows data, it grades nothing.
Anything interesting seen here that is not already in the v5
registry goes to v6 and waits for the next data vintage
(protocol rule 8). Default floats are starred; the domestic-
institutional line is labeled combined (T86 layout differences
across eras make trust/dealer splits an analysis-time task not
yet done); forced est uses the SINGLE lambda 0.093 (the
quartile band exists in perstock_flow_model.json — the print
RANGE methods live in the advisory, not here).

## Extending

- Another market: needs that market's caches (see
  market_profiles activation path) — the script's structure
  transfers; the cache readers are the adapter.
- More charts: add a fig in render(); keep normalization
  by ADV/float so cross-name reading survives.
- The 2015-2026 sweep: loop registry keys; the panel builder is
  the same (that run belongs with the v5 grading protocol, not
  ad-hoc EDA).
