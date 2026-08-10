# Registered open items

## R1 — SWAP THE STEP-5 CHART WHEN FLOAT ARRIVES  (Bill, c-174)
The animated walk in "Predict MSCI Index Changes"
currently accumulates FULL market cap, which is the §2.3.3
SORT order, and its caption says so. The moment free float
lands for the shortlisted names, change it to accumulate
FLOAT-adjusted cap and draw the 85% coverage crossing — that
is the line MSCI actually sets the cutoff on.
  Files: views/walkthrough.py `_walk_animation`, and the
  caption directly beneath it.
  Also revisit: step 4's float-stack paragraph, and
  derive_cutoff's "seed only" wording, which exists purely
  because we lack float today.

## R2 — AUSTRALIA'S MEMBER LIST IS INCOMPLETE
derive_cutoff protects a country-flagged name from exclusion
IF it is a current MSCI member. That protection is only as
good as apac_members.json. Australia holds 47 names there;
MSCI Australia is larger. The country check flagged ResMed,
Amcor, James Hardie and Fisher & Paykel as foreign, and only
Xero was matched as a member — so the others are being
excluded from the anchor when MSCI may well assign them to
Australia. AU's cutoff carries that risk today.
  Fix: refresh apac_members.json for Australia, then re-run
  `shortlist Australia`.

## R3 — HONG KONG'S COUNT ANCHOR IS UNRELIABLE
111 of 165 checked names flagged foreign, and the ones that do
NOT flag include China Mobile and CNOOC — HK-INCORPORATED
companies that sit in MSCI China, not MSCI Hong Kong.
Incorporation cannot separate the two indexes. The shortlist
prints [LOW CONFIDENCE] for this market. Needs MSCI's own
Hong Kong member list to bound it properly.

## R4 — PHILIPPINES EXCLUDED, REVERSIBLY
See scripts/markets.py. Delete one dict entry to restore.


## R5 — YAHOO HAS NO SHARE COUNT FOR SOME LARGE MEMBERS
Verified in BOTH v7/quote and v10/quoteSummary
(defaultKeyStatistics + price): a valid price comes back and
sharesOutstanding / marketCap are null. Without shares there
is no market cap and the name cannot be sized.

Worst in Australia — 29 names, 13 of them MSCI members
(ANZ, CSL, NAB, MQG, GMG, QBE, IAG, CPU, EVN, TLS, WOW, TCL,
STO). Also Kweichow Moutai (600519.SS), the largest A-share.

This is NOT fixed by re-running. It needs a share-count source
per market: ASX company data for Australia, SSE/SZSE for the
A-share gap. Until then those markets' ladders are missing
real members and their cutoffs are biased.

## R6 — MSCI CHINA SPANS THREE VENUES
183 of 576 China members are unmatched because our China
universe is region=cn (SSE + SZSE) only. MSCI China also holds
H-shares listed in Hong Kong (1024, 1044, 1088, ...) and US
ADRs. Those rows exist in the HongKong size file and as bare
symbols; the China universe needs to merge them before its
cutoff means anything.

## R7 — MALAYSIA AND SINGAPORE MEMBER MATCHING
Malaysia matches 1/21, Singapore 8/16 — members are stored as
local short names/codes the size file does not key on. Needs
the verified hand map, as in c-165.


## R8 — MEMBER LISTS ARE FUND HOLDINGS, AUDITED c-179
Checked every market's holdings count against the MSCI
factsheet. 9 of 12 match EXACTLY. Three do not:

  Taiwan  EWT 79 vs factsheet 77 (+2). Cause identified: the
    holdings carry 1602 and 2418, BOTH of which the exchange
    register says are delisted. Stale lines in the fund file.
  Korea   EWY 78 vs factsheet 77 (+1). Cause: preferred-share
    lines — 005935 Samsung Electronics pref, 005385/005387
    Hyundai Motor pref. These are real securities and MSCI
    Korea does hold preferreds, so the +1 is a counting
    convention difference, not stale data. Needs a decision
    rather than a fix.
  NewZealand  no factsheet count parsed at all; falls back to
    the ENZL holdings (5). Unverified.

The CUTOFF is already insulated: derive_cutoff prefers the
factsheet count where one exists (c-177). NZ still runs on the
fund count and is the one to watch.

TO DO: purge delisted tickers from the holdings lists using
data/dead_tickers.json, and parse the NZ factsheet count.

## R9 — TWO WRONG TICKERS FOUND IN THE COLLISION AUDIT (c-202)

Auditing every ticker in msci_changes_db that carries more than
one MSCI spelling (25 of them) turned up two that are not
renames, and both trace to a bad ticker upstream:

  India ENRIN     mapped to BOTH "SIEMENS INDIA" (ADD May06,
                  DEL Nov18, ADD Nov19) and "SIEMENS ENERGY
                  INDIA" (ADD Nov25). Siemens Energy India was
                  DEMERGED from Siemens India and listed
                  separately in 2025 — two companies. ENRIN is
                  also not the NSE symbol for either; NSE
                  carries SIEMENS and SIEMENSENRG. This is why
                  both India event-window fetches for ENRIN
                  came back empty.
                  FIX: split the rows and re-map the tickers in
                  the changes DB.

  China 000596    carried by both "ANHUI GUJING A (HK-C)" and
                  "ANHUI GUJING DISTILLER B". Same issuer, but
                  the A line is 000596 and the B line is
                  200596. The B row has the A ticker.
                  FIX: re-map the B row to 200596, or drop it
                  if B shares are out of scope for the study.

Until then both are in views/history_explorer.NEVER_MERGE, so
the page shows them as separate rows marked with a warning
rather than silently inventing one company. The display is
honest; the data is still wrong.
