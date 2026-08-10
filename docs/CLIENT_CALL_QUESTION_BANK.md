# The client-call question bank (c-137)

Premise: not "what would a researcher measure" (that is the
34-question liquidity bank) but **what a client actually asks
a CLSA PT trader on the phone** — trackers ask about getting
FILLED, hedge funds ask about EDGE, CAPACITY and PAIN. A
question earns its place only if a desk that can answer it
wins the order. Statuses: [NOW] = answerable from data on
disk (file cited); [DESK] = needs CLSA internal data (flow
logs, crossing records) — flagged so Bill can name them in
the interview as what the desk's own exhaust would unlock;
[NEEDS] = needs a dataset from TW_DATASETS_BRAINSTORM.md.

## A. The tracker's calls (an index PM at BlackRock/Vanguard)
The tracker cannot choose WHETHER to trade — only how. Every
question is about fills, mechanics, and defensible deviation.

- **T1. "Will I even get filled at the close?" Limit-lock
  risk.** TW has a daily price limit (7% pre-Jun-2015, 10%
  after). If the name locks limit, my MOC doesn't fill and I
  carry overnight tracking error. [NOW — ANSWERED, first
  cut, tw_event_windows.json]: **adds have NEVER near-locked
  the limit on effective day (0/64); deletions near-lock
  9.7% of effective days (9/93)** — the fill risk is real
  ONLY on the sell side, one in ten. Within-window days lock
  ~3.5% either side. Desk line: "your add MOC fills; your
  del MOC has a 1-in-10 chance of a locked market — we
  pre-plan the overflow into E+1."
- **T2. "How much can you cross?"** If CLSA holds both the
  tracker buy and the HF unwind, an internal cross saves
  both sides the auction spread. What share of effective-day
  flow historically crossed? [DESK — crossing logs. Public
  proxy: our C3 answer (arbs DO sell into the close) proves
  the other side exists; its size per name is desk exhaust.]
- **T3. "If I show you the full order, what does leakage
  cost me?"** Split-across-brokers vs single-broker; does
  pre-announcing size move the window against me? [DESK —
  needs order-level data; the honest public answer is the
  elasticity number: 0.042/ADV-day IS the cost of the flow
  being visible in aggregate.]
- **T4. "What does the auction itself cost per unit of my
  size?"** Impact per %-of-auction-volume, not per ADV —
  is the auction nonlinear? [NOW, partially — Q32/Q33 give
  demand-conditional dispersion (p95 7.6% high-demand vs
  5.7% low). A per-%-of-auction curve NEEDS per-stock
  auction volume (brainstorm: close-auction endpoint hunt).]
- **T5. "Can I trade E−1 instead and how wrong can it go?"**
  E−1 close vs E close tracking difference distribution.
  [NOW — eff_day IS that distribution: ADD med −0.4% /
  DEL −1.6%, with P3 revert showing part comes back.]
- **T6. "How much of the market's rebalance volume prints
  before E?"** If most prints early, my MOC is the residual.
  [NOW — ANSWERED: E−1 volume is only 28% (ADD) / 12% (DEL)
  of E volume; C1 progress metric says the window trades
  early in RETURN space but volume mass is squarely at E —
  the flow waits for the print even though the price moved.]
- **T7. "Foreign-room risk: can I buy at all?"** For names
  near the FOL cap (financials, telecom), can the full
  tracker demand clear before foreign room closes? [NOW,
  screen-level — MI_QFIIS room in tw_universe_pit; a breach
  ledger across history NEEDS the daily QFIIS backfill
  (brainstorm Tier 2 #6).]
- **T8. "What about the weight-CHANGE trades?"** Most index
  turnover is FIF/NOS re-weightings, not add/del. Do small
  weight changes drift too, or is the effect add/del-only?
  [NEEDS — QCIR weight-change lists per review; harvestable
  from consecutive factsheet/constituent snapshots we
  already store. High value: it is the UNstudied 80% of
  tracker flow.]
- **T9. "Are there corporate-action landmines in the
  window?"** Ex-dividend dates inside ann→eff distort both
  my benchmark and your drift stats. [NEEDS — t187ap
  announcements day-file (brainstorm Tier 3 #8); cheap
  join, flags contaminated analogs too.]

## B. The hedge fund's calls (a Millennium pod PM)
The HF can choose everything — so every question is edge,
sizing, and what kills them.

- **H7. "How crowded is THIS event vs history?"** Not the
  average — a percentile for the current window. [NOW — the
  live loop computes borrow-build + pre-drift vs the 157-
  window historical distribution; S3 excess-vs-tide z is the
  separator that actually works.]
- **H8. "What's my capacity before I AM the market?"** At
  what size does my own entry consume the drift? [NOW,
  first-order — invert elasticity: at 0.042/ADV-day, buying
  0.5 ADV-day costs ~2.1% of the ~4% median drift; capacity
  ≈ 0.5-1 ADV-day per name. The nonlinear version NEEDS the
  T4 auction curve.]
- **H9. "For the del short: locate, fee, and RECALL risk."**
  Trackers lending the stock must recall before they sell it
  — does borrow tighten mechanically into E? [NOW, size only
  — SBL balance path exists (idx1); fee and recall NEEDS SBL
  fee-rate feed (brainstorm Tier 2 #5).]
- **H10. "What's the max squeeze if I'm crowded-short a del
  with the crowd?"** The MAE analog on the short side. [NOW
  — computable from windows + C_del_borrow crowded tercile:
  the +3.3% E+5 bounce IS the squeeze; per-window MAE on
  dels is one function call away in event_conditional.]
- **H11. "Would you quote me a guaranteed close?"** Risk
  price on the auction print — what spread is fair given the
  dispersion? [NOW, pricing input — the desk's fair spread
  ≥ the p75-p25 eff_day band (~4.6%) scaled by hedge
  quality; the actual quote is a principal-desk decision.
  Good interview answer: agency-only CLSA does NOT hold this
  risk — it advises instead.]
- **H12. "Does the alpha diversify across APAC?"** If I run
  TW+KR+JP+IN books, are window alphas correlated (one
  regime) or independent (12 uncorrelated bets/year)? [NOW
  — apac_event_metrics has per-market alphas on a shared
  calendar; cross-market correlation of same-review alphas
  is computable today. Unasked in any bank so far.]
- **H13. "What if MSCI corrects or re-flags between ann and
  eff?"** Frequency and price impact of mid-window
  announcement corrections/early inclusions. [NOW, count
  only — our announcement registry shows off-cycle events;
  systematic correction-tagging NEEDS archive work.]
- **H14. "Intraday on E: when does the flow arrive?"** Short
  the open and cover 13:25, or wait? Path of E-day. [NOW for
  2023+ shortlist names — ib_bars 5-min; full history NEEDS
  paid ticks (brainstorm Tier 3 #9).]
- **H15. "What regime kills this trade?"** Not the median —
  the conditional where I lose. [NOW — S1: risk-off tapes
  (TAIEX −4%+) kill raw adds (Teco −17%) while excess
  survives; 2024 cohort −6.3%. The screen: hedge beta,
  fade cold starts, size to MAE p10 −9.7%.]

## C. The questions the DESK should ask itself before either
client calls (prep, not phone)

- **D1. Calendar collisions.** When MSCI eff collides with
  FTSE-TW or 0050 rebalance week, whose flow dominates the
  close? [NEEDS — local tracker units (brainstorm Tier 2
  #7) + FTSE dates join; the Nov-25 ambiguity is exactly
  this.]
- **D2. Auction microstructure regime breaks.** TWSE moved
  to continuous trading + 5-min call auction close in
  Mar-2020; limit widened 2015. Do pre-break stats still
  bind? [NOW — split every headline stat at 2015-06 and
  2020-03; the era tables already do this implicitly, the
  explicit regime-break table is one script away.]
- **D3. The off-cycle tail.** IPO fast-track inclusions and
  deletion-for-suspension arrive OUTSIDE review windows with
  ~5-day notice — different playbook? [NOW, partially — the
  off-cycle census exists (c-120s); their event windows are
  harvestable with the same tooling.]

## Scoreboard
NOW fully: T1 ✓ (answered), T5, T6 ✓ (answered), H7, H8,
H10, H12, H15, D2. NOW partial: T4, T7, H9, H11, H13, H14,
D3. DESK (name them in the interview): T2, T3. NEEDS: T8
(QCIR weight-changes — highest value), T9, D1.

Next compute batch, in value order: **H12 (cross-market
correlation) → T8 (weight-change drift) → D2 (regime-break
table) → H10 (del-side MAE)**.
