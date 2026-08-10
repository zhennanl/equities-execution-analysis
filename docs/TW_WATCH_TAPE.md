# The tape for the August-2026 Taiwan calls

Built 2026-08-10T09:35:47.

## Coverage

- vintage price cache to **2026-07-31**
- turnover (TWSE+TPEx) to **20260807**
- T86 foreign net to **20260805**
- live refresh: **NOT RUN — prices below are stale**

## Per name

### 2344 Winbond Electronics Corporation (TWSE)

- last close **130.0** on 2026-07-31
- 20d -29.2%, 30d -34.7%, -41.4% from the 30d high
- 30d realised vol 92%
- ADV shares: 20d 124,821,967, 60d 212,599,104, 120d 201,370,333, 250d 204,894,607
- **ADV spread across horizons 1.70x** — the capacity ladder's answer moves by this much depending on which horizon it is struck on
- turnover ratio 0.97x its own median, **61%** of 1,933 codes trading that day
- foreign net 5d +69,684,964 sh (+0.56 days of 20d ADV)
- foreign net 20d -4,519,770 sh (-0.04 days of 20d ADV)
- foreign net 60d -114,750,152 sh (-0.92 days of 20d ADV)
- 8 block prints in 30 sessions, 15,894,851 sh (0.13 days of ADV)
- borrow balance 136,709,165, 20d change -58,979,009 (-0.47 days)

### 2408 Nanya Technology Corporation (TWSE)

- last close **360.5** on 2026-07-31
- 20d -11.4%, 30d -17.5%, -28.6% from the 30d high
- 30d realised vol 109%
- ADV shares: 20d 81,938,105, 60d 117,636,208, 120d 113,889,904, 250d 113,839,484
- **ADV spread across horizons 1.44x** — the capacity ladder's answer moves by this much depending on which horizon it is struck on
- turnover ratio 0.67x its own median, **45%** of 1,933 codes trading that day
- foreign net 5d +41,793,866 sh (+0.51 days of 20d ADV)
- foreign net 20d -25,115,508 sh (-0.31 days of 20d ADV)
- foreign net 60d +30,803,452 sh (+0.38 days of 20d ADV)
- 4 block prints in 30 sessions, 1,607,000 sh (0.02 days of ADV)
- borrow balance 89,670,645, 20d change +65,050,478 (+0.79 days)

### 8046 Nan Ya Printed Circuit Board Corporation (TWSE)

- last close **920.0** on 2026-07-31
- 20d -19.7%, 30d +4.0%, -35.0% from the 30d high
- 30d realised vol 114%
- ADV shares: 20d 18,080,087, 60d 18,119,921, 120d 17,306,746, 250d 19,128,076
- **ADV spread across horizons 1.11x** — the capacity ladder's answer moves by this much depending on which horizon it is struck on
- turnover ratio 0.24x its own median, **9%** of 1,933 codes trading that day
- foreign net 5d -839,650 sh (-0.05 days of 20d ADV)
- foreign net 20d -16,636,396 sh (-0.92 days of 20d ADV)
- foreign net 60d +10,070,544 sh (+0.56 days of 20d ADV)
- 2 block prints in 30 sessions, 2,900,000 sh (0.16 days of ADV)
- borrow balance 1,400,976, 20d change -32,752 (-0.00 days)

### 8299 Phison Electronics Corp. (TPEX)

- last close **1640.0** on 2026-07-31
- 20d -26.8%, 30d -29.6%, -36.4% from the 30d high
- 30d realised vol 75%
- ADV shares: 20d 4,782,135, 60d 6,837,640, 120d 7,885,817, 250d 6,770,164
- **ADV spread across horizons 1.65x** — the capacity ladder's answer moves by this much depending on which horizon it is struck on
- turnover ratio 1.06x its own median, **64%** of 1,933 codes trading that day

## What this cannot see

- **Broker-branch (券商分點) is not here.** TWSE serves per-branch, per-stock buy/sell only through bsr.twse.com.tw, which is CAPTCHA-gated and holds the most recent session only. There is no historical endpoint and no lawful automated route, so this is a vendor purchase or a manual daily capture, not a harvest.
- **Foreign net is a net**, and 8299 is TPEx-listed so T86 never carries it.
- **Traded value is missing before the refresh.** The vintage cache has close and volume only; value is left null rather than approximated as close x volume.
