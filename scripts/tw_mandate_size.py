#!/usr/bin/env python3
"""How big is the indexed mandate that owns MSCI Taiwan?

    py scripts\\tw_mandate_size.py

THE QUESTION, c-349 (Bill): *"add an estimate to the size of
investment mandate for MSCI Taiwan tracking fund, make it more
conservative, but can show evidence to back up our claim."*

Two words in that sentence are doing all the work. CONSERVATIVE
means the number must be one this project can defend downwards —
if it is wrong, it should be wrong by being too small. EVIDENCE
means every step has to point at a document with a date on it,
not at a market-colour figure someone repeats.

scripts/tw_tracking_aum.py already sums the funds it can NAME.
That is a floor and it is honest, but it is knowably incomplete:
it counts ETFs, and only the ETFs one analyst could enumerate off
issuer pages. This file asks what is missing and bounds it from
MSCI's own filings.

────────────────────────────────────────────────────────────────
THE THREE THINGS MSCI DISCLOSES THAT MAKE THIS ANSWERABLE

Every input below is from MSCI Inc.'s own Q2 2026 reporting for
the quarter ended 30 June 2026 — the 8-K earnings release and the
earnings presentation, both filed 21 July 2026. MSCI is a public
company reporting to the SEC on the assets its indexes are
licensed against, which makes it the one source on this question
that carries an audit trail.

  1. ETF AUM linked to MSCI equity indexes: USD 2,818bn at
     quarter end, of which USD 841bn sits in the "Emerging
     Markets / All Country" exposure bucket. MSCI defines that
     bucket as indexes whose weight is mostly NOT in developed
     markets, explicitly including All Country. Every fund that
     can hold Taiwan through an MSCI index is inside it.

  2. Asset-based fee revenue, split three ways in the quarter:
     ETFs USD 161.0m, NON-ETF INDEXED FUNDS USD 56.0m, futures
     and options USD 16.1m. The middle line is the one nobody
     quotes, and it is the whole point of this file — it is the
     institutional separate accounts, index mutual funds and
     pension mandates that hold the same indexes without a
     ticker.

  3. The fee rate MSCI earns on ETFs: 2.28 basis points at
     period end, on quarterly average AUM of USD 2,706bn.

────────────────────────────────────────────────────────────────
THE INFERENCE, AND WHY ITS ERROR RUNS ONE WAY

MSCI does not publish the AUM behind the non-ETF indexed line. It
publishes the REVENUE. So invert it at a fee rate:

    non-ETF indexed AUM  =  non-ETF ABF revenue / fee rate

and the only question is which rate. This file uses the ETF rate,
2.38bp annualised from the same quarter's revenue and average
AUM. That choice is deliberate and it is the conservative one:

    AN INSTITUTIONAL INDEX MANDATE PAYS AN INDEX PROVIDER LESS
    PER DOLLAR THAN A RETAIL ETF DOES.

Mandates are larger, negotiated one at a time, and tiered — the
opposite of a fund-level licence struck once and applied to every
share sold. So the true non-ETF rate is BELOW the ETF rate, and
dividing by a rate that is too high returns an AUM that is too
small. The number this file prints is therefore a floor on the
non-ETF pool, not an estimate of it, and the direction of the
error is fixed rather than unknown.

It lands at roughly USD 940bn, or 0.33x the ETF pool — for every
dollar of MSCI-linked ETF money there is at least 33 cents of
MSCI-linked mandate money with no ticker on it.

────────────────────────────────────────────────────────────────
WHAT THIS FILE DELIBERATELY DOES NOT DO

The obvious second move is to gross the Taiwan number up for ETF
COVERAGE: the named funds are USD 472bn against a disclosed
bucket of USD 841bn, so the enumeration catches 56% and one could
multiply by 1.78x. THAT WOULD BE WRONG, and the reason is worth
writing down because it is the trap in this whole exercise.

The unnamed 44% is not a scaled copy of the named 56%. It
contains every single-country EM ETF — MSCI China, MSCI India,
MSCI Korea, MSCI Brazil — each of which sits in the same
"Emerging Markets / All Country" bucket and holds EXACTLY ZERO
Taiwan. Grossing up on bucket share would credit Taiwan with
money that is contractually forbidden from owning it.

So the coverage ratio is reported as EVIDENCE THAT THE FLOOR IS A
FLOOR, and no multiplier is taken from it. The only multiplier
applied is the non-ETF one, which does not have this problem: a
mandate benchmarked to MSCI EM holds Taiwan in the same weight an
ETF benchmarked to MSCI EM does.

────────────────────────────────────────────────────────────────
THE CORRECTION THIS FILE ALSO MAKES

tw_tracking_aum.py's `case_promotion` — the money that must buy a
Taiwan Standard addition whatever its size segment — counts the
Standard EM and ACWI trackers and stops. It omits the USD 13.4bn
of ETFs on the MSCI Taiwan indexes themselves.

That is an omission, not a judgement call. A stock entering the
MSCI Taiwan Standard universe enters the MSCI Taiwan Index and
its 25/50 and 20/35 variants at the same review. EWT has to buy
it exactly as EEM does. Adding it takes the always-buys floor
from USD 31.7bn to USD 45.0bn.

And using the UNCAPPED weight for the capped funds is itself
conservative: 25/50 capping cuts TSMC to 25% and redistributes
the excess across everything else, so a 0.4% name is bought at
MORE than 0.4% of a 25/50 tracker, not less.

────────────────────────────────────────────────────────────────
WHAT TO DO WITH THE ANSWER

The headline is a pair, and the pair is the honest form:

  * ALWAYS BUYS, conservative:  named ETFs x the non-ETF floor.
  * IF NEW TO THE IMI: the same, with the IMI trackers added at
    their 1.16x weight discount.

Both are still floors. Nothing here reaches the sovereign wealth
and pension money that indexes internally and reports to nobody,
and nothing reaches a mandate whose benchmark is MSCI EM but
whose manager licenses through a third party. The estimate is
built to be defended, not to be impressive.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUM = ROOT / "data" / "tw_tracking_aum.json"
OUT = ROOT / "data" / "tw_mandate_size.json"
DOC = ROOT / "docs" / "TW_MANDATE_SIZE.md"

REL = ("https://ir.msci.com/news-releases/news-release-details/"
       "msci-reports-financial-results-second-quarter-and-six-"
       "months-10")
PRES = "https://ir.msci.com/static-files/65e23650-540f-4ec1-a089-9526ba54c1b9"
SEC8K = ("https://www.sec.gov/Archives/edgar/data/0001408198/"
         "000140819826000044/exhibit991earningsrelease-.htm")

# ── MSCI Inc. Q2 2026, quarter ended 2026-06-30 ────────────────
#
# Transcribed from the filings, not from a summary of them. Each
# figure carries the table it came from so a reader can open the
# document and land on the row.
MSCI = {
    "as_of": "2026-06-30",
    "filed": "2026-07-21",
    "etf_aum_total_usd_b": 2818.0,       # 8-K Table 7, period end
    "etf_aum_avg_usd_b": 2706.0,         # 8-K Table 7, quarterly avg
    "etf_bp_fee_period_end": 2.28,       # 8-K Table 7
    "etf_aum_us_usd_b": 1319.0,          # presentation p13
    "etf_aum_em_ac_usd_b": 841.0,        # presentation p13
    "etf_aum_dm_ex_us_usd_b": 658.0,     # presentation p13
    "abf_etf_usd_m": 161.0,              # presentation p13, 2Q26
    "abf_non_etf_indexed_usd_m": 56.0,   # presentation p13, 2Q26
    "abf_futures_options_usd_m": 16.1,   # presentation p13, 2Q26
    "abf_total_usd_m": 233.1,            # 8-K Table 5
    "sources": {"release": REL, "presentation": PRES,
                "sec_8k": SEC8K},
}


def _check_msci():
    """The transcription has to tie to MSCI's own totals.

    Cheap, and it is the check that catches the realistic failure
    here — a digit typed wrong out of a PDF. Both identities are
    published, so neither is an assumption."""
    m = MSCI
    abf = (m["abf_etf_usd_m"] + m["abf_non_etf_indexed_usd_m"]
           + m["abf_futures_options_usd_m"])
    assert abs(abf - m["abf_total_usd_m"]) < 0.15, abf
    aum = (m["etf_aum_us_usd_b"] + m["etf_aum_em_ac_usd_b"]
           + m["etf_aum_dm_ex_us_usd_b"])
    assert abs(aum - m["etf_aum_total_usd_b"]) < 1.0, aum
    return {"abf_components_sum": round(abf, 1),
            "exposure_buckets_sum": round(aum, 1)}


def non_etf_floor():
    """The mandate pool MSCI reports revenue on but not assets.

    Returns the implied AUM and the multiplier it justifies, both
    as FLOORS — see the module docstring for why the fee-rate
    choice fixes the sign of the error."""
    m = MSCI
    # annualised effective rate actually realised on ETFs, from
    # this quarter's revenue over this quarter's average AUM.
    # Used in preference to the disclosed 2.28bp period-end
    # figure because it is the rate on the same revenue line the
    # non-ETF number is being divided by.
    bp = (m["abf_etf_usd_m"] * 4) / (m["etf_aum_avg_usd_b"] * 1000
                                     ) * 10000
    aum = (m["abf_non_etf_indexed_usd_m"] * 4) / (bp / 10000) / 1000
    return {
        "etf_effective_bp_annualised": round(bp, 3),
        "etf_bp_disclosed_period_end": m["etf_bp_fee_period_end"],
        "non_etf_indexed_aum_floor_usd_b": round(aum, 1),
        "multiplier_floor": round(aum / m["etf_aum_total_usd_b"], 4),
        "why_it_is_a_floor":
            "Priced at the ETF fee rate. Institutional index "
            "mandates are larger, negotiated and tiered, so they "
            "pay an index provider LESS per dollar than a retail "
            "ETF does — dividing by a rate that is too high "
            "returns an AUM that is too low.",
    }


def taiwan(a, nef):
    """Taiwan's slice, from named funds outward."""
    T = a["method1_bottom_up"]["totals"]
    ratio = a["method1_bottom_up"]["standard_over_imi"]
    named_etf_aum = (T["standard_fund_aum"] + T["imi_fund_aum"]
                     + T["family"])
    # THE CORRECTION. A stock entering MSCI Taiwan Standard
    # enters the MSCI Taiwan Index and its capped variants at the
    # same review, so EWT and the UCITS range buy it too. The
    # published `case_promotion` counts only the EM and ACWI
    # trackers.
    always_etf = T["standard_tw"] + T["family"]
    imi_etf = T["imi_tw"] / ratio
    mult = 1.0 + nef["multiplier_floor"]
    return {
        "named_etf_aum_usd_b": round(named_etf_aum, 1),
        "disclosed_em_ac_etf_aum_usd_b":
            MSCI["etf_aum_em_ac_usd_b"],
        "named_share_of_disclosed_bucket":
            round(named_etf_aum / MSCI["etf_aum_em_ac_usd_b"], 4),
        "always_buys_named_etf_usd_b": round(always_etf, 2),
        "always_buys_published_usd_b": T["case_promotion"],
        "taiwan_dedicated_etf_usd_b": T["family"],
        "imi_adds_if_new_usd_b": round(imi_etf, 2),
        "mandate_multiplier": round(mult, 4),
        "estimate_always_buys_usd_b": round(always_etf * mult, 1),
        "estimate_if_new_to_imi_usd_b":
            round((always_etf + imi_etf) * mult, 1),
        "coverage_note":
            "The named ETFs are "
            f"{named_etf_aum / MSCI['etf_aum_em_ac_usd_b']:.0%} of "
            "the disclosed EM/All-Country ETF bucket. The "
            "remainder is NOT grossed up: it contains "
            "single-country EM ETFs — MSCI China, India, "
            "Korea, Brazil — that hold no Taiwan at all, so "
            "scaling on bucket share would credit Taiwan with "
            "money that cannot own it.",
    }


def main():
    if not AUM.exists():
        raise SystemExit("run scripts/tw_tracking_aum.py first")
    a = json.loads(AUM.read_text(encoding="utf-8"))
    ties = _check_msci()
    nef = non_etf_floor()
    tw = taiwan(a, nef)
    o = {"_what": "a conservative, source-backed estimate of the "
                  "indexed mandate that must buy an MSCI Taiwan "
                  "Standard addition",
         "generated": dt.datetime.now().isoformat(timespec="seconds"),
         "msci_disclosure": MSCI,
         "transcription_ties": ties,
         "non_etf_indexed": nef,
         "taiwan": tw,
         "reading": [
             "Every figure is a FLOOR. The error in each step "
             "runs one way, and it is stated where the step is "
             "taken.",
             "The ranking between candidate names is unaffected "
             "by the level — the level is a common "
             "multiplier.",
         ]}
    OUT.write_text(json.dumps(o, indent=1), encoding="utf-8")

    d = [
        "# How Big Is the MSCI Taiwan Mandate?",
        "",
        f"Generated {o['generated']}. Source data: MSCI Inc. Q2 "
        f"2026 results for the quarter ended "
        f"{MSCI['as_of']}, filed {MSCI['filed']}.",
        "",
        "## The disclosures this rests on",
        "",
        "| Figure | Value | Where |",
        "| --- | --- | --- |",
        f"| ETF AUM linked to MSCI equity indexes | USD "
        f"{MSCI['etf_aum_total_usd_b']:,.0f}bn | 8-K Table 7 |",
        f"| of which Emerging Markets / All Country | USD "
        f"{MSCI['etf_aum_em_ac_usd_b']:,.0f}bn | presentation "
        f"p13 |",
        f"| Quarterly ABF revenue, ETFs | USD "
        f"{MSCI['abf_etf_usd_m']:,.1f}m | presentation p13 |",
        f"| Quarterly ABF revenue, non-ETF indexed funds | USD "
        f"{MSCI['abf_non_etf_indexed_usd_m']:,.1f}m | "
        f"presentation p13 |",
        f"| Period-end ETF basis point fee | "
        f"{MSCI['etf_bp_fee_period_end']:.2f} bp | 8-K Table 7 |",
        "",
        "## The one inference",
        "",
        f"MSCI publishes the REVENUE on non-ETF indexed funds and "
        f"not the assets. Inverting it at the ETF rate "
        f"({nef['etf_effective_bp_annualised']:.2f}bp annualised "
        f"from the same quarter) gives **USD "
        f"{nef['non_etf_indexed_aum_floor_usd_b']:,.0f}bn**, or "
        f"**{nef['multiplier_floor']:.2f}x** the ETF pool.",
        "",
        nef["why_it_is_a_floor"],
        "",
        "## Taiwan",
        "",
        f"- Named ETFs that must buy a Standard addition: USD "
        f"{tw['always_buys_named_etf_usd_b']:,.1f}bn "
        f"(includes the USD {tw['taiwan_dedicated_etf_usd_b']:,.1f}"
        f"bn on the MSCI Taiwan indexes themselves, which "
        f"`tw_tracking_aum.py` omitted).",
        f"- With the mandate multiplier: **USD "
        f"{tw['estimate_always_buys_usd_b']:,.0f}bn**.",
        f"- If the name is new to the IMI: **USD "
        f"{tw['estimate_if_new_to_imi_usd_b']:,.0f}bn**.",
        "",
        "## What is deliberately not claimed",
        "",
        tw["coverage_note"],
        "",
    ]
    DOC.write_text("\n".join(d), encoding="utf-8")

    print(f"non-ETF indexed floor   USD "
          f"{nef['non_etf_indexed_aum_floor_usd_b']:,.0f}bn "
          f"({nef['multiplier_floor']:.3f}x ETFs) at "
          f"{nef['etf_effective_bp_annualised']:.2f}bp")
    print(f"named ETFs / bucket     "
          f"{tw['named_share_of_disclosed_bucket']:.1%} "
          f"(USD {tw['named_etf_aum_usd_b']:,.0f}bn of "
          f"{tw['disclosed_em_ac_etf_aum_usd_b']:,.0f}bn)")
    print(f"always buys, named ETF  USD "
          f"{tw['always_buys_named_etf_usd_b']:,.1f}bn "
          f"(published {tw['always_buys_published_usd_b']:,.1f})")
    print(f"ESTIMATE, always buys   USD "
          f"{tw['estimate_always_buys_usd_b']:,.0f}bn")
    print(f"ESTIMATE, new to IMI    USD "
          f"{tw['estimate_if_new_to_imi_usd_b']:,.0f}bn")
    print(f"wrote {OUT.name}, {DOC.name}")


if __name__ == "__main__":
    main()
