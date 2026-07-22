# Index Rebalancing Execution — Research Base

*Academic and practitioner evidence underpinning the rebalance best-execution
strategy simulator (Module 2). Each finding maps to a strategy the simulator
implements or a parameter it defaults. Compiled 2026-07-07.*

---

## 1. The canonical index effect

- **Harris & Gurel (1986)** and **Shleifer (1986)**: stocks added to the
  S&P 500 earned ~3% abnormal returns around the announcement. Two competing
  explanations that matter for execution design: **price pressure**
  (temporary — index funds' demand is satisfied, then prices revert) vs.
  **downward-sloping demand curves** (permanent shift).
- **Lynch & Mendenhall (1997)**: 3–8% abnormal returns across event windows;
  distinct announcement-day and effective-day dynamics.
- **Chen, Noronha & Singal (2004)**: the response is **asymmetric** — additions
  behave differently from deletions (deletions' losses largely reverse;
  investor-recognition explanation).
- Reversal of the temporary component sets in after the effective date;
  classic estimates put meaningful reversal within **~5–20 trading days**.

**Execution implication:** the *temporary* component is the exploitable /
avoidable part. A tracker that trades 100% at the effective close buys at the
point of maximum price pressure; a cost-minimizer that completes after the
effective date captures the reversal — at the price of tracking error.

## 2. What rebalancing costs indexers

- **Petajisto (2011)**, *The index premium and its hidden cost for index
  funds*: announcement-to-effective price impact averaged **+8.8% (S&P 500
  adds) / +4.7% (Russell 2000 adds)** and **−15.1% / −4.6% for deletions**
  (1990–2005). Annualized drag on mechanical indexers: **21–28 bps (S&P 500)**
  and **38–77 bps (Russell 2000)**, peaking at 65–82 / 232–463 bps in 2000.
- **Madhavan (2003)**, *The Russell Reconstitution Effect*: waiting until the
  reconstitution-day close costs **hundreds of bps** vs. gradually acquiring
  in advance **with minimal additional tracking error**; conversely, building
  inventory post-announcement and *providing* liquidity at the event earned
  several hundred bps (undiversified, high price risk).

**Execution implication:** the cost-vs-tracking-error frontier is the central
client deliverable — Madhavan's result is precisely the "pre-position
gradually" strategy the simulator must quantify per event.

## 3. Modern evidence — the effect has shrunk, the flow hasn't

- **Greenwood & Sammon (Journal of Finance, 2025)**, *The Disappearing Index
  Effect*: S&P 500 addition abnormal returns fell from **3.4% (1980s)** and
  **7.6% (1990s)** to **~0.8% (2010–2020)**; deletions to **−0.6%**. Drivers:
  more adds/deletes are migrations from the S&P MidCap; changes became more
  predictable, attracting **anticipatory arbitrage** that moves prices before
  announcement; average announcement→effective gap is **4.8 days (adds) /
  5.8 days (deletes)**.
- **Pegoraro, Sammon & Shim (2025+)**, *Optimal Index-Linked Rebalancing with
  Anticipatory Trading*: index investors trade off execution cost against
  tracking error while speculators anticipate them — gradual/advance execution
  reduces cost without materially increasing tracking error.

**Execution implication:** pre-positioning *alpha* has compressed, but
avoiding crowding at the close still matters because the *flow* is bigger
than ever. Strategy payoffs must be computed per-event from actual data, not
assumed from 1990s magnitudes.

## 4. The closing-auction concentration problem

- Rebalance volume is extremely concentrated in the effective-day closing
  auction: close-volume multiples of normal range from **~3× (CRSP US Mid)**
  to **>27× (S&P 500)** on reconstitution dates.
- Nasdaq's closing cross executed **~2.5B shares in <1 second** on the 2025
  Russell recon day — the auction can absorb enormous size, which is why
  trackers use it; but close execution **underperforms in the US and
  Asia-Pacific ex-Japan** while performing better in Europe and Japan
  (regional differences the simulator's per-market auction assumptions
  should reflect).
- Practitioner playbook (transition-management literature): a **mix** of
  in-advance market trading and closing-auction participation, sometimes with
  a **futures overlay** for interim index exposure (futures overlay requires
  futures data — out of scope, tracked in the gap register).

## 5. Emerging-market / MSCI evidence (this app's Asian coverage)

- MSCI Standard Index reconstitutions show significant announcement-day
  abnormal returns; effects are **stronger in emerging markets** and for
  China A-share inclusions (price + volume surge on effective date; deletions
  show volume without significant price response in several studies).
- Implication: identical strategy logic, but per-market parameters (auction
  share, impact, reversal) differ — consistent with the app's per-market
  design elsewhere (venues, sessions).

## 6. Strategy families the simulator implements

| # | Strategy | Literature anchor | Trade-off |
|---|---|---|---|
| S1 | **Tracker baseline**: 100% at effective-day close (MOC) | What mechanical indexers do; Petajisto's cost estimates measure exactly this | Zero tracking error; maximum crowding cost |
| S2 | **Pre-position**: fraction *f* spread over T−k…T−1, remainder MOC | Madhavan (2003); Pegoraro-Sammon-Shim | Lower cost; tracking error from pre-effective price moves |
| S3 | **Post-effective completion**: MOC partial, remainder over T+1…T+m | Reversal evidence (Harris-Gurel; Chen et al.) | Captures reversal; tracking error + risk the reversal doesn't come |
| S4 | **Announcement-anchored**: begin at A+1, spread to effective | Beneish-Whaley "S&P game"; Greenwood-Sammon predictability | Front-runs the index demand; largest deviation from the benchmark print |
| — | Futures overlay for interim exposure | Transition management practice | Not implementable with free data — gap register |

**Metrics per strategy (computed from actual event-window data):**
implementation cost vs. pre-announcement price; execution shortfall vs. the
effective close (the tracker's benchmark = realized tracking difference);
share of order in the closing auction vs. an auction-capacity assumption;
market impact via the app's square-root model at day-level participation;
reversal captured/foregone over T+1…T+m.

## 7. Default parameters (all user-overridable, all disclosed)

- Announcement→effective gap when unknown: **5 trading days** (Greenwood-Sammon
  4.8/5.8).
- Reversal measurement horizon: **10 trading days** post-effective (mid of the
  5–20 range).
- Closing-auction share of effective-day volume: per-market default **~10%**
  of daily volume normally, scaled by the observed effective-day volume
  multiple (the event study already measures close-window concentration).
- Impact: existing square-root model (η=0.3) at daily participation, with the
  Almgren-2005 cross-check caveats carried over.

## Sources

- Harris & Gurel (1986); Shleifer (1986) — summarized in [Greenwood & Sammon, HBS WP 23-025](https://www.hbs.edu/ris/Publication%20Files/23-025_563e45c6-df92-4d9c-ae05-608d4d0acab1.pdf)
- [Lynch & Mendenhall / long-term S&P additions-deletions analysis (JBF 2013)](https://www.sciencedirect.com/science/article/abs/pii/S0378426613003592)
- [Chen, Noronha & Singal (2004) — asymmetric price response](https://www.researchgate.net/publication/4992686_The_Price_Response_to_SP_500_Index_Additions_and_Deletions_Evidence_of_Asymmetry_and_a_New_Explanation)
- [Petajisto (2011) — The index premium and its hidden cost for index funds (JEF)](https://www.petajisto.net/papers/petajisto%202011%20jef%20-%20hidden%20cost%20for%20index%20funds.pdf) · [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1235604)
- [Madhavan (2003) — The Russell Reconstitution Effect, FAJ 59(4)](https://www.hillsdaleinv.com/uploads/The_Russell_Reconstitution_Effect,_Ananth_Madhaven,_Financial_Analysts_Journal,_JulyAugust_2003,_Pages_51-64.pdf) · [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=488027)
- [Greenwood & Sammon — The Disappearing Index Effect (JF 2025)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4294297) · [NBER w30748](https://www.nber.org/papers/w30748)
- [Pegoraro, Sammon & Shim — Optimal Index-Linked Rebalancing with Anticipatory Trading (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6772502)
- [Vijh (2022) — Negative returns on S&P 500 addition? (Financial Management)](https://onlinelibrary.wiley.com/doi/full/10.1111/fima.12391)
- [Eastspring — Navigating index rebalancing effects (practitioner)](https://www.eastspring.com/insights/deep-dives/navigating-index-rebalancing-effects-key-insights-for-smarter-execution)
- [Ryedale — Planning and Executing Index Rebalance Trades (practitioner)](https://www.ryedale.com/insights/thought-leadership/planning-and-executing-index-rebalance-trades)
- [On the hidden costs of passive investing (arXiv 2025)](https://arxiv.org/pdf/2506.21775)
- [CME — Russell Reconstitution impact](https://www.cmegroup.com/openmarkets/equity-index/2025/How-Does-the-Russell-Reconstitution-Impact-Equity-Markets.html) · [LSEG 2026 recon key facts](https://www.lseg.com/en/insights/ftse-russell/more-key-facts-ahead-of-the-2026-russell-us-indexes-reconstitution)
- [MSCI Standard Index reconstitutions — price effect & investor awareness (JEF 2019)](https://www.sciencedirect.com/science/article/abs/pii/S0927539819300027)
- [China A-shares MSCI inclusion — market internationalization evidence](https://www.sciencedirect.com/science/article/abs/pii/S0275531923001150)


## 8. Rulebook-based reconstitution prediction (session 6j)

`agents/reconstitution.py` applies the public structure of the provider
methodologies to a candidate universe (cap / free float / ADV / ATVR):

- **MSCI GIMI approximation:** GMSR = full cap at 85% cumulative free-float
  coverage of the sorted eligible universe; Global Minimum Size Range
  0.5x-1.15x GMSR (buffers keep incumbents / gate newcomers); configurable
  stricter QIR add multiple (default 1.8x — verify current book); free-float
  >= 15% and ATVR liquidity screens.
- **FTSE-style rank buffer:** add at rank <= 90, delete at rank >= 111
  (scaled per index size), reserves pair to hold index size — the published
  FTSE UK ground-rule structure.
- **Flow estimate:** weight x tracked-AUM input / ADV -> days-to-trade.
  AUM is the desk's input, not a claim.

NOT modeled (disclosed in every output): country-level minimum-size
interplay, FIF granularity/foreign room, nationality & fast-entry rules,
multiple lines, corporate-event windows, provider discretion.

Sources: [MSCI GIMI methodology](https://www.msci.com/indexes/documents/methodology/1_MSCI_Global_Investable_Market_Indexes_Methodology_20240812.pdf) ·
[FTSE UK Index Series ground rules](https://www.lseg.com/content/dam/ftse-russell/en_us/documents/ground-rules/ftse-uk-index-series-ground-rules.pdf) ·
[FTSE GEIS ground rules](https://www.lseg.com/content/dam/ftse-russell/en_us/documents/ground-rules/ftse-global-equity-index-series-ground-rules.pdf)
