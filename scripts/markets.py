"""Which APAC markets the pipeline covers — and which it does
not, with the reason (c-174).

WHY A CENTRAL LIST rather than deleting the country from
twenty files: the Philippines has a real MSCI review HISTORY,
and that history is legitimate data. Scrubbing it out of the
changes database would corrupt the APAC-wide statistics
(reviews per period, seasonality, churn) and destroy a record
we cannot rebuild. So the country is EXCLUDED FROM THE
FORWARD PIPELINE AND THE UI, and its history stays intact
underneath.

This also keeps the decision reversible. If a Philippine data
source turns up, deleting one dict entry restores it.

THE EVIDENCE for the exclusion, probed 2026-08-08:
  v7/finance/quote  AC.PS, BDO.PS, SM.PS, ICT.PS, BPI.PS,
                    JFC.PS, TEL.PS, ALI.PS -> symbol echoed
                    back with EVERY field null: no marketCap,
                    no sharesOutstanding, no price, no
                    currency, no name.
  v8 chart AC.PS -> a result shell with no price in meta and
                    no close series.
  screener region "ph" -> total 0.
So there is no market cap, which means no §2.2.3 size screen,
which means no cutoff and no prediction. PSE Edge does serve
company NAMES (202 harvested in c-165) but not prices or
share counts, so it cannot fill the gap on its own.
"""

EXCLUDED = {
    "Philippines":
        "no usable data source — Yahoo returns null for every "
        "field on every PSE symbol, and the screener reports "
        "region 'ph' total 0. Without market cap there is no "
        "size screen. History retained; forward pipeline and "
        "UI exclude it.",
}

ACTIVE = ["Japan", "HongKong", "China", "Korea", "Taiwan",
          "India", "Australia", "Malaysia", "Indonesia",
          "Singapore", "Thailand", "NewZealand"]


def is_active(market):
    return str(market) not in EXCLUDED


def filter_markets(names):
    """Drop excluded markets from any list of market names."""
    return [m for m in names if is_active(m)]


def why_excluded(market):
    return EXCLUDED.get(str(market))
