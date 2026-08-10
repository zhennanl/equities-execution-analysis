"""The STRATEGIST study (c-133) — context conditioning for the
rebalance window, built to answer the client call:

  "Reviews are announced. How should we trade these names on
   the effective date? What flows are you seeing?"

THE QUESTIONS (self-generated, per Bill's brief — each one is
something the desk must have AN ANSWER TO before picking up
that call):

  S1  MARKET REGIME: does the add drift survive a risk-off
      tape? (window TAIEX return terciles x outcomes — the
      "maybe nobody buys adds in a selloff" hypothesis)
  S2  SECTOR: do tech adds behave like financial adds? (TWSE
      industry codes, grouped)
  S3  SECTOR TIDE: is our stock's foreign buying just its
      sector's tide, or name-specific? (stock's flow z-score
      MINUS its sector peers' median z, from t86 which covers
      every listed name daily)
  S4  MARKET-WIDE FOREIGN APPETITE: do adds drift more when
      foreigners are net buyers of Taiwan overall that month?
      (aggregate t86 across all names)
  S5  CASE CARDS: the 3 best / 3 worst add windows and the
      crowded-short deletion bounces, WITH their context —
      the "lessons from the past" a client actually remembers.

DATA: everything local except ^TWII (one Yahoo chart call,
cached to data/twii_daily.json) and the industry map (one TWSE
call, cached). t86 gives sector tides AND market appetite with
no further API — it carries every stock, every day.

REPLICATION NOTE for other markets (the procedure): (1) a
market index series — Yahoo ^N225/^KS11/^NSEI etc., one call;
(2) an industry map — every exchange's company file has one;
(3) a market-wide daily flow series — KR: KRX investor-type
file; IN: FPI daily; TH: NVDR aggregate; AU: ASIC total
shorts. Same conditioning code after that.

Usage:  py scripts\\strategist_study.py
Output: data/strategist_tw.json + console
"""
import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "strategist_tw.json"

SECTOR_GROUP = {
    "24": "TECH", "25": "TECH", "26": "TECH", "27": "TECH",
    "28": "TECH", "29": "TECH", "30": "TECH", "31": "TECH",
    "05": "TECH",
    "17": "FINANCIAL",
    "15": "SHIPPING",
    "22": "HEALTHCARE",
    "01": "TRADITIONAL", "02": "TRADITIONAL",
    "03": "TRADITIONAL", "04": "TRADITIONAL",
    "09": "TRADITIONAL", "10": "TRADITIONAL",
    "11": "TRADITIONAL", "12": "TRADITIONAL",
    "14": "TRADITIONAL", "21": "TRADITIONAL",
    "23": "TRADITIONAL"}


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(st.median(xs), 4) if xs else None


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
    twii = json.loads((ROOT / "data" / "twii_daily.json")
                      .read_text(encoding="utf-8"))
    ind = json.loads((ROOT / "data" / "tw_industry_map.json")
                     .read_text(encoding="utf-8"))

    # pre-index: per-day sector membership of t86 + market agg
    day_codes = {}                     # cache per needed day

    def mkt_ret(a, b):
        ka = max((k for k in twii if k <= a), default=None)
        kb = max((k for k in twii if k <= b), default=None)
        return (twii[kb] / twii[ka] - 1) if ka and kb and \
            ka != kb else None

    def sector_of(c):
        return SECTOR_GROUP.get(ind.get(c, ""), "OTHER")

    def flow_z(code, days):
        """window-mean foreign net / its own trailing |median|
        (self-normalized -> comparable across sizes)."""
        pre, win = [], []
        for k in days["pre"]:
            f = (t86.get(k, {}).get(code) or {}).get("f")
            if f is not None:
                pre.append(abs(f))
        for k in days["win"]:
            f = (t86.get(k, {}).get(code) or {}).get("f")
            if f is not None:
                win.append(f)
        base = st.median(pre) if pre else None
        return (st.median(win) / base
                if win and base else None)

    rows = []
    for v in W.values():
        px = v["px"]
        if len(px) < 12:
            continue
        dts = [r["d"] for r in px]
        close = [r["c"] for r in px]
        i0 = max((i for i, d in enumerate(dts)
                  if d <= v["ann"]), default=None)
        ie = max((i for i, d in enumerate(dts)
                  if d <= v["eff"]), default=None)
        if i0 is None or ie is None or ie <= i0 + 2 \
                or len(px) < ie + 2:
            continue
        r = {"rev": v["rev"], "code": v["code"],
             "name": v["name"], "action": v["action"],
             "year": int(v["ann"][:4]),
             "sector": sector_of(v["code"]),
             "drift": close[ie - 1] / close[min(i0 + 1,
                                               ie - 1)] - 1,
             "eff_day": close[ie] / close[ie - 1] - 1,
             "revert5": close[min(ie + 5, len(close) - 1)]
             / close[ie] - 1,
             "total": close[ie - 1] / close[i0] - 1,
             "mkt_window": mkt_ret(dts[i0], dts[ie - 1])}
        r["excess_total"] = (r["total"] - r["mkt_window"]
                             if r["mkt_window"] is not None
                             else None)
        if r["year"] >= 2015:
            days = {"pre": [d.replace("-", "") for d in
                            dts[max(0, i0 - 20):i0]],
                    "win": [d.replace("-", "") for d in
                            dts[i0 + 1:ie]]}
            r["flow_z"] = flow_z(v["code"], days)
            # sector tide: median flow_z of sector peers
            # (peers = all t86 names in the sector, sampled
            # via the same days)
            k0 = days["win"][0] if days["win"] else None
            if k0 and k0 in t86:
                if k0 not in day_codes:
                    day_codes[k0] = list(t86[k0])
                peers = [c for c in day_codes[k0]
                         if sector_of(c) == r["sector"]
                         and c != v["code"]][:80]
                pz = [flow_z(c, days) for c in peers[:40]]
                r["sector_tide"] = med(pz)
                r["excess_flow"] = (r["flow_z"]
                                    - r["sector_tide"]
                                    if r["flow_z"] is not None
                                    and r["sector_tide"]
                                    is not None else None)
            # market-wide foreign appetite over the window
            agg = []
            for k in days["win"][:10]:
                fs = [x.get("f") for x in t86.get(k, {})
                      .values() if x.get("f") is not None]
                if fs:
                    agg.append(sum(fs))
            r["mkt_foreign_net"] = (st.median(agg)
                                    if agg else None)
        rows.append(r)

    adds = [r for r in rows if r["action"] == "ADD"]
    out = {"n": len(rows), "n_adds": len(adds)}

    # ---- S1 market regime --------------------------------
    mk = sorted(r["mkt_window"] for r in adds
                if r["mkt_window"] is not None)
    if len(mk) >= 9:
        t1, t2 = mk[len(mk) // 3], mk[2 * len(mk) // 3]
        out["S1_market_regime_ADD"] = {
            "cutoffs": [round(t1, 4), round(t2, 4)]}
        for name, cond in (
                ("risk_off", lambda r: r["mkt_window"] <= t1),
                ("neutral", lambda r: t1 < r["mkt_window"]
                 <= t2),
                ("risk_on", lambda r: r["mkt_window"] > t2)):
            g = [r for r in adds if r["mkt_window"] is not None
                 and cond(r)]
            out["S1_market_regime_ADD"][name] = {
                "n": len(g),
                "raw_total_med": med([x["total"] for x in g]),
                "EXCESS_total_med": med([x["excess_total"]
                                         for x in g]),
                "eff_day_med": med([x["eff_day"] for x in g]),
                "revert5_med": med([x["revert5"]
                                    for x in g])}

    # ---- S2 sector ---------------------------------------
    out["S2_sector_ADD"] = {}
    for s in ("TECH", "FINANCIAL", "SHIPPING", "TRADITIONAL",
              "HEALTHCARE", "OTHER"):
        g = [r for r in adds if r["sector"] == s]
        if len(g) >= 3:
            out["S2_sector_ADD"][s] = {
                "n": len(g),
                "total_med": med([x["total"] for x in g]),
                "excess_med": med([x["excess_total"]
                                   for x in g]),
                "revert5_med": med([x["revert5"]
                                    for x in g])}

    # ---- S3 sector-relative flow -------------------------
    fl = [r for r in adds if r.get("excess_flow") is not None]
    if len(fl) >= 9:
        xs = sorted(r["excess_flow"] for r in fl)
        t1, t2 = xs[len(xs) // 3], xs[2 * len(xs) // 3]
        lo = [r for r in fl if r["excess_flow"] <= t1]
        hi = [r for r in fl if r["excess_flow"] > t2]
        out["S3_excess_vs_sector_ADD"] = {
            "question": "is the name's foreign flow above its "
                        "own sector's tide?",
            "cutoffs": [round(t1, 3), round(t2, 3)],
            "below_sector": {"n": len(lo),
                             "total_med": med([x["total"]
                                               for x in lo]),
                             "revert5_med": med([x["revert5"]
                                                 for x in lo])},
            "above_sector": {"n": len(hi),
                             "total_med": med([x["total"]
                                               for x in hi]),
                             "revert5_med": med([x["revert5"]
                                                 for x in hi])}}

    # ---- S4 market foreign appetite ----------------------
    fa = [r for r in adds
          if r.get("mkt_foreign_net") is not None]
    if len(fa) >= 9:
        xs = sorted(r["mkt_foreign_net"] for r in fa)
        t1, t2 = xs[len(xs) // 3], xs[2 * len(xs) // 3]
        out["S4_market_foreign_appetite_ADD"] = {
            "foreign_selling_TW": {
                "n": len([r for r in fa
                          if r["mkt_foreign_net"] <= t1]),
                "total_med": med([r["total"] for r in fa
                                  if r["mkt_foreign_net"]
                                  <= t1])},
            "foreign_buying_TW": {
                "n": len([r for r in fa
                          if r["mkt_foreign_net"] > t2]),
                "total_med": med([r["total"] for r in fa
                                  if r["mkt_foreign_net"]
                                  > t2])}}

    # ---- S5 case cards -----------------------------------
    scored = [r for r in adds if r["total"] is not None]
    best = sorted(scored, key=lambda r: -r["total"])[:3]
    worst = sorted(scored, key=lambda r: r["total"])[:3]

    def card(r):
        return {k: (round(v, 4) if isinstance(v, float) else v)
                for k, v in r.items()}
    out["S5_case_cards"] = {"best_adds": [card(r)
                                          for r in best],
                            "worst_adds": [card(r)
                                           for r in worst]}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items()
                      if k != "S5_case_cards"}, indent=1))
    print("\nCASE CARDS (best adds):")
    for r in best:
        print(f"  {r['rev']} {r['code']} {r['name'][:20]:20} "
              f"{r['sector']:11} total {r['total']:+.1%} "
              f"mkt {r['mkt_window'] if r['mkt_window'] is None else round(r['mkt_window'],3)}")
    print("CASE CARDS (worst adds):")
    for r in worst:
        print(f"  {r['rev']} {r['code']} {r['name'][:20]:20} "
              f"{r['sector']:11} total {r['total']:+.1%} "
              f"mkt {r['mkt_window'] if r['mkt_window'] is None else round(r['mkt_window'],3)}")


if __name__ == "__main__":
    main()
