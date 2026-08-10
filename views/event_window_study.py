"""Page 5 — the announcement -> effective window study (c-127).

What a PT desk actually stares at in the 9-14 sessions between
the MSCI announcement and the effective close: how adds and
deletes DRIFT once the news is out, and whether the trade is
already CROWDED.

Timing convention (see scripts/tw_event_window.py): Geneva
announces ~23:00 CET = ~05:00 Taipei next morning, so day 0 =
the announcement date's Taipei close (pre-news, cum return 0)
and day 1 is the first session that can react.

Panels:
  1. Cumulative returns from day 0, one line per (review,
     stock), filterable: action, era, single review. Effective
     day marked.
  2. Crowding overlays (2015+ from the decade caches, no new
     harvest): cumulative FOREIGN NET BUY (t86) for adds,
     BORROW BALANCE indexed to day 0 (sbl) for deletes,
     volume vs its own pre-announcement average.
  3. Pre-positioning lens: extend the window 25d BEFORE the
     announcement — drift and borrow build before day 0 is
     the hedge-fund-front-running fingerprint.
"""
import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]


@st.cache_data(show_spinner=False)
def _windows():
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "scripts"))
    from study_window import filter_windows   # c-188: 2015 floor
    p = ROOT / "data" / "tw_event_windows.json"
    if not p.exists():
        return {}
    # c-196 BUG I SHIPPED. c-188 imported filter_windows and
    # never called it. The file holds 179 windows back to 2010;
    # the page was rendering all of them, including the 44 whose
    # announcement date was ESTIMATED as effective-10-business-
    # days and measured 3 sessions late — while the caption
    # underneath told the reader the sample was 2015+. The
    # import sat there as decoration. Bill asked for the 2015
    # floor twice; it was applied to the harvester and to the
    # APAC path, but not to the page that says so loudest.
    return filter_windows(json.loads(p.read_text(encoding="utf-8"))["windows"])


@st.cache_data(show_spinner=False)
def _flow(name):
    p = ROOT / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


ADIR = ROOT / "data" / "apac_event_windows"

# A market needs this many priced windows before its medians are
# shown as a playbook. Below it the sample is displayed but not
# aggregated — three additions cannot describe how additions
# behave, and a median of three prints invites exactly the
# over-reading the number does not support.
MIN_N = 20


@st.cache_data(show_spinner=False)
def _apac_windows(mkt):
    p = ADIR / f"{mkt}.json"
    return (json.loads(p.read_text(encoding="utf-8")).get("windows") or {}
            if p.exists() else {})


@st.cache_data(show_spinner=False)
def _playbooks():
    p = ROOT / "data" / "apac_event_playbooks.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _coverage(mkt):
    """What this market's sample can and cannot support."""
    W = _apac_windows(mkt)
    px = [v for v in W.values() if v.get("px")]
    if not px:
        return None
    pre = sorted(sum(1 for r in v["px"] if r["d"] <= v["ann"])
                 for v in px)
    src = (px[0].get("src") or "")
    return {
        "market": mkt,
        "windows": len(px),
        "of": len(W),
        "ADD": sum(1 for v in px if v["action"] == "ADD"),
        "DEL": sum(1 for v in px if v["action"] == "DEL"),
        "reviews": len({v["rev"] for v in px}),
        "from": min(v["ann"] for v in px)[:7],
        "pre_sessions": pre[len(pre) // 2],
        "survivorship": ("delisted-safe" if "bhavcopy" in src
                         else "survivors only"),
        "aggregate?": "yes" if len(px) >= MIN_N else
                      f"NO — {len(px)} windows",
    }


def render():
    from views import design
    design.css()
    st.markdown("# Announcement → Effective — the rebalance "
                "window")
    # c-207: coverage in the status strip rather than buried in
    # a caption. Whether the sample is delisted-safe or
    # survivors-only changes what every number below means, so
    # it belongs above them.
    _W = _windows()
    _n = sum(1 for v in _W.values() if v.get("px"))
    _adir = ROOT / "data" / "apac_event_windows"
    _mk = len([p for p in _adir.glob("*.json")]) if \
        _adir.exists() else 0
    design.status(
        [("SCOPE", "TAIWAN + APAC"),
         ("FLOOR", "2015 (registry dates)"),
         ("TW WINDOWS", _n),
         ("APAC MARKETS", _mk)],
        right="TW DELISTED-SAFE · APAC SURVIVORS-ONLY",
        state="warn")
    t1, t2 = st.tabs(["Taiwan — full detail",
                      "APAC — every market"])
    with t1:
        _taiwan()
    with t2:
        _apac()


def _apac():
    from views import design
    """The same window study, market by market."""
    import pandas as pd
    import plotly.graph_objects as go
    if not ADIR.exists():
        st.info("No APAC windows yet. Run "
                "`py scripts\\apac_event_days.py all`.")
        return
    mkts = sorted(p.stem for p in ADIR.glob("*.json"))
    cov = [c for c in (_coverage(m) for m in mkts) if c]
    if not cov:
        st.info("No priced windows yet. Run "
                "`py scripts\\apac_event_days.py all`.")
        return

    st.caption(
        "Day 0 = the announcement date's LOCAL close — the last "
        "pre-news print in each market (MSCI announces from "
        "Geneva ~23:00 CET, which is the following morning "
        "across Asia). Cumulative returns are benchmarked to 0 "
        "at day 0. 2015 onwards, where announcement dates come "
        "from MSCI's registry rather than being estimated.")

    st.subheader("What each market's sample can support")
    st.dataframe(pd.DataFrame(cov), use_container_width=True,
                 hide_index=True)
    thin = [c["market"] for c in cov if c["windows"] < MIN_N]
    stale = [c["market"] for c in cov if c["pre_sessions"] < 28]
    if thin:
        st.warning(
            f"**Not aggregated:** {', '.join(thin)} — under "
            f"{MIN_N} priced windows. Their curves are drawn "
            "because individual paths are still worth seeing, "
            "but no median is reported. Hong Kong in particular "
            "has ONE addition in the whole sample.")
    if stale:
        st.error(
            "**The pre-announcement window on disk is ~18 "
            "sessions, not 30.** These files were harvested "
            "before the window was widened, so the "
            "pre-positioning lens below is limited to what was "
            "stored, and the rows are close-only (no OHLC). Run "
            "`py scripts\\apac_event_days.py all` to rebuild at "
            "45 calendar days either side. Until then the "
            "pre-announcement leg is a partial month, and every "
            "number computed from it is labelled accordingly.")
    surv = [c["market"] for c in cov
            if c["survivorship"] == "survivors only"]
    if surv:
        st.warning(
            "**Survivorship:** " + ", ".join(surv) + " are "
            "priced from Yahoo, which lists the living. A "
            "company deleted from the index that later delisted "
            "is absent, so DELETION medians in those markets "
            "lean optimistic. India and Taiwan are "
            "delisted-safe (exchange day-files). The measured "
            "size of the gap per market is in "
            "`data/apac_delisted_movers.json` — and the "
            "register check showed most missing names are still "
            "listed, i.e. our own ticker bugs rather than "
            "survivorship.")

    # ---- cross-market comparison ------------------------
    st.subheader("Drift from announcement to effective, by "
                 "market")
    pbs = _playbooks()
    rows = []
    for c in cov:
        pb = (pbs.get(c["market"]) or {}).get("playbook") or {}
        if c["windows"] < MIN_N:
            continue
        for act in ("ADD", "DEL"):
            a = pb.get(act) or {}
            if not a.get("n"):
                continue
            rows.append({"market": c["market"], "action": act,
                         "n": a["n"], "drift": a.get("drift"),
                         "gap1": a.get("gap1"),
                         "eff_day": a.get("eff_day"),
                         "revert5": a.get("revert5"),
                         "pre_drift": a.get("pre_drift"),
                         "vol xADV on eff":
                             a.get("vol_mult_eff")})
    if rows:
        df = pd.DataFrame(rows)
        fig = go.Figure()
        for act, col in (("ADD", "#2e7d52"), ("DEL", "#c0392b")):
            s = df[df.action == act]
            fig.add_bar(x=s.market, y=[100 * v for v in s.drift],
                        name=act, marker_color=col,
                        customdata=s.n,
                        # c-334: the side is the eyebrow, so the
                        # market can have the title to itself.
                        hovertemplate=design.hover(
                            "%{x}", eyebrow=act.lower(),
                            rows=[("drift", "%{y:.2f}%"),
                                  ("n", "%{customdata}")]))
        fig.add_hline(y=0, line_color="#888", line_width=1)
        fig.update_layout(
            height=380, barmode="group",
            yaxis_title="median drift, day 1 → effective-1 (%)",
            xaxis_title="")
        design.chart(fig)
        st.caption(
            "Median per market, so one violent print cannot set "
            "the bar. The trade the desk cares about is the "
            "SPREAD: a positive ADD bar with a negative DEL bar "
            "means the long/short pair drifted apart between "
            "announcement and effective. Markets under "
            f"{MIN_N} windows are excluded from this chart "
            "rather than shown with a thin median.")
        st.dataframe(df, use_container_width=True,
                     hide_index=True)

    # ---- per-market curves ------------------------------
    st.subheader("Every window, one market at a time")
    mkt = st.selectbox("Market", [c["market"] for c in cov],
                       key="apac_mkt")
    W = _apac_windows(mkt)
    c1, c2, c3 = st.columns([1, 1, 1])
    act = c1.radio("Show", ["Both", "ADD", "DEL"],
                   horizontal=True, key="apac_act")
    revs = sorted({v["rev"] for v in W.values()
                   if v.get("px")},
                  key=lambda r: min(v["ann"] for v in W.values()
                                    if v["rev"] == r),
                  reverse=True)
    pick = c2.selectbox("Single review", ["All"] + revs,
                        key="apac_rev")
    prepos = c3.checkbox("Pre-positioning lens (show sessions "
                         "BEFORE the announcement)",
                         value=False, key="apac_pre")
    sel = [v for v in W.values()
           if v.get("px")
           and (act == "Both" or v["action"] == act)
           and (pick == "All" or v["rev"] == pick)]
    if not sel:
        st.warning("No priced windows match the filter.")
        return
    _curves(sel, prepos)
    st.caption(f"{len(sel)} windows. Green = additions, red = "
               "deletions.")

    pb = (pbs.get(mkt) or {}).get("playbook") or {}
    if pb and len(sel) >= MIN_N:
        st.markdown(f"**{mkt} playbook** — medians across all "
                    "priced windows in this market")
        st.dataframe(pd.DataFrame([
            {"action": a, "n": pb[a]["n"],
             "day-1 gap": pb[a]["gap1"],
             "drift → E-1": pb[a]["drift"],
             "effective day": pb[a]["eff_day"],
             "revert E+5": pb[a]["revert5"],
             "pre-ann drift": pb[a]["pre_drift"],
             "eff-day vol (xADV)": pb[a]["vol_mult_eff"],
             "labels": str(pb[a]["labels"])}
            for a in ("ADD", "DEL") if pb.get(a, {}).get("n")]),
            use_container_width=True, hide_index=True)
    elif pb:
        st.info(f"{mkt} has {len(sel)} windows in view — under "
                f"the {MIN_N}-window bar, so no median is "
                "reported. Read the individual paths above.")


def _curves(sel, prepos):
    """Panel 1, shared by both tabs."""
    from views import design
    import plotly.graph_objects as go
    fig = go.Figure()
    eff_offsets = []
    for v in sel:
        px = v["px"]
        dts = [r["d"] for r in px]
        try:
            i0 = max(i for i, d in enumerate(dts)
                     if d <= v["ann"])
        except ValueError:
            continue
        if not prepos:
            px = px[i0:]
            dts = dts[i0:]
            i0 = 0
        base = px[i0]["c"]
        x = list(range(-i0, len(px) - i0))
        y = [100 * (r["c"] / base - 1) for r in px]
        ieff = next((i for i, d in enumerate(dts)
                     if d >= v["eff"]), None)
        if ieff is not None:
            eff_offsets.append(x[ieff])
        col = "#2e7d52" if v["action"] == "ADD" else "#c0392b"
        fig.add_scatter(
            x=x, y=y, mode="lines",
            line=dict(color=col, width=1.3),
            opacity=0.55 if len(sel) > 6 else 0.9,
            name=f"{v['rev']} {v['code']} {v['action']}",
            hovertemplate=design.hover(
                f"{v['code']} {v['name']}",
                eyebrow=f"{v['rev']} {v['action'].lower()}",
                rows=[("day", "%{x}"),
                      ("cumulative", "%{y:.1f}%")]))
    fig.add_hline(y=0, line_color="#888", line_width=1)
    if eff_offsets:
        if len(set(eff_offsets)) == 1:
            fig.add_vline(x=eff_offsets[0], line_dash="dash",
                          line_color="#1f4e79",
                          annotation_text="effective")
        else:
            med_eff = sorted(eff_offsets)[len(eff_offsets) // 2]
            fig.add_vline(
                x=med_eff, line_dash="dash",
                line_color="#1f4e79",
                annotation_text=f"effective (median day "
                f"+{med_eff}; range {min(eff_offsets)}-"
                f"{max(eff_offsets)})")
    fig.add_vline(x=0, line_dash="dot", line_color="#555",
                  annotation_text="announcement close")
    fig.update_layout(
        height=460, xaxis_title="trading days from "
        "announcement close (day 0 = pre-news baseline)",
        yaxis_title="cumulative return (%)",
        showlegend=(len(sel) <= 12))
    design.chart(fig)


def _taiwan():
    from views import design
    import pandas as pd
    import plotly.graph_objects as go
    st.caption(
        "Day 0 = the announcement date's Taipei close — the "
        "last PRE-NEWS print (Geneva announces ~23:00 CET, "
        "which is ~05:00 next morning in Taipei). Day 1 is the "
        "first session that can react. Cumulative returns are "
        "benchmarked to 0 at day 0.")
    W = _windows()
    st.caption("Taiwan: DELISTED-SAFE (TWSE day-files) "
               "with full flow overlays (t86/SBL/margin).")
    if not W:
        st.info("Run `py scripts\\tw_event_window.py harvest` "
                "first.")
        return
    revs = sorted({v["rev"] for v in W.values()},
                  key=lambda r: min(v["ann"] for v in W.values()
                                    if v["rev"] == r),
                  reverse=True)
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.4])
    act = c1.radio("Show", ["Both", "ADD", "DEL"],
                   horizontal=True)
    year_min = min(int(v["ann"][:4]) for v in W.values())
    yr = c2.slider("From year", year_min, 2026, year_min)
    pick = c3.selectbox("Single review", ["All"] + revs)
    prepos = c4.checkbox(
        "Pre-positioning lens (show 25d BEFORE announcement)",
        value=False,
        help="Drift and borrow build before day 0 = the "
             "market front-running the prediction.")

    sel = [v for v in W.values()
           if v["px"]
           and (act == "Both" or v["action"] == act)
           and int(v["ann"][:4]) >= yr
           and (pick == "All" or v["rev"] == pick)]
    if not sel:
        st.warning("No harvested windows match the filter.")
        return

    # ---- panel 1: cumulative returns ---------------------
    # c-196: the curve panel now lives in _curves() and is
    # shared with the APAC tab, so the two tabs cannot
    # drift apart in how they draw day 0 or the effective
    # marker. One definition, two renderings.
    _curves(sel, prepos)
    st.caption(
        f"{len(sel)} windows. Green = additions, red = "
        "deletions. Coverage note: exact announcement dates "
        "2015 onwards only. Announcement dates come from "
        "MSCI's registry, so day-0 is measured rather than "
        "inferred. Windows before 2015 exist on disk but are "
        "excluded: their announcement date was estimated as "
        "effective minus 10 business days, and the true gap "
        "measures 13, which placed day-0 three sessions late "
        "and put part of the announcement reaction inside the "
        "zero baseline.")

    # ---- panel 2: crowding overlays (2015+) --------------
    st.header("Crowding overlays")
    st.caption(
        "From the decade caches (2015+, per stock per day, "
        "already harvested): foreign net buying for adds, "
        "borrow balance for deletes, volume vs its own "
        "pre-announcement norm.")
    one = st.selectbox(
        "Pick one window",
        [f"{v['rev']} {v['code']} {v['action']} {v['name']}"
         for v in sel])
    v = sel[[f"{x['rev']} {x['code']} {x['action']} {x['name']}"
             for x in sel].index(one)]
    t86 = _flow("t86_history.json")
    sbl = _flow("sbl_history.json")
    dts = [r["d"] for r in v["px"]]
    keys = [d.replace("-", "") for d in dts]
    fnet = [(t86.get(k, {}).get(v["code"]) or {}).get("f")
            for k in keys]
    bor = [(sbl.get(k, {}).get(v["code"]) or [None, None])[1]
           for k in keys]
    vol = [r["v"] for r in v["px"]]
    i0 = max((i for i, d in enumerate(dts) if d <= v["ann"]),
             default=0)
    fig2 = go.Figure()
    x = list(range(-i0, len(dts) - i0))
    if any(f is not None for f in fnet):
        run, cum = 0.0, []
        for f in fnet:
            run += (f or 0)
            cum.append(run / 1e6)
        fig2.add_scatter(x=x, y=cum, name="cum foreign net "
                         "buy (M sh)", line=dict(
                             color="#1f4e79"))
    if any(b for b in bor):
        b0 = next((b for b in bor[i0:] if b), None)
        if b0:
            fig2.add_scatter(
                x=x, y=[(b / b0 * 100) if b else None
                        for b in bor],
                name="borrow balance (day0=100)",
                line=dict(color="#c0392b"), yaxis="y2")
    pre_v = [q for q in vol[:i0] if q] or [1]
    nv = sum(pre_v) / len(pre_v)
    fig2.add_bar(x=x, y=[(q or 0) / nv for q in vol],
                 name="volume / pre-ann avg",
                 marker_color="#b9c2c8", opacity=0.5,
                 yaxis="y3")
    fig2.add_vline(x=0, line_dash="dot", line_color="#555",
                   annotation_text="announcement close")
    # single window here -> the effective line is EXACT
    ieff1 = next((i for i, d in enumerate(dts)
                  if d >= v["eff"]), None)
    if ieff1 is not None:
        fig2.add_vline(x=ieff1 - i0, line_dash="dash",
                       line_color="#1f4e79",
                       annotation_text="effective")
    fig2.update_layout(
        height=380,
        yaxis=dict(title="cum foreign net (M sh)"),
        yaxis2=dict(overlaying="y", side="right",
                    title="borrow idx"),
        yaxis3=dict(overlaying="y", side="right",
                    showticklabels=False),
        xaxis_title="trading days from announcement close")
    design.chart(fig2)
    st.caption(
        "Reading it: for an ADD, foreign net buying that "
        "starts BEFORE day 0 = pre-positioning; the steeper "
        "the pre-announcement leg, the more crowded the "
        "trade. For a DEL, borrow building before day 0 says "
        "shorts anticipated it — and the borrow UNWIND after "
        "the effective day is the recall/cover flow.")

    # ---- panel 3: the playbook ---------------------------
    mp = ROOT / "data" / "event_window_metrics.json"
    if mp.exists():
        M = json.loads(mp.read_text(encoding="utf-8"))
        st.header("The playbook (aggregated, "
                  f"{M['n_analyzed']} windows)")
        st.caption(
            "Median market-adjusted paths per action. "
            f"Market adjustment: {M['market_adjustment']}. "
            "Framework and registered thresholds: "
            "docs/EVENT_WINDOW_FRAMEWORK.md. Labels: "
            "CLEAN-DRIFT (tradeable anticipation), "
            "FRONT-RUN-FADE (consensus already in the price), "
            "SQUEEZE (crowded short into effective), QUIET.")
        pb = M["playbook"]
        rows = []
        for act in ("ADD", "DEL"):
            a = pb[act]
            rows.append({
                "action": act, "n": a["n"],
                "day-1 gap": a["gap1"],
                "drift → E-1": a["drift"],
                "effective day": a["eff_day"],
                "revert E+5": a["revert5"],
                "revert E+20": a["revert20"],
                "pre-ann drift": a["pre_drift"],
                "eff-day vol (xADV)": a["vol_mult_eff"],
                "labels": str(a["labels"])})
        st.dataframe(pd.DataFrame(rows),
                     use_container_width=True, hide_index=True)
        with st.expander("Per-window metrics table"):
            st.dataframe(pd.DataFrame(M["windows"]),
                         use_container_width=True,
                         hide_index=True, height=380)
        st.info(
            "**Aug-2026 live loop:** from the first reaction "
            "session run `py scripts\\event_window_live.py "
            "pull` then `report` daily (Bill's terminal). Each "
            "report scores the declared shortlist against "
            "these historical distributions at the same "
            "day-offset and appends to the ledger — graded "
            "Sep-1.")
