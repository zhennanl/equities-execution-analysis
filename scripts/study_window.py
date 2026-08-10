"""The date floor for the announcement -> effective study
(c-188).

Bill: limit the rebalance-window analysis to 2015 onwards.

WHY THIS IS THE RIGHT CUT, not just a shorter one. The windows
had two different pedigrees:

  2015+       announcement dates come from the REGISTRY — MSCI's
              actual published announcement date. 135 windows.
  2010-2014   announcement dates were ESTIMATED as
              effective - N business days. 44 windows.

The estimate was measurably wrong. Against the 34 real
announcements the true gap is a median of 13 business days
(mean 13.2, range 12-17); the estimator used 10, placing day-0
THREE SESSIONS LATE. Day-0 is the baseline that the whole study
defines as zero cumulative return, so a late day-0 puts part of
the announcement reaction inside the baseline.

So cutting at 2015 does not just shorten the sample — it drops
every window whose day-0 was inferred rather than known. What
remains is measured end to end. That is worth more than five
extra years of quietly biased observations.

WHAT IS LOST, stated plainly: 44 of 179 windows (25%), and the
2010-2014 era bucket. Any statement about how the trade behaved
before 2015 is now out of scope rather than weakly supported.

The raw windows are NOT deleted — the harvest keeps them on
disk. This is a READ-TIME filter, so raising or lowering the
floor is one edit and needs no re-harvest.
"""

FLOOR = "2015-01-01"
FLOOR_YEAR = 2015

REASON = ("2015+ only: before 2015 the announcement date was "
          "estimated (effective - 10 business days) rather than "
          "taken from MSCI's registry, and that estimate was "
          "measured to be 3 sessions late — which contaminates "
          "day-0, the study's zero baseline.")


def keep(window):
    """True if this window's announcement is inside the floor."""
    ann = str(window.get("ann") or "")
    if not ann:
        return False
    return ann >= FLOOR


def filter_windows(windows):
    """Accepts the dict or list form used across the studies."""
    if isinstance(windows, dict):
        return {k: v for k, v in windows.items() if keep(v)}
    return [w for w in windows if keep(w)]


def note(n_before=None, n_after=None):
    s = REASON
    if n_before is not None and n_after is not None:
        s += f"  ({n_before} windows -> {n_after})"
    return s
