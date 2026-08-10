# The USD 180bn tracking-AUM assumption — sourcing attempt

Researched 2026-08-10, after Bill asked where the number came
from. **Short answer: it cannot be sourced as written, and the
label on it is wrong rather than the magnitude.**

## Where it originates in this project

`scripts/event_window_analyze.py`:

```python
TRACKING_AUM_USD_B = 180.0   # MSCI TW passive proxy
```

A hand-set constant with a comment. The rebalance question bank
then refers to "the registered $180bn", but the bank is
describing what this project already used — the citation is
circular and there is no measurement behind it.

## What MSCI actually publishes

| Item | Value | As of | Source |
|---|---|---|---|
| AUM in ETFs linked to **all** MSCI equity indexes | USD 2,816.2bn | Jul 2026 | [ir.msci.com](https://ir.msci.com/aum-etfs-linked-msci-indexes) |
| Assets benchmarked to **MSCI EM** indexes (incl. active) | ">USD 1.8trn" | 31 Dec 2025 | [msci.com EM index group](https://www.msci.com/indexes/group/emerging-markets-indexes) |
| MSCI Taiwan Index float-adjusted market cap | USD 3,183bn | 31 Jul 2026 | [MSCI Taiwan factsheet](https://www.msci.com/documents/10199/6f36d84d-425d-4e1f-8d56-e65c455ebda1) |

**MSCI publishes no AUM at country or individual-index level
anywhere public** — not in the 10-K, not in the earnings deck,
not on the IR AUM page. What it does publish per index is the
list of linked ETPs, names only, no assets.

For the **MSCI Taiwan Index (uncapped standard, code 915800)**
that list is two Taiwan-domiciled ETFs: Yuanta/P-shares
(006203 TT) and Fubon (0057 TT). EWT is not on it — EWT tracks
the **25/50** variant (index 710464).

## Bottom-up: every ETF on an MSCI Taiwan index

| Fund | Index tracked | AUM | As of |
|---|---|---|---|
| iShares MSCI Taiwan (EWT US) | Taiwan **25/50** | USD 11,151m | 30 Jun 2026 |
| iShares MSCI Taiwan UCITS | Taiwan 20/35 | EUR 1,324m | Aug 2026 |
| Xtrackers MSCI Taiwan 1C/1D | Taiwan 20/35 Custom | EUR 429m | Aug 2026 |
| HSBC MSCI Taiwan Capped UCITS | Taiwan 20/35 | EUR 93m | Aug 2026 |
| Yuanta/P-shares (006203 TT) | **Taiwan uncapped** | NT$1,913m | 7 Aug 2026 |
| Fubon (0057 TT) | **Taiwan uncapped** | NT$469m | 7 Aug 2026 |

- **Uncapped standard index only: ~USD 0.08bn.**
- **Whole MSCI Taiwan family: ~USD 13.3bn.**

Franklin FTSE Taiwan (FLTW) tracks a FTSE index and is correctly
excluded.

## The indirect channel, which is what 180 is really doing

Taiwan's weight, 31 Jul 2026: **MSCI EM 26.63%** (now the largest
country weight, ahead of China 21.38% and Korea 20.33%),
**MSCI ACWI 3.14%**.

- Via MSCI's own EM figure: 1.8trn x 26.63% ≈ **USD 479bn** — but
  that includes ACTIVE money, which does not mechanically trade a
  rebalance.
- ETF-only, bottom-up: IEMG USD 160.7bn x 27.41% = 44.1bn, EEM
  USD 30.3bn x 27.28% = 8.3bn → **USD 52.4bn from two funds
  alone**, before EIMI and every UCITS/Asia-listed EM tracker.
- Ceiling check: 2,816bn x 3.14% ≈ USD 88bn, order of magnitude
  only.

## Verdict

| Definition | Sourced | Is 180 plausible? |
|---|---|---|
| ETFs on MSCI Taiwan (uncapped standard) | ~0.08bn | No, off ~2,000x |
| All MSCI Taiwan-family single-country ETFs | ~13.3bn | No, off ~14x |
| Passive ETF Taiwan exposure via MSCI EM/ACWI | 52bn+ measured, plausibly 90-120bn globally | Marginal, high end |
| All INDEXED Taiwan exposure via MSCI (ETF + mandate) | not disclosed | **Yes — the only definition where 180 is a sane midpoint** |
| All assets benchmarked to MSCI EM incl. active | ~430-480bn | No, too low |

**The number is doing the indirect job while wearing the direct
label.** "Assets tracking MSCI Taiwan" is ~13bn. What actually
has to buy a new MSCI Taiwan constituent is passive money holding
Taiwan through MSCI EM and ACWI, and that is plausibly 90-180bn
depending on how much non-ETF indexed mandate you credit.

## What to do about it

1. **Relabel, do not just re-set.** The input is
   *indexed Taiwan exposure via all MSCI indexes*, not
   *assets tracking MSCI Taiwan*. The current label is the actual
   error; the magnitude may survive.
2. **Drive it off Taiwan's EM weight**, which is public,
   published monthly, and moved from ~23.8% to 26.63% across the
   May-2026 review — a live driver baked into a constant.
3. **Keep reporting the 0.5x / 1x / 2x sensitivity.** It already
   brackets the honest range.
4. The ranking between names is invariant to this input. The
   level is not. Say which one you are standing behind.

## Could not verify

- No public MSCI disclosure at country or index level.
- No sell-side or press estimate of "passive assets tracking MSCI
  Taiwan" with a number, found at all.
- MSCI's per-index ETP lists are stamped "last updated 9 Feb
  2026" and may miss newer products.
- Global MSCI EM ETF universe not summed — only US-listed IEMG
  and EEM.
- EWT's AUM is moving fast (USD 7.18bn at 31 Mar 2026, 11.15bn at
  30 Jun 2026). Any constant here goes stale within a quarter.
