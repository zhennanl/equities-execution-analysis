# Closing Auctions Across Asia — The Mechanics That Set the Benchmark Print

*Session 8n (2026-07-29). The T-day goal is one number: the official
closing price. This reference is how each market PRODUCES that
number — mechanism, windows, cancellation rules, transparency, and
what each detail means for a PT desk completing an index basket.
Consolidates pt_dealer.AUCTION_CUTOFFS (live registry), the measured
TW auction work, and today's verification searches. Times local.*

---

## The one-line taxonomy

Three ways Asia prints a close: (1) a TRUE CALL AUCTION (TW, JP, KR,
CN, HK, SG, TH, MY, ID, VN — one matched print, MOC-able); (2) a
VWAP WINDOW (India today — no single print exists; you replicate an
average, not an auction); (3) India AFTER Aug 3, 2026 — migrating to
a call auction (CAS) for F&O names. Everything about T-day sizing,
cutoff discipline, and "hiding in the print" follows from which of
the three you are in.

## Per-market mechanics

| Market | Mechanism | Window (close) | No-cancel / cutoff | Transparency during window | Random end |
|---|---|---|---|---|---|
| Taiwan (TWSE) | Call auction | 13:25–13:30 | orders rest from 13:25 | **BEST IN ASIA: indicative price+volume broadcast every ~5s** | no |
| Japan (TSE) | Closing auction (itayose) at 15:30 (post Nov-2024 reform) | orders accumulate to 15:30 | amendable to the print | order book visible (itayose quotes) | no |
| Korea (KRX) | Call auction | 15:20–15:30 | continuous stops 15:20 | expected price disseminated | no |
| China A (SSE/SZSE) | Call auction | 14:57–15:00 | **NO CANCELS 14:57+** | indicative match shown | no |
| Hong Kong (HKEX) | CAS, 4 phases | 16:00–16:10 | phase-gated: reference-price band ±5% then ±2%; no-cancel phase | IEP/IEV published | **yes, 16:08–16:10** |
| Singapore (SGX) | Pre-close call | 17:00–17:06 | non-cancel sub-phase | IEP shown | yes, to 17:06 |
| Thailand (SET) | Call auction | after 16:30 | at random-close trigger | projected price | **yes, closes 16:30–16:40** |
| Indonesia (IDX) | Pre-closing call 15:50–16:00 + closing auction to ~16:05 | order entry 15:50–16:00 | at window end | IEP disclosure (post-2019 reform; random-close under review) | partial |
| Malaysia (Bursa) | Pre-close phase with Theoretical Closing Price (TCP) | 16:45–16:50 into 17:00 | at phase end | TCP published | no |
| Vietnam (HOSE) | ATC call | 14:30–14:45 | **no cancels in ATC** | limited | no |
| India (NSE/BSE) — TODAY | **NO AUCTION: close = VWAP of a 30-min window** (recently shifted to 15:10–15:40 for derivative alignment); post-close session 15:40–16:00 trades AT the close | n/a — it's an average | n/a | n/a | n/a |
| India — FROM AUG 3, 2026 | **CAS call auction 15:15–15:35 for F&O stocks** (SEBI reform); non-F&O stays VWAP | 20-min session | per CAS rules | expected | tbd |

*Registry note: pt_dealer.AUCTION_CUTOFFS is the live source for
cutoffs (versioned via Reg-Watch); this doc adds the mechanism
detail. The India row is a Reg-Watch FLASH-class change — see below.*

## What each mechanic means for index execution

**Rationing and the meaning of "MOC-able."** In a call auction your
MOC order fills at the single matched price — but only the crossing
volume prints. If the auction is one-sided (every tracker the same
way), the price moves until enough contra shows; in band markets
(TW ±10%, CN ±10%, VN ±7%, TH ±30%) the price can hit the band
before contra arrives — limit-lock, partial or zero fill, forced
T+1 residual. Auction capacity, not desk skill, binds first.

**Transparency ranking drives the T-day playbook.** Taiwan's 5-second
indicative broadcast is the only real-time "how violent will the
print be" feed in Asia — hence our indicative-vs-expected read is a
TAIWAN tool first. HK's IEP/IEV and Bursa's TCP give a slower
version; Japan's itayose book is readable; China gives 3 minutes of
locked-in imbalance; VN gives almost nothing. Where transparency is
poor, the lunch run-rate checkpoint carries MORE weight — it is the
last reliable signal before the print.

**No-cancel windows are commitment devices.** China's 14:57 and
HK's no-cancel phase mean the decision deadline is EARLIER than the
print: our cutoff column, not the auction time, is the real
deadline. The run-sheet orders the cascade by CUTOFF.

**Random ends (HK/SG/TH) kill last-second gaming** — you cannot
snipe the final indicative; plans must be right at cutoff, not
clever at 16:09:59.

**HK's CAS price bands (±5% then ±2% off the reference) cap the
print's violence** — a crowded CAS shows up as volume, not price
gap; the reversal trade is smaller in HK than in band-free theory.

**India is the special case, twice over.** Today: no print to hide
in — completing an Indian index name means REPLICATING A 30-MINUTE
VWAP (algo work, participation discipline, no single-moment risk
transfer). From Aug 3, 2026: F&O names (≈ all MSCI India
constituents) move to a genuine closing auction — and our Sep-1
MSCI effective day will execute into a mechanism that is FOUR WEEKS
OLD, with no measured event history, unsettled auction-share norms,
and every desk learning simultaneously. That is both a risk flag
for the Aug pack (India flows: no T-multiple prior applies — the
VWAP-era priors are the wrong reference class) and exactly the kind
of regime change Reg-Watch exists to catch.

## Tie-back to our measured numbers

TW close-auction share of T-day volume: ~25–30% measured (derived
daily − Σ intraday bars; 2330 = 24.8% on a normal day, event days
higher). MSCI-delete T-day volume 16x median / 38x max — most of it
into the close. These two numbers together are why the auction
footprint column (order ÷ expected auction volume) is the sheet's
capacity check, and why >30% footprint triggers the client
conversation ("you ARE the auction").

*Sources: SEBI CAS reform coverage (tradebrains.in, sahi.com,
anandrathi.com, Aug-2026 implementation); IDX pre-closing mechanics
(jakartaglobe.id, kontan.co.id, realtrading.com); SET random close
16:30–16:40 (tradinghours.com); TWSE/JPX/HKEX/KRX/SSE mechanics from
the exchange rulebooks as encoded in pt_dealer.AUCTION_CUTOFFS.*
