# Original TWSE Limit-Up/Down Project — Review of the Source Materials

*2026-07-08. Digest of the internship-era artifacts (two Jupyter notebooks,
code documentation, intraday pickles, weekly notes, and the AI team
presentation) so the author has an accurate record of what was actually
built, what the data holds, and what to improve. Companion to the platform's
Page 2, which generalizes this work.*

**Reading coverage:** both notebooks digested via complete cell-by-cell
outlines plus full source of the key cells (categorization function, dates
appendix, threshold logic); `TWSE Intraday Code Documentation.docx` read in
full (429 extracted lines); `June 24 - 28.docx` read in full;
`Team 1 Presentation Slides.pptx` all 46 slides' text extracted;
pickle structures inspected. Partially read: `Sentiment Scrapper.docx`
(~200 of 339 extracted lines — remainder is more of the same prompt-log
format). `Rebalancing.docx` contains only an embedded image (no extractable
text) and could not be reviewed.

---

## 1. What the project actually was (pipeline reconstruction)

**Universe & events.** FTSE (quarterly, 2016–2024) and MSCI (quarterly,
2015–2024) Taiwan rebalance dates — provided via CLSA, hand-verified, with a
holiday-adjustment step (7 MSCI February dates collide with 228 Peace
Memorial Day; one FTSE date with Mid-Autumn). Universe = TWSE index members
(~1,000 names; TWOTCI OTC names identified as an extension for more
limit-down instances) as a proxy for the desk's tradable book.

**Detection & categorization (daily, Bloomberg BDH).** Limit hits defined by
`PX_HIGH == PX_MAX_LIMIT` / `PX_LOW == PX_MIN_LIMIT` on the effective date;
`process_data()` then buckets every instance into a 2×4 taxonomy: limit-up /
limit-down × {opened at limit, opened off limit, closed at limit ("locked"),
closed off limit ("retreated")} — the analytically load-bearing distinction.
Optional filters: market cap (>100B TWD), liquidity, industry.

**Path analysis (daily, T+1…T+7).** For each instance, 7-day cumulative
return paths; binary up/down encodings; per-sequence average returns (e.g.
all stocks with pattern [1,1,0,…]); path frequency counts; first-order
transition matrices (P(up_{t+1}|up_t) per day); a cutoff-scan (share of
returns above x% for x ∈ [−20%, +90%] per T+day); Excel exports per
sequence; a networkx path-tree visualization. Headline finding (per the
author's account): retreat-type limit-ups gained ~+2% T+1 and ~+1.5% T+2 —
buy the intraday dip rather than wait.

**Intraday layer (1-minute, blp.bdib, 2024 dates only — Bloomberg's ~140-day
intraday retention).** The uploaded pickles are this layer's cache: dicts of
`"date_ticker" → 1-min OHLCV+trades+value` frames, **full TWSE universe**,
~1,980 name-days each for MSCI May-2024 and FTSE Jun-2024 plus ~1,000 for
MSCI Aug-2024 — a genuinely valuable dataset (the whole cross-section, not
just the limit names). Built on it: the "distance to limit" curve
(limit-ratio − intraday return, 5-min sampling); time-of-first-hit
histograms (most hits 9–11 AM); intraday VWAP; average max drawdown after a
hit; T+1 intraday recovery paths; and Part 2's **threshold detector** —
"given +x% by time t, will it lock?" — with an honest false-positive
concern and a `compare_dictionaries` hit-rate check (incomplete at handover).

**Adjacent workstreams (from the notes).** A 12-index Asia-Pacific study of
next-day index returns after rebalance days — MSCI days skew strongly
positive T+1 (TPX 88.9%, HSI/SHCOMP 77.8%) while FTSE days skew negative
(most indices 20–30% positive) — an intriguing provider asymmetry worth
revisiting with proper inference. And an index-level volatility-regime
bucketing (tight / normal / trending / extremely-trending by range vs
average) — the exact labels that later became this platform's Agent-2 regime
taxonomy.

**Engineering culture.** Bloomberg quota management (500k hits/day), the
DPDF-settings pitfall (unadjusted vs adjusted prices — confirmed with a
Bloomberg rep), pickle caching to survive quota/RAM limits, an explicit
handover document. Weaknesses the author self-flagged: naming
inconsistencies, near-duplicated FTSE/MSCI code paths (notebook 2 began
refactoring into `process_data`), untestable-after-access-expired.

## 2. What to improve (ranked, each mapped to the current platform)

1. **No statistical inference anywhere.** Every number is a raw count or
   mean over small, event-clustered samples (all names on one date share the
   market shock — observations are cross-correlated, so naive averages
   overstate precision). Fix: binomial/bootstrap CIs on the T+1 continuation
   rates, date-clustered errors, and market-model abnormal returns instead
   of raw returns (the +2% T+1 could partly be beta on a strong tape). *The
   platform's event-study inference and library medians are exactly this
   upgrade.*
2. **Threshold detector risks overfitting and was never validated
   out-of-sample.** The grid scan picks thresholds on the same data that
   evaluates them. Fix: formalize as a hazard/logit model of
   P(lock | return-so-far, time, volume-so-far) with walk-forward splits by
   year; report precision/recall and the COST of false positives
   (accelerating into names that don't lock). *This is the "limit-up hazard
   surface" already specced as the platform's next Taiwan feature.*
3. **Rebalance attribution is assumed, not established.** The universe is
   all TWSE members on rebalance dates — limit hits from idiosyncratic news
   are counted as rebalance phenomena (the author's own noted caveat). Fix:
   join against actual add/delete/weight-change lists (Agent 12 solves the
   feed) and compare limit-hit base rates on rebalance vs matched
   non-rebalance dates — the natural control that was never run.
4. **Path machinery ignores magnitude and assumes order-1 dynamics.**
   Binary sequences discard size-of-move; transition matrices are first-order
   with no duration dependence. Fix where it matters (the T+1/T+2 numbers):
   condition on the magnitude and on locked-vs-retreat type simultaneously,
   which the 2×4 taxonomy already supports.
5. **Sample depth.** 2024-only intraday (a data-access constraint, not a
   design flaw). Fix: accumulate forward every review cycle (the platform's
   event-library pattern), and/or source TWSE historical intraday from the
   exchange/TEJ to extend backward toward the "10-year" wish.
6. **Execution realism.** VWAP was started; costs, board lots (1,000
   shares), short-sale/locate constraints, and T+1 auction mechanics were
   not modeled. *The platform's explicit-costs, lot/short checks, and S1–S4
   simulator close this.*
7. **Engineering.** Notebook → module extraction with tests and pinned
   anchors (the near-duplicated FTSE/MSCI paths and naming drift are exactly
   what the platform's per-agent, per-test structure prevents); the pickles
   should carry a manifest (fields, dates, DPDF settings) so the dataset
   remains usable as access changes.

## 3. The AI presentation (Team 1, July 26 2024) — summary

*"Artificial Intelligence: Rational or Irrational Exuberance?"* — Sherman
Lee (Institutional Business), Bill Luo (Trading), Sally Ng (Investments);
46 slides. Argument arc:

- **Setup:** AI history (Turing → AI winters → deep-learning era), then the
  enthusiasm evidence — AI patents and earnings-call mentions surging,
  Magnificent-7 ~400% since 2020, widening P/E gap — framed by Greenspan's
  "irrational exuberance" question.
- **Dot-com comparison:** Nasdaq −75% (2000–02) and 15 years to reclaim
  5,000; IPO frenzy of unprofitable firms; Nvidia's multiple tracking
  Cisco's bubble path as the bear case.
- **"Why this time is different":** earnings expansion is real (Mag-7 EPS
  growth vs rest of S&P), enterprise adoption/spend steadier, margins and
  FCF far healthier, capex funded from revenues not equity issuance, and
  investors now punish undisciplined spending (a stock −15% on an aggressive
  AI-spend announcement).
- **Opportunity map (four layers):** hardware enablers (semis value chain:
  IDMs/fabless/foundries/OSATs; training compute ×4.1/yr), software enablers
  (cloud/model/apps; AI to reach ~12% of public-cloud spend), infrastructure
  (data-center power: +~200 TWh by 2030; hyperscaler renewables PPAs),
  adopters (broad sector productivity; quantified-AI-disclosure firms
  outperformed). Enablers led 2023 (+$6T market cap); adopters expected to
  catch up.
- **Bottom line (4 takeaways):** AI is transformative; this is not the
  dot-com bubble; the recent correction is healthy; diversify across the AI
  stack — closed with Shiller: "Nothing important has ever been built
  without irrational exuberance." Appendix: pets.com case study,
  supercomputer barriers to entry, ASEAN data-center growth, geographic
  power-demand differences, the Buffett indicator.

## 4. One-line synthesis

The internship work was a hand-built, data-constrained but genuinely
desk-relevant empirical study of Taiwan's limit-lock tail risk around index
rebalances — strongest on taxonomy, data engineering under Bloomberg
constraints, and practical framing (wait vs buy-the-dip, threshold
acceleration); weakest on inference, validation, and attribution — and the
current platform is, item by item, the systematized answer to its own
improvement list, with the limit-up hazard surface as the last unbuilt piece.
