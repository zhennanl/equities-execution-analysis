"""The three-persona study of the announcement->effective
window, answered on Taiwan's 115 historical windows (c-130).

Personas and the questions they need answered (full reasoning
in docs/PERSONA_PLAYBOOK.md):

  TRACKER (BlackRock/Vanguard): benchmark = the effective
  close; the only decision is close-vs-early and its cost.
    P1 what does trading AT the close cost (the print vs E-1)?
    P2 what does pre-trading early cost instead (the drift)?
    P3 is the close print systematically rich/cheap (does it
       revert)?
    P4 can the close absorb the size (volume multiples)?

  HEDGE FUND (Millennium pod): alpha = anticipate the flow.
    H1 total tradeable alpha day1->E-1, and IS IT DECAYING?
    H2 how much is gone after day 1 (entry timing)?
    H3 exit at E-1 or hold INTO the close?
    H4 the reversal trade (fade the close, cover E+5): edge +
       hit rate?
    H5 does the market front-run announcements (pre-ann drift
       + borrow build on eventual movers)?
    H6 hit rates and tails (is this a carry trade or a coin)?

  AGENCY PT DESK (CLSA): advice + crossing + the mandate.
    C1 how much flow prints BEFORE the close (progress at E-1)?
    C2 the client table: full-close vs partial-early costs
       (P1 vs P2 assembled).
    C3 do arbs sell INTO the close (liquidity for my client)?
       (= sign of eff_day: adds falling ON effective day means
       supply met the trackers)
    C4 which T-3 indicators predict a bad close (crowding
       triage: PRE/borrow tercile vs eff_day)?
    C5 post-effective fade advice (H4 reframed).

Everything computed from data already on disk; every answer
carries n. Output: data/persona_study_tw.json + console.
"""
import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "persona_study_tw.json"


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(st.median(xs), 4) if xs else None


def frac(xs, cond):
    xs = [x for x in xs if x is not None]
    return round(sum(1 for x in xs if cond(x)) / len(xs), 3) \
        if xs else None


def main():
    m = json.loads((ROOT / "data" / "event_window_metrics.json")
                   .read_text(encoding="utf-8"))
    W = m["windows"]
    adds = [w for w in W if w["action"] == "ADD"]
    dels = [w for w in W if w["action"] == "DEL"]
    out = {"n": {"windows": len(W), "adds": len(adds),
                 "dels": len(dels)}}

    # ---------- TRACKER ----------------------------------
    out["P1_close_cost"] = {
        "question": "what does the effective close itself cost "
                    "vs the E-1 close?",
        "ADD_eff_day_med": med([w["eff_day"] for w in adds]),
        "DEL_eff_day_med": med([w["eff_day"] for w in dels]),
        "read": "the tracker BUYS adds at a print that is this "
                "far above/below E-1; negative for adds = the "
                "close was actually CHEAPER than E-1"}
    out["P2_early_cost"] = {
        "question": "what does pre-trading cost instead (the "
                    "drift you chase day2->E-1)?",
        "ADD_drift_med": med([w["drift"] for w in adds]),
        "DEL_drift_med": med([w["drift"] for w in dels]),
        "ADD_gap1_med": med([w["gap1"] for w in adds]),
        "read": "buying early means paying the drift; buying "
                "day-1 means paying the gap first"}
    out["P3_close_reverts"] = {
        "question": "is the close print systematically rich?",
        "ADD_revert5_med": med([w["revert5"] for w in adds]),
        "ADD_frac_reverting": frac([w["revert5"] for w in adds],
                                   lambda x: x < 0),
        "DEL_revert5_med": med([w["revert5"] for w in dels]),
        "DEL_frac_reverting": frac([w["revert5"] for w in dels],
                                   lambda x: x > 0),
        "read": "adds falling after E / dels bouncing after E "
                "= the close was a temporarily-pressured print"}
    vm = [w["vol_mult_eff"] for w in W]
    out["P4_close_capacity"] = {
        "question": "can the close absorb the size?",
        "eff_day_volume_x_ADV_med": med(vm),
        "p90": round(sorted([x for x in vm if x])[
            int(0.9 * len([x for x in vm if x]))], 2)
        if any(vm) else None,
        "read": "effective-day volume runs this multiple of "
                "normal — the day the whole market shows up"}

    # ---------- HEDGE FUND -------------------------------
    def era(w):
        y = int(w["ann"][:4])
        return ("2010-14" if y <= 2014 else
                "2015-18" if y <= 2018 else
                "2019-22" if y <= 2022 else "2023-26")
    out["H1_alpha_and_decay"] = {
        "question": "total alpha day1->E-1, by era — decaying?",
        "ADD_total_alpha_med": med([w["total_alpha"]
                                    for w in adds]),
        "DEL_total_alpha_med": med([w["total_alpha"]
                                    for w in dels]),
        "ADD_by_era": {e: med([w["total_alpha"] for w in adds
                               if era(w) == e])
                       for e in ("2010-14", "2015-18",
                                 "2019-22", "2023-26")},
        "DEL_by_era": {e: med([w["total_alpha"] for w in dels
                               if era(w) == e])
                       for e in ("2010-14", "2015-18",
                                 "2019-22", "2023-26")}}
    out["H2_entry_timing"] = {
        "question": "how much is left after day 1?",
        "ADD_capture_med": med([w["capture"] for w in adds]),
        "read": "capture = drift/(gap+drift): the share of the "
                "move NOT taken instantly. >0.5 = latecomers "
                "still ate most of it"}
    out["H3_exit_timing"] = {
        "question": "exit E-1 or hold into the close?",
        "ADD_extra_from_holding": med([w["eff_day"]
                                       for w in adds]),
        "ADD_frac_close_higher": frac([w["eff_day"]
                                       for w in adds],
                                      lambda x: x > 0),
        "read": "positive = the close pays you to hold and "
                "sell TO the trackers; negative = exit E-1"}
    out["H4_reversal_trade"] = {
        "question": "fade the close (short adds / buy dels at "
                    "E close, unwind E+5): edge + hit rate?",
        "short_ADD_edge_med": med([-w["revert5"]
                                   for w in adds]),
        "short_ADD_hit": frac([w["revert5"] for w in adds],
                              lambda x: x < 0),
        "long_DEL_edge_med": med([w["revert5"] for w in dels]),
        "long_DEL_hit": frac([w["revert5"] for w in dels],
                             lambda x: x > 0)}
    out["H5_front_running"] = {
        "question": "does the market pre-position before the "
                    "announcement?",
        "ADD_pre_drift_med": med([w["pre_drift"]
                                  for w in adds]),
        "DEL_pre_drift_med": med([w["pre_drift"]
                                  for w in dels]),
        "DEL_borrow_build_pre_med": med(
            [w["borrow_build_pre"] for w in dels]),
        "read": "adds already up / dels already down before "
                "day 0, and borrow built pre-announcement = "
                "the prediction was tradeable consensus"}
    out["H6_hit_rates"] = {
        "ADD_alpha_hit": frac([w["total_alpha"] for w in adds],
                              lambda x: x > 0),
        "DEL_alpha_hit": frac([w["total_alpha"] for w in dels],
                              lambda x: x < 0),
        "ADD_worst": min((w["total_alpha"] for w in adds
                          if w["total_alpha"] is not None),
                         default=None),
        "ADD_best": max((w["total_alpha"] for w in adds
                         if w["total_alpha"] is not None),
                        default=None)}

    # ---------- AGENCY PT DESK ---------------------------
    prog = [w["progress_eff_minus1"] for w in adds
            if w.get("progress_eff_minus1") is not None]
    out["C1_flow_before_close"] = {
        "question": "how much of expected passive demand "
                    "printed as foreign net buy by E-1?",
        "ADD_progress_Eminus1_med": med(prog), "n": len(prog),
        "read": ">1 = arbs accumulated MORE than tracker "
                "demand before the close (inventory to sell "
                "into it); <0.5 = the close must do the work"}
    # C4: crowding triage — eff_day by PRE tercile (adds)
    pres = sorted([w["PRE"] for w in adds
                   if w["PRE"] is not None])
    if len(pres) >= 9:
        t1, t2 = pres[len(pres) // 3], pres[2 * len(pres) // 3]
        lo = [w["eff_day"] for w in adds if w["PRE"] <= t1]
        hi = [w["eff_day"] for w in adds if w["PRE"] >= t2]
        out["C4_crowding_triage"] = {
            "question": "does high pre-positioning predict a "
                        "worse close for the tracker?",
            "ADD_eff_day_lowPRE_med": med(lo),
            "ADD_eff_day_highPRE_med": med(hi),
            "PRE_terciles": [round(t1, 3), round(t2, 3)],
            "read": "if high-PRE closes are lower (adds), the "
                    "crowd sells into the tracker's buy — the "
                    "client should shift flow earlier"}
    out["C3_arb_exit"] = {
        "question": "do arbs sell into the close?",
        "evidence": {
            "ADD_eff_day_med": med([w["eff_day"]
                                    for w in adds]),
            "ADD_drift_med": med([w["drift"] for w in adds])},
        "read": "drift up then a flat/negative effective day "
                "= supply meeting the trackers AT the close — "
                "the arbs' exit IS the tracker's liquidity"}

    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    for k, v in out.items():
        if k == "n":
            continue
        print(f"== {k}")
        for kk, vv in v.items():
            if kk not in ("question", "read"):
                print(f"   {kk}: {vv}")
    print(f"-> {OUT.name}")


if __name__ == "__main__":
    main()
