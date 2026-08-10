# Building the listed universe for every APAC market (c-149)

The one missing input for the ADDITION side. This is the
build plan, the sources, and an honest answer to "once we
have it, do we have everything?"

## A discovery that shrinks the problem
MSCI's public constituents tool serves far more than the
Standard country indexes. Probing its dropdown (1,246
indexes) turned up the SMALL CAP and IMI families:

| Index | Code | Covers |
|---|---|---|
| EM SMALL CAP | 655061 | TW KR IN ID MY TH PH CN |
| EAFE SMALL CAP | 106232 | JP AU HK SG NZ |
| AC FAR EAST ex JAPAN SMALL CAP | 655042 | ex-JP Asia |
| EM IMI / EAFE IMI | 664220 / 664152 | full IMI |
| JAPAN / SINGAPORE / INDIA SMALL CAP | 106218 / 106224 / 655072 | single-country |
| JAPAN / SINGAPORE / THAILAND / PHILIPPINES IMI | 664171 / 664181 / 664248 / 664241 | single-country |

**Why this matters:** a Standard-index addition almost always
migrates UP from the Small Cap segment — those companies have
already passed every §2.2 screen (that is what IMI membership
means). So the Small Cap lists ARE the addition candidate
pool, with weights attached, which means their FIFs are
recoverable by the same inversion we use for members.

Caveats, stated before anyone relies on it: the regional
lists are country-MIXED (names carry no country tag), so a
name->country mapping step is required; and Small Cap
membership is itself ~2 months delayed, so a brand-new IPO
above the cutoff can still be invisible (our registered
"blind band").

## Per-market universe sources (in preference order)

| Market | Primary (bulk, survivorship-safe) | Status |
|---|---|---|
| Taiwan | TWSE MI_INDEX + MI_QFIIS + TPEx day-files | **BUILT** (890 screened) |
| India | NSE bhavcopy day-file | adapter EXISTS (event windows) — reuse |
| Korea | KRX day-file | terminal only (bot-blocked from sandbox) |
| Japan | JPX / J-Quants | needs J-Quants signup |
| Indonesia | IDX day-file | terminal only |
| Thailand | SET day-file | terminal only (session ritual works) |
| Malaysia | Bursa | terminal only |
| Australia | ASX company list + Yahoo | sandbox OK |
| HongKong | HKEX securities list + Yahoo | sandbox OK |
| Singapore | SGX list + Yahoo | sandbox OK |
| NewZealand | NZX (5-member index; tiny) | sandbox OK |
| China | SSE/SZSE lists | large; terminal |
| Philippines | PSE EDGE | **no Yahoo prices** — separate problem |

Fallback for any market whose exchange is unreachable: the
MSCI Small Cap list above gives the candidate pool directly,
skipping the full listing.

## Do we then have everything? — honest audit

| §2.2/§2.3 requirement | Have it after the build? | Source |
|---|---|---|
| Full market cap | YES | price x shares (exchange or Yahoo) |
| Float-adjusted cap | YES | Yahoo floatShares/sharesOut for non-members; inversion for members |
| §2.2.3 EU Min Size ($537M) | YES | global constant (Aug value is a forecast — registered) |
| §2.2.4 float cap >= 50% EUMSR | YES | derived |
| §2.2.5 ATVR 3m/12m >= 15% + 80% frequency | YES, with work | 12 months of daily volume x price from Yahoo chart (not throttled) / float cap |
| §2.2.6 FIF >= 0.15 | YES | as above |
| §2.2.7 3 months trading | YES | first trade date |
| §2.2.8 foreign room >= 15% | **PARTIAL** | only binds in FOL markets: TW (MI_QFIIS ✓), TH, ID, IN, PH, VN. Others n/a |
| §2.2.9 financial reporting | **NO** | NOT_EVALUATED, as in Taiwan — rarely binds |
| §2.3.3 cutoff + Segment Number of Companies | YES | measured from the built universe |
| §3.1.5 buffers / priority queue | YES | rulebook constants |

**So: yes — with two named exceptions.** Foreign room is a
real gap in the FOL markets other than Taiwan (Thailand and
Indonesia most likely to bite), and the financial-reporting
screen stays unevaluated. Both are labelled NOT_EVALUATED in
the output rather than silently assumed to pass, exactly as
the Taiwan engine already does.

Two further honest limits that no dataset removes:
- **The blind band.** New listings and names MSCI has never
  covered are invisible until they appear in a published
  list. Taiwan's decade of history says ~2 changes per August
  review originate below the visible floor.
- **Count flex (§2.3.3).** MSCI may change the Segment Number
  of Companies, which moves the cutoff under our feet. We
  price this as a probability haircut, not a certainty.

## Build order (post-Aug-11)
1. **India** — bhavcopy adapter already written; largest
   addition flow in APAC.
2. **Korea** — KRX day-file on Bill's terminal.
3. **Japan** — J-Quants signup, then the same shape.
4. **Australia / HongKong / Singapore** — sandbox-reachable
   listing files + Yahoo.
5. **Thailand / Indonesia / Malaysia** — terminal harvests
   with the session rituals already proven.
6. **China** — largest (576 members); last.
7. **Philippines** — needs a non-Yahoo price source first.
