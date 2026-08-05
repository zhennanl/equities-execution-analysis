# How the Index Review Prediction Engine Runs — Step by Step

*Session 9i (2026-08-04). Exported from the methodology discussion.
Companion docs: EXPLAINER_INDEX_REVIEW_FOR_TRADERS.md (plain-language
version), TW_FUNNEL.md (May-2026 graded walkthrough with name
journeys), PREDICTION_ENGINE_REVIEW_2026.md (accuracy audit).*

## The premise: MSCI publishes the rules, not the answers

The [GIMI Methodology book](https://www.msci.com/eqb/gimi/stdindex/methodology.html)
(~250 pages, May-2026 edition) is public and binding — universe
construction, the 85% coverage rule, size-segment cutoffs, buffer
zones (§3.1.5.1), review procedures. Our engine is a
re-implementation of that published arithmetic, not a statistical
guess.

What is NOT public, pre-announcement: MSCI's official GMSR value
(published only with results), their internal free-float estimates,
the exact price-cutoff date (one of the last 10 business days of the
prior month, unannounced), and licensed constituent files. Every
graded prediction error traces to one of these input gaps — never to
the rules.

## The engine, step by step

1. **Assemble the market universe** — every listed stock per market
   from public exchange lists, with price, shares, and our own
   free-float estimate (yfinance + exchange filings). Refresh
   caps/shorts on every run (freshness guarantee, TTL 4h).

2. **Verify current membership** — reconstruct who is already in the
   index from public ETF holdings and our archives. No call ships
   against an unverified member list.

3. **Rebuild the size cutoff (GMSR)** — rank all stocks by full
   market cap, walk down the ladder until cumulative free-float
   coverage hits 85% of the market. The cap at that line is our GMSR
   estimate (an *estimate*, labeled as such — MSCI's official number
   differs slightly).

4. **Apply the published hurdles** — non-members with cap ≥ 1.8×
   GMSR (QIR) or ≥ 1.15× (SAIR) become ADD candidates; members below
   0.5× GMSR become DELETE candidates; below ~2/3 they enter the
   hazard zone (decade-measured: only ~2/3 of hazard names actually
   convert). Apply liquidity/float screens and the A-share 20%
   inclusion factor.

5. **Layer measured provider behavior** — things the rulebook
   doesn't tell you but a decade of graded reviews does: churn
   buffers, SAIR-only migration sweeps (62–90% of deletions),
   per-market×review base rates (L8 priors), hazard-velocity tags
   from 3-month cap decline.

6. **Convert to probabilities** — for each candidate,
   p = P(any change this review) × visible share × proximity softmax
   to the hurdle. The unobservable mass (names below our data floor —
   13 of 21 recent TW changes) is carried explicitly as BLIND_SHARE,
   not hidden.

7. **Self-check against history** — two-sided decade-consistency
   test: if our call count sits outside the market's historical
   range (too many OR too few), the engine flags itself
   (OUTSIDE_HIGH/LOW) rather than silently shipping.

8. **Lock and grade** — the registry locks before announcement day;
   after MSCI announces, every call including the zeros is graded
   publicly (May-2026: 17/17 adds at point-in-time, deletes ~90%
   with each miss traced to a named data gap).

## One-line summary for a trader

Public rules + public data + measured provider behavior + honest
probability on what we can't see, graded every review.

## Where each step maps to the GIMI book

| Engine step | GIMI May-2026 |
|---|---|
| 1 Universe | §3.1.1–3.1.2 (equity universe refresh, investability screens) |
| 2 Membership | — (ours: the Feng Tay verification gate) |
| 3 GMSR walk | §2.3.2 p.24 (GMS Reference; Range = 0.5×–1.15×), §2.3.5, Appendix X |
| 4 Hurdles | §3.1.4–3.1.5 (cutoffs, segment assignment), §3.1.5.1 p.44 (buffer zones), §3.1.2.4/§3.1.6.2 (retention grace) |
| 5 Behavior priors | — (ours: decade-measured frequencies the book doesn't state) |
| 6 Probabilities | — (ours: L8 graded record) |
| 7 Consistency check | — (ours) |
| 8 Lock & grade | — (ours: honesty protocol) |

The book is the golden standard for the *rules*; prediction quality
is decided by input estimation and measured behavior — which is
where the graded record lives.
