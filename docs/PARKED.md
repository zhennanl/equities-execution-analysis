# PARKED — decisions waiting on Bill

The mechanism that lets me work without stopping. When a choice
is genuinely yours, I write it here with a recommendation, skip
the item, and continue. Answer a batch whenever you like.

Nothing here is blocking anything else.

---

## P1 — "IND" appears twice in the APAC strip
India and Indonesia both truncate to IND at three letters. The
strip is deliberately narrow, so full names do not fit.
OPTIONS: 4-letter codes (INDI/INDO, breaks the grid slightly) ·
ISO-style (IN/ID/JP/TW, shortest and unambiguous but less
readable at a glance) · leave it.
MY PICK: ISO-style two-letter. It is what a desk uses anyway,
and it removes the collision rather than papering over it.

## P2 — pre-2015 rows are half-estimated
1,534 of 4,403 change rows have no ticker, and pre-2015 rows
also have an ESTIMATED effective date (eff_date_est) with no
announcement date at all. They are real MSCI changes, so they
belong in counts, but they cannot support anything date-precise.
OPTIONS: show everywhere with a provenance flag · show only in
counts, exclude from date-based views · a 2015+ toggle defaulting
to on.
MY PICK: provenance flag plus a toggle. The 2006-2014 era is
genuinely interesting for churn, and useless for timing.

## P3 — is the Philippines shown or hidden here?
It is excluded from the forward pipeline (no data source) but
its review HISTORY is real and complete. Today it is absent
from the selector. On an informational page that arguably loses
data for no reason.
OPTIONS: keep hidden · show in history-only views with an
"excluded forward" tag.
MY PICK: show it, tagged. This page makes no predictions, so
the reason for the exclusion does not apply to it.

## P4 — the findings sweep produces 17 statements, 9 of them nearly identical
Seven are "market X runs N adds per deletion" and nine are
"market X was quiet at N% of reviews". Individually each clears
the bar; together they are a table pretending to be prose.
OPTIONS: promote as TWO tables (skew by market, quiet rate by
market) rather than 17 sentences · keep only the extremes
(Japan 0.50, India 2.07) as sentences and drop the middle ·
leave as is.
MY PICK: two tables. The per-market numbers are genuinely
useful side by side and useless one at a time — and a table is
presentation, not assertion, so it stays inside the spec.

## P5 — four markets have a REVERSING add/delete skew
Hong Kong 1.16 -> 0.47, Indonesia 1.33 -> 0.56, Korea 1.62 ->
0.72, Philippines 1.56 -> 0.35 across the Feb-2016 split. Each
full-sample ratio looks unremarkable because the two eras
cancel. That reversal is arguably more interesting than any of
the 17 that survived — four APAC markets flipping from net
adding to net deleting in the same decade.
OPTIONS: promote as a finding in its own right · leave in the
REJECTED section · investigate first (is it index expansion
into EM, or genuine shrinkage?).
MY PICK: investigate before promoting. I can tell you the sign
flipped; I cannot yet tell you why, and the why is what makes
it a finding rather than an artefact of MSCI's own coverage
changes.

## P6 — spec section 4 "Membership time machine" never renders
`_time_machine()` is defined in views/history_explorer.py,
contains its own `_sect(4, ...)`, and is NEVER CALLED — the
call site at line ~1008 is a bare comment with nothing under
it. It has been dead since before the lint existed, and the
lint reported CLEAN over it twice because it read `_sect()`
calls in the source instead of checking what reaches the
screen.

The function itself looks complete: it reads
membership_history.json and reconstructs index composition at
any review back to 2006.

OPTIONS: restore the call (one line) · delete the function and
drop section 4 from the spec · leave dead.
MY PICK: restore it. But it is a CONTENT change, and you said
"without changing the content of the website at this moment" —
so it waits for you. The lint now prints it as a KNOWN GAP on
every run rather than passing silently.

## P7 — the per-market "Most recent change" block was removed
c-214 replaced the first snapshot with an all-markets grid that
carries the names on hover. That made the old per-market
"Most recent change" section a SECOND "Section 1" answering the
same question for one market, so I removed it. Its quiet-review
statistic moved into section 2 rather than going with it.

What is genuinely gone: a persistent, printable list of the
selected market's latest movers. The hover shows it, but hover
cannot be read on a phone and does not survive a screenshot.
OPTIONS: leave as is · restore it under a different number ·
add a click-to-pin so the card stays open.
MY PICK: leave it for now, and revisit if you find yourself
wanting the names visible without a mouse.

## P8 — the ticker-coverage disclosure is now nowhere on the site
c-218 removed section 6 ("All APAC compared") at Bill's
request. Its "Tickered" column was the LAST place the coverage
figure appeared, after the status strip that carried it was
removed at c-214.

The fact it disclosed: 17% (Taiwan) to 55% (Australia) of
change rows carry no ticker, so ticker-keyed views (roster,
lookup) and count-based views (timeline, figures) are counting
different populations. Nothing on the page now says so.

OPTIONS: a one-line caption under the Security lookup table ·
restore the scoreboard · accept it, since docs/ still records
it and this is an informational page rather than a data-quality
report.
MY PICK: the one-line caption. It costs a line and it is the
only disclosure that stops two sections quietly disagreeing.
Not doing it unilaterally — you have removed this number twice
now, which I read as a preference rather than an oversight.
