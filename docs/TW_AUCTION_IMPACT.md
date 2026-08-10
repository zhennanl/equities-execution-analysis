# Price impact of the closing auction itself

Generated 2026-08-10T10:25:50.

`impact = close(13:30 bar) / close(13:20 bar) - 1` — the call print against the last continuous price. The 13:25 bar is the frozen pre-auction interval and is not used (64 bars in the whole panel carry volume there).

IQR width is p75 minus p25 — the span the middle half of events fall inside. `abs p90` is the 90th percentile of the ABSOLUTE impact: nine events in ten move the price by less than this across the auction, either way.

| side | day type | n | p25 | median | p75 | IQR width | abs p90 | max abs |
|---|---|---|---|---|---|---|---|---|
| ADD | effective | 15 | -1.04% | -0.25% | +0.52% | 1.56% | 1.82% | 2.06% |
| ADD | control | 1,041 | -0.24% | +0.00% | +0.22% | 0.45% | 0.67% | 2.11% |
| DEL | effective | 26 | -0.98% | +0.00% | +1.05% | 2.02% | 1.78% | 3.13% |
| DEL | control | 1,820 | -0.27% | +0.00% | +0.16% | 0.43% | 0.62% | 4.90% |

## The finding

**The auction does not move the median price. It roughly quadruples the uncertainty.** The middle-half width goes from 0.45% to 1.56% on additions (3.4x) and from 0.43% to 2.02% on deletions (4.7x), while both medians stay within a quarter of a percent of zero.

For a desk that is the useful shape: crossing in the close is not systematically expensive, it is systematically UNCERTAIN, and the risk is two-sided rather than a predictable cost to be budgeted.

## Why this replaces close-vs-VWAP as the impact measure

An index mover puts 79% of its effective-day volume through the call. The auction is therefore most of the VWAP, and comparing the close to the VWAP compares the auction to itself.

- measured close vs VWAP: **-0.060%**
- scaled by 1/(1 - 0.79) = 4.8x: **-0.286%**
- directly measured against the last continuous price: **-0.251%** (additions)

The arithmetic reproduces the direct measurement, which means the small close-vs-VWAP number was an artefact of the benchmark, not evidence that the auction is cheap.

## The five largest single-event impacts

| rev | code | name | side | effective | impact |
|---|---|---|---|---|---|
| Feb26 | 2105 | CHENG SHIN RUBBER IND | DEL | 2026-02-26 | +3.13% |
| May26 | 1402 | FAR EASTERN NEW CENTURY | DEL | 2026-05-29 | +2.81% |
| Nov25 | 2360 | CHROMA ATE | ADD | 2025-11-24 | -2.06% |
| Nov25 | 2368 | GOLD CIRCUIT ELECTRONICS | ADD | 2025-11-24 | -2.00% |
| Feb24 | 8454 | MOMO.COM | DEL | 2024-02-29 | -1.88% |

## Limits

- **No market adjustment.** The panel carries no index series, so a market-wide move in the last ten minutes sits inside every number.
- **n = 15 additions and 26 deletions** with usable bars. Dispersion is readable at that size; the medians are not precise and no p-value is quoted.
- **IB bars, not TWSE's own tape.**
