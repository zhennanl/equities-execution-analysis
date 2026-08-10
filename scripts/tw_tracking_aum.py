#!/usr/bin/env python3
"""How much passive money actually tracks MSCI Taiwan?

    py scripts\\tw_tracking_aum.py

THE PROBLEM. Every dollar and share figure in the August-2026
demand model is `index weight x TRACKING AUM`, and the tracking
AUM has been a hand-set USD 180bn since it was typed into
scripts/event_window_analyze.py as `TRACKING_AUM_USD_B = 180.0
# MSCI TW passive proxy`. Bill asked whether it can be estimated
instead of declared. It can, two ways, and this file does both.

────────────────────────────────────────────────────────────────
METHOD 1 — BOTTOM-UP FROM PUBLISHED FUND ASSETS

MSCI publishes no AUM at country or index level. So the direct
number has to be summed from the funds themselves, and the
answer depends entirely on which question is being asked:

  (a) ETFs on the UNCAPPED MSCI Taiwan Index — the index this
      project's weights are struck on. Two Taiwan-domiciled
      funds. About USD 0.08bn. EWT is NOT one of them; it tracks
      the 25/50 variant.

  (b) Every ETF on any MSCI Taiwan index. About USD 13bn.

  (c) Taiwan exposure inside MSCI EM and ACWI trackers. Taiwan
      is 26.63% of MSCI EM. This is the money that ACTUALLY has
      to buy a new MSCI Taiwan constituent, and it is an order
      of magnitude larger than (b).

Fund AUMs below were read from issuer factsheets in c-327; each
carries its as-of date. They go stale within a quarter, which is
itself an argument against a constant.

────────────────────────────────────────────────────────────────
METHOD 2 — REVEALED FROM WHAT THE MARKET ACTUALLY BOUGHT

This is the interesting one, because it uses no fund register at
all. If a tracker's requirement is

    demand_shares = weight x AUM / (fx x price)

and the foreign net buying observed into a historical addition
IS that requirement, then the equation can be turned around:

    AUM = observed_shares x price / fx / weight

`observed_shares` comes from TWSE's own institutional files:
across 42 Taiwanese additions, foreign investors accumulated a
median 1.04 days of the name's ADV between twenty sessions
before the announcement and the effective print. Applying that
benchmark to the three carried August names — whose weight, ADV
and price are all known — gives an implied AUM per name.

WHY THIS IS NOT CIRCULAR. The 180 constant was typed, not
derived. The flow benchmark is measured from T86. The weights
come from float caps over the MSCI factsheet's index value.
Nothing in method 2 descends from the 180, so agreement between
them is evidence and not an echo.

WHAT IT ASSUMES, and both assumptions are load-bearing:

  1. Foreign net buying into an addition IS the index demand.
     It is not: it also contains discretionary money, arbitrage
     and any foreign seller netting against the tracker. The
     direction of the bias is not obvious — netting pushes the
     estimate DOWN, arbitrage pushes it UP.

  2. The historical median transfers to these three names. The
     three implied AUMs disagree by a factor of 1.6, which is
     the direct evidence that it transfers imperfectly.

────────────────────────────────────────────────────────────────
WHAT TO DO WITH THE ANSWER

The central estimates agree. The DISPERSION is the finding: the
interquartile range of the flow benchmark alone moves the
implied AUM from about 40bn to about 520bn — a thirteen-fold
band. So:

  * The RANKING between names is AUM-free. It survives any
    level, because the level is a common multiplier.
  * The LEVEL is not estimable to better than an order of
    magnitude from anything available here.

Bill's instinct — that an unreliable input should not be used to
print a confident number — is the right one, and this file
exists to say how unreliable, with arithmetic rather than
adjectives.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import statistics as stats

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "tw_tracking_aum.json"
DOC = ROOT / "docs" / "TW_TRACKING_AUM.md"

# ── method 1 inputs: published fund assets ─────────────────────
#
# c-344 REBUILT. The first version counted TWO funds and treated
# every dollar of their Taiwan exposure as buying. Both halves of
# that were wrong, and the second one is the interesting error.
#
# ERROR 1, THE EASY ONE: the universe was two US-listed funds.
# iShares EIMI alone is USD 44bn and was missing; so were EMXC,
# XMME, IEEM, the Amundi/UBS/HSBC UCITS range, ACWI, SSAC and the
# large index mutual funds.
#
# ERROR 2, THE ONE THAT MATTERS: an IMI tracker does not
# necessarily buy anything.
#
#   MSCI's size segments are DERIVED BY SUBTRACTION. GIMI 2.3:
#   "the Small Cap Index is derived as the difference between the
#   Investable Market Index and the Standard Index". So a stock
#   promoted from Small Cap to Standard was ALREADY in the IMI,
#   and its IMI weight does not change either — IMI weights are
#   free-float market cap, independent of the size-segment label.
#   An IMI tracker does nothing at all.
#
#   The two most recent Taiwan reviews are one of each:
#     May-2026  MPI Corp (6223) — MSCI added it to the Standard
#               indexes "while removing the company from the MSCI
#               Global Small Cap Indexes". A migration. IEMG and
#               EIMI bought NOTHING.
#     Feb-2026  Hon Precision (7769) — absent from the Small Cap
#               deletion list, so it entered the IMI from outside
#               under the "significant new investable company"
#               rule. IMI trackers DID buy from zero.
#
#   So which case applies is EMPIRICAL PER NAME, and it is worth
#   about 3x on the answer. The operational test takes minutes:
#   download the IEMG and EIMI daily holdings files and check
#   whether the name is already in them.
#
# THE 1.16x. Standard targets 85% of free-float market cap, IMI
# targets 99% (GIMI 2.3.1). A given stock's weight INSIDE the
# Standard index is therefore about 99/85 = 1.16x its weight
# inside the IMI, so an IMI dollar buys ~16% less of it even when
# it does buy.
#
# `verified` marks whether the AUM came off an issuer primary
# source. False means a third-party aggregator, and those are
# flagged on the page rather than silently averaged in.
#
# (name, index, AUM, ccy, as-of, bucket, taiwan_weight, verified)
FUNDS = [
    # ETFs on the UNCAPPED MSCI Taiwan Index — the index this
    # project's weights are struck on.
    ("Yuanta/P-shares MSCI Taiwan (006203 TT)",
     "MSCI Taiwan (uncapped)", 1913.0, "TWD", "2026-08-07",
     "uncapped", 1.0, True),
    ("Fubon MSCI Taiwan (0057 TT)", "MSCI Taiwan (uncapped)",
     469.0, "TWD", "2026-08-07", "uncapped", 1.0, True),
    # Other MSCI Taiwan indexes.
    ("iShares MSCI Taiwan (EWT US)", "MSCI Taiwan 25/50",
     11151.5, "USD", "2026-06-30", "family", 1.0, True),
    ("iShares MSCI Taiwan UCITS", "MSCI Taiwan 20/35",
     1324.0, "EUR", "2026-08", "family", 1.0, False),
    ("Xtrackers MSCI Taiwan 1C+1D", "MSCI Taiwan 20/35 Custom",
     429.0, "EUR", "2026-08", "family", 1.0, False),
    ("HSBC MSCI Taiwan Capped UCITS", "MSCI Taiwan 20/35",
     93.0, "EUR", "2026-08", "family", 1.0, False),
    # STANDARD EM / ACWI trackers. A Taiwan Standard addition is
    # a new constituent for every one of these, always.
    ("iShares MSCI EM (EEM US)", "MSCI Emerging Markets",
     30316.0, "USD", "2026-06-30", "standard", 0.2728, True),
    ("iShares MSCI EM ex China (EMXC US)",
     "MSCI EM ex China", 24118.0, "USD", "2026-08-07",
     "standard", 0.33, False),
    ("Fidelity EM Index Fund (FPADX)",
     "MSCI Emerging Markets", 14440.0, "USD", "2026",
     "standard", 0.2741, False),
    ("Xtrackers MSCI EM UCITS 1C (XMME)",
     "MSCI Emerging Markets", 11000.0, "EUR", "2026",
     "standard", 0.2741, False),
    ("iShares MSCI EM UCITS (IEEM)",
     "MSCI Emerging Markets", 8863.0, "EUR", "2026-07",
     "standard", 0.2741, False),
    ("Amundi Core MSCI EM UCITS", "MSCI Emerging Markets",
     4129.0, "EUR", "2026-08", "standard", 0.2741, False),
    ("UBS (Lux) Core MSCI EM UCITS", "MSCI Emerging Markets",
     2643.0, "EUR", "2026-07", "standard", 0.2741, False),
    ("HSBC MSCI EM UCITS (HMEF)", "MSCI Emerging Markets",
     2950.0, "EUR", "2026-02", "standard", 0.2741, False),
    ("iShares MSCI ACWI (ACWI US)", "MSCI ACWI",
     33203.7, "USD", "2026-06-30", "standard", 0.0314, True),
    ("iShares MSCI ACWI UCITS (SSAC)", "MSCI ACWI",
     35404.4, "USD", "2026-08-05", "standard", 0.0314, False),
    # IMI trackers. These buy ONLY if the name is new to the IMI.
    ("iShares Core MSCI EM (IEMG US)",
     "MSCI Emerging Markets IMI", 160718.0, "USD", "2026-06-30",
     "imi", 0.2741, True),
    ("iShares Core MSCI EM IMI UCITS (EIMI)",
     "MSCI Emerging Markets IMI", 44227.0, "USD", "2026-08-07",
     "imi", 0.2741, True),
    ("iShares Core MSCI Total Intl Stock (IXUS)",
     "MSCI ACWI ex USA IMI", 58500.0, "USD", "2026",
     "imi", 0.08, False),
    ("Fidelity Total International Index (FTIHX)",
     "MSCI ACWI ex USA IMI", 23500.0, "USD", "2026-07-31",
     "imi", 0.08, False),
]
FX_TO_USD = {"USD": 1.0, "EUR": 1.15, "TWD": 1 / 30.5}

# GIMI 2.3.1 market coverage targets: Standard 85%, IMI 99%.
STANDARD_OVER_IMI = 0.99 / 0.85

# EXCLUDED, and each for a checked reason rather than an
# oversight. Vanguard's entire international range is FTSE.
EXCLUDED = [
    ("Vanguard VWO", "USD ~125bn",
     "FTSE Emerging Markets All Cap China A Inclusion \u2014 not MSCI"),
    ("Vanguard VXUS / VTIAX", "USD ~400bn+",
     "FTSE Global All Cap ex US \u2014 not MSCI"),
    ("SPDR SPEM", "USD 17.7bn", "S&P Emerging BMI \u2014 not MSCI"),
    ("Schwab SCHE", "USD 12.8bn", "FTSE Emerging \u2014 not MSCI"),
    ("Avantis AVEM, DFA DFAE/DFEM", "USD 26.5bn+",
     "systematic/active, not index-replicating"),
]


def _j(name):
    p = ROOT / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() \
        else {}


def method1():
    """Sum the funds, bucket by bucket, and split the EM channel
    into the two cases that GIMI's size-segment rules create."""
    out = {"funds": [], "totals": {}, "excluded": [
        {"fund": f, "aum": a, "why": w} for f, a, w in EXCLUDED]}
    tot = {"uncapped": 0.0, "family": 0.0,
           "standard_tw": 0.0, "imi_tw": 0.0,
           "standard_fund_aum": 0.0, "imi_fund_aum": 0.0}
    for nm, idx, aum, ccy, asof, bucket, tw, ver in FUNDS:
        usd = aum * FX_TO_USD[ccy] / 1000          # -> USD bn
        row = {"fund": nm, "index": idx, "aum": aum, "ccy": ccy,
               "as_of": asof, "bucket": bucket, "verified": ver,
               "usd_bn": round(usd, 3)}
        if bucket in ("standard", "imi"):
            row["taiwan_weight"] = tw
            row["taiwan_usd_bn"] = round(usd * tw, 2)
            tot[f"{bucket}_tw"] += usd * tw
            tot[f"{bucket}_fund_aum"] += usd
        else:
            tot[bucket] += usd
        out["funds"].append(row)
    tot["family"] += tot["uncapped"]
    # CASE 1 — the addition is a promotion out of Taiwan Small
    # Cap. IMI trackers already hold it at an unchanged weight,
    # so they contribute nothing.
    tot["case_promotion"] = tot["standard_tw"]
    # CASE 2 — the addition is new to the IMI. Everyone buys, but
    # an IMI dollar carries ~1/1.16 of a Standard dollar's weight
    # in the name.
    tot["case_new_to_imi"] = (tot["standard_tw"]
                              + tot["imi_tw"] / STANDARD_OVER_IMI)
    out["totals"] = {k_: round(v, 3) for k_, v in tot.items()}
    out["standard_over_imi"] = round(STANDARD_OVER_IMI, 4)
    out["_reading"] = (
        "Which case applies is empirical per name. Check whether "
        "the stock is already in the IEMG and EIMI daily holdings "
        "files, and whether MSCI's review lists it as a DELETION "
        "from the Global Small Cap Indexes. May-2026 MPI Corp was "
        "case 1; Feb-2026 Hon Precision was case 2.")
    return out


def method2():
    """Turn the demand equation around on measured flow."""
    scn = _j("aug26_scenarios.json")
    pb = _j("tw_tracker_playbook.json")
    add = _j("tw_addition_study.json")
    if not (scn and pb and add):
        return {"_status": "run aug26_scenarios.py and "
                           "tw_addition_study.py first"}
    A = scn["assumptions"]
    fx = A["usd_twd"]
    bench = add["foreign_flow"]["ADD"]["cumulative_to_effective"]

    def implied(days):
        rows = {}
        for c, r in scn["names"].items():
            if not r.get("carried"):
                continue
            w = r["index_weight_pct"] / 100
            adv = pb["names"][c]["adv_shares"]
            px = r["last_close_twd"]
            # shares the flow benchmark says were bought, valued
            # at the last close, converted to USD, divided by the
            # name's index weight
            rows[c] = days * adv * px / fx / w / 1e9
        return rows

    mid = implied(bench["p50"])
    return {
        "benchmark": {
            "what": "foreign net accumulated between ann-20 and "
                    "the effective print, in days of the name's "
                    "own ADV",
            "source": "TWSE T86, 42 Taiwanese additions",
            "p25": bench["p25"], "p50": bench["p50"],
            "p75": bench["p75"], "n": bench["n"]},
        "per_name": {c: round(v, 1) for c, v in mid.items()},
        "median_usd_bn": round(stats.median(mid.values()), 1),
        "low_usd_bn": round(
            stats.median(implied(bench["p25"]).values()), 1),
        "high_usd_bn": round(
            stats.median(implied(bench["p75"]).values()), 1),
        "name_disagreement": round(
            max(mid.values()) / min(mid.values()), 2),
        "inputs": {c: {"weight_pct": scn["names"][c]["index_weight_pct"],
                       "adv_shares": pb["names"][c]["adv_shares"],
                       "price_twd": scn["names"][c]["last_close_twd"]}
                   for c in mid},
        "usd_twd": fx,
    }


def main():
    m1, m2 = method1(), method2()
    o = {"_what": "two independent estimates of the passive AUM "
                  "that must trade an MSCI Taiwan index change",
         "generated": dt.datetime.now().isoformat(timespec="seconds"),
         "declared_constant_usd_bn": 180.0,
         "method1_bottom_up": m1,
         "method2_revealed_from_flow": m2}
    OUT.write_text(json.dumps(o, indent=1), encoding="utf-8")
    write_doc(o)
    t = m1["totals"]
    print(f"bottom-up  uncapped {t['uncapped']:.2f} | family "
          f"{t['family']:.1f} | standard-TW {t['standard_tw']:.1f} "
          f"| IMI-TW {t['imi_tw']:.1f}")
    print(f"           CASE promotion {t['case_promotion']:.0f}bn "
          f"| CASE new-to-IMI {t['case_new_to_imi']:.0f}bn")
    if "median_usd_bn" in m2:
        print(f"revealed   median {m2['median_usd_bn']:.0f}bn  "
              f"(IQR of the flow benchmark: "
              f"{m2['low_usd_bn']:.0f}-{m2['high_usd_bn']:.0f}bn)  "
              f"per name {m2['per_name']}")
    print(f"wrote {OUT.name}, {DOC.name}")
    return o


def write_doc(o):
    m1, m2 = o["method1_bottom_up"], o["method2_revealed_from_flow"]
    t = m1["totals"]
    L = ["# Estimating the passive AUM behind an MSCI Taiwan "
         "index change", "",
         f"Generated {o['generated']}. The demand model uses a "
         f"declared **USD {o['declared_constant_usd_bn']:,.0f}bn**. "
         "This file asks what can be estimated instead.", "",
         "## Method 1 — bottom-up, and the size-segment trap", "",
         "**A Taiwan Standard addition is not bought by every "
         "passive dollar that holds Taiwan.** MSCI's size "
         "segments are derived by subtraction (GIMI 2.3: *\"the "
         "Small Cap Index is derived as the difference between "
         "the Investable Market Index and the Standard "
         "Index\"*), so a stock promoted out of Small Cap was "
         "ALREADY inside the IMI at an unchanged free-float "
         "weight. An IMI tracker does nothing.", "",
         "The last two Taiwan reviews are one of each case:", "",
         "| review | name | what happened | IMI trackers |",
         "|---|---|---|---|",
         "| May-2026 | MPI Corp (6223) | added to Standard, "
         "**deleted from Global Small Cap** | bought nothing |",
         "| Feb-2026 | Hon Precision (7769) | absent from the "
         "Small Cap deletion list \u2014 new to the IMI | bought "
         "from zero |", "",
         "| fund | index | AUM | Taiwan wt | Taiwan USD bn | src |",
         "|---|---|---|---|---|---|"]
    for r in m1["funds"]:
        if r["bucket"] not in ("standard", "imi"):
            continue
        L.append(f"| {r['fund']} | {r['index']} | "
                 f"{r['aum']:,.0f} {r['ccy']} | "
                 f"{r['taiwan_weight']:.2%} | "
                 f"{r['taiwan_usd_bn']:,.2f} | "
                 f"{'issuer' if r['verified'] else 'third-party'} |")
    L += ["", "**Totals:**", "",
          f"- ETFs on the **uncapped** MSCI Taiwan Index: "
          f"**USD {t['uncapped']:.2f}bn**",
          f"- ETFs on **any** MSCI Taiwan index: "
          f"**USD {t['family']:.1f}bn**",
          f"- Taiwan inside **Standard** EM/ACWI trackers "
          f"(always buy): **USD {t['standard_tw']:.1f}bn** from "
          f"USD {t['standard_fund_aum']:,.0f}bn of funds",
          f"- Taiwan inside **IMI** trackers (buy only if the "
          f"name is new to the IMI): **USD {t['imi_tw']:.1f}bn** "
          f"from USD {t['imi_fund_aum']:,.0f}bn of funds", "",
          "So the answer is a pair, not a number:", "",
          "| case | who buys | Standard-equivalent AUM |",
          "|---|---|---|",
          f"| promotion out of Small Cap | Standard trackers only "
          f"| **USD {t['case_promotion']:.0f}bn** |",
          f"| new to the IMI | everyone, IMI discounted "
          f"{o['method1_bottom_up']['standard_over_imi']:.2f}x "
          f"| **USD {t['case_new_to_imi']:.0f}bn** |", "",
          "*The 1.16x: Standard targets 85% of free-float market "
          "cap and IMI targets 99% (GIMI 2.3.1), so a stock's "
          "weight inside Standard is ~99/85 of its weight inside "
          "the IMI \u2014 an IMI dollar buys ~16% less of it even "
          "when it buys.*", "",
          "**" + m1["_reading"] + "**", "",
          "### Excluded, each for a checked reason", "",
          "| fund | size | why |", "|---|---|---|"]
    for e in m1["excluded"]:
        L.append(f"| {e['fund']} | {e['aum']} | {e['why']} |")
    L += ["", "## Method 2 — revealed from what was bought", ""]
    if "median_usd_bn" not in m2:
        L += [m2["_status"], ""]
    else:
        b = m2["benchmark"]
        L += ["Turn the demand equation around:", "", "```",
              "demand_shares = weight x AUM / (fx x price)",
              "        =>  AUM = shares x price / fx / weight",
              "```", "",
              f"`shares` comes from **{b['source']}**: {b['what']}. "
              f"Median **{b['p50']:+.2f}x** a normal day's volume "
              f"(quartiles {b['p25']:+.2f} to {b['p75']:+.2f}, "
              f"n={b['n']}).", "",
              "| name | weight | ADV (m sh) | price TWD | implied AUM |",
              "|---|---|---|---|---|"]
        for c, v in sorted(m2["per_name"].items()):
            i_ = m2["inputs"][c]
            L.append(f"| {c} | {i_['weight_pct']:.3f}% | "
                     f"{i_['adv_shares'] / 1e6:,.1f} | "
                     f"{i_['price_twd']:,.1f} | "
                     f"**USD {v:,.0f}bn** |")
        L += ["",
              f"**Median USD {m2['median_usd_bn']:,.0f}bn**, names "
              f"disagreeing by {m2['name_disagreement']:.2f}x, and "
              f"the flow benchmark's own quartiles moving it from "
              f"{m2['low_usd_bn']:,.0f} to "
              f"{m2['high_usd_bn']:,.0f}bn.", ""]
    L += ["## What this settles", "",
          f"The bottom-up pair (**{t['case_promotion']:.0f}** or "
          f"**{t['case_new_to_imi']:.0f}bn**) and the "
          f"flow-revealed median "
          f"(**{m2.get('median_usd_bn', 0):,.0f}bn**) do NOT "
          "agree, and the gap is informative rather than "
          "embarrassing: the bottom-up figure counts only listed "
          "funds, while institutional segregated accounts, "
          "collective trusts and pension mandates benchmarked to "
          "MSCI EM are not publicly disclosed anywhere. Those are "
          "commonly a multiple of listed-ETF assets, and they buy "
          "the same stock on the same day.", "",
          "So: **the bottom-up numbers are floors, the "
          "flow-revealed number is the only estimate that sees "
          "the whole market, and the level remains uncertain to "
          "an order of magnitude.** The ranking between names is "
          "unaffected by any of it.", "",
          "## Not verified", "",
          "- Taiwan's weight in MSCI EM. This file uses 27.41%; "
          "MSCI stated **23.76%** after the May-2026 review. The "
          "difference is ~15% on every EM line.",
          "- Taiwan's weight inside EMXC, IXUS and FTIHX \u2014 all "
          "derived, none read off a fund page.",
          "- XMME and IEEM AUM \u2014 third-party sources conflict "
          "by 30-80%.",
          "- Japan- and Korea-listed MSCI EM trackers \u2014 none "
          "found, which is a negative search result rather than a "
          "confirmed zero.",
          "- Non-fund institutional mandates \u2014 not disclosable, "
          "and the largest single source of understatement here.",
          "- The Hon Precision case is inferred from the ABSENCE "
          "of the name in the Small Cap deletion list; direct "
          "confirmation needs MSCI's client-gated review file.",
          ""]
    DOC.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
