# JP Step-1 Upgrade — from daily data already held

*Session 9i. 181 JP name-events (29 seasons, 2015-2025, yfinance daily from the decade harvest). No new data source required: prediction runs on dailies. J-Quants free tier documented as the official upgrade path; IB TSE (JPY 3,000/mo) gates INTRADAY only — deferred by choice.*

## Alias verification (survivorship stated)

|                               |   n |
|:------------------------------|----:|
| ('Buy', 'NO-MATERIAL-PRINT')  |   1 |
| ('Buy', 'PRINT-WEAK')         |   4 |
| ('Buy', 'VERIFIED')           |  53 |
| ('Sell', 'NO-MATERIAL-PRINT') |   8 |
| ('Sell', 'PRINT-WEAK')        |   2 |
| ('Sell', 'VERIFIED')          | 113 |

## JP class T-multiple priors (print-verified names)

```json
{
 "Buy": {
  "median": 7.7,
  "max": 21.3,
  "n": 53,
  "basis": "JP decade name-events, print-verified, daily yfinance"
 },
 "Sell": {
  "median": 10.0,
  "max": 24.5,
  "n": 113,
  "basis": "JP decade name-events, print-verified, daily yfinance"
 }
}
```

Wired into the Asia pack: the Japan section now shows JP-measured priors instead of silently reusing Taiwan's 16x (an honesty gap this closes).