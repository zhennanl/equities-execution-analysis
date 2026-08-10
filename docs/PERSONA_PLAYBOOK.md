# The Rebalance Window Through Three Sets of Eyes (c-130, refreshed c-131)

Measured on Taiwan's **157** historical windows (**2010→2026**
after Bill's terminal run extended the harvest into the
2010-2014 era; delisted-safe, flows attached 2015+).

**c-131 headline updates on the fuller sample** (the JSON is
the source of truth; the 115-window narrative below still
reads correctly in direction, these numbers supersede where
they differ): add drift +3.3% (unchanged), add eff-day +0.29%
(the close still ~free for trackers), capture 0.86, fade-the-
close +2.4% at 69% hit (was +3.5%/72% — the 2010-14 era fades
less), del-fade still ~zero at 47%. **The era path is now an
inverted U: add alpha +2.2% (2010-14) → +4.9% (2015-18) →
+7.6% (2019-22) → +2.9% (2023-26)** — the trade GREW for a
decade before crowding bit; the 2023-26 print is back to
2010-14 levels, not below them. Every number below carries its
source in data/persona_study_tw.json; era splits and hit rates
are medians unless stated.

---

## 1. The passive tracker (BlackRock EWT desk, Vanguard)

**Their objective function is not price — it is TRACKING
ERROR.** The index reprices at the effective close, so a fill
AT the close, at ANY price, is a perfect fill. Every share
traded before the close is a bet against the benchmark taken
for an impact saving. Their whole window reduces to one
decision: how much to move early, if any.

**Their questions, answered:**

- **P1. What does trading at the close cost?** Remarkably
  little in Taiwan: the effective-day move is **−0.08%** for
  adds (the close was marginally CHEAPER than E−1) and −1.3%
  for dels. The feared "pay up at the close" is not in the
  median — the arbs' supply meets the trackers there.
- **P2. What does trading early cost instead?** A lot: adds
  drift **+3.3%** from day 2 to E−1 (after a +1.4% day-1 gap).
  Pre-trading an add means CHASING that drift with tracking
  risk on top.
- **P3. Is the close print rich?** Yes, but that is the NEXT
  week's problem: adds give back **−3.5% by E+5** (72% of
  windows revert). The tracker doesn't care — the benchmark
  repriced at the same print — but it explains why everyone
  else behaves as they do.
- **P4. Can the close absorb size?** Effective-day volume runs
  **12.7× ADV** (median), 38× at p90. The market shows up.
- **Verdict for Taiwan: the data supports trading AT the
  close.** The early-trade "saving" is illusory (P2 > P1), and
  capacity is there (P4). The exception: names with extreme
  demand/ADV, where the desk's capacity math (Piece B) takes
  over.

## 2. The hedge fund (Millennium index-rebal pod)

**Their objective: be the other side of a known, forced,
dated flow — early in, out into the forced buyer.** The
questions are entry, exit, size, and whether the trade is
dying from crowding.

- **H1. The alpha is real and NOT yet dead:** adds return
  **+4.9%** day-0→E−1 (median), dels **−2.3%**. By era: +4.9%
  (2015-18) → +7.6% (2019-22) → **+2.9% (2023-26)**. Decay is
  visible in the recent era but the trade still pays.
- **H2. Day-1 is NOT too late:** capture = **0.83** — 83% of
  the pre-effective move happens AFTER day 1. The gap takes
  little; the drift is the trade.
- **H3. Exit at E−1, not into the close:** holding through the
  effective day adds **−0.08%** with a 48% win rate — a coin
  flip with crowd risk. Sell to the trackers at E−1/the close
  approach, don't hold past it.
- **H4. The SECOND trade — fading the close — is as good as
  the first:** shorting adds at the effective close and
  covering E+5 earns **+3.5% with a 72% hit rate**. On dels
  the fade earns nothing (+0.2%, 51%) — deletions stay down.
  The asymmetry: add-side pressure is temporary, del-side
  repricing is permanent. (This is Taiwan's version of the
  regime split found APAC-wide: TW/KR round-trip, IN/JP
  stick.)
- **H5. The market front-runs the announcement itself:** adds
  are already **+3.8%** in the 25 days BEFORE day 0; dels
  −1.6%; borrow on future dels builds to **1.20×** its
  starting level pre-announcement. The prediction (our
  engine's output) is tradeable consensus — which is exactly
  why H1 decays.
- **H6. It is a carry trade, not a coin:** 70% of adds and 62%
  of dels produce alpha in the intended direction; the worst
  add window lost −17%, the best made +50%. Position sizing
  survives the tails.

## 3. The agency PT desk (CLSA)

**No book. The product is advice, crossing, and the mandate.
Everything above is reframed as what to tell two different
clients — and the desk's edge is knowing both sides' state.**

- **C1. How much flow prints before the close?** The
  measured progress ratio came out implausibly low (0.0125,
  n=22) — FLAGGED AS A UNITS/AUM-ASSUMPTION ARTIFACT, not
  reported as a finding. Piece B (AUM calibration) resolves
  it; until then the honest answer is "not yet measured."
- **C2. The client table (tracker):** close cost ≈ −0.1%
  (adds) vs early cost ≈ +3.3% drift — full-close execution
  wins in the Taiwan median; carve out only extreme
  demand/ADV names.
- **C3. Do arbs provide the close liquidity? Yes** — drift up
  +3.3% then a flat effective day is exactly the signature of
  arb supply meeting tracker demand AT the print. The desk
  can promise the tracker a workable close in the median
  name.
- **C4. Crowding triage at T−3:** the PRE-score terciles do
  NOT yet separate effective-day outcomes (−0.20% vs −0.24%)
  — an honest negative: the crude PRE score is not a close
  predictor. The borrow-based SQZ side (dels) and the
  richer C1-style progress measure are the registered next
  candidates.
- **C5. Post-effective advice:** for opportunistic clients
  the add-fade (H4) is quotable: "adds give back ~3.5% within
  a week, 7 times out of 10." For dels: "don't wait for the
  bounce; there isn't one."

---

## PART III — The conditional study (c-132): what each player
## actually needs to know, per stock

Averages hide the decision. These tables condition on what is
OBSERVABLE at the time, with mechanism attribution from
Taiwan's three separately-labeled flows (foreign = t86,
retail leverage = margin balance, shorts = SBL). n=157
windows; flow attribution 2015+; attribution correlational.

### A. Bill's question answered: is early strength hedge-fund
### pre-positioning?

ADDs by day-1→3 return tercile, with concurrent flows:

| Early tercile | n | foreign net (xADV) | rest of window | eff day | revert E+5 |
|---|---|---|---|---|---|
| weak (≤+0.3%) | 16 | **−0.02 (selling)** | −1.4% | +0.3% | −1.1% |
| mid | 15 | **+0.069 (heavy buying)** | **+6.9%** | +1.1% | −2.0% |
| strong (>+3.2%) | 15 | +0.004 (flat!) | +5.1% | −0.5% | **−6.5%** |

And splitting the STRONG-early movers by whether foreign flow
led them:

| Strong early, split | n | continues | reverts E+5 |
|---|---|---|---|
| foreign-led | 7 | +3.2% | −3.1% |
| **NOT foreign-led** | 8 | **+8.8%** | **−7.4%** |

**The answer: early strength per se is NOT the HF signature —
early strength WITH concurrent foreign buying is.** The
institutional pattern is the MID bucket: heavy foreign
accumulation with a controlled price grind, then the best
continuation with modest reversion. Early pops WITHOUT foreign
flow (speculative/momentum money — margin medians are flat, so
"retail-led vs idiosyncratic" is not separable at the median)
run the hottest into effective and round-trip almost entirely
(−7.4%). Desk translation: a flow-less pop is the best
fade-the-close candidate on the board; a foreign-led grind is
real accumulation.

### B. "It already moved — is the trade over?" NO — the
### opposite.

ADDs by day-5 return quartile-ish tercile:

| Day-5 start | n | REMAINING drift to E−1 | full window |
|---|---|---|---|
| cold (≤0%) | 23 | +0.2% | −1.4% |
| mid | 20 | +3.1% | +4.3% |
| **hot (>+4.2%)** | 21 | **+6.7% more** | **+15.5%** |

Momentum, not exhaustion: hot starts keep paying; cold starts
never wake up. "I missed it" is empirically the reason to
ENTER, and the cold tercile is the screen-out.

### C. Deletions: the borrow book is the tell

| Pre-announcement borrow build | n | window return | revert E+5 |
|---|---|---|---|
| low | 24 | −1.3% | ~0 |
| **high (>1.28x)** | 23 | **−3.8%** | **+3.3%** |

Crowded pre-positioned shorts push the deletion further down
AND produce the only reliable post-effective bounce in the
dataset (the cover). The unconditional "del-fade earns
nothing" hides this: **buy-the-close works ONLY on
crowded-short deletions.** In-window build shows the same
monotonicity (light −0.1% / mid −2.2% / crowded −2.8%).

### D. Liquidity buckets (read with an era caveat)

Large-ADV adds (> $60M/day) show the biggest windows (+15%
median) — but the bucket is confounded with the 2019-22 era's
semi mega-adds; flagged, not celebrated.

### E. The risk shape a pod actually sizes to

Day-1 long held to E−1: median MAE **−2.2%**, but **p10 =
−9.7%** — one add-long in ten sits through a near-10% drawdown
before collecting. Median MFE +5.7%. The trade's Kelly math
must survive the p10 path, not the median.

### F. Big reviews are NOT diluted

Adds in reviews with ≥6 names: +5.7% median window vs +3.2%
in ≤3-name reviews. Arb capital does not spread thin — big
reviews attract MORE attention, not less.

---

## PART IV — The strategist layer (c-133): context, sector,
## regime — the client-call answers

Data: data/strategist_tw.json. Market = ^TWII (one Yahoo
call); sector = TWSE industry codes; sector tides and
market-wide foreign appetite computed from t86 (it carries
EVERY listed name daily — no new API).

### S1. Does the add trade survive a risk-off tape? YES — it
### was hiding inside beta all along.

| Window tape (TAIEX) | n | RAW add return | **EXCESS (mkt-adj)** | revert E+5 |
|---|---|---|---|---|
| risk-off (≤+0.3%) | 25 | +1.5% | **+3.0%** | **−4.4%** |
| neutral | 18 | +2.2% | +1.7% | −0.2% |
| risk-on (>+1.8%) | 21 | **+7.0%** | +1.7% | −2.4% |

The excess alpha is roughly REGIME-INVARIANT (~2-3%): the
risk-on windows' fat raw returns were mostly beta, and the
risk-off windows' weak raw returns were hiding intact alpha.
Client answer to "it's a selloff, does the add trade still
work?": **yes — hedge the market, keep the name.** One
asymmetry: risk-off adds revert hardest post-effective
(−4.4%), so the fade-the-close leg is BEST in bad tapes.

### S2. Sector: the Taiwan add effect is substantially a TECH
### phenomenon.

| Sector | n | total | excess | revert E+5 |
|---|---|---|---|---|
| TECH | 37 | +4.9% | **+3.8%** | **−5.1%** |
| SHIPPING | 5 | +4.9% | +2.3% | −0.7% |
| TRADITIONAL | 8 | +1.1% | **+0.2%** | −0.2% |

Traditional-economy adds barely move net of market — the drift
AND the reversion live in tech. Sector determines which
playbook page applies.

### S3. THE STRONGEST SEPARATOR FOUND SO FAR: flow vs the
### sector's own tide.

Bill's proposed indicator, tested: is this name's foreign
buying just its sector's tide, or name-specific? (name's flow
z-score minus sector-peers' median z)

| | n | window total | revert E+5 |
|---|---|---|---|
| flow BELOW sector tide | 16 | +2.1% | −2.7% |
| **flow ABOVE sector tide** | 15 | **+9.8%** | −4.3% |

A ~5x separation — bigger than any single-name conditioner in
Part III. The tide-adjustment removes the "it's just a sector
rally" false positive exactly as hypothesized. THIS goes on
the client dashboard as indicator #1.

### S4. A surprise, held loosely: adds during market-wide
### foreign SELLING did BETTER (+9.5% vs +4.9%, n=16/15).
Hypothesis: when foreigners are net sellers of Taiwan
broadly, index-driven buying stands out against the tide and
moves price further. Confounded with era (the selling regimes
include the hot 2022/2025 windows) — flagged for the
walk-forward, not yet quotable.

### S5. Case cards (the "lessons" clients remember)

- **Caliway (6919), Aug-25 add: +50.4%** in a flat tape —
  healthcare momentum with no institutional flow signature...
  and MSCI DELETED it two reviews later after the collapse.
  The lesson: a parabolic add window is not index demand, and
  the index itself will disown it.
- **Wistron, May-23: +39.6%** — but the tape did +7.1%; the
  AI-rally beta dressed up as index alpha. Always quote
  excess.
- **Walsin Tech, May-18: +35.3% in a FLAT tape** — the clean
  specimen of real index-flow alpha.
- **Teco (Nov-25, −17.1%) and Jentech (Nov-24, −16.3%)** —
  both in −4%+ tapes: the worst adds cluster in risk-off
  windows AND the recent era. Beta kills the raw trade even
  when the excess survives; the un-hedged version of this
  strategy dies in exactly these windows.

### The client-call indicator dashboard (what to have open)

1. **Excess-vs-sector flow z** (S3 — the #1 separator)
2. Concurrent foreign net vs the name's ADV (Part III-A: is
   the strength institutional?)
3. Borrow build vs pre-announcement level (dels: the only
   fade signal that pays)
4. Day-5 heat check (Part III-B: cold = screen out)
5. Window TAIEX return (S1: quote excess, hedge beta)
6. Sector group (S2: tech playbook vs traditional playbook)
7. MAE p10 (−9.7%) for sizing talk

## What additional data the other markets need

| Need | Serves | Source + file |
|---|---|---|
| Per-market flow (foreign/short) | H5, C1, C3, C4 | KR: `kr_flow_harvest.py` ✓ · TH: `th_nvdr_harvest.py` ✓ · AU: ASIC ✓ done · JP/others: registered gap |
| Delisted prices JP | unbiased DEL side | J-Quants signup + `jq_harvest.py` (written after creds) |
| PH prices | any PH analysis | PSE EDGE per-stock or paid; registered |
| Tracker AUM / creation flow | Piece B, C1 units fix | `etf_flows_harvest.py` — iShares NAV/shares HISTORY needs the DevTools URL (page is JS-built; documented inside the file) |
| Per-stock close-auction volume | close-share truth (TW first) | endpoint hunt registered |
| Announcement dates pre-2015 | longer era studies | archive work, registered |
"""

## PART V — The literature test (c-136): does Taiwan behave
like the academic record says indices behave?

Method: read the index-effect literature, extract its three
core empirical claims, and re-run each claim on our own 157
Taiwan windows. Numbers below computed from
`tw_event_windows.json` (script: inline study, c-136).

### L1 — Permanence and (a)symmetry
The classic result (Chen, Noronha & Singal 2004, JF) is
ASYMMETRY: adds gain permanently, deletions' losses fully
reverse — explained by investor awareness rising on inclusion
but not falling on exclusion. The 2023 re-examination
(Journal of Banking & Finance) finds the modern S&P effect
has decayed and both sides are mostly PERMANENT price moves
tied to fundamentals/flows, not temporary pressure.

**Taiwan verdict: the modern picture, not the classic one.**
- ADD: at E cum +5.6% → E+20 keeps +3.4% (≈60% permanent)
- DEL: at E cum −3.7% → E+20 keeps −2.9% (≈78% permanent)
Both sides largely permanent; no CNS asymmetry. Consistent
with flows-with-information, and it justifies the desk line
that the window move is mostly real, with only the last ~1-2%
(the auction concession) mean-reverting (P3/H4).

### L2 — The price elasticity of index demand
The "index inclusion elasticity" literature (Anatomy of Index
Rebalancings; hidden-costs work) frames the window move as
demand-curve slope: % price per % of float (or ADV) demanded.

**Taiwan estimate: median window return / foreign-net-buy in
ADV-days = 0.0418 per ADV-day (n=36 flow-attached adds).**
A tracker needing 5 ADV-days of stock moves the name ~20% —
which is why the big-demand adds (Yageo-class) print the big
windows. This is our sizing formula for the Aug-26 names:
expected drift ≈ 0.042 × (tracker demand ÷ ADV).

### L3 — Is the effect disappearing?
The US literature documents a shrinking index premium
(Petajisto; the 2023 JBF decay result). Taiwan by year of the
recent era: 2023 +27.2% (Yageo distortion), 2024 −6.3%,
2025 +2.1% — noisy, NOT monotone-decaying, and the era table
(H1) shows an inverted U (peak 2019-22 at +7.6%, softer
2023-26 at +2.9%) rather than a collapse. Read: TW is
CROWDING (alpha migrating earlier into the window, H5
pre-drift growing) — not disappearing. The trade is earlier,
not gone.

### What the literature adds to our question bank
- Q-L4 (open): compute elasticity per YEAR — if slope is
  falling, crowding is supplying liquidity faster than
  trackers demand it. NEEDS: yearly flow coverage pre-2015.
- Q-L5 (open): deletions' permanence vs borrow cost — the
  literature's "awareness" story predicts no relation; our
  crowded-short bounce (+3.3%) suggests pressure DOES matter
  at the tail. NEEDS: SBL fee rates (datasets doc, Tier 2 #5).
- Q-L6 (open): index-provider discretion risk — papers note
  rule-based indices are front-runnable precisely because
  rules are public; MSCI's count-flex (§2.3.3) is the
  discretion valve. Our engine already prices it via bands.
