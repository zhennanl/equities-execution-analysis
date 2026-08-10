# BACKLOG — MSCI Index Review Database

Ordered. Work top to bottom. Every item states a DONE that can
be evaluated without Bill in the room.

Tags: [order] section priority · [density] screen budget ·
[data] correctness · [lint] mechanical check

---

## 1. [order] Latest review across all 13 markets, as a strip
Bill: *"only a snapshot, that is very easy to read, and doesn't
take a lot of space."* Today the page leads with the SELECTED
market's latest review; the spec wants all of APAC first.
DONE: a single strip above the market selector showing the most
recent review label and, per market, add/delete counts; height
under ~90px; renders for every market selection; no market
hardcoded.
STATUS: done c-209.

## 2. [lint] page_lint.py enforces the spec
DONE: `py scripts\page_lint.py` exits non-zero when section
order drifts from PAGE_SPEC section 3, a section lead exceeds
200 chars, or a market list is hardcoded in the view.
STATUS: done c-209.

## 3. [density] Section leads to one line
Spec voice is minimal. Several leads are two or three lines of
prose explaining things the reader knows.
DONE: every `_sect` lead <= 200 chars; page_lint green.
STATUS: done c-210. All five leads now 43-57 chars.

## 4. [data] Show the 35% of rows with no ticker
1,534 of 4,403 change rows have no ticker — mostly pre-2015 and
delisted names. They are currently invisible in ticker-keyed
views, which makes counts silently disagree between sections.
DONE: a coverage line stating rows with and without a ticker
per market, and every count on the page reconciles to one of
the two.
STATUS: done c-210. Coverage is in the status strip; amber below 80%.

## 5. [order] Move seasonality below the security lookup
Spec puts it 7th; it currently sits 2nd.
DONE: order matches spec section 3; page_lint green.
STATUS: done c-210. Now renders after section 6.

## 6. [density] Constituent view earns its space
Section 3 in the spec ("who is in the index right now") is what
Bill meant by the weight breakdown, so it is a first-class
section, not an expander.
DONE: promoted out of the expander, weights sorted descending,
tenure shading retained, under one screen.
STATUS: done c-210. Out of the expander, sorted by weight.

## 7. [data] Cross-market scoreboard
All 13 markets on one table: reviews, changes, add/delete skew,
quiet-review rate, churn. No free source presents this.
DONE: sortable table, every column traceable to the changes DB,
Philippines shown in history but flagged as excluded forward.
STATUS: done c-210. Section 7, Philippines included and tagged.

## 8. [density] Kill the remaining Streamlit default spacing
DONE: no `st.header`; all section rules via `design.sect`.
STATUS: already clean — no st.header in the view.

## 9. [data] Candidate findings pass
Sweep the database for statements that clear n>=30 and hold in
both halves of the sample. Do NOT put them on the page.
DONE: `docs/CANDIDATE_FINDINGS.md` populated, each with n,
method, and the one-line claim, for Bill to pick from.
STATUS: done c-210. 17 survived, 4 rejected.


---

BACKLOG EMPTY as of c-210. New items go at the
bottom with a definition of done.
