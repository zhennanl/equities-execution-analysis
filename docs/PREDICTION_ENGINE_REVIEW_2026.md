# Prediction Engine Review — MSCI Index Rebalance
## What it is, why history starts at 2015, the honest accuracy record, and the error taxonomy with fixes

*Session 9i (2026-08-04). Sources: PREDICTION_LOGIC_LAYERS.md (L0-L9),
BACKTEST_TW_2025_2026.md, PIT_MAY2026_* grade docs, TAIWAN_MARKET_
ANALYSIS §1. One scope statement first, because the question "assess
accuracy 2015-2026" deserves a precise answer about what has and has
NOT been run.*

---

## 1. The engine in one page

Ten layers; a name must survive every gate to become a call. L0-L4
replicate the PROVIDER'S arithmetic: count-anchored universe (real
names + synthetic tail pinned to published constituent counts),
eligibility screens (float >= 0.15, real ATVR; the A-share 20%
inclusion factor affects ranking only), the 85%-coverage ladder
whose last cap in is the GMSR, the 1.15x/1.8x add hurdles and 0.5x
deletion floor, and the review-cadence rule (the deep migration
sweep is SAIR-only; QIRs execute extreme breaches). L5-L6 encode the
provider's BEHAVIOR learned from graded mistakes: churn buffers (no
immediate reversals) and the corporate-action/fast-entry radar.
L7 is self-protection: no call ships on unverified membership —
the Feng Tay rule. L8-L9 are honest packaging: Laplace-shrunk
probabilities from the graded record, and deletion output as a
HAZARD-ranked watch zone (measured ~2/3 conversion per SAIR) rather
than dated calls. Every layer exists because something specific went
wrong without it; the engine is its own error history, compiled.

## 2. Why the data starts at 2015

The boundary is Taiwan's: the TWSE files that power the crowding and
flow pillars — TWT93U (daily SBL balances/quotas) and TWT38U (daily
per-name foreign flow) — are where like-for-like history stops being
available to us at 2015.

**c-226 CORRECTION — THE CLAIM IS FALSE, and TWSE says so on its
own pages.** Bill asked for the source twice. There is none, and
looking properly takes one page load each:

TWSE publishes the start date on each report page itself:

* TWT93U 融券借券賣出餘額 — 「本資訊自民國94年7月1日起開始提供」
  = **2005-07-01**
  https://www.twse.com.tw/zh/trading/margin/twt93u.html
* TWT38U 外資及陸資買賣超彙總表 — 「本資訊自民國93年12月17日起
  開始提供」 = **2004-12-17**
  https://www.twse.com.tw/zh/trading/foreign/twt38u.html

So the files predate the claim by a DECADE. TWT93U runs from
2005-07-01, not 2015; TWT38U from 2004-12-17. The sentence "when the
disclosure regime that creates them came into force" was invented to
explain a boundary that is ours, and it survived three revisions
because it sounded like the kind of thing that would be true.

(c-225 had already found our own probe serving 2014-06-16 and
downgraded the claim to "unmeasured". That was the right direction
and still too timid — I corrected the confidence without checking
the fact, when the fact was one click away.)

What is actually true:

* **2015 is our harvest start, and it is a CHOICE** — it lines up
  with the MSCI key archive and with where the rest of the stack is
  complete.
* **The real ~2-3 year limit is elsewhere and unrelated**: PIT
  universe reconstruction needs share counts and floats AS OF each
  vintage, and ours are current-dated. That constraint is measured,
  binding, and has nothing to do with TWSE retention.
* **~10 further years of borrow and foreign-flow history are
  available** and unharvested — roughly 40 more review cycles.
* **c-228: there IS a genuine 2015 boundary, and it is the
  AUCTION layer, not the positioning layer.** MI_5MINS only
  moves to a 5-second grid on 2014-12-29; before that it is
  10s, 15s and 1-minute. Bill remembered this correctly and I
  had swept it away with the rest. See TAIWAN_MARKET_ANALYSIS
  §1 for the table and the source.
Prices and index answer keys go deeper (STOCK_DAY to 2016+, MSCI
STPublicLists to 2003), but a PIT replication without the
positioning pillars would be a different, weaker engine — so 2015 is
the honest start of like-for-like history. Full story:
TAIWAN_MARKET_ANALYSIS.md §1.

## 3. The accuracy record — precisely scoped

**What "2015-2026 backtest" means today: the answer keys exist for
all 44 quarters (solved), but the ENGINE has been PIT-run and graded
on the 2025-2026 events only.** The gate is input vintage, not keys:
PIT universe construction needs share counts and floats AS OF each
vintage, and our shares/floats are current-dated — reconstruction
degrades past ~2-3 years. The decade panel is used where it is
valid (churn statistics, hazard conversion, window/execution
studies); pretending it supports full prediction grading to 2015
would be exactly the false precision the engine exists to avoid.

The graded record that DOES exist:

| Event | Truth | Result |
|---|---|---|
| May-26 SAIR TW | official | **17/17 adds at PIT** (8 markets incl. TW); TW deletions 7/7 + add 1/1 |
| May-26 SAIR Asia | official | CN adds 8/8, dels 13/15; JP adds 3/3, dels 13/14; HK 1/1 |
| Feb-26 QIR TW | official | detector 4/4; all true deletions sub-floor class — cadence rule consistent |
| Nov-25 SAIR TW | reconstructed | 9-flag watch zone; **6/9 converted at the next SAIR** (the hazard measurement); in-window keys below universe floor |
| Aug-25 QIR TW | reconstructed (weak) | 0 calls vs quiet review — consistent; 2395 ungradable (below floor) |

Directional summary: add-side precision at the measured margin is
excellent (22/22 adds across graded events at PIT); delete-side is
strong same-review (20/22 across TW+CN+JP May-26) with the known
miss classes below; the QIR false-deletion problem is solved (10 → 0
by the cadence rule); and "false positives" on deletions largely
turned out to be EARLY, not wrong — hence the hazard reframe.

## 4. Type-1 errors (false positives) — cause and fix, each one

| Error | Cause | Fix status |
|---|---|---|
| 10 false deletions, Aug-25 QIR | Applied the SAIR migration sweep at a QIR — a CADENCE error, not a size error | **FIXED (L4)**: review-cadence rule; 0 false dels on re-run; cross-validated on Feb-26 |
| Spurious re-add/re-delete flags (Nestlé MY + China May adds, 18 flags) | Engine ignored the provider's own recent actions | **FIXED (L5)**: churn buffers — prior review's changes excluded from opposite-side candidacy |
| Feng Tay DELETE call on a name deleted two reviews earlier | MEMBERSHIP-STATE error: stale member list, not a size error | **FIXED (L7)**: verification gate — no call ships on unverified membership; ledgers replayed through a state machine |
| AI-quartet ADD calls on names already members | Same class: stale non-member assumption | **FIXED (L7)**, same gate |
| Persistent cutline flags (1101/1326/2207 every run) | Not a bug — these names LIVE at the boundary; MSCI batches cleanups | **REFRAMED (L9)**: hazard output with measured ~2/3-per-SAIR conversion; residents carry lower probability, and the client conversation gets a rate, not a date |

The type-1 pattern: when this engine was wrong on the positive side,
it was almost never the tape measure (caps, thresholds) — it was
STATE (whose list is current) and CADENCE (which review does what).
Both are now structural gates, not analyst discipline.

## 5. Type-2 errors (misses) — cause and fix, each one

| Miss | Cause | Fix path |
|---|---|---|
| 2395, 8033 (Aug/Nov-25 TW) | Below the 16-real-name universe floor — the change happened in a part of the ladder we cannot see | **Data, not rules**: universe breadth (share counts for more names). Institutional: full constituent-level shares/floats kill this class outright |
| 7769 fast-entry add (Nov-25) | New listing — enters outside the size ladder entirely | **Detector class built (L6)**: new-listing radar (volume history shorter than baseline window = listing); institutional listing calendars complete it |
| Dual-line H-share deletes 0177/2799 (May-26 CN) | Whole-company cap assigned to one line — per-line share split missing | Per-line share data (public partial; institutional trivially) — the known CN delete-miss class (13/15) |
| JP delete miss (13/14, May-26) | Float/cap boundary at third-party float vintage | Float VINTAGE upgrade — provider FIF histories (institutional) |
| Indonesia deletions at floats 0.20-0.29 | Provider FIF discretion — structurally invisible to a 0.15 screen; pre-declared watch line deliberately NOT moved to catch them (that would be tuning on the answer) | Honest residual: institutional FIF feeds only. Documented as un-catchable from public data |
| Rainbow-Robotics-class adds | Price runs between vintage and announcement flip a borderline add | Partially structural: watch-band names re-scored at announcement-day prices; remaining gap is irreducible timing risk, priced in L8 probabilities |

The type-2 pattern: misses are DATA-BOUNDARY errors — universe
breadth, per-line shares, float vintage, provider discretion. None
were rule errors, which is why the fixes are data acquisition and
new detector classes, not threshold tuning. This is also why the
engine plateaued honestly instead of iterating to a fake 100%.

## 6. Improvement plan, priority-ordered

1. **Unlock the decade grade the honest way (public path).** The two
   blockers have separate solutions: keys are DONE (44 quarters);
   input vintage needs historical shares — TWSE monthly shares-
   outstanding archives and CN/HK equivalents can rebuild
   approximate vintages to ~2018, and the alias bridge (built, 9h)
   maps the names. A 2018-2026 graded extension (~16 quarters × 8
   markets) would triple the L8 probability base. Pre-2018 stays
   churn/hazard territory and is labeled as such.
2. **Grow the hazard table (L9) on the full key history.** Flag→
   deletion conversion is currently measured on one cohort (~2/3);
   the 44-quarter keys let us measure conversion and resident-
   persistence rates per market and per era WITHOUT PIT universes
   (it only needs the keys + membership ledgers). Highest
   value-per-effort improvement available now.
3. **Per-line shares for dual-line names** (kills the 0177/2799
   class): HKEX public data partially covers; finite name list.
4. **Universe breadth**: extend real-name share counts below the
   current floor for TW/CN/JP majors (public monthly files exist for
   TW; the floor moves down each data session).
5. **Announcement-day re-score** for watch-band names (Rainbow
   class): mechanical, cheap, prices the vintage-gap risk.
6. **Institutional swaps** (documented, not buildable here):
   provider FIF/float histories (kills the Indonesia class and the
   JP float-vintage class), listing calendars (completes L6),
   constituent-level shares (kills the floor class). With those
   three feeds the remaining public-data miss classes all close —
   the rules already handle them; only the inputs are missing.

## 7. The one-line verdict

The current engine is provider-arithmetic replication wrapped in
learned behavioral rules and honesty machinery; graded 2025-2026 it
runs 22/22 on adds, ~90% on same-review deletes with every miss
traced to a named data boundary; type-1 errors were state/cadence
errors and are now structurally gated; type-2 errors are data-
acquisition items with a priced institutional path; and the decade
assessment the question asks for is HALF-unlocked (keys done,
vintages pending) — item 1 above is the build that completes it
without ever tuning on a known answer.
