# Step 3 against the rulebook — terminology and numbers

*c-253. Bill: "let's first check with rulebook and make sure we
have the latest data and apply the latest methodology… verify
that our numbers and terminology are correct."*

**Edition used.** MSCI Global Investable Market Indexes
Methodology, **May 2026**. The URL Bill gave is live and still
serves that edition; the equivalent `_Aug2026` path does not
exist, so May 2026 is current. Our archived copy at
`data/msci_archive/MSCI_GIMIMethodology_May2026.pdf` is the
same edition — it carries the same worked example, priced as
of the close of **20 April 2026**.

---

## 1. The chain, with citations

Every number in step 3 is one link in a single chain. Nothing
here is a standalone threshold.

**§2.3.2.1, p.24–25 — Global Minimum Size Reference.** Sort the
**DM** Investable Equity Universe by full market cap, cumulate
free-float-adjusted cap, and take the full cap of the company
at **85%** coverage. Published value: **USD 15,748 million**
(Apr-20-2026 data). *"For Emerging Markets, the Global Minimum
Size Reference is set at one-half the corresponding level"* —
so **EM Standard = USD 7,874 million**.

**§2.3.2, p.24 — Global Minimum Size Range.** *"specifying a
range of 0.5 times to 1.15 times those References."* The
rulebook prints the answer: DM Standard **$7.87B–$18.11B**, EM
Standard **$3.94B–$9.06B**.

**§2.3.3, p.26 — Market Size-Segment Cutoff.** The same 85%
walk, but over **that market's** Investable Equity Universe.
If the resulting company's full cap lies inside the Global
Minimum Size Range, that cap *is* the market's cutoff. If not,
the company count is moved until it is. *"This process is
designed to give priority to global size integrity over market
coverage."*

**§3.1.5.1, p.43–44 — buffer zones.** *"The buffer zones at
Index Reviews are defined with boundaries of 2/3rd of and 1.5
times the **Market Size-Segment Cutoff** between two
size-segments."*

So the chain is:

```
DM universe → 85% walk        → DM reference        15.75
              ÷ 2             → EM reference         7.87
              × 0.5 … × 1.15  → EM range        3.94 – 9.06
Taiwan universe → 85% walk    → raw crossing         6.74
              clamp into range→ MARKET CUTOFF        6.74
              × 2/3           → lower buffer         4.49
              × 1.5           → upper buffer        10.11
```

---

## 2. Terminology — three labels are wrong

| on the page | what the rulebook calls it |
|---|---|
| "Global size reference" | **Global Minimum Size Reference — DM Standard** (§2.3.2.1). Ours is a forecast of it, not the published figure. |
| **"Taiwan's permitted band"** | **Global Minimum Size Range, EM Standard** (§2.3.2). It is **not Taiwan's** — the identical band applies to every emerging market. |
| "Deletion floor" / "Addition bar" | **lower and upper buffer zones** (§3.1.5.1). Fine as plain English, but they must be shown as *derived from the Market Size-Segment Cutoff*. |

The genuinely Taiwan-specific number — the **Market Size-Segment
Cutoff** — is the one number step 3 does not currently show.

---

## 3. Two numeric errors

### 3a. The buffers are applied to the wrong base

`walkthrough_story.story()` builds, for the live review:

```python
"floor": round(2 / 3 * d["em_range_busd"][1], 2),   # 6.29
"bar":   round(1.5   * d["em_range_busd"][1], 2),   # 14.16
```

`em_range_busd[1]` is the **ceiling of the global EM range**
(9.44). §3.1.5.1 applies the buffers to the **Market
Size-Segment Cutoff**, which our own engine has already
computed for Taiwan as **6.74** (`aug26_cutoff_calc.json`,
`C_cutoff.cutoff_busd`; raw crossing at rank 115, inside the
range, so not clamped).

The page is therefore showing thresholds **40% above** the
engine's own, and neither matches the rulebook.

| | page | engine | rulebook |
|---|---|---|---|
| base | 9.44 (range ceiling) | 6.74 (market cutoff) | 6.74 |
| lower | 6.29 | 4.50 | **4.49** |
| upper | 14.16 | 12.14 | **10.11** |

### 3b. The 1.8× multiple is a market-stress rule, not a QIR rule

The engine records `"add_bar_rule": "1.8x (Aug = QUARTERLY
review)"`. That reading is wrong. Footnote 24 on p.44 —
*"At 'light' rebalancings, the buffer zones are set at one half
of and 1.8 times"* — refers to the contingency defined at
**p.107, "Potential Switch to a Light Rebalancing during Index
Reviews"**: a switch **under conditions of market stress**,
triggered by the Market Monitoring Framework (ACWI-weighted
bid-ask spreads, market functioning) over the last ten business
days before the announcement, and decided by MSCI's Equity
Index Committee and Index Policy Committee.

It has nothing to do with August being a quarterly review.
Absent a declared light rebalancing, the August-2026 buffers
are **2/3 and 1.5**.

Note also that the engine is internally inconsistent today: it
uses 2/3 (the full-review lower buffer) *and* 1.8 (the
light-rebalancing upper buffer) in the same calculation.

---

## 4. What is a forecast, not a fact

The published reference is **15.75** on Apr-20-2026 data. Our
**16.41** is that figure scaled by **+4.2%** — a proxy for the
DM market move to the August price cutoff, with a declared
±2pt band. §3.1.3 confirms the references *are* reset at each
Index Review, so scaling is the right shape of adjustment; the
scalar is ours, and the whole ladder below it inherits that
uncertainty.

---

## 5. Recommendation

1. Show the **Market Size-Segment Cutoff** as step 3's centre —
   it is the market's own number and the base of both buffers.
2. Rename the band to the **Global Minimum Size Range (EM
   Standard)** and say plainly that it is not Taiwan's.
3. Apply buffers to the cutoff: **4.49 / 10.11**.
4. Keep 1.8× documented as the light-rebalancing contingency,
   not as the August rule.

Item 3 changes the thresholds the page has been displaying, and
the Aug-2026 call was declared in advance on 2026-08-05. That
is a decision about a registered prediction, not a display bug,
so it is Bill's to make rather than mine.

---

## 6. What was done (c-253)

**Bill chose to fix both and re-register.**

- `scripts/aug26_recall.py` re-applies the corrected
  thresholds to the **unchanged inputs** and writes
  `data/aug26_call_v2.json`. The original call is not
  overwritten; both are graded against the 12 August print.
- The result: **5 additions** (2408, 8046, 2344, plus **8299
  and 3189**, which cleared the corrected 10.11 bar but not
  the old 12.14 one) and **zero size-driven deletions** — the
  smallest incumbent on the watchlist is $4.94B against a
  corrected lower buffer of $4.49B. "Zero size-driven" is not
  "zero": liquidity, float, foreign room and the surveillance
  boards can still delete a name, and none of those is in this
  file.
- `walkthrough_story` now builds the thresholds from
  `C_cutoff.cutoff_busd`, and step 3 is rewritten around the
  chain with section-and-page citations, including a
  correction paragraph on the record.
- `data/msci_gimi_constants.json` holds the published rulebook
  figures so prose can quote them without a typed literal.
- `diagrams.size_ladder` draws the chain and the ladder.

**Still open.** `review_reconstruct.py` carries the same
mis-based buffers, so every reconstructed review — including
the graded May-2026 example — is affected. Step 3 now withholds
those numbers and says why rather than printing them. Re-running
the backtest under the corrected rule is the follow-up, and it
will move the historical hit rate.
