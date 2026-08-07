"""Market profiles — the single registry that standardizes
Steps 1-2 across APAC markets WITHOUT overgeneralizing (c-74).

Design rule: everything in UNIVERSAL is index-methodology
physics (GIMI applies identically to every market it covers;
lambda x float is AUM arithmetic). Everything that varies lives
in PROFILES with an explicit status tag:

  fitted / validated  measured on this market's own data
  UNCALIBRATED        the method transfers, the parameter does
                      not — refit before use, never borrow TW's
  NOT_INTEGRATED      data exists in the market, not wired in
  NOT_OBSERVABLE      the channel has no public data here
  DOES_NOT_TRANSFER   the market's structure differs in KIND —
                      the tool must not run (e.g., India has no
                      closing auction; "the print" is a VWAP)
  TO_VERIFY           institutional fact recorded from desk
                      knowledge, must be confirmed against the
                      exchange's rulebook before that market
                      goes live

The honesty contract: a market's Step-1/Step-2 run reports each
stage's tag; BLOCKED/UNCALIBRATED stages produce NO numbers
(never silently fall back to another market's parameter).

Usage:
  from agents.market_profiles import profile, step1_plan, \
      step2_plan, report
  py -c "from agents.market_profiles import report; report()"
"""

# ---------------------------------------------------------------
# THE SHARED CORE — identical for every GIMI market, by
# construction of the methodology (citations in
# INDEX_REVIEW_METHODOLOGY.md / QA doc Q9-Q22)
# ---------------------------------------------------------------
UNIVERSAL = {
    "coverage_target": 0.85,          # GIMI 2.3.1 (Standard)
    "corridor_of_ref": (0.5, 1.15),   # EM half / DM full band
    "buffers": (2 / 3, 1.5),          # GIMI 3.1.5.1
    "float_min": 0.15,                # GIMI 3.1.2.3
    "atvr_min_em": 0.15,              # GIMI 3.1.2.4
    "foreign_room_min": 0.15,         # GIMI 3.1.2.6 (where a
                                      # limit regime exists)
    "flow_model": "forced = lambda x float_shares "
                  "(Pavlova-Sikorskaya benchmarking intensity; "
                  "price cancels)",
    "frame_robust_policy": "verdicts ship only if they hold "
                           "under every denominator frame",
}

_STD_STAGES = [
    ("factsheet_inversion", "index float-cap / coverage -> "
     "implied denominator"),
    ("cutoff_corridor", "DM/EM tier x global reference"),
    ("membership_anchor", "ETF anchor + composite reconcile"),
    ("member_caps_census", "per-name caps/floats via resolver"),
    ("full_universe_census", "MIEU screens -> denominator"),
    ("float_estimation", "insider/promoter-based FIF estimate"),
    ("foreign_room_gate", "room >= 15% where regime exists"),
    ("verdict_frame_check", "frame-robustness policy"),
]

# ---------------------------------------------------------------
# PER-MARKET PROFILES — the differences, tagged
# ---------------------------------------------------------------
PROFILES = {
    "Taiwan": {
        "tier": "EM", "ccy": "TWD", "anchor": "EWT",
        "access": {"regime": "FOL per-industry caps + foreign "
                   "investor ID", "gate_active": True},
        "float_source": ("named_insiders_v2", "validated 0.022 "
                         "vs MSCI implied FIFs"),
        "universe_census": ("mieu_census.py", "running"),
        "borrow": ("official daily TWT93U 2015+", "integrated"),
        "short_sale": {"status": "allowed", "era_flags": []},
        "price_limit": "±10%",
        "settlement": "T+2",
        "close_mech": {"type": "call_auction",
                       "window": "13:25-13:30",
                       "disclosure": "5s indicative since "
                                     "2015-06-29 (not archived)",
                       "note": "cancel rules changed mid-2015 — "
                               "era split in auction5s"},
        "lambda": ("fitted", 0.093),
        "derivatives_oi": ("TAIFEX SSF", "capture-forward"),
    },
    "Japan": {
        "tier": "DM", "ccy": "JPY", "anchor": "EWJ",
        "access": {"regime": None, "gate_active": False},
        "float_source": ("yahoo_insiders_est", "ungraded"),
        "universe_census": (None, "OPEN"),
        "borrow": ("JSF / TSE lending data exist",
                   "NOT_INTEGRATED"),
        "short_sale": {"status": "allowed (uptick trigger)",
                       "era_flags": []},
        "price_limit": "value-based daily bands",
        "settlement": "T+2",
        "close_mech": {"type": "call_auction",
                       "window": "itayose at 15:30 close",
                       "note": "close moved 15:00->15:30 on "
                               "2024-11-05 — era flag REQUIRED "
                               "for any close-volume history"},
        "lambda": ("UNCALIBRATED", None),
        "derivatives_oi": ("OSE SSF exist", "NOT_INTEGRATED"),
    },
    "Australia": {
        "tier": "DM", "ccy": "AUD", "anchor": "EWA",
        "access": {"regime": None, "gate_active": False},
        "float_source": ("yahoo_insiders_est", "ungraded"),
        "universe_census": (None, "OPEN"),
        "borrow": ("ASIC public short positions (lagged)",
                   "NOT_INTEGRATED"),
        "short_sale": {"status": "allowed", "era_flags": []},
        "price_limit": "none",
        "settlement": "T+2",
        "close_mech": {"type": "call_auction",
                       "window": "CSPA ~16:00-16:10 + random "
                                 "end (TO_VERIFY exact band)"},
        "lambda": ("UNCALIBRATED", None),
        "derivatives_oi": (None, "NOT_INTEGRATED"),
    },
    "HongKong": {
        "tier": "DM", "ccy": "HKD", "anchor": "EWH",
        "access": {"regime": None, "gate_active": False},
        "float_source": ("yahoo_insiders_est", "ungraded"),
        "universe_census": (None, "OPEN"),
        "borrow": ("SFC weekly aggregated short reports",
                   "NOT_INTEGRATED"),
        "short_sale": {"status": "allowed (designated list)",
                       "era_flags": []},
        "price_limit": "none (per-stock VCM circuit)",
        "settlement": "T+2",
        "close_mech": {"type": "call_auction",
                       "window": "CAS 16:00-16:10, two-stage "
                                 "±5% band, random 16:08-16:10"},
        "lambda": ("UNCALIBRATED", None),
        "derivatives_oi": ("HKEX SSF exist", "NOT_INTEGRATED"),
    },
    "Korea": {
        "tier": "EM", "ccy": "KRW", "anchor": "EWY",
        "access": {"regime": "sector foreign-ownership ceilings "
                   "(telecom/utility/air)", "gate_active": True},
        "float_source": ("yahoo_insiders_est", "ungraded"),
        "universe_census": (None, "OPEN"),
        "borrow": ("KRX short-sale disclosure",
                   "NOT_INTEGRATED"),
        "short_sale": {"status": "allowed (resumed 2025)",
                       "era_flags": ["BAN 2020-03->2021-05 "
                                     "(partial resume)",
                                     "BAN 2023-11->2025-03"]},
        "price_limit": "±30%",
        "settlement": "T+2",
        "close_mech": {"type": "call_auction",
                       "window": "15:20-15:30"},
        "lambda": ("UNCALIBRATED", None),
        "derivatives_oi": ("KRX single-stock futures deep",
                           "NOT_INTEGRATED"),
    },
    "China": {
        "tier": "EM", "ccy": "CNY", "anchor": "MCHI/share-class",
        "access": {"regime": "Stock Connect eligibility + "
                   "daily quota; QFI", "gate_active": True},
        "float_source": ("state/strategic holdings dominate",
                         "LOW_CONFIDENCE"),
        "universe_census": (None, "OPEN"),
        "borrow": ("domestic margin/SBL, restricted post-2024",
                   "NOT_OBSERVABLE for foreign flow"),
        "short_sale": {"status": "heavily restricted",
                       "era_flags": ["inclusion-tranche events "
                                     "2018-19 FLAGGED (v3): ann "
                                     "was not the info event"]},
        "price_limit": "±10% (±20% STAR/ChiNext)",
        "settlement": "T+1 regime (Connect specifics apply, "
                      "TO_VERIFY detail)",
        "close_mech": {"type": "call_auction",
                       "window": "14:57-15:00 (SSE since "
                                 "2018-08; SZSE earlier) — era "
                                 "flag for pre-2018 SSE"},
        "lambda": ("UNCALIBRATED", None),
        "derivatives_oi": (None, "NOT_OBSERVABLE"),
    },
    "India": {
        "tier": "EM", "ccy": "INR", "anchor": "INDA",
        "access": {"regime": "FPI registration + sectoral "
                   "limits; foreign room ACTIVELY binds",
                   "gate_active": True},
        "float_source": ("exchange promoter-shareholding "
                         "filings (quarterly, NAMED — v2-grade "
                         "source)", "NOT_INTEGRATED"),
        "universe_census": (None, "OPEN"),
        "borrow": ("SLB segment thin", "NOT_INTEGRATED"),
        "short_sale": {"status": "allowed (institutional "
                       "constraints)", "era_flags": []},
        "price_limit": "circuit bands (name-dependent)",
        "settlement": "T+1",
        "close_mech": {"type": "vwap_close",
                       "window": "last-30-min VWAP",
                       "note": "NO closing auction: the 'print' "
                               "is a VWAP - every auction "
                               "analytic DOES_NOT_TRANSFER; "
                               "execution = participate the "
                               "window, not cross at a point"},
        "lambda": ("UNCALIBRATED", None),
        "derivatives_oi": ("NSE single-stock futures DEEP "
                           "(largest SSF market)",
                           "NOT_INTEGRATED"),
    },
    "Malaysia": {
        "tier": "EM", "ccy": "MYR", "anchor": "EWM",
        "access": {"regime": None, "gate_active": False},
        "float_source": ("yahoo_insiders_est", "ungraded"),
        "universe_census": (None, "OPEN"),
        "borrow": ("Bursa centralised SBL, thin",
                   "NOT_INTEGRATED"),
        "short_sale": {"status": "regulated (RSS list)",
                       "era_flags": ["RSS suspended "
                                     "2020-03->2021-01"]},
        "price_limit": "±30% static",
        "settlement": "T+2",
        "close_mech": {"type": "call_auction",
                       "window": "pre-close fixing ~16:45-17:00 "
                                 "(TO_VERIFY phase detail)"},
        "lambda": ("UNCALIBRATED", None),
        "derivatives_oi": (None, "NOT_INTEGRATED"),
    },
    "Indonesia": {
        "tier": "EM", "ccy": "IDR", "anchor": "EIDO(IMI "
        "variant — composite is the Standard source)",
        "access": {"regime": None, "gate_active": False},
        "float_source": ("yahoo_insiders_est", "ungraded"),
        "universe_census": (None, "OPEN"),
        "borrow": (None, "NOT_OBSERVABLE"),
        "short_sale": {"status": "restricted list",
                       "era_flags": ["asymmetric auto-rejection "
                                     "bands changed post-2020 — "
                                     "era flag"]},
        "price_limit": "auto-rejection bands (asymmetric, "
                       "era-dependent)",
        "settlement": "T+2",
        "close_mech": {"type": "call_auction",
                       "window": "pre-closing 15:50-16:00 + "
                                 "random close (TO_VERIFY)"},
        "lambda": ("UNCALIBRATED", None),
        "derivatives_oi": (None, "NOT_OBSERVABLE"),
    },
    "Philippines": {
        "tier": "EM", "ccy": "PHP", "anchor": "EPHE(IMI "
        "variant — composite is the Standard source)",
        "access": {"regime": "foreign ownership caps in "
                   "nationalized sectors", "gate_active": True},
        "float_source": ("yahoo_insiders_est", "ungraded"),
        "universe_census": (None, "OPEN"),
        "borrow": (None, "NOT_OBSERVABLE"),
        "short_sale": {"status": "SBL framework nascent",
                       "era_flags": []},
        "price_limit": "static ±(TO_VERIFY exact bands)",
        "settlement": "T+2",
        "close_mech": {"type": "call_auction",
                       "window": "pre-close ~15:15-15:20 + "
                                 "run-off (TO_VERIFY)"},
        "lambda": ("UNCALIBRATED", None),
        "derivatives_oi": (None, "NOT_OBSERVABLE"),
    },
    # ---- c-86: full-region completion (zero-change-in-May
    # markets; small but reviewable) ----
    "NewZealand": {
        "tier": "DM", "ccy": "NZD", "anchor": "ENZL",
        "access": {"regime": None, "gate_active": False},
        "float_source": ("yahoo_insiders_est", "ungraded"),
        "universe_census": (None, "OPEN"),
        "borrow": (None, "NOT_INTEGRATED"),
        "short_sale": {"status": "allowed", "era_flags": []},
        "price_limit": "none",
        "settlement": "T+2",
        "close_mech": {"type": "call_auction",
                       "window": "~16:45 close auction "
                                 "(TO_VERIFY)"},
        "lambda": ("UNCALIBRATED", None),
        "derivatives_oi": (None, "NOT_OBSERVABLE"),
    },
    "Singapore": {
        "tier": "DM", "ccy": "SGD", "anchor": "EWS",
        "access": {"regime": None, "gate_active": False},
        "float_source": ("yahoo_insiders_est", "ungraded"),
        "universe_census": (None, "OPEN"),
        "borrow": ("SGX SBL pool exists", "NOT_INTEGRATED"),
        "short_sale": {"status": "allowed (marking regime)",
                       "era_flags": []},
        "price_limit": "none (circuit breakers)",
        "settlement": "T+2",
        "close_mech": {"type": "call_auction",
                       "window": "17:00-17:06 w/ random end "
                                 "(TO_VERIFY exact band)"},
        "lambda": ("UNCALIBRATED", None),
        "derivatives_oi": ("SGX SSF exist", "NOT_INTEGRATED"),
    },
    "Thailand": {
        "tier": "EM", "ccy": "THB", "anchor": "THD",
        "access": {"regime": "foreign limits held via the NVDR "
                   "structure — GENUINE DIFFERENCE: foreigners "
                   "typically hold NVDRs (no voting), so float/"
                   "room semantics differ in kind",
                   "gate_active": True},
        "float_source": ("yahoo_insiders_est", "ungraded"),
        "universe_census": (None, "OPEN"),
        "borrow": ("SET publishes NVDR + short data",
                   "NOT_INTEGRATED"),
        "short_sale": {"status": "allowed (uptick)",
                       "era_flags": ["uptick tightened 2024 — "
                                     "era flag TO_VERIFY"]},
        "price_limit": "±30%",
        "settlement": "T+2",
        "close_mech": {"type": "call_auction",
                       "window": "random close 16:35-16:40 "
                                 "(TO_VERIFY)"},
        "lambda": ("UNCALIBRATED", None),
        "derivatives_oi": ("TFEX single-stock futures",
                           "NOT_INTEGRATED"),
    },
}


def profile(mkt):
    return PROFILES[mkt]


# ---------------------------------------------------------------
# REVIEW CALENDAR (c-92) — GIMI May-2026 §3.1.9 p.48: the three
# data dates are defined PER REVIEW, GLOBALLY — one calendar for
# every market in the index family. Universe: last b-day of
# Nov/Feb/May/Aug; Liquidity: last b-day of Dec/Mar/Jun/Sep;
# Price: any ONE of the last 10 b-days of Jan/Apr/Jul/Oct.
# Business days approximated as weekdays here; fn 29's >80%-of-
# ACWI-open definition and local-listing holiday handling are a
# registered refinement (TO_VERIFY per date), not silently
# assumed away.
# ---------------------------------------------------------------
_REVIEW_MONTHS = {2: (11, 12, 1), 5: (2, 3, 4),
                  8: (5, 6, 7), 11: (8, 9, 10)}


def review_dates(year, month):
    """The three GIMI data dates for a review (year, month in
    {2,5,8,11}). Returns dict with universe_cutoff,
    liquidity_cutoff, price_window (list of ~10 weekday dates,
    any ONE of which is the undisclosed Price Cutoff Date)."""
    import datetime as dt

    def last_weekday(y, m):
        d = (dt.date(y + (m == 12), m % 12 + 1, 1)
             - dt.timedelta(days=1))
        while d.weekday() > 4:
            d -= dt.timedelta(days=1)
        return d

    um, lm, pm = _REVIEW_MONTHS[month]
    uy = year - (um > month)
    ly = year - (lm > month)
    py = year - (pm > month)
    end = last_weekday(py, pm)
    window, d = [], end
    while len(window) < 10:
        if d.weekday() < 5:
            window.append(d)
        d -= dt.timedelta(days=1)
    return {"universe_cutoff": last_weekday(uy, um).isoformat(),
            "liquidity_cutoff": last_weekday(ly, lm).isoformat(),
            "price_window": [x.isoformat()
                             for x in sorted(window)],
            "note": "weekday approximation; fn29 ACWI-open "
                    "definition = registered refinement"}


def step1_plan(mkt):
    """Ordered Step-1 stages with per-market status. STD stages
    run the shared code path; hooks activate off the profile;
    OPEN stages produce no numbers."""
    p = PROFILES[mkt]
    plan = []
    for stage, desc in _STD_STAGES:
        if stage == "full_universe_census":
            status = ("STD" if p["universe_census"][0]
                      else "OPEN (denominator = factsheet "
                           "inversion only)")
        elif stage == "float_estimation":
            status = f"HOOK: {p['float_source'][0]} " \
                     f"[{p['float_source'][1]}]"
        elif stage == "foreign_room_gate":
            status = ("HOOK: " + p["access"]["regime"]
                      if p["access"]["gate_active"]
                      else "SKIP (no limit regime — gate "
                           "vacuously passes)")
        else:
            status = "STD"
        plan.append((stage, status, desc))
    return plan


def step2_plan(mkt):
    """Step-2 channels with observability + calibration tags."""
    p = PROFILES[mkt]
    lam_tag, lam = p["lambda"]
    ch = [("forced_flow", f"lambda {lam_tag}"
           + (f" ({lam})" if lam else "")
           + " — physics universal, parameter per-market")]
    ch.append(("ch1_borrow", p["borrow"][1] + " — "
               + str(p["borrow"][0])))
    ch.append(("ch2_inventory", "STD residual method (needs "
               "window volume + completion data)"))
    ch.append(("ch3_daytrade", "integrated (TWTB4U)"
               if mkt == "Taiwan" else "NOT_INTEGRATED"))
    ch.append(("ch3_5_derivatives", f"{p['derivatives_oi'][1]}"
               f" — {p['derivatives_oi'][0]}"))
    cm = p["close_mech"]
    ch.append(("auction_analytics",
               "DOES_NOT_TRANSFER — " + cm.get("note", "")
               if cm["type"] != "call_auction"
               else f"call auction {cm['window']}"
               + ("; " + cm["note"] if cm.get("note") else "")))
    if p["short_sale"]["era_flags"]:
        ch.append(("era_flags", "; ".join(
            p["short_sale"]["era_flags"])))
    return ch


def report():
    for mkt in PROFILES:
        p = PROFILES[mkt]
        print(f"\n=== {mkt} ({p['tier']}) ===")
        for stage, status, _ in step1_plan(mkt):
            print(f"  S1 {stage:22s} {status}")
        for chan, status in step2_plan(mkt):
            print(f"  S2 {chan:22s} {status}")


if __name__ == "__main__":
    report()
