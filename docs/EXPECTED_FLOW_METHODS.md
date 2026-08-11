# Modelling Expected Flow = P(add) × Δw × AUM

**A survey of methods — academic and institutional — for each
term, for the product, and for the step the identity leaves out:
what the flow does to the price.**

Written 2026-08-11 (c-363). Sources are listed at the end; where
a claim is this project's own measurement, the generating script
is named instead.

---

## 0 · Why this identity, and its one hidden assumption

The identity prices an event before it happens:

```
Expected Flow ($)  =  P(add)  ×  Δw  ×  AUM
Alpha signal       =  Expected Flow ÷ Available Liquidity
```

Each term is estimable from a different kind of evidence — a
rulebook, a float register, a fund census — which is why desks
split it this way: three separately-auditable estimates rather
than one guess.

The hidden assumption is in the LAST step, not the first three.
Turning flow into expected return requires a price multiplier
(how many percent per percent of market cap bought), and the
academic literature disagrees about it by an order of magnitude.
Sections 5–6 cover that.

---

## 1 · P(add) — the probability term

**What academics do.** The Russell-reconstitution literature
treats index assignment as a threshold rule observed with error:
the modeller's ranking is a noisy measure of the provider's, so
P(assignment) is a smooth function of distance from the
reconstructed threshold — the "fuzzy RDD" first stage
(Chang–Hong–Liskovich 2015; Appel–Gormley–Keim's later
correction of that first stage; the NBER "improved method"
paper). The estimator is a probit/logit of actual assignment on
reconstructed rank or cap distance.

**What institutions do.** Deterministic rulebook replication,
scored. L&G publishes its MSCI World predictions each quarter
and tracks a Rebalance Accuracy Score (57 of 64 last quarter,
~86 long-run). Sell-side index desks (UBS, Morgan Stanley,
societies' index-event teams) publish banded conviction lists —
"high conviction add" is a probability statement without the
number attached.

**What this project runs** (`scripts/tw_add_probability.py`):
the fuzzy-threshold idea implemented as a seeded Monte Carlo —
the rule stays sharp; the two inputs unknowable before the
announcement (cutoff ±5%, one-of-ten price dates × realised
vol) are drawn. The FIF is taken as computed: its error study
against MSCI's implied FIFs has n=10, too thin to parameterize,
so it is recorded as evidence and not drawn from (float-stack
error rides in the cutoff band, which is struck on that stack).
MSCI discretion is a named unpriced risk.

**Methods not yet used here, in order of value:**

1. **Historical calibration curve.** Fit P(added | clearance
   band) on the 32-review backtest the way the RDD papers fit
   their first stage — requires cleaning the gate-failure
   recurrences out of the >1.5× band, which needs point-in-time
   float screens per review.
2. **Market-implied probability.** Invert the identity: if a
   typical confirmed addition drifts +X% into its announcement,
   a candidate's actual pre-announcement drift relative to that
   benchmark implies the market's own P. Institutions read the
   same thing off option skew where listed options exist.

   RUN ON THE AUGUST NAMES, the lens is stark. The typical
   confirmed Taiwan addition carries **+7.0%** excess drift into
   its announcement (p50, 52 events); Nanya sits at **−17.6%**
   excess over the same window (4th percentile of its own
   history), and all three names sit below their peer median on
   foreign flow. The market-implied P is approximately ZERO
   against our rule-implied >95% — and that gap is the entire
   thesis, in one number. Either the rule is right and the flow
   is unpriced, or the market knows something the rulebook does
   not (a count-flex, an off-cycle action). There is no reading
   in which both lenses are right and the event is boring.
3. **Ensemble ML classifiers** (gradient boosting on rank,
   float, ATVR proxies, sector). Standard at quant funds; needs
   hundreds of labelled candidates per market to beat the
   rulebook, which one market's 32 reviews does not supply.

---

## 2 · Δw — the weight term

**What academics do.** Mostly take it as given from the index
provider's published weights after the fact — the RDD papers use
actual post-reconstitution weights, and the banding around the
threshold does the identification work.

**What institutions do.** Full pro-forma replication: rebuild
the index calculation (free-float cap ÷ index free-float value,
capping algorithm applied) from licensed constituent and FIF
files, so Δw is known to the basis point before the effective
date. Index desks at banks distribute pro-forma weights to
clients days after each announcement — this is a solved problem
WITH the licence.

**What this project runs:** float cap ÷ index float value from
public float factors and factsheet-implied caps
(`aug26_scenarios.py`), with the FIF error measured at
mean −3.7%, sd 6.0% on ten aligned names
(`tw_fif_aligned_jul31.json`).

**Refinements available without the licence:**

1. **Capped-index weight adjustment.** 25/50 and 20/35 capping
   redistributes weight from TSMC to everything else, so a small
   name's Δw in EWT is HIGHER than its uncapped weight. We note
   this qualitatively; the capping algorithm (GIMI Appendix) is
   mechanical and could be run on the reconstructed member list.
2. **Error propagation.** Δw uncertainty already feeds P(add)
   via the Monte Carlo; carrying the same draws through to a
   flow DISTRIBUTION (rather than a point) is free — the
   machinery exists.

---

## 3 · AUM — the money term

The least observable term, and where methods differ most.

**Method A — fund-register bottom-up** (institutional
standard). Sum tracker AUM from Morningstar / Bloomberg fund
data, mandate data from eVestment for the institutional pool.
This is what our `tw_tracking_aum.py` does with public
factsheets — USD 45bn of named ETFs.

**Method B — provider-disclosure inversion** (our
contribution, `tw_mandate_size.py`). MSCI reports ETF-linked
AUM ($2.82tn) and asset-based-fee revenue split ETF / non-ETF /
futures to the SEC. Inverting non-ETF fee revenue at the ETF fee
rate floors the invisible mandate pool at USD 941bn (0.33× the
ETF pool) — conservative because mandates pay lower rates.

**Method C — holdings aggregation** (academic standard).
Sum 13F / N-PORT / fund-report holdings of index funds per
stock: Appel–Gormley–Keim build passive-ownership shares this
way from mutual-fund reports. Taiwan's analogue is thinner (no
13F), but TDCC's custody census gives the large-holder bucket —
a holdings series this project already uses for the
pre-positioning test, and which could proxy CHANGES in indexed
ownership around events.

**Method D — flow-revealed inversion** (our
`tw_tracking_aum.py` method 2). If observed foreign net into
historical additions IS the index demand, then
AUM = observed shares × price ÷ Δw. Median across 42 additions
lands at USD ~180bn with a 13× IQR — the dispersion is the
finding; the level is weak evidence.

**Method E — futures and options open interest.** For markets
with liquid index futures, benchmark-linked money reveals itself
in roll open interest. TAIFEX MSCI Taiwan futures died in 2011;
SGX FTSE Taiwan OI is observable and was not pursued — worth a
harvest if the AUM band must narrow.

**Method F — demand-system estimation** (frontier academic).
Koijen–Yogo estimate every institution's demand function from
holdings data; indexed demand falls out as the inelastic
component. Needs comprehensive holdings data — the full
institutional version of what method C approximates.

---

## 4 · The product — validating Expected Flow against realised flow

The identity is testable, and this is the highest-value build
this project has not yet done:

```
realised foreign net (shares, eff day)  =  a + b × modelled flow (shares)
```

cross-sectionally over events with reconstructable weights. A
slope near 1 validates the AUM level; the intercept absorbs the
non-index flow; the R² says how much of effective-day flow the
identity explains. Our two halves already exist separately —
realised flow per event (`tw_foreign_baseline.json`: additions
print +3.3× a normal day on the effective day) and modelled flow
for the current candidates — but per-event HISTORICAL weights
need the point-in-time float stack, which exists only for recent
reviews. With MSCI's files this regression is a day's work; it
is the single most direct calibration the framework admits.

Two biases are known in advance: T86 NETS all foreign accounts
(tracker buying minus foreign selling), pushing b below 1; and
benchmark-aware active money buying early pushes flow out of the
effective day into the mid window, also pushing b down. Both
biases make the identity a FLOOR test, which matches how the AUM
was built.

---

## 5 · From flow to price — the term the identity omits

The reason to model flow is to price its impact, and here the
literature is genuinely split:

* **Event-study tradition** (Shleifer 1986; Harris–Gurel 1986):
  S&P 500 additions earned ~3% around announcement — read as
  evidence that demand curves slope down (Shleifer) or that
  price pressure is temporary (Harris–Gurel). Petajisto (2011)
  measures the "index premium" and its hidden cost to indexers
  across S&P 500 and Russell.
* **RDD identification** (Chang–Hong–Liskovich 2015): Russell
  threshold crossings imply a stock-level demand elasticity
  around −1.5 (universal rebalancing) to −0.46 (passive-only) —
  i.e., buying 1% of a company moves its price ~0.7–2%.
* **Macro multiplier** (Gabaix–Koijen, "Inelastic Markets
  Hypothesis"): $1 of flow into the aggregate market raises
  aggregate value by ~$5 — far larger than micro elasticities,
  because stock-level substitution is easy and market-level
  substitution is not. For single-stock index events the
  stock-level elasticity is the relevant one.
* **The decay result** (Greenwood–Sammon, "The Disappearing
  Index Effect"): S&P 500 addition returns fell from ~7% in the
  1990s to ~1% in the 2010s despite passive AUM growing —
  consistent with more arbitrage capital pre-positioning, better
  liquidity provision at the close, and announcement-day
  anticipation.

**Where this project sits in that debate, with its own data:**
our out-of-sample null (no fitted rule predicts direction,
best p=0.11 as max of six draws) and the near-zero median
auction impact with 3–5× wider dispersion are exactly what the
Greenwood–Sammon world looks like from inside one market: the
LEVEL of the index effect is mostly arbitraged away, while the
VARIANCE the forced flow injects is alive and measurable. That
is why the site sizes the trade and does not forecast the
price — the framework's alpha term, divided by today's arbitrage
capital, nets to roughly the execution cost.

---

## 6 · Method-to-data map

| Term | Method | Needs | Status here |
| --- | --- | --- | --- |
| P | Rule replication + input Monte Carlo | public | **live** |
| P | Calibration curve on past reviews | PIT float stack | blocked |
| P | Market-implied from drift | public | one line from live |
| Δw | Pro-forma replication | MSCI licence | approximated |
| Δw | Capping algorithm on reconstruction | public | buildable |
| AUM | Fund-register bottom-up | public factsheets | **live** (45bn) |
| AUM | Provider fee-revenue inversion | SEC filings | **live** (0.33×) |
| AUM | Holdings aggregation | 13F/N-PORT equiv. | partial (TDCC) |
| AUM | Flow-revealed inversion | public | **live** (weak) |
| AUM | Futures open interest | SGX data | not pursued |
| Flow | Identity regression vs realised | PIT weights | the next build |
| Price | Stock-level elasticity | event panel | direction null; dispersion live |

---

## Sources

* Shleifer (1986); Harris & Gurel (1986) — the original S&P 500
  index-effect studies.
* [Petajisto (2011), "The index premium and its hidden cost for
  index funds"](https://www.petajisto.net/papers/petajisto%202011%20jef%20-%20hidden%20cost%20for%20index%20funds.pdf)
* [Greenwood & Sammon, "The Disappearing Index Effect"
  (NBER w30748)](https://www.nber.org/system/files/working_papers/w30748/w30748.pdf)
* [Chang, Hong & Liskovich (2015), "Regression Discontinuity and
  the Price Effects of Stock Market Indexing"
  (RFS)](https://academic.oup.com/rfs/article-abstract/28/1/212/1680962)
* [Gabaix & Koijen, "In Search of the Origins of Financial
  Fluctuations: The Inelastic Markets
  Hypothesis"](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3686935)
* [Appel, Gormley & Keim (2016), "Passive Investors, Not Passive
  Owners" (JFE)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2475150)
* [NBER w26370, "An Improved Method to Predict Assignment of
  Stocks into Russell Indexes"](https://www.nber.org/papers/w26370)
* [L&G Q3 2026 MSCI rebalancing predictions](https://am.landg.us.com/insights/insights-blog/2026/our-q3-msci-rebalancing-predictions/)
* This project: `tw_add_probability.py`, `tw_mandate_size.py`,
  `tw_tracking_aum.py`, `tw_forced_flow.py`,
  `tw_foreign_baseline.py`, `tw_addition_study.py`.
