# Estimating the passive AUM behind an MSCI Taiwan index change

Generated 2026-08-10T15:44:33. The demand model uses a declared **USD 180bn**. This file asks what can be estimated instead.

## Method 1 — bottom-up, and the size-segment trap

**A Taiwan Standard addition is not bought by every passive dollar that holds Taiwan.** MSCI's size segments are derived by subtraction (GIMI 2.3: *"the Small Cap Index is derived as the difference between the Investable Market Index and the Standard Index"*), so a stock promoted out of Small Cap was ALREADY inside the IMI at an unchanged free-float weight. An IMI tracker does nothing.

The last two Taiwan reviews are one of each case:

| review | name | what happened | IMI trackers |
|---|---|---|---|
| May-2026 | MPI Corp (6223) | added to Standard, **deleted from Global Small Cap** | bought nothing |
| Feb-2026 | Hon Precision (7769) | absent from the Small Cap deletion list — new to the IMI | bought from zero |

| fund | index | AUM | Taiwan wt | Taiwan USD bn | src |
|---|---|---|---|---|---|
| iShares MSCI EM (EEM US) | MSCI Emerging Markets | 30,316 USD | 27.28% | 8.27 | issuer |
| iShares MSCI EM ex China (EMXC US) | MSCI EM ex China | 24,118 USD | 33.00% | 7.96 | third-party |
| Fidelity EM Index Fund (FPADX) | MSCI Emerging Markets | 14,440 USD | 27.41% | 3.96 | third-party |
| Xtrackers MSCI EM UCITS 1C (XMME) | MSCI Emerging Markets | 11,000 EUR | 27.41% | 3.47 | third-party |
| iShares MSCI EM UCITS (IEEM) | MSCI Emerging Markets | 8,863 EUR | 27.41% | 2.79 | third-party |
| Amundi Core MSCI EM UCITS | MSCI Emerging Markets | 4,129 EUR | 27.41% | 1.30 | third-party |
| UBS (Lux) Core MSCI EM UCITS | MSCI Emerging Markets | 2,643 EUR | 27.41% | 0.83 | third-party |
| HSBC MSCI EM UCITS (HMEF) | MSCI Emerging Markets | 2,950 EUR | 27.41% | 0.93 | third-party |
| iShares MSCI ACWI (ACWI US) | MSCI ACWI | 33,204 USD | 3.14% | 1.04 | issuer |
| iShares MSCI ACWI UCITS (SSAC) | MSCI ACWI | 35,404 USD | 3.14% | 1.11 | third-party |
| iShares Core MSCI EM (IEMG US) | MSCI Emerging Markets IMI | 160,718 USD | 27.41% | 44.05 | issuer |
| iShares Core MSCI EM IMI UCITS (EIMI) | MSCI Emerging Markets IMI | 44,227 USD | 27.41% | 12.12 | issuer |
| iShares Core MSCI Total Intl Stock (IXUS) | MSCI ACWI ex USA IMI | 58,500 USD | 8.00% | 4.68 | third-party |
| Fidelity Total International Index (FTIHX) | MSCI ACWI ex USA IMI | 23,500 USD | 8.00% | 1.88 | third-party |

**Totals:**

- ETFs on the **uncapped** MSCI Taiwan Index: **USD 0.08bn**
- ETFs on **any** MSCI Taiwan index: **USD 13.4bn**
- Taiwan inside **Standard** EM/ACWI trackers (always buy): **USD 31.7bn** from USD 172bn of funds
- Taiwan inside **IMI** trackers (buy only if the name is new to the IMI): **USD 62.7bn** from USD 287bn of funds

So the answer is a pair, not a number:

| case | who buys | Standard-equivalent AUM |
|---|---|---|
| promotion out of Small Cap | Standard trackers only | **USD 32bn** |
| new to the IMI | everyone, IMI discounted 1.16x | **USD 86bn** |

*The 1.16x: Standard targets 85% of free-float market cap and IMI targets 99% (GIMI 2.3.1), so a stock's weight inside Standard is ~99/85 of its weight inside the IMI — an IMI dollar buys ~16% less of it even when it buys.*

**Which case applies is empirical per name. Check whether the stock is already in the IEMG and EIMI daily holdings files, and whether MSCI's review lists it as a DELETION from the Global Small Cap Indexes. May-2026 MPI Corp was case 1; Feb-2026 Hon Precision was case 2.**

### Excluded, each for a checked reason

| fund | size | why |
|---|---|---|
| Vanguard VWO | USD ~125bn | FTSE Emerging Markets All Cap China A Inclusion — not MSCI |
| Vanguard VXUS / VTIAX | USD ~400bn+ | FTSE Global All Cap ex US — not MSCI |
| SPDR SPEM | USD 17.7bn | S&P Emerging BMI — not MSCI |
| Schwab SCHE | USD 12.8bn | FTSE Emerging — not MSCI |
| Avantis AVEM, DFA DFAE/DFEM | USD 26.5bn+ | systematic/active, not index-replicating |

## Method 2 — revealed from what was bought

Turn the demand equation around:

```
demand_shares = weight x AUM / (fx x price)
        =>  AUM = shares x price / fx / weight
```

`shares` comes from **TWSE T86, 42 Taiwanese additions**: foreign net accumulated between ann-20 and the effective print, in days of the name's own ADV. Median **+1.04x** a normal day's volume (quartiles +0.23 to +2.92, n=42).

| name | weight | ADV (m sh) | price TWD | implied AUM |
|---|---|---|---|---|
| 2344 | 0.396% | 138.7 | 130.0 | **USD 147bn** |
| 2408 | 0.512% | 80.6 | 360.5 | **USD 183bn** |
| 8046 | 0.223% | 17.6 | 920.0 | **USD 234bn** |

**Median USD 183bn**, names disagreeing by 1.60x, and the flow benchmark's own quartiles moving it from 40 to 516bn.

## What this settles

The bottom-up pair (**32** or **86bn**) and the flow-revealed median (**183bn**) do NOT agree, and the gap is informative rather than embarrassing: the bottom-up figure counts only listed funds, while institutional segregated accounts, collective trusts and pension mandates benchmarked to MSCI EM are not publicly disclosed anywhere. Those are commonly a multiple of listed-ETF assets, and they buy the same stock on the same day.

So: **the bottom-up numbers are floors, the flow-revealed number is the only estimate that sees the whole market, and the level remains uncertain to an order of magnitude.** The ranking between names is unaffected by any of it.

## Not verified

- Taiwan's weight in MSCI EM. This file uses 27.41%; MSCI stated **23.76%** after the May-2026 review. The difference is ~15% on every EM line.
- Taiwan's weight inside EMXC, IXUS and FTIHX — all derived, none read off a fund page.
- XMME and IEEM AUM — third-party sources conflict by 30-80%.
- Japan- and Korea-listed MSCI EM trackers — none found, which is a negative search result rather than a confirmed zero.
- Non-fund institutional mandates — not disclosable, and the largest single source of understatement here.
- The Hon Precision case is inferred from the ABSENCE of the name in the Small Cap deletion list; direct confirmation needs MSCI's client-gated review file.
