# APAC rebalance-event daily OHLC — final coverage

*c-258 measured it; c-259 corrected three ticker defects and
re-cut the counts. This is the dataset the index rebalance
analysis will be built on.*

---

## What changed at c-259

**Three securities were pointed at the wrong listing.** Each
was proved before it was touched, and each correction is
recorded with its reason in `data/ticker_corrections.json`.

| security | was | now | how it was proved |
|---|---|---|---|
| China MEITU | `3690.HK` | `1357.HK` | 3690 is **Meituan**; Meitu Inc is 1357. Two of six windows failed only because Meituan had not listed in 2017. |
| China ANHUI GUJING DISTILLER **B** | `000596.SZ` | `200596.SZ` | Internally: the same code was also mapped to *ANHUI GUJING A (HK-C)*, and two securities cannot share one code. |
| Australia BANK OF QUEENSLAND | `BOQPG.AX` | `BOQ.AX` | BOQPG is a preference/capital-notes line; MSCI deleted the ordinary share. |

**Five of those windows held real prices for the wrong
company — 353 daily bars.** They looked healthy. They have
been removed by `scripts/window_orphans.py` and will re-fetch
against the corrected codes.

**On BOQPG specifically:** the instruction was to drop the row
because a preference line does not belong in an equity
rebalance study. That is right about the instrument and wrong
about the row — the event is a deletion of the ORDINARY line,
and the map simply pointed at the wrong listing. Dropping it
would have discarded a real index event to hide a ticker bug,
so it is repointed instead.

**A side-effect worth knowing.** Rebuilding the changes
database also picked up **19 tickers that a previous session
had already resolved but never propagated** — Japan +17,
Australia +2. Those are 19 real windows that have never been
fetched, which is why `missing` rose rather than fell.

---

## Coverage after the re-run (final)

China, Japan and Australia were re-harvested against the
corrected tickers.

| market | expected | extracted | missing | % |
|---|---:|---:|---:|---:|
| China | 1,253 | 1,241 | 12 | 99.0% |
| Japan | 219 | 219 | 0 | 100% |
| India | 166 | 166 | 0 | 100% |
| Taiwan | 136 | 117 | 19 | 86.0% |
| Korea | 102 | 102 | 0 | 100% |
| Indonesia | 53 | 51 | 2 | 96.2% |
| Thailand | 41 | 41 | 0 | 100% |
| Australia | 38 | 38 | 0 | 100% |
| Malaysia | 37 | 37 | 0 | 100% |
| Hong Kong | 20 | 20 | 0 | 100% |
| Singapore | 19 | 19 | 0 | 100% |
| New Zealand | 13 | 13 | 0 | 100% |
| **TOTAL** | **2,097** | **2,064** | **33** | **98%** |
| *Philippines (EXCLUDED)* | *14* | *0* | *14* | *no source* |

The corrections paid: Australia and Japan closed completely,
and China's MEITU and Anhui Gujing windows now price against
the right companies instead of the wrong ones.

**Philippines is named, not folded in.** `coverage` now
excludes it from the headline and prints it on its own line.
Quoting a coverage rate that includes a market we have decided
not to cover flatters and misleads at the same time.

Against every name-event MSCI has published since 2015 the
figure is different and worth carrying separately: **2,037 of
3,146**, because 894 rows still carry no ticker at all —
China 593, Korea 81, Japan 65. That is a resolution gap, not a
price-data gap.

---

## The 60 missing, by cause

`gaps` now classifies every unpriced window instead of listing
them undifferentiated. A bug we own and a limit of the world
are not the same thing, and counting them together makes our
own defects look like nature.

| cause | n | meaning |
|---|---:|---|
| NO_SOURCE | 14 | Philippines. No usable feed at all. |
| TICKER_DEFECT | 7 | the code asked for is provably not that company's |
| UNEXPLAINED | 7 | attempted, empty, no cause established |
| *Taiwan* | 19 | separate harvester, `tw_event_window.py` |
| *never fetched* | 19 | the newly-resolved Japan/Australia tickers |

**TICKER_DEFECT is proved, not guessed**, by two rules that
need no external listings file:

1. **the board did not exist** — a `688xxx` STAR code before
   July 2019, or a `301xxx` before August 2020;
2. **the code listed later** — the same code returns bars in a
   later review, and its earliest bar post-dates this window's
   effective date.

The 7 UNEXPLAINED are left unexplained on purpose. Jiayuan
(2768.HK) and Waskita (WSKT.JK) look like genuine vendor gaps;
the remaining China names are truncated past resolution
("QINGDAO HAIER A (HK-C)") and guessing a code for them needs
the A-share listings file that is already a registered gap. A
wrong guess is worse than a blank, because a blank is visible.

---

## What is still unbounded

The three corrections were found because the wrong code
*failed*. A wrong code that existed at the time returns
plausible numbers and no error message, and nothing here can
detect that. `MEITU` is the proof: four of its six windows
priced cleanly against a US$100bn company for a US$5bn
company's index event, and only the two 2017 failures gave it
away.

**The visible defect rate is not the defect rate.**

---

## The sequence that produced this, all done

```
py scripts\ticker_corrections.py apply
py scripts\changes_db.py build
py scripts\window_orphans.py apply
py scripts\apac_event_days.py yf China
py scripts\apac_event_days.py yf Japan
py scripts\apac_event_days.py yf Australia
py scripts\apac_event_days.py coverage     # a REPORT, not a harvest
```

## c-261 — Taiwan's "0 days" was a broken endpoint

The Taiwan harvest reported `0 days` for eighteen windows. All
eighteen are **live, well-known OTC names** — E Ink, Phison,
Aspeed, eMemory, Win Semiconductors, PharmaEssentia,
International Games System. None is delisted. That is not
attrition, and the shape of it said so: every unpriced Taiwan
window was a TPEx listing and no TWSE one was.

**Bug 1 — the date.** TPEx wants `date=YYYY/MM/DD` in the
GREGORIAN year; the harvester sent the ROC year because c-232
assumed TPEx was "the same shape as TWSE". Every request
returned `{"stat":"參數輸入錯誤"}` — parameter input error —
and the empty result was read as "this name did not trade".
Half the assumption was right, which is why it looked fine:
the ROWS come back in ROC.

**Bug 2 — the unit, and this is the dangerous one.** TWSE
returns 成交股數, **shares**. TPEx returns 成交張數, **lots**,
where one lot is 1,000 shares. Fixing only the date would have
put every OTC name's volume in the same field 1,000x too
small — in a dataset built to measure trade size against ADV.
Verified on the response rather than assumed: E Ink on
2026-02-02 shows 2,610 lots and 448,660 thousand TWD at a
171.50 close, and 2.61m x 171.50 = 448m only if the figure is
lots.

**A missing window announces itself. A volume off by a factor
of a thousand does not.** `tests/test_tpex_units.py` pins both,
including a distribution check that fails if lots ever leak
into the shares field again.

Taiwan moved 117 -> 131 on a partial re-run. The remaining
four have data at TPEx and simply had not been reached; one
(HONPRECISION, Feb-26) has no window because the TW registry
missed the name, a gap already recorded in `changes_db.py`.

---

## One command still adds data

```
py scripts\tw_event_window.py harvest      # Taiwan's 19
```

Taiwan is on its own harvester (TWSE/TPEx board routing, and
delisted-safe day files rather than Yahoo), so the APAC
re-runs never touched it. After that, nothing left in the
missing column can be closed by running anything: 14 are the
ticker residue, 2 are a genuine vendor gap, and 14 are the
excluded Philippines.

**Then the daily set is frozen.**
