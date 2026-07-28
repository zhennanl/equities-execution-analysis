# Reg-Watch — Design Notes (JD Bullet 5)

*Session 7l. Module `agents/reg_watch.py`, page `views/page5_regwatch.py`,
script `scripts/fetch_reg_notices.py`, 11 tests (suite 358).*

## The design problem

A PT desk trades against rules that change — short-sell regimes, limit
bands, lot sizes, auction mechanics, session hours — published as
circulars across 10+ exchanges in 4 languages. Desks track this today
with humans reading notices and compliance memos. The failure modes:
a missed change (trade against a dead rule) and triage fatigue (40
irrelevant circulars a day). The design answers both, under one
non-negotiable: **nothing auto-mutates the rules the desk trades on.**

## Architecture: three layers, one gate

1. **Versioned rules registry — single source of truth.** Every rule is
   an entry: value, version, effective date, source, approver. Seeded
   v1 from the project's static tables (public-rule approximations,
   disclosed). `pt_dealer` now reads limit bands and auction cutoffs
   FROM the registry (lazy import, static fallback) — an approved
   change propagates to `limit_proximity`, `auction_countdown`, and the
   compliance pre-flight with no code edits. `rules_version()` folds
   the registry hash into every audit pack, so an auditor can see which
   rule state produced each check. Tested end-to-end:
   `test_approved_change_propagates_to_pt_dealer` widens Taiwan's band
   via the workflow and watches `limit_proximity` reclassify a +12% day
   from LOCKED to WATCH.
2. **Notice triage.** Fetch public feeds → deterministic multilingual
   keyword classifier (zh/ja/ko/en; substring matching, no tokenizer
   dependency; fully offline-testable) → HIGH/MED/IGNORE → daily
   markdown digest with pending-approval diffs at the top.
   **LLM hook:** `llm_summarize_hook(notice, llm=...)` is a slot for a
   desk-approved endpoint — richer summaries where permitted, template
   digest where not. Public notice text only; never client or order
   data; always upstream of the human gate.
3. **Human approval workflow.** `propose_change` (with source citation)
   → pending queue → `approve` (version+1, supersede, log) or `reject`
   (logged with reason). The approval log IS the audit trail of how the
   desk learned each rule.

Cross-check: `market_structure` drift detection catches changes the
circulars (or keyword net) miss — a lot/tick regime change shows up in
spread/size distributions empirically.

## Feed status (probed live, honest)

| Source | Lang | Status |
|---|---|---|
| TWSE openapi news | zh | IMPLEMENTED (479 notices on first fetch) |
| JPX news json | ja/en | IMPLEMENTED (90) |
| NSE circulars api | en | IMPLEMENTED (139) |
| TPEx / HKEX / KRX / SGX / SET | — | PROTOCOL (403/JS from sandbox; desk network or subscription feeds) |

## First live run validated the concept

The 2026-07-28 digest surfaced, unprompted: **NSE's introduction of a
Closing Auction Session in the equity cash segment** (mock-trading
circulars — a structural change to how every India MOC order will
work), JPX daily-price-limit broadenings (the exact per-stock band
mechanic), and TWSE margin/short-sell eligibility changes. 708 notices
in, 69 HIGH out — and the single most execution-relevant regulatory
story in Asia this month was in the top block.

## Honest limitations

Keyword recall is bounded: a notice avoiding standard vocabulary slips
to IGNORE (mitigations: HIGH-side bias in term lists, the empirical
drift cross-check, and MED review). Precision is imperfect the other
way (mock-session circulars rank HIGH — arguably correct for CAS
testing, noisy in general). The registry's seed values are public-rule
approximations — compliance owns the golden copy on a real desk; this
is the dealer-side mirror with provenance. Notice BODIES are not
fetched (titles only) — the LLM hook is where body-level extraction
would land, on a desk-approved endpoint.

---

## Addendum (session 7m) — from notice pile to proactive insight

User review verdict accepted: gathering announcements is INPUT, not the
product. New pipeline (all deterministic, all explainable):

    fetch (all feeds) -> diff vs seen-state -> cluster into STORIES
    -> score importance -> flash brief (only when something matters)
    -> drill-down links to raw notices

**Story clustering** (`cluster_stories`): titles normalized (department
prefixes, stock codes, dates, counts stripped) so six NSE CAS mock
circulars or three JPX limit-broadening notices become ONE story with
N links. Live: 708 raw notices → 109 stories.

**Importance scoring** (`score_story`): category weight (price
limit/auction/session/short-sell 3 > settlement/lots 2 > fees 1) ×
scope multiplier (market-wide 3 / subset 2 / single-stock 1, detected
from title patterns) + drumbeat bonus (repeated notices) + BASKET
RELEVANCE (+3 when a story touches a name in the trader's working
basket — pass the residuals, get personal ranking) − mock/test
dampening (×0.6: a mock session is NOTABLE; the go-live is FLASH).
Tiers: FLASH ≥8 / NOTABLE ≥4 / ROUTINE. Every score prints its
reasons — no black-box ranking on a desk.

**Impact notes** (`IMPACT_NOTES`): each category maps to WHAT IT MEANS
FOR EXECUTION ("auction mechanics drive MOC benchmarks and cutoff
discipline..."), so the brief reads as trading language, not
compliance language.

**Proactive delivery** (`watch` mode in fetch_reg_notices.py): seen-ID
state; on each scheduled run only NEW notices are clustered and scored;
a flash brief file is emitted ONLY when a FLASH/NOTABLE story arrived.
Silence means no news — alert fatigue is a design goal. First run
establishes the baseline (758 IDs) without alerting.

**UI:** the triage tab now renders stories (tier badge, score, impact,
scoring reasons) with the raw notices one expander-click deeper, plus a
basket-names box for personal relevance boosting.

## Why only 3 feeds at first (now 4) — the honest answer

All APAC exchanges publish notices; the constraint is anti-bot
infrastructure, not availability. From this sandbox's plain HTTP
client: TWSE, JPX, NSE responded on first probe; **SGX yielded on the
second attempt** (its circulars API works with a Referer header — 4th
live feed); TPEx/HKEX/KRX/SET/Bursa/IDX/HOSE serve 403s or JS-rendered
shells to non-browser clients. Coverage grid: 4/12 live from the
sandbox, 8 PROTOCOL. On a desk this constraint mostly disappears —
desk networks, vendor terminals (Bloomberg regulatory news), exchange
e-mail subscriptions, and compliance feeds cover the rest, and the
pipeline is source-agnostic: anything that lands as
{source, date, title, url} joins the same clustering/scoring. The
registry itself covers ALL 15 markets regardless of feed status.

Suite: 364 passed. Design rule kept: scoring is deterministic (LLM
hook remains a summarization slot, never the ranker).
