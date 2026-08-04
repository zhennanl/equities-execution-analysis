# T-Day Forecast Cards — MSCI Aug-2026 QIR Taiwan shortlist (ann Aug-11/12, print Aug-31)
*Generated 2026-08-04. Cards exist for SHORTLIST candidates — names that MIGHT convert at announcement. Every number traces to the METHOD table; if a prior does not exist for a class, the card says so.*

## METHOD — how every metric is calculated

| metric | rule | source | basis |
|---|---|---|---|
| p_convert | shortlist probability: P(any change, decade base rate for this market x review type) x visible share (1 - BLIND_SHARE) x proximity softmax | msci_decade_stats.json + review_engine.shortlist_candidates | 44 quarters 2015-2025 |
| flow_if_converts_usd | cap x free-float x passive-ownership rate 5%-9% of float (lo-hi band). This is UNCONDITIONAL on p — the flow that prints IF the name converts | review_engine.PASSIVE_OWN_RATE | literature + May-2026 measured event class |
| flow_p_weighted_usd | p_convert x midpoint of flow_if_converts — the EXPECTED-VALUE flow for desk capacity planning only; never use for T-day sizing (the print is all-or-nothing) | derived | — |
| adv_days | flow_if_converts / ADV(USD); bucket: <1 MOC, 1-3 WORK+MOC, >3 MULTI-DAY | universe ADV + event_window bucket rule | Step-2 planner convention |
| print_multiple | median / max of measured T-day volume multiples for this provider x side; NO-PRIOR stated when the class has no measured events (never borrowed silently) | event_flow_study.json via pitch_pack.expected_t_multiples | 2026 measured events |
| expected_t_volume_usd | ADV x median print multiple (only when a measured prior exists) | derived | — |
| auction_share_pct | range and median of MEASURED per-name closing-auction shares on TW effective days (control name excluded) | auction_study_2026.json | Jun-18-2026 per-name measurements |
| auction_footprint_pct | mid flow_if_converts / (expected_t_volume x median EVENT-DAY auction share) — the fraction of the expected closing print the obligated flow represents. Values > 100%% are meaningful, not errors: the index flow IS most of the print on 16x days, and the print size and the flow co-adjust — read > 100%% as 'the flow cannot clear in one print at prior sizes' -> multi-day working or a larger-than-prior print | derived | — |
| gap_band_bps | mean +/- std of |official close vs last continuous price| on measured event names. SIGN IS NOT PREDICTED: the violence-curve share->gap regression is a pinned NULL (R2~0), and the 6919/2344 cases show the print direction is set by the CROWD'S EXIT, not the index flow's side | violence_curve.load_points | 17 measured event points |
| limit_context | baseline daily %% of the TW tape touching / locking the +/-10%% band, and the print-day multiple; rule of thumb from the case studies: PRINT-DAY locks favor the obligated flow (band caps the price in the passive side's favor) | tw_limits.json (limit_moves_tw) | 19 baseline + 4 print days, exact tick math |
| crowding | live short-balance read (build vs 30-session baseline) where a cache is supplied; 'no live read' otherwise — never fabricated | TWT93U/TPEx via event_data | daily official |
| playbook | discretion-matrix row for this side x crowding (illustrative envelope 20%) + the decade execution-cost table for the event class; MSCI-add WAIT rule is flagged as a demoted hypothesis where it applies | event_window.discretion_decision + TWAP_VWAP_MOC_STUDY | decade tables: 109 TW name-events |

## ADD 2324.TW — p=0.061 (cap $4.85B, ff 0.95)

- **p basis**: non-member 0.56x the add bar (needs +78%); P(any add at a TAIWAN QIR) = 46% decade-measured, x visible share 40%, x proximity weight 33%; CAUTION recent deletion — decade re-add-within-4 rate here is 0%
- **Flow if converts**: $229-413M (cap $4.8B x ff 0.95 x 5%-9% of float); p-weighted $19.6M (capacity planning only)
- **ADV-days**: 2.2-4.0 (ADV $102.2M) -> bucket **MULTI-DAY**
- **Print multiple**: NO MEASURED MSCI Buy TW events — stated, not borrowed. (FTSE-class Buy prints measured ~5x are a CROSS-CLASS reference only.)
- **Gap band**: |gap| 123 +/- 82 bps (n=17); direction NOT predicted (null pinned); the crowd's exit sets the print direction (6919/2344 exhibits)
- **Limit bands**: baseline 3.0% of tape touches limit-up daily (2.0% locks); print days ~5.5%; print-day locks historically FAVOR the obligated side
- **Crowding**: LOW (-70%/30obs)
- **Playbook**: PRE-POSITION up to 20% within envelope — uncrowded add (unpriced): the close will jump; the envelope exists to capture part of that move; evidence: crowding read 'LOW (-70%/30obs)' [illustrative 20% envelope]; class cost (TW MSCI adds (measured, 2025 events)): window-VWAP -280 bps vs close (n=7); NOTE MSCI-add WAIT rule is a demoted hypothesis (decade: adds grind up; Aug-2026 arbitrates)

## ADD 1504.TW — p=0.049 (cap $4.59B, ff 0.66)

- **p basis**: non-member 0.53x the add bar (needs +88%); P(any add at a TAIWAN QIR) = 46% decade-measured, x visible share 40%, x proximity weight 27%; CAUTION recent deletion — decade re-add-within-4 rate here is 0%
- **Flow if converts**: $150-271M (cap $4.6B x ff 0.66 x 5%-9% of float); p-weighted $10.3M (capacity planning only)
- **ADV-days**: 3.0-5.5 (ADV $49.5M) -> bucket **MULTI-DAY**
- **Print multiple**: NO MEASURED MSCI Buy TW events — stated, not borrowed. (FTSE-class Buy prints measured ~5x are a CROSS-CLASS reference only.)
- **Gap band**: |gap| 123 +/- 82 bps (n=17); direction NOT predicted (null pinned); the crowd's exit sets the print direction (6919/2344 exhibits)
- **Limit bands**: baseline 3.0% of tape touches limit-up daily (2.0% locks); print days ~5.5%; print-day locks historically FAVOR the obligated side
- **Crowding**: MED (+6%/8obs)
- **Playbook**: PRE-POSITION up to 10% (half envelope) — partial positioning seen: capture part of the jump, capped; evidence: crowding read 'MED (+6%/8obs)' [illustrative 20% envelope]; class cost (TW MSCI adds (measured, 2025 events)): window-VWAP -280 bps vs close (n=7); NOTE MSCI-add WAIT rule is a demoted hypothesis (decade: adds grind up; Aug-2026 arbitrates)

## ADD 2633.TW — p=0.036 (cap $4.27B, ff 0.37)

- **p basis**: non-member 0.50x the add bar (needs +102%); P(any add at a TAIWAN QIR) = 46% decade-measured, x visible share 40%, x proximity weight 20%; CAUTION recent deletion — decade re-add-within-4 rate here is 0%
- **Flow if converts**: $78-141M (cap $4.3B x ff 0.37 x 5%-9% of float); p-weighted $3.9M (capacity planning only)
- **ADV-days**: 7.6-13.7 (ADV $10.3M) -> bucket **MULTI-DAY**
- **Print multiple**: NO MEASURED MSCI Buy TW events — stated, not borrowed. (FTSE-class Buy prints measured ~5x are a CROSS-CLASS reference only.)
- **Gap band**: |gap| 123 +/- 82 bps (n=17); direction NOT predicted (null pinned); the crowd's exit sets the print direction (6919/2344 exhibits)
- **Limit bands**: baseline 3.0% of tape touches limit-up daily (2.0% locks); print days ~5.5%; print-day locks historically FAVOR the obligated side
- **Crowding**: LOW (-72%/30obs)
- **Playbook**: PRE-POSITION up to 20% within envelope — uncrowded add (unpriced): the close will jump; the envelope exists to capture part of that move; evidence: crowding read 'LOW (-72%/30obs)' [illustrative 20% envelope]; class cost (TW MSCI adds (measured, 2025 events)): window-VWAP -280 bps vs close (n=7); NOTE MSCI-add WAIT rule is a demoted hypothesis (decade: adds grind up; Aug-2026 arbitrates)

## ADD 1402.TW — p=0.036 (cap $4.26B, ff 0.7)

- **p basis**: non-member 0.50x the add bar (needs +102%); P(any add at a TAIWAN QIR) = 46% decade-measured, x visible share 40%, x proximity weight 20%; CAUTION recent deletion — decade re-add-within-4 rate here is 0%
- **Flow if converts**: $149-269M (cap $4.3B x ff 0.70 x 5%-9% of float); p-weighted $7.5M (capacity planning only)
- **ADV-days**: 4.6-8.3 (ADV $32.5M) -> bucket **MULTI-DAY**
- **Print multiple**: NO MEASURED MSCI Buy TW events — stated, not borrowed. (FTSE-class Buy prints measured ~5x are a CROSS-CLASS reference only.)
- **Gap band**: |gap| 123 +/- 82 bps (n=17); direction NOT predicted (null pinned); the crowd's exit sets the print direction (6919/2344 exhibits)
- **Limit bands**: baseline 3.0% of tape touches limit-up daily (2.0% locks); print days ~5.5%; print-day locks historically FAVOR the obligated side
- **Crowding**: LOW (-17%/8obs)
- **Playbook**: PRE-POSITION up to 20% within envelope — uncrowded add (unpriced): the close will jump; the envelope exists to capture part of that move; evidence: crowding read 'LOW (-17%/8obs)' [illustrative 20% envelope]; class cost (TW MSCI adds (measured, 2025 events)): window-VWAP -280 bps vs close (n=7); NOTE MSCI-add WAIT rule is a demoted hypothesis (decade: adds grind up; Aug-2026 arbitrates)

## ADD — BELOW-FLOOR (unobservable) (p=0.273)

blind-band mass: 13/21 of 2025-26 TW changes sat below the 16-name floor (Nov-25 re-grade vs May-26 grade) — no per-name card is computable for the unobservable band; this row exists so the probability mass stays visible.

## DELETE 1101.TW — p=0.149 (cap $5.25B, ff 0.86)

- **p basis**: member 2.19x the del floor (needs +119%); P(any delete at a TAIWAN QIR) = 50% decade-measured, x visible share 40%, x proximity weight 75%
- **Flow if converts**: $226-407M (cap $5.2B x ff 0.86 x 5%-9% of float); p-weighted $47.1M (capacity planning only)
- **ADV-days**: 9.8-17.6 (ADV $23.1M) -> bucket **MULTI-DAY**
- **Print multiple**: median 16.0x / max 38.1x (n=8; measured MSCI Sell events 2026) -> expected T volume ~$369M
- **Auction**: share prior med 60.0% (n=20, DIRECT IB auction bars, class MSCI/Sell); our footprint **142.9%** of the expected print (mid flow $316M / (ADV x 16.0x x 60.0% auction share; DIRECT IB auction bars, class MSCI/Sell n=20))
- **Gap band**: |gap| 123 +/- 82 bps (n=17); direction NOT predicted (null pinned); the crowd's exit sets the print direction (6919/2344 exhibits)
- **Limit bands**: baseline 3.0% of tape touches limit-up daily (2.0% locks); print days ~5.5%; print-day locks historically FAVOR the obligated side
- **Crowding**: HIGH (+32%/30obs)
- **Playbook**: WORK AHEAD up to 20% of order pre-close — crowded delete: street pre-sold, pressure part-spent, covering bounce enlarged — working ahead beats donating the close to the covering crowd; evidence: crowding read 'HIGH (+32%/30obs)' [illustrative 20% envelope]; class cost (TW MSCI deletes): window-VWAP +48 bps vs close (n=20)

## DELETE 2207.TW — p=0.022 (cap $8.5B, ff 0.51)

- **p basis**: member 3.55x the del floor (needs +255%); P(any delete at a TAIWAN QIR) = 50% decade-measured, x visible share 40%, x proximity weight 11%
- **Flow if converts**: $215-388M (cap $8.5B x ff 0.51 x 5%-9% of float); p-weighted $6.6M (capacity planning only)
- **ADV-days**: 17.7-31.8 (ADV $12.2M) -> bucket **MULTI-DAY**
- **Print multiple**: median 16.0x / max 38.1x (n=8; measured MSCI Sell events 2026) -> expected T volume ~$195M
- **Auction**: share prior med 60.0% (n=20, DIRECT IB auction bars, class MSCI/Sell); our footprint **257.8%** of the expected print (mid flow $301M / (ADV x 16.0x x 60.0% auction share; DIRECT IB auction bars, class MSCI/Sell n=20))
- **Gap band**: |gap| 123 +/- 82 bps (n=17); direction NOT predicted (null pinned); the crowd's exit sets the print direction (6919/2344 exhibits)
- **Limit bands**: baseline 3.0% of tape touches limit-up daily (2.0% locks); print days ~5.5%; print-day locks historically FAVOR the obligated side
- **Crowding**: LOW (-41%/30obs)
- **Playbook**: WAIT — MOC the full order — uncrowded/unknown delete: pressure arrives at the print; pre-trading a clean close adds impact and tracking for nothing; evidence: crowding read 'LOW (-41%/30obs)' [illustrative 20% envelope]; class cost (TW MSCI deletes): window-VWAP +48 bps vs close (n=20)

## DELETE 2002.TW — p=0.019 (cap $8.79B, ff 0.73)

- **p basis**: member 3.68x the del floor (needs +268%); P(any delete at a TAIWAN QIR) = 50% decade-measured, x visible share 40%, x proximity weight 9%
- **Flow if converts**: $319-574M (cap $8.8B x ff 0.73 x 5%-9% of float); p-weighted $8.5M (capacity planning only)
- **ADV-days**: 8.7-15.7 (ADV $36.6M) -> bucket **MULTI-DAY**
- **Print multiple**: median 16.0x / max 38.1x (n=8; measured MSCI Sell events 2026) -> expected T volume ~$586M
- **Auction**: share prior med 60.0% (n=20, DIRECT IB auction bars, class MSCI/Sell); our footprint **127.0%** of the expected print (mid flow $446M / (ADV x 16.0x x 60.0% auction share; DIRECT IB auction bars, class MSCI/Sell n=20))
- **Gap band**: |gap| 123 +/- 82 bps (n=17); direction NOT predicted (null pinned); the crowd's exit sets the print direction (6919/2344 exhibits)
- **Limit bands**: baseline 3.0% of tape touches limit-up daily (2.0% locks); print days ~5.5%; print-day locks historically FAVOR the obligated side
- **Crowding**: LOW (-33%/30obs); EXITING (-42% off peak)
- **Playbook**: WAIT — MOC the full order — uncrowded/unknown delete: pressure arrives at the print; pre-trading a clean close adds impact and tracking for nothing; evidence: crowding read 'LOW (-33%/30obs); EXITING (-42% off peak)' [illustrative 20% envelope]; class cost (TW MSCI deletes): window-VWAP +48 bps vs close (n=20)

## DELETE 1326.TW — p=0.01 (cap $10.36B, ff 0.56)

- **p basis**: member 4.33x the del floor (needs +333%); P(any delete at a TAIWAN QIR) = 50% decade-measured, x visible share 40%, x proximity weight 5%
- **Flow if converts**: $289-520M (cap $10.4B x ff 0.56 x 5%-9% of float); p-weighted $4.0M (capacity planning only)
- **ADV-days**: 3.3-5.9 (ADV $88.7M) -> bucket **MULTI-DAY**
- **Print multiple**: median 16.0x / max 38.1x (n=8; measured MSCI Sell events 2026) -> expected T volume ~$1419M
- **Auction**: share prior med 60.0% (n=20, DIRECT IB auction bars, class MSCI/Sell); our footprint **47.5%** of the expected print (mid flow $404M / (ADV x 16.0x x 60.0% auction share; DIRECT IB auction bars, class MSCI/Sell n=20))
- **Gap band**: |gap| 123 +/- 82 bps (n=17); direction NOT predicted (null pinned); the crowd's exit sets the print direction (6919/2344 exhibits)
- **Limit bands**: baseline 3.0% of tape touches limit-up daily (2.0% locks); print days ~5.5%; print-day locks historically FAVOR the obligated side
- **Crowding**: LOW (-41%/30obs)
- **Playbook**: WAIT — MOC the full order — uncrowded/unknown delete: pressure arrives at the print; pre-trading a clean close adds impact and tracking for nothing; evidence: crowding read 'LOW (-41%/30obs)' [illustrative 20% envelope]; class cost (TW MSCI deletes): window-VWAP +48 bps vs close (n=20)

## DELETE — BELOW-FLOOR (unobservable) (p=0.3)

blind-band mass: 13/21 of 2025-26 TW changes sat below the 16-name floor (Nov-25 re-grade vs May-26 grade) — no per-name card is computable for the unobservable band; this row exists so the probability mass stays visible.
