# Script Refinement Kit — MSCI Index Review presentation

**How to use this file:** open a new Claude session, attach or
paste this file, and say "run the kit." Everything Claude needs
is inside: the process to follow, the facts it must not deviate
from, my style rules, and the current script's shape. If the
session has access to the project folder, the live script is
`PRESENTATION_SCRIPT.md` — read it; otherwise I'll paste the
sections as we go.

---

## PART 1 · Instructions to Claude (the process)

You are refining a spoken presentation script for me (Bill). The
audience is a program trading desk at CLSA — deep market
knowledge, no patience, ~12 minutes plus questions. Work
**one section at a time**, never the whole script in one pass.

**The loop, per section:**

1. I name a section (or say "next").
2. You show me **two candidate rewrites, labelled A and B**, that
   differ in one meaningful way (e.g., A leads with the number,
   B leads with the question). Keep each under ~120 spoken words
   unless the section is 5.x.
3. I reply with a verdict using the shorthand below, or free
   text.
4. You apply it and show the final version of that section only.
   Then move on.

**Feedback shorthand** (I'll use these words; apply them
without asking for clarification):

| I say | You do |
| --- | --- |
| `tighter` | cut 30% of the words, keep all numbers |
| `plainer` | shorter sentences, no metaphors, no cleverness |
| `punchier` | lead with the strongest number or claim |
| `warmer` | more spoken, contractions, one aside allowed |
| `too AI` | kill parallelism ("not X, it's Y"), stacked em-dashes, three-beat lists, bolded mid-sentence phrases |
| `more me` | rewrite using only sentence patterns from PART 4 samples |
| `numbers` | put the exact figures from PART 3 back in |
| `denumber` | keep at most one figure, describe the rest |
| `A` / `B` | that candidate wins; finalize it |
| `merge` | A's opening + B's body |
| `lock` | section is final; never touch it again in this session |

**Hard rules, always on:**

- Every figure you write must come from PART 3. If a number is
  not there, write `[CHECK: …]` instead of guessing.
- Never revise a `lock`ed section, even if a later change would
  make it inconsistent — flag the inconsistency instead.
- Stage directions in brackets, spoken text as plain prose.
- When I paste a competitor example or a phrasing I like, treat
  it as a style sample, not as content to copy facts from.
- End every session by regenerating ONLY the sections we touched,
  in order, in one block I can paste back into
  `PRESENTATION_SCRIPT.md`.

**First move of the session:** ask me exactly one question —
"Which section first, and is there a section already `lock`ed?"
Then start the loop. Do not summarize this kit back to me.

---

## PART 2 · The talk's fixed shape (do not restructure)

| # | Page | Time | The one thing it must land |
| --- | --- | --- | --- |
| 0 | Opening | 0:20 | Forced demand, not fundamental demand — a dealer's question |
| 1 | Start Here | 0:40 | The two data constraints, up front |
| 2 | Review Database | 0:45 | Every past change, searchable — a lookup tool |
| 3 | Predict Changes | 1:30 | Rulebook reproducible end to end; per-name P(add) |
| 4 | Daily Data | 1:00 | The print is one day; venues differ → why one market |
| 5 | Taiwan Case Study | 7:00 | The close is the venue; here's the order |
| 6 | Agentic Workflow | 1:00 | Fetcher → Analyst → Author → Reviewer; 3 of 4 built |
| — | Close | 0:15 | Four sentences, stop talking |

Case study sub-beats (5.x): ground rules → the trade's two
sides (Expected Flow = P × Δw × AUM; Alpha = Flow ÷ Liquidity;
tracker vs provider) → where volume prints → intraday shape →
close vs VWAP (the self-correction) → what the close absorbs →
foreign flow vs normal day → positioning (flow + holders +
price drift) → order size → deletion borrow check → the null
result.

---

## PART 3 · Fact sheet (the only numbers allowed)

**The venue**
- Ordinary Taiwanese close: **9.5%** of a day's volume. Index
  effective day: **79%**.
- Close vs VWAP reads **−0.06%** but is circular (the auction is
  79% of its own benchmark). Direct measure, last continuous
  price → auction print: **−0.25%** (adds). Reconciliation:
  −0.06% ÷ (1−0.79) ≈ −0.29%.
- Auction file: **2,815 sessions, 11 years**. Effective-day
  impact median ≈ 0, dispersion **3–5× wider** than the same
  name's normal auctions (IQR ~0.45% normal → 1.6% adds / 2.0%
  dels). Nine in ten inside ~1.8%.

**The samples**
- 124 events (52 adds, 72 dels), May-2015 → May-2026 reviews.
- Intraday panel: 43 events (17 adds, 26 dels), IB 5-min bars,
  May-2023 onward only.
- Foreign-flow baseline study: 97 events (39 adds, 58 dels),
  T86 daily file 2015–2026. The counts differ from the intraday
  sections because the instruments differ — deeper file, bigger
  sample. Not a mistake.

**Foreign flow vs a normal day** (per-session rates ÷ the same
stock's own normal |net|; pre window = 30 sessions since c-368)
- Normal day ≈ 7% of ADV (adds' names) / 15% (dels').
- Effective day: adds **+3.2×** normal, dels **−5.1×**.
- Pre-announcement and ann→eff phases: inside ±1× normal.
- Dels keep selling **−1.8×** normal per session for 10 sessions
  after; adds revert.
- Caveat if pushed: T86 nets all foreign accounts → these
  multiples UNDERSTATE gross index demand.

**The August 2026 call** (announcement 12 Aug, effective 31 Aug)
- Cutoff **USD 7.22bn** (±5% band), addition bar 10.83, floor
  4.81, min float 3.61.
- Adds: Nanya 2408 (4.78×, P(add) **>95%**), Nan Ya PCB 8046
  (2.54×, >95%), Winbond 2344 (2.50×, >95%), Phison 8299
  (1.55×, **65%**). Border deletion: Caliway 6919 (1.03× floor,
  P(delete) **36%** — re-struck 11 Aug on the calmer Jul/Aug
  tape after refreshing its stale June price window; vol input
  5.3% → 4.0%).
- P method: 20,000 seeded Monte Carlo draws; rule sharp, two
  inputs perturbed — cutoff ±5%, one-of-ten price dates ×
  realised vol. Free float is taken as computed: the FIF error
  study vs MSCI-implied FIFs has only n=10, too thin to draw
  from, so float error rides in the cutoff band. MSCI
  discretion (count flex, ATVR) is NOT priced — say so if
  asked about the >95%.

**The money**
- Tracking AUM estimate: **USD 125bn** = 45bn named ETFs (31.7
  Standard EM/ACWI + 13.4 MSCI-Taiwan funds) × 2.77 mandate
  multiplier, anchored on MSCI's OWN disclosure — ~USD 5tn of
  non-ETF indexed AUM stated on the Q2-26 earnings call, ÷ the
  2,818bn ETF pool (8-K Table 7) = 1.77× per ETF dollar.
  Cross-check: 56.0m quarterly non-ETF fee × 4 ÷ 5,000bn ≈
  **0.45bp**, a fifth of the 2.28bp ETF rate — mandates pay
  less, measured not assumed. Stated assumption: mandate mix
  mirrors ETF mix (MSCI doesn't split the 5tn by index).
  Downside variant if challenged: the old fee inversion at the
  ETF rate → USD 60bn floor. Never gross up by the 56% bucket
  coverage — the remainder holds no Taiwan.
- Orders at the estimate (four names): Phison **144% of ADV**,
  Winbond **88%**, Nanya **71%**, Nan Ya PCB **55%** — arriving
  in an auction that normally takes 9.5% of the day. At the USD
  60bn floor variant they are 69/43/34/27%. Phison is the
  tightest print AND the least certain add (65%).
- Deletion borrow check (Caliway 6919): SBL balance 9.55m sh,
  **18th percentile** of covered history, **−12%** over 20
  sessions — no visible borrow build. Caveat: SBL only; margin
  and synthetic shorts are invisible.

**The positioning read (as of 07 Aug)**
- All three TWSE-listed adds BELOW peer median on foreign flow
  (Phison is TPEx-listed — absent from the T86 file); TDCC
  large-holder buckets all |z| < 0.75; Nanya price drift
  **−17.6%** excess vs the **+7.0%** a typical confirmed add
  carries. Market-implied P ≈ 0 vs rule-implied >95% — that gap
  is the thesis.

**The honest limits**
- Direction is unpredictable out of sample: best of six fitted
  rules picks 7 events, p = 0.11, and is the max of six draws.
  Null result, reported as one → we size, we don't forecast.
- No MSCI licence (float estimated), no positioning data
  (borrow book, tracker-level fund flows).
- Data provenance if asked: ranks from TWSE official price ×
  point-in-time shares; float is tiered — MSCI factsheet-implied
  (10) → MSCI weights-inversion (66) → Yahoo (319, includes all
  four candidates) → calibrated TDCC (3).

**Forbidden:** USD 180bn (the old unsourced AUM), "P 100%",
1.27× ADV (old basis), any 0.6177/62% flat probability, "±5%
float error moves the cutoff" as a precise claim (say "a small
float error").

---

## PART 4 · My voice (style contract)

**Sound like:** a candidate who did the work, talking to
seniors — confident, plain, direct. Contractions fine.
Transitions explicit ("So", "Now", "Before any of it"). Logical
skeleton visible: claim → evidence → what it means.

**Sentence patterns I've kept** (use these shapes):
- "On a normal day, X. On the effective day, Y."
- "I'd rather volunteer it than be caught by it."
- "That's a sizing input, not a price forecast."
- "Which sounds great, and I didn't believe it."
- "Different instrument, deeper history."

**Kill on sight** (`too AI` markers):
- "not X — it's Y" more than once per page
- three-item rhetorical lists; alliteration; "full stop"
- bolded phrases mid-spoken-sentence; stacked em-dashes
- "honest", "genuinely", "the point is", "here's the thing"
- any sentence that sounds like a LinkedIn post

**Structural preferences:**
- Say out loud that pages 1–4 are setup.
- Volunteer weaknesses before they're asked (the VWAP
  circularity, the null result, the netting caveat).
- Numbers only where they carry the argument; at most ~6 in
  pages 0–4 combined; the case study carries the rest.
- Close = four sentences, then stop.

---

## PART 5 · Q&A bank (keep answers ready, refine on request)

1. "Why trust your float?" → I don't ask you to; the band and
   the flagged coin-flips exist because I don't either.
2. "AUM is a guess" → anchored on MSCI's own numbers: 45bn of
   named ETFs, times 1 + the non-ETF/ETF ratio MSCI itself
   disclosed (5tn ÷ 2,818bn). One assumption — mandate mix
   mirrors ETF mix — and I say it. If you want the number with
   no call-transcript citation, the fee-inversion floor is USD
   60bn and the ranking doesn't move.
3. "Why not gross up from 56% coverage?" → remainder is MSCI
   China/India/Korea funds holding zero Taiwan.
4. "43 events is small" → dispersion not point estimates; the
   auction work is 2,815 sessions on a different instrument.
5. "Is Nanya certain at >95%?" → that's the rule on true
   inputs; MSCI's count-flex and ATVR discretion are not
   modelled, and I say so rather than fake a haircut.
6. "Would you trade it?" → size it, don't direct it; execute in
   the close, zero tracking error by definition; nothing here
   predicts direction.
7. "With a terminal?" → licensed floats (kills the band),
   mandate data (kills the mix-mirroring assumption), holdings on
   benchmark-aware active (the invisible fourth pool), borrow
   book (crowding live). Then the one test I couldn't run:
   realised flow regressed on modelled flow, per event, a
   decade back.
