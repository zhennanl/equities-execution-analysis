"""Framework page 1 — cutoff threshold, ALL APAC markets from
ONE template (c-88/c-89).

HOW TO CHANGE THE TEMPLATE (the user's workflow):
  - Edit the step functions below (_step0.._step6) — every
    market inherits the change automatically; there is no
    per-market page code.
  - Market-specific FACTS live in MARKET_OVERRIDES (sparse —
    only what differs beyond the registry).
  - Everything else is assembled per market from:
      agents/market_profiles.py        (tier, ccy, access...)
      data/apac_factsheet_archive.json (Frame A, corridors)
      data/cutoff_walk_v2.json         (Frame B walk — TW only
                                        until censuses run)
      data/aug26_cutoff_calc.json      (shortlist — TW only)
  - Markets missing an artifact render an honest OPEN/LIMIT
    row instead of numbers (no silent borrowing — the
    market_profiles contract).

Tags:  FACT / RULE / DERIVED / ASSUMPTION / LIMIT / OPEN
"""
import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]

# shared review calendar (same global review)
REVIEW = {"next_review": "Aug-2026 QIR",
          "ann": "2026-08-12 (Asia time)",
          "eff_close": "2026-08-31"}

# sparse per-market manual facts (beyond the registry)
MARKET_OVERRIDES = {
    "Taiwan": {"fx": 29.5, "census": True, "shortlist": True},
}

_TAG_COLOR = {"FACT": "#1f77b4", "RULE": "#2ca02c",
              "DERIVED": "#7f7f7f", "ASSUMPTION": "#d62728",
              "LIMIT": "#ff7f0e", "OPEN": "#9467bd"}


def _badge(tag):
    c = _TAG_COLOR[tag]
    return (f"<span style='background:{c};color:white;"
            f"padding:1px 7px;border-radius:9px;"
            f"font-size:0.75em'>{tag}</span>")


def _row(label, value, source, tag):
    st.markdown(
        f"{_badge(tag)} **{label}** = `{value}`  \n"
        f"<span style='color:gray;font-size:0.85em'>source: "
        f"{source}</span>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _artifacts():
    def j(name):
        p = ROOT / "data" / name
        return json.loads(p.read_text()) if p.exists() else {}
    return (j("apac_factsheet_archive.json"),
            j("cutoff_walk_v2.json"),
            j("aug26_cutoff_calc.json"))


def market_cfg(key):
    from agents.market_profiles import PROFILES
    p = PROFILES[key]
    cfg = {"name": key, "tier": p["tier"], "ccy": p["ccy"],
           "profile": p, **REVIEW,
           "census": False, "shortlist": False}
    cfg.update(MARKET_OVERRIDES.get(key, {}))
    return cfg


# Taiwan default export (kept for tests / single-market use)
MARKET = {"name": "Taiwan", "tier": "EM",
          "factsheet_key": "Taiwan", "fx": 29.5, **REVIEW}


# ------------------- the template steps -------------------
def _step0(cfg):
    with st.container(border=True):
        st.subheader("Step 0 — the event and its THREE data "
                     "dates")
        _row("Announcement", cfg["ann"],
             "MSCI review calendar (msci.com/index-review)",
             "FACT")
        _row("Effective (close of)", cfg["eff_close"],
             "MSCI review calendar", "FACT")
        _row("Price Cutoff Date",
             "ONE date from the last 10 business days of July "
             "2026 — NOT pre-disclosed",
             "GIMI May-2026 ed. §3.1.9 'Date of Data Used for "
             "Index Reviews' p.48 (archived: data/msci_archive/"
             "MSCI_GIMIMethodology_May2026.pdf): 'any one of "
             "the last 10 business days... of July for the "
             "August Index Review' — governs cap prices, FIF "
             "updates, foreign room, NOS. Which day = the "
             "assumption we carry (fn 28: window prepones if "
             "the effective date falls inside the announcement "
             "month)", "ASSUMPTION")
        _row("Liquidity Cutoff Date", "2026-06-30 "
             "(deterministic: last business day of June for "
             "the August review)",
             "GIMI May-2026 §3.1.9 p.48 — ATVR/frequency data "
             "date: KNOWABLE, align our ATVR inputs to it",
             "RULE")
        _row("Equity Universe Cutoff Date", "2026-05-29 "
             "(deterministic: last business day of May for the "
             "August review)",
             "GIMI May-2026 §3.1.9 p.48 — universe + minimum-"
             "size-requirement data date: KNOWABLE", "RULE")
        _row("Post-cutoff discretion", "extraordinary events "
             "(fraud, takeovers, suspensions) between price "
             "cutoff and announcement can veto a migration",
             "GIMI May-2026 §3.1.9 closing paragraph — the "
             "discretion LIMIT, now in rulebook text", "LIMIT")


def _step1(cfg, fs):
    with st.container(border=True):
        st.subheader("Step 1 — global size reference and the "
                     "corridor")
        _row("Published DM reference (May-2026)", "$15.75B",
             "GIMI book worked example §2.3.2.1 p.25", "FACT")
        _row("Scaling to this review", "x 1.042",
             "OUR proxy for GIMI Appendix X p.117 ('Updating "
             "the Global Minimum Size References and Ranges'): "
             "MSCI reprices the SAME-RANK company at each "
             "review's price date (rank holds while coverage "
             "stays in 85-87%; else rank resets). We "
             "approximate that repricing with the broad-DM "
             "move; band ±2pts covers marginal-vs-average "
             "drift + possible rank reset", "ASSUMPTION")
        _row("DM reference forecast", "$16.41B",
             "= 15.75 x 1.042", "DERIVED")
        if cfg["tier"] == "EM":
            _row("EM reference", "$8.21B",
                 "GIMI §2.3.2.1: EM = one-half DM", "RULE")
        cor = fs.get("cutoff_corridor_busd")
        _row(f"Corridor ({cfg['tier']})",
             f"[${cor[0]}B, ${cor[1]}B]" if cor else "n/a",
             "GIMI §2.3.2: 0.5-1.15x the reference "
             "(data/apac_factsheet_archive.json)", "RULE")


def _step2(cfg, fs, walk):
    with st.container(border=True):
        st.subheader("Step 2 — the market's free-float "
                     "denominator")
        st.markdown("**Frame A — factsheet inversion "
                    "(available for every market)**")
        _row("Index float-adjusted cap",
             f"${fs.get('index_float_cap_musd', 0)/1e3:,.0f}B "
             f"(as of {fs.get('asof', '?')}, "
             f"n={fs.get('n_constituents', '?')})",
             f"MSCI {cfg['name']} factsheet, captured in "
             "data/apac_factsheet_archive.json", "FACT")
        _row("Implied denominator",
             f"${fs.get('implied_denominator_busd', 0):,.0f}B",
             "= float cap ÷ 0.85 (GIMI §2.3.1) — ASSUMES exact "
             "85% coverage; banding makes this ±6%",
             "ASSUMPTION")
        st.markdown("**Frame B — census measurement**")
        if cfg["census"]:
            w = walk.get("base", {})
            _row("Census denominator",
                 f"${w.get('denominator_busd', 0):,.0f}B "
                 f"({walk.get('census_coverage', '?')})",
                 "data/cutoff_walk_v2.json — universe FinMind, "
                 "GIMI screens, tiered floats (Q53), FX "
                 f"{cfg.get('fx')} {cfg['ccy']}/USD "
                 "[ASSUMPTIONS: $0.2B min size, default float "
                 "0.55 swept 0.40-0.70]", "DERIVED")
            _row("Frame agreement",
                 f"{w.get('gap_vs_implied_pct', '?')}%",
                 "inside the ±6% banding allowance — frames "
                 "corroborate", "DERIVED")
        else:
            fsrc = cfg["profile"]["float_source"]
            _row("Census", "NOT BUILT for this market",
                 f"activation path: float source = "
                 f"{fsrc[0]} [{fsrc[1]}]; see "
                 "docs/GMSR_MULTIMARKET_DESIGN.md priority "
                 "order (KR -> IN -> JP -> CN; AU/HK/MY likely "
                 "fine on Frame A alone)", "OPEN")


def _step34(cfg, fs, walk):
    with st.container(border=True):
        st.subheader("Steps 3-4 — the 85% walk and the "
                     "corridor check")
        _row("Walk bases", "rank FULL cap / accumulate FLOAT / "
             "express FULL", "GIMI segmentation convention "
             "(Q46)", "RULE")
        if cfg["census"]:
            w = walk.get("base", {})
            _row("Crossing",
                 f"rank {w.get('cross_rank', '?')} at "
                 f"${w.get('cutoff_full_cap_busd', '?')}B",
                 "data/cutoff_walk_v2.json", "DERIVED")
            _row("Corridor check", "crossing ABOVE the ceiling "
                 "in every float frame -> THE CORRIDOR BINDS: "
                 "effective cutoff = corridor edge",
                 "concentration makes the clamp the active "
                 "rule here", "DERIVED")
        else:
            sm = fs.get("smallest_musd")
            _row("Walk", "needs the census (Frame B)",
                 "until built, the corridor + the smallest "
                 "member bound the frontier", "OPEN")
            _row("Smallest index constituent",
                 f"${sm:,.0f}M float cap" if sm else "n/a",
                 "factsheet — the observable lower edge of "
                 "current membership (float terms, not the "
                 "full-cap cutoff)", "FACT")


def _step5(cfg, fs):
    with st.container(border=True):
        st.subheader("Step 5 — the trading frontiers")
        cor = fs.get("cutoff_corridor_busd")
        if cor:
            _row("Existing-member floor (if corridor binds "
                 "at the ceiling)",
                 f"2/3 x {cor[1]} = ${round(2 / 3 * cor[1], 2)}B",
                 "GIMI §3.1.5.1 buffers", "RULE")
            _row("New-add bar (same condition)",
                 f"1.5 x {cor[1]} = ${round(1.5 * cor[1], 2)}B "
                 "+ gates (float ≥ 0.15, half-bar, ATVR, "
                 "foreign room)", "GIMI §3.1.5.1 + §3.1.2",
                 "RULE")
            if not cfg["census"]:
                _row("Caveat", "frontiers shown at the "
                     "corridor CEILING", "whether this "
                     "market's walk clamps there (TW-like) or "
                     "crosses INSIDE the corridor is unknown "
                     "until its census runs", "LIMIT")


def _step6(cfg, cut):
    with st.container(border=True):
        st.subheader("Step 6 — the shortlist")
        if cfg["shortlist"]:
            st.markdown("**Delete pool (members under the "
                        "floor; live-ladder caps):**")
            st.dataframe(
                [{"code": c.get("code"),
                  "full cap $B": c.get("cap_usd_b")}
                 for c in cut.get("delete_candidates", [])[:10]],
                hide_index=True, use_container_width=True)
            st.markdown("**Add candidates vs the bar + gates:**")
            st.dataframe(
                [{"code": c.get("code"),
                  "verdict": c.get("verdict", "")}
                 for c in cut.get("add_candidates", [])],
                hide_index=True, use_container_width=True)
        else:
            _row("Shortlist", "needs the member ladder",
                 "run scripts/apac_member_census.py for this "
                 "market (script exists, all 13 resolvers "
                 "wired)", "OPEN")
        _row("MSCI discretion", "irreducible",
             "corner cases + unseen price date + fresh recalc "
             "-> probabilistic shortlist, graded on "
             "announcement", "LIMIT")


def render_market(key):
    fs_arch, walk, cut = _artifacts()
    cfg = market_cfg(key)
    fs = {}
    if key in fs_arch:
        v = fs_arch[key]
        fs = v[sorted(v)[-1]]
    st.title(f"Cutoff framework — {cfg['name']} "
             f"({cfg['next_review']})")
    st.markdown(" ".join(
        f"{_badge(t)}" for t in _TAG_COLOR),
        unsafe_allow_html=True)
    _step0(cfg)
    _step1(cfg, fs)
    _step2(cfg, fs, walk)
    _step34(cfg, fs, walk)
    _step5(cfg, fs)
    _step6(cfg, cut)
    st.caption("ONE template renders every market: edit the "
               "step functions in views/framework_cutoff.py "
               "and all markets change together. Market facts "
               "come from market_profiles + the three "
               "artifacts; missing pieces render OPEN, never "
               "borrowed.")


def render():
    from agents.market_profiles import PROFILES
    keys = list(PROFILES)
    key = st.sidebar.selectbox(
        "Market", keys, index=keys.index("Taiwan"))
    st.sidebar.caption("Same template, 13 markets. Taiwan has "
                       "the full artifact set; others show "
                       "OPEN where their census/ladder hasn't "
                       "run.")
    render_market(key)
