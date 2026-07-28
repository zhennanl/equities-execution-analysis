# Case Study — Reconstitution Screener: MSCI Japan, August 2026 QIR

*Session 6u. Run with `agents/reconstitution.py` on an approximate
universe; regenerate with live data via
`scripts/run_msci_japan_screener.py` (local, needs network).*

## Why this index and this date

- **Provider by recency:** MSCI's August 2026 Quarterly Index Review
  announces **Aug 12, 2026**, effective **Sep 1** — ahead of FTSE's
  September semi-annual (effective Sep 21). ([MSCI schedule](https://www.msci.com/eqb/pressreleases/archive/ir_dates.pdf),
  [FTSE GEIS 2026 FAQ](https://www.lseg.com/content/dam/ftse-russell/en_us/documents/policy-documents/ftse-faq-document-geis-2026.pdf))
- **Index by tracking AUM (Asia):** MSCI Japan — EWJ alone is **$21.2B**
  (largest single-Asia MSCI tracker; vs EWT $10.7B, INDA $6.9B, MCHI
  $6.0B). EWJ is used as a **disclosed lower bound** of
  MSCI-Japan-benchmarked AUM in the flow estimate.
- **QIR matters for the framework:** quarterly reviews apply the STRICTER
  add hurdle (1.8x GMSR configurable) vs SAIR 1.15x.

## The run (approximate universe: 35 named JP large/mids + 350-name
modeled mid/small tail; caps/floats/ADV approximate, labeled)

| Output | SAIR rules | QIR rules (applies in August) |
|---|---|---|
| GMSR proxy | $5.7B | $5.7B |
| Add threshold | $6.5B | **$10.2B** |
| Deletion floor | $2.85B | $2.85B |
| Predicted add (named) | Kioxia (2.81x GMSR) | **Kioxia — clears even the QIR hurdle** |
| Predicted deletes (named) | none | none |
| Watch | 12 tail-zone names | 12 |

- **Fallen incumbents survive:** Nissan/Shiseido (~$8B full cap) sit well
  above the 0.5x-GMSR floor — the buffer is why indices don't churn, and
  the screener reproduces it.
- **Flow for the predicted add:** Kioxia FF cap ~$7.2B -> weight x $21.2B
  (EWJ lower bound) ≈ **$56M / ~0.3 ADV days**; true MSCI-Japan-benchmarked
  AUM is a multiple of EWJ, so real event-day demand scales accordingly.

## The methodological lesson (keep this for the interview)

The FIRST run used only the top-35 slice — and the 85% coverage cutoff
landed at $55B, flagging solid members (Nidec, Fujikura) as deletions.
The GMSR is defined on the FULL investable universe; truncate the
universe and the cutoff inflates by an order of magnitude. The fix —
modeling the mid/small tail — moved the proxy to $5.7B, matching the
published interim-GMSR zone. **A screener is only as good as its
universe file** — on a desk this is exactly why the reconciler runs
against MSCI's official provisional lists.

## Disclosures

Caps/floats/ADV approximate (mid-2026, ±20%); membership assumptions
unverified (esp. Kioxia — if already added at a 2025 review, the
screener's story becomes 'correctly retained', verify against MSCI
announcements); tail is modeled, not enumerated; country-vs-global GMSR
interplay not modeled. Regenerate with the live script before using
numbers anywhere that matters.
