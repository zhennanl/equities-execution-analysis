# The Anticipation Clock — when pre-positioning starts (c-83)

*Module: scripts/anticipation_clock.py ->
data/anticipation_clock.json + reports/anticipation_clock.html.
DESCRIPTIVE CALIBRATION — timing for monitoring, not a graded
hypothesis; tradeable anticipation claims live in registry v3
(H11 family). Detection rule DECLARED in code: deletion-minus-
control median >= 0.25 ADV-days sustained 5 trading days.*

## Design

63-70 deletion name-events (33 reviews, 2015-2026), SBL borrow
balance relative to each name's own base period, in ADV-days;
controls = per-event median of all non-event watch names (the
market's ambient borrow drift); the clock = deletions minus
controls. Secondary panels: addition borrow-fade analog (n~40)
and cumulative T86 foreign net (the real-money leg — shorts
print in borrow, not in T86).

## Findings (with the caveats attached to them)

1. **98% of deletions show a detectable excess borrow build.**
   Pre-positioning is not occasional — it is the base case.
2. **By announcement day the borrow is ALREADY THERE: ~4.5
   ADV-days of control-adjusted build at day 0** — against
   typical forced demand of 6-20 ADV-days, a third to half of
   the print's needs are borrowed before MSCI says a word.
3. **The ann->eff window adds almost nothing at the median**
   (4.0-4.6 at ann vs ~4.2 at eff): the deletion game is
   substantially pre-announcement. Window-level CH1 (which
   measures build SINCE announcement) therefore understates
   pre-positioned supply exactly as the CH1b standing-base
   refinement anticipated — this study is CH1b's empirical
   justification.
4. **The start is LEFT-CENSORED at both lookbacks tried** (-60:
   start -42; -120: per-name median start -99.5, hugging the
   baseline edge). Builds begin 5+ months out for many names.
   HONESTY LIMIT: at that distance, "this-review anticipation"
   blends with chronic shorts riding a declining stock —
   deletion candidates fall for months by construction. The
   clean index-specific readings are the LEVEL at announcement
   and the window increment, not the raw start day.

## Desk implications

- Monitoring must switch on with the CANDIDATE LIST (T-60 or
  earlier), not with the announcement — by announcement the
  positioning story is mostly written.
- Pre-event marketing (Phase-0, Q50/Q52): the clock is the
  evidence that a desk publishing candidate + crowding color
  two months early is describing positioning that actually
  exists at that horizon.
- Aug-2026 use, declared now: for the Aug-11 candidates, the
  standing borrow base AT announcement (not window build) is
  the primary CH1 supply reading.

## Registered refinements (not built)

- Matched-decline controls (control names matched on trailing
  6m return + size) to separate index anticipation from
  fundamental shorting of decliners.
- Era split (pre/post 2020) and QIR-vs-SAIR split.
- The addition fade-clock read properly (n=37-40 curves exist
  in the artifact).
