"""The Question-Bank batch run (c-135): Q1-Q34 answered where
the data reaches, plus Bill's close-auction question.

Sources (all local): tw_event_windows (179), t86 / sbl /
margin (per stock per day 2015+), twii_daily, industry map,
reconstruct verdicts (the engine join), ib_bars (5-minute bars
incl. the 13:25 last-continuous and 13:30 auction prints for
event names 2023+ — Bill's auction question).

DEFERRED with reasons (honesty ledger in the output):
  Q4 TAIFEX OI, Q5 ETF creations, Q12 TDCC brackets (weekly
  archive too short), Q15 SBL supply limit (field not in our
  cache), Q19/Q20 peers (peer price windows not harvested —
  t86-activity proxy only), Q21 ADR, Q26 skipped-name windows
  (non-mover windows not harvested).

Usage: py scripts\\liquidity_qa.py
Output: data/liquidity_qa_tw.json + console digest
"""
import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "liquidity_qa_tw.json"


def _num(x):
    try:
        return float(str(x).replace(",", ""))
    except (ValueError, TypeError):
        return None


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(st.median(xs), 4) if xs else None


def pct(xs, p):
    xs = sorted(x for x in xs if x is not None)
    return round(xs[min(len(xs) - 1,
                        int(p * len(xs)))], 4) if xs else None


def corr(a, b):
    pairs = [(x, y) for x, y in zip(a, b)
             if x is not None and y is not None]
    if len(pairs) < 8:
        return None
    xs, ys = zip(*pairs)
    mx, my = st.mean(xs), st.mean(ys)
    sx = (sum((x - mx) ** 2 for x in xs)) ** 0.5
    sy = (sum((y - my) ** 2 for y in ys)) ** 0.5
    if not sx or not sy:
        return None
    return round(sum((x - mx) * (y - my)
                     for x, y in pairs) / sx / sy, 3)


def main():
    W = json.loads((ROOT / "data" / "tw_event_windows.json")
                   .read_text(encoding="utf-8"))["windows"]
    # c-188: 2015 floor — see scripts/study_window.py
    import sys as _sys
    _sys.path.insert(0, str(ROOT / 'scripts'))
    from study_window import filter_windows
    W = filter_windows(W)
    t86 = json.loads((ROOT / "data" / "t86_history.json")
                     .read_text(encoding="utf-8"))
    sbl = json.loads((ROOT / "data" / "sbl_history.json")
                     .read_text(encoding="utf-8"))
    mg = json.loads((ROOT / "data" / "margin_history.json")
                    .read_text(encoding="utf-8"))
    twii = json.loads((ROOT / "data" / "twii_daily.json")
                      .read_text(encoding="utf-8"))

    def mgf(k, c, i):
        r = (mg.get(k, {}).get(c) or {}).get("raw")
        return _num(r[i]) if r and len(r) > i else None

    # ---- window frame extraction -------------------------
    rows = []
    for v in W.values():
        px = v["px"]
        if len(px) < 12:
            continue
        dts = [r["d"] for r in px]
        cl = [r["c"] for r in px]
        vol = [r["v"] for r in px]
        i0 = max((i for i, d in enumerate(dts)
                  if d <= v["ann"]), default=None)
        ie = max((i for i, d in enumerate(dts)
                  if d <= v["eff"]), default=None)
        if i0 is None or ie is None or ie <= i0 + 3 \
                or len(px) < ie + 2:
            continue
        keys = [d.replace("-", "") for d in dts]
        c = v["code"]
        adv = st.median([q for q in vol[max(0, i0 - 20):i0]
                         if q] or [1])
        f = [(t86.get(k, {}).get(c) or {}).get("f")
             for k in keys]
        bor = [(sbl.get(k, {}).get(c) or [None, None])[1]
               for k in keys]
        marg = [mgf(k, c, 5) for k in keys]
        shrt = [mgf(k, c, 11) for k in keys]
        r = {"rev": v["rev"], "code": c, "action": v["action"],
             "year": int(v["ann"][:4]),
             "month": v["ann"][5:7],
             "eff": v["eff"], "i0": i0, "ie": ie,
             "adv": adv, "px_close": cl, "vol": vol,
             "dts": dts, "f": f, "bor": bor, "marg": marg,
             "shrt": shrt,
             "price_lvl": cl[i0],
             "drift": cl[ie - 1] / cl[min(i0 + 1, ie - 1)] - 1,
             "eff_day": cl[ie] / cl[ie - 1] - 1,
             "revert5": cl[min(ie + 5, len(cl) - 1)]
             / cl[ie] - 1,
             "total": cl[ie - 1] / cl[i0] - 1,
             "vol_eff_x": (vol[ie] / adv
                           if adv and vol[ie] else None)}
        rows.append(r)
    adds = [r for r in rows if r["action"] == "ADD"]
    dels = [r for r in rows if r["action"] == "DEL"]
    out = {"n": len(rows), "answers": {}, "deferred": {
        "Q4": "TAIFEX SSF OI not harvested",
        "Q5": "ETF creation series needs the AJAX id",
        "Q12": "TDCC weekly archive too short (2026 only)",
        "Q15": "SBL supply-limit field not in cache",
        "Q19_Q20": "peer price windows not harvested; "
                   "t86-activity proxy only would conflate",
        "Q21": "ADR series one Yahoo call away",
        "Q26": "skipped-name price windows not harvested"}}
    A = out["answers"]

    # Q1 counterparty decomposition on E (2015+)
    q1 = []
    for r in rows:
        if r["year"] < 2015:
            continue
        ie = r["ie"]
        fe = r["f"][ie]
        dm = (r["marg"][ie] - r["marg"][ie - 1]
              if r["marg"][ie] and r["marg"][ie - 1] else None)
        ds = (r["shrt"][ie] - r["shrt"][ie - 1]
              if r["shrt"][ie] and r["shrt"][ie - 1] else None)
        va = r["vol"][ie]
        if fe is not None and va:
            q1.append({"act": r["action"],
                       "f_share": fe / va,
                       "marg_share": (dm * 1000 / va
                                      if dm is not None
                                      else None),
                       "short_share": (ds * 1000 / va
                                       if ds is not None
                                       else None)})
    A["Q1_eff_day_counterparties"] = {
        "ADD": {"foreign_net/vol_med":
                med([x["f_share"] for x in q1
                     if x["act"] == "ADD"]),
                "margin_chg/vol_med":
                med([x["marg_share"] for x in q1
                     if x["act"] == "ADD"]),
                "short_chg/vol_med":
                med([x["short_share"] for x in q1
                     if x["act"] == "ADD"])},
        "DEL": {"foreign_net/vol_med":
                med([x["f_share"] for x in q1
                     if x["act"] == "DEL"]),
                "margin_chg/vol_med":
                med([x["marg_share"] for x in q1
                     if x["act"] == "DEL"]),
                "short_chg/vol_med":
                med([x["short_share"] for x in q1
                     if x["act"] == "DEL"])},
        "read": "on E, foreign net buys this share of an ADD's "
                "volume; margin (retail, lots->shares x1000) "
                "and short deltas show who else moved"}

    # Q2 migration vs churn
    q2 = []
    for r in adds:
        if r["year"] < 2015:
            continue
        fs = [x for x in r["f"][r["i0"] + 1:r["ie"] + 1]
              if x is not None]
        gross = sum(x for x in r["vol"][r["i0"] + 1:
                                        r["ie"] + 1] if x)
        if fs and gross:
            q2.append({"mig": abs(sum(fs)) / gross,
                       "revert5": r["revert5"]})
    if len(q2) >= 12:
        xs = sorted(x["mig"] for x in q2)
        t = xs[len(xs) // 2]
        A["Q2_migration_vs_churn_ADD"] = {
            "migration_ratio_med": round(t, 3),
            "high_migration_revert5":
                med([x["revert5"] for x in q2
                     if x["mig"] > t]),
            "low_migration_revert5":
                med([x["revert5"] for x in q2
                     if x["mig"] <= t]),
            "read": "|cum foreign net| / gross volume; high = "
                    "ownership genuinely migrated"}

    # Q3 add<->del rotation within events
    from collections import defaultdict
    ev = defaultdict(lambda: {"ADD": [], "DEL": []})
    for r in rows:
        if r["year"] >= 2015:
            ev[r["rev"]][r["action"]].append(r)
    rots = []
    for rev, g in ev.items():
        for a in g["ADD"]:
            for d in g["DEL"]:
                fa = a["f"][a["i0"] + 1:a["ie"]]
                fd = d["f"][d["i0"] + 1:d["ie"]]
                n = min(len(fa), len(fd))
                cc = corr(fa[:n], fd[:n])
                if cc is not None:
                    rots.append(cc)
    A["Q3_add_del_rotation"] = {
        "n_pairs": len(rots),
        "daily_flow_corr_med": med(rots),
        "read": "negative correlation = same-day rotation "
                "(foreigners buying the add while selling the "
                "del)"}

    # Q6/Q7/Q8 volume profile
    prof = defaultdict(list)
    e1rank, weak_e1 = [], []
    for r in rows:
        i0, ie, adv = r["i0"], r["ie"], r["adv"]
        if not adv:
            continue
        for i in range(i0, min(ie + 1, len(r["vol"]))):
            if r["vol"][i]:
                prof[i - ie].append(r["vol"][i] / adv)
        win = [q for q in r["vol"][i0 + 1:ie + 1] if q]
        if len(win) > 3:
            e1 = r["vol"][ie - 1]
            e1rank.append(sorted(win, reverse=True)
                          .index(e1) + 1 if e1 in win else None)
            if e1 and e1 / adv < 2:
                weak_e1.append(r["eff_day"])
    A["Q6_volume_profile"] = {
        str(k): med(v) for k, v in sorted(prof.items())
        if -10 <= k <= 2 and len(v) >= 20}
    A["Q7_Eminus1"] = {
        "E-1_rank_in_window_med": med(e1rank),
        "eff_day_when_E-1_weak(<2xADV)": med(weak_e1),
        "n_weak": len(weak_e1)}
    cent = defaultdict(list)
    for r in rows:
        i0, ie = r["i0"], r["ie"]
        ws = [(i - i0, q) for i, q in
              enumerate(r["vol"]) if i0 < i <= ie and q]
        tot = sum(q for _, q in ws)
        if tot:
            c_ = sum(t * q for t, q in ws) / tot / (ie - i0)
            era = ("2010-14" if r["year"] <= 2014 else
                   "2015-18" if r["year"] <= 2018 else
                   "2019-22" if r["year"] <= 2022 else
                   "2023-26")
            cent[era].append(c_)
    A["Q8_profile_centroid_by_era"] = {
        e: med(v) for e, v in sorted(cent.items())}

    # Q10 hangover
    q10 = []
    for r in rows:
        ie, adv = r["ie"], r["adv"]
        if not adv:
            continue
        n = None
        for j, q in enumerate(r["vol"][ie + 1:ie + 21]):
            if q and q / adv < 1.5:
                n = j + 1
                break
        q10.append(n if n is not None else 21)
    A["Q10_hangover_days_to_1.5xADV"] = {
        "med": med(q10), "p90": pct(q10, 0.9)}

    # Q13 elasticity kink (drift vs realized eff-vol multiple)
    pairs = [(r["vol_eff_x"], r["total"]) for r in adds
             if r["vol_eff_x"]]
    if len(pairs) >= 12:
        pairs.sort()
        k3 = len(pairs) // 3
        A["Q13_elasticity"] = {
            "low_demand_total_med":
                med([y for _, y in pairs[:k3]]),
            "mid": med([y for _, y in pairs[k3:2 * k3]]),
            "high_demand_total_med":
                med([y for _, y in pairs[2 * k3:]]),
            "read": "realized eff-volume multiple as the "
                    "demand proxy; monotone rise without "
                    "saturation = no kink visible yet"}

    # Q14 price-level buckets
    A["Q14_price_level_ADD"] = {
        "low(<50 TWD)": med([r["total"] for r in adds
                             if r["price_lvl"] < 50]),
        "mid": med([r["total"] for r in adds
                    if 50 <= r["price_lvl"] < 300]),
        "high(>=300)": med([r["total"] for r in adds
                            if r["price_lvl"] >= 300])}

    # Q16 borrow unwind speed vs bounce
    q16 = []
    for r in dels:
        ie = r["ie"]
        b0 = r["bor"][ie] if r["bor"][ie] else None
        b5 = next((b for b in r["bor"][ie + 5:ie + 8] if b),
                  None)
        if b0 and b5:
            q16.append({"unwind": 1 - b5 / b0,
                        "revert5": r["revert5"]})
    if q16:
        xs = sorted(x["unwind"] for x in q16)
        t = xs[len(xs) // 2]
        A["Q16_borrow_unwind_DEL"] = {
            "fast_unwind_revert5":
                med([x["revert5"] for x in q16
                     if x["unwind"] > t]),
            "slow_unwind_revert5":
                med([x["revert5"] for x in q16
                     if x["unwind"] <= t]),
            "n": len(q16)}

    # Q17 retail vs institutional shorts
    q17 = []
    for r in dels:
        i0, ie = r["i0"], r["ie"]
        ds = (r["shrt"][ie] - r["shrt"][i0]
              if r["shrt"][ie] and r["shrt"][i0] else None)
        db = (r["bor"][ie] - r["bor"][i0]
              if r["bor"][ie] and r["bor"][i0] else None)
        if ds is not None and db is not None:
            q17.append({"retail_up": ds > 0, "inst_up": db > 0,
                        "total": r["total"]})
    if q17:
        both = [x for x in q17 if x["retail_up"]
                and x["inst_up"]]
        opp = [x for x in q17 if x["retail_up"]
               != x["inst_up"]]
        A["Q17_short_battle_DEL"] = {
            "same_side_n": len(both),
            "same_side_total_med": med([x["total"]
                                        for x in both]),
            "opposite_n": len(opp),
            "opposite_total_med": med([x["total"]
                                       for x in opp])}

    # Q18 recall-squeeze signature
    q18 = []
    for r in dels:
        ie = r["ie"]
        pb = list(zip(r["px_close"][ie:ie + 6],
                      r["bor"][ie:ie + 6]))
        dp = [b[0] - a[0] for a, b in zip(pb, pb[1:])
              if a[0] and b[0]]
        db = [b[1] - a[1] for a, b in zip(pb, pb[1:])
              if a[1] and b[1]]
        cc = corr(dp, db)
        if cc is not None:
            q18.append({"corr": cc, "revert5": r["revert5"]})
    if q18:
        forced = [x for x in q18 if x["corr"] > 0.3]
        vol_ = [x for x in q18 if x["corr"] < -0.3]
        A["Q18_squeeze_signature_DEL"] = {
            "price_and_borrow_fall_together(forced)_revert5":
                med([x["revert5"] for x in forced]),
            "borrow_falls_as_price_bounces(voluntary)_revert5":
                med([x["revert5"] for x in vol_]),
            "n": (len(forced), len(vol_))}

    # Q22 market drain on E (t86 total activity proxy)
    eff_days = {r["eff"].replace("-", "") for r in rows
                if r["year"] >= 2015}
    mov = {(r["eff"].replace("-", ""), r["code"])
           for r in rows}
    drains, norms = [], []
    kk = sorted(t86)
    for i, k in enumerate(kk[20:-1], start=20):
        tot = sum(abs(x.get("f") or 0)
                  for c2, x in t86[k].items()
                  if (k, c2) not in mov)
        (drains if k in eff_days else norms).append(tot)
    if drains and norms:
        A["Q22_market_drain"] = {
            "ex-mover_|foreign|_on_E_vs_normal":
                round(st.median(drains) / st.median(norms), 3),
            "read": ">1 = MORE market-wide foreign activity on "
                    "effective days, not a drain"}

    # Q23 flow momentum
    fe, fl = [], []
    for r in adds:
        if r["year"] < 2015:
            continue
        i0, ie = r["i0"], r["ie"]
        a = [x for x in r["f"][i0 + 1:i0 + 4]
             if x is not None]
        b = [x for x in r["f"][i0 + 4:ie] if x is not None]
        if a and b and r["adv"]:
            fe.append(sum(a) / r["adv"])
            fl.append(sum(b) / len(b) * 3 / r["adv"])
    A["Q23_flow_momentum_ADD"] = {
        "corr(early_flow, later_flow)": corr(fe, fl),
        "n": len(fe)}

    # Q24 build speed vs level (dels)
    q24 = []
    for r in dels:
        i0, ie = r["i0"], r["ie"]
        b0 = r["bor"][i0]
        be = next((b for b in r["bor"][ie::-1] if b), None)
        if b0 and be and ie > i0:
            q24.append({"speed": (be / b0 - 1) / (ie - i0),
                        "total": r["total"]})
    if len(q24) >= 12:
        xs = sorted(x["speed"] for x in q24)
        t = xs[2 * len(xs) // 3]
        A["Q24_build_speed_DEL"] = {
            "fast_build_total_med": med([x["total"]
                                         for x in q24
                                         if x["speed"] > t]),
            "slow_build_total_med": med([x["total"]
                                         for x in q24
                                         if x["speed"] <= t])}

    # Q25 the engine join: EXPLAINED vs NOT dels
    verd = {}
    for p in (ROOT / "data" / "reconstruct").glob("TW_*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        for v2 in d.get("verdicts", []):
            verd[(d["review"], v2["code"])] = \
                v2["verdict"].split(":")[0]
    q25 = defaultdict(list)
    for r in dels:
        k = (r["rev"], r["code"])
        if k in verd:
            q25[verd[k]].append(r)
    A["Q25_engine_join_DEL"] = {
        v: {"n": len(g),
            "pre+window_total_med": med([x["total"]
                                         for x in g]),
            "eff_day_med": med([x["eff_day"] for x in g]),
            "revert5_med": med([x["revert5"] for x in g])}
        for v, g in q25.items() if len(g) >= 3}

    # Q27 the scissors by era
    sc = {}
    for e, lo, hi in (("2010-14", 0, 2014),
                      ("2015-18", 2015, 2018),
                      ("2019-22", 2019, 2022),
                      ("2023-26", 2023, 2026)):
        g = [r for r in adds if lo <= r["year"] <= hi]
        sc[e] = {"vol_eff_x_med": med([r["vol_eff_x"]
                                       for r in g]),
                 "drift_med": med([r["drift"] for r in g]),
                 "n": len(g)}
    A["Q27_scissors"] = sc

    # Q28 2020 auction reform split
    A["Q28_reform_split_ADD"] = {
        "pre_2020-03": {
            "eff_day_med": med([r["eff_day"] for r in adds
                                if r["eff"] < "2020-03"]),
            "vol_eff_x_med": med([r["vol_eff_x"] for r in adds
                                  if r["eff"] < "2020-03"])},
        "post": {
            "eff_day_med": med([r["eff_day"] for r in adds
                                if r["eff"] >= "2020-03"]),
            "vol_eff_x_med": med([r["vol_eff_x"] for r in adds
                                  if r["eff"] >= "2020-03"])}}

    # Q29 November habit post-2023
    A["Q29_nov_habit_post2023_ADD"] = {
        "Nov": med([r["total"] for r in adds
                    if r["year"] >= 2023
                    and r["month"] == "11"]),
        "other_months": med([r["total"] for r in adds
                             if r["year"] >= 2023
                             and r["month"] != "11"])}

    # Q30 vol-regime elasticity
    tw_keys = sorted(twii)

    def tw_vol(day):
        ks = [k for k in tw_keys if k <= day][-21:]
        if len(ks) < 15:
            return None
        rets = [twii[b] / twii[a] - 1
                for a, b in zip(ks, ks[1:])]
        return st.pstdev(rets)
    vv = [(tw_vol(r["dts"][r["i0"]]), r) for r in adds]
    vv = [(v_, r) for v_, r in vv if v_ is not None]
    if len(vv) >= 12:
        xs = sorted(v_ for v_, _ in vv)
        t = xs[len(xs) // 2]
        A["Q30_vol_regime_ADD"] = {
            "calm_total_med": med([r["total"] for v_, r in vv
                                   if v_ <= t]),
            "volatile_total_med": med([r["total"]
                                       for v_, r in vv
                                       if v_ > t])}

    # Q31 the client x-table
    xt = {}
    for x in (0, 0.25, 0.5, 0.75, 1.0):
        costs = []
        for r in adds:
            i0, ie = r["i0"], r["ie"]
            days = r["px_close"][i0 + 1:ie]
            if not days:
                continue
            avg = st.mean(days)
            close = r["px_close"][ie]
            costs.append(x * (avg - close) / close)
        xt[f"early_{int(x * 100)}%"] = med(costs)
    A["Q31_client_x_table_ADD"] = {
        **xt,
        "read": "cost vs the close benchmark of executing x "
                "early (evenly day1..E-1) — negative = early "
                "tranche bought BELOW the eventual close"}

    # Q32 the guaranteed-cross fair price
    A["Q32_cross_price_ADD"] = {
        "E-1_to_E_spread_p25": pct([r["eff_day"]
                                    for r in adds], 0.25),
        "med": med([r["eff_day"] for r in adds]),
        "p75": pct([r["eff_day"] for r in adds], 0.75)}

    # Q33 p95 slippage per bucket
    small = [r["eff_day"] for r in adds
             if (r["vol_eff_x"] or 0) > 15]
    large = [r["eff_day"] for r in adds
             if 0 < (r["vol_eff_x"] or 0) <= 15]
    A["Q33_tail_slippage_ADD"] = {
        "high_demand_p95_|eff_day|":
            pct([abs(x) for x in small], 0.95),
        "low_demand_p95_|eff_day|":
            pct([abs(x) for x in large], 0.95)}

    # Q34 stagger or not
    agree = []
    for rev, g in ev.items():
        aa = [r["eff_day"] for r in g["ADD"]
              if r["eff_day"] is not None]
        if len(aa) >= 3:
            pos = sum(1 for x in aa if x > 0)
            agree.append(max(pos, len(aa) - pos) / len(aa))
    A["Q34_same_day_agreement"] = {
        "sign_agreement_med": med(agree),
        "n_events": len(agree),
        "read": "~0.5 = dislocations independent (stagger "
                "helps); ~1 = correlated (stagger illusory)"}

    # ---- BILL'S AUCTION QUESTION (ib_bars 2023+) ---------
    ib = json.loads((ROOT / "data" / "ib_bars.json")
                    .read_text(encoding="utf-8"))
    auc = []
    for r in rows:
        c = r["code"]
        if c not in ib or "5m" not in ib[c]:
            continue
        ed = r["eff"]
        bars = [b for b in ib[c]["5m"]
                if str(b[0]).startswith(ed)]
        if not bars:
            continue
        last_cont = next((b for b in reversed(bars)
                          if b[0].endswith("13:25")), None)
        close_bar = next((b for b in reversed(bars)
                          if b[0].endswith("13:30")), None)
        dayvol = sum(b[3] for b in bars if b[3])
        if last_cont and close_bar and last_cont[2]:
            auc.append({
                "act": r["action"],
                "auction_jump": close_bar[2] / last_cont[2] - 1,
                "auction_vol_share": (close_bar[3] / dayvol
                                      if dayvol else None)})
    A["AUCTION_close_vs_1325"] = {
        "ADD_jump_med": med([x["auction_jump"] for x in auc
                             if x["act"] == "ADD"]),
        "ADD_n": len([x for x in auc if x["act"] == "ADD"]),
        "DEL_jump_med": med([x["auction_jump"] for x in auc
                             if x["act"] == "DEL"]),
        "DEL_n": len([x for x in auc if x["act"] == "DEL"]),
        "auction_vol_share_med": med([x["auction_vol_share"]
                                      for x in auc]),
        "auction_vol_share_p90": pct([x["auction_vol_share"]
                                      for x in auc], 0.9),
        "read": "close print vs the 13:25 last-continuous "
                "price on effective days (IB 5-minute bars, "
                "2023+ events); vol share = the auction's cut "
                "of the day"}

    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(A, indent=1))


if __name__ == "__main__":
    main()
