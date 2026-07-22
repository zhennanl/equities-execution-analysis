# CLSA PT Dealer — JD Mapping & Desk Automation Roadmap

*Built session 6h against the CLSA Program Trading Stock Dealer JD.
Companion to HANDOFF_CLSA_PORTFOLIO_TRADING.md (interview capsule).*

---

## 1. JD bullet → platform feature

| JD responsibility | Platform feature | Status |
|---|---|---|
| Execute program trades across Asia, support basket execution | Page 3 program blotter (`run_program_pretrade`), basket mode on Page 2 | existing |
| Monitor intraday liquidity/volatility/market conditions | **Attention queue** (`pt_dealer.attention_queue`): one ranked list — limit proximity + auction urgency + behind-schedule + dry tape, explicit reasons | NEW 6h |
| Minimize impact, slippage, transaction costs | Cost model + algo simulator + IS attribution + markouts (Page 1); per-event strategy frontier (Page 2) | existing |
| Coordinate cross-market execution across time zones | `wave_plan` (market ordering) + **`auction_countdown`** (per-market close-auction mechanism + minutes-to-cutoff) | existing + NEW 6h |
| Market-specific regulations: short-selling, lot sizes, circuit breakers | `MARKET_REG` reference + `lot_check` + `short_check` + **`limit_proximity`** (daily-band usage with WATCH/ALERT/LOCKED levels) | existing + NEW 6h |
| Regulatory adherence during execution & reporting | Pre-flight checks run per name in the blotter; short-BLOCK pins attention score to 100 | existing + NEW 6h |
| Accurate trade records, audit readiness | **Audit pack** (`build_audit_pack`): timestamped JSON of basket + every check + attention state, written as a by-product, not reconstructed | NEW 6h |
| Post-trade settlement, reconciliation, discrepancies | `settlement_date` (T+n by market) + `program_recon` breaks report | existing |

**The cockpit's design principle:** a dealer watching 6 markets doesn't need
more screens — they need one ranked list saying who needs their eyes NOW and
why, in words they can challenge. Score weights: limit 40 / auction 25 /
behind-schedule 20 / liquidity 15; short-sale BLOCK overrides to 100.

## 2. What the cockpit knows per market (static tables, disclosed)

- **Daily bands:** TW ±10, CN-A ±10 (ST ±5 / STAR-ChiNext ±20 noted),
  KR ±30, TH ±30, VN ±7, MY ±30, ID ~±20 proxy, JP ~±18 tier proxy,
  IN ~±10 proxy; HK/SG/US/AU/UK = dynamic mechanisms (VCM, CB, LULD), no
  static band — flagged n/a with mechanism note.
- **Close-auction cutoffs:** TW 13:25→13:30 call; JP 15:25→15:30; HK CAS
  16:00–16:10 (no-cancel + random close); KR 15:20→15:30; CN 14:57→15:00
  (no cancels); SG/IN/AU/US/TH/ID/MY/VN/UK per table.
- **Everything carries the disclaimer:** static approximations of public
  rules; a desk deployment replaces these with exchange parameter feeds
  (lot files, band tiers, holiday calendars). This honesty is a feature —
  say it in the interview.

## 3. Automation roadmap — NOW IMPLEMENTED (session 6i)

Items 1-5 below are implemented in `agents/pt_automation.py` + Page 3
"Desk Automations" section (tests: tests/test_pt_automation.py); item 6 is
the Page-4 QBR; item 7 is `pt_dealer.rules_version()` stamped into every
audit pack, alert acknowledgment, and pre-open pack.

Ordered by effort-to-value; each starts from a piece the platform already
proves out:

1. **Pre-open basket pack (T-1 evening / pre-open).** Client file lands →
   auto-parse, normalize lot sizes per market, run compliance pre-flight
   (lot/short/limit/ownership flags), estimate per-name + basket cost,
   side/exposure imbalance, auction capacity vs order size, settlement
   dates per market — one PDF/email to the sales trader before the open.
   *Platform proof: run_program_pretrade + audit pack.*
2. **Intraday attention alerting.** The attention queue pushed to
   chat/EMS instead of a screen: limit WATCH→ALERT transitions, cutoff
   T-15 with unfilled residuals, run-rate collapse. Dealer acknowledges;
   acknowledgments land in the audit trail. *Proof: attention_queue +
   auction_countdown.*
3. **EOD client summary auto-draft.** Per program: fills vs benchmark,
   residuals + roll plan, notable events (locks, halts, VCM triggers),
   settlement calendar — drafted automatically, dealer edits 10%, sales
   trader sends. *Proof: desk pack text generator + QBR aggregations.*
4. **Recon break classifier.** Triage settlement/recon breaks by cause
   pattern (qty vs price vs missing-fill vs FX) and route the obvious
   ones; humans keep the ambiguous tail. *Proof: program_recon.*
5. **Index-event radar.** The Page-2 rebalance calendar + crowding score
   pointed at the desk's client holdings: "these 14 names in client
   baskets are in the MSCI review window; close-volume multiples expected
   3–8×." *Proof: Agent 12 calendar + crowding score.*
6. **Quarterly client review pack.** The Page-4 QBR (difficulty-adjusted,
   CI-gated) as the desk's standard review deck — the PT Sales Trader
   progression path in the JD makes this the natural "grow into
   client-facing" artifact.
7. **Rule-table service.** Replace static bands/lots/cutoffs with a small
   internal service fed by exchange notices + holiday calendars, versioned
   so the audit pack records WHICH rule version every check used.

## 4. Honest boundaries

Simulated fills on historical bars; static rule tables with proxies for
tiered bands (JP/ID/IN); no holiday calendars in settlement math; no FX
leg; no real-time feed (yfinance 5-min bars / kdb+ / tick files). None of
this is hidden — every table and note discloses it, because an agency desk
audits claims.


## 5. Round 2 automations (session 6m — `agents/pt_ops.py`, Page 3)

| # | Automation | JD bullet | Key behavior |
|---|---|---|---|
| A8 | Client file normalizer | "coordination with sales traders / client-driven flows" | Bloomberg codes ("2330 TT"→2330.TW, "700 HK"→0700.HK), B/S/1/2 sides, notional→shares at supplied prev close; duplicates aggregated; every guess/skip is an explicit ISSUE, never silent |
| A9 | Holiday-aware settlement + closures + FX notes | "cross-market coordination / settlement" | 2026 Asia closures (approx, disclosed): CNY cluster pushes TWSE T+2 from Feb-12 to Feb-24; Golden-Week warnings; TWD/KRW/INR restricted-currency notes |
| A10 | Internal crossing detector | "client-driven flows / minimize costs" | Same name, opposite sides, different clients → crossable qty + spread saved + the COMPLIANT mechanism per market (ToSTNeT / HK direct-business reporting / China-A exchange-only) |
| A11 | Two-sided exposure scheduler | "optimize execution / coordinate" | Terminal net is structural; scheduling controls the PATH — front-loaded urgency throttled to a ±band around the structural line, with the unthrottled counterfactual reported |

Tests: tests/test_pt_ops.py (12). All Page-3 "Desk Automations — round 2" expanders.
