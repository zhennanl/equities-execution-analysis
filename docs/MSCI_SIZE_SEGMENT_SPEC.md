# The size-segment rules, read straight from the rulebook (c-117)

Source: **MSCI Global Investable Market Indexes Methodology,
May 2026 edition** (192 pp). Every claim below carries its
section and page. This supersedes the ad-hoc "ceiling ±
buffers" convention the engine has been using since c-88.

---

## 1. What the engine had wrong

The engine treated the **upper bound of the Global Minimum
Size Range** as the operative cutoff and hung the buffers off
it:

```
WRONG:  cutoff  := EM range ceiling        (e.g. May-26: $9.06B)
        delete  := full cap < 2/3 x ceiling      ($6.04B)
        add     := full cap > 1.5 x ceiling      ($13.59B)
```

The rulebook says the cutoff is a **computed number that lives
inside that range**, and the buffers hang off the computed
number, not off the range boundary:

```
RIGHT:  cutoff  := Market Size-Segment Cutoff  (May-26 TW: ~$7.5B)
        delete  := full cap < 2/3 x cutoff           (~$4.98B)
        add     := full cap >= 1.0 x cutoff  (necessary)
                   full cap >  1.5 x cutoff  (guaranteed slot)
```

Measured consequence for Taiwan May-2026: the wrong floor
($6.04B vs ~$4.98B) manufactured **exactly the 8 false alarms**
in the backtest. Under the correct cutoff that review scores
**7 hits / 0 misses / 0 false alarms**.

---

## 2. The chain of definitions, in order

### 2.1 Equity Universe Minimum Size Requirement — §2.2.3, p.17
Sort the **DM Equity Universe** by full market cap descending;
cumulate **free float-adjusted** market cap; the company at
**99% coverage** sets the minimum. *May-2026 value: USD 537
million* for DM and EM (p.18). Companies below it are in no
Market Investable Equity Universe at all.

Related screens that must all pass before a company is even a
candidate (§2.2.4–2.2.9): float-adjusted cap ≥ 50% of that
minimum; the DM/EM liquidity requirement (ATVR); global minimum
FIF; minimum length of trading; **minimum foreign room ≥ 15%**;
financial reporting.

### 2.2 Global Minimum Size Reference — §2.3.2.1, p.24
Sort the **DM Investable Equity Universe** by full cap
descending; cumulate free float-adjusted cap; take the full cap
of the company at:

| Segment | Coverage | May-26 DM | May-26 EM (half) |
|---|---|---|---|
| Large Cap | 70% | $51,345M | $25,672M |
| **Standard** | **85%** | **$15,748M** | **$7,874M** |
| Investable Market | 99% | $1,187M | $594M |

"For Emerging Markets, the Global Minimum Size Reference is set
at one-half the corresponding level" (p.24). Data as of the
close of **April 20, 2026**.

### 2.3 Global Minimum Size RANGE — §2.3.2, p.24
> "specifying a range of **0.5 times to 1.15 times** those
> References."

DM Standard: $7.87B – $18.11B. **EM Standard: $3.94B – $9.06B.**
(Confirms the range the engine already used.)

### 2.4 Market Size-Segment Cutoff — §2.3.3, p.26
This is the number that actually decides everything, and it is
computed **per market**:

1. Sort the **Market** Investable Equity Universe (Taiwan's, not
   DM's) by **full** market cap descending.
2. Cumulate **free float-adjusted** market cap.
3. Take the full cap of the company at **85% coverage** (for
   Standard).
4. **If that full cap lies inside the Global Minimum Size
   Range**, it *is* the Market Size-Segment Cutoff, and that
   company's rank is the **Segment Number of Companies**.
5. If it lies outside, flex the COUNT instead: decrease
   companies until the smallest is ≥ the range's lower bound,
   or increase to include everything above the upper bound.
   The last company's full cap then defines the cutoff.

> "This process is designed to give priority to global size
> integrity over market coverage in situations where both
> objectives cannot be achieved simultaneously." (p.26)

Note what step 3 requires: **free float for every company in
the market's universe**, not just for the borderline names.
This is why float is not a tie-breaker in this methodology —
it *sets the threshold itself*.

### 2.5 Buffers — §3.1.5.1, p.43-44
> "The buffer zones at Index Reviews are defined with
> boundaries of **2/3rd of and 1.5 times** the Market
> Size-Segment Cutoff between two size-segments."

Footnote 24: at "light" rebalancings the buffers widen to
**one half and 1.8 times**.

An existing constituent stays in its segment while its full cap
remains inside the buffer. So:
- **Deletion trigger:** full cap falls below **2/3 × cutoff**.
- **Upward migration trigger:** full cap rises above
  **1.5 × cutoff**.

### 2.6 How additions actually happen — §3.1.5, p.42
Companies are assigned in **priority order until the Segment
Number of Companies is reached**:

1. Current Standard constituents ≥ cutoff.
2. **Newly investable companies with full cap ≥ cutoff.**
3. Companies above the **upper buffer (1.5×)** of the lower
   segment — i.e. Small Cap constituents migrating up.
4. Current constituents sitting in the lower buffer, largest
   first, until the buffer threshold is reached.
5. **"The largest companies from the upper buffer of the next
   lower size-segment"** — the residual slot-filler.

This is the structure the engine never modelled. There is no
single "addition bar": **≥ 1.0× cutoff is necessary**, **> 1.5×
gives you a guaranteed slot**, and between the two you are in a
queue that is filled by descending size until the count is met.

### 2.7 The float gate — §2.3.6.1, p.30
> "a security can be included in the Standard Index only if its
> free float-adjusted market capitalization is at least **50%
> of the Market Size-Segment Cutoff**"

If the cutoff sits above/below the range, substitute the range
boundary. For **FIF < 0.15**, the requirement becomes **1.8×**
the minimum. Anything excluded from Standard by this rule is
also excluded from the IMI.

Foreign room (§2.3.6.2, p.30): room < 25% and ≥ 15% → FIF
multiplied by an adjustment factor of 0.5; room < 15% → not
eligible at all (§2.2.8).

Existing constituents get relief (§3.1.6.2, p.44): they may
stay if they meet **2/3 of the float threshold**; Small Cap
constituents need FIF ≥ 0.15; Standard constituents with FIF <
0.15 must meet 2/3 of the 1.8× requirement.

### 2.8 Which data, on which date — §3.1.9, p.48
| Cutoff date | When (for the May review) | Governs |
|---|---|---|
| Equity Universe | last business day of **February** | the Equity Universe; the Equity Universe Minimum Size Requirement |
| Liquidity | last business day of **March** | ATVR, frequency of trading |
| **Price** | **any one of the last 10 business days of April** | **prices for market cap, FIF updates, foreign room changes, number of shares** |

Confirmed May-2026 price cutoff: **April 20, 2026** (§2.3.2.1
worked example, p.24).

Note the Price Cutoff Date governs **FIF and NOS as well as
price** — so a point-in-time reconstruction needs the float
factor *as of that date*, not today's.

Discretion is explicit (p.48): for extraordinary events between
the price cutoff and announcement — fraud allegations,
accounting falsification, takeover bids, indefinite suspension
— MSCI may simply decline to move the company.

---

## 3. What the May-2026 Taiwan result implies

Full caps computed at the disclosed price cutoff (2026-04-20),
FX 31.626:

| Deleted | Full cap | | Smallest survivors | Full cap |
|---|---|---|---|---|
| Taiwan High Speed Rail | $4.76B | | 2834 Taiwan Business Bank | $5.19B |
| Teco Electric | $4.64B | | 6919 Caliway | $5.24B |
| Far Eastern New Century | $4.43B | | 2356 Inventec | $5.29B |
| Compal Electronics | $4.22B | | 2609 Yang Ming | $5.53B |
| Asia Cement | $3.92B | | 8069 E Ink | $5.77B |
| Catcher Technology | $3.67B | | 1101 Taiwan Cement | $5.90B |
| China Airlines | $3.48B | | 2376 Gigabyte | $5.91B |

**Perfectly separable.** The lower buffer sits between $4.76B
and $5.19B, so:

- **2/3 × cutoff ∈ ($4.76B, $5.19B)**
- **⇒ Market Size-Segment Cutoff ≈ $7.14B – $7.79B** (midpoint
  **~$7.5B**), comfortably inside the Global Minimum Size Range
  $3.94B – $9.06B — consistent with §2.3.3 step 4.

The single addition corroborates it: **MPI Corp at $15.91B =
2.13× the inferred cutoff**, clearing the 1.5× upper buffer
outright.

Across the 8 reviews where deletions and survivors separate
cleanly, **16 of 16 additions cleared 1.0× the inferred
cutoff** and only **8 of 16** cleared 1.5× — exactly the
two-path structure of §3.1.5 (guaranteed slot above 1.5×, queue
between 1.0× and 1.5×).

---

## 4. Can we compute the cutoff point-in-time?

| Input needed | Have it? | Note |
|---|---|---|
| Prices at the price cutoff date | **Yes** | vintage series, exact date |
| Shares outstanding at that date | **Mostly** | NOS series, last value ≤ date |
| FX at that date | **Yes** | live TWD=X monthly |
| Which day MSCI picked | **Yes, ex post** | disclosed in each methodology edition's worked example |
| **Free float for the whole TW universe** | **No** | the blocker — see below |
| Market Investable Equity Universe membership | **No** | needs all §2.2 screens rebuilt at the Feb cutoff |
| ATVR / liquidity at the March cutoff | **Collected, not wired** | TWSE decade harvest |
| Foreign room per security | **Partial** | live only |

**The binding constraint is universe-wide point-in-time free
float.** §2.3.3 needs a float factor for *every* company in the
Taiwan universe in order to find the 85%-coverage company. We
hold float for roughly 11% of historically deleted names, and
current-vintage at that.

### CORRECTION (c-118): "historical float is not published by
anyone" was WRONG

That claim, made in the c-116 data audit, does not survive
checking. Ownership disclosure is a listing requirement across
APAC and most of it is public and dated. What is true is
narrower: **nobody publishes MSCI's FIF**, and nobody publishes
a ready-made back-history in one file. The raw material exists.

| Market | Public source | History | Grade |
|---|---|---|---|
| **Japan** | JPX publishes the **TOPIX Free-Float Weight per constituent**, monthly, plus the FFW methodology; constituents and FFW on J-Quants DataCube | monthly, free-float regime since 2005-06 | **A** — an actual published float factor, not a proxy |
| **India** | SEBI-mandated **quarterly shareholding pattern** on NSE/BSE, promoter vs public vs FII/DII, per company; NSE also publishes an ownership tracker by free-float market cap | quarterly, long history | **A** |
| **Taiwan** | **TDCC shareholding-dispersion table**, weekly, per stock, by holding-size bracket (data.gov.tw dataset 11452, plus an OpenAPI); TWSE foreign-holding ratios; MOPS insider filings | weekly since 2007, but TDCC's own portal retains only ~1 year — the archive must be **accumulated forward** or sourced from mirrors | **B** — a strong proxy, awkward history |
| **Thailand** | **SET publishes free float %** — it is a listing-maintenance requirement (≤5% holders count as free float); PSIMS major-shareholder service, SETSMART archive | via SETSMART / data request, not a free bulk file | **A-** (paywalled bulk) |
| **Philippines** | **Public Ownership Report**, filed regularly, on PSE EDGE; minimum public float now 20% for index names | per filing, on EDGE | **A-** |
| **Hong Kong / China H** | CCASS participant holdings daily; SFC Disclosure of Interests for substantial holders | daily/event, long history | **B** |
| **Korea** | DART filings (5% rule, major shareholders); KRX publishes float-adjusted index data | event-driven | **B** |
| **Malaysia / Indonesia / Singapore / Australia / NZ** | Bursa shareholding spread; IDX free-float disclosures; SGX annual-report substantial holders; ASX substantial-holder notices (3%+) | annual to event-driven | **C** — usable, patchy |

Practical read: **Japan and India are close to solved** — a
published float factor and a mandated quarterly ownership
table. **Taiwan is the awkward one**: excellent weekly data,
but the free archive is short, so the history has to be
accumulated going forward (we already snapshot TDCC weekly —
`tdcc_archive` in the event-data cache) or bought.

Three routes, all registered:
1. **Estimate the cutoff empirically** from the observed
   deletion/survivor bracket at past reviews — cheap, works
   today, and is what the numbers above already do.
2. **Harvest the published float sources above**, starting
   with Japan (published FFW) and India (quarterly pattern),
   which double as a validation set for the proxy method used
   elsewhere.
3. **Rebuild TW PIT float** from TDCC + MOPS per period. Only
   this also fixes the float gate (§2.3.6.1) and the
   above-floor deletions the backtest could not explain.

---

## 3b. CORRECTION (c-119): the cutoff is ~$5.2B, not ~$7.5B — and the COUNT is primary

§3 inferred the cutoff from the deletion/survivor bracket and
got ~$7.5B. That interpretation was **wrong**, and an
independent number from the **July-31-2026 Taiwan factsheet**
arbitrates it.

The factsheet publishes, besides the top 10:
- Number of constituents: **77**
- Index float-adjusted market cap: **$3,183.0B**
- Largest constituent (float-adj): **$1,848.5B** (TSMC)
- **Smallest constituent (float-adj): $1.84B**
- Average $41.3B, median $10.4B

Test the two candidate cutoffs against the float gate
(§2.3.6.1: 50% of cutoff; §3.1.6.2: existing constituents may
stay at 2/3 of that):

| Candidate cutoff | Float gate | Existing-constituent relief | Smallest constituent $1.84B |
|---|---|---|---|
| $7.47B (bracket inference) | $3.73B | $2.49B | **FAILS** — contradicts its membership |
| **$5.19B** (smallest survivor's FULL cap) | $2.60B | **$1.73B** | **PASSES** ✓ |

$5.19B is also what §2.3.3/§2.3.4 imply directly: the company
at 85% coverage *defines* the cutoff, its rank *is* the Segment
Number of Companies, and every company at or above its full cap
is in the segment. **The cutoff company IS the smallest
constituent.** So the cutoff is read straight off the index, no
inference needed.

### The consequence: deletions were COUNT-driven, not buffer-driven

With cutoff $5.19B the lower buffer is 2/3 × 5.19 = **$3.46B**.
The seven May-26 deletions measured **$3.48B–$4.76B** — every
one of them *above* the buffer. They were not removed for
breaching it. They were squeezed out because the **Segment
Number of Companies fell** (§3.1.5: companies are assigned
"until the Segment Number of Companies is achieved"; priority 4
admits lower-buffer constituents in descending size order only
"until the threshold of the buffer is reached").

This is the mechanism the engine does not model at all, and it
is the *primary* one:

> **The count is primary; the buffers govern who fills the
> marginal slots.**

Practical restatement of the prediction problem: do not ask
"whose cap fell below a threshold". Ask **"how many slots are
there, and who is below the line when the music stops"**. The
count comes from the 85%-coverage rank, so getting the universe
and its float right determines N, and N determines the cut.

---

## 3c. Which float source is actually best? (c-121, graded)

Graded against the factsheet-implied FIFs for the top 10 —
MSCI's published float cap ÷ our full cap, an identity that
ties to $0.01B:

| Code | Name | MSCI implied | Yahoo | err | TDCC proxy | err |
|---|---|---|---|---|---|---|
| 2330 | TSMC | 0.952 | 0.912 | −4% | 0.846 | −11% |
| 2454 | MediaTek | 0.902 | 0.879 | −3% | 0.910 | +1% |
| 2308 | Delta | 0.752 | 0.604 | **−20%** | 0.882 | +17% |
| 2317 | Hon Hai | 0.873 | 0.861 | −1% | 0.740 | −15% |
| 3711 | ASE | 0.748 | 0.741 | −1% | 0.954 | +27% |
| 2303 | UMC | 0.902 | 0.863 | −4% | 0.690 | −24% |
| 2383 | Elite Material | 0.802 | 0.825 | +3% | 0.849 | +6% |
| 2881 | Fubon | 0.601 | 0.590 | −2% | 0.342 | **−43%** |
| 2891 | CTBC | 0.852 | 0.869 | +2% | 0.558 | **−35%** |
| 2345 | Accton | 0.902 | 0.837 | −7% | 1.000 | +11% |

**Median absolute error: Yahoo 2.7%, TDCC proxy 16.3%.** Yahoo
is six times more accurate, and eight of its ten estimates are
within 4%. MSCI rounds FIF to 2.5% steps above 25% float, so
Yahoo is close to the resolution limit of the rulebook itself.

The TDCC proxy's failure is systematic, not random: the worst
cases are **financials** (Fubon −43%, CTBC −35%), because
bracket 15 lumps large domestic institutional holders in with
strategic holders, and MSCI counts those as float.

### The architecture this implies

Neither source wins outright — they fail in opposite ways:

| | Accuracy | Coverage | Cost |
|---|---|---|---|
| Factsheet-implied | exact (it *is* MSCI) | **top 10 only** | free, one PDF |
| Yahoo | **2.7% median** | per-name, rate-limited | slow at 2,000 names |
| TDCC | 16.3%, sector-biased | **4,019 securities, 1 call** | free, instant |

So use each where its weakness does not bind, which is exactly
what §4b's sensitivity analysis prescribed independently:

1. **Top 10 — factsheet-implied.** Free, exact, and these names
   dominate the coverage curve (TSMC alone is ~49% of Taiwan's
   float).
2. **Rest of the large caps — Yahoo.** A few hundred names,
   2.7% error, and this is the band where float error still
   shifts the crossing.
3. **The tail — TDCC.** Only the aggregate matters there;
   independent errors average out across hundreds of names
   (§4b: sd 30% per name → 2.7% on the aggregate).

The one warning: Yahoo's `float_shares` is a vendor estimate,
not a filing. Delta at −20% shows it can be badly wrong on a
single name. It should be treated as a strong prior to be
overridden by the factsheet where the factsheet speaks.

---

## 3d. The APAC-wide float-source test (c-124, partial — 7 of 13 markets scored)

Bill's TW method repeated across APAC: parse each July-2026
factsheet's top-10 float caps, divide by an independent full
cap, grade Yahoo's float against the implied FIFs. (Date
caveat: Yahoo caps are ~Aug-7 vs the Jul-31 factsheet — a
~1-week drift, so 1-2% differences are noise here.)

| Market | n | Yahoo median abs err | Reading |
|---|---|---|---|
| Australia | 6 | **1.1%** | near-exact; ONE DLC outlier (RIO) |
| Singapore | 4 | **2.6%** | near-exact |
| New Zealand | 4 | **4.4%** | clean, incl. Meridian's govt stake |
| Japan | 10 | **4.6%** | strong |
| Hong Kong | 10 | 5.3% | good |
| Taiwan | 10 | 6.1% (2.7% at exact Jul-31 caps, c-121) | good |
| Indonesia | 10 | 8.8% | usable |
| Korea | 10 | 13.7% | pref-line artifact + chaebol cross-holdings |
| Malaysia | 10 | 14.1% | bimodal — see below |
| China | 10 | 22.8% | H-share DENOMINATOR artifact (ours) |
| Thailand | 10 | **23.0%** | FOL-bound, like India |
| India | 9 | **32.1%** | FOL-bound (the known reason) |
| Philippines | 0 | **no Yahoo coverage at all** | PSE fundamentals absent from Yahoo; source = PSE EDGE Public Ownership Reports |

### The outliers are not float errors — they are index-construction structure

- **India (+24% to +74% everywhere):** Yahoo says HDFC/ICICI/
  Infosys float ≈ 1.0 and it is *right about the float* — these
  have no promoter block. MSCI's implied FIFs sit at 0.72-0.75
  because **FIF = min(float, foreign-limit adjustment)**
  (Appendix VI p.97; §2.2.8/§2.3.6.2). India caps foreign
  ownership per stock, so the FIF is FOL-bound, not
  float-bound. Yahoo can never see this; the fix is FOL/
  headroom data (NSDL publishes FPI limits per company).
- **Korea structural cases:** SAMSUNG ELECTRONICS PREF implied
  0.136 vs Yahoo 1.0 — Yahoo returns the COMPANY's cap for the
  pref line, so the denominator is wrong, an artifact of ours
  not MSCI's. HYUNDAI MOTOR implied 0.496 vs Yahoo 0.955 —
  chaebol cross-holdings that MSCI classifies strategic and
  Yahoo counts as float: here Yahoo is genuinely wrong.
- **RIO TINTO (AU) implied 0.219:** dual-listed company — the
  Yahoo cap is the global DLC group while MSCI's AU line holds
  only the Australian listing. Denominator artifact.

### What this settles for the APAC rollout

Yahoo float is a **legitimate universal tier-2 source** in
markets without structural overlays (JP/AU/HK/ID/TW confirmed),
but the FIF is only equal to free float when nothing else
binds. Per market, the needed overlay:

| Market | Overlay needed on top of float |
|---|---|
| India | **FOL/FPI headroom** (NSDL) — mandatory, binds the largest names (all 9 errors positive, +24% to +74%) |
| **Thailand** | **FOL/NVDR** — same signature as India: every error positive (+19% to +98%; PTT implied 0.347 vs float 0.459, Gulf 0.247 vs 0.488). Thai foreign limits + the NVDR structure cap the FIF below the float |
| Korea | pref lines (Samsung pref: Yahoo returns the COMPANY cap — our artifact) + chaebol cross-holdings (Hyundai: genuine Yahoo failure) |
| China | **H-share class denominator** — ICBC implied 0.192 / BOC 0.219 / Ping An 0.369 vs Yahoo ~1.0 are OUR artifact: Yahoo's cap is the whole company (A+H) while MSCI's line is the H class. Fix = per-class share counts (HKEX), not better float |
| Malaysia | bimodal: half the names near-exact (Public Bank +3%, Press Metal +2%, Sunway −4%), half FOL/GLC-bound (Maybank +102%, RHB +57%, IHH +81% — state funds Khazanah/PNB/EPF classified strategic by MSCI, float by Yahoo) |
| Australia | DLC handling (RIO; BHP historically) |
| JP / HK / SG / NZ / ID | none evident — Yahoo alone lands within ~5-9% |
| Philippines | Yahoo has NO PSE fundamentals — use PSE EDGE Public Ownership Reports (they publish public-float % directly) |

---

## 3e. The float scoreboard after the alternative-source round (c-126), and the APAC rollout verdict

All sources graded against factsheet-implied FIFs to date:

| Market | Yahoo | Best alternative | Best result |
|---|---|---|---|
| Australia | **1.1%** | (DLC override for RIO) | Yahoo |
| Singapore | **2.6%** | — | Yahoo |
| Taiwan | 6.1% | factsheet>Yahoo>TDCC-calibrated stack | **~3%** hybrid |
| New Zealand | **4.4%** | — | Yahoo |
| Japan | **4.6%** | JPX FFW (published; unharvested) | Yahoo now, JPX later |
| Hong Kong | 5.3% | — | Yahoo |
| Indonesia | 8.8% | IDX list (bot-blocked; terminal task) | Yahoo |
| Korea | 13.7% | line fix resolves pref; cross-holdings remain | line fix + Yahoo |
| Malaysia | 14.1% | calibrated GLIC classifier (built, unrun) | pending |
| China | 22.8% | per-line share counts (Yahoo's own field) | **13.1%** ex-artifact |
| **Thailand** | 23.0% | **SET float+FOL: min(f,FOL) = 11.3%** | SET overlay |
| India | 32.1% | NSDL FPI headroom (manual download pending) | pending |
| Philippines | none | **PSE EDGE float+FOL: 12.2%** | PSE overlay |

Thailand refinement registered: min(float, FOL) OVER-corrects
the NVDR-accessible names — BDMS (implied 0.638, FOL 0.30) and
SCC (0.582, FOL 0.25) sit far ABOVE their FOLs because foreign
investors reach them through NVDRs, which MSCI counts. The
Thai estimator needs three branches: FOL-capped (banks/PTT),
float-bound (NVDR names), and the §2.3.6.2 room adjustment.

### Can the Taiwan process run on Yahoo alone, per market?

The TW pipeline needs three inputs: (1) the full listed
universe with prices and shares, (2) float per name, (3)
validation anchors. The anchors exist EVERYWHERE (constituents
tool count + factsheet smallest + top-10 implied FIFs). The
binding questions are universe assembly and float quality:

| Market | Universe source (bulk) | Float | Verdict |
|---|---|---|---|
| Japan | JPX listed-issues file | Yahoo 4.6% (JPX FFW upgrade available) | **GO** — largest build (~1,300 names >$537M) |
| Australia | ASX company list | Yahoo 1.1% + DLC table | **GO** |
| Hong Kong | HKEX securities list | Yahoo 5.3% | **GO** (watch class lines) |
| Singapore | SGX securities list | Yahoo 2.6% | **GO** (~100 names) |
| New Zealand | NZX list | Yahoo 4.4% | **GO** (~25 names, trivial) |
| Indonesia | IDX list (terminal) | Yahoo 8.8% | **GO** with wider bands |
| Korea | KRX list | Yahoo + line fix; cross-holdings unresolved | **GO with caution** — expect KR-specific misses |
| Thailand | SET list | SET float+FOL (11.3%, NVDR branch pending) | **GO** — float source is the EXCHANGE, not Yahoo |
| Philippines | PSE list | PSE EDGE (12.2%) | **GO** — Yahoo not needed |
| Malaysia | Bursa list (terminal) | GLIC classifier pending | HOLD until calibrated |
| India | NSE/BSE lists | blocked on NSDL headroom | HOLD — float wrong without FOL |
| China | 3 exchanges + Connect eligibility | line caps + Connect screens | HOLD — a build of its own |

Rollout order by (impact x readiness): JP, AU, HK, SG first;
KR/TH/ID next; NZ/PH anytime (small); MY/IN/CN after their
overlays land.

Bill's argument: wrong float → wrong float-adjusted cap →
wrong 85% threshold. **Directionally right, but the mechanism
is narrower than it looks**, and the narrowing is useful.

The cutoff is a **coverage rank**, and coverage is a ratio.
Scale every float in the universe by the same constant and the
numerator and denominator scale together — the 85% company does
not move. Measured on the 148-name TW vintage universe at the
May-26 price date:

| Error model | Effect on the crossing |
|---|---|
| **Uniform** — all floats ×0.6, ×0.8 | **no change at all** |
| Uniform ×1.2, ×1.5 | small drift, only because floats clip at 1.0 |
| **Random per-name noise**, sd 10% | median unchanged; range ±6% |
| Random noise, sd 20% | median +1%; range −23% to +7% |
| Random noise, sd 30% | median +2%; range −29% to +8% |
| **Size-correlated bias**, large-cap float −10% vs small | **−9%** |
| Size-correlated bias, large-cap float −20% vs small | **−12%** |

So the thing that moves the cutoff is not float *level* and
not unbiased float *noise* — it is **float bias correlated with
company size**. A default of 0.55 applied to the tail while
large caps carry researched FIFs is exactly that kind of
correlated error, and it is what our stack does today.

Two practical consequences:
1. Chasing float precision name-by-name across the whole
   universe has lower value than it appears. Getting the
   **cross-sectional shape** right — particularly large-cap
   floats relative to the tail — is what matters.
2. The float gate (§2.3.6.1) is different: it tests one
   security's own float against 50% of the cutoff, so there
   the **level** matters directly. That is where Formosa
   Petrochemical (FIF ≈ 0.12) and Nanya (≈ 0.46) live, and it
   is why they were deleted while sitting far above the size
   floor.

---

## 4c. "If we had PIT float for every stock, would we match MSCI?"

Closer, but **not automatically**. Three gaps remain, and they
are listed in order of measured size — which is not the order
one would guess.

### Gap 1 — universe completeness (the biggest, and it is not about float)

Measured at the May-26 price date on our 148-name Taiwan
universe: at the implied cutoff of ~$7.5B we have accumulated
**94.6%** of our universe's float. MSCI accumulates **85%**
there. For both to be true, MSCI's universe must hold

> **1.11× our float mass — roughly $310B of float sitting in
> companies our universe never sees.**

The Equity Universe Minimum Size Requirement for May-26 was
**USD 537 million** (§2.2.3, p.18). Taiwan has several hundred
listed companies above that line; we carry 148 names, and only
43 of them under $3B. Perfect float on a universe missing a
tenth of the market's float cannot converge on MSCI's answer —
the denominator is wrong before float is even applied.

**Two thresholds, and they are not the same number** (a
correction to how §4c first read):

- **§2.2.3, company level: FULL market cap ≥ USD 537M.**
  "a company must have the required minimum **full** market
  capitalization" (p.17). Not float-adjusted.
- **§2.2.4, security level: FLOAT-ADJUSTED cap ≥ 50% of that
  = USD 268.5M** (p.18).

So float *does* enter universe construction — via the second
screen. The earlier phrasing "universe completion needs no
float" was too strong.

### Why float precision still matters far less in the tail (measured)

The tail names never individually cross the cutoff; they matter
only through their **contribution to the coverage denominator**,
i.e. their aggregate float. Aggregates are forgiving in a way
individual thresholds are not. Measured on the same universe:

| Test | Effect |
|---|---|
| ±30% random float error on **tail names only** (< $7.5B) | crossing $14.21–15.09B (**±3%**) |
| ±30% random float error on **large names only** (≥ $7.5B) | crossing $8.90–15.91B (**−40% to +8%**) |
| Per-name float error sd 20% → error in **aggregate tail float** | 1.9% |
| Per-name float error sd 30% → aggregate tail float | 2.7% |
| Per-name float error sd 50% → aggregate tail float | 4.6% |
| **Omitting the missing tail entirely** | **11%** |

Independent per-name errors average out across hundreds of
names (roughly error/√n); omission does not average out at all.
So a crude flat float on 300 recovered tail names beats a
perfect float on a universe that is missing them, by roughly
4× on the denominator.

The asymmetry is the whole point: **float precision buys you
almost nothing in the tail and almost everything at the top**,
because a large-cap float error shifts a big block of coverage
past the 85% line, while a tail error shifts a rounding
error — and, near the cutoff itself, decides which company is
the marginal one.

**Priority that follows**: recover the missing names with any
defensible float estimate first; spend research effort on the
large caps and on the names bracketing the cutoff.

### Gap 2 — MSCI's FIF is not "published free float"

Appendix VI, p.97, is unusually encouraging:

> **"MSCI's estimation of free float is based solely on
> publicly available shareholder information. For each
> security, all available shareholdings are considered where
> public data is available, regardless of the size of the
> shareholding."**

So MSCI is working from the *same* public disclosures surveyed
in §4 — TDCC, DART, SEBI patterns, CCASS, Public Ownership
Reports. There is no private data moat. The residual gap is
therefore **definitional and operational, not informational**:

- **Strategic vs non-strategic classification.** MSCI splits
  holders by investor type; the rules live in a *separate*
  document, the "MSCI Free Float Data Methodology". This is the
  real unknown, and it is where our TDCC bracket-proxy and
  insider-filings proxy will diverge from MSCI.
- **Foreign Ownership Limits** (p.97): for FOL securities the
  float available to foreigners is `min(estimated free float,
  FOL)`. Taiwan applies FOLs in some sectors.
- **Rounding** (p.97-98): FIF is rounded to the **nearest 2.5%
  above 25% float**, 0.5% between 5% and 25%, 0.1% below 5%.

That rounding rule is a useful discipline: above 25% float,
**any precision finer than ~1% is discarded by MSCI itself.**
It reinforces §4b — chase the cross-sectional shape, not
decimal places.

### Gap 3 — the cutoff is not recomputed from scratch

§2.3.3 (p.26): cutoffs are "maintained daily, and updated at
Index Reviews, **additionally taking into account index
stability and continuity rules**". Appendix X rank-anchors the
Global Minimum Size References between reviews. So even a
perfect universe with perfect float would reproduce the
*unconstrained* crossing, not necessarily MSCI's published
cutoff.

And §3.1.9 (p.48) reserves explicit discretion for
extraordinary events.

### The honest bottom line

Perfect point-in-time float would take us from "wrong number"
to "right method, residual error". It is necessary. It is not
sufficient, and on today's evidence it is **not even the
binding constraint** — universe completeness is.

---

## 4d. SAIR vs QIR — the distinction was ABOLISHED in Feb-2023

Appendix XX, p.148-149, "Transition to a Quarterly
Comprehensive Index Review":

> "**Prior to the February 2023 Index Review**, the MSCI Global
> Investable Market Indexes were reviewed on a quarterly basis
> which involved: Semi-Annual Index Reviews (SAIRs) in May and
> November and Quarterly Index Reviews (QIRs) in February and
> August. The objective of the SAIRs was to systematically
> reassess the various dimensions of the Equity Universe for all
> markets, involving a comprehensive review of the Size-Segment
> Indexes. **QIRs aimed to capture significant market driven
> changes** that were not captured in the index at the time of
> their actual occurrence but are significant enough to be
> reflected before the next SAIR."

> "MSCI transitioned to a **Quarterly Comprehensive Index Review
> (QCIR)** schedule starting from the February 2023 Index
> Review. In a QCIR, MSCI employs the index maintenance
> methodology of an SAIR across each of the quarterly Index
> Reviews. Foreign Inclusion Factors and Number of Shares were
> fully reviewed up to the Price Cutoff Date of each QCIR
> starting from the May 2023 Index Review."

So: **yes, they had different rules — and no, they no longer
do.** §3.1 (p.35) in the current book calls all four
"Quarterly Index Reviews" and applies the full maintenance list
to every one of them.

Our own database confirms the change cleanly (APAC, all 13
markets, average changes per review):

| Era | QIR (Feb/Aug) | SAIR (May/Nov) |
|---|---|---|
| 2015 – 2022 | **12.7** | **117.3** |
| Feb-2023 onward | **72.9** | **81.3** |

A 9× gap collapses to 1.1×. The old asymmetry was not a
seasonal quirk — it was the methodology, and it ended. Anything
in the project that treats "SAIRs carry the breadth" as a live
rule is now wrong for post-2023 data (the History Explorer
caption has been corrected).

**Trading consequence**: the Feb and Aug reviews are now as
dangerous as May and Nov. Aug-2026 is a full comprehensive
review — universe refresh, cutoffs reassessed, FIF and NOS
fully updated to the price cutoff.

---

## 5. Corrected engine specification

```
cutoff        = MarketSizeSegmentCutoff(review)      # §2.3.3
                clipped to [0.5, 1.15] x GMSR_EM     # §2.3.2
delete_floor  = (2/3)  x cutoff                      # §3.1.5.1
add_necessary = (1.0)  x cutoff                      # §3.1.5 (2)
add_sufficient= (1.5)  x cutoff                      # §3.1.5 (3)
float_gate    = 0.50   x cutoff                      # §2.3.6.1
  ... x1.8 if FIF < 0.15;  existing constituents x2/3 (§3.1.6.2)
count         = SegmentNumberOfCompanies             # §2.3.3
all inputs as of the Price Cutoff Date               # §3.1.9
  (price, FIF, NOS, foreign room)
light rebalancing: buffers widen to 0.5x / 1.8x      # §3.1.5.1 fn24
```

**Open items this exposes**
- The Segment Number of Companies (a count) is not modelled at
  all; it decides who fills the 1.0×–1.5× queue.
- The float gate is not applied historically.
- Newly-investable additions (path 2) are structurally
  invisible to us — they enter from outside our universe.
