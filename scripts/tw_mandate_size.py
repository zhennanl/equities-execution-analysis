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
THE FOUR THINGS MSCI DISCLOSES THAT MAKE THIS ANSWERABLE

Every input below is from MSCI Inc.'s own Q2 2026 reporting for
the quarter ended 30 June 2026 — the 8-K earnings release, the
earnings presentation (both filed 21 July 2026), and management's
statements on the earnings call. MSCI is a public company
reporting to the SEC on the assets its indexes are licensed
against, which makes it the one source on this question that
carries an audit trail.

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

  4. c-400: the non-ETF pool itself. Management put the non-ETF
     indexed AUM at ABOUT USD 5 TRILLION as of 30 June on the
     Q2 2026 earnings call — client-reported, one quarter in
     arrears. This is the number the file used to have to infer.

────────────────────────────────────────────────────────────────
THE ANCHOR, AND THE FLOOR IT RETIRES (c-400)

Earlier versions of this file had no asset figure for the
non-ETF line, so they inverted the USD 56.0m of quarterly
revenue at the ETF fee rate. That was a floor by construction —
mandates pay less per dollar than ETFs, so dividing by a rate
that is too high returns an AUM that is too small. It landed at
roughly USD 940bn, or 0.33x the ETF pool.

The disclosed USD 5tn replaces the inversion as the anchor:

    5,000 / 2,818  =  1.77x the ETF pool

— for every dollar of MSCI-linked ETF money there is about
USD 1.77 of MSCI-linked mandate money with no ticker on it.
The revenue line the old floor was built from now works the
other way, as the CROSS-CHECK on the disclosure:

    56.0m x 4 / 5,000bn  =  0.45bp

— roughly a fifth of the 2.28bp ETF rate, which is exactly the
mandates-pay-less relationship the floor argument asserted. The
two disclosures are consistent with each other, and the old
inversion is kept in the output as `floor_variant` (basis
~USD 60bn) for anyone who wants the number that needs no
call-transcript citation.

The one assumption the anchor adds: the USD 5tn spans every MSCI
index family, so applying the aggregate ratio to the
Taiwan-relevant ETF pool assumes the mandate mix mirrors the ETF
mix. That is the step a licensed mandate census would replace.

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

  * ALWAYS BUYS: named ETFs x (1 + the disclosed non-ETF/ETF
    ratio). The floor variant — the old fee inversion — rides
    along in the output for the downside case.
  * IF NEW TO THE IMI: the same, with the IMI trackers added at
    their 1.16x weight discount.

Nothing here reaches the sovereign wealth and pension money that
indexes internally and reports to nobody, and nothing reaches a
mandate whose benchmark is MSCI EM but whose manager licenses
through a third party. The estimate is built to be defended, not
to be impressive.
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
CALL = ("https://www.investing.com/news/transcripts/earnings-"
        "call-transcript-msci-tops-q2-2026-estimates-but-shares-"
        "fall-93CH-4803910")

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
    # c-400: MSCI DISCLOSES the non-ETF pool now — management
    # put it at "about $5 trillion as of June 30" on the Q2
    # 2026 earnings call (client-reported AUM, one quarter in
    # arrears). This replaces the fee inversion as the anchor;
    # the inversion survives below as the floor variant.
    "non_etf_aum_disclosed_usd_b": 5000.0,   # Q2-26 call
    "sources": {"release": REL, "presentation": PRES,
                "sec_8k": SEC8K, "earnings_call": CALL},
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
    # c-400, Bill: THE ANCHOR MOVES TO THE DISCLOSED NUMBER.
    # MSCI now states the non-ETF pool outright (~USD 5tn, Q2-26
    # call), so the estimate uses the disclosed AUM directly and
    # the derived NON-ETF fee rate becomes the cross-check:
    #     56.0m x 4 / 5,000bn = 0.45bp
    # against 2.28bp on ETFs — mandates pay roughly a fifth per
    # dollar, which is exactly why the old inversion (at the ETF
    # rate) was a floor. That inversion is KEPT below as the
    # floor variant.
    disc = m["non_etf_aum_disclosed_usd_b"]
    non_etf_bp = (m["abf_non_etf_indexed_usd_m"] * 4) / (
        disc * 1000) * 10000
    return {
        "etf_effective_bp_annualised": round(bp, 3),
        "etf_bp_disclosed_period_end": m["etf_bp_fee_period_end"],
        "non_etf_aum_disclosed_usd_b": disc,
        "non_etf_bp_derived": round(non_etf_bp, 3),
        "multiplier_disclosed": round(
            disc / m["etf_aum_total_usd_b"], 4),
        "non_etf_indexed_aum_floor_usd_b": round(aum, 1),
        "multiplier_floor": round(aum / m["etf_aum_total_usd_b"], 4),
        "why_the_floor_was_a_floor":
            "The old inversion priced the USD 56.0m at the ETF "
            "fee rate. Mandates are larger, negotiated and "
            "tiered — the disclosed pool implies they actually "
            "pay ~0.45bp, a fifth of the ETF rate — so dividing "
            "by the ETF rate understated their assets by "
            "construction.",
        "assumption":
            "Applying the aggregate non-ETF/ETF ratio to the "
            "Taiwan-relevant ETF pool assumes the mandate mix "
            "mirrors the ETF mix at the index-family level. "
            "MSCI does not break the USD 5tn out by index, so "
            "this is the step a licensed mandate census would "
            "replace.",
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
    # c-400: the multiplier is the DISCLOSED ratio; the old
    # fee-inverted 0.33x survives as the floor variant.
    mult = 1.0 + nef["multiplier_disclosed"]
    mult_floor = 1.0 + nef["multiplier_floor"]
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
        # the c-349 fee-inversion floor, kept as the downside
        # variant of the same arithmetic
        "floor_variant_multiplier": round(mult_floor, 4),
        "floor_variant_usd_b": round(always_etf * mult_floor, 1),
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
             "Every input is MSCI's own disclosure; the one "
             "assumption (mandate mix mirrors ETF mix) is "
             "stated where it is taken, and the old "
             "fee-inversion floor rides along as the downside "
             "variant.",
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
        f"| Non-ETF indexed AUM | ~USD "
        f"{MSCI['non_etf_aum_disclosed_usd_b']:,.0f}bn | Q2-26 "
        f"earnings call |",
        "",
        "## The anchor, and the floor it retires",
        "",
        f"MSCI stated the non-ETF indexed pool at **~USD "
        f"{MSCI['non_etf_aum_disclosed_usd_b']:,.0f}bn** on the "
        f"Q2 2026 call — "
        f"**{nef['multiplier_disclosed']:.2f}x** the ETF pool. "
        f"The revenue line is the cross-check: USD "
        f"{MSCI['abf_non_etf_indexed_usd_m']:.1f}m x 4 / USD "
        f"{MSCI['non_etf_aum_disclosed_usd_b']:,.0f}bn = "
        f"**{nef['non_etf_bp_derived']:.2f}bp**, about a fifth "
        f"of the {MSCI['etf_bp_fee_period_end']:.2f}bp ETF rate.",
        "",
        f"The old inversion of that revenue at the ETF rate "
        f"({nef['etf_effective_bp_annualised']:.2f}bp annualised) "
        f"gave USD "
        f"{nef['non_etf_indexed_aum_floor_usd_b']:,.0f}bn, or "
        f"{nef['multiplier_floor']:.2f}x — kept as the floor "
        f"variant.",
        "",
        nef["why_the_floor_was_a_floor"],
        "",
        nef["assumption"],
        "",
        "## Taiwan",
        "",
        f"- Named ETFs that must buy a Standard addition: USD "
        f"{tw['always_buys_named_etf_usd_b']:,.1f}bn "
        f"(includes the USD {tw['taiwan_dedicated_etf_usd_b']:,.1f}"
        f"bn on the MSCI Taiwan indexes themselves, which "
        f"`tw_tracking_aum.py` omitted).",
        f"- With the mandate multiplier "
        f"({tw['mandate_multiplier']:.2f}x): **USD "
        f"{tw['estimate_always_buys_usd_b']:,.0f}bn**.",
        f"- If the name is new to the IMI: **USD "
        f"{tw['estimate_if_new_to_imi_usd_b']:,.0f}bn**.",
        f"- Floor variant (fee inversion, "
        f"{tw['floor_variant_multiplier']:.2f}x): USD "
        f"{tw['floor_variant_usd_b']:,.0f}bn.",
        "",
        "## What is deliberately not claimed",
        "",
        tw["coverage_note"],
        "",
    ]
    DOC.write_text("\n".join(d), encoding="utf-8")

    print(f"non-ETF pool, disclosed USD "
          f"{nef['non_etf_aum_disclosed_usd_b']:,.0f}bn "
          f"({nef['multiplier_disclosed']:.3f}x ETFs), implied "
          f"{nef['non_etf_bp_derived']:.2f}bp")
    print(f"floor variant (invert)  USD "
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
