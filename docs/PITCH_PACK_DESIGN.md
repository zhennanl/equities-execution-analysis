# Pre-Mandate Pitch Pack — Design & Institutional AI Leverage

*Session 7o. The analytics that win broker selection (lifecycle Step 1 /
Phase 0). Module `agents/pitch_pack.py` (6 tests), real example
`scripts/build_pitch_pack_tw50.py` →
docs/case_studies/PITCH_PACK_TW50_Jun2026.md.*

## Why this is the right place to invest analytics

Broker selection happens BEFORE the order exists, and among qualified
brokers the tie-breaker is differentiated content (factor #4 in the
selection ranking, and the cheapest to be exceptional at). The pack is
the sales trader's weapon: predictions with confidence, flows with
buckets, positioning reads, measured event behavior, risk flags — and a
track record that includes its own misses.

## The seven sections and their engines

| Section | Engine | Public data |
|---|---|---|
| 1. Predicted changes + confidence | reconstitution (GMSR/rank buffers) | caps, floats, memberships |
| 2. Expected flows + ADV buckets | index_flow (self-financing sim) | AUM disclosures, ADV |
| 3. Measured T-day behavior | event_flow_study (21 real 2026 names) | exchange volumes/prices |
| 4. Street positioning | event_data short ledger | TWSE TWT93U daily |
| 5. Risk flags | deterministic rules | limit bands, borrow, ADV |
| 6. Track record w/ misses | graded case-study library | our own git history |
| 7. Post-event validation | validate_pack | outcomes vs claims |

## Two design rules that ARE the product

**Point-in-time discipline.** `as_of` gates every input; the June-1
example provably uses nothing after June 1 (tested:
`test_t_multiples_point_in_time_gating`, `test_crowding_table_respects_as_of`).
Without this the validation loop is theater. With it, the pack becomes
a falsifiable document — which is the entire sales pitch to a
quantitative client.

**The desk grades itself.** `validate_pack` scores the pack's own
claims after the event and the scorecard is appended to the same
document. June example results: 6/8 actual changes called, **4/4
HIGH-confidence calls correct**, misses listed by name (1101/1326/2615
false flags; 2002/1301 not predicted — with the section-4 crowding
table showing the street at +74.5% on China Steel anyway, which is
what the 7i STREET-ONLY overlay now catches systematically).

## What the June-1 example shows a client

The add side was actionable (4/4 HIGH, margins 17-78%); the delete side
was honestly labeled a watch zone and behaved like one; the crowding
table carried real information the model didn't (China Steel); MSCI
T-multiples were quotable (median 16x, n=8) while FTSE said "no
measured events yet" instead of guessing. A client comparing this
against a competitor's confident-everything pitch sees the difference
immediately.

## Institutional AI leverage (with desk data and approved LLM access)

Ranked by impact:

1. **Client-conditioned packs.** The same engine output, rendered per
   client: their benchmark, their tracking tolerance, their (13F/public
   filing-inferred or disclosed) holdings overlap with the event names
   — "your funds hold 3 of the 4 adds already" changes the whole
   conversation. LLM renders the narrative per client from the same
   deterministic tables; numbers never come from the LLM.
2. **RFQ win/loss learning loop.** Log every pitch → mandate outcome →
   realized execution. Over cycles, learn which pack sections and which
   claims correlate with winning (and with profitable mandates) —
   the same predicted-vs-realized discipline we run on execution,
   applied to sales.
3. **Automated pack refresh.** The pack regenerates nightly from the
   forward archive between announcement and T; the client link always
   shows current crowding and provider amendments — a living document
   instead of a PDF, with a change log (what moved since yesterday,
   auto-summarized).
4. **Cross-event memory (RAG).** Sales traders answer client questions
   with retrieval over every graded case study and event post-mortem:
   "what happened last time an MSCI delete was borrow-constrained?" →
   the THSR/Compermed evidence, cited. The corpus is exactly what this
   project has been building.
5. **Bespoke scenario turnaround.** Client asks "what if we split
   40% pre-position / 60% MOC?" — the crowding-adjusted frontier
   already prices it; LLM-assisted intake turns the emailed question
   into the parameterized run and drafts the reply for the sales
   trader's sign-off. Minutes instead of hours = more at-bats per
   mandate.
6. **Anomaly-triggered pitches.** The watch loop (Reg-Watch pattern)
   monitors crowding and provider notices; when something notable
   happens in a name a target client cares about, it drafts the
   outreach note. Proactive coverage at machine frequency, human send.

Human-in-the-loop invariants: LLMs render and retrieve, never predict
or rank; every number traces to a deterministic engine; every outbound
artifact carries the track-record section including misses; client
data stays inside the client's pack.

## Honest boundaries

The June example uses the round-2 backtest's predictions (built on a
reconstruction-grade universe, disclosed in the pack notes) — a desk
build uses vendor cap files and the live screener. Flows use the $70B
0050-only AUM lower bound. The validation loop has run on ONE event;
the Aug 12 QIR pack will be the first born-live pack (pre-registration
protocol), which is the real test. Section-5 borrow flags are
parameter inputs, not yet wired to an SBL-utilization feed (next
fetcher, unchanged).
