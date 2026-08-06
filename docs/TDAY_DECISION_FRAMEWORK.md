# T-Day Decision Framework — Early vs MOC + the Attention Budget (c-75)

*Step 3 of the lifecycle: the effective date itself. Module:
`agents/tday_decider.py` (tested). Everything below is DECLARED
— split priors and thresholds are on record before Aug-2026
grades them.*

## The decision, framed as economics

The benchmark IS the close, so 100% MOC = zero tracking error by
definition. Trading early is a purchase: you pay impact plus
tracking risk, and the only thing you can buy with it is escape
from an ADVERSE close dislocation. So the rule is one
inequality:

    trade early only if E[adverse dislocation at the print]
        > impact cost of the early leg + the client's
          tracking-error tolerance

Our own measurements set the default: the print usually moves IN
FAVOR of the forced side (deletes close +45 bps above the last
tape, adds below it — Q38). The base case is therefore MOC, and
deviation needs a named, scenario-specific reason. The tool's
job is to produce that reason or stay quiet.

## The split table (declared priors, by v2 scenario)

| Scenario | Split (early/MOC/T+1) | The named reason |
|---|---|---|
| SQUEEZE-RISK | 0 / 1.0 / 0 | the cross clears in your favor — don't pre-trade into your own tailwind |
| COMMITTED | 0 / 1.0 / 0 | the median case: the print helps you; MOC is the trade |
| OVERSUPPLIED | 0.2 / 0.8 / 0 | clean print, post-print crack risk (2324) — don't hold past T |
| PARTIAL | 0.3 / 0.7 / 0 | cross depth unproven — moderate early leg |
| TOLL-DEPENDENT | 0.5 / 0.5 / 0 | the ONE adverse scenario: no committed supply, discount print expected — early trading buys real edge |

Mandate gate first: MOC-only clients get (0,1,0) always; the
scenario split ships as labeled advice. Every plan logs its
prediction (status DECLARED) so forward events grade the table.

## Four decision moments — everything else is monitoring

T-1 plan lock -> 09:00 confirm (gap/news only) -> 13:00 pace +
drift digest -> 13:20 final peel call -> (13:25-13:30 is
monitor-only; the auction is watched, not decided). A busy
trader makes four choices per event day, at known times, from
one-page digests.

## The alert contract (attention is the scarce resource)

- **SILENT** is the default state and most names stay there.
- **AMBER** never interrupts — it batches into the checkpoint
  digests (one line per name).
- **RED** interrupts, under three constraints: only 4 trigger
  classes (dislocation >= p90 of our measured distribution =
  281 bps; indicative at the price-limit band; 13:00 volume
  pace < 0.5x forecast floor; halt/news); fires on STATE
  TRANSITIONS only (a name that stays bad never re-alerts);
  hard budget 5/day — overflow collapses into ONE MARKET-MODE
  banner ("event-wide stress") instead of per-name spam,
  because if everything is red the information is the regime,
  not the names.
- Thresholds are percentiles of data/auction_expost.json (p75
  amber = 146 bps, p90 red = 281 bps), recomputed as the panel
  grows — the alert line moves with evidence, not mood.

## Signals feeding the engine (all existing or queued)

T-1: v2 supply decomposition (scenario per name), print ranges
M1-M4, borrow standing base, SSF OI capture. 13:00: cumulative
volume vs forecast floor (pace), drift vs event basket. 13:20:
peel decision inputs frozen. 13:25+: 5-sec indicative capture ->
dislocation vs range mid + limit-band proximity (the RED feeds).
Market-wide MI_5MINS arrival curve = the baseline that says
whether a name's auction is unusual or the whole market is.

## What gets graded (Aug-2026 forward)

Per event: (1) split-table EV vs 100%-MOC per scenario cell;
(2) RED precision — fraction of REDs a trader would call
worth the interruption (target > 1/2); (3) digest
sufficiency — decisions changed at checkpoints vs between them.
The alert engine is a forecasting system for "does this deserve
attention"; it gets Brier-graded like every other forecast.
