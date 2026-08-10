# Index Review, Explained From Zero — Running Q&A Record

*Session 9i (2026-08-05). Part 1 is the plain-language explanation
(no abbreviations, no assumed knowledge). Part 2 records every
follow-up question and answer — this file is the running record;
new questions get appended here. Rulebook references are to the
MSCI Global Investable Market Indexes Methodology, May-2026
edition (192 pages; the copy linked from MSCI_REVIEW_LINKS doc).
Quotations are limited for copyright — references give section and
page so the exact wording can be read in the book itself.*

## Part 1 — How we derive the addition and deletion shortlists

**The setting.** A stock index is a published list of companies.
MSCI, the company that maintains this list for Taiwan, promises
investors that the list always contains the large companies that
together represent most of Taiwan's stock market value. Four times
a year, MSCI checks whether the list still keeps that promise, and
adds or removes companies so that it does. Our job is to predict
those changes before MSCI announces them. Everything below uses one
measuring stick: market capitalization — the total value of a
company, its share price multiplied by the total number of shares
that exist.

**Drawing the size line.** We line up companies from largest to
smallest by market capitalization, walk down the line adding up
value, and stop when we have covered eighty-five percent of the
market's value. The size of the company where we stop becomes the
reference line — MSCI calls it the Global Minimum Size Reference;
think of it as the size a company needs to be to belong. Every
candidate judgment is a comparison against this line.

**Finding deletion candidates.** Deletions can only come from
inside the list. We rebuild the current member list from the
published holdings of index-tracking funds, sort members by market
capitalization smallest-first, and look at the left edge. A sitting
member is not removed the moment it slips below the line — MSCI
gives members tolerance — but once it falls meaningfully below,
removal becomes likely at the next review. Deletion candidates =
members whose value has sunk below, or close to, the size line. In
the last two real reviews, every company MSCI actually removed sat
exactly in this left-edge group.

**Finding addition candidates.** The mirror image, but entry is
deliberately harder than staying: a newcomer must be clearly above
the line (roughly one-and-a-half to two times it depending on the
review type) and must pass three gates. Gate one: enough shares
must be genuinely available to the public — shares locked up by
founders, governments, or parent companies do not count; the
available portion is called the free float, and the value of the
freely tradable shares alone must clear its own bar. Gate two: the
stock must trade actively enough to be bought in size. Gate three:
in markets that cap foreign ownership, room must remain under the
cap — if foreigners cannot buy, index funds cannot track, so MSCI
will not add.

**The honest limits.** We estimate free float from public filings;
MSCI uses private estimates — at the exact boundary MSCI sometimes
keeps a company we expected out (our only wrong calls in May 2026).
And our newcomer pool only contains companies that have come near
the index before; a company rocketing from nowhere can reach the
bar before we see it. Both blind spots are carried as explicit
statements.

## Part 2 — Questions and answers (running record)

### Q1. How is the eighty-five percent determined?

It is not our choice — it is MSCI's published design parameter.
The rulebook sets a target coverage for each size segment of every
market: the Large Cap segment targets 70% ± 5%, the **Standard
segment (the index we predict) targets 85% ± 5%**, and the
broadest segment 99% (§2.3.1, p.23). The 85% is measured in
free-float-adjusted value — the value of the freely tradable
shares, not total company value. So the walk stops when the
freely-tradable value covered reaches eighty-five percent.

### Q2. What is "the whole market's value" in the walk?

Two layers, and the distinction matters. For the GLOBAL reference
line, the book uses the combined investable universe of the
developed markets — all companies in developed markets that pass
the basic investability screens, measured at free-float-adjusted
value; the Emerging Markets reference is then set at one-half of
the developed-markets reference (§2.3.2.1, p.24–25). For each
individual market (Taiwan), the actual cutoff is then chosen
within or near the range built around that reference, using
Taiwan's own investable universe (§2.3.5, p.26–27). Our engine
approximates the second layer directly: it walks Taiwan's own
universe. "The whole market's value" therefore means: the
free-float-adjusted value of all investable Taiwan-listed
companies — which is why our universe must model the mid-cap body
of the market, not just the large names.

### Q3. Which company do we stop at, in the May-2026 Taiwan example?

The book itself publishes the May-2026 global numbers (worked
example, §2.3.2.1, p.25, using April 20, 2026 data): the
developed-markets reference came out at **USD 15.75 billion**,
giving a developed-markets range of USD 7.87–18.11 billion; the
Emerging-Markets reference is half of that (≈ USD 7.9 billion),
giving an Emerging-Markets range of roughly **USD 3.9–9.1
billion**. Our Taiwan-specific walk (frozen at April 30, 2026)
lands the Taiwan line at **≈ USD 4.6–5.8 billion** depending on
frame — comfortably inside MSCI's published range, which is the
consistency check.

And an honesty point our own data demonstrates: there is NO single
identifiable real company at the stopping point. If we walk only
the ~150 companies we track by name, the crossing lands absurdly
high (rank 33, ≈ USD 15 billion) because one company — Taiwan
Semiconductor, 55% of the tracked universe's tradable value —
compresses everything. The real market has ~1,800 listed
companies; our engine models that mid-cap body (anchored to MSCI's
published member count), which pushes the crossing down to ≈ USD
5.8 billion, landing between real members like Gigabyte
(2376, ≈ USD 5.6B) and the next members above USD 6 billion. The
stopping "company" is a modeled point in the mid-cap body, and we
say so rather than naming a false precision.

### Q4. Can we explicitly show the GMSR calculation when presenting our work?

Yes — recorded as a planned addition: the workbench will get a
"show the walk" view — the cumulative-coverage curve, the 85%
crossing marked, the resulting line, and the sensitivity (how much
the line moves if free-float estimates shift ±10%). Everything
needed is already computed; this is display work.

### Q5. What is the size line for DELETION in May-2026 Taiwan, and where is it in the rulebook?

Three nested lines, from loosest to hardest:

1. **The buffer zone** (the operative line): an existing member
   stays in its segment while its value remains within a buffer of
   two-thirds of, to one-and-a-half times, the market's cutoff
   (§3.1.5.1, p.44, including the buffer diagram on p.44–45;
   at "light" rebalancings the buffers widen to one-half and 1.8× —
   footnote 24, p.44). Falling through the lower buffer migrates
   the company out of the Standard segment — which IS the deletion.
2. **The range floor**: the overall range around the reference is
   0.5× to 1.15× (§2.3.2, p.24) — 0.5× is the absolute lower bound
   of where the cutoff itself may sit.
3. **Empirically, in May-2026 Taiwan**: with our reconstructed line
   at ≈ USD 4.6 billion (April-30 frame), the seven companies MSCI
   deleted had values of ≈ USD 2.9–4.6 billion — 0.73× to 0.99× of
   the line — and every surviving member sat at 1.05× or higher.
   The deletion line, as realized, was almost exactly 1.0× our
   reconstructed reference, consistent with the buffer arithmetic
   operating on MSCI's (private) cutoff.

### Q6. Are the three addition gates defined in the rulebook?

Yes, all three, with retention leniency for existing members in
each case (existing members are judged on looser versions —
§3.1.2, p.37):

1. **Free float**: a security needs a free-float factor of at
   least 0.15 (the Global Minimum Foreign Inclusion Factor rule;
   §2.2.4 with the low-float exception mechanics restated for
   reviews at §3.1.2.5, p.39–40 — very-low-float names must clear
   1.8× half the cutoff on tradable value), and the tradable value
   itself must clear half the applicable size bar (the minimum
   free-float-adjusted capitalization requirement, §3.1.2.3, p.38;
   final segment-level float conformity at §3.1.6, p.45–46).
2. **Liquidity**: a minimum annualized traded-value ratio — 15%
   for Emerging Markets new entrants (20% developed), with
   existing members retained down to two-thirds of those levels
   plus short-horizon trading-frequency floors (§2.2.5, applied at
   review per §3.1.2.4, p.38–39).
3. **Foreign room**: securities under a foreign ownership limit
   need at least 15% of the foreign quota still available to be
   ADDED; existing members are exempt from this check (§3.1.2.6,
   p.40).

### Q7. Why does the index we predict belong to the Standard segment (the 85% one)?

Because that is where the money is. The rulebook builds three
nested size layers for every market (§2.3, p.22–23): the broadest
layer covering ~99% of value (the Investable Market segment), the
**Standard segment covering 85%** (defined as Large Cap + Mid Cap),
and the Large Cap layer alone at 70%; Small Cap is the difference
between the broadest layer and Standard. The flagship products —
the "MSCI Taiwan Index" itself, and the MSCI Emerging Markets index
that the giant tracker funds follow — are STANDARD-segment
products. The official change lists we grade against are the
Standard-index changes, and the rebalance flows a program-trading
desk executes are overwhelmingly Standard-tracker flows. We predict
the Standard segment because that is the segment whose changes
move money. (The broadest-segment trackers exist too — one of the
large emerging-markets funds tracks it — which is why a
Standard-to-Small-Cap migration produces flow for one client type
and none for another; recorded in the client-archetype work.)

### Q8. Did we actually calculate Taiwan's total free-float-adjusted market value? What number does our walk use?

Honest answer: we never measure the true total directly — and here
is exactly what our walk uses instead (May-2026 frame, April-30
prices). The universe inside our walk has two parts: the 144
companies we track by name (total value ≈ USD 3,510 billion; ≈
USD 2,840 billion after adjusting for freely tradable shares) plus
a modeled body of 400 mid-size companies standing in for the rest
of the market (≈ USD 1,016 billion; ≈ USD 711 billion tradable).
So the "whole market's value" our eighty-five-percent walk divides
by is an IMPLICIT total of ≈ **USD 3,552 billion tradable value**
(≈ USD 4,527 billion before the float adjustment), of which Taiwan
Semiconductor alone is 43.7%. The modeled body is not guessed
freely — it is anchored so that the total member count matches
MSCI's published constituent count, which is what disciplines the
implicit total. Stated plainly: the count anchor substitutes for
measuring the true market total. The true total IS publicly
measurable (the Taiwan Stock Exchange publishes aggregate market
capitalization), and reconciling our implicit total against the
exchange's official figure is now recorded as a calibration
upgrade — it would convert the modeled body from count-anchored to
value-anchored.

### Q9. Where can I confirm on MSCI's website that MSCI Taiwan and MSCI Emerging Markets are Standard-segment (85%) products?

Three places, each one click deep (all links verified live
2026-08-05):

1. **MSCI Taiwan Index — official factsheet (PDF):**
   https://www.msci.com/documents/10199/255599/msci-taiwan-index.pdf
   The first paragraph states the index measures the large- and
   mid-cap segments of the Taiwan market and, with its constituent
   count, covers approximately 85% of the free float-adjusted
   market capitalization in Taiwan. "Large and mid cap" IS the
   definition of the Standard segment (methodology §2.3), and the
   85% is the coverage target from §2.3.1. The index profile page
   carries the same description:
   https://www.msci.com/indexes/index/915800/msci-taiwan-index
2. **MSCI Emerging Markets Index — profile/factsheet:**
   https://www.msci.com/indexes/index/990100/msci-emerging-markets-index
   Same construction language: large- and mid-cap representation
   across the emerging-markets countries, targeting approximately
   85% of the free float-adjusted market capitalization in EACH
   country — i.e., the union of the country Standard segments,
   which is the building-block principle.
3. **The methodology book itself** (§2.3.1, p.23 of the May-2026
   edition): the Standard segment's target coverage of 85% ± 5% —
   the design parameter both factsheets are quoting.

Bonus cross-check: the iShares EWT fund page states its benchmark
is the MSCI Taiwan 25/50 Index — the capped variant of the same
Standard-segment index (capping reweights, membership unchanged),
which is why fund holdings observe Standard membership.

### Q10. Would the Taiwan Stock Exchange's official aggregate market value be a better estimate — and how would we handle free float on it?

Yes for one half of the problem, and here is the honest treatment
of the other half.

**What the exchange's number fixes.** The exchange publishes the
official TOTAL market value of all listed companies (full value,
daily). Today our walk's denominator carries a modeled body whose
total value is implied by a member-count anchor; replacing that
implied total with the exchange's measured total converts the body
from "modeled to match a count" to "measured, then shaped" —
measuring beats modeling wherever measuring is possible.

**What it does not fix.** The walk divides by FREE-FLOAT-ADJUSTED
value — the value of freely tradable shares only — and the
exchange's aggregate is full value. No official float-adjusted
market total is published anywhere; even index providers compute
their own.

**The bridge, in three layers.** (1) For the ~144 companies we
track by name — which are ≈ 80% of the market's tradable value —
we already hold per-company float estimates, so the head of the
market gets an exact float-adjusted sum. (2) For the residual body
(the exchange's measured total minus our named total), apply an
ESTIMATED average float ratio, stated with a band rather than a
point. (3) The saving grace is arithmetic: because the head
dominates, the body's float assumption is second-order — moving
the body's assumed float ratio from 0.7 to 0.5 changes the total
tradable denominator by only ≈ 6% (from ≈ $3,552B to ≈ $3,349B in
the May-2026 frame), which moves the size line by less than the
frame-to-frame differences we already disclose. So the body's
float uncertainty is real, bounded, and reportable as a band.

**The remaining irreducible.** Even a perfect reconciliation
approximates MSCI's denominator rather than equalling it, because
MSCI uses its own private float estimates throughout. The
consistency check stays the same: our line must land inside MSCI's
published range (it does — Q3).

**Upgrade spec, recorded:** value-anchor the modeled body to the
exchange's official total (full value), float-adjust the head
per-name and the body by a banded ratio, and report the size line
with its band. Replaces the count-only anchor; count becomes the
cross-check instead of the driver.

### Q11. Explain like I'm five: what does "covers 85% of the free float-adjusted market capitalization" mean — and what is the EXACT calculation?

**The five-year-old version.** Imagine every company in Taiwan is a
jar of coins. The coins are only the shares ordinary people can
actually buy — coins glued to the jar (the founder's shares, the
government's shares) don't count. Now line up all the jars, biggest
pile of loose coins first. Start putting jars into a basket,
biggest first, and keep going until your basket holds 85 cents of
every dollar of loose coins in the whole country. Stop. The basket
is the index. "Covers 85%" means: the coins in the basket are 85%
of all the loose coins — NOT that you took 85% of anything, and
NOT that there are 85 jars. The number of jars is whatever it
takes; in Taiwan it currently takes about 79.

**The exact calculation, step by step (no shortcuts):**

1. For ONE company: free-float-adjusted market capitalization =
   share price × total shares × the free-float factor (the portion
   of shares genuinely available to public investors; MSCI
   estimates this factor per company and rounds it).
2. For TAIWAN AS A WHOLE: sum step 1 over EVERY investable listed
   company. This sum — company by company, never a single
   top-down number — is "the free float-adjusted market
   capitalization in Taiwan." (May-2026, our reconstruction:
   ≈ USD 3,552 billion.)
3. The coverage TARGET in dollars = that sum × 0.85
   (≈ USD 3,019 billion in May-2026).
4. THE WALK: sort companies largest-first by value and add them
   one at a time, accumulating their step-1 values, until the
   running total reaches the target from step 3. The companies
   accumulated so far ARE the index (before buffers smooth the
   edges); the FULL market value of the company where you crossed
   the target is the size line (≈ USD 5.8 billion in our May-2026
   frame).

**Correcting the proposed shortcut.** "TWSE official total × 85% ×
float ratio" mixes two different things. The exchange's official
total × an average float ratio is a legitimate ESTIMATE of step 2
(the denominator) — that is exactly the Q10 upgrade. Multiplying
by 85% then gives you step 3, the dollar target — but the target
is NOT the answer to anything by itself: the index is the SET of
companies you collect walking toward that target, and the size
line is where the walk stops. The 85% selects companies; it never
multiplies a company's value. Also note the order: float-adjust
first, THEN take 85% of the sum — companies with huge locked
holdings contribute little to the denominator, which is why a
company's rank by tradable value can differ sharply from its rank
by total value.

### Q12. Walk me through the ≈ $3,552B derivation and simulate the May-2026 walk — and show the work on the website.

**The derivation, ingredient by ingredient (all reproducible via
scripts/show_the_walk.py):**

1. Named head: 144 tracked companies. Each one = April-30 share
   price × total shares outstanding (Taiwan Stock Exchange filings
   via the FinMind archive) ÷ 32.5 currency conversion → USD 3,510
   billion full value; multiply each by its per-company float
   estimate (holder filings; default 0.7 where unfiled, flagged) →
   **USD 2,840 billion tradable**.
2. Modeled body: 400 stand-in companies for the ~1,700 listed
   names we do not track, sizes drawn log-uniform between USD 0.3
   and 10 billion (seed 11 — reproducible), float ratio 0.7 →
   **USD 711 billion tradable**.
3. Denominator = 2,840 + 711 = **USD 3,552 billion** (the
   "free float-adjusted market capitalization in Taiwan" of Q11).

**The simulated walk (May-2026):** target = 3,552 × 0.85 = **USD
3,019 billion**. Adding companies largest-first: Taiwan
Semiconductor alone reaches 43.7% coverage; ~rank 20 reaches
~70%; the target is crossed at **rank 135**, where the company's
full value is **USD 5.81 billion — the size line**, at exactly
85.0% coverage. Honesty: rank 135 lands in the MODELED body — the
nearest real members bracket the line (5871 at 6.08, 2615 at
6.44, 3293 at 6.49 just above). Sensitivity band: body float 0.5
→ line 6.79; body float 0.8 → 5.15; head floats ±10% → 5.22–6.08.
**Whole band sits inside MSCI's published May-2026 Emerging
Markets range (~3.9–9.1), the external consistency check.**

**On the website:** the "📐 Show the walk" panel (Step 1 page) now
displays all of this — the three step-cards (denominator, target,
size line), the denominator breakdown, the cumulative-coverage
curve with the 85% crossing marked, the honesty note with
bracketing real names, and the sensitivity table — closed with the
reproduction instruction so users can rerun the script and check
every number themselves. (This delivers the Q4 commitment.)

### Q13. Where do the 144 companies come from? Why default 0.7 float? Isn't $3,552B arbitrary — how do others calculate this, and what better float sources exist?

**Where the 144 come from (nothing arbitrary):** the union of
three defined sets — every current index member (from the
three-fund holdings pipeline), every company that appeared in any
official review change 2015–2026 (from the print-verified change
archive), and the boundary set — minus names delisted or unpriced
at the frame date. It is "every company that is, was, or plausibly
could be index-relevant," which is why it captures ≈ 80% of the
market's tradable value with 144 of ~1,800 listed names.

**Why 0.7 as the default float:** an assumption, honestly flagged
per-row wherever used, chosen as a typical mid-cap float and
sensitivity-tested (Q12: moving it 0.5–0.8 shifts the size line
5.15–6.79). It is the weakest input by design visibility — which
is why the better sources below matter.

**Is $3,552B arbitrary? MSCI's own factsheet says no.** The
official MSCI Taiwan factsheet (July 31, 2026, fetched live)
publishes: 77 constituents (EXACTLY our three-fund unanimous
count) and an index float-adjusted market capitalization of **USD
3,183 billion**. Since the index covers ~85% of the market, MSCI's
implied market denominator is 3,183 ÷ 0.85 ≈ **USD 3,745
billion** — our reconstruction of USD 3,552 billion sits within
≈ 5% of MSCI's own number, using only free data. Per-name check:
the factsheet lists TSMC's float-adjusted value at USD 1,848.5
billion; ours computes 1,935 × 0.912 ≈ 1,765 (−4.5%) — the gap is
the float estimate (MSCI's implied TSMC factor ≈ 0.955 vs our
0.912), not the price or shares. Arbitrary would mean unanchored;
this is anchored on three sides (MSCI's published range, MSCI's
factsheet cap, and the sensitivity band).

**How the professionals do it (looked up):** MSCI excludes
strategic holders — governments, corporations, controlling
shareholders, management — plus foreign-restriction effects, via
the Foreign Inclusion Factor (their float-adjustment framework,
documented in the methodology appendices and their float
research). FTSE, for the FTSE TWSE Taiwan series, has used ACTUAL
free float (rounded up to the next 1%) since March 2013 — the
banded shortcut era is over. Morningstar publishes its own float
calculation methodology in the same spirit. Common thread:
float = shares outstanding minus identified strategic blocks,
name by name — exactly the structure we approximate.

**Better float sources for Taiwan (upgrade queue, best first):**

1. **MSCI factsheet reverse-engineering (free, monthly):** the
   factsheet's top-10 float-adjusted values ÷ our full caps =
   MSCI's OWN implied float factors for the largest names —
   direct calibration against the ground truth we are trying to
   approximate.
2. **TDCC open data (free, weekly):** the central depository
   publishes the shareholding-dispersion table for ALL listed
   companies (holdings by size bracket) — large-block
   concentration is a strategic-holder proxy at full breadth.
3. **MOPS insider filings (free, monthly):** director/supervisor
   and 10%-holder balances — the literal strategic-holder list
   MSCI's definition names.
4. **Taiwan Index Plus / FTSE TWSE actual floats:** the
   exchange-affiliated index company applies actual free float;
   its constituent disclosures cross-check the same quantity from
   a second index-provider's eyes.
5. Current source (retained as base): per-company float from
   holder filings via public APIs, default 0.7 where unfiled.

### Q14. Can we find historical factsheets, and can the index cap number reverse-engineer the 85% threshold line?

**Finding history.** MSCI's factsheet URL always serves the CURRENT
month — history is not downloadable from MSCI. Two routes: (a) the
Internet Archive's Wayback Machine holds snapshots of that exact
URL across years — blocked from this working environment, but
checkable in any browser at
web.archive.org/web/*/https://www.msci.com/documents/10199/255599/msci-taiwan-index.pdf
— any snapshots found can be dropped into data/factsheets/ for the
parser; (b) CAPTURE-FORWARD, now running:
scripts/factsheet_capture.py fetches and parses the sheet monthly
into data/msci_factsheet_archive.json (July-2026 seeded — the same
pattern as the auction-snapshot archive: what cannot be
backfilled gets accumulated).

**What the number CAN reverse-engineer.** Index float-adjusted cap
÷ 0.85 = MSCI's implied market denominator for that month
(July-2026: 3,183 ÷ 0.85 ≈ USD 3,745 billion) — a monthly
ground-truth series for our walk's denominator, historically too
if Wayback snapshots exist. Better still: with the denominator
KNOWN, the coverage target in dollars equals the index cap itself,
so walking OUR member ladder until cumulative tradable value
reaches the published index cap recovers the REALIZED boundary —
which the factsheet also hands over directly as "Smallest
constituent" (July-2026: USD 1.84 billion float-adjusted; divide
by a float ratio for the full-value floor). And the top-10 rows
give MSCI's OWN implied float factors: float cap ÷ our full cap —
July-2026 extraction: MediaTek 0.905, Delta 0.754, ASE 0.750,
Elite Material 0.805, Fubon 0.603, CTBC 0.855, Accton 0.905 — the
free monthly float calibration from Q13, now implemented.

**What it CANNOT do.** The single cap number does not by itself
locate the FORWARD-LOOKING size line for the next review — that
still requires the walk over per-company values (the line is a
crossing point, not a ratio). What the factsheet does is anchor
the walk's denominator to MSCI's own number (retiring the modeled
body's guesswork month by month) and hand us the realized boundary
to grade the walk against. Prediction still walks; the factsheet
grades the walker.

### Q15. Can we animate the summation? Are the last-added companies the deletion candidates? Do we still need float ratios for all members — best source? And factsheet history beyond the Wayback Machine?

**The animation — built.** "Show the walk" now has an
"Animate the walk" toggle: press Play and companies join
largest-first (Taiwan Semiconductor first at 43.7%, then one by
one), the coverage line climbs, and the 85% line waits at the top;
the title names each arriving company with the running total.
Gray dots are the modeled body between real names.

**The reading — almost correct, one refinement.** The companies
added just BEFORE the line is crossed are the borderline
SURVIVORS — nervous, but in. The deletion candidates are current
members whose size places them AFTER the crossing — the market no
longer needs them to reach 85%. And the buffer applies: the
rulebook gives sitting members grace down to roughly two-thirds
of the cutoff before removal, so "after the line" means AT RISK,
with the deepest below-line names the likeliest deletions (May-26:
the seven deleted were the seven deepest).

**Float ratios — yes, still needed for every company in the
summation** (the walk accumulates float-adjusted values — Q11's
ordering). Best sources, ranked: (1) MSCI factsheet implied
factors — exact ground truth, but top-10 names only, monthly
(now captured automatically); (2) TDCC open data — the central
depository's weekly shareholding-dispersion table, ALL listed
companies, free: large-block concentration proxies the
strategic-holder exclusion; (3) MOPS insider/major-holder filings
(monthly, free) — the literal strategic-holder list; (4) Taiwan
Index Plus / FTSE actual floats as a second provider's estimate;
(5) holder-filing estimates via public APIs as the base layer.
Practical recipe: factsheet factors for the giants, TDCC+MOPS for
the middle, flagged defaults only where all else fails.

**Factsheet history beyond the Wayback Machine:** (a) SEC EDGAR —
fund prospectuses, annual reports and free-writing filings that
attach or restate MSCI index characteristics for their benchmark
(searchable full-text, free); (b) fund-distributor and private
bank archives that cached monthly factsheet PDFs (searchable via
the PDF's exact title); (c) institutional databases — Refinitiv
Datastream/Eikon and Bloomberg carry MSCI index market-cap and
constituent-count HISTORY as data series (the cleanest route if
CLSA access arrives — one query replaces the whole archaeology);
(d) academic access (WRDS) for the same series; (e) MSCI's own
end-of-day index search gives historical index LEVELS free — but
levels only, no caps, stated so nobody wastes an evening on it.
And regardless: our own capture-forward archive accumulates from
July-2026 onward.

### Q16. Can the latest factsheet predict the Global Minimum Size Reference for the August-2026 review — and do we still need floats for the remaining members?

**One structural correction first.** The official Global Minimum
Size Reference is GLOBAL: derived from the developed-markets
universe, then halved for Emerging Markets (Q2). The Taiwan
factsheet therefore predicts the TAIWAN cutoff; the global
reference is forecast separately — and the book already gave us
its May value ($15.75 billion, April-20 data), so the August
forecast is that number scaled by the developed-markets move to
MSCI's (unannounced) August price cutoff.

**The August forecast (data/aug26_gmsr_forecast.json):** scaling
$15.75B by the developed-markets proxy (+4.2%, banded ±2 points):
DM reference ≈ **$16.1–16.7B** → EM reference ≈ **$8.0–8.4B** →
EM range ≈ **$4.0–9.6B** — the deletion-relevant lower bound
rising ~4% from May's $3.94B. Our Taiwan cutoff estimates
($5.8–6.5B by frame) sit comfortably inside the forecast range.

**The float question — yes, and the factsheet delivers a
calibration nobody expected.** Per-name floats are still needed
for candidate-level decisions (the walk is float-adjusted). But
the factsheet PINS THE AGGREGATE: index float cap ($3,183B) minus
the published top-10 float sum ($2,443B) means the remaining 67
members' floats MUST sum to $739.8B. Our independent estimates
for those same 67 sum to **$719.0B — an aggregate calibration
factor of 1.029, within 2.9% of MSCI's own arithmetic.** So: the
top-10 get MSCI's exact implied factors, the residual members are
validated (and scalable) in aggregate, and per-name uncertainty
now lives only in the DISTRIBUTION across the 67, not their
total. That is the difference between "estimated floats" and
"estimated floats reconciled to the index provider's own sum."

### Q17. We tried the TDCC framework for all 77 members — the graded, honest result

**What was built.** The depository's weekly dispersion table
(July-31, same date as the factsheet — clean grading alignment)
gives, per stock, the share held by accounts with more than one
million shares ("bracket 15"). Recipe v1: treat bracket-15 as the
strategic-holder proxy, subtract the foreign-held share (foreign
institutions are float), and float = one minus the remainder.
Computed for all 77 members: data/tw_float_tdcc.json.

**The grade — v1 REJECTED as a replacement.** Against the eight
names where MSCI's own implied factors are known, the TDCC recipe
scored a mean absolute error of 0.143 versus 0.104 for our
incumbent estimates; on the aggregate constraint the recipe
summed the residual-67 to $670B versus the incumbent's $719B
against MSCI's implied $739.8B. Worse on both tests — so it does
NOT replace the incumbent, and a pinned test enforces that verdict
until a better version beats it.

**Why it failed — the diagnostic worth keeping.** Bracket 15
counts everyone with a million-plus shares: founders and
governments (strategic, correctly excluded) but ALSO domestic
mutual funds, ETFs, insurers and pension money — which are FLOAT.
The pollution is worst exactly where domestic institutions are
biggest: the financial holdings (Fubon: recipe 0.34 vs MSCI 0.60;
CTBC 0.56 vs 0.86). Size brackets cannot tell a founder from a
fund. What CAN: the MOPS insider/major-holder filings — the
literal strategic list, named not sized — which is the v2 recipe
(insider% + government stakes directly, TDCC relegated to a
change-detection signal). Recorded as the queued build; the null
is shipped, not shelved.

### Q18. Untangling the global reference vs the Taiwan line; confirming the two-sided boundary reading; and does estimated float weaken the backtest?

**The confusing paragraph, untangled.** There are TWO lines, not
one. Line one: the GLOBAL reference. MSCI runs the 85% walk once
on the combined developed-markets universe, publishes the result
($15.75 billion in the May-2026 book), and sets the
Emerging-Markets reference at exactly half. This global line
exists so a "large company" means roughly the same thing in every
country. Line two: the TAIWAN cutoff. Each market then gets its
own cutoff, chosen from Taiwan's own 85% walk but REQUIRED to
land inside the band built around the global reference (half of
it to 1.15 times it). So: the Taiwan factsheet helps us compute
line two; the methodology book hands us line one for free, and
forecasting its August value is just scaling the published May
number by how much developed markets moved since April.

**Your two-sided reading — deletion side right, addition side
needs two fixes.** Deletion: correct. Current members that the
85% walk no longer needs — the ones the walk passes AFTER
crossing the target — are deletion candidates, with the buffer
grace (down to roughly two-thirds of the cutoff) deciding how far
below before removal actually happens. Addition, fix one: the
primary test for an outsider is its FULL market capitalization
(price × ALL shares), not its float-adjusted value — float enters
as a secondary test (the tradable value must clear half the bar)
and as the 15% minimum-float gate, but the headline comparison is
full value against the line. Fix two: outsiders do not join by
merely CROSSING the line — entry is deliberately harder than
staying, requiring roughly one-and-a-half to two times the
cutoff depending on review type. One line, two unequal doors:
members fall out well below it, outsiders climb in well above it.
The gap between the two doors is the buffer zone where nothing
happens — by design, to stop churn.

**The backtest question — yes, floats are estimated, and here is
exactly why that does not quietly poison the results.** In the
point-in-time reconstructions, per-company float estimates are
today's values held constant (with defaults of 0.7 where unfiled,
flagged), because historical float vintages are not publicly
archived. That makes the LEVEL of the reconstructed line
uncertain — we measure this rather than deny it (the sensitivity
band: body float 0.5–0.8 and head floats ±10% move the May line
between $5.15B and $6.79B). Three design features keep the graded
conclusions safe anyway: (1) the delete-pool results rest on CAP
ORDERING, not the line's level — the seven May deletions were the
seven DEEPEST members by full value, and float error barely
reorders a full-value ladder; (2) pools are deliberately WIDE
bands, not point cuts, so line-level error widens a pool rather
than dropping a candidate; (3) the declared policy: any backtest
conclusion that FLIPS inside the float-sensitivity band is marked
FLOAT-SENSITIVE and excluded from headline accuracy. Where float
error genuinely bites is the cutline — WHICH borderline member
survives — and that is precisely our stated miss class
(1101/1326/2207 in May), now being attacked from the other side
by MSCI's own implied factors and the aggregate reconciliation
(Q16). Estimated floats make the line fuzzy; they do not make the
ordering wrong — and the grading separates the two honestly.

### Q19. The MOPS v2 (named-insiders) float estimator — built, graded, ADOPTED

**The build.** MOPS itself is unreachable from this working
environment, but the same filings-derived quantity — the
percentage held by NAMED insiders (directors, officers,
controlling holders) — is served through Yahoo's data feed, which
is reachable. Recipe: float = one minus the insider percentage,
computed for 76 of the 77 members (one TPEx name unresolved,
listed). File: data/tw_float_mops_v2.json.

**The grade — a decisive win.** Against the eight names with
MSCI's own implied factors: mean absolute error **0.022**, versus
0.104 for the incumbent estimates and 0.143 for the rejected TDCC
v1 — five times more accurate. Per name it is almost eerie:
Fubon 0.593 vs MSCI's 0.603, Elite Material 0.810 vs 0.805, ASE
0.757 vs 0.750, Delta 0.741 vs 0.754. The residual-67 aggregate
lands at $770B vs the implied $739.8B (+4%, vs the incumbent's
−3%) — comparable in aggregate, transformed per-name.

**Why v2 succeeds where v1 failed:** it subtracts holders BY NAME
(the founder, the family, the parent company), not by size
bracket — so domestic funds and insurers, which are float, are no
longer miscounted as strategic. Exactly the fix Q17's diagnosis
prescribed.

**The stated residual:** government stakes without insider
classification escape the table — TSMC comes out at 1.00 vs
MSCI's 0.955 (the development-fund stake), CTBC 0.92 vs 0.855.
In production this residual barely matters because the stack is
layered: **MSCI's exact implied factors for the top-10 (covering
TSMC), v2 insiders for the rest, flagged defaults only as last
resort.** Note on scope: float estimates affect the
FLOAT-ADJUSTED values (the walk's denominator and index weights);
full market capitalizations — price times shares — are untouched
by this change.

**Verdict: ADOPTED for the live float layer** (pinned by test;
graded historical frames keep their stated float policy so
past grades are not silently rewritten). Next wiring: feed the
layered stack into the live Aug-2026 walk and workbench.

### Q20. Interpreting the v2 result end-to-end — best method? Aug-2026 numbers? total market value? why the accuracy despite estimation? and can rules alone predict Aug-2026?

**Did v2 improve the float estimate?** Yes, decisively: mean
absolute error 0.022 against MSCI's own implied factors, versus
0.104 for the incumbent — five times better. **The methodology in
one sentence:** subtract the shares held by NAMED strategic
parties (directors, officers, controlling holders, from company
filings) instead of guessing from holder-size brackets — names
distinguish a founder from a fund; sizes cannot.

**Is it "the best way"?** Precisely stated: it is the best
ESTIMATOR we have tested where MSCI's truth is unavailable — and
the production stack is better still, because it is layered: for
the ten largest names we use MSCI's own implied factors from the
factsheet (no estimation at all), v2 for the remaining members,
flagged defaults only as a last resort. Two bounds on confidence:
the grading set is eight names, and government stakes without
board seats escape the insider table (the TSMC/CTBC residual).

**The Aug-2026 numbers (live frame, v2-layered floats):** the
GLOBAL Emerging-Markets reference forecast is UNCHANGED at
**$8.0–8.4 billion** — it is derived from developed markets and
no Taiwan float work touches it. The TAIWAN line, recomputed with
the upgraded floats and current prices: **$6.74 billion**
(crossing at rank 115), inside the forecast global band, with a
17-name inclusive delete pool. Cross-checks: our members' float
sum $3,301B vs the factsheet's $3,183B (+3.7%, prices have moved
since July 31); denominator $4,197B vs the factsheet-implied
$3,745B at July-31 prices.

**Total Taiwan market value, estimated:** named names $3,958B
full value + modeled body $1,016B ≈ **$4,974 billion (≈ five
trillion US dollars)**. The upgrade route remains Q10's: replace
the modeled body's total with the exchange's official aggregate
market value (published monthly) — measurement over modeling.

**"High accuracy despite estimated floats because MSCI allows a
wide band" — partially correct; the full answer has three legs.**
(1) Yes, the buffers mean small float errors rarely flip a
decision — your point, and it is real. (2) The decisions ride
mostly on FULL-capitalization ORDERING, which floats do not touch
at all — May's seven deletions were the seven deepest by full
value. (3) And now the float estimates themselves are validated
to 0.022 against MSCI's own numbers — so the remaining error is
small even before the band protects it. The band is the third
line of defense, not the only one — and the May cutline misses
(survivors we called deletions) prove the band alone is not full
protection.

**Can rules + factsheet + good floats predict Aug-2026 WITHOUT
historical training?** The honest split: the mechanical layer —
rules faithfully implemented on current data — gets you the
CANDIDATE SHEET, and May-2026 proved that layer alone is
powerful (the seven deletions were exactly the ladder's bottom
seven). But four things only history provides: (1) CADENCE —
which review type does what; our worst-ever error (ten false
deletions at August-2025) came from applying semi-annual sweep
logic at a quarterly review, a mistake no rulebook paragraph
flags loudly; (2) DISCRETION CALIBRATION — how often borderline
members actually survive (the ~two-thirds conversion rate), which
turns lists into probabilities; (3) THE BLIND BAND — history
tells us 13 of 21 recent Taiwan changes originated below the
visible floor, so a "zero visible candidates" read must ship with
a declared blind probability, not confidence; (4) PROOF — without
grading against past reviews we would never KNOW the
implementation is faithful. So: rules alone can name the
candidates for August; history is what makes the call calibrated,
probabilistic, and trustworthy — and for August specifically,
where the visible margin shows zero adds, the historical layer IS
most of the remaining signal.

### Q21. The Taiwan cutoff, walked through once more — and the honest history of the four lessons

**How the cutoff for a country index is set, in five steps.**
(1) GLOBALLY: MSCI runs the 85% coverage walk on the combined
developed-markets universe and publishes the resulting size — the
Global Minimum Size Reference ($15.75 billion in May-2026); the
Emerging-Markets reference is set at exactly half (~$7.9
billion). This global anchor exists so "large company" means
roughly the same thing everywhere. (2) The reference spawns a
RANGE: half of it to 1.15 times it (May-2026 Emerging range:
~$3.9–9.1 billion). (3) LOCALLY: Taiwan's own 85% walk — line up
Taiwan's investable companies largest-first, accumulate freely
tradable value, stop at 85% of Taiwan's total — proposes Taiwan's
cutoff, and the rule is that this cutoff must land INSIDE the
global range (if the walk says otherwise, the cutoff is pulled to
the range boundary and the member count adjusts instead). Our
current live estimate: ~$6.7 billion, comfortably inside. (4) The
cutoff then gets BUFFERS: sitting members are safe down to
roughly two-thirds of it; newcomers must clear roughly
one-and-a-half to two times it. (5) Every review, all of this is
recomputed at MSCI's chosen price date and membership is
reassessed through those buffered doors.

**The four lessons, told as the mistakes and near-mistakes they
were:**

**1. Cadence — a genuine error, our worst.** Reviews come in two
flavors: the comprehensive semi-annual ones (May, November),
where MSCI historically executes the migration sweep that moves
weakened members down to Small Cap, and the lighter quarterly
ones (February, August). Our engine originally applied the sweep
logic at EVERY review. Backtesting August-2025 — a quarterly —
it confidently deleted ten members. The official result: two
deletions, neither of them ours. Ten false calls from one wrong
assumption about WHEN a rule fires, not WHAT the rule is. The
rulebook describes both review types but never shouts "the sweep
concentrates at semi-annuals" — that frequency is an empirical
regularity (62–90% of deletions across our decade key happen at
semi-annuals). Fix: a structural cadence gate — sweep logic arms
only at semi-annual reviews. Re-run: zero false deletions;
cross-validated on February-2026.

**2. Discretion calibration — learning that our false positives
were EARLY, not wrong.** At November-2025 the engine flagged nine
members as deletion-risk. Same-review result: none of the nine
deleted (that review's real deletions were elsewhere — see lesson
3). A naive grader calls that nine misses. Then May-2026
arrived: six of those nine were deleted. The pattern across the
decade: roughly TWO-THIRDS of names entering the danger zone are
eventually removed, but often one or two reviews later, and the
survivors are repeat "cutline residents" (the same three names —
1101, 1326, 2207 — survived our May call too, on MSCI's private
float arithmetic). The lesson: a flag is not a call; it is a
probability. The engine now attaches the measured conversion rate
instead of shipping certainty — that is exactly what "the ~2/3
that turns lists into probabilities" means.

**3. The blind band — the humbling one.** The same November-2025
re-grade showed something worse than early flags: the seven
ACTUAL deletions overlapped our nine flags ZERO times, because
every one of them sat below the sixteen names our universe
tracked by name. Counting the decade: 13 of 21 recent Taiwan
changes originated below that visible floor. Any "zero
candidates" statement from a partial universe is not a forecast —
it is a statement about our eyesight. Fix, two layers: honesty
first (every no-change call ships with a declared blind-band
probability — the decade says ~2 changes typically live below the
floor), then structure (the fund-holdings ladder now prices ALL
members, and the November-2025 replay on that full ladder catches
7 of 7 — the blindness is structurally gone for the delete side,
and the declared-blind-share discipline remains for what still
is not visible: never-before-seen newcomers).

**4. Proof — the meta-lesson underneath the other three.** Every
one of the above was discovered ONLY by grading predictions
against official outcomes. The cadence error looked like a
working engine until August-2025 was graded. The early-flag
insight required grading the SAME names across TWO reviews. The
blind band was invisible until the official November list was
compared against our floor — and that grading also exposed that
our earlier reconstructed answer keys were themselves wrong (the
old detector had found only 2 of 13 changes; conclusions built on
it had to be re-graded against the official archive). An engine
that is never graded against history can be wrong in all three
ways at once while looking confident. That is why every rule in
the system traces to a graded mistake, every probability to a
graded record, and why August-11 will grade everything currently
on the site — including the zero.

### Q22. The August-2026 cutoff, calculated end-to-end — and the candidates it proposes

**Step A — the global reference** (every number sourced): the May
book published the developed-markets reference at $15.75B
(April-20 data); developed markets moved ≈ +4.2% since (three-
month proxy) → August developed reference ≈ **$16.41B** → the
Emerging-Markets reference is half: **$8.21B** → the allowed
range for any emerging market's cutoff: 0.5× to 1.15× =
**$4.10–9.44B**.

**Step B — Taiwan's own walk** (v2-layered floats: MSCI's implied
factors for the top-10, named-insider estimates elsewhere,
flagged defaults last): named universe $3,486B tradable + modeled
body $711B = denominator **$4,197B**; target = 85% =
**$3,568B**; the walk crosses at rank 115, full value **$6.74B**.

**Step C — the cutoff and its doors**: $6.74B sits inside the
global range (no bound applied) → **cutoff $6.74B**; August is a
QUARTERLY review so the add bar is 1.8× = **$12.14B**; member
grace extends down to 2/3 = **$4.50B**; the watch band tops out
at 1.15× = $7.75B.

**ADD candidates — with the reason for each verdict** (real
floats fetched for every name; the default-0.7 verdicts were
refused and recomputed): **2408 Nanya Technology — QUALIFIES
STRONGLY**: $34.4B full value = 2.83× the bar (3.99× even under
the conservative boundary-frame bar), real float 0.456 (parent
Nan Ya Plastics holds 54.4%, by name) → tradable value 2.58× the
half-bar, foreign room 88%, deleted February-2025 so the one-
review churn buffer has expired — the memory-cycle rally built a
textbook re-add. **2344 Winbond — qualifies (moderate)**: 1.48×
bar, float 0.69. **8046 Nan Ya PCB — qualifies (marginal)**:
1.51× bar but float 0.381 leaves its tradable value only 1.15×
the half-bar — one float-estimate error from blocked. And the
framework's proof-by-counterexample: **6505 Formosa Petrochemical
— BLOCKED**: 1.71× the bar on size, but 88% insider-held → float
0.12, under the 0.15 floor — which is exactly why size alone has
never re-added it. 8299 Phison sits 8% below the bar: first
riser to watch.

**DELETE candidates — and why the honest probability is LOW for
August itself**: nine members sit below the cutoff (deepest:
6919 at 0.73×, 2834/2609 at 0.81×, 1101 at 0.84×, 3529, 5871,
3533, 8069, 3293 near 1.0×) and eight more in the 1.0–1.15×
watch band. But August is a quarterly: the migration sweep that
executes deletions is historically a semi-annual event (62–90%
of decade deletions) — so this pool is primarily the
NOVEMBER-2026 semi-annual watchlist, carrying the ~2/3 eventual-
conversion rate, not an August call. Decade base for August
reviews: changed 7 years of 11, median ~2 names, typically
below-visible or corporate-event driven — the declared blind
band stands.

**Governance, stated:** the LOCKED August registry call (zero
visible adds + probabilistic shortlist, from the boundary-frame
engine that cannot see 2408) remains the call of record. This
full-ladder result is the SHADOW engine's call — declared
today (T-6), timestamped, published beside the locked call so
that August-12 grades BOTH honestly. If 2408 is added, the
shadow frame earns primacy; if not, we learn what the mechanical
read still misses.

### Q23. Every number in the August cutoff, source by source

**Why May's $15.75B × 1.042 — and where 1.042 comes from.** MSCI
recomputes the global reference at every review by re-running the
developed-markets walk at their chosen price date. We cannot run
that walk (it needs thousands of global names), but the reference
moves roughly in proportion to the developed-markets' total
value. So we take the reference MSCI PUBLISHED for May ($15.75
billion, April-20 prices — the book's own worked example) and
scale it by how much developed markets rose between that date and
the August price window. The +4.2% comes from the factsheet's own
performance table: the broad all-country index's three-month
return as of July 31. It is a proxy, not the exact universe —
which is why the calculation carries a ±2-point band ($16.07 to
$16.73 billion) rather than pretending precision.

**Why halve it — yes, exactly your reason.** The rulebook states
the Emerging-Markets reference is set at ONE-HALF the developed-
markets reference (§2.3.2.1, p.24–25), and MSCI classifies Taiwan
as an Emerging Market (their market-classification framework —
economics aside, that is their bucket for Taiwan). So Taiwan is
judged against $16.41 ÷ 2 = $8.21 billion.

**The allowed range.** Also straight from the book (§2.3.2,
p.24): the reference spawns a range of 0.5× to 1.15× around it —
$8.21 × 0.5 = $4.10 billion to $8.21 × 1.15 = $9.44 billion. Any
emerging market's own cutoff must land inside this corridor.

**The denominator $4,197B.** Taiwan's total freely-tradable value,
built bottom-up: the 150 tracked companies at current prices —
each one price × total shares × its float factor (MSCI's implied
factors for the top ten, named-insider estimates for the rest) —
summing to $3,486 billion; plus the modeled 400-company mid-cap
body at $711 billion tradable. 3,486 + 711 = 4,197.

**The target $3,568B.** Simply 85% of the denominator: 4,197 ×
0.85 = 3,568 — the dollar amount of tradable value the index must
contain (Q11's step three).

**"Crossing at rank 115, $6.74B."** Sort every company (tracked
and modeled) largest-first. Add their tradable values one by one.
The running total reaches $3,568 billion while adding the 115th
company; that company's FULL market value — price × all shares,
not float-adjusted — is $6.74 billion. That is where the walk
stops: the raw size line. (Rank 115 counts modeled body names
too; the crossing itself sits in the modeled body, bracketed by
real members — the Q12 honesty note.)

**The final cutoff $6.74B.** One last check: the raw crossing
must sit inside the corridor from step three. $6.74 is between
$4.10 and $9.44, so no adjustment is applied and the cutoff IS
the crossing. Had the walk landed outside, the cutoff would be
clamped to the corridor's edge and the member count would flex
instead — that rule simply did not bind this time.

### Q24. The denominator challenged — MSCI's definition, why 150+400, and the better number that was hiding in plain sight

**MSCI's definition of the denominator** (GIMI §2.2 and §2.3.5):
the free float-adjusted capitalization of the Market INVESTABLE
Equity Universe — every Taiwan security that PASSES the
investability screens (minimum size, float ≥ 0.15, liquidity,
foreign room), valued at price × shares × float factor. It is
NOT the whole listed market: sub-screen names are excluded. So
$4,197B never claimed to be "Taiwan's total market cap" — it was
our estimate of the investable, tradable subset (the full-value
analog was ≈ $4,974B; the whole listed market including
sub-screen names is larger still).

**Why 150 tracked + 400 modeled:** the 150 are every company
that is, was, or plausibly could be index-relevant; the 400 are
a stand-in for the investable mid-caps we do not price by name,
disciplined only by the member-count anchor. That body was the
weakest link — which is exactly what the challenge exposed.

**The better estimate — accepted, and it was in the factsheet all
along:** MSCI's own arithmetic inverted. Index float cap ÷ 0.85 =
**$3,745B** (July-31) IS MSCI's denominator, by construction, at
the same price vintage as our caps. Our bottom-up $4,173B runs
**+11.4% above it** (body guesswork + float estimation +
residual gaps). Verdict: the MSCI-implied number is ADOPTED as
denominator-of-record; the bottom-up build survives as the
cross-check that catches factsheet staleness. (The truly
independent third source — the exchange's official monthly
aggregate — remains queued; today's endpoints served trade
values, not caps.)

**What re-running the walk on the better denominator revealed —
the deeper lesson:** an 11% denominator change moved the raw
crossing from $6.7B to **$11.2B**, because the cumulative curve
is nearly FLAT in the tail — the crossing point is
ill-conditioned. MSCI's own procedure absorbs exactly this with
slack our point-estimate hid: the coverage target is an AREA
(85% ± 5%), the cutoff lives in the global corridor, and buffers
retain members far below it. Practical consequence, now policy:
**candidate verdicts must hold under BOTH frames; only
frame-robust verdicts ship as calls.** Applied: 2408 Nanya
remains STRONG (2.84× and 1.71× the bar across frames — robust);
2344 Winbond and 8046 drop to FRAME-SENSITIVE — declared, not
called. And the MSCI-implied frame adds a structural argument:
under MSCI's own denominator the top ~54 companies already
deliver 85% coverage, which is pressure for the review to ADD
the large outsiders — the Nanya call got STRONGER under the
better number, not weaker.

### Q25. Computing the investable universe EXACTLY — feasibility and the census run

Assessed by building it: entirely feasible with free data; the
cost is breadth, not access. `scripts/mieu_census.py` censuses
all ~2,146 TWSE/TPEx common equities, applies the GIMI screens
(size, float ≥ 0.15, 12m and 3m traded-value ratios ≥ 15%,
trading frequency ≥ 70%), and sums float-adjusted values — ~75–90
unattended minutes, resumable at every step. Success test: land
near the factsheet-implied $3,745 billion. The pilot (50 names)
validated the plumbing; the full run is handed off to run
locally — instructions, reading guide, and the follow-up queue
are in **docs/MIEU_CENSUS_HANDOFF.md**. Result will be recorded
here as the next entry when the census returns.

### Q26. Step 2 worked example — May-2026: the changes, and exactly how "accumulated pre-positioning ÷ expected passive flow" is computed

**The May-2026 changes** (announced May 12, effective at the
May 29 close): one addition — 6223 MPI Corporation (TPEx) — and
seven deletions: 1102 Asia Cement, 1402 Far Eastern New Century,
1504 TECO Electric, 2324 Compal Electronics, 2474 Catcher
Technology, 2610 China Airlines, 2633 Taiwan High Speed Rail.

**The calculation, step by step (worked on 2474 Catcher):**

1. **Baseline daily volume.** Take the 60 trading days BEFORE the
   announcement and use the median daily volume — the stock's
   normal day. Catcher: 2,680,237 shares. (Median, not mean, so
   one freak day cannot distort "normal.")
2. **Expected passive flow.** How much must trade at the
   effective close? Measured from prior Taiwan events (before
   May — so usable without peeking): deletion prints run about
   16× a normal day, additions about 8×. Catcher's expected
   passive flow = 16 × 2,680,237 ≈ **42.9 million shares**.
3. **Accumulated pre-positioning.** For each trading day from the
   announcement (May 12) through the day before effective
   (May 28 — the point-in-time cutoff), take that day's volume
   MINUS the baseline — the ABNORMAL part, floored at zero — and
   add it all up. This cumulative excess volume is the footprint
   of arbitrageurs building inventory: every share the passive
   funds must sell at the close needs a buyer, and the buyers
   accumulate during the window; their activity shows up as
   volume above normal. Catcher's window accumulated ≈ **72.9
   million abnormal shares**.
4. **The ratio.** 72.9M ÷ 42.9M = **1.70** — the market had
   already pre-traded 170% of the expected passive flow before
   the effective day. Above the declared 1.2 threshold →
   OVERCROWDED.

**The full May table** (announcement May-12 → frozen May-28):

| Stock | Side | Baseline ADV | Expected flow | Completion | Foreign Δ | Scenario | Realized print |
|---|---|---|---|---|---|---|---|
| 1102 | del | 9.10M | 145.6M | 0.39 | −1.78pp | BUILDING | 21.7× |
| 2474 | del | 2.68M | 42.9M | **1.70** | −2.56pp | OVERCROWDED | 24.8× |
| 2610 | del | 29.8M | 476.6M | 0.17 | −0.08pp | UNDERSUPPLIED | 9.9× |
| 2324 | del | 35.1M | 561.0M | **2.04** | **+2.85pp (wrong-way)** | OVERCROWDED | 19.9× |
| 1402 | del | 14.5M | 231.6M | 1.65 | −0.93pp | OVERCROWDED | 22.8× |
| 2633 | del | 5.29M | 84.6M | 0.91 | −1.14pp | WELL-SUPPLIED | 41.7× |
| 1504 | del | 9.59M | 153.4M | 0.49 | −0.19pp | BUILDING | 18.4× |
| 6223 | add | 1.32M | 10.5M | 0.31 | +0.42pp | BUILDING | 5.9× |

**Why abnormal volume proxies positioning — and its stated
limit.** Volume is anonymous and two-sided: the excess includes
noise traders and momentum money, not only arbitrageurs. That is
why the ratio never stands alone — the corroborating legs
(foreign-holding direction, securities-lending balances, retail
shorts) confirm WHO is accumulating. The May table shows the
system at work: 2324's completion of 2.04 came WITH wrong-way
foreign flow (foreigners BUYING a deletion, +2.85pp) — the
compound signature (registry H16) — and 2324 delivered the +28%
reversal. 2610's 0.17 completion (thin pre-positioning) preceded
the smallest print of any deletion (9.9× vs 18–42×): nobody had
inventory to unwind, so the close stayed small.

### Q27. Where do the 16× (deletes) and 8× (adds) multiples come from?

**They are measured, not theoretical.** For every past MSCI Taiwan
change we hold tape for, we computed the same ratio the model
uses: effective-day total volume ÷ that stock's pre-announcement
baseline (60-day median). The class MEDIANS across those measured
pre-May events came out ≈ 16× for deletions and ≈ 8× for
additions — our own empirical priors, from our own event
measurements (the same method later produced Japan's measured
10.0× / 7.7×, which differ from Taiwan's exactly as Japan's
bigger baseline tapes predict). Nothing in the rulebook and
nothing from MSCI supplies these numbers.

**Why deletions print RELATIVELY bigger than additions:** a
deletion candidate is a shrunken company — its price and its
daily liquidity have both fallen, but index funds must still
dump the full position, so the forced flow is huge relative to
its withered normal day. An addition is usually a rising,
increasingly liquid name — big absolute flow, smaller multiple
of its already-large normal day. The auction data shows the same
asymmetry from another angle: deletions' closing prints ran
60–91% of their whole day's tape; additions only ~7–51%.

**The honest error bar — this is the model's weakest input,
stated as such from day one:** realized May-2026 multiples ran
9.9× to 41.7× against the 16× prior, and the decade panel shows
the multiple itself DEPENDS on crowding (bucket means 8.3× to
21.1×) — which is precisely why the model's real output is the
crowding-conditioned read, not the raw prior. The prior is the
denominator's scale-setter; per-name error in it propagates
one-for-one into the completion ratio, which the scenario BANDS
(not point estimates) are designed to absorb.

**The cross-check that exists when needed:** expected flow can
also be built first-principles — index weight × tracking assets ÷
price — but that route imports its own uncertain estimate
(tracking assets). The measured multiple folds realized demand
AND realized supply behavior into one observed number; the two
routes can be reconciled per name when a call is close.

### Q28. The 16×/8× critique accepted — the per-stock forced-flow model, the literature behind it, and the graded upgrade

**The critique is right.** A class median is a SCALE prior, not a
model: it ignores that forced flow is a per-stock quantity
determined by ownership structure. The "must print 16×" phrasing
overstated a crude average.

**The correct per-stock model.** What must trade at the close is
the passive complex's HOLDING of the stock:

    forced_shares = Σ over benchmarks (AUM_b × weight_of_stock_b) ÷ price
                  ≈ λ × float_shares

where λ is the fraction of the stock's freely tradable shares
held by index-tracking money — per-stock inelastic demand. The
academic name for exactly this object is **Benchmarking
Intensity** (Pavlova & Sikorskaya, Review of Financial Studies
2023): a stock's cumulative weight across benchmarks, weighted by
assets following each. The index-effect literature around it:
Shleifer (1986) and Harris & Gurel (1986) established
demand-curve price effects at S&P inclusions; Petajisto (2011)
quantified the index premium's hidden cost; Greenwood (2005) the
Nikkei-redefinition natural experiment; Duffie (2010)
slow-moving-capital framing; Chen–Noronha–Singal (2004) the
add/delete asymmetry. Implied multiple per stock:
forced_shares ÷ ADV = λ × (float_shares ÷ ADV) — λ times the
stock's FLOAT-TURNOVER DAYS. The constant-16× model is the
special case where every stock has the same float-days — which
is false, and that falseness is the critique.

**Graded on our tape (77 deletions, 31 events, 2015–2026,
data/perstock_flow_model.json):** fitted λ = **0.093** — about
9.3% of a Taiwan deletion's float is forced through the print, a
measured benchmarking-intensity proxy for Taiwan and an
economically sensible passive-ownership share.
corr(log float-days, log realized multiple) = **0.671**
(0.645 event-clustered). Mean absolute error: **7.8× vs 12.1×
for the constant** — a 36% improvement. ADOPTED as the v2
expected-flow for deletions (adds pending the same treatment;
λ to be re-fitted annually as passive share grows; saturation
visible at extreme float-days — 2633 predicted 69× vs realized
42×, stated).

**The residual is the crowding signal — the elegant part.** The
names that printed far ABOVE their passive-only prediction in
May were exactly the OVERCROWDED ones: 2324 predicted 8.2×,
realized 20.2×; 2474 predicted 13.6×, realized 23.1× — the
excess over forced passive flow is the arbitrage inventory
unwinding through the same print. Model v2 therefore separates
cleanly: **passive base = λ × float-days (structural), excess =
positioning (the Step-2 read)** — the two components the old
constant conflated.

### Q29. Understanding the per-stock forced-flow model, from first principles

**The question it answers:** when a stock is deleted, exactly how
many shares MUST be sold at the effective close?

**Step 1 — who must sell, and how much each holds.** Every index
fund tracking a benchmark that contains the stock holds it in
proportion to its weight: a fund with assets AUM holds
AUM × weight dollars of the stock, which is AUM × weight ÷ price
SHARES. On deletion day the fund's target weight goes to zero, so
it must sell its ENTIRE holding — no discretion, that is what
"passive" means. Sum this over every benchmark containing the
stock (the Emerging-Markets index, the country index, the
composite variants) and you have the total forced sale:
forced_shares = Σ (AUM_per_benchmark × weight_in_it) ÷ price.

**Step 2 — the simplification, and why it is exact rather than
lazy.** A float-weighted index sets each member's weight as its
tradable value over the index's total tradable value:
weight = (float_shares × price) ÷ index_float_value. Substitute
into step 1 and the PRICE CANCELS:

    shares held by one fund = float_shares × (AUM ÷ index_float_value)

The bracket — assets tracking the index divided by the index's
tradable value — is the SAME NUMBER for every stock in that
index. Call it λ. The identity says: an index fund holds the same
FRACTION of every member's tradable shares. Summing across all
tracking funds: forced_shares = λ_total × float_shares. That is
the whole model — passive money is a fixed co-ownership stake in
every member's float, and deletion forces that stake through the
exit in one day.

**Step 3 — what λ means and what we measured.** λ is the passive
complex's collective ownership share of members' float. Fitted on
77 Taiwan deletions across 31 events: **λ ≈ 0.093** — index-
tracking money holds roughly 9.3 cents of every tradable dollar
of a Taiwan member. One mental image: the index funds are a
consortium that co-owns 9.3% of every member's tradable shares;
when a name is expelled, the consortium's whole stake must find
new owners at one closing auction.

**Step 4 — from shares to the volume multiple.** Divide by the
stock's normal day: multiple = λ × (float_shares ÷ ADV) = λ ×
float-turnover-days. Worked on Catcher (2474, May-2026): float
≈ 393 million shares; × 0.093 → ≈ 36.5 million shares forced;
÷ 2.68 million normal day → **≈ 13.6× predicted** (realized
23.1× — the excess above the passive base being the arbitrage
inventory unwinding, the Step-2 crowding read). The old constant
16× is what this model becomes if every stock had identical
float-days — they don't, which is why the per-stock version cut
the error by 36%.

**Step 5 — what the academic paper adds.** Pavlova & Sikorskaya's
Benchmarking Intensity is the general version of λ when stocks
belong to DIFFERENT benchmark sets with different followings
(then λ varies per stock — their Russell 1000/2000 setting), and
their cutoff evidence establishes that this demand is truly
INELASTIC — the funds trade regardless of price, which is
precisely why the desk gets paid to supply the other side.

### Q31. If the safest agency execution is all-MOC, wouldn't every desk produce the same result? Where do desks actually compete?

**The premise is right — and it defines the commodity floor.** A
pure tracker benchmarked to the close, executed 100%
market-on-close, receives exactly the closing price at any desk.
Zero tracking error by construction, zero skill differential.
That slice of the business is a commission commodity, priced in
fractions of a basis point. If that were the whole business,
desks would be interchangeable. Five things make them not:

1. **Risk transfer — the real product.** Clients often do not
   want agency-MOC; they want a GUARANTEED close (the desk
   commits to deliver the closing price as principal, absorbing
   auction risk: imbalance, partial fills, limit-locks) or they
   auction blind program baskets to competing desks bidding in
   basis points. Pricing that risk correctly IS the competition —
   and it requires exactly the Step-2 analytics: expected print
   size (the per-stock forced-flow model), crowding state, the
   compound reversal signature. A desk that misprices bids too
   tight and eats losses, or too wide and never wins flow.
2. **Netting and internalization.** A desk holding BOTH sides
   (one client's deletion sell, another's benchmark buy, a
   liquidity provider's standing interest) crosses internally —
   price improvement for clients, spread capture for the desk.
   Flow begets flow: the desk that wins more baskets nets more,
   quotes tighter, wins more. All-MOC-to-exchange has no such
   effect.
3. **The close is not operationally identical across desks.**
   Taiwan's close is a call auction with real failure modes: a
   deletion locked limit-down does NOT fill your
   market-on-close order — then residual handling (T+1 strategy,
   the limit-move playbook) separates desks brutally. Order
   type, entry timing in the 13:25–13:30 window, and imbalance
   reading (the 5-second indicative feed) all differ.
4. **Not every client is a pure tracker.** Benchmarked actives,
   transition managers, and broadest-index trackers have
   discretion — for them, scenario-conditioned execution
   demonstrably beats all-MOC (the May-2026 OVERCROWDED names:
   the playbook split beat the close by ~590 basis points via the
   deferred leg). Desks compete on the quality of that ADVICE and
   on proving it afterward (TCA).
5. **Winning the order in the first place.** Baskets are awarded
   BEFORE effective day, largely on research quality: prediction
   of the changes, expected-flow analysis, crowding color. The
   desk that tells the client on announcement day exactly what
   will trade and how the close will behave wins the mandate —
   execution merely has to not fumble what research won.

**The map to our platform is one-to-one:** Step 1 wins the
mandate, Step 2 prices the risk transfer, Step 3 handles the
auction and its failure modes, Step 4 proves the value and
retains the client. The commodity slice (pure agency MOC) is
real but thin; everything the platform builds lives in the four
places above where desks genuinely differ.

### Q32. Where does crossing come from if flow is one-way? — and the limit-lock case study, 2015–2026

**Part 1 — the crossing question.** Correct: TRACKER flow is
one-way per name (an addition means every tracker buys). The
other side comes from five places: (1) the LIQUIDITY PROVIDERS —
the desk's hedge-fund clients who accumulated the addition
during the window are SELLING it at the close; a desk serving
both client types crosses tracker buys against arbitrageur sells
in the same name — that IS the canonical cross; (2) SEGMENT
MIGRATIONS — a Standard addition is often a Small-Cap DELETION,
so broad-index (IMI) trackers hold it already while Standard
trackers buy: genuinely opposite passive flows in the same stock
on the same day; (3) CALENDAR DIFFERENCES — FTSE and MSCI
rebalance on different dates, and capped-variant reweightings
can point opposite to the parent index; (4) OPPORTUNISTS —
active managers and transition desks deliberately use the
liquidity event to enter or exit positions they wanted anyway;
(5) the desk's own PRINCIPAL book (guaranteed-close inventory).
Honest quantification: name-level crossing is PARTIAL — the
residual imbalance is exactly what the auction prints — but the
slice that can be crossed is the profitable slice.

**Part 2 — the case study (data/limit_lock_study.json).** Every
index-change name's effective-date close screened for limit
locks, 2015–2026 (~140 name-events):

| Event | Stock | Side | Eff-day | Verdict | T+1 | T+2 |
|---|---|---|---|---|---|---|
| Feb-15 | 2615 Wan Hai | add | +7.0% | LIMIT-UP locked (7% era) | −2.0% | −3.3% |
| May-15 | 1789 ScinoPharm | del | −6.9% | LIMIT-DOWN locked (7% era) | +1.1% | −2.3% |
| Nov-15 | 4174 OBI Pharma | add | +9.9% | presumed limit-up (=10% cap; delisted, OHLC unverifiable) | +6.2% | +3.6% |
| May-26 | 2324 Compal | del | +9.6% | NOT locked (close 36.70 vs high 36.85) | +9.9% | +20.8% |

**Findings.** (1) **Rarity is the headline**: three locks in
twelve years, ALL in 2015 — zero locked effective closes
2016–2026. Wider limits (10% since June-2015) plus fully
anticipated flows plus pre-positioned supply (the Step-2
mechanism) have made the classic lock nearly extinct for Taiwan
index names. (2) The n=3 outcomes are anecdotes and pinned as
such: the locked-up add REVERSED next day (stuck buyers got
better prices), the locked-down deletion bounced mildly, the
mania add continued. (3) **The modern tail risk is the SQUEEZE,
not the lock**: Compal — a deletion closing +9.6% UP on its own
deletion day and running +20.8% by T+2 — is what replaced it.
For agency client sells a squeeze is a gift (better exit); for a
guaranteed-close desk pre-hedged short it is the loss scenario —
which is why the compound crowding signature (H16) is now the
monitoring priority, with the limit-move playbook retained for
corporate-event days and thin TPEx names where locks remain
possible.

### Q33. CLSA is agency-only — verified. Does that mean undifferentiated MOC commodity execution?

**The claim, checked:** confirmed — CLSA positions itself as
Asia's largest AGENCY-ONLY equity brokerage, "unconflicted since
1986": no proprietary trading, no market making, no banking
conflicts; execution services (portfolio/program trading,
electronic, high-touch) are pure agency. One nuance for
completeness: the parent (CITIC Securities) runs principal
businesses at group level, and brokers' facilitation policies
can vary by market — but agency-only is the verified CLSA model
and brand.

**The interpretation — half right, and the half that's wrong is
where the job lives.** What agency-only genuinely REMOVES is the
risk-transfer axis: no guaranteed-close pricing, no capital
commitment, no principal netting — that business sits with the
bulge-bracket desks. At the pure fill level, yes: an agency MOC
order from CLSA and from anyone else receives the same closing
price.

But four differentiation axes survive agency-only — and one is
STRENGTHENED by it:

1. **Agency crossing.** Matching one client's tracker buy against
   another client's arbitrage unwind at the close is agency
   business — no capital required. Cross rates differ hugely by
   desk and are pure client price-improvement.
2. **Advice and research — the axis where mandates are actually
   won.** Which changes are coming (Step 1), what the close will
   look like (Step 2), whether a flexible client should deviate
   from MOC (the May-2026 OVERCROWDED names: scenario-conditioned
   splits beat the close by ~590 basis points). The basket is
   awarded before effective day, on exactly this.
3. **Operational auction excellence.** Squeeze and limit
   handling, residual management, entry timing, reading the
   indicative feed — measured in TCA basis points, differing by
   desk even for "identical" MOC mandates.
4. **The unconflicted position is itself the differentiator.**
   Index-rebalance flow is the most predictable, most
   front-runnable flow in equities. Clients with leakage
   concerns route it to agency-only desks PRECISELY BECAUSE no
   proprietary book sits behind the wall. For this specific
   product, no-prop is not a limitation — it is the pitch.

**The business conclusion:** an agency-only desk cannot monetize
risk pricing, so it must monetize information, operations, and
trust — advice quality upfront, execution craft at the close,
and proof (TCA) afterward. Which is, precisely, what the
four-step analytics platform is for: it is the differentiation
engine an agency PT desk runs on.

### Q34. Who supplies the opposite side — and what should we measure for adds vs deletes?

**Is the opposite side mostly institutional? Yes — at the sizes
that matter.** A deletion print running 10–30× a normal day
cannot be absorbed by retail; the suppliers are index-arbitrage
hedge funds and proprietary traders (dominant), auction
liquidity providers, and opportunistic institutions (active
managers using the event to enter/exit). Our reconciliations
show the footprint: auction volume ≈ 77–125% of the predicted
passive stake, and the excess in crowded names matched measured
positioning. Retail matters in Taiwan generally, but not at the
rebalance close.

**Is stock borrow-lending THE institutional dataset? For
DELETIONS, yes; for ADDITIONS, no.** The instrument follows the
direction of the pre-position: a deletion pre-positioner is
SHORT, and shorting requires borrow — so securities-lending
balances are the direct, daily, free footprint (Compal: 440
million borrowed shares standing, the squeeze fuel; 1101 today:
18.7 ADV-days). An addition pre-positioner is LONG — no borrow
involved — so the add-side instruments are: cumulative abnormal
VOLUME (the completion metric), FOREIGN NET BUYING (Taiwan
publishes signed per-name foreign flow daily — direction, not
just activity), holdings/margin changes. Borrow data on an add
is only a secondary read (shorts positioning for the post-add
fade).

**Should we analyze buy volume after announcement, before
effective? Yes — with one technical caveat and one fix.** Tape
volume is UNSIGNED (every share bought is a share sold), so "buy
volume" cannot be read off the tape directly. The working
proxies, both already in the model: abnormal TOTAL volume
(activity = accumulation when the passive side has not yet
traded) and the SIGNED series that Taiwan uniquely gifts —
official daily foreign net buy/sell per stock — which is how the
wrong-way flag exists at all. Institutional data (real client
flow) would replace proxies with signed truth; until then,
completion + foreign direction is the pair.

**Is short-then-cover the ONLY deletion pre-position? No —
three-and-a-half channels:** (1) SHORT in advance, buy back at
the print — the classic, borrow-visible channel; (2) EXISTING
HOLDERS selling early and buying back at the close — active
funds and non-benchmark holders need no borrow, leave no lending
footprint, and show up only in volume (one reason completion and
borrow can diverge); (3) NO pre-position at all — simply BID in
the closing auction at a discount and exit afterward: the pure
toll-collector, invisible in the window entirely, visible only
in the auction print and the T+1 reversal; (3.5) derivative
variants (futures/swap hedges) that shift the footprint into
other instruments. This is precisely why the model reads
MULTIPLE legs — volume completion, borrow balances, foreign
direction — rather than any single one: each channel leaks into
a different dataset.

### Q35. Before the new data lands — what relationships might it show, and what statistics make findings trustworthy?

Asked while the decade harvesters (SBL, T86, margin, day-trade,
blocks) are still downloading — which is precisely why the answer
was written NOW. Hypothesizing before seeing data is the only
version of this exercise that produces evidence rather than
stories; the same questions asked after the data arrives become
curve-fitting.

**The hypotheses (Registry v5, LOCKED c-69 — 8 entries, full
table with thresholds in docs/VARIABLE_LAB_REGISTRY.md):**

Each new dataset observes a different actor, so each hypothesis
is really a claim about WHO is on the other side of the forced
passive print:

- **Margin balances (retail, H18/H19).** Margin longs are
  leveraged weak hands: high margin-long balance into a deletion
  should mean worse effective-day performance and more follow-
  through (forced deleveraging amplifies). Margin SHORTS are the
  opposite — a retail borrow-supply channel running parallel to
  SBL, so short build over the window should raise completion
  and reduce squeeze incidence.
- **Day-trading (toll collectors, H20/H21).** Names where
  day-traders are structurally active have deeper intraday
  recycling capacity (channel CH3), so the close should
  dislocate less and reverse less. And on T itself, a day-trade
  spike should shift volume from the close into the session.
- **Blocks (crossing, H22).** Block prints in the window are
  demand met off-tape — more window block volume should mean a
  smaller forced close print and higher measured completion.
- **SSF open interest (synthetic, H23).** OI build in an event
  name is pre-positioning the cash tape cannot see. Direction
  declared, but honestly LOG-ONLY: capture starts today, n=1 at
  Aug-2026; no test before five events.
- **T86 signed flow (the arb desks, H24/H25).** Dealer-prop net
  flow is the direct arbitrage footprint: dealers leaning
  against the side should predict the bounce. And H16's foreign
  leg gets REBUILT from true signed flow — if the compound
  effect vanishes under better data, H16 is downgraded, not
  defended.
- **The crowding index (H26).** The λ-model residual we've been
  calling "crowding" becomes measurable: a standardized sum of
  borrow build + margin-short build + dealer flow (+ SSF when
  powered) should explain part of that residual out-of-sample.

**The statistics that make findings useful (v5 protocol):**

1. **Pre-registration** — done above; direction and threshold on
   record before evaluation.
2. **Multiple-testing control** — 8 hypotheses = 8 chances to
   fool ourselves; Benjamini-Hochberg at q=0.10 on top of each
   hypothesis's own bar.
3. **Clustered inference** — name-events within one review move
   together; block permutation by event (the pattern-study
   machinery), never naive p-values.
4. **Effect sizes with event-bootstrap CIs** — a rho of 0.15
   with p=0.04 is not tradeable; size first, significance
   second.
5. **Temporal out-of-sample** — fit 2015–2022, validate
   2023–2026; Aug-2026 is the standing live OOS event.
6. **Incremental-value regression** — a new variable must beat
   the controls we already have (size, side, float-days, era),
   i.e. explain the λ residual, not re-explain λ.
7. **Power stated up front** — n≈77 deletions detects |rho|≈0.31
   at 80% power; anything weaker grades INDETERMINATE, never
   "suggestive".
8. **Nulls get pinned** — a miss is a result; the c-65 return-
   prediction null remains the bar.

One deliberate omission: NO hypothesis on SBL fee rates, because
that variable doesn't exist yet — it gets registered (H27) the
day a fee series is in hand and before it is evaluated.

### Q36. Where can data science integrate into the workflow, with external frameworks to reference?

Answered in full in **docs/DATA_SCIENCE_INTEGRATION.md** (c-70).
Short version: Step-1 calls become Brier-graded calibrated
probabilities; the rule engine keeps deciding the SIDE while a
meta-labeling layer (Lopez de Prado, AFML) only sizes
confidence; the T-day print is the Optiver "Trading at the
Close" Kaggle problem and our 5-sec auction capture feeds the
same feature family; print ranges get conformal-prediction
coverage guarantees graded empirically; outcomes get
triple-barrier labels; validation adopts purged/embargoed CV and
backtest-overfitting (PBO) checks; the data layer maps onto the
ML4T/MLOps architecture (sentinels = drift detection, PIT caches
= feature store) plus harvest-time expectation checks — the
class of guard that would have caught the mieu ghost-cache bug.
Priority order proposed in the doc; conformal range grading is
first (cheap, live-gradeable Aug-31).

### Q37. The Optiver "Trading at the Close" contest — what exactly was the question, and what methods won?

**The setup.** Nasdaq runs a closing cross: in the last ten
minutes (3:50–4:00 pm ET) an auction book accumulates
market-on-close and limit-on-close orders while the continuous
book keeps trading. The exchange publishes auction state as it
evolves: indicative (reference) price, matched size, the
IMBALANCE (unmatched size and its direction), plus near/far
prices and the regular book's best bid/ask. Optiver's 2023
Kaggle competition gave ~200 anonymized Nasdaq stocks, snapshots
through each day's final ten minutes, and asked one question:

**The question.** At each snapshot, predict the stock's
weighted-average-price move over the NEXT 60 SECONDS, *minus*
the move of a synthetic index built from the whole basket — in
basis points. Two design choices matter: the target is
RELATIVE (index move subtracted, so you predict idiosyncratic
auction pressure, not the market), and the metric is MAE
(penalizes typical-case error, not tail misses). Final ranking
was scored on three months of genuinely FUTURE live data after
submissions locked — a real out-of-sample period, not a held-out
history.

**What won.** The 1st-place solution (hyd): ~300 engineered
features into an ensemble of CatBoost (weight 0.5), a GRU
(0.3), and a Transformer (0.2); ONLINE RETRAINING every ~12
days through the live period; and a zero-sum post-processing
step (demean predictions across the basket each snapshot —
since relative moves must roughly cancel, forcing the
cross-section to sum to zero is free accuracy). Across the
leaderboard the pattern was consistent: gradient-boosted trees
(LightGBM/CatBoost) as the backbone, neural nets for ensemble
diversity, and the alpha concentrated in FEATURE ENGINEERING on
the auction fields — imbalance ÷ matched size, near/far vs
reference-price spreads, WAP momentum, rolling stats, target
lags, cross-sectional ranks.

**The lessons that transfer to our TWSE problem.** Taiwan's
close is a 5-minute call auction (13:25–13:30) with 5-second
indicative price/volume disclosure — the same information
family the contest features were built on (indicative price
drift ≈ near/far spread; disclosed unmatched ≈ imbalance). The
transferable grammar: (1) predict RELATIVE, not raw — our
analog is dislocation vs the event basket; (2) MAE against a
naive baseline — a model must beat "predict the range mid";
(3) trees first, NNs only for diversity — at our sample sizes
(133 name-events) trees only, per the c-65 null; (4) the score
is graded on LIVE forward data — our Aug-31 5-sec capture is
that period; (5) structure-aware post-processing — their
zero-sum trick is the kind of constraint our event baskets
also satisfy.

### Q38. What can we do with Taiwan close-auction data ex-post — and do we have it back to 2015?

Full study + tables in **docs/AUCTION_EXPOST_TCA.md** (built
c-71 from data already on disk). The availability answer has
three layers: the intra-auction 5-sec indicative path has NO
history for anyone (disclosure regime only since Mar-2020, feed
not archived — capture-forward from Aug-31); the auction
OUTCOME (close price/volume) is available 2015+ (the daily
close IS the print); the dislocation around the print (last
continuous vs close, 5m resolution) is measurable 2023+ from
the IB bars. On usefulness: yes — ex-post review is TCA, and
the first pass already produced a desk-relevant result: on 80
name-events the auction print moved AGAINST the forced flow in
71-80% of cases (deletes close a median +45 bps ABOVE the last
continuous price; adds -15 bps below), meaning the MOC
benchmark is less punitive than the afternoon tape implies —
the other side shows up in the cross. Deletes concentrate 72%
of day volume in the auction vs 44% for adds. All descriptive,
named as v6-registry candidates, graded only on forward events.

### Q39. Doesn't Taiwan officially publish last-5-minute auction data? (User correction — verified TRUE)

The user was right, on two counts, and Q38's layer-1 claim
needed correcting. (1) The per-stock indicative-price
disclosure did NOT start in Mar-2020 — TWSE has disclosed
simulated closing price/volume + best-5 during 13:25–13:30
since **June 29, 2015** (a lighter form since Feb-2012);
Mar-2020 was the continuous-trading change. What survives of
the original claim: that live feed is still not publicly
archived, so per-stock paths remain capture-forward. (2) More
importantly, TWSE DOES archive an official 5-second dataset —
**MI_5MINS**, market-wide accumulated bid/ask orders + trades,
09:00→13:30 including the whole call window, downloadable back
past 2015. Probed live: trades freeze 13:25→13:29:55 while
order arrival keeps ticking, and the 13:30:00 row is the cross.
Harvester added (roadmap_harvest.py auction5s, piloted; the
2015 pilot even shows cancellation-era bid-volume shrinkage
into the cross — a regime marker).

How it complements: it gives the DECADE of auction-window
order-arrival anatomy that the per-stock capture can't reach —
event-day vs control-day order-surge and imbalance signatures
into the cross, late-arrival timing (last 30s), the market-wide
size of the cross, and era documentation (cancellation era vs
ban era) needed to interpret both the ex-post TCA panel and the
Aug-31 per-stock capture. It's the market-level baseline the
Optiver-style features get normalized against.

### Q40. So MI_5MINS is market-wide only — meaning the IB 5-minute bars are the most useful source for per-stock auction behavior?

Correct, with the boundary stated: the IB 5m bars (2023+) are
the ONLY per-name historical source that separates the last
continuous price from the auction print (dislocation) and
auction volume from session volume (auction share) — the whole
ex-post TCA panel rests on them. Their limit: they see the
auction as ONE bar (the print), so they cover behavior AROUND
the call, never inside it. The full stack, sharpest tool per
question: per-stock print-vs-tape = IB 5m (2023+); per-stock
final price = daily close (2015+); market-wide order arrival
INTO the call = MI_5MINS (2015+); per-stock inside-the-call =
our 5-sec capture (Aug-31 forward). The layers don't overlap —
they stack.

### Q41. How can MARKET-level inside-auction data reveal anything about INDIVIDUAL stock auctions on effective dates?

Through concentration: on an effective date the abnormal
component of market-wide auction flow largely IS the event
names. Four inference routes: (1) difference-in-differences —
subtract the era-matched control-day order-arrival curve
(13:25→13:30) from the event day's; the residual ≈ the sum of
the event basket's abnormal auction flows; (2) timing-signature
transfer — WHEN the passive complex enters MOC orders (early
show vs last-30s snipe) is a procedural behavior of the same
desks across all names, so market-level identification applies
per stock, and the Aug-31 capture then verifies it name by
name; (3) aggregate reconciliation — the event-day excess in
the 13:30 cross size must ≈ Σ(per-name forced-print forecasts),
a bias check the λ model has never faced; (4) side-mix
direction — bid-vs-ask accumulation during the call should lean
with the review's net side mix, and a wrong-way lean is the
pre-positioned-other-side signature (seen in prices in the TCA
panel, 2023+) now observable in ORDER FLOW back to 2015.
Limits: cannot separate event names from each other, no
per-name prices, concentration weakens on small-change reviews,
and each event = ONE market observation (n=33, not 133). A
basket-level instrument that sharpens per-stock inference —
never a replacement. These four analyses are v6-registry
candidates once the auction5s harvest lands.

### Q42. What does "market level" mean in MI_5MINS — is it TAIEX index auction data? How to interpret it?

Not an index — it is the WHOLE EXCHANGE's counters: every
5 seconds, seven running totals summed across all TWSE-listed
stocks' regular-session order books — accumulated buy orders
(count + volume), sell orders (count + volume), and executed
trades (count + volume + value). Units pinned by reconciling
against the official daily summary (FMTQIK, 2026-06-05): volume
in THOUSANDS of shares, value in NT$M. Worked read of that day:
by 13:29:50, 25.30B shares of buy orders submitted vs 15.06B
traded (most resting volume never fills); 13:25:00→13:29:55 the
trade columns FREEZE (call window) while order columns keep
climbing = pure arrival into the auction; the 13:30:00 row
jumps +506M shares / +NT$73.0B in one print = the market-wide
cross (~5.9% of the day's value). Any 5-sec flow = difference
between consecutive rows. Cautions: (1) coverage is the regular
main board only — odd-lot, blocks, after-hours excluded (hence
13:30 totals 15.57B shares / 4.84M trades vs official 16.02B /
7.92M — the transaction gap is mostly odd-lot's tiny trades);
(2) TAIEX is frozen during the call (no matching = no price
changes), so the separate MI_5MINS_INDEX file adds ~nothing
inside the window — the auction's information lives in order
FLOW, which is what MI_5MINS carries.

### Q43. In historical simulation, how do we account for the price impact our re-simulated order WOULD have created but the tape never felt?

Already researched AND built (2026-07-09):
**docs/COUNTERFACTUAL_IMPACT_MODEL.md** +
`agents/impact_propagator.py` (5 pinned tests). Mechanics: each
simulated fill is charged square-root-law instantaneous impact
(η·σ·√(q/ADV), Level-1 labeled overlay), and then PERTURBS ALL
LATER BARS via a propagator kernel — 40% permanent (never
decays) + 60% temporary (exponential decay, 10–30 min
half-life), signed adverse to the order's side — so an
aggressive simulated morning makes the simulated afternoon more
expensive. Causality enforced (no back-propagation, no
double-charge). Unknown parameters are SWEPT, not hidden: the
delta between two schedules ships only if its sign is stable
across the η × half-life grid; otherwise the tool says "run a
live A/B". NEW cross-link (c-72): the ex-post TCA panel's
t1_revert_bps column is measured reversion on events with
KNOWN forced quantity (λ model) — exactly the calibration data
the doc's roadmap item 1 needs to fit the permanent/temporary
split from our own event library instead of defaults.

### Q44. If simulated fills carry impact, must we adjust for the (smaller) auction slice — or is the close so deep that no adjustment is needed?

Asymmetric answer, registered as the AUCTION LEG upgrade in
docs/COUNTERFACTUAL_IMPACT_MODEL.md §3b. The continuous kernel
(√(q/ADV) + forward propagation) is the wrong physics for a
call auction: one simultaneous match, lumpy impact along the
clearing step function, no afternoon to propagate into — the
temporary component becomes the OVERNIGHT revert (measured:
adds +182 / deletes +50 bps at T+1). Deciding variable =
marginal share of the cross. Effective dates: cross = 8–21×
ADV, ~72% of delete day volume — a single desk's slice is
second-order (< ~5% marginal share ⇒ skip, sub-noise). Normal
days: cross ≈ 6% of day volume — the same order dominates, and
the auction leg is mandatory for any schedule moving size into
a non-event close. Elasticity calibratable from our own panel
(pressure_bps vs forced-flow size, n=80); auction fills charge
the auction leg INSTEAD of the continuous kernel, never both.

### Q45. How do we calculate the total free-float market cap (→ the 85% cutoff) for the other markets?

Design in **docs/GMSR_MULTIMARKET_DESIGN.md**. Terminology fix
first: the GMSR is GLOBAL (no per-market denominator needed);
what each market needs is its own 85% COVERAGE CUTOFF, which
the GMSR corridor then disciplines. Three-layer architecture:
Layer A factsheet inversion (done, all 10; ±6% structural band
from coverage banding), Layer B member-based (script exists —
live numerator ÷ 0.85; disagreement vs A flags stale
factsheets/float errors), Layer C full census (the TW gold
standard) = ONE census engine + per-market adapters (universe
provider, resolver, shares source, float source — only the
adapter forks, never the screens or the walk). Per-market float
reality drives priority: Korea first (EM corridor + official
KRX day-files + DART holders), India second (promoter patterns
= the best named float data in Asia), Japan third (DM anchor),
China fourth (tradable-shares shortcut but Connect second-stage
float → wider band), AU/HK likely fine on Layers A/B, MY/ID/PH
honestly capped at Layer B + wide bands (census with default
floats measures little). Acceptance per market: |D_census −
D_implied| ≤ ~6% validates both; verdicts ship only
frame-robust across all available frames.

### Q46. The old cutoff calculation reviewed — what was wrong, and the corrected walk (user challenge, verified)

The user challenged the old calculation (Q23) — right again.
Three faults found, one narrative-level correction shipped
(scripts/cutoff_walk_v2.py -> data/cutoff_walk_v2.json):

**Fault 1 — stale denominator.** The old walk ran on the
bottom-up $4,197B frame (150 tracked + a 400-name MODELED
body). Rerun with REAL census names (774 pass the GIMI screens
of 1,709 cached), the gap vs the factsheet-implied $3,745B
reproduced at +11.4% — proving the modeled body was NOT the
error source.

**Fault 2 — head floats.** The v2 named-insider method gives
TSMC float 1.0 (the documented government-stake blind spot) vs
MSCI's implied ~0.87. With ~50% concentration that one factor
dominated the gap. Fix: top-10 FIFs implied IN-FRAME (factsheet
float cap ÷ our census full cap). Gap collapsed to +3.7% —
inside the ±6% banding allowance; frames now agree.

**Fault 3 — the walk's bases muddied.** Stated exactly now:
RANK by full company cap descending; ACCUMULATE free-float-
adjusted value; stop at 85% of the float total; EXPRESS the
cutoff as the crossing company's FULL cap.

**The narrative correction:** the old walk's "crossing at rank
115, $6.74B, inside the corridor, no clamp" was an artifact of
the inflated denominator. Corrected: the crossing is at rank
~53 at $12.95B full cap — ABOVE the EM corridor ceiling
($9.44B) — and this holds across the whole default-float band
(0.40 -> 0.70: cutoff $15.6 -> $9.7B). So in Taiwan THE
CORRIDOR BINDS: the effective cutoff is corridor-clamped
(~$9.44B), membership extends below it via buffers (existing-
member floor 2/3 x 9.44 = $6.29B), and that — not the raw 85%
line — is why the index carries 77 members, deeper than the
raw crossing. Add hurdle rises to 1.5 x 9.44 = $14.16B; the
2408 shadow call SURVIVES ($46.7B full cap) — now robust
across three frames. Logged T-5 before the Aug-11 announcement.

**APAC standardization (factsheet-only recipe):** per market,
(1) D = index float cap ÷ 0.85 (±6% band); (2) corridor = tier
reference x [0.5, 1.15]; (3) where the member census has run,
do the corrected walk on members (rank full / accumulate
float) and check whether the crossing lands inside the
corridor — in less concentrated markets it should, making the
crossing itself the cutoff; in concentrated ones (TW-like) the
corridor clamps; (4) the factsheet's "smallest constituent"
stat bounds the membership frontier from below. Only the
concentration structure differs per market — the procedure
never forks.

### Q47. Which data sources give a standard free-float estimate for ALL companies in each APAC market — and is it feasible?

Survey table in docs/GMSR_MULTIMARKET_DESIGN.md (addendum
c-80). Short version: two markets publish it OFFICIALLY for
essentially the whole market — India (mandatory quarterly
promoter/public shareholding patterns, grade A) and Japan (JPX
TOPIX Free-Float Weights, grade A-). Korea is close behind
(KRX free-float ratios via data.krx, B+). China is two-stage
(official tradable-share counts free, strategic-holder strip
from filings, B). Taiwan has NO official file — TAIEX is
full-cap weighted; FTSE/MSCI floats are licensed — which is
why the v2 named-insider method exists and, at 0.022 error, is
already the best available (B). Philippines has mandatory
Public Ownership Reports but document-scraping per company
(B-). Indonesia tracks float for its 15% rule but a bulk file
is TO_VERIFY (C+). Hong Kong (bounds + CCASS proxy only),
Australia and Malaysia (vendor estimates only) grade C — for
those, Layer A/B (factsheet inversion + member census) is the
honest ceiling. Priority consequence: India and Japan rise in
the census queue — official floats remove the hardest input.

### Q48. Why is free-float data so hard to get — and how does MSCI estimate it?

Hard because float is a JUDGMENT about intent, not a disclosed
fact: registers record who holds, never why; disclosure is
threshold-based (sub-5% strategic stakes and nominee/custodian
chains are invisible); ownership webs (cross-holdings, chaebol
circulars, multi-vehicle government stakes) need entity
resolution; float moves daily while filings arrive quarterly;
and because the work is expensive, index providers license
their factors as IP — so no public standard emerged (exchanges
that publish floats do it only because their own indices need
them). MSCI's method (GIMI float definition): classify every
disclosed holder as strategic (governments, corporations,
founders/families, officers/boards, employee trusts,
controlling banks) vs non-strategic (funds, pensions,
insurers, retail); subtract strategic; cap by foreign room
where a limit binds; round to 5% increments = the FIF;
review quarterly/semi-annually + event-driven; analyst
judgment where filings are ambiguous. I.e., our v2 method with
more analyst-hours — which is why v2 lands within 0.022, why
its one blind spot (board-seatless government stakes, TSMC) is
a classification miss not a data miss, and why implied-FIF
reverse-engineering extracts their paid judgment free where it
matters.

### Q49. The CURRENT Taiwan procedure, end to end (post-c-79 correction)

**Denominator, two frames triangulated:** Frame 1 = factsheet
inversion: index float cap $3,183.0B (Jul-31) ÷ 0.85 = $3,745B
(±6% coverage-banding band). Frame 2 = census walk: 2,146-name
universe -> GIMI screens (min size, float ≥ 0.15, ATVR ≥ 15%,
frequency) -> 774 pass -> sum price × shares × float = $3,883B
(+3.7%, inside the allowance — frames corroborate). Float
stack, tiered: top-10 = in-frame implied FIFs (factsheet float
cap ÷ census full cap — MSCI's own judgment, fixes the TSMC
gov-stake error) > members = v2 named-insider (0.022) >
non-members = default 0.55 swept [0.40, 0.70], default share
reported (12.4%). Census coverage partial (1,709/2,146),
stated.

**Cutoff:** reference $15.75B × 1.042 = $16.41B DM; EM = half
= $8.21B; corridor [4.10, 9.44]. Corrected walk: rank FULL cap
/ accumulate FLOAT / stop at 85% ($3,301B) -> crossing rank
~53 at $12.95B FULL cap -> ABOVE the ceiling in every frame ->
THE CORRIDOR BINDS: effective cutoff ≈ $9.44B (coverage
overshoots 85%, allowed). Frontiers: delete pool = members
below 2/3 × 9.44 = $6.29B; adds need 1.5 × 9.44 = $14.16B +
half-bar + float/ATVR/foreign-room gates. Frame-robust policy
governs every verdict; 2408 ($46.7B) clears in all three
frames. Declared proxies labeled (1.042, FX 29.5, price
vintage). Graded at the Aug-11 announcement.

### Q50. How do PT desks (CLSA-like) predict index reviews — same framework as ours? What do institutional inputs buy them?

Same skeleton, necessarily — the GIMI is public and there is
only one funnel (denominator -> reference -> corridor -> walk
-> buffers -> gates); every street index team publishes preview
notes from it. Three real advantages: (1) LICENSED INPUTS —
MSCI subscribers get daily security-level FIFs, full caps,
segment membership, foreign room; our whole estimation layer
(inversion, v2 floats, implied FIFs, triangulation) is
unnecessary for them. Their residual uncertainty = exactly ours:
the snapped price date, the fresh GMSR recalc, and corner-case
discretion — licensing removes estimation risk, not the
fundamental unknowns. (2) CALIBRATION — decades of graded
reviews; knowledge of how discretion behaves at the margin;
methodology disambiguation via MSCI client coverage. Their edge
concentrates on the 2-3 borderline names. (3) FLOW VISIBILITY —
client orders and inventory in candidates during the window:
doesn't predict MSCI better, predicts the TRADE better
(crowding observed directly vs our SBL/T86/margin inference).
Where we're NOT behind: implied FIFs recover the licensed
factors for members (0.022 / +3.7% quantify the remainder), and
our formalized Step-2/3 supply machinery is more structure than
most desks' preview notes carry (they hold it as trader
intuition). The true remaining gap: non-member floats,
borderline calibration (they graded ~40 reviews; we grade our
first Monday), and flow sight (structural).

### Q51. Step-2 (ann→eff) data inventory for Taiwan — what we hold, what's missing

**Held (decade-deep unless noted):** the liquidity panel (133
name-events — calibration backbone), the lambda flow model +
float stack (passive demand), SBL balances (CH1), T86 signed
flow by investor type (CH2 attribution, H24/H25), margin both
sides (H18/H19), day-trade (CH3, H20/H21), blocks (H22), IB 5m
bars 2023+ + the ex-post TCA panel (decider thresholds, auction
leg), auction5s market-wide call-window arrival (pilot; full
run pending), TAIFEX SSF capture (forward-only), vintage/PIT/
event registries. Every v2 channel observable except
derivatives-history; every v5 hypothesis has its input landed
or pending one run.

**Missing, in value order:** (1) SBL FEE rates (quantity
without price; TWSE transaction-detail day-files vs FinMind
paid tier — gates H27); (2) historical SSF OI (TAIFEX download
forms 2017+ — CH3.5 backward); (3) QFIIS foreign-holding
day-file (levels + daily foreign room; T86 is flow only); (4)
ETF PCF baskets (DIRECT local passive demand — small scrape,
high signal); (5) broker-branch files (retail geography,
heavy — conditional on H18/H19 grading); (6) odd-lot (cheap,
modest); (7) per-stock intra-auction pre-Aug-31 (no public fix
exists — permanently capture-forward). Items 3-4 added to the
handoff roadmap as the sleepers: official, harvester-pattern
compatible, and they convert inferred quantities into measured
ones.

### Q52. Adds vs deletes — checkpoint lists per side; the 3.5 deletion methods; and can liquidity be predicted BEFORE the announcement?

**The 3.5 deletion methods** (= v2 channels, STEP2 doc): CH1
borrow-and-short (SBL-visible; cover = the bid at the print),
CH2 inventory/long (buy cheap in window, supply patience at the
print — zero borrow footprint; 2474), CH3 toll-collectors
(uncommitted, intraday recycling on T, paid the toll), CH3.5
derivatives (SSF synthetic — the half; unobservable from cash
until the TAIFEX capture). Deletion checkpoints: SBL build AND
standing base (CH1/CH1b), T86 completion residual signed by
foreign direction (CH2), day-trade share (CH3 capacity), SSF OI
(CH3.5), margin-short build (H19), blocks, print anatomy.

**Addition checkpoints** (meanings flip): WHO accumulates (T86
dealer/foreign = CH2 supply-in-waiting), SBL FADE, margin-short
build (retail fading the rally), SSF OI, foreign-room
consumption pace (TW gate), blocks, drift vs basket (premium
already paid -> fade risk +182bps), day-trade share, ETF PCF
when captured. Asymmetry stated: deletion pre-positioning is
OBSERVABLE (borrow is registered); addition supply is INFERRED
from accumulation -> wider add ranges.

**Pre-announcement prediction:** hard but tractable. Objection
1 (change uncertain) -> probability-weighted forecasts,
P(change) x conditional supply, Brier-graded Step-1 weights.
Objection 2 (how to see positioning early) -> the arbs predict
the same public rulebook, so positioning starts pre-
announcement IN OUR CANDIDATE NAMES with the SAME footprints
(SBL, dealer flow, SSF OI, drift — the front-running
literature's 0.86%/mo is this). Framework = Step-2 channels
PLUS three pre-announcement pieces: candidate-vs-control
differencing (anticipatory vs noise), the anticipation clock
(decade calibration: when does borrow start building relative
to announcement for correctly-predicted deletes), and
crowding-as-feedback (heavy pre-positioning -> well-supplied
print -> lower expected dislocation — the market grading our
prediction before MSCI does). Registry v3 (H11 family) is the
locked home for these; the decade harvest supplies the data.
Commercially: this package IS the Phase-0 pre-event marketing
artifact that wins the order (Q50).

### Q53. How are we currently deriving Taiwan free floats?

Four tiers, best source per name: (1) top-10 members =
IN-FRAME IMPLIED FIFs (factsheet float cap ÷ census full cap —
MSCI's own factors extracted; fixes the TSMC gov-stake case);
(2) other members = v2 NAMED-INSIDER floats (1 − directors/
officers/controlling holders from filings; 0.022 mean error;
stated blind spot: board-seatless government stakes — hence
tier 1 overrides the head); (3) census non-members = DEFAULT
0.55 swept [0.40, 0.70], default share printed (12.4% of D);
upgrade = census floats phase; (4) ex-members in event studies
= default 0.55 STARRED; upgrade = PIT insider fetch. Rejected
and null-pinned: TDCC size-bracket concentration (v1 — can't
tell founder from fund). Context: TW publishes NO official
float file (Q47), so this stack is the public-data state of
the art, structurally identical to MSCI's own classification
exercise (Q48) with the top-10 answers copied from their
published arithmetic.

### Q54. With CLSA-like licensed MSCI access, what data would help the research?

REPLACED outright: (1) daily security-level constituent files
(actual FIFs, shares, float/full caps, weights, segment
membership — kills implied-FIF extraction, v2 floats, ETF
membership triangulation, factsheet inversion; daily history =
true PIT membership); (2) the official review parameters (the
actual GMSR/ranges + per-market cutoffs — the corrected walk
becomes verification; the 44-review backtest can decompose
every miss into input error vs discretion — the license's
single most valuable calibration unlock); (3) machine-readable
change lists + corporate-event notices. SHARPENED: (4)
pro-forma files at announcement (exact Δweights -> forced flow
= Σ AUM x Δw / px, replacing lambda post-announcement); (5)
Small/IMI files — the quiet biggest upgrade: demotions get
BOUGHT by small-cap trackers, net flow = Standard sell − Small
buy, changing print forecasts for every demoted name; (6)
foreign-room data for restricted markets (CN/IN activation);
(7) index-linked AUM estimates (pins the flow arithmetic).
UNCHANGED by any license: the price-snap date, fresh GMSR
recalc, discretion corner cases — and the ENTIRE supply side
(SBL/T86/margin/auction/anticipation clock/channel model):
MSCI sells inputs, not knowledge of who's pre-positioned. The
license removes estimation risk; the differentiating research
remains the Step-2/3 machinery (Q50).

### Q55. Can retail investors buy MSCI's data — and at what cost?

Practically no retail tier exists for the data that matters
(Q54's security-level files). Licensing is custom/institutional:
reported averages ~$120k/yr (small team) to ~$733k/yr
(enterprise); MSCI's published pricing principles are
quote-based by content/usage. Middle path = a terminal
(Bloomberg ~$30k/yr shows membership/weights interactively —
checking, not files); academic WRDS-type access sometimes
carries history. Free retail layer = exactly what this project
mines: latest factsheets (overwritten monthly — hence
capture-forward), change lists/press releases, the GIMI book,
ETF holdings as membership proxies. Framing: our
public-exhaust approach IS the retail ceiling, and the
measured gaps (0.022 floats, +3.7% denominator) quantify the
distance between that ceiling and the six-figure product.

### Q56. Where does the rulebook say MSCI "snaps any of the last 10 business days"?

[CITATIONS SUPERSEDED — see the c-91 correction below; the
user then pointed to the CURRENT May-2026 edition.] Originally
pinned to the Dec-2022 edition (§3.2.6 p.66 QIR / §3.1.9 p.54
SAIR). **Current citation (GIMI May-2026, archived at
data/msci_archive/MSCI_GIMIMethodology_May2026.pdf): §3.1.9
"Date of Data Used for Index Reviews", p.48** — the edition
restructured the old SAIR/QIR split into one section covering
all four reviews ("any one of the last 10 business days of
January / April / July / October"; old §3.2.6 is now "Early
Deletions"). The provision governs cap prices, FIF updates,
foreign room, and NOS. Precisions: MSCI picks ONE undisclosed
date (fn 28: the window PREPONES if the effective date falls
inside the announcement month; fn 29 defines a business day
as >80% of ACWI float open); the two OTHER data dates are
deterministic and per-review — for Aug-2026: Equity Universe
Cutoff 2026-05-29, Liquidity Cutoff 2026-06-30 — so universe
and ATVR inputs align to MSCI's exact dates while the price
date cannot. NEW in this edition's text: the post-cutoff
extraordinary-events discretion (fraud/takeover/suspension
between price cutoff and announcement can veto a migration) —
the discretion LIMIT now has a rulebook citation. Step 0
renders all of this; full record in
docs/FRAMEWORK_CUTOFF_STEPS.md.

### Q57. Explain the three cutoff dates and their mapping to our analysis
### Q58. Explain Step 1 term by term ($15.75B / x1.042 / half / corridor)

Both answered in full in docs/FRAMEWORK_CUTOFF_STEPS.md Q&A
section (c-91). Q57 headline: universe cutoff (Aug-26:
2026-05-29) = who can be considered — post-May listings
auto-disqualified; liquidity cutoff (2026-06-30) = ATVR
windows must END 6/30 (actionable census correction — we use
latest-12m); price cutoff (one of last 10 July b-days) = the
only stochastic date, mapping onto frame-robustness (formal
upgrade: 10-day ladder sweep). Q58 headline: $15.75B = full
cap of the company at the aggregated DM universe's 85%
free-float coverage crossing (the global yardstick, §2.3.2.1);
x1.042 = our proxy for MSCI's per-review recompute (broad-DM
move between price windows; ±2pt honesty tax for marginal-vs-
average, unknown day, composition churn); EM = half by fixed
rule; the corridor (§2.3.2, 0.5-1.15x) = the coverage-vs-
comparability treaty — inside it the market's walk wins,
outside it the clamp wins (Taiwan's case).

### Q59. Do the three data dates apply to all APAC markets — and how do they affect the analysis?

YES — global by construction: GIMI §3.1.9 defines the dates
PER REVIEW for the whole index family, not per market (one
methodology, one calendar; fn 29's business-day definition is
itself global — >80% of ACWI float open — with per-listing
holiday handling). Consequence: the data-date logic is
STANDARDIZED once — agents/market_profiles.review_dates(year,
month) now returns the three dates for any review (Aug-2026:
universe 2026-05-29, liquidity 2026-06-30, price window
2026-07-20..31), used identically by all 13 markets AND by
historical PIT backtests (all 44 reviews can now be
date-aligned properly). Effects on the analysis, per input:
(1) UNIVERSE — membership eligibility and the minimum-size
data freeze at end-May: post-May listings are auto-
disqualified adds; (2) LIQUIDITY — ATVR windows must END at
the liquidity cutoff (actionable census correction; July
volume earns no credit); (3) PRICE — caps/FIFs/foreign room/
NOS from ONE undisclosed day in the 10-day window: the formal
upgrade is sweeping the ladder across all 10 dates and
shipping only sweep-stable verdicts. Registered refinement:
weekday approximation vs fn29's exact ACWI-open day count.

### Q60. The Global Minimum Size Reference, explained (with the §2.3.2.1 text in hand)

THE PROBLEM: each market's Standard index targets 85% of ITS
OWN float, but "the 85% line" is a $20B company in a deep
market and a $1B company in a small one — without a yardstick,
"Standard member" would mean different sizes everywhere. THE
FIX: pool the ENTIRE DM investable universe, sort by FULL cap,
walk cumulative FREE-FLOAT coverage, and read the full cap at
three crossings: 70% -> Large Cap ref ($51.3B), 85% ->
STANDARD ref ($15.75B — our number), 99% -> IMI ref ($1.19B).
The reference = "the size of the company at the global
boundary". EM = one-half DM by fixed rule; FM refs come from
the FM universe's own walk (hence tiny). USE: each market's
own 85% walk proposes a cutoff; it must land in 0.5-1.15x the
applicable reference — the book computes the ranges itself:
DM [7.87, 18.11], EM [3.94, 9.06] — and our corridor [4.10,
9.44] = exactly those numbers x our 1.042 scaling (check
passes to the cent). Inside the range the walk wins; outside
(Taiwan) the clamp wins. One sentence: THE MARKET'S WALK
PROPOSES, THE GLOBAL RANGE DISPOSES.

**NEW FACT surfaced by the passage:** "based on April 20, 2026
data" = MSCI disclosed, EX POST, the May-2026 review's chosen
Price Cutoff Date (2nd business day of the April window).
Each methodology edition reveals the prior review's choice ->
(a) the 10-day sweep can be graded retroactively per review by
collecting disclosed dates from successive editions; (b) a
prior on WHERE in the window MSCI tends to pick becomes
buildable. Registered as a follow-up (edition-mining the
price-date history).

### Q61. Must Taiwan's 85% crossing fall in [3.94, 9.06] — and what happens if it doesn't?

The FINAL cutoff must respect the range; the RAW crossing need
not — and §2.3.3 (May-2026 ed., archived) gives the exact
mechanism, sharper than the "clamp" shorthand: if the crossing
company's full cap lies inside the range it BECOMES the cutoff
(the walk wins). If not, MSCI adjusts the MEMBERSHIP COUNT,
not the number: crossing ABOVE the ceiling (Taiwan, ~$12.95B)
-> "the number of companies is increased to include ALL
companies with a full market capitalization higher than the
upper bound" — cutoff = full cap of the smallest company above
~$9.44B, coverage OVERSHOOTS 85% (hence 77 members vs the raw
walk's ~53); crossing BELOW the floor -> count DECREASED until
the smallest member clears the lower bound, coverage
undershoots. The book's own philosophy line: "priority to
GLOBAL SIZE INTEGRITY over market coverage" — coverage is the
goal, size integrity the constraint, coverage the casualty.
Knock-ons surfaced: §2.3.6.1 — with the cutoff outside the
range, the HALF-BAR float requirement references the RANGE
BOUNDARY not the cutoff (affects our add gates); fn 22 — a
company inside the range is deletion-protected if its removal
would drag coverage below the coverage target range (a
delete-pool subtlety for the frontier logic).

### Q62. Why the 1.042 scaling — does the rulebook prescribe it?

No — the rulebook prescribes MSCI's OWN update, and the
scaling is our labeled proxy for it. **GIMI May-2026 Appendix
X p.117** ("Updating the Global Minimum Size References and
Ranges"): at each review the DM Standard reference = the full
cap of the company AT THE SAME RANK as last review's
reference-setter, held as long as coverage at that rank stays
within 85-87%; outside the tolerance, the rank resets and the
reference is recalculated. EM stays = half DM; FM from its own
universe. So the published $15.75B / [3.94, 9.06] are the MAY
review's values at April-20 prices; the AUGUST review gets a
NEW reference repriced (rank-anchored) at the July price date.
Unscaled May numbers would judge an August review at April
prices (~4% stale in a rising tape). Our x1.042 = broad-DM
move as a stand-in for "reprice the rank-N company" — an
ASSUMPTION by construction, with the ±2pt band now precisely
characterized by Appendix X: (a) the marginal rank-anchored
company ≠ the average index; (b) a rank reset (85-87%
tolerance breaking) is a discontinuity smooth scaling can't
see. Vocabulary note: the 85-87% band is the GMSR RANK-HOLD
tolerance — distinct from the market-level coverage target
range. Framework page Step 1 now cites Appendix X.

### Q63. May-2026 confirmed latest edition; the GMSR-to-shortlist chain

Edition check: Jun/Jul/Aug-2026 URLs 404, May-2026 200 — the
latest, and the edition in force for the Aug-2026 review. The
chain, each link mapped to its artifact: (1) reference ->
range (Appendix X repricing, our x1.042 proxy; EM = half);
(2) the market walk PROPOSES ($12.95B crossing —
cutoff_walk_v2); (3) the range DISPOSES (§2.3.3 membership
expansion; effective cutoff ~$9.44B); (4) buffers -> two
frontiers (delete ~$6.29B, add ~$14.16B — asymmetric by
design: turnover paid only for decisive moves); (5) the
ladder names names (members below the floor = delete pool;
non-members above the bar = add candidates); (6) add gates
prune (universe eligibility by 5/29, float ≥ 0.15, half-bar
vs the RANGE boundary, ATVR ending 6/30, foreign room); (7)
delete protections prune (fn22 coverage protection,
extraordinary-events discretion); (8) robustness ships
(frames + float band + the 10-day price sweep -> sweep-stable
names only). One sentence: the GMSR sets the yardstick, the
walk and range set the boundary, buffers set the frontiers,
the ladder names the names, gates and protections prune,
robustness decides what survives to the client email.

### Q64. The Q63 chain made concrete — Taiwan's Aug-2026 worked example

Link by link with real numbers (ladder vintage): (1) 15.75 x
1.042 = 16.41 -> EM 8.21 -> range [4.10, 9.44]; (2) the walk
crosses at rank ~53 / $12.95B; (3) above the ceiling ->
membership expands, effective cutoff ~$9.44B (hence 77
members); (4) frontiers 6.29 / 14.16; (5) the ladder: delete
pool = 6919 4.94, 2834 5.44, 2609 5.46, 1101 5.63, 3529 5.69,
5871 5.87; sweep-sensitive survivors 3533 6.42, 8069 6.71,
3293 6.73, 5876 6.80, 2356 6.82; add side 2408 34.4 (census
46.7), 6505 20.8, 8046 18.3, 2344 18.0, below-bar 8299/3189/
6770; (6) gates: 6505 BLOCKED (float 0.12); 2408 passes all
(float 0.456 parent-named, half-bar 1.56-2.59x, room 88%);
8046/2344 pass in-frame; (7) fn22 doesn't bind (coverage
overshoots); (8) robustness: 2408 = the one STRONG call
(1.7-2.8x the bar in every frame, declared T-6); 8046/2344
frame-sensitive; delete ordering: 6919 safest call, 5871
within ~7% of the floor (price-sweep rescue-able), 3533 only
2% above it (nearest at-risk survivor). THE BOX: adds 2408
strong, 8046/2344 possible, 6505 excluded; deletes 6919/2834/
2609/1101/3529/5871. Graded at the Aug-12 announcement;
misses ship.

### Q65. How would CLSA's PT desk predict THIS shortlist (TW Aug-26) — and what data makes them more accurate?

Same eight links; at each one the desk READS what we ESTIMATE:
(1-2) reference via repricing the actual Appendix-X rank
company from the licensed daily DM universe (band ~fractions
of a pt vs our ±2); denominator exact from official FIFs/NOS —
our whole float stack is work they never do; (3-4) INTERIM
Market Size-Segment Cutoffs distributed to clients daily
(§3.2.1) — the frontier is read, not derived; (5) same public
prices, exact shares, evaluated on all 10 candidate dates; (6)
the gate labels change: 6505's float-block becomes certain
(official FIF), 8046/2344's "frame-sensitive" label DISSOLVES
(one exact denominator = one frame -> definite yes/no), 2408's
foreign room read from MSCI's published room fields; (7-8)
still no price date and no discretion foresight — 5871's
rescue-ability is THEIR uncertainty too; their edge there =
~40 graded reviews of MSCI behavior + the client-coverage
phone line + FLOW (their borrow desk sees locates building in
2609/1101; client inquiries reveal the street's consensus).
NET: their box differs from ours in CONFIDENCE, not much in
NAMES — the license converts our labeled assumptions into
facts and leaves the two unknowables (price date, discretion)
untouched.

### Q66. From the range to the shortlist — the RATIONALE at each step (teaching version)

Each step exists because the prior one left a problem: the
RANGE constrains but doesn't pick (MSCI's objective is still
85% of TAIWAN's buyable value) -> the WALK finds Taiwan's own
line (rank by full cap = "how big", accumulate float = "how
much can be owned"; TSMC ~half the float -> the line lands at
~rank 53 / $12.95B) -> the COLLISION ($12.95 > $9.44 ceiling
would break global comparability) resolves by GROWING THE
LIST, not shrinking the boundary (§2.3.3: all companies above
the ceiling enter; cutoff ~$9.44B; 77 members; coverage
overshoots — harmless, unlike a broken yardstick) -> the
FRONTIERS add hysteresis (thermostat logic: members deleted
only below 2/3x = $6.29B, entrants only above 1.5x = $14.16B
— turnover paid only for decisive changes) -> the LADDER makes
prediction two look-ups (retention test: 6 members below the
floor, 6919 deepest at -21%, 5871 shallowest at -7%; entry
test: 4 non-members above the bar; distance from frontier =
confidence, since caps are measured on ONE unknown July day)
-> the GATES add buyability (float floor kills 6505 at $20.8B;
half-bar, ATVR, room, universe date) -> protections + the
robustness sweep decide what ships. The shortlist is the
residue of six honest filters, each with a stated reason.

### Q67. Precision audit of the Q64 caps (user question — caught a real bug)

**Provenance of the Q64/Q66 ladder numbers:** FULL company
market cap (the correct GIMI basis for cutoff/floor/bar tests
— float matters only for coverage + half-bar), computed as
close x NumberOfSharesIssued ÷ FX from the vintage cache;
BOTH price and shares are 2026-07-31 vintage — the LAST day of
MSCI's own price window, i.e., a legitimate candidate price
day.

**The bug the question caught:** ladder_engine converted at FX
32.5 TWD/USD (stale) while the census uses 29.5 — and MSCI's
own factsheet arbitrates: TSMC float cap ÷ implied FIF ->
full cap ~$2,125B vs 62,367B TWD -> implied FX ≈ 29.3. The
32.5 understated every USD cap ~10%. FIXED (ladder FX -> 29.5,
suite green).

**Corrected pool (7/31 closes, 7/31 shares, FX 29.5):** DELETE
POOL = 6919 5.44, 2834 6.00, 2609 6.01, 1101 6.20, 3529 6.27
(all < 6.29) — **5871 EXITS the pool at 6.47** (the Q64 six
becomes five; 3529 is now the marginal name at 0.3% under the
floor — maximally price-date-sensitive). ADD side: order
unchanged (2408 37.9, 6505 22.9, 8046 20.2, 2344 19.8 all
clear the bar; 8299 12.3 / 3189 11.3 still below). The 2408
STRONG call and the 6505 float-block are UNAFFECTED (FX
cancels in ratios vs the bar by >30%); the frame-robust
verdicts survive; the pool's marginal names were always the
labeled uncertainty and the FX fix moved exactly them —
demonstrating why the precision audit mattered. Q64's numbers
stand as the historical record; THIS entry is the corrected
current state.

### Q68. Extending the TW framework to all APAC — readiness exam + membership complete (c-95)

MEMBERSHIP now complete for all 13 markets (ENZL 239672 / EWS
239678 / THD 239688 added to the harvester; ENZL+THD are IMI
anchors like EIDO/EPHE — Standard = composite subset). Counts
match factsheets EXACTLY: NZ 5, SG 16, TH 18 (13/13 total).
READINESS TIERS: full TW replication possible = Korea (KRX FF
ratios; short-ban era breaks), India (promoter floats better
than TW's; NO closing auction — Step-3 doesn't transfer),
Japan (JPX FFW; close-time era). Partial = China (two-stage
floats, borrow unobservable). Structurally capped at Frame A +
implied member FIFs = AU/HK/SG/MY (no float sources exist —
not closable, least harmful given deep DM floats). Semantic
restriction = Thailand (NVDR: float/room mean different
things). Small three (ID/PH/NZ): concentration means implied
FIFs cover most of the index (NZ Standard = 5 names). Next:
price the ladders via apac_member_census (resolvers wired).
Tests updated INTENTIONALLY (10->13; NZ n=5). Suite 468 green.

### Q69. Do default floats CREATE add candidates? (user pattern-spot in the walk display)

The mechanism check: NO — the add-candidate test is on FULL
cap (1.5x cutoff), which never touches ff, so a default float
cannot create a candidate. Where ff bites for adds is the
float gate (≥ 0.15) and the HALF-BAR (float cap ≥ 50% of the
boundary) — and there the risk runs OPPOSITE to the worry: a
too-high default FLATTERS a candidate. The user's instinct to
fetch real floats was right for exactly that reason. Fetched
(named-insider v2 method): 2408 = 0.456, 8046 = 0.381, 6505 =
0.120 — all BELOW the 0.55 default (2344 = 0.690 above; also
3189 0.604, 6274 0.872, 8299 0.852, 6770 0.790). Wired into
the walk as tier "v2_insiders_nonmember" (NONMEMBER_V2 in
cutoff_walk_v2). VERDICTS UNDER REAL FLOATS: 2408 float cap
17.3B, 2344 13.7B, 8046 7.7B — all clear the 4.72B half-bar
comfortably; 6505 blocked twice over (float 0.12 < 0.15 AND
float cap 2.7B < half-bar). Every shipped verdict SURVIVES;
what changed is that the shipped verdicts now rest on named
floats instead of defaults for all four names near the bar.
(Walk gap 6.3% vs implied — census MID-HARVEST, test tolerance
temporarily 8%, tighten after the floats phase.)

### Q70. Where do our TW ff values come from — is there a source with ALL companies?

No official all-company float file exists (Q47: TAIEX is
full-cap weighted; FTSE/MSCI floats are licensed) — ff is
DERIVED through three layers: (1) PRIMARY: TWSE MOPS monthly
insider-holding filings (directors/supervisors/officers/10%
holders — official, free, all companies, but per-company form
pages); (2) the AGGREGATED SHORTCUT we query: Yahoo
heldPercentInsiders (vendor aggregation of those filings) ->
ff = 1 − insiders (the v2 method); (3) VALIDATION: MSCI's own
implied FIFs from factsheet arithmetic (v2 graded 0.022;
gov-stake blind spot -> top-10 use implied directly). Files:
tw_float_mops_v2.json (76 members), factsheet archive implied
(top-10), NONMEMBER_V2 (8 bar names), insider_pct_cache (85),
mieu floats phase (= the all-companies extension, pending
Bill's `floats` run; shrinks the 11.7% default share).
Registered upgrade: scrape MOPS directly (layer 1) — the same
work MSCI's analysts do (Q48).

### Q71. THE FX SAGA RESOLVED — Q67's "fix" was circular; the live series arbitrates (c-108)

Phase 2's PIT-FX input check caught it: the live TWD=X series
reads Jul-26 ≈ 32.2-32.4, contradicting the 29.5 adopted in
Q67. The audit exposed MY circularity: "factsheet-implied FX ≈
29.3" assumed TSMC FIF ≈ 0.87 — but that FIF was computed by
dividing factsheet caps by census caps priced AT 29.5.
Breaking the circle with independent facts: TSMC holders (gov
~6.3%, insiders ~0.4%) -> true float ~0.93 -> MSCI FIF 0.95 ->
implied FX = 32.05 ✓ matching the live series. THE ORIGINAL
32.5 WAS APPROXIMATELY RIGHT; the Q67 correction was wrong.
FIX SWEEP (single source = data/fx_twd_history.json, monthly,
live): walk TWD -> 32.214, ladder FX, census FX. RESULTS: D =
$3,811B, gap vs implied +1.8% — the BEST frame agreement yet
(corroborating the fix); crossing rank 57 @ $11.07B — corridor
still binds in base and ff=0.40 frames, but at ff=0.70 the
crossing ($7.44B) falls INSIDE the corridor: the binding
conclusion is now flagged FRAME-SENSITIVE at the high-float
end (weaker than before — stated, not hidden). POOL at
7/31-close/FX-32.2: SIX names again — 6919 4.98, 2834 5.49,
2609 5.51, 1101 5.67, 3529 5.74, 5871 5.92 (Q67's five-name
pool superseded; 3533 nearest survivor at 6.48). Adds
unchanged: 2408 34.7 / 6505 20.9(blocked) / 8046 18.5 / 2344
18.2. LESSON: circular validation is invisible until an
INDEPENDENT input contradicts it — the halt-on-abnormal gate
did exactly its job.

### Q72. Did we verify all "OUT — off-cycle exit" rows? (c-113 — YES, to the limit of the data)

**Q:** After the ticker backfill (1,792/2,849 = 63%, stable),
can we now check the 405 UNPROBEABLE candidates?

**A:** The verification is now COMPLETE in the sense that every
candidate carries an evidence-based classification; 3 findings:

1. **The candidate list itself shrank 1,080 → 466** once
   tickers joined the entity keys. All 377 candidates that
   vanished in the first regeneration were verified one-by-one
   as CURRENT MEMBERS matched via ticker (APA GROUP, CHINA
   MERCHANTS BANK H, ANHUI CONCH A...) — name-variant false
   positives, exactly what the ticker-first design was for.

2. **75 probeable names: ALL still trading — and that's the
   signature, not a bug.** Selection bias explains the shape
   (Yahoo only issues tickers for live names, so dead names
   stay UNPROBEABLE), and the still-trading exits decompose
   into: **11 EO-13959 sanction deletions** — MSCI's own
   documented OFF-CYCLE waves (close of Jan 5/8/26 + Jul 26,
   2021: HIKVISION 002415.SZ is the flagship — correct
   ticker, still trading, genuinely out), 10 entity-splits
   (the DEL row exists under an unresolved variant:
   KASIKORNBANK FGN, BGF RETAIL (NEW), GUNGHO ENTMT...), and
   ~54 residual for the L4 queue (KANGMEI, BRILLIANCE,
   HAINAN AIR suspensions; ARTGO's inclusion-reversal).

3. **391 UNPROBEABLE remain honestly unproven**: no live
   ticker resolvable anywhere — CONSISTENT with genuine
   delisting (Yahoo drops dead symbols) but not positively
   confirmed. Positive confirmation needs exchange delisting
   archives (registered L4 task), not more Yahoo.

En route, the probe HALTED twice legitimately: once on the
all-STILL-TRADING anomaly (control probes TWTR/ATVI cleared
the mechanism), once on PING AN INS A appearing as an exit —
which exposed three real China ticker bugs (wrong-venue A→H
resolutions, ETF/index codes passing as equities, truncated
member names dropping the class letter) now fixed and pinned
in tests/test_offcycle_verify.py. Artifacts:
data/offcycle_exit_classified.csv, offcycle_verify_cache.json.

### Q73. Does MSCI publish full index constituents? (c-114 — YES, with two limits)

**Q:** I don't think MSCI produces the full member list — fact-check
this. If they do, take it from the website; if not, use fund
holdings. And can we reverse-engineer past membership back to 2006?

**A: They do publish it.** msci.com/constituents serves the complete
constituent list with closing weights for every index — but it exists
because EU **ESMA guidelines for ETFs/UCITS require it**, not as a
service, which is why it carries two limits that matter to us:

1. **~2-month delay.** Today (Aug 2026) it serves "As Of 01 Jun 2026" —
   the **May-2026** membership. It will not show Aug-2026 until roughly
   October. So it can never front-run a live review; for the Aug-26
   trade the iShares census remains primary.
2. **Names and weights only** — no tickers, shares, or float. Joining
   to a tradeable universe still needs our own entity resolution.

What it adds that nothing else did: **closing weights** (the project's
first real weight data — the ETF census has none) and an authoritative
dated anchor.

**The validation was the payoff.** Three independent MSCI artifacts —
the constituents tool, the July-2026 country factsheets ("Number of
Constituents"), and our iShares census built months earlier from a
different source — agree on index size in **all 13 markets**. Where
they didn't, the official list arbitrated: Taiwan's census said 79,
MSCI says 77, so 1602 Pacific Electric Wire and 2418 Ya Hsin are
EWT holdings that are not index members.

**Both your reverse-engineering routes were tried.** Route A
(historical fund holdings) is rejected as the spine: iShares publishes
only the *latest* holdings file, and an ETF's book is a portfolio
(sampling, cash, fair-value lines), not the index — it stays as a
cross-check. **Route B is implemented**: reverse-roll from MSCI's own
dated list back to Feb-2006, undoing one review at a time through the
count-validated changes database. Taiwan went 77 members (May-26) to
101 (Feb-06); Japan 168 to 390; China 576 to 221.

The estimate is honest about its error: off-cycle exits and IPO
fast-entries never appear in review lists, so the roll undercounts by
the number of off-cycle names already added at that point. That's
published as an uncertainty band on the chart, not buried. And the
band is corroborated — the additions the roll *cannot* undo turn out
to be 92–100% exactly the names the off-cycle audit independently
flagged (Taiwan 11 of 12, Australia 23 of 23), two pipelines built for
different purposes naming the same securities.

One halt fired: India's anchor produced 164 keys for 165 published
names because the entity key stripped all parentheses, merging VEDANTA
with VEDANTA (DETACHED) — the demerged line, a separate index
security. Country markers like (AU)/(CN) are noise; identity
qualifiers are not. Fixed, and the anchor now hard-gates against the
factsheet count.

### Q74. How should the plain-English walkthrough be built? (c-115)

**Q:** I want an easy-to-understand walkthrough of how we run the
point-in-time analysis, comprehensible to someone not in finance.
This is critical because we'll apply the same framework to explain
predictions for every APAC market.

**A: the decisive choice is that the walkthrough is GENERATED, not
written.** Every number in the narrative is interpolated from the
engine's own output at render time. Two consequences, and they are
the whole reason for the design:

- It cannot drift from the code. If the floor moves, the sentence
  moves. A hand-written explainer would be wrong within a quarter
  and nobody would notice.
- Pointing it at another market regenerates the entire story. Thirteen
  markets need **zero** additional prose — only their reconstructions.
  A test enforces this: any `$<number>B` literal appearing in prose
  without interpolation fails the suite.

**Two layers, because you have two audiences.** Each step carries a
`plain` layer (zero jargon, every term defined on first use — a friend
outside finance reads only this and gets the whole method) and a
collapsed `desk` layer (§3.1.9 cutoff window, §2.3.2.1 GMSR, error
bars, where the edge dies). Plus an always-visible **"what this step
can get wrong"** — the house rule, applied to teaching.

**The seven steps:** what's being decided and why money must move →
the photograph is taken before anyone sees it → how big is big enough
→ measuring at the frozen instant → draw the two lines → what we said
vs what MSCI did → what we still cannot know.

**The one interactive lever** sits at step 5: drag the size threshold
and watch companies cross it, with captured-removals and
wrongly-flagged updating live. It teaches the thing no paragraph can —
that there is no correct setting. Drop the line and false alarms
vanish along with real removals; raise it and you catch everything
while flagging half the index. That trade-off *is* the problem.

**Step 6 is where the honesty culture pays off pedagogically.** May-26
scored 7 of 7 removals caught and 8 false alarms — and the walkthrough
explains that the false alarms are not simply errors: our rule says
"below the floor", MSCI removes only a subset and judges the rest, so
the gap is MSCI's discretion *measured*, which is precisely the
prediction model's learning target.

Lives at page 4 of the site plus a self-contained HTML export (inline
CSS and SVG, no scripts or CDN, ~21KB — opens anywhere, prints, emails).

### Q75. What do the May-2026 rules actually say, and what did MSCI actually do? (c-117)

**Q:** Our addition engine is clearly wrong. Go to the May-2026
rulebook: how are the addition and deletion thresholds defined —
which price data, which date, which free float, how is the cutoff
calculated, and where does it say so? Any difficulty getting the
point-in-time data? And from the actual result, what calculation was
really used?

**A: the defect is bigger than the addition bar — we were anchoring
every threshold to the wrong number.**

The engine treated the **upper bound of the Global Minimum Size
Range** as the cutoff and hung 2/3 and 1.5 off it. §2.3.3 (p.26) says
the **Market Size-Segment Cutoff** is computed *per market* — sort
Taiwan's Investable Equity Universe by full market cap, cumulate
**float-adjusted** cap, take the full cap of the company at 85%
coverage; if it lands inside the range, that *is* the cutoff and its
rank becomes the Segment Number of Companies. The range (§2.3.2,
0.5×–1.15× the Global Minimum Size Reference, EM Standard $3.94–9.06B
for May-26) only *constrains* the cutoff; it is not the cutoff.

The buffers then hang off that computed number, not off the range:
§3.1.5.1 (p.43) — **"boundaries of 2/3rd of and 1.5 times the Market
Size-Segment Cutoff"** (0.5×/1.8× at light rebalancings, fn24).

And there is no single addition bar. §3.1.5 (p.42) is a priority list
filled **until the Segment Number of Companies is reached**: newly
investable companies need **≥ 1.0× cutoff**; Small Cap constituents
migrating up need **> 1.5×**; and between those two sits a queue —
*"the largest companies from the upper buffer of the next lower
size-segment"* — filled largest-first until the count is met.

**Dates (§3.1.9, p.48):** Equity Universe cutoff = last business day
of February for a May review; Liquidity cutoff = last business day of
March; **Price Cutoff = any one of the last 10 business days of
April**, and it governs *price, FIF, number of shares and foreign
room* — so point-in-time float is required by the rules, not optional.
May-2026 used **April 20, 2026** (disclosed in §2.3.2.1's worked
example). **Float gate (§2.3.6.1, p.30):** float-adjusted cap ≥ **50%
of the cutoff**, ×1.8 if FIF < 0.15, with existing constituents
getting 2/3 relief (§3.1.6.2).

**What MSCI actually did in May-2026.** At the disclosed cutoff date
the seven deletions ($3.48B–$4.76B) and the survivors ($5.19B and up)
are **perfectly separable**. So 2/3 × cutoff sits between $4.76B and
$5.19B, implying a **Market Size-Segment Cutoff of about $7.5B** —
inside the range, and well below the $9.06B ceiling we assumed. Run
the review with that cutoff and it scores **7 hits, 0 misses, 0 false
alarms**; the eight false alarms our engine produced were exactly the
names sitting between the true floor and our inflated one. MPI Corp,
the sole addition, comes in at 2.13× the inferred cutoff — clearing
the 1.5× upper buffer outright. Across the eight cleanly separable
reviews, **16 of 16 additions clear 1.0× the cutoff and only 8 of 16
clear 1.5×** — precisely the two-path structure of §3.1.5.

**The difficulty is one input.** Prices, shares, FX and the price date
are all obtainable. Computing the cutoff from first principles is not:
§2.3.3 needs a free-float factor for **every company in the Taiwan
universe**, at that date, and we hold float for ~11% of the relevant
names, current-vintage. That is the same D-grade input from the
backtest — but its role is now clear. Float is not a tie-breaker in
this methodology; **it sets the threshold that decides every case.**

So the reframe: our precision was never limited by the rule. It was
limited by our cutoff estimate. A fixed multiple of the ceiling cannot
repair it (tested on a grid — it just trades recall for precision)
because the true cutoff moves within the range each period, 0.56×–0.82×
the ceiling across clean reviews. Full write-up with page citations:
`docs/MSCI_SIZE_SEGMENT_SPEC.md`.

*(Next planned entry: the MIEU census result, then the
point-in-time review of prediction quality across 2015–2026.)*

### Q76. Where do the weights-inversion FIFs come from, and how does the inversion work? (c-139)

**The two public inputs.** (1) MSCI's official constituents
page for the Taiwan index (harvested by
`scripts/msci_constituents.py`) publishes every member's
**index weight** — gated in our harvester to sum to ~100%.
(2) The MSCI Taiwan **factsheet** publishes the index's total
float-adjusted market cap ($3,331.4B at Jun-01).

**The identity being inverted.** A cap-weighted index defines
each member's weight as

    weight_i = (P_i x S_i x FIF_i) / IndexFloatCap

Every quantity except FIF_i is public or computable by us:
weight_i (constituents page), IndexFloatCap (factsheet),
P_i x S_i = full cap (our PIT universe: TWSE close x
NumberOfSharesIssued, same date). Rearranged:

    FIF_i = weight_i x IndexFloatCap / (P_i x S_i)

**Worked example — MediaTek (2454).** weight 6.208% x
$3,331.4B = $206.8B MSCI float cap; our Jun-01 full cap
$229.26B; FIF = 206.8/229.26 = **0.902** -> MSCI grid 0.90.

**Why the date must match (and why it then cancels).** The
weight's numerator contains MSCI's price on date D; our full
cap contains OUR price on date D'. If D = D' the price
cancels exactly and pure FIF drops out. If D != D' the error
equals the price return between the dates — same lesson as
the implied-FIF work (price moves 6.0% in 11 days, float
0.39%): align dates and the method is exact; small
misalignment contaminates via price only.

**Self-validation (why we trust it).** The recovered FIFs
land ON MSCI's rounding grid without being asked to — Wan Hai
0.251 -> 0.25, Eva Air 0.501 -> 0.50 — a fingerprint no noisy
estimator produces. And the weight-derived float caps of the
top-10 reproduce the factsheet top-10 float caps (the
identity check that ties the two publications together).

**Coverage.** 60 of 77 members mapped (name->ticker prefix
matching limits, not method limits). Stored in
`data/tw_member_fifs_weights.json`; used as tier 2 of the
c-139 float policy stack (upgraded 53 names off Yahoo/TDCC,
median correction 2.3pp).

### Q77. Why only 60/77 members? Is the constituents page complete, and would EWT holdings help? (c-140)

**The 60/77 was OUR mapping gap, not MSCI's.** The public
constituents tool (the page behind
www-cdn.msci.com/web/msci/index-tools/constituents — the same
tool our harvester consumes via its JSON endpoint, index code
915800) carries ALL 77 Taiwan members and the weights sum to
exactly 100.000%. Seventeen names failed our name->ticker
prefix matcher on MSCI's abbreviations ('TAIWAN SEMICONDUCTOR
MFG', 'NOVATEK MICROELECTRS', 'TAIWAN COPR FINL HLDG'...) —
and they included TSMC itself at 54.78% weight. Fixed by a
17-line hand map in scripts/tw_fif_inversion.py:
**77/77 mapped, and all 77 recovered FIFs land on MSCI's
rounding grid within <=1pp** (TSMC 0.952->0.95, Hon Hai
0.873->0.875) — the strongest validation the method has
produced.

**So is the EWT route needed?** Not for coverage. But the
idea is sound and worth registering, with two caveats:
1. EWT tracks the MSCI Taiwan **25/50** (an IRS-capped
   version: no issuer >25%, sum of >5% weights <50%). Its
   WEIGHTS are therefore distorted vs the plain index —
   TSMC is capped far below its natural 54.8%. Inverting
   EWT weights directly gives WRONG FIFs for capped names.
2. The clean version uses SHARES HELD, not weights: for a
   replicating fund, shares_held_i / shares_outstanding_i =
   (TNA / IndexFloatCap) x FIF_i — a constant times FIF —
   and the constant calibrates off names whose FIF we know.
   Proportional 25/50 rescaling cancels for uncapped names.
**Where EWT genuinely adds value: FRESHNESS.** The ESMA
constituents tool is ~2 months delayed; iShares publishes
EWT's full holdings daily (T-1). Between MSCI publications,
daily EWT holdings could reveal FIF changes (block sales,
new caps) before the constituents tool does. Registered as a
data route (TW_DATASETS_BRAINSTORM.md), not built.

### Q78. How different are fund-derived FIFs (EWT) from weights-inversion FIFs? (c-141 — MEASURED: very)

Bill asked for the head-to-head table. Built
(`scripts/ewt_fif_compare.py`; EWT holdings as of Aug-06 via
the /latest-holdings.csv endpoint found in the page DOM —
all 77 members present in the fund). Method: hold-ratio
shares_held/shares_out = c x FIF, c calibrated on sub-5%
names.

**Result — the EWT route FAILS for FIF levels:**
- clean-name (sub-5%) median |gap| = **19.1pp**; p90 34.7pp;
  only 5.3% of names land within one grid step (2.5pp)
- several fund-implied "FIFs" exceed 1.0 (impossible):
  Taiwan Business Bank 1.246, Caliway 1.036
- cap cohort as predicted: TSMC 0.16 vs true 0.95,
  MediaTek 0.47 vs 0.90, Hon Hai 0.47 vs 0.87

**Why it fails (the real lesson):** EWT tracks the 25/50
CAPPED index, and with TSMC's natural weight at 54.8% the
cap forces ~34% of the index to be REDISTRIBUTED. The 5%/50%
aggregate constraint makes that redistribution iterative and
non-proportional — it contaminates every name, not just the
capped ones, so no single calibration constant can undo it.
On top sits representative-sampling noise. The
weights-inversion (plain index, Q76-Q77) remains the only
reliable public recovery of MSCI FIFs.

**What EWT holdings remain good for:** day-over-day CHANGES
(T-1 freshness) as a directional tell between MSCI
publications — levels no, deltas maybe. A fund tracking the
PLAIN index (e.g. iShares MSCI Taiwan UCITS) would be the
clean test of the fund route; the UK site geo-gated our
sandbox (HTTP 500) — registered as a terminal follow-up.
Artifacts: reports/ewt_fif_compare.csv (full 77-row table),
data/ewt_fif_compare.json.

### Q79. Do ALL funds tracking MSCI Taiwan use capped designs? Does MSCI itself cap? Is this universal? (c-142)

**1. Foreign-domiciled funds: capped BY REGULATION, not
choice.** EWT (US) tracks MSCI Taiwan 25/50 — the US
Internal Revenue Code's RIC diversification rules (no issuer
>25%, sum of >5% issuers <50%). ITWN (UCITS) tracked the
plain MSCI Taiwan Index until 2020-02-11, then switched to
MSCI Taiwan 20/35 — the UCITS concentration limits. TSMC at
~55% natural weight violates BOTH regimes, so no US or EU
fund CAN replicate the plain index.

**2. MSCI itself does NOT cap the plain country index.**
Confirmed three ways: (a) our own constituents harvest shows
TSMC at 54.78% — no cap applied; (b) the capped variants
exist as SEPARATE index families (25/50, 20/35, 10/40)
precisely because the parent is uncapped; (c) the GIMI
universe/cutoff machinery runs on FULL market caps
(§2.3.2.1) and weights on uncapped float caps — the capping
families sit downstream of index construction, applied only
for fund-regulatory consumption.

**3. Universal? Almost — with one useful exception.**
LOCALLY-domiciled funds escape both RIC and UCITS: the
Yuanta MSCI Taiwan ETF (006203.TW) tracks the PLAIN MSCI
Taiwan Index — TSMC weight 54.88%, matching MSCI's official
54.78% (vintage gap). Taiwan-listed, discloses holdings
daily. So an exact-weight fund DOES exist; registered as the
candidate FRESHNESS overlay (daily vs the ~2-month ESMA
delay) — to be tested with the same hold-ratio method that
failed on EWT (Q78) before trusting it (sampling noise
possible in a small fund).
Also: the capping only BITES in concentrated markets. Korea
(EWY -> 25/50, Samsung) has the same disease; India/Japan
funds (INDA, EWJ) track effectively-uncapped exposure since
no issuer approaches the caps — there, fund holdings ARE a
usable weights source.

**Verdict (Bill's argument, confirmed and sharpened):** for
Taiwan, US/EU fund weights are structurally wrong for FIF
work; the MSCI official weights inversion stays primary
despite its delay; 006203 daily holdings are the one fund
route worth testing for freshness.

### Q80. Top-10 FIF: Jul-31 factsheet-implied vs Jun-1 weights-inversion (c-143 — EXACT MATCH)

Two independent MSCI publications, two months apart, two
different derivations:
  - implied  = Jul-31 factsheet float cap / Jul-31 full cap
  - inverted = Jun-1 constituents weight x Jun-1 index float
               cap / Jun-1 full cap
All 10 names agree to the THIRD DECIMAL (TSMC 0.952=0.952,
MediaTek 0.902=0.902, ... Accton 0.902=0.902; max |diff|
0.0pp). Reading: FIF is a slow variable — MSCI left every
top-10 FIF untouched between publications — and both
recovery methods are exact, validating each other. This also
retroactively certifies the c-140 hand-mapping (TSMC, Hon
Hai, UMC recovered identically through both routes). Table:
reports/fif_factsheet_vs_weights.csv.

### Q81. How often does 006203 rebalance, does it front-run FIF changes, and which date's FIF governs the Aug review? (c-143)

**1. 006203 has no rebalance schedule of its own.** It is a
FULL-REPLICATION tracker of the plain MSCI Taiwan Index
(Yuanta product page / MoneyDJ), so it trades exactly when
the INDEX changes: at the four review effective dates
(Feb/May/Aug/Nov) plus any event-driven implementation MSCI
makes between reviews.

**2. A FIF change after Jun-1: two regimes (GIMI §3.2.3).**
- Event MEETS the Corporate Events implementation threshold
  (large placement, block sale, rights): MSCI implements the
  FIF change "simultaneously with the event" -> the index
  moves that day -> the fund rebalances that day -> its
  daily holdings REVEAL the change ~T+1. This is exactly the
  freshness value of the 006203 overlay.
- Event BELOW threshold (gradual drift, NOS <±1%): MSCI
  itself defers to the next Index Review (§3.1.7/3.1.8) —
  the index does not move, so the fund does not either.
  Nothing to observe, because the OFFICIAL FIF genuinely
  has not changed yet. The fund can never front-run MSCI;
  it can only echo implementations fast.

**3. The governing date (§3.1.9 + §3.1.7): the Price Cutoff
Date.** For the Aug-2026 review, MSCI uses security data —
price, NOS, FIF, foreign room — as of one undisclosed day
among the LAST 10 BUSINESS DAYS OF JULY. §3.1.7: "FIF
changes are implemented as part of a given Index Review if
the changes take place prior to the Price Cutoff Date...
changes effective after... postponed to the next closest
Index Review" (escape hatch: MSCI MAY still include late
changes, announceable until 3 b-days before effective).
The Equity Universe Cutoff (last b-day of May) governs the
universe list and EUMSR, not FIFs. Our Jul-31
factsheet-implied FIFs — which Q80 showed identical to the
Jun-1 inversion on the top-10 — are therefore exactly the
right vintage for the prediction: hence the 20260720-31
universe harvest.

### Q82. Yuanta 006203 (Aug-7) vs MSCI Jun-1 weights: do they match, and is Jun-1 FIF safe for the Aug prediction? (c-143 — YES)

Fund holdings scraped from the Yuanta ratio page (Trade Date
2026-08-07, all 77 names + quantities; saved
data/yuanta_006203_holdings.json). Two tests:

**1. Weights (fund Aug-7, renormalized, vs Jun-1 MSCI
weights rolled forward by prices to Jul-31):** median |diff|
**0.022pp**, p90 0.12pp across all 77. The fund IS the Jun-1
index composition, moved only by prices. The one visible
gap — TSMC 56.29% vs 58.14% expected (−1.85pp) — is fund
mechanics, not index information: 006203 runs a 1.04%
futures sleeve and odd-lot practicalities that dilute the
mega-position slightly.

**2. Hold-ratio FIF (quantity/shares, price-free):** median
|diff| 1.9pp vs the weights-inversion FIFs; the tail (p90
7.8pp) is concentrated in sub-0.2%-weight positions (2615
held just 6,928 shares — creation-basket rounding dominates)
— replication noise, not FIF signal.

**Verdict — agree with Bill, with three stated caveats:**
Jun-1 weights-inversion FIFs are SAFE for the Aug-26
prediction, because (Q80) the Jul-31 factsheet reproduces
them exactly on the top-10 AND (this test) the live fund
shows no implemented FIF change through Aug-7, bracketing
the late-July Price Cutoff window. Caveats: (a) the
guarantee covers implemented changes only — a big corporate
event before the cutoff would appear in the index and fund
first (none has); (b) don't read FIF levels off the fund for
micro-weight names; (c) fund weights carry a small
futures-sleeve bias on TSMC.

### Q83. CORRECTION — where the $3,331.4B "Jun-1 index float cap" actually came from (c-145)

**I described it in-session as read off a June factsheet.
That is wrong, and the record is corrected here rather than
edited silently.** MSCI publishes a factsheet monthly, but
our archive holds only the JUL-31 edition ($3,183.0B). The
Jun-1 figure was never published to us — it was SOLVED
(c-126b, "FIF-constancy calibration").

**The derivation.** For each of the ten Jul-31 factsheet
anchors, assume its FIF did not change between Jun-1 and
Jul-31 (floats drift ~0.4%/11 days vs prices ~6%), then

    IdxCap(Jun-1) = FIF_Jul31 x full_cap_i(Jun-1) / weight_i

Ten independent solutions: 3331.0 / 3331.1 / 3331.4 (x2) /
3331.5 / 3331.6 / 3331.7 (x2) / 3331.8 (x2) — **spread
0.026%**. Ten different companies, ten different sizes, one
answer. That agreement is what justified the constant.

**The consequence, which must be stated: Q80's "exact match"
on the top-10 is NOT independent evidence.** IdxCap(Jun-1)
was calibrated by assuming precisely those ten FIFs constant,
so their Jun-1-inverted and Jul-31-implied values agree BY
CONSTRUCTION. Q80 demonstrates internal consistency (and that
the 17-name hand map didn't corrupt the anchors), not
external validation.

**What DOES independently validate the Taiwan FIFs:**
1. **The 67 non-anchor members.** Nothing forces them onto
   MSCI's 2.5% grid — yet all 77 land within 1pp (c-140).
2. **Grid-snap (c-144).** It uses only weights, full caps and
   the grid — never the anchors, never any index float cap —
   and independently recovered c = 33.27 vs the calibrated
   33.314 (0.13%). An unrelated route reaching the same
   constant is the real check.
3. **The live fund (Q82).** 006203's Aug-7 weights match the
   Jun-1 composition price-rolled forward to 0.022pp median.

Net: the number stands, the evidence for it is different
from what I first said, and the anchor-circularity is now on
the record.

### Q84. Is "rank by full cap, accumulate float cap to 85%" the correct MSCI method? (c-149 — YES, verbatim)

Bill restated the engine's logic from walk_display.html. It is
correct, and §2.3.3 says it almost word for word:
  - "The companies in the Market Investable Equity Universe
    are sorted in descending order of FULL market
    capitalization."
  - "The cumulative FREE FLOAT-ADJUSTED capitalization
    coverage of the Market Investable Equity Universe is
    calculated at each company."
  - MSCI notes the FULL market cap of the company providing
    70% (Large), **85% (Standard)**, 99% (IMI) coverage.
  - If that full cap sits inside the Global Minimum Size
    Range, it IS the Market Size-Segment Cutoff and the count
    of companies at or above it becomes the Segment Number of
    Companies, "used to maintain the indexes over time". If
    not, the COUNT flexes until it fits.

Three refinements to the restatement:
1. **85%, not 90%.** The +-5% in §2.3.1 is the tolerance band
   the RESULT may land in, not the target.
2. **Coverage is of the MIEU** — the post-screen universe —
   not of the whole listed market. And the crossing company's
   FULL cap is the cutoff, while the accumulator is FLOAT cap.
   Two different columns; mixing them is the classic error.
3. **Additions are not "everything above the cutoff."**
   §3.1.5: >=1.0x cutoff is necessary, >1.5x is guaranteed,
   the gap is a priority queue; and incumbents get 2/3
   relief (§3.1.4.2). That relief is why walk_display shows
   77 members but only 67 companies above the ceiling.

Screens confirmed against the rulebook (Bill's list was
right; exact clauses):
  §2.2.3 full cap >= Equity Universe Minimum Size Req ($537M)
  §2.2.4 float-adj cap >= 50% of EUMSR ($268.5M)
  §2.2.5 ATVR 3m/12m >= 15% + 80% frequency of trading
  §2.2.6 FIF >= 0.15
  §2.2.7 3 months of trading before implementation (IPOs)
  §2.2.8 foreign room >= 15%
  §2.2.9 financial reporting (we mark NOT_EVALUATED)

So the addition side needs exactly what Bill described: every
listed company in the market, screened, ranked, accumulated.
That is the universe file — the one input the weights
inversion can never supply.

### Q85. Is the factsheet's 3,183,008.39 full or float-adjusted cap — and which do we accumulate? (c-151)

**The factsheet number is FLOAT-ADJUSTED market cap, in USD
millions: $3,183.0B.** Proof from our own data, no
interpretation needed: the factsheet's TSMC line is
$1,848.51B, our measured FULL cap for TSMC at the same date
is $1,941.23B, and 1848.51/1941.23 = **0.952 — exactly
TSMC's FIF**. A full-cap table would show 1,941, not 1,848.
Same for every top-10 line (their 10 sum to $2,443B vs
$2,666B of full cap).

**Both measures are used, for different jobs (§2.3.3):**
  - RANK the universe by FULL market cap
  - ACCUMULATE FREE FLOAT-ADJUSTED cap down that ranking
  - the cutoff VALUE is the FULL cap of the company where
    cumulative FLOAT coverage hits 85%

Taiwan at 2026-07-31, measured:
  MIEU float total          $3,609B
  85% target                $3,068B
  crossing                  rank 52 (3481), cum float
                            $3,072B, FULL cap $11.22B
  rank 77 (count stability) FULL cap $6.74B, cum float
                            $3,224B = 89.3% coverage

**Cross-check on the factsheet:** index float cap $3,183.0B
divided by our MIEU float $3,609B = **88.2% coverage** —
inside the §2.3.1 85%+-5% band, and close to the 89.3% our
rank-77 walk implies. Two independent constructions agreeing
to ~1pp is the strongest evidence the universe is measured
correctly.

**Which cutoff the engine uses, and why it matters:** the
raw crossing says $11.22B, the count-stability rank-77 says
$6.74B. We use $6.74B because §2.3.3 says the Segment Number
of Companies is "used to maintain the indexes over time",
and the factsheet still shows 77 constituents. If MSCI let
the count shrink toward the raw crossing instead, far more
names would go. That single choice is the largest source of
error in the Aug call and is carried as the count_flex
haircut (x0.85) on every probability.

### Q86. Can we replace the MIEU build with "factsheet index float / 0.85"? (c-151 — NO, but keep it as the error bar)

**Does it follow the rulebook? No.** §2.3.3 defines a
PROCEDURE, not an identity: sort the MIEU by full cap,
accumulate float-adjusted cap, note the company whose full
cap sits at 85% coverage. The universe determines the index.
Dividing the index by 0.85 reverses that arrow and assumes
the outcome landed exactly on target. §2.3.1 explicitly makes
85% a TARGET RANGE (+-5%), so the assumption is not merely
unsupported — for Taiwan it is measurably false: realised
coverage is 88.2%, so /0.85 overstates the universe by 3.7%
(3,745 vs our measured 3,611).

**And it cannot produce a cutoff anyway.** The cutoff is the
full cap of a SPECIFIC company. A scalar total names no
company; the ranked list is still required. Worse, feeding
MSCI's denominator into OUR ranked list mixes numerator and
denominator from two different constructions: the crossing
then lands at rank 69 ($7.34B) largely because ~$3,183B of
our list IS the index membership. That is an artifact of list
composition, not an independent measurement of the cutoff.

**What it IS good for, and how we already use it:**
1. COMPLETENESS CHECK. The band [index/0.90, index/0.80] =
   [$3,537B, $3,979B] is where a correctly-built MIEU float
   total must sit. Ours ($3,611B) is inside — evidence the
   universe is not materially missing names. This is the
   `implied_denominator_busd` / `cutoff_corridor_busd` already
   stored in apac_factsheet_archive.
2. ERROR BAR ON THE CUTOFF. Measured walk says $11.22B;
   count-stability rank-77 says $6.75B; Bill's /0.85 route
   says $7.34B. The two MSCI-anchored numbers cluster low and
   apart from the raw walk — so the defensible range for the
   Aug call is **$6.75-11.22B**, not a point estimate, and
   the count_flex haircut is justified rather than cosmetic.

**Verdict:** build the MIEU (it is the rulebook's own
procedure and the only route to names); use the factsheet
ratio to validate the build and to size the uncertainty.


## Q87 — How do we know a company is delisted, rather than
## just missing from our data?

We stopped inferring it and started checking a register. The
TWSE and TPEx open-data endpoints publish every currently
listed company (1,983 codes as of 08 Aug 2026). If MSCI's
historical member code is absent from that list, the exchange
is telling us it no longer trades. That is evidence. Our
earlier method — "our search found nothing, so it must be
gone" — is not evidence, and it was wrong nine times out of
the twelve names tested, because those companies had simply
been RENAMED.

The asymmetry worth remembering for the desk: a rename keeps
the code, a merger kills it. Checking the CODE against the
live register separates the two cleanly; checking the NAME
never will.
