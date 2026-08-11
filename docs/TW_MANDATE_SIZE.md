# How Big Is the MSCI Taiwan Mandate?

Generated 2026-08-11T19:57:49. Source data: MSCI Inc. Q2 2026 results for the quarter ended 2026-06-30, filed 2026-07-21.

## The disclosures this rests on

| Figure | Value | Where |
| --- | --- | --- |
| ETF AUM linked to MSCI equity indexes | USD 2,818bn | 8-K Table 7 |
| of which Emerging Markets / All Country | USD 841bn | presentation p13 |
| Quarterly ABF revenue, ETFs | USD 161.0m | presentation p13 |
| Quarterly ABF revenue, non-ETF indexed funds | USD 56.0m | presentation p13 |
| Period-end ETF basis point fee | 2.28 bp | 8-K Table 7 |
| Non-ETF indexed AUM | ~USD 5,000bn | Q2-26 earnings call |

## The anchor, and the floor it retires

MSCI stated the non-ETF indexed pool at **~USD 5,000bn** on the Q2 2026 call — **1.77x** the ETF pool. The revenue line is the cross-check: USD 56.0m x 4 / USD 5,000bn = **0.45bp**, about a fifth of the 2.28bp ETF rate.

The old inversion of that revenue at the ETF rate (2.38bp annualised) gave USD 941bn, or 0.33x — kept as the floor variant.

The old inversion priced the USD 56.0m at the ETF fee rate. Mandates are larger, negotiated and tiered — the disclosed pool implies they actually pay ~0.45bp, a fifth of the ETF rate — so dividing by the ETF rate understated their assets by construction.

Applying the aggregate non-ETF/ETF ratio to the Taiwan-relevant ETF pool assumes the mandate mix mirrors the ETF mix at the index-family level. MSCI does not break the USD 5tn out by index, so this is the step a licensed mandate census would replace.

## Taiwan

- Named ETFs that must buy a Standard addition: USD 45.0bn (includes the USD 13.4bn on the MSCI Taiwan indexes themselves, which `tw_tracking_aum.py` omitted).
- With the mandate multiplier (2.77x): **USD 125bn**.
- If the name is new to the IMI: **USD 274bn**.
- Floor variant (fee inversion, 1.33x): USD 60bn.

## What is deliberately not claimed

The named ETFs are 56% of the disclosed EM/All-Country ETF bucket. The remainder is NOT grossed up: it contains single-country EM ETFs — MSCI China, India, Korea, Brazil — that hold no Taiwan at all, so scaling on bucket share would credit Taiwan with money that cannot own it.
