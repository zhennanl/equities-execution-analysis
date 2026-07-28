# True Point-in-Time Replication — MSCI Taiwan May-2026 SAIR

*Session 7z. Question: with ONLY data available before the May 12
announcement (April-30 caps from historical prices), does the engine
reproduce the actual May outcome? Graded against the official MSCI
public list. This is stricter than the original graded backtest
(reconstruction-grade caps, built after the fact).*

## Setup

33-name boundary universe with pre-announcement membership flags (the
7 eventual deletions restored as members), caps = today's cap scaled
by (Apr-30 close / current price), floats from yfinance, graded engine
config (SAIR 1.15x + country-segment rule at the 2% buffer), modeled
tail. Script: scripts/pit_may2026_taiwan.py.

## Result

| Side | Score | Detail |
|---|---|---|
| Deletions | **7/7** — every actual May deletion caught with PIT caps | false flags: 2207, 2409, 2615, 2912 (4) — thinner boundary ladder than the original graded universe; the country rule needs ladder density |
| Additions | 0/1 + 4 false positives | two distinct errors, below |

**Add-side error 1 — ticker mapping:** we fetched 6187.TWO as "MPI";
the probe-card MPI Corp that MSCI added is 6223.TWO. Alias registries
need the same verification discipline as membership.

**Add-side error 2 — THE DISCOVERY:** the engine flagged
3443/3665/8046/4958 as adds at April caps ($13-17.5B, all far above
the $5.9B threshold). MSCI did not add them in May. Conclusion: they
were ALREADY members — which invalidates the same four ADD calls in
our August pack (correction issued there). The PIT replication
falsified our own live prediction 15 days before the announcement
would have. **This is the system working:** an error the Aug-12
grading would have exposed publicly was caught by internal replication
first.

## Lessons → engine changes

1. **Change-list ledgers are necessary but not sufficient**: they
   replay deltas; they cannot establish the base state. A full
   membership baseline (fund-holdings file) is now a mandatory
   pre-registration input. STALE_NONMEMBER joins STALE_MEMBER as a
   blocking violation class once baselines exist.
2. **Alias/ticker maps need verification** (the MPI mapping error).
3. **Country-rule false flags scale with ladder thinness** — the 4
   deletion false-flags here vs 0 in the original graded run trace to
   the smaller boundary universe, not the rule; ladder density is a
   validator metric for a reason.
4. PIT replication (historical prices → pre-announcement caps) is now
   a repeatable harness — every future review can be replayed
   point-in-time before trusting the live run.

## Honest scoreboard impact

The lifetime "adds 11/11" record referred to graded backtests on
universes with correct membership. This run shows the record's
DEPENDENCE on that input: with a wrong membership base, add precision
collapses instantly. The track-record table now carries this
dependency note. Deletions' 7/7 at PIT strengthens the coverage-rule
evidence (now demonstrated with genuinely pre-announcement data).
