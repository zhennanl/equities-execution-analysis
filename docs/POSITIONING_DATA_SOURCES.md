# Positioning Data for Index-Rebalance Names

*How to check who is already in a rebalance name, how brokers source it,
and what is publicly available. Session 6k. Implemented in
`agents/positioning.py` + Page 2 "Positioning check" expander.*

## 1. Three layers of positioning data

**Layer 1 — inference from price/volume (free, any market).**
No register anywhere discloses LONG pre-positioning, so the honest
estimator is the footprint: excess abnormal volume between announcement
and T-1 (in ADV-days) x an assumed event-driven participation share,
with CAR drift as direction confirmation. Implemented as
`positioning_footprint` — bounds the position, cannot name holders.

**Layer 2 — official disclosures (free, short side + investor types).**
- Japan: per-holder short positions >=0.2% published same-day (JPX);
  weekly trading by investor type (foreign/individual/prop net flows).
- Taiwan: DAILY margin purchase/short sale balances + SBL short balance
  per stock (TWSE open data); daily foreign ownership.
- Korea: net-short register (>=0.01% or KRW 1bn) + short-sale balances.
- Hong Kong: SFC weekly aggregated reportable short positions (Friday
  snapshot); HKEX daily short-selling turnover per stock.
- US: FINRA bi-monthly short interest (~T+9 lag); SEC Reg SHO
  fails-to-deliver; 13F quarterly (45-day lag — passive base only);
  daily ETF shares outstanding = creation/redemption flow.
- EU/UK: public net-short registers >=0.5%.

**Layer 3 — broker-only (not public, listed for honesty).**
Own client flow by segment, prime-brokerage securities-lending book
(borrow demand = short build, seen before public data), internal crossing
interest and IOIs, paid vendors (S&P Global Securities Finance for
borrow/loan, EPFR for fund flows), exchange member-level reports.
This is a real information advantage of large agency desks — the public
proxies approximate it with a lag.

## 2. Interview framing

"Longs have no register, so I estimate them from the tape — excess
ADV-days into the effective date with CAR confirmation. Shorts I read
from the official regimes, which in Asia are excellent: Taiwan gives me
margin and SBL balances DAILY, Japan publishes 0.2% positions same-day,
Korea has a register, HK is weekly. A broker adds what I can't see —
its own flow and the PB lending book. My platform implements layer 1
everywhere and layer 2 where a free API exists, with the source map for
the rest."

## 3. Sources

- [JPX — outstanding short selling positions](https://www.jpx.co.jp/english/markets/public/short-selling/01.html)
- [SFC — aggregated reportable short positions](https://www.sfc.hk/en/Regulatory-functions/Market/Short-position-reporting/Aggregated-reportable-short-positions-of-specified-shares)
- [FINRA — equity short interest](https://www.finra.org/finra-data/browse-catalog/equity-short-interest)
- [SFC — short position reporting rules](https://www.sfc.hk/en/Rules-and-standards/Short-position-reporting-rules)
- KRX/FSS net short register; TWSE open-data margin/SBL endpoints (see
  per-market table in `agents/positioning.py`).
