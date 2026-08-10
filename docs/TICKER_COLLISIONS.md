# TICKER COLLISIONS — securities sharing a ticker

Generated 2026-08-09 by `py scripts\ticker_collisions.py`.

The Review Database collapses roster rows on the
TICKER, because MSCI has spelled the same company
several ways over twenty years. That is right for a
rename and WRONG for two different issuers, so every
collision is listed here with what was done to it.

**25 colliding tickers. 23 merged, 2 kept separate.**

| Market | Ticker | MSCI spellings | Changes | Handling |
|---|---|---|---|---|
| China | `000596` | ANHUI GUJING A (HK-C) · ANHUI GUJING DISTILLER B | 3 | KEPT SEPARATE — ANHUI GUJING A and ANHUI GUJING DISTILLER B are different share classes (A 000596 / B 200596); the B row carries the A ticker. |
| China | `002081` | SUZHOU A (HK-C) · SUZHOU GOLD MAN A (HK-C) | 3 | merged; histories combined |
| China | `002797` | CAPITAL SECURIT A (HK-C) · FIRST CAPITAL A (HK-C) | 4 | merged; histories combined |
| China | `0552` | CHINA COMM SERVI H · CHINA COMMU SERVICES H | 2 | merged; histories combined |
| China | `0658` | CHINA HIGH SPEED TRANSMI · HIGH SPEED TRANSMI | 2 | merged; histories combined |
| China | `1157` | ZOOMLION HEAVY IND H · ZOOMLION HEAVY IND SCI H | 3 | merged; histories combined |
| China | `1772` | GANFENG LITHIUM CO H · GANFENG LITHIUM GROUP H | 3 | merged; histories combined |
| China | `2196` | SHANGHAI FOSUN PHARM H · SHANGHAI FOSUN PHARMA H | 2 | merged; histories combined |
| China | `601668` | CHINA STATE CON A (HK-C) · CHINA STATE CONSTRUCTION | 3 | merged; histories combined |
| China | `601818` | CHINA EVERBRIGHT · CHINA EVERBRIGHT A(HK-C) | 2 | merged; histories combined |
| China | `688009` | CHINA RAIL SIGNA A(HK-C) · CHINA RAILWAY SIGNAL COM | 4 | merged; histories combined |
| China | `688396` | CHINA RES MICRO A (HK-C) · CHINA RESOURCES A (HK-C) | 3 | merged; histories combined |
| India | `ENRIN` | SIEMENS ENERGY INDIA · SIEMENS INDIA | 4 | KEPT SEPARATE — SIEMENS INDIA and SIEMENS ENERGY INDIA are separate listed companies after the 2025 demerger — not a rename. The ticker is also wrong for both. |
| India | `IDFCFIRSTB` | IDFC BANK · IDFC FIRST BANK | 3 | merged; histories combined |
| Indonesia | `ICBP` | INDOFOOD CBP SUKSES · INDOFOOD CBP SUKSES MAK | 2 | merged; histories combined |
| Indonesia | `TBIG` | TOWER BERSAMA INFR · TOWER BERSAMA INFRA | 4 | merged; histories combined |
| Japan | `3288` | OPEN HOUSE · OPEN HOUSE GROUP CO | 2 | merged; histories combined |
| Japan | `8804` | TATEMONO CO · TOKYO TATEMONO CO | 3 | merged; histories combined |
| Korea | `001450` | HYUNDAI MARINE & FIRE · HYUNDAI MARINE & FIRE IN | 4 | merged; histories combined |
| Korea | `036460` | KOREA GAS CORP · KOREA GAS CORPORATION | 2 | merged; histories combined |
| Malaysia | `5249` | IOI PROPERTIES · IOI PROPERTIES GROUP | 2 | merged; histories combined |
| Singapore | `T82U` | SUNTEC REAL ESTATE INV · SUNTEC REIT | 3 | merged; histories combined |
| Taiwan | `2408` | NANYA TECHNOLOGY · NANYA TECHNOLOGY CORP | 4 | merged; histories combined |
| Thailand | `BEM` | BANGKOK EXPRESSWAY · BANGKOK EXPRESSWAY & MET | 2 | merged; histories combined |
| Thailand | `TTB-R` | TMB BANK · TMBTHANACHART BANK | 2 | merged; histories combined |

## Kept separate, and why

**India `ENRIN`** — SIEMENS INDIA and SIEMENS ENERGY INDIA are separate listed companies after the 2025 demerger — not a rename. The ticker is also wrong for both.

**China `000596`** — ANHUI GUJING A and ANHUI GUJING DISTILLER B are different share classes (A 000596 / B 200596); the B row carries the A ticker.

Both also point at a wrong ticker upstream — see
OPEN_ITEMS R9. The display is honest; the data is
still wrong.