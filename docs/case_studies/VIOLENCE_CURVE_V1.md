# Violence Curve v1 — A Null Result and a Better Hypothesis

*Session 8z. Factor 5 of the pitch (expected price path), fitted on
the 17 measured per-name auction points (CN-A May-29 closing calls,
TW Jun-18 TW50 prints). agents/violence_curve.py.*

## The null result, stated first

**Auction share does not predict print deviation: R² ≈ 0.00 on 17
points.** The naive model every desk sketches — bigger footprint,
bigger gap — fails on real data. Pinned by a regression test so new
data forces a conscious update.

## What survives

**The unconditional prior: event-name |gap| ≈ 125 ± 85 bps.** Until
n grows, that band — not a share-conditioned curve — is the honest
number a client budgets for the print's deviation from the last
continuous price.

## The better hypothesis the points support

| Cohort | Auction share | Gap |
|---|---|---|
| TW Jun adds — ALL CONSENSUS (short builds +67%..+116% verified pre-event) | 44-71% | **−16 to −192 bps: at or BELOW the last price** |
| CN May adds (crowding unmeasured) | 5-19% | **+194 to +239 bps** on three of five |
| CN May deletes | 4-37% | −144 to −229 bps (flow-signed), two exceptions |

The four most crowded prints in the sample were the LEAST violent in
the flow direction — pre-positioned supply sells into the add's
print. Sign and size follow POSITIONING, not footprint: the
discretion matrix's premise (crowded = pressure pre-spent), now with
print-level evidence on the TW side. The CN side's crowding was
unmeasured at vintage, so the link is SUPPORTED, not proven — every
archived event adds points, and the Sep-1 effective day (with live
crowding on every covered market) is the designed out-of-sample
test.

## Client translation

- Budget ±125 bps (band 40-210) for any event name's print.
- If our crowding read says CONSENSUS, expect the print NOT to pay
  you the flow direction — the move happened before T (measured:
  −4.3% front-run) and the auction may even invert.
- If UNPRICED, the +200 bps-class gap is still ahead — the
  operational case for the discretion envelope.
