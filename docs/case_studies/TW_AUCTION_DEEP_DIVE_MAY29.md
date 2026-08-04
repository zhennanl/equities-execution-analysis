# Taiwan Closing Auction Deep Dive — May-29 MSCI Effective Day
*Session 8r. Full 5-second official series (TWSE MI_5MINS), event day vs three baselines. Caveat: accumulated order volumes are gross entries (cancels not netted) — consistent across days, so comparisons stand.*

## 1. Where the day traded — the volume curve and the lunch checkpoint

|     date | day      |   12:00 |   13:00 |   13:24 |
|---------:|:---------|--------:|--------:|--------:|
| 20260526 | baseline |    77.6 |    88.7 |    95   |
| 20260527 | baseline |    73.4 |    88.6 |    95.4 |
| 20260529 | EVENT    |    58.9 |    68.9 |    75.1 |
| 20260605 | baseline |    76.3 |    86.4 |    94   |

**Lunch checkpoint, validated on a real event day:** at 12:00 the event day had printed 0.94x the baseline-median value for that time; the FULL day closed at 1.23x baseline. The noon run-rate UNDERSTATES the final multiple by the auction's share — because the event's flow concentrates in the print, the morning tape looks deceptively normal. Desk rule refined: the lunch read must compare against `expected multiple x (1 − expected auction share)`, not the raw multiple — otherwise every event day reads 'thin' at noon and triggers a false resize.

## 2. The five minutes that set the price — order RETENTION inside 13:25-13:30

*Finding about the data itself (recorded, not hidden): accumulated order volume FALLS during the call window — the counter nets out cancels/purges, so order ARRIVAL cannot be read from this field. The decline itself is the signal: it measures how much resting interest is withdrawn before the match.*

|     date | day      |   book_at_13:25_Mshares |   withdrawn_into_match_% |
|---------:|:---------|------------------------:|-------------------------:|
| 20260526 | baseline |                    66   |                     24.1 |
| 20260527 | baseline |                    66   |                     23.4 |
| 20260529 | EVENT    |                    62.6 |                     13.8 |
| 20260605 | baseline |                    59.5 |                     24.7 |

**Read:** baselines withdraw ~24% of the resting book before the match; the EVENT day withdrew only ~14% — event-day order flow is COMMITTED (MOC obligation stays to trade; the fair-weather quotes that normally pull, trade instead). Desk translation: on rebalance day the 13:25 indicative is MORE trustworthy than on normal days, because less of the book behind it will vanish — the one day the crowd cannot blink is the day the preview means what it says.

## 3. The imbalance walk into the close

|     date | day      | bid/ask ratio walk                        |
|---------:|:---------|:------------------------------------------|
| 20260526 | baseline | 13:00 1.567 -> 13:24 1.523 -> 13:30 1.302 |
| 20260527 | baseline | 13:00 1.470 -> 13:24 1.484 -> 13:30 1.267 |
| 20260529 | EVENT    | 13:00 1.574 -> 13:24 1.582 -> 13:30 1.333 |
| 20260605 | baseline | 13:00 1.532 -> 13:24 1.536 -> 13:30 1.306 |

**Read alongside the known outcome (auction −41 bps, sell-side event):** gross order-entry ratios stay bid-heavy on all days (retail bid clutter), so the LEVEL is uninformative — but the event day's ratio DROPS into the close while baselines hold or rise: the DIRECTION of the walk carries the signal. Desk translation: on the live feed, watch the imbalance DELTA between 13:00 and the indicative, not its level.

## What this adds to the playbook

1. **Lunch-checkpoint correction term** — compare run-rate to `mult x (1 − auction share)`; raw comparison false-alarms on every auction-concentrated event.
2. **Event-day books are committed** — only ~14% of resting interest withdrew before the match vs ~24% on baselines: the rebalance-day indicative is MORE reliable than normal, strengthening the 3.3 close-read rule.
3. **Watch imbalance deltas, not levels** — gross bid clutter makes levels lie; direction into the window told the truth on the event day.
4. All three now parameterize the replay simulator and the Sep-1 run-sheet.
