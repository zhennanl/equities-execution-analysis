# Interview Lessons — a 20-Year Index-Rebalance PM, Applied to Our Process

*Session 9i (2026-08-05). Source: Resonance Spotlight interview with
the head of equity market neutral at a European fund running index
rebalancing since ~2004 (ex-Millennium / BofA / SocGen). Each lesson:
what he said → what we already have (honest) → the concrete upgrade
and where it plugs in.*

## 1. The trade is liquidity PROVISION, not prediction alone

He frames the strategy as being paid to provide liquidity passive
managers must take — "like a market maker... paid for carrying risk."
- **Already have:** the T-day playbook measures exactly this toll
  (print lands AGAINST the obligated side; p_gap_fav 0.08–0.38;
  15–55bps) — our data independently confirms his framing.
- **Upgrade:** reframe Step-1 client materials around the
  liquidity-provision economics (expected toll earned vs risk
  carried), not just call accuracy. Marketing language change, zero
  new data needed.

## 2. Crowding can INVERT the textbook trade (his Apple example)

A $30B, fully-flagged Apple up-weight printed DOWN 2% into the close
— arb flows exceeded passive flows; quants who stopped at the
methodology got run over.
- **Already have:** crowding_watch (5-obs delta alerts), H2
  crowding-build ADOPTED (+149bps direction-corrected), playbook
  cells keyed on crowding, and our measured result that crowded
  prints land against the obligated side — the Apple anecdote is our
  playbook's central finding, observed independently at S&P scale.
- **Upgrade (biggest one): a WRONG-WAY RISK score per event** —
  ratio of estimated pre-positioned flow (cumulative abnormal volume
  since announcement, borrow build, foreign-flow skew) to estimated
  passive demand (index weight x tracking AUM). Above a measured
  threshold, the card should say "textbook direction at risk of
  inversion," and the playbook leg flips from momentum to fade.
  Feasible now for TW/HK/CN from held data.

## 3. Flow-completion tracking ("how much has already traded")

Passive managers know their impact and now spread implementation;
he tracks how much of the expected flow has ALREADY traded before T.
- **Already have:** window-intraday studies, H9 auction-share
  migration (ADOPTED), crowding 5-obs deltas — pieces, not a gauge.
- **Upgrade: a flow-completion ratio** on every live card:
  cumulative excess volume since announcement ÷ expected index flow,
  updated daily in the ann→T window. Directly buildable from the
  ann→eff harvest; becomes the input to lesson 2's score.

## 4. Quant proposal + fundamental/overcrowding overlay + the right to take ZERO

Their process: quantitative proposal first, then a fundamental and
crowding overlay that can retime, resize, filter, skip, or REVERSE —
"we don't have a predefined number of additions or deletions."
- **Already have:** the honesty analog — validated-zero posture,
  shortlist p's, no forced calls. What we lack is the structured
  overlay step between engine output and the desk.
- **Upgrade: a CONVICTION GATE on each call/card** — a checklist
  section: pending corporate events on the name, halts/limit-move
  regime, borrow availability, crowding read, wrong-way score →
  verdict TAKE / RESIZE / RETIME / SKIP / FADE, recorded and graded
  like every other output. The gate's grades build the record that
  tells us when the overlay adds value vs when it burns it.

## 5. Corporate-event-driven index changes are a BLIND-BAND cause

M&A, delistings, spin-offs drive changes the cap ladder cannot see;
he says this channel is growing.
- **Already have:** nothing structured — part of our BLIND_SHARE is
  exactly this channel, unnamed.
- **Upgrade: a corporate-events watch in Step 1** — scrape announced
  M&A/delistings/suspensions touching current members (TWSE/TPEx
  notices, reg-watch feeds we already collect) and attach an
  event-driven deletion flag independent of the cap ladder. This
  converts part of the blind band from "unobservable" to "observed
  via a different instrument" — the single most direct BLIND_SHARE
  reduction available.

## 6. Regime-conditional priors (his published VIX result)

Their research: higher vol regimes → more small/mid-cap dispersion →
more migration candidates → bigger rebalances (index-family
specific; NOT true for the S&P 500).
- **Already have:** unconditional decade priors (L8) — P(any) per
  market×review ignores regime.
- **Upgrade: registry v4 candidates (LOCK BEFORE EVALUATION):**
  H13: trailing 6-m index vol vs number of changes at the next
  review, per market, on the 46-review outcome key. H14: same with
  rate regime. If ADOPTED, L8 priors become regime-conditional; his
  own caveat (family-specific, may be null for TW) makes this a
  clean pre-registered test either way.

## 7. Alpha decay and the R&D treadmill

"What made you successful 10 years ago is not a given... question
every success, it WILL disappear."
- **Already have:** this is our variable-lab constitution — locked
  registries, misses ship, nulls pinned, Aug-2026 as standing OOS.
- **Upgrade:** none needed to philosophy; add a decay check to the
  yearly protocol — re-grade ADOPTed variables (H2/H5/H9) on each
  new season and demote on failure, exactly as H3 was demoted.

## Priority order (feasibility x impact, all from held data)

1. Flow-completion ratio (3) — direct build, feeds everything else
2. Wrong-way risk score (2) — the Apple lesson, our playbook's core
3. Corporate-events watch (5) — named BLIND_SHARE reduction
4. Conviction gate (4) — process discipline, graded like all output
5. Registry v4 H13/H14 (6) — locked test on the outcome key
6. Marketing reframe (1) — language only
