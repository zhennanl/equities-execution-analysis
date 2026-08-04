"""T-day forecast cards — per-shortlist-name effective-date analytics.

Session 9i. For each shortlist candidate (a name that MIGHT be added/
deleted at the upcoming review), chain the project's MEASURED priors
into one card a PT trader can read before announcement day. TRANSPARENCY
IS THE CONTRACT: every metric on a card carries its formula, its data
source, and its sample size — the METHOD table below is rendered at the
top of every artifact, and no number appears without a "how".

Priors consumed (all measured in this project, none tuned):
  passive flow rate   review_engine.PASSIVE_OWN_RATE (5-9% of float)
  print multiples     data/event_flow_study.json (2026 measured events)
  auction shares      data/auction_study_2026.json (per-name measured)
  gap band            agents/violence_curve real points (n=17; the
                      share->gap NULL result is respected: band only)
  limit context       data/tw_limits.json (23 measured days)
  class exec costs    TWAP/VWAP/MOC decade study (109 name-events)
  crowding            live TWT93U/TPEx short reads where supplied
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

METHOD = {
    "p_convert": dict(
        rule="shortlist probability: P(any change, decade base rate "
             "for this market x review type) x visible share "
             "(1 - BLIND_SHARE) x proximity softmax",
        source="msci_decade_stats.json + review_engine.shortlist_"
               "candidates", basis="44 quarters 2015-2025"),
    "flow_if_converts_usd": dict(
        rule="cap x free-float x passive-ownership rate 5%-9% of "
             "float (lo-hi band). This is UNCONDITIONAL on p — the "
             "flow that prints IF the name converts",
        source="review_engine.PASSIVE_OWN_RATE",
        basis="literature + May-2026 measured event class"),
    "flow_p_weighted_usd": dict(
        rule="p_convert x midpoint of flow_if_converts — the "
             "EXPECTED-VALUE flow for desk capacity planning only; "
             "never use for T-day sizing (the print is all-or-"
             "nothing)", source="derived", basis="—"),
    "adv_days": dict(
        rule="flow_if_converts / ADV(USD); bucket: <1 MOC, 1-3 "
             "WORK+MOC, >3 MULTI-DAY",
        source="universe ADV + event_window bucket rule",
        basis="Step-2 planner convention"),
    "print_multiple": dict(
        rule="median / max of measured T-day volume multiples for "
             "this provider x side; NO-PRIOR stated when the class "
             "has no measured events (never borrowed silently)",
        source="event_flow_study.json via pitch_pack."
               "expected_t_multiples", basis="2026 measured events"),
    "expected_t_volume_usd": dict(
        rule="ADV x median print multiple (only when a measured "
             "prior exists)", source="derived", basis="—"),
    "auction_share_pct": dict(
        rule="range and median of MEASURED per-name closing-auction "
             "shares on TW effective days (control name excluded)",
        source="auction_study_2026.json",
        basis="Jun-18-2026 per-name measurements"),
    "auction_footprint_pct": dict(
        rule="mid flow_if_converts / (expected_t_volume x median "
             "EVENT-DAY auction share) — the fraction of the "
             "expected closing print the obligated flow represents. "
             "Values > 100%% are meaningful, not errors: the index "
             "flow IS most of the print on 16x days, and the print "
             "size and the flow co-adjust — read > 100%% as 'the "
             "flow cannot clear in one print at prior sizes' -> "
             "multi-day working or a larger-than-prior print",
        source="derived", basis="—"),
    "gap_band_bps": dict(
        rule="mean +/- std of |official close vs last continuous "
             "price| on measured event names. SIGN IS NOT PREDICTED: "
             "the violence-curve share->gap regression is a pinned "
             "NULL (R2~0), and the 6919/2344 cases show the print "
             "direction is set by the CROWD'S EXIT, not the index "
             "flow's side",
        source="violence_curve.load_points",
        basis="17 measured event points"),
    "limit_context": dict(
        rule="baseline daily %% of the TW tape touching / locking "
             "the +/-10%% band, and the print-day multiple; rule of "
             "thumb from the case studies: PRINT-DAY locks favor "
             "the obligated flow (band caps the price in the "
             "passive side's favor)",
        source="tw_limits.json (limit_moves_tw)",
        basis="19 baseline + 4 print days, exact tick math"),
    "crowding": dict(
        rule="live short-balance read (build vs 30-session baseline) "
             "where a cache is supplied; 'no live read' otherwise — "
             "never fabricated",
        source="TWT93U/TPEx via event_data", basis="daily official"),
    "playbook": dict(
        rule="discretion-matrix row for this side x crowding "
             "(illustrative envelope 20%) + the decade execution-"
             "cost table for the event class; MSCI-add WAIT rule is "
             "flagged as a demoted hypothesis where it applies",
        source="event_window.discretion_decision + "
               "TWAP_VWAP_MOC_STUDY",
        basis="decade tables: 109 TW name-events"),
}


# ---------------------------------------------------------------- priors
def gap_prior():
    from agents.violence_curve import load_points
    p = load_points()
    if p is None or len(p) < 10:
        return None
    g = p["gap_bps"].abs()
    return {"mean": round(float(g.mean()), 0),
            "std": round(float(g.std()), 0), "n": int(len(g))}


EVENT_DAYS = ("2026-06-18", "2026-05-29")     # the measured prints


def auction_share_prior(exclude=("2330.TW",), provider="MSCI",
                        side="Sell"):
    """Session 9i upgrade: class-conditional DIRECT prior from the
    IB 5m auction bars (86 name-days, tday_execution_studies) —
    replaces the n=4 event-day sample. Falls back to the old
    2026-prints sample if the studies file is absent."""
    f = ROOT / "data" / "tday_execution_studies.json"
    if f.exists():
        try:
            import pandas as _pd
            d = json.loads(f.read_text())
            dec = d["decompose"]
            key = f"('{provider}', '{side}')"
            if key in dec.get("share", {}):
                med = dec["share"][key] * 100
                n = dec["n"][key]
                return {"lo": None, "hi": None,
                        "med": round(med, 1), "n": int(n),
                        "basis": "DIRECT IB auction bars, class "
                                 f"{provider}/{side}"}
        except Exception:                              # noqa: BLE001
            pass
    f2 = ROOT / "data" / "auction_study_2026.json"
    if not f2.exists():
        return None
    a = json.loads(f2.read_text()).get("names", {})
    shares = [d["auction_share"] for t, days in a.items()
              if t not in exclude
              for day, d in days.items()
              if day in EVENT_DAYS and d.get("auction_share")]
    if not shares:
        return None
    s = pd.Series(shares)
    return {"lo": round(float(s.min()) * 100, 1),
            "hi": round(float(s.max()) * 100, 1),
            "med": round(float(s.median()) * 100, 1),
            "n": len(s), "basis": "2026 event-day sample"}


def limit_prior():
    f = ROOT / "data" / "tw_limits.json"
    if not f.exists():
        return None
    from scripts.limit_moves_tw import table
    df = table()
    base = df[df["kind"] == "baseline"]
    ev = df[df["kind"] != "baseline"]
    return {"base_touch_up": round(base["pct_touch_up"].mean(), 1),
            "base_lock_up": round(base["pct_lock_up"].mean(), 1),
            "event_touch_up": round(ev["pct_touch_up"].mean(), 1),
            "n_days": len(df)}


def class_costs():
    """Decade execution-cost medians per class (vs close, bps;
    negative = beat MOC). Computed from the study cache."""
    try:
        from scripts.twap_vwap_moc_study import build_table
        df, _ = build_table()
    except Exception:                                  # noqa: BLE001
        return None
    if not len(df):
        return None
    out = {}
    for (prov, side), g in df.groupby(["provider", "side"]):
        out[f"{prov}_{side}"] = {
            "vwap_w_med": round(g["VWAP_W_vs_close"].median(), 0),
            "n": len(g)}
    return out


# ----------------------------------------------------------------- cards
def build_cards(shortlist: pd.DataFrame, universe: pd.DataFrame,
                crowding_map: dict | None = None) -> list[dict]:
    from agents.pitch_pack import expected_t_multiples
    from agents.review_engine import PASSIVE_OWN_RATE
    from agents.event_window import discretion_decision
    ev_cache = json.loads(
        (ROOT / "data" / "event_flow_study.json").read_text())
    gp, lp, cc = gap_prior(), limit_prior(), class_costs()
    ap_by_side = {"Sell": auction_share_prior(side="Sell"),
                  "Buy": auction_share_prior(side="Buy")}
    uni = universe.set_index("ticker")
    cards = []
    for _, r in shortlist.iterrows():
        t = r["ticker"]
        if t.startswith("BELOW-FLOOR"):
            cards.append({"ticker": t, "side": r["side"],
                          "p_convert": r["p"],
                          "note": r["reasoning"] + " — no per-name "
                          "card is computable for the unobservable "
                          "band; this row exists so the probability "
                          "mass stays visible."})
            continue
        if t not in uni.index:
            continue
        u = uni.loc[t]
        cap, ff, adv = (float(u["full_mktcap_usd"]),
                        float(u["free_float_frac"]),
                        float(u["adv_usd"]))
        lo, hi = (cap * ff * PASSIVE_OWN_RATE[0],
                  cap * ff * PASSIVE_OWN_RATE[1])
        mid = (lo + hi) / 2
        side_ms = "Sell" if r["side"] == "DELETE" else "Buy"
        tm = expected_t_multiples(ev_cache, "MSCI", side_ms)
        adv_days = (lo / adv, hi / adv) if adv else (None, None)
        bucket = ("MOC" if adv_days[1] and adv_days[1] < 1 else
                  "WORK+MOC" if adv_days[1] and adv_days[1] < 3
                  else "MULTI-DAY")
        card = {
            "ticker": t, "side": r["side"],
            "p_convert": float(r["p"]),
            "p_how": r["reasoning"],
            "cap_usd_b": round(cap / 1e9, 2),
            "free_float": round(ff, 2),
            "flow_if_converts_usd_m": [round(lo / 1e6), round(hi / 1e6)],
            "flow_how": (f"cap ${cap/1e9:.1f}B x ff {ff:.2f} x "
                         f"{PASSIVE_OWN_RATE[0]:.0%}-"
                         f"{PASSIVE_OWN_RATE[1]:.0%} of float"),
            "flow_p_weighted_usd_m": round(r["p"] * mid / 1e6, 1),
            "adv_usd_m": round(adv / 1e6, 1),
            "adv_days": [round(x, 1) for x in adv_days]
            if adv_days[0] is not None else None,
            "bucket": bucket,
        }
        if tm.get("available"):
            card["print_multiple"] = {
                "median": tm["median"], "max": tm["max"],
                "n": tm["n"],
                "how": f"measured MSCI {side_ms} events 2026"}
            card["expected_t_volume_usd_m"] = round(
                adv * tm["median"] / 1e6)
            ap = ap_by_side.get(side_ms)
            if ap:
                exp_auc = adv * tm["median"] * ap["med"] / 100
                card["auction_share_prior_pct"] = ap
                card["auction_footprint_pct"] = round(
                    100 * mid / exp_auc, 1) if exp_auc else None
                card["footprint_how"] = (
                    f"mid flow ${mid/1e6:.0f}M / (ADV x "
                    f"{tm['median']}x x {ap['med']}% auction share; "
                    f"{ap.get('basis', '')} n={ap['n']})")
        else:
            card["print_multiple"] = {
                "available": False,
                "how": f"NO MEASURED MSCI {side_ms} TW events — "
                       "stated, not borrowed. (FTSE-class Buy prints "
                       "measured ~5x are a CROSS-CLASS reference "
                       "only.)"}
        if gp:
            card["gap_band_bps"] = {
                "band": f"|gap| {gp['mean']:.0f} +/- {gp['std']:.0f}",
                "n": gp["n"],
                "sign_rule": "direction NOT predicted (null pinned); "
                             "the crowd's exit sets the print "
                             "direction (6919/2344 exhibits)"}
        if lp:
            card["limit_context"] = (
                f"baseline {lp['base_touch_up']}% of tape touches "
                f"limit-up daily ({lp['base_lock_up']}% locks); "
                f"print days ~{lp['event_touch_up']}%; print-day "
                "locks historically FAVOR the obligated side")
        code = t.split(".")[0]
        crowd = (crowding_map or {}).get(code)
        card["crowding"] = crowd or "no live read (run with TW " \
                                    "short caches for the daily read)"
        dd = discretion_decision(side_ms, crowd, 20.0)
        # session 9i: MSCI TW Buy is now MEASURED (2025 events added
        # to the registry) — in-class prior preferred; FTSE stays as
        # the labeled fallback only if the in-class row is absent
        if side_ms == "Sell":
            cls, ref = (cc or {}).get("MSCI_Sell"), "TW MSCI deletes"
        else:
            cls, ref = (cc or {}).get("MSCI_Buy"), \
                "TW MSCI adds (measured, 2025 events)"
            if not cls:
                cls, ref = (cc or {}).get("FTSE_Buy"), \
                    "FTSE adds (cross-class ref)"
        cls_txt = ""
        if cls:
            cls_txt = (f"; class cost ({ref}): window-VWAP "
                       f"{cls['vwap_w_med']:+.0f} bps vs close "
                       f"(n={cls['n']})")
        card["playbook"] = (f"{dd['decision']} — {dd['rationale']} "
                            f"[illustrative 20% envelope]{cls_txt}")
        if side_ms == "Buy":
            card["playbook"] += ("; NOTE MSCI-add WAIT rule is a "
                                 "demoted hypothesis (decade: adds "
                                 "grind up; Aug-2026 arbitrates)")
        cards.append(card)
    return cards


def render_cards_md(cards: list[dict], event_name: str,
                    as_of: str) -> str:
    L = [f"# T-Day Forecast Cards — {event_name}",
         f"*Generated {as_of}. Cards exist for SHORTLIST candidates "
         "— names that MIGHT convert at announcement. Every number "
         "traces to the METHOD table; if a prior does not exist for "
         "a class, the card says so.*\n",
         "## METHOD — how every metric is calculated\n",
         "| metric | rule | source | basis |", "|---|---|---|---|"]
    for m, d in METHOD.items():
        L.append(f"| {m} | {d['rule']} | {d['source']} | "
                 f"{d['basis']} |")
    L.append("")
    for c in cards:
        if "note" in c:
            L.append(f"## {c['side']} — {c['ticker']} "
                     f"(p={c['p_convert']})\n\n{c['note']}\n")
            continue
        L.append(f"## {c['side']} {c['ticker']} — p={c['p_convert']}"
                 f" (cap ${c['cap_usd_b']}B, ff {c['free_float']})\n")
        L.append(f"- **p basis**: {c['p_how']}")
        L.append(f"- **Flow if converts**: "
                 f"${c['flow_if_converts_usd_m'][0]}-"
                 f"{c['flow_if_converts_usd_m'][1]}M "
                 f"({c['flow_how']}); p-weighted "
                 f"${c['flow_p_weighted_usd_m']}M (capacity "
                 "planning only)")
        if c.get("adv_days"):
            L.append(f"- **ADV-days**: {c['adv_days'][0]}-"
                     f"{c['adv_days'][1]} (ADV ${c['adv_usd_m']}M) "
                     f"-> bucket **{c['bucket']}**")
        pm = c["print_multiple"]
        if pm.get("available", True) and "median" in pm:
            L.append(f"- **Print multiple**: median {pm['median']}x "
                     f"/ max {pm['max']}x (n={pm['n']}; "
                     f"{pm['how']}) -> expected T volume "
                     f"~${c['expected_t_volume_usd_m']}M")
            if c.get("auction_footprint_pct") is not None:
                ap = c["auction_share_prior_pct"]
                rng = (f"{ap['lo']}-{ap['hi']}% range, "
                       if ap.get("lo") is not None else "")
                L.append(f"- **Auction**: share prior {rng}med "
                         f"{ap['med']}% (n={ap['n']}, "
                         f"{ap.get('basis', 'measured')}); our "
                         f"footprint "
                         f"**{c['auction_footprint_pct']}%** of the "
                         f"expected print ({c['footprint_how']})")
        else:
            L.append(f"- **Print multiple**: {pm['how']}")
        if c.get("gap_band_bps"):
            g = c["gap_band_bps"]
            L.append(f"- **Gap band**: {g['band']} bps "
                     f"(n={g['n']}); {g['sign_rule']}")
        if c.get("limit_context"):
            L.append(f"- **Limit bands**: {c['limit_context']}")
        L.append(f"- **Crowding**: {c['crowding']}")
        L.append(f"- **Playbook**: {c['playbook']}\n")
    return "\n".join(L)
