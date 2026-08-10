# How Big Is the MSCI Taiwan Mandate?

Generated 2026-08-10T16:36:07. Source data: MSCI Inc. Q2 2026 results for the quarter ended 2026-06-30, filed 2026-07-21.

## The disclosures this rests on

| Figure | Value | Where |
| --- | --- | --- |
| ETF AUM linked to MSCI equity indexes | USD 2,818bn | 8-K Table 7 |
| of which Emerging Markets / All Country | USD 841bn | presentation p13 |
| Quarterly ABF revenue, ETFs | USD 161.0m | presentation p13 |
| Quarterly ABF revenue, non-ETF indexed funds | USD 56.0m | presentation p13 |
| Period-end ETF basis point fee | 2.28 bp | 8-K Table 7 |

## The one inference

MSCI publishes the REVENUE on non-ETF indexed funds and not the assets. Inverting it at the ETF rate (2.38bp annualised from the same quarter) gives **USD 941bn**, or **0.33x** the ETF pool.

Priced at the ETF fee rate. Institutional index mandates are larger, negotiated and tiered, so they pay an index provider LESS per dollar than a retail ETF does — dividing by a rate that is too high returns an AUM that is too low.

## Taiwan

- Named ETFs that must buy a Standard addition: USD 45.0bn (includes the USD 13.4bn on the MSCI Taiwan indexes themselves, which `tw_tracking_aum.py` omitted).
- With the mandate multiplier: **USD 60bn**.
- If the name is new to the IMI: **USD 132bn**.

## What is deliberately not claimed

The named ETFs are 56% of the disclosed EM/All-Country ETF bucket. The remainder is NOT grossed up: it contains single-country EM ETFs — MSCI China, India, Korea, Brazil — that hold no Taiwan at all, so scaling on bucket share would credit Taiwan with money that cannot own it.
