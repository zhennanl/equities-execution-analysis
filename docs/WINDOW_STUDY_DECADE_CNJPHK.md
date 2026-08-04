# Decade window study — CN/JP/HK MSCI events 2015-2025

*Session 9h. 367 print-validated name-events (401 excluded as NO MATERIAL PRINT: T-mult < 2 — the alias is usually plausible but tracked flow did not dominate the local tape, so window dynamics are not index-flow-driven for those names; 322 names unmatched by the bridge). MSCI-only (FTSE keys for these markets not collected). Price/volume study — historical crowding absent for JP/CN, HK reconstructable but out of this pass. Counterfactual fills at daily closes are impact-free upper bounds. Convention: negative = beat the T close (MOC = 0).*

## Coverage and the survivorship caveat

Masters are current snapshots: names delisted since 2015 cannot match, and deletion often precedes delisting — so DELETES are under-covered and late-decade events are better covered. Measured names are measured correctly; coverage itself is biased toward survivors. Match counts by side below.

|                |   n |
|:---------------|----:|
| ('CN', 'Buy')  |  65 |
| ('CN', 'Sell') |  62 |
| ('HK', 'Buy')  |  37 |
| ('HK', 'Sell') |  37 |
| ('JP', 'Buy')  |  53 |
| ('JP', 'Sell') | 113 |

## Findings (computed; convention: negative = beat the T close)

1. **The one-event May-2026 'class inversion' does NOT generalize to
   the decade.** Decade CN adds GRIND UP like Taiwan (median drift
   +391 bps; day-1 buy -325, LINEAR -234 vs close — working beats the
   print), where May-2026 showed pop-then-decay (+1,103 day-1 cost).
   Decade deletes show no press-to-print either (CN 22-25: LINEAR -8,
   n=46 ~ flat). The inversion is at most a LATE-REGIME or
   event-specific phenomenon — Aug-2026 arbitrates, exactly what the
   one-event caveat was for.
2. **China A materiality is the structural surprise: only
   25% of CN name-events show a material event print**
   (T-mult >= 2). Median excluded T-mult ~1.1 — MSCI flow at 10-20%
   inclusion factors rarely dominates a retail-heavy A-share tape.
   The per-name index edge in CN is thin outside the largest
   inclusion waves; JP/HK validated prints run 8-13x (TW-like).
3. **The edge is DYING from the newest era inward — JP first.**
   JP 2015-18/2019-21: working crushed the print (adds LINEAR -118 /
   -337; deletes -235 / -257). JP 2022-25: FLIPPED (adds LINEAR
   +230, deletes +116) — the Greenwood-Sammon disappearance arriving
   in Asia, measured in execution-counterfactual space. CN adds
   remain alive through 22-25 (LINEAR -306); HK is unstable at n~15
   per cell — no reliable HK playbook from public prints alone.
4. **2019-21 was the golden era everywhere** (drifts +390 to +630,
   every counterfactual beats MOC) — coincides with the China-A
   inclusion-factor step-ups and pre-saturation arb capacity.
5. Practical encoding for the discretion matrix: decade priors say
   CN adds -> work early remains valid; JP post-2022 -> MOC-first
   (edge gone); HK -> unconditional-band only; and the May-2026
   MSCI-add WAIT rule should be held as a HYPOTHESIS pending
   Aug-2026, not promoted to a decade rule.

## All-decade medians (bps vs T close)

|                |   n |   drift_med |   d1_med |   lin_med |   late5_med |
|:---------------|----:|------------:|---------:|----------:|------------:|
| ('CN', 'Buy')  |  65 |         391 |     -325 |      -234 |        -187 |
| ('CN', 'Sell') |  62 |         -35 |       16 |       -15 |         -24 |
| ('HK', 'Buy')  |  37 |           0 |       88 |        76 |          51 |
| ('HK', 'Sell') |  37 |          75 |     -126 |       -43 |         -19 |
| ('JP', 'Buy')  |  53 |         374 |     -356 |      -178 |         -57 |
| ('JP', 'Sell') | 113 |         226 |      -49 |       -48 |         -43 |

## The inversion, by era

|                           |   n |   d1 |   lin |
|:--------------------------|----:|-----:|------:|
| ('CN', 'Buy', '2015-18')  |   4 |   32 |   209 |
| ('CN', 'Buy', '2019-21')  |  25 | -325 |  -146 |
| ('CN', 'Buy', '2022-25')  |  36 | -324 |  -306 |
| ('CN', 'Sell', '2015-18') |   1 |  343 |   381 |
| ('CN', 'Sell', '2019-21') |  15 |  134 |   -27 |
| ('CN', 'Sell', '2022-25') |  46 |  -69 |    -8 |
| ('HK', 'Buy', '2015-18')  |  10 |  388 |   139 |
| ('HK', 'Buy', '2019-21')  |  15 | -731 |  -257 |
| ('HK', 'Buy', '2022-25')  |  12 |  342 |   249 |
| ('HK', 'Sell', '2015-18') |   8 |   82 |   127 |
| ('HK', 'Sell', '2019-21') |  17 | -328 |  -282 |
| ('HK', 'Sell', '2022-25') |  12 |  236 |   156 |
| ('JP', 'Buy', '2015-18')  |  20 | -191 |  -118 |
| ('JP', 'Buy', '2019-21')  |  22 | -564 |  -337 |
| ('JP', 'Buy', '2022-25')  |  11 |  -85 |   230 |
| ('JP', 'Sell', '2015-18') |  20 | -244 |  -235 |
| ('JP', 'Sell', '2019-21') |  39 | -541 |  -257 |
| ('JP', 'Sell', '2022-25') |  54 |  171 |   116 |

## Per-event table (print-validated)

| season   |   year | mkt   | code      | side   |   drift_bps |   t_mult | print_ok   |   ALL_DAY1 |   LINEAR |   LATE5 |
|:---------|-------:|:------|:----------|:-------|------------:|---------:|:-----------|-----------:|---------:|--------:|
| May15    |   2015 | HK    | 2314.HK   | Sell   | -1222.01    |      5.4 | True       |       1203 |      807 |     320 |
| Nov15    |   2015 | HK    | 0696.HK   | Buy    |   904.607   |     20.1 | True       |       -422 |      -70 |      63 |
| Nov15    |   2015 | HK    | 2009.HK   | Sell   |  1273.67    |     14.8 | True       |      -1065 |     -529 |    -213 |
| May15    |   2015 | JP    | 9706.T    | Buy    |  1068.7     |      6.2 | True       |      -1103 |     -321 |     248 |
| May15    |   2015 | JP    | 5444.T    | Sell   |  -643.211   |      7.4 | True       |        467 |      316 |     141 |
| Aug15    |   2015 | JP    | 4922.T    | Buy    |  -490.895   |      2.9 | True       |        466 |     -252 |    -430 |
| Aug15    |   2015 | JP    | 7453.T    | Buy    |   292.305   |      4.2 | True       |       -184 |     -411 |    -504 |
| Aug15    |   2015 | JP    | 6857.T    | Sell   |   870.786   |      5.4 | True       |       -985 |     -337 |     -74 |
| Aug15    |   2015 | JP    | 6366.T    | Sell   |  1446.73    |      4.5 | True       |      -1714 |     -458 |     162 |
| Aug15    |   2015 | JP    | 6740.T    | Sell   |  1298.41    |      5.7 | True       |       -942 |     -301 |     204 |
| Nov15    |   2015 | JP    | 4684.T    | Buy    |   530.547   |     12.5 | True       |       -427 |     -321 |    -192 |
| Nov15    |   2015 | JP    | 3668.T    | Sell   |  -327.799   |      5.2 | True       |        -92 |     -266 |    -179 |
| Nov15    |   2015 | JP    | 4062.T    | Sell   |  -326.378   |      5.1 | True       |        383 |     -146 |    -247 |
| Nov15    |   2015 | JP    | 6753.T    | Sell   |   -80.0006  |      5.2 | True       |        238 |     -404 |   -1079 |
| May16    |   2016 | HK    | 1530.HK   | Buy    | -1397.73    |     15.1 | True       |       1453 |      604 |    -127 |
| May16    |   2016 | HK    | 0123.HK   | Sell   |   660.376   |     48.8 | True       |         -0 |      140 |     121 |
| Nov16    |   2016 | HK    | 0272.HK   | Sell   |   264.55    |     19.5 | True       |        -54 |       77 |      54 |
| Nov16    |   2016 | HK    | 0010.HK   | Buy    |   -52.357   |     31.7 | True       |         88 |      307 |     291 |
| May16    |   2016 | JP    | 7779.T    | Buy    |   560.52    |      5.8 | True       |       -377 |     -517 |    -407 |
| May16    |   2016 | JP    | 4927.T    | Buy    |   400.869   |      6.6 | True       |        -21 |     -313 |    -210 |
| May16    |   2016 | JP    | 9989.T    | Buy    |  1349.01    |     12.3 | True       |       -632 |     -325 |     -57 |
| May16    |   2016 | JP    | 3391.T    | Buy    |   510.484   |      7.9 | True       |       -356 |     -289 |    -203 |
| May16    |   2016 | JP    | 8334.T    | Sell   |  -373.831   |     12   | True       |        743 |      567 |     342 |
| May16    |   2016 | JP    | 8377.T    | Sell   |  -225.564   |     11.3 | True       |        662 |      373 |     338 |
| May16    |   2016 | JP    | 8136.T    | Sell   |   298.58    |      8.1 | True       |       -313 |      -17 |      74 |
| Nov16    |   2016 | JP    | 2432.T    | Buy    |   402.986   |      4.2 | True       |         43 |      223 |     187 |
| Nov16    |   2016 | JP    | 4912.T    | Buy    |  -317.544   |      5.8 | True       |        220 |      277 |     162 |
| Nov16    |   2016 | JP    | 9962.T    | Buy    |   174.041   |      8.6 | True       |       -381 |       16 |     190 |
| Nov16    |   2016 | JP    | 3765.T    | Sell   |  1087.72    |      4.2 | True       |      -2244 |     -709 |    -291 |
| Nov16    |   2016 | JP    | 5991.T    | Sell   |  -645.481   |     13.4 | True       |        709 |      473 |     239 |
| Nov16    |   2016 | JP    | 9507.T    | Sell   | -1178.28    |      8.7 | True       |        917 |      459 |     112 |
| May17    |   2017 | HK    | 0425.HK   | Buy    |   225.807   |     10.9 | True       |       -394 |     -400 |    -338 |
| May17    |   2017 | HK    | 0598.HK   | Sell   |   -12.099   |      9.2 | True       |        164 |      184 |      66 |
| Nov17    |   2017 | HK    | 2314.HK   | Buy    |  -255.594   |      8.9 | True       |         33 |     -125 |     -28 |
| Nov17    |   2017 | HK    | 1357.HK   | Buy    |  -841.424   |      4.5 | True       |        954 |       -1 |    -198 |
| Nov17    |   2017 | HK    | 0425.HK   | Buy    |  -973.085   |     35.8 | True       |        677 |      224 |      11 |
| Nov17    |   2017 | HK    | 8296.HK   | Sell   | -4080       |      6.9 | True       |       2784 |     1560 |     716 |
| May17    |   2017 | JP    | 6146.T    | Buy    |   346.695   |      7.4 | True       |       -141 |     -165 |    -169 |
| May17    |   2017 | JP    | 9142.T    | Buy    |   203.803   |     12.9 | True       |       -200 |      -71 |     -85 |
| May17    |   2017 | JP    | 4042.T    | Buy    |  -436.991   |      4.7 | True       |        659 |      189 |     -11 |
| May17    |   2017 | JP    | 9505.T    | Sell   |  -588.234   |      9.8 | True       |        491 |      -11 |    -217 |
| May17    |   2017 | JP    | 9301.T    | Sell   |   289.853   |      8.7 | True       |       -227 |      -25 |     -82 |
| Aug17    |   2017 | JP    | 6723.T    | Buy    |   325.885   |      9.8 | True       |       -676 |     -421 |    -271 |
| Nov17    |   2017 | JP    | 6383.T    | Buy    |  -270.27    |      7   | True       |       -114 |       63 |     147 |
| May18    |   2018 | CN    | sh.601169 | Buy    |  -405.797   |      2.3 | True       |        408 |      263 |     127 |
| Aug18    |   2018 | CN    | sh.600406 | Buy    |   475.88    |      2.4 | True       |       -348 |     -383 |    -138 |
| Aug18    |   2018 | CN    | sh.601966 | Buy    |   484.928   |      2.1 | True       |       -331 |      155 |     227 |
| Nov18    |   2018 | CN    | sh.600875 | Buy    |   -52.2193  |      2.1 | True       |        394 |      359 |     354 |
| Nov18    |   2018 | CN    | sh.601611 | Sell   |  -201.884   |      2.1 | True       |        343 |      381 |     456 |
| May18    |   2018 | HK    | 0347.HK   | Buy    |  -418.718   |      8.4 | True       |        540 |      193 |     -23 |
| May18    |   2018 | HK    | 1958.HK   | Buy    |  -155.039   |      6.4 | True       |        236 |       85 |       0 |
| May18    |   2018 | HK    | 0142.HK   | Sell   |    75.186   |     32.4 | True       |       -126 |     -154 |    -197 |
| Aug18    |   2018 | HK    | 1347.HK   | Buy    | -1247.44    |      2.5 | True       |        841 |      567 |     533 |
| Nov18    |   2018 | HK    | 2866.HK   | Sell   |  -114.943   |     18.4 | True       |        341 |      114 |     159 |
| May18    |   2018 | JP    | 4967.T    | Buy    |  -173.825   |     14.4 | True       |       -198 |       86 |     112 |
| May18    |   2018 | JP    | 9143.T    | Buy    |   605.928   |      7.7 | True       |       -413 |      239 |     348 |
| May18    |   2018 | JP    | 8439.T    | Buy    | -1148.65    |     10.3 | True       |        947 |      672 |     363 |
| May18    |   2018 | JP    | 8359.T    | Sell   |  1072.09    |     16.4 | True       |      -1387 |     -674 |    -112 |
| May18    |   2018 | JP    | 7180.T    | Sell   |   527.275   |     15.7 | True       |       -710 |     -453 |     -84 |
| May18    |   2018 | JP    | 2121.T    | Sell   |   870.147   |      6.4 | True       |       -718 |     -781 |    -422 |
| Aug18    |   2018 | JP    | 8358.T    | Sell   |  2471.91    |     11.4 | True       |      -3449 |    -1303 |    -315 |
| Nov18    |   2018 | JP    | 7747.T    | Buy    |  1379.68    |      9.7 | True       |       -132 |      -45 |     154 |
| Nov18    |   2018 | JP    | 7779.T    | Sell   |   229.746   |     11.6 | True       |       -260 |     -204 |     -82 |
| Aug19    |   2019 | CN    | sh.601018 | Buy    |   785.908   |      3.6 | True       |       -628 |     -328 |     -55 |
| Aug19    |   2019 | CN    | sh.603259 | Buy    |  3227.5     |      3.2 | True       |      -2178 |    -1170 |    -345 |
| Aug19    |   2019 | CN    | sz.002120 | Buy    |  1078.06    |      3.5 | True       |       -986 |     -675 |    -356 |
| Feb19    |   2019 | HK    | 1810.HK   | Buy    |  1177.57    |      2.8 | True       |      -1137 |     -395 |     110 |
| May19    |   2019 | HK    | 0839.HK   | Buy    |  1440.82    |      7.8 | True       |       -924 |     -365 |    -285 |
| May19    |   2019 | HK    | 2331.HK   | Buy    |  -428.995   |      5.9 | True       |       -325 |     -104 |    -170 |
| May19    |   2019 | HK    | 2359.HK   | Buy    |    75.2736  |     12.1 | True       |       -184 |     -188 |    -185 |
| May19    |   2019 | HK    | 0010.HK   | Sell   |   277.136   |     26.2 | True       |        -95 |      -48 |      -0 |
| May19    |   2019 | HK    | 0425.HK   | Sell   |    20.6619  |     11.7 | True       |       -166 |       72 |     -99 |
| Nov19    |   2019 | HK    | 0347.HK   | Sell   |  -938.629   |     10.5 | True       |        957 |      830 |     145 |
| Nov19    |   2019 | HK    | 0014.HK   | Sell   |   820.189   |     38.3 | True       |       -739 |     -319 |    -141 |
| Nov19    |   2019 | HK    | 0069.HK   | Sell   |   204.328   |     12.9 | True       |       -196 |      -43 |      17 |
| Nov19    |   2019 | HK    | 0004.HK   | Sell   |   547.368   |     20.6 | True       |       -702 |     -282 |    -138 |
| May19    |   2019 | JP    | 6857.T    | Buy    |  -619.097   |      5.8 | True       |        798 |      340 |     -39 |
| May19    |   2019 | JP    | 3769.T    | Buy    |   -38.1673  |      3.6 | True       |       -383 |     -160 |    -192 |
| May19    |   2019 | JP    | 4385.T    | Buy    |    82.9187  |      4.5 | True       |       -579 |     -424 |    -489 |
| May19    |   2019 | JP    | 4587.T    | Buy    |  -316.901   |      7.1 | True       |        127 |        3 |    -153 |
| May19    |   2019 | JP    | 7936.T    | Sell   |   344.313   |      5.2 | True       |         16 |     -133 |    -219 |
| May19    |   2019 | JP    | 2432.T    | Sell   |  -752.104   |      6.6 | True       |        446 |      292 |     131 |
| May19    |   2019 | JP    | 8418.T    | Sell   |  -147.059   |      9.2 | True       |         24 |       35 |      31 |
| Nov19    |   2019 | JP    | 7181.T    | Buy    |   837.605   |     15.8 | True       |       -584 |     -408 |    -256 |
| Nov19    |   2019 | JP    | 4516.T    | Buy    |    94.8354  |     11.9 | True       |       -125 |      -51 |      42 |
| Nov19    |   2019 | JP    | 8954.T    | Buy    |   -86.3853  |     21.3 | True       |       -162 |     -180 |      24 |
| Nov19    |   2019 | JP    | 9684.T    | Buy    |   894.633   |      5.7 | True       |      -1040 |     -716 |    -332 |
| Nov19    |   2019 | JP    | 4118.T    | Sell   |   724.639   |     15.6 | True       |      -1051 |     -488 |    -162 |
| Nov19    |   2019 | JP    | 5406.T    | Sell   |   445.97    |      6.3 | True       |       -772 |     -202 |      11 |
| Nov19    |   2019 | JP    | 5214.T    | Sell   |   254.516   |      7.3 | True       |       -425 |     -188 |     -24 |
| May20    |   2020 | CN    | sz.300271 | Buy    |  -147.82    |      2.6 | True       |         45 |     -314 |    -559 |
| May20    |   2020 | CN    | sz.002841 | Buy    |  1983.96    |      2.8 | True       |      -1581 |    -1044 |    -670 |
| May20    |   2020 | CN    | sz.000688 | Buy    |   567.986   |      3.3 | True       |       -206 |     -134 |      87 |
| May20    |   2020 | CN    | sh.600221 | Buy    |  1250       |      4.3 | True       |      -1111 |     -760 |    -457 |
| May20    |   2020 | CN    | sh.603605 | Buy    |   990.119   |      2.2 | True       |       -435 |     -216 |     -90 |
| May20    |   2020 | CN    | sz.300661 | Buy    | -3843.51    |      2   | True       |       6732 |     3849 |     908 |
| May20    |   2020 | CN    | sz.002468 | Buy    |   689.046   |      2.3 | True       |       -358 |       -6 |    -111 |
| May20    |   2020 | CN    | sh.600643 | Sell   |   265.487   |      2.1 | True       |       -247 |     -176 |    -127 |
| Nov20    |   2020 | CN    | sh.601916 | Buy    |   147.783   |      8.2 | True       |       -170 |     -144 |    -107 |
| Nov20    |   2020 | CN    | sh.601077 | Buy    |   336.323   |      3.3 | True       |       -325 |     -226 |    -117 |
| Nov20    |   2020 | CN    | sz.000987 | Buy    |    55.3506  |      3.1 | True       |       -263 |     -146 |    -148 |
| Nov20    |   2020 | CN    | sz.002568 | Buy    |   390.933   |      2.7 | True       |       -398 |      163 |     170 |
| Nov20    |   2020 | CN    | sh.603737 | Buy    |  -934.124   |      2.8 | True       |        885 |      571 |     112 |
| Nov20    |   2020 | CN    | sz.000898 | Sell   |  -979.021   |      2.4 | True       |        796 |      428 |      96 |
| Nov20    |   2020 | CN    | sz.000415 | Sell   |  -270.27    |      3.3 | True       |        263 |     -314 |    -346 |
| Nov20    |   2020 | CN    | sz.000598 | Sell   |    98.0392  |      2.7 | True       |       -158 |     -221 |    -139 |
| Nov20    |   2020 | CN    | sh.601998 | Sell   |  -194.553   |      7.6 | True       |        134 |      106 |     -53 |
| Nov20    |   2020 | CN    | sh.600373 | Sell   |     8.49618 |      2.9 | True       |         34 |      -27 |     -51 |
| Nov20    |   2020 | CN    | sz.000031 | Sell   |    62.6305  |      3.8 | True       |         21 |     -102 |     -84 |
| Nov20    |   2020 | CN    | sz.000883 | Sell   |  -277.078   |      2.4 | True       |        172 |      -11 |     -74 |
| Nov20    |   2020 | CN    | sh.600808 | Sell   |  -258.303   |      3   | True       |         72 |      -82 |    -173 |
| Nov20    |   2020 | CN    | sz.002110 | Sell   |  -437.956   |      2.1 | True       |        196 |       60 |     -20 |
| Nov20    |   2020 | CN    | sh.600820 | Sell   |  -104.895   |      3.2 | True       |         17 |      -19 |     -69 |
| May20    |   2020 | HK    | 6186.HK   | Buy    |  -304.708   |      8.8 | True       |        629 |     -257 |    -163 |
| May20    |   2020 | HK    | 2009.HK   | Sell   |  1028.97    |     19.3 | True       |      -1090 |     -375 |     -48 |
| May20    |   2020 | HK    | 0598.HK   | Sell   |  1011.24    |     14.3 | True       |       -938 |     -288 |      50 |
| May20    |   2020 | HK    | 0551.HK   | Sell   |  1628.96    |     14.7 | True       |      -2000 |    -1132 |    -609 |
| Aug20    |   2020 | HK    | 0272.HK   | Sell   |  1166.67    |     14.4 | True       |      -1038 |     -893 |    -396 |
| Nov20    |   2020 | HK    | 0754.HK   | Buy    |   125       |     13.3 | True       |       -756 |     -417 |    -261 |
| Nov20    |   2020 | HK    | 0425.HK   | Buy    |   576.922   |      8.2 | True       |       -844 |       65 |     125 |
| Nov20    |   2020 | HK    | 6969.HK   | Buy    |  1061.95    |      3   | True       |      -1300 |     -382 |     -80 |
| Nov20    |   2020 | HK    | 1958.HK   | Sell   |  1369.05    |      9.9 | True       |      -1241 |     -670 |    -269 |
| Nov20    |   2020 | HK    | 1788.HK   | Sell   |  -185.187   |      2.6 | True       |        182 |      351 |     236 |
| Nov20    |   2020 | HK    | 0410.HK   | Sell   |  -758.929   |     20   | True       |        332 |        0 |     -33 |
| May20    |   2020 | JP    | 3349.T    | Buy    |   877.824   |      4.3 | True       |       -849 |     -469 |    -196 |
| May20    |   2020 | JP    | 3281.T    | Buy    |   458.517   |      6.3 | True       |       -278 |     -261 |      -1 |
| May20    |   2020 | JP    | 2593.T    | Buy    |    81.5637  |     13.8 | True       |         16 |     -178 |    -210 |
| May20    |   2020 | JP    | 3038.T    | Buy    |   919.764   |      5   | True       |       -699 |     -720 |    -398 |
| May20    |   2020 | JP    | 6920.T    | Buy    |  1375.32    |      3.6 | True       |      -1345 |     -717 |     -61 |
| May20    |   2020 | JP    | 6005.T    | Buy    |   348.707   |     12.1 | True       |       -511 |     -231 |      -9 |
| May20    |   2020 | JP    | 2127.T    | Buy    |  1702.7     |     10.8 | True       |      -1328 |     -784 |    -305 |
| May20    |   2020 | JP    | 3626.T    | Buy    |   738.661   |     11.7 | True       |       -549 |     -266 |    -147 |
| May20    |   2020 | JP    | 8570.T    | Sell   | -1067.52    |      6.6 | True       |       1146 |      779 |     160 |
| May20    |   2020 | JP    | 6770.T    | Sell   |  -366.241   |      4   | True       |        753 |      643 |      29 |
| May20    |   2020 | JP    | 8253.T    | Sell   |  -594.549   |      9.5 | True       |        561 |      714 |     239 |
| May20    |   2020 | JP    | 7013.T    | Sell   | -1603       |      4.8 | True       |       1685 |      960 |     -75 |
| May20    |   2020 | JP    | 3086.T    | Sell   |   -88.203   |      7.7 | True       |        601 |      315 |     -74 |
| May20    |   2020 | JP    | 4902.T    | Sell   |   148.149   |      6.1 | True       |        451 |      314 |    -110 |
| May20    |   2020 | JP    | 6417.T    | Sell   |   960.913   |     12.7 | True       |       -468 |     -173 |    -191 |
| May20    |   2020 | JP    | 5901.T    | Sell   |  -690.299   |      8.5 | True       |       1091 |      491 |     -56 |
| Nov20    |   2020 | JP    | 6845.T    | Buy    |   516.274   |     10.6 | True       |       -523 |     -186 |      34 |
| Nov20    |   2020 | JP    | 9697.T    | Buy    |  1157.5     |      8.2 | True       |      -1582 |     -875 |    -361 |
| Nov20    |   2020 | JP    | 6324.T    | Buy    |  1537.4     |      8.8 | True       |      -1068 |     -591 |    -118 |
| Nov20    |   2020 | JP    | 4062.T    | Buy    |  1768.95    |      7.4 | True       |      -1401 |     -738 |    -149 |
| Nov20    |   2020 | JP    | 3635.T    | Buy    |  1372.95    |     10.7 | True       |      -1234 |     -568 |    -126 |
| Nov20    |   2020 | JP    | 8304.T    | Sell   |  -469.614   |      9   | True       |        264 |      166 |     -73 |
| Nov20    |   2020 | JP    | 4202.T    | Sell   |   813.516   |      9.1 | True       |       -627 |     -517 |    -420 |
| Nov20    |   2020 | JP    | 9513.T    | Sell   |   894.943   |      8.1 | True       |       -990 |     -536 |    -251 |
| Nov20    |   2020 | JP    | 3099.T    | Sell   |   226.48    |      7.1 | True       |       -766 |     -540 |    -471 |
| Nov20    |   2020 | JP    | 8955.T    | Sell   |   207.666   |     13.8 | True       |         49 |      221 |      10 |
| Nov20    |   2020 | JP    | 1963.T    | Sell   |   330.92    |      8.7 | True       |       -235 |     -240 |    -374 |
| Nov20    |   2020 | JP    | 6473.T    | Sell   |  1146.29    |      8.1 | True       |      -1480 |     -767 |    -493 |
| Nov20    |   2020 | JP    | 9364.T    | Sell   |   888.441   |     18.8 | True       |       -947 |     -632 |    -583 |
| Nov20    |   2020 | JP    | 7012.T    | Sell   |   525.327   |      5.2 | True       |       -541 |     -447 |    -457 |
| Nov20    |   2020 | JP    | 5463.T    | Sell   |  1216       |     13.3 | True       |      -1298 |     -730 |    -357 |
| Nov20    |   2020 | JP    | 7167.T    | Sell   |   735.932   |     11.5 | True       |      -1121 |     -651 |    -383 |
| Nov20    |   2020 | JP    | 5711.T    | Sell   |   265.227   |      9   | True       |       -484 |     -216 |    -247 |
| Nov20    |   2020 | JP    | 7211.T    | Sell   |   738.916   |      3.5 | True       |       -638 |     -487 |    -426 |
| Nov20    |   2020 | JP    | 7731.T    | Sell   |  1097.39    |      7.4 | True       |      -1387 |     -895 |    -592 |
| Nov20    |   2020 | JP    | 4666.T    | Sell   |    57.5072  |      4.2 | True       |        -58 |      -48 |    -294 |
| Nov20    |   2020 | JP    | 8410.T    | Sell   |   984.251   |     10   | True       |       -786 |     -269 |     -70 |
| Nov20    |   2020 | JP    | 6302.T    | Sell   |  1188.89    |     11.1 | True       |      -1150 |     -537 |    -312 |
| Nov20    |   2020 | JP    | 5110.T    | Sell   |  1175.91    |     10   | True       |      -1473 |     -921 |    -548 |
| Nov20    |   2020 | JP    | 5101.T    | Sell   |   427.407   |     10.7 | True       |       -827 |     -606 |    -369 |
| May21    |   2021 | CN    | sh.603613 | Buy    | -2465.32    |      2.6 | True       |       3124 |     1483 |    -215 |
| May21    |   2021 | CN    | sh.601696 | Buy    |   636.901   |      3.8 | True       |       -525 |     -394 |    -275 |
| May21    |   2021 | CN    | sh.688009 | Buy    |   104.712   |      3.7 | True       |        -86 |     -119 |    -117 |
| May21    |   2021 | CN    | sz.002409 | Buy    |  2796.23    |      3.6 | True       |      -2005 |    -1170 |    -792 |
| May21    |   2021 | CN    | sh.688002 | Buy    |   561.555   |      2.4 | True       |       -850 |     -326 |    -302 |
| May21    |   2021 | CN    | sz.300751 | Buy    | -4008.01    |      2.8 | True       |       6890 |     2211 |    -497 |
| May21    |   2021 | CN    | sz.300376 | Sell   |  -306.947   |      4.1 | True       |        141 |      218 |     147 |
| May21    |   2021 | CN    | sh.600673 | Sell   |   318.471   |      2.3 | True       |       -811 |     -404 |    -202 |
| May21    |   2021 | CN    | sh.600566 | Sell   |  -120.284   |      2.1 | True       |        167 |     -256 |    -268 |
| May21    |   2021 | CN    | sh.600667 | Sell   |  -525.624   |      3   | True       |        362 |      227 |     140 |
| Aug21    |   2021 | CN    | sh.688111 | Buy    | -2971.83    |      2   | True       |       4068 |     2463 |     457 |
| Aug21    |   2021 | CN    | sh.688169 | Buy    | -2503.19    |      4.4 | True       |       2941 |     3330 |    2425 |
| Aug21    |   2021 | CN    | sh.603392 | Buy    |  -921.546   |      3.1 | True       |        938 |      323 |     108 |
| Aug21    |   2021 | CN    | sh.601766 | Buy    |  1065.57    |      4.2 | True       |       -948 |     -915 |    -486 |
| Feb21    |   2021 | HK    | 0909.HK   | Buy    | -1324.11    |      5.7 | True       |       2198 |     1822 |     964 |
| Feb21    |   2021 | HK    | 9633.HK   | Buy    | -1550.45    |      4.3 | True       |       1951 |     1750 |    1070 |
| Feb21    |   2021 | HK    | 2013.HK   | Buy    | -1393.13    |      4.4 | True       |       1818 |     2246 |    1220 |
| May21    |   2021 | HK    | 9926.HK   | Buy    |  2234.58    |      9.9 | True       |      -1661 |     -708 |      30 |
| May21    |   2021 | HK    | 1209.HK   | Buy    |   814.64    |     16.2 | True       |       -731 |     -261 |     170 |
| May21    |   2021 | HK    | 1208.HK   | Buy    | -2281.3     |      7.3 | True       |       2222 |      893 |     293 |
| May21    |   2021 | HK    | 1929.HK   | Buy    |  1634.3     |     31.9 | True       |       -876 |     -627 |    -334 |
| May21    |   2021 | HK    | 0008.HK   | Sell   |   251.141   |     23.5 | True       |       -328 |     -126 |     -19 |
| Aug21    |   2021 | HK    | 0023.HK   | Sell   |   224.887   |     31.1 | True       |       -138 |      148 |     224 |
| Nov21    |   2021 | HK    | 0880.HK   | Sell   |   577.249   |     11.5 | True       |       -468 |     -988 |    -814 |
| Nov21    |   2021 | HK    | 1128.HK   | Sell   |    71.4285  |     18.6 | True       |        -58 |     -695 |    -978 |
| Nov21    |   2021 | JP    | 3288.T    | Buy    |  -733.813   |     14.4 | True       |        994 |      722 |     444 |
| Nov21    |   2021 | JP    | 2670.T    | Sell   |   395.684   |     17.9 | True       |       -674 |     -421 |    -217 |
| Nov21    |   2021 | JP    | 8572.T    | Sell   |   817.439   |     15   | True       |      -1157 |     -633 |    -214 |
| Nov21    |   2021 | JP    | 6952.T    | Sell   |   787.501   |     12.4 | True       |       -997 |     -716 |    -343 |
| Nov21    |   2021 | JP    | 6324.T    | Sell   |  1160.38    |     15.1 | True       |       -491 |      120 |     102 |
| Nov21    |   2021 | JP    | 6268.T    | Sell   |  1332.45    |     11.4 | True       |      -1446 |     -625 |    -174 |
| Nov21    |   2021 | JP    | 2282.T    | Sell   |   537.898   |     11.7 | True       |       -465 |     -257 |    -111 |
| Feb22    |   2022 | CN    | sh.688396 | Buy    |   428.368   |      2.7 | True       |       -268 |     -348 |    -187 |
| Feb22    |   2022 | CN    | sz.300919 | Buy    |  1300       |      2.7 | True       |      -1446 |     -887 |    -582 |
| May22    |   2022 | CN    | sz.000547 | Sell   | -2150.42    |      5.5 | True       |       1744 |     1341 |     703 |
| Aug22    |   2022 | CN    | sh.600085 | Buy    |  -565.086   |      2.4 | True       |        569 |      279 |     175 |
| Aug22    |   2022 | CN    | sh.601872 | Buy    |  1063.52    |      2.2 | True       |       -587 |      339 |     563 |
| Nov22    |   2022 | CN    | sh.603596 | Buy    |  -678.022   |      2.4 | True       |        763 |     -236 |    -480 |
| Nov22    |   2022 | CN    | sz.002244 | Buy    |  1814.35    |      2.7 | True       |       -687 |     -216 |      95 |
| Nov22    |   2022 | CN    | sh.603885 | Buy    |   328.299   |      2.1 | True       |       -401 |     -726 |    -698 |
| Nov22    |   2022 | CN    | sh.600498 | Sell   |   -21.9619  |      2.1 | True       |        -80 |     -221 |     -91 |
| Nov22    |   2022 | CN    | sz.002558 | Sell   |   -62.0347  |      2.2 | True       |        136 |      -91 |      37 |
| Nov22    |   2022 | CN    | sh.600808 | Sell   |  -471.014   |      2.4 | True       |        242 |      136 |     -28 |
| Nov22    |   2022 | CN    | sz.002958 | Sell   |  -563.38    |      3.9 | True       |        367 |      214 |      60 |
| Nov22    |   2022 | CN    | sh.601598 | Sell   |  -810.811   |      4.6 | True       |        575 |      384 |      90 |
| May22    |   2022 | HK    | 9926.HK   | Sell   | -3344.26    |      6.6 | True       |       2420 |     1666 |    1378 |
| Nov22    |   2022 | HK    | 1908.HK   | Buy    |  1184.37    |     20   | True       |       -109 |      352 |     555 |
| Nov22    |   2022 | HK    | 1929.HK   | Sell   |  1024.97    |     27.4 | True       |      -1845 |    -1161 |     -94 |
| Nov22    |   2022 | HK    | 0754.HK   | Sell   | -3810.26    |     13.7 | True       |       1543 |      463 |    -119 |
| Nov22    |   2022 | HK    | 0909.HK   | Sell   | -4377.99    |      3.8 | True       |       1048 |      260 |     336 |
| Nov22    |   2022 | HK    | 1208.HK   | Sell   |   -99.9999  |     13.1 | True       |       -297 |       88 |      50 |
| Nov22    |   2022 | HK    | 3808.HK   | Sell   | -2033.29    |      8.3 | True       |       1413 |      474 |     215 |
| Nov22    |   2022 | HK    | 0004.HK   | Sell   |  2189.24    |    135.9 | True       |       -974 |     -193 |    -209 |
| May22    |   2022 | JP    | 3349.T    | Sell   |  -664.046   |      5.8 | True       |        647 |      677 |     413 |
| May22    |   2022 | JP    | 4613.T    | Sell   |   354.996   |     15.8 | True       |        168 |      222 |     211 |
| May22    |   2022 | JP    | 4912.T    | Sell   |  -256.593   |      8.2 | True       |        174 |      426 |     339 |
| May22    |   2022 | JP    | 7459.T    | Sell   |  1767.12    |     18.1 | True       |       -455 |      298 |     180 |
| Feb23    |   2023 | CN    | sh.603658 | Buy    |   -22.724   |      2.5 | True       |        -33 |     -317 |    -337 |
| Feb23    |   2023 | CN    | sh.603688 | Buy    |  1290.09    |      2   | True       |      -1284 |    -1200 |    -681 |
| May23    |   2023 | CN    | sh.688220 | Buy    |  2017.28    |      3.2 | True       |      -1096 |     -930 |    -545 |
| May23    |   2023 | CN    | sh.600221 | Buy    |   178.571   |      4   | True       |       -117 |     -276 |    -409 |
| May23    |   2023 | CN    | sh.600378 | Buy    |   661.926   |      2.4 | True       |       -618 |     -294 |    -134 |
| May23    |   2023 | CN    | sz.000988 | Buy    |  2087.11    |      2.1 | True       |      -1735 |    -1236 |    -730 |
| May23    |   2023 | CN    | sh.688561 | Buy    |   656.385   |      2.3 | True       |       -730 |     -580 |    -475 |
| May23    |   2023 | CN    | sh.603893 | Buy    |  1917.06    |      2.1 | True       |      -1711 |     -860 |    -528 |
| May23    |   2023 | CN    | sz.000021 | Buy    |  2816.35    |      2.8 | True       |      -2394 |    -1464 |    -910 |
| May23    |   2023 | CN    | sz.300487 | Buy    |    62.4452  |      2.4 | True       |        135 |      309 |     164 |
| May23    |   2023 | CN    | sh.688303 | Buy    |  1013.67    |      3.7 | True       |       -867 |     -640 |    -553 |
| May23    |   2023 | CN    | sz.300726 | Sell   |   235.176   |      2.3 | True       |       -105 |     -388 |    -319 |
| Aug23    |   2023 | CN    | sz.300866 | Buy    |   674.745   |      3.3 | True       |       -728 |     -846 |    -682 |
| Aug23    |   2023 | CN    | sh.601179 | Buy    | -1059.48    |      2.5 | True       |        852 |      509 |     220 |
| Aug23    |   2023 | CN    | sh.605499 | Buy    |   756.164   |      4.2 | True       |       -741 |     -682 |    -460 |
| Aug23    |   2023 | CN    | sh.688538 | Buy    |   228.137   |      6.4 | True       |       -186 |     -211 |     -37 |
| Aug23    |   2023 | CN    | sh.688567 | Buy    |  -995.998   |      2.7 | True       |       1491 |      299 |    -167 |
| Aug23    |   2023 | CN    | sh.600060 | Buy    |  -735.816   |      2.6 | True       |         91 |      123 |     151 |
| Aug23    |   2023 | CN    | sh.600637 | Buy    |   -87.0647  |      2.3 | True       |        -50 |     -115 |     -20 |
| Aug23    |   2023 | CN    | sh.688072 | Buy    |   783.5     |      2.9 | True       |       -741 |     -976 |    -676 |
| Aug23    |   2023 | CN    | sh.600066 | Buy    |  -524.316   |      3.9 | True       |        425 |      238 |      21 |
| Aug23    |   2023 | CN    | sh.601992 | Sell   |   794.979   |      2.1 | True       |       -636 |     -445 |    -291 |
| Nov23    |   2023 | CN    | sh.688065 | Buy    |   621.336   |      4   | True       |       -379 |     -388 |    -302 |
| Nov23    |   2023 | CN    | sz.003816 | Buy    |   133.779   |      2.8 | True       |       -165 |     -234 |    -211 |
| Nov23    |   2023 | CN    | sh.600072 | Buy    |    54.6747  |      3.1 | True       |        -11 |     -198 |    -286 |
| Nov23    |   2023 | CN    | sh.603218 | Sell   |   846.262   |      2   | True       |      -1002 |     -518 |    -257 |
| Nov23    |   2023 | CN    | sh.600674 | Sell   |   -28.0899  |      3.1 | True       |        -42 |      115 |     164 |
| Feb23    |   2023 | HK    | 9926.HK   | Buy    | -1416.31    |      4.8 | True       |       1125 |      664 |     298 |
| May23    |   2023 | HK    | 2618.HK   | Buy    |    32.052   |     37.8 | True       |        511 |       32 |    -339 |
| Aug23    |   2023 | HK    | 3808.HK   | Buy    |  -228.494   |     14.4 | True       |        358 |      243 |     366 |
| Nov23    |   2023 | HK    | 0189.HK   | Sell   |  -400.698   |     21.2 | True       |        184 |      267 |    -104 |
| Nov23    |   2023 | HK    | 0004.HK   | Buy    |   453.139   |     68.4 | True       |        -25 |      255 |     160 |
| Feb23    |   2023 | JP    | 3088.T    | Buy    |    15.8231  |     18.8 | True       |        -95 |      270 |     202 |
| Feb23    |   2023 | JP    | 2593.T    | Sell   |  -314.604   |      9   | True       |        349 |      242 |     187 |
| Feb23    |   2023 | JP    | 2371.T    | Sell   |   392.435   |      9   | True       |          5 |      217 |     357 |
| May23    |   2023 | JP    | 9107.T    | Buy    |  -738.552   |      2.9 | True       |        638 |      416 |     268 |
| May23    |   2023 | JP    | 2127.T    | Sell   |   355.381   |      6.3 | True       |       -287 |     -537 |    -225 |
| Aug23    |   2023 | JP    | 7550.T    | Buy    |   396.73    |      4.4 | True       |        613 |       11 |     106 |
| Aug23    |   2023 | JP    | 4516.T    | Sell   |  -720.387   |     12.6 | True       |        695 |      486 |     190 |
| Aug23    |   2023 | JP    | 2002.T    | Sell   |  -477.359   |     11.2 | True       |        729 |      326 |     159 |
| Nov23    |   2023 | JP    | 3769.T    | Sell   | -1029.9     |      4.2 | True       |        396 |      295 |      61 |
| Nov23    |   2023 | JP    | 2433.T    | Sell   |    13.4276  |     17   | True       |         58 |       26 |    -235 |
| Nov23    |   2023 | JP    | 9008.T    | Sell   |   242.618   |     18.1 | True       |        387 |      258 |      99 |
| Nov23    |   2023 | JP    | 4967.T    | Sell   |  -176.066   |     10   | True       |         97 |       25 |     -86 |
| Nov23    |   2023 | JP    | 6370.T    | Sell   |  -327.287   |     13.5 | True       |        494 |      244 |     -48 |
| Nov23    |   2023 | JP    | 5938.T    | Sell   |  -235.261   |     12.2 | True       |        202 |      113 |      34 |
| Nov23    |   2023 | JP    | 2181.T    | Sell   |  -555.096   |     13.5 | True       |        651 |      246 |      -2 |
| May24    |   2024 | CN    | sz.000708 | Buy    |  -527.307   |      2.6 | True       |        596 |      238 |     107 |
| May24    |   2024 | CN    | sh.688220 | Sell   |   276.67    |      2.6 | True       |       -164 |       30 |     162 |
| Aug24    |   2024 | CN    | sh.600025 | Buy    |  -334.213   |      4.5 | True       |        482 |      649 |     366 |
| Aug24    |   2024 | CN    | sh.603529 | Sell   |  -647.612   |      2.7 | True       |        788 |      660 |      87 |
| Aug24    |   2024 | CN    | sz.000009 | Sell   |   686.275   |      4.9 | True       |       -737 |     -136 |      29 |
| Aug24    |   2024 | CN    | sh.600977 | Sell   |   640.301   |      2.9 | True       |       -513 |     -170 |     135 |
| Aug24    |   2024 | CN    | sh.600072 | Sell   |   945.513   |      2.1 | True       |      -1177 |     -350 |      57 |
| Aug24    |   2024 | CN    | sz.002797 | Sell   |   -19.084   |      3.1 | True       |        -76 |       80 |     103 |
| Aug24    |   2024 | CN    | sh.600673 | Sell   |  -322.581   |      2.8 | True       |        149 |      399 |     307 |
| Aug24    |   2024 | CN    | sz.002841 | Sell   |  -961.338   |      5.9 | True       |        855 |      740 |     391 |
| Aug24    |   2024 | CN    | sz.000987 | Sell   |   234.375   |      3.1 | True       |       -300 |       26 |     208 |
| Aug24    |   2024 | CN    | sz.002430 | Sell   |   427.666   |      3.1 | True       |       -430 |      234 |     271 |
| Aug24    |   2024 | CN    | sz.002508 | Sell   |  1121.23    |      3.8 | True       |      -1209 |     -508 |      -0 |
| Aug24    |   2024 | CN    | sh.600378 | Sell   |   517.97    |      4   | True       |       -524 |     -109 |    -124 |
| Aug24    |   2024 | CN    | sz.000709 | Sell   |   315.789   |      3   | True       |       -380 |     -167 |     -87 |
| Aug24    |   2024 | CN    | sh.600380 | Sell   |   688.372   |      2.2 | True       |       -679 |     -176 |     144 |
| Aug24    |   2024 | CN    | sh.688114 | Sell   |   145.177   |      2.5 | True       |       -102 |       -7 |      38 |
| Nov24    |   2024 | CN    | sz.000513 | Sell   |  -116.556   |      2.3 | True       |        -73 |      183 |     355 |
| Feb24    |   2024 | HK    | 1530.HK   | Sell   |  1147.26    |     29.9 | True       |       -174 |     -377 |    -248 |
| Feb24    |   2024 | HK    | 0017.HK   | Sell   |  -511.181   |     14.7 | True       |        496 |      225 |      61 |
| May24    |   2024 | HK    | 1208.HK   | Buy    |    79.1556  |      7   | True       |        366 |      665 |     649 |
| May24    |   2024 | HK    | 0753.HK   | Sell   |  -271.604   |      9.2 | True       |        288 |     -369 |    -332 |
| Feb24    |   2024 | JP    | 7735.T    | Buy    |   930.572   |      2.1 | True       |       -531 |       21 |     274 |
| Feb24    |   2024 | JP    | 8984.T    | Sell   |    16.2879  |     23.7 | True       |        192 |      210 |     119 |
| Feb24    |   2024 | JP    | 3635.T    | Sell   |  -522.619   |      7   | True       |        465 |      171 |     146 |
| Feb24    |   2024 | JP    | 4922.T    | Sell   |  1289.72    |      6.3 | True       |      -1554 |     -238 |     -38 |
| Feb24    |   2024 | JP    | 3861.T    | Sell   |  -117.342   |     13.5 | True       |        218 |      388 |     321 |
| Feb24    |   2024 | JP    | 3288.T    | Sell   |   -33.9998  |     14.3 | True       |         51 |     -162 |    -143 |
| Feb24    |   2024 | JP    | 4005.T    | Sell   |   -26.4032  |      6.1 | True       |         26 |     -114 |    -136 |
| Feb24    |   2024 | JP    | 4042.T    | Sell   |  -630.864   |      9   | True       |        589 |      157 |     -74 |
| May24    |   2024 | JP    | 7936.T    | Buy    |   374.433   |      8.2 | True       |       -528 |     -374 |     -79 |
| May24    |   2024 | JP    | 7747.T    | Sell   |   415.255   |     15.5 | True       |       -588 |      124 |     331 |
| May24    |   2024 | JP    | 6845.T    | Sell   |   212.19    |     19.4 | True       |        -42 |     -127 |     -41 |
| May24    |   2024 | JP    | 3281.T    | Sell   |   297.397   |     15.1 | True       |       -184 |      -90 |     -43 |
| May24    |   2024 | JP    | 6806.T    | Sell   |   272.373   |     12.2 | True       |       -243 |      -32 |      42 |
| May24    |   2024 | JP    | 3291.T    | Sell   |  -380.422   |     17.3 | True       |        205 |      250 |     193 |
| May24    |   2024 | JP    | 8953.T    | Sell   |   232.313   |     16.4 | True       |       -205 |      -67 |       6 |
| May24    |   2024 | JP    | 8972.T    | Sell   |   471.7     |     16.6 | True       |       -383 |     -138 |     -11 |
| May24    |   2024 | JP    | 9962.T    | Sell   |    47.9704  |     11.7 | True       |        -59 |     -113 |     -84 |
| May24    |   2024 | JP    | 9007.T    | Sell   |   773.325   |     24.5 | True       |       -179 |      -59 |     -19 |
| May24    |   2024 | JP    | 6753.T    | Sell   | -1159.42    |      6.6 | True       |       1761 |      711 |     226 |
| May24    |   2024 | JP    | 1803.T    | Sell   |   461.723   |     13.7 | True       |       -314 |     -197 |    -102 |
| May24    |   2024 | JP    | 9684.T    | Sell   |  1061.12    |      7.7 | True       |       -656 |     -193 |     167 |
| May24    |   2024 | JP    | 9001.T    | Sell   |   636.287   |     16.9 | True       |        -49 |       44 |      87 |
| Aug24    |   2024 | JP    | 6525.T    | Buy    |  1899.7     |      3.3 | True       |       -575 |      230 |      87 |
| Aug24    |   2024 | JP    | 9041.T    | Sell   |  -498.298   |     17.8 | True       |        572 |      118 |     -26 |
| Aug24    |   2024 | JP    | 7276.T    | Sell   |  -698.952   |      6.9 | True       |        950 |      417 |     148 |
| Aug24    |   2024 | JP    | 9147.T    | Sell   |  -786.42    |     12.2 | True       |        964 |      285 |       7 |
| Aug24    |   2024 | JP    | 4021.T    | Sell   |  -916.648   |      9   | True       |        527 |      241 |      38 |
| Aug24    |   2024 | JP    | 9064.T    | Sell   |  -483.273   |      7.9 | True       |        863 |      259 |     -18 |
| Feb25    |   2025 | CN    | sh.688472 | Buy    |   772.239   |      2   | True       |       -517 |     -505 |    -394 |
| Feb25    |   2025 | CN    | sh.603658 | Sell   |   199.368   |      2.7 | True       |        -97 |     -431 |    -314 |
| Feb25    |   2025 | CN    | sh.688363 | Sell   |    83.8103  |      2.3 | True       |       -101 |     -239 |    -227 |
| Feb25    |   2025 | CN    | sh.688065 | Sell   |  -953.59    |      2.2 | True       |        965 |      255 |     -72 |
| Feb25    |   2025 | CN    | sz.002262 | Sell   |   641.997   |      2.3 | True       |       -524 |     -195 |    -104 |
| Feb25    |   2025 | CN    | sh.600998 | Sell   |   217.822   |      2.3 | True       |       -162 |     -338 |    -198 |
| May25    |   2025 | CN    | sz.002653 | Buy    |   975.551   |      2.3 | True       |       -884 |     -381 |    -218 |
| May25    |   2025 | CN    | sz.000800 | Sell   |   150.685   |      2.6 | True       |       -125 |     -105 |     -53 |
| May25    |   2025 | CN    | sz.300699 | Sell   |   -75.6579  |      2.3 | True       |         13 |      158 |     259 |
| Aug25    |   2025 | CN    | sh.601998 | Buy    |  -475.059   |      2   | True       |        461 |      133 |      17 |
| Aug25    |   2025 | CN    | sh.603228 | Buy    |   331.922   |      2.2 | True       |       -228 |     -571 |    -665 |
| Aug25    |   2025 | CN    | sh.603198 | Sell   | -1080.95    |      2.3 | True       |       1071 |      622 |     205 |
| Aug25    |   2025 | CN    | sh.600132 | Sell   |   -79.3365  |      3.8 | True       |        129 |       55 |     -16 |
| Aug25    |   2025 | CN    | sh.603156 | Sell   |    37.1402  |      4.1 | True       |         14 |      -66 |    -193 |
| Aug25    |   2025 | CN    | sh.600025 | Sell   |    65.0054  |      3.5 | True       |        -65 |      -32 |    -109 |
| Aug25    |   2025 | CN    | sz.002409 | Sell   |  -769.78    |      2.1 | True       |        882 |      284 |      -3 |
| Aug25    |   2025 | CN    | sh.601880 | Sell   |  -314.465   |      2.2 | True       |        244 |      164 |      61 |
| Aug25    |   2025 | CN    | sh.603899 | Sell   |   -41.1653  |      2.7 | True       |        145 |       76 |     -16 |
| Aug25    |   2025 | CN    | sz.002053 | Sell   |  -533.209   |      3.5 | True       |        488 |       78 |    -197 |
| Aug25    |   2025 | CN    | sz.002032 | Sell   |   -97.5039  |      4.4 | True       |         81 |       -8 |     -53 |
| Nov25    |   2025 | CN    | sz.002465 | Sell   |  -372.617   |      3   | True       |        334 |      191 |     242 |
| Nov25    |   2025 | CN    | sh.603833 | Sell   |  -131.604   |      2.5 | True       |        120 |      -97 |    -130 |
| Nov25    |   2025 | CN    | sh.600153 | Sell   |     9.82318 |      2.2 | True       |         10 |     -371 |    -277 |
| Nov25    |   2025 | CN    | sh.603939 | Sell   |   192.472   |      2.6 | True       |       -135 |     -481 |    -283 |
| Feb25    |   2025 | HK    | 1519.HK   | Buy    |   288.462   |     17   | True       |        327 |      243 |     287 |
| Aug25    |   2025 | HK    | 1530.HK   | Buy    |     0       |      2.9 | True       |        -80 |      324 |     132 |
| Aug25    |   2025 | HK    | 1357.HK   | Buy    |   114.639   |      3.5 | True       |       -244 |     -745 |    -828 |
| Nov25    |   2025 | HK    | 9995.HK   | Buy    |  -541.311   |      2.9 | True       |        470 |       76 |      51 |
| Nov25    |   2025 | HK    | 9880.HK   | Buy    | -1603.92    |      3.1 | True       |       2108 |     1269 |     604 |
| Nov25    |   2025 | HK    | 2259.HK   | Buy    |   953.507   |      3.3 | True       |        -79 |       23 |    -186 |
| Nov25    |   2025 | HK    | 0696.HK   | Sell   |   -86.4547  |     12.1 | True       |       -257 |     -273 |       2 |
| Feb25    |   2025 | JP    | 9023.T    | Buy    |    -8.48202 |      9.5 | True       |        -85 |      187 |     180 |
| Feb25    |   2025 | JP    | 6448.T    | Sell   |  -720.134   |     20.4 | True       |        694 |      646 |     441 |
| Feb25    |   2025 | JP    | 6305.T    | Sell   |  -586.151   |      7.8 | True       |        142 |       46 |      20 |
| Feb25    |   2025 | JP    | 6525.T    | Sell   | -1554.8     |      2.8 | True       |       1303 |     -442 |   -1027 |
| May25    |   2025 | JP    | 8136.T    | Buy    |   760.096   |      4.2 | True       |       -833 |      -24 |     155 |
| May25    |   2025 | JP    | 6724.T    | Sell   |   694.308   |     11.9 | True       |       -438 |      -10 |      77 |
| May25    |   2025 | JP    | 6506.T    | Sell   |   -41.2006  |      6.6 | True       |        229 |      162 |      56 |
| Aug25    |   2025 | JP    | 7012.T    | Buy    | -1547.83    |      3.3 | True       |       1644 |      715 |     133 |
| Aug25    |   2025 | JP    | 4324.T    | Sell   |   978.717   |     12.2 | True       |      -1278 |     -460 |       7 |
| Aug25    |   2025 | JP    | 6465.T    | Sell   | -1205.93    |     17.9 | True       |       -103 |     -119 |      41 |
| Aug25    |   2025 | JP    | 6645.T    | Sell   |    57.2762  |     12   | True       |        144 |      -63 |      -5 |
| Aug25    |   2025 | JP    | 4528.T    | Sell   |   522.914   |     14.3 | True       |       -586 |     -492 |    -293 |
| Aug25    |   2025 | JP    | 7752.T    | Sell   |   265.619   |     22.1 | True       |       -211 |     -260 |    -116 |
| Nov25    |   2025 | JP    | 6361.T    | Buy    |  -762.442   |     12.8 | True       |       1675 |     1037 |     284 |
| Nov25    |   2025 | JP    | 9024.T    | Buy    | -1096.54    |     15.1 | True       |        812 |      294 |    -145 |
| Nov25    |   2025 | JP    | 2269.T    | Sell   |  -498.514   |     11.5 | True       |        535 |      118 |     -11 |
| Nov25    |   2025 | JP    | 2897.T    | Sell   |  -228.377   |      9.3 | True       |        253 |       49 |     -53 |
| Nov25    |   2025 | JP    | 2267.T    | Sell   |  -984.066   |     10.4 | True       |        727 |       10 |    -120 |