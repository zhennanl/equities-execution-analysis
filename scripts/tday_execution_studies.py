"""T-day execution studies on the TV harvest — the three builds.

Session 9i. Inputs: data/tv_bars.json (61 codes hourly 2022-2026 +
30 codes 5m 2026), data/auction_shares_derived.json (85 shares),
official STOCK_DAY closes. All three studies mirror a buy-side TCA
dimension (see chat/summary): decomposition = attribution, violence
v2 = estimate accuracy input, THIN/RICH = the real-time read.

1. violence_v2 : |auction gap| vs derived auction share, n~85 —
   the v1 NULL (n=17, R2~0, pinned) re-tested at 5x the data.
   Gap here = official close vs LAST CONTINUOUS close (TV), the
   same definition as v1.
2. decompose   : per name-day cost attribution in favorable bps:
   AM leg (open->12:00) + PM leg (12:00->last continuous) +
   AUCTION leg (last continuous->official close), by class.
3. thin_rich   : for 5m-covered 2026 prints — does the 13:00-13:25
   continuous volume run-rate predict the derived print size?
   (Backtestable proxy of the indicative read; small n, stated.)

Usage: python scripts/tday_execution_studies.py [all|violence|
       decompose|thinrich]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np                                     # noqa: E402
import pandas as pd                                    # noqa: E402

DOC = ROOT / "docs" / "case_studies" / "TDAY_EXECUTION_STUDIES.md"
OUT = ROOT / "data" / "tday_execution_studies.json"


IB_UNIT_CUTOFF = "2024-05-01"   # sanity-verified: bars before this
#                                 are in LOTS (x1000); after, SHARES
#                                 (2024-03-15 = 0.001, 2024-05-31 =
#                                 0.953 vs official)


def _load_ib():
    f = ROOT / "data" / "ib_bars.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def _ib_day(ib, code, day):
    """Normalized IB bars for a day: [[hh:mm, o, c, v_shares]...].
    Returns (continuous_bars, auction_vol, last_cont_close)."""
    raw = [r for r in ib.get(code, {}).get("5m", [])
           if r[0].startswith(day)]
    if not raw:
        return None
    mult = 1000.0 if day < IB_UNIT_CUTOFF else 1.0
    bars = [[r[0][11:16], r[1], r[2], r[3] * mult]
            for r in sorted(raw)]
    # TWSE: 13:30 bar = the closing-auction print (13:25 bar = call
    # window, ~0). TPEx labels the print 13:25. Take the last bar at
    # >= 13:25 as the auction; continuous = bars strictly before.
    auction = sum(v for t, _, _, v in bars if t >= "13:25")
    cont = [b for b in bars if b[0] < "13:25"]
    if not cont:
        return None
    return cont, auction, cont[-1][2]


def _bars(cache, code, day):
    """Best-resolution TV bars for a day: 5m if present else 60m."""
    for k in ("5m", "60m"):
        b = [r for r in (cache.get(code, {}).get(k) or [])
             if r[0].startswith(day)]
        if b:
            return k, sorted(b)
    return None, []


def _official_close(code, day):
    sd = json.loads((ROOT / "data" / "tw_history" /
                     "stock_day.json").read_text(encoding="utf-8"))
    for m in sd.get(code, {}):
        for r in sd[code][m]:
            if r[0] == day:
                return float(r[6])
    return None


def base_table() -> pd.DataFrame:
    """One row per event name-day. Source priority: IB 5m (DIRECT
    auction bar, unit-normalized) > TV 5m > TV 60m (derived shares).
    Events: the full IB event set (bridge events included)."""
    from scripts.ib_harvest import _ib_event_set
    ib = _load_ib()
    cache = json.loads((ROOT / "data" / "tv_bars.json").read_text(encoding="utf-8"))
    try:
        derived = pd.read_json(ROOT / "data" /
                               "auction_shares_derived.json")
        dmap = {(str(r["code"]), r["t_day"]): r["auction_share"]
                for _, r in derived[derived["flag"] == "OK"]
                .iterrows()}
    except Exception:                                  # noqa: BLE001
        dmap = {}
    rows = []
    for event, prov, eff, names in _ib_event_set():
        for code, side in names.items():
            # holiday-shifted prints ("data not calendar" x5 — e.g.
            # Feb-28 is ALWAYS a TW holiday): T = last day <= stated
            # eff with bars
            day = eff
            for back in range(4):
                d_try = (pd.Timestamp(eff) - pd.Timedelta(days=back)
                         ).strftime("%Y-%m-%d")
                if _ib_day(ib, code, d_try) or _bars(cache, code,
                                                     d_try)[1]:
                    day = d_try
                    break
            off = _official_close(code, day)
            sgn = 1.0 if side == "Buy" else -1.0
            ibd = _ib_day(ib, code, day)
            if ibd:
                cont, auc_vol, last_cont = ibd
                cont_vol = sum(r[3] for r in cont)
                if off is None or not cont_vol:
                    continue
                share = auc_vol / (auc_vol + cont_vol) \
                    if auc_vol + cont_vol else None
                src = "5m_ib"
                b = cont
            else:
                src, b = _bars(cache, code, day)
                if not b or off is None:
                    continue
                share = dmap.get((code, day))
                if share is None:
                    continue
                cont_vol = sum(r[3] for r in b)
                last_cont = b[-1][2]
            o_am = b[0][1]
            c12 = next((r[2] for r in reversed(b)
                        if (r[0][11:16] if len(r[0]) > 5 else r[0])
                        <= "12:00"), None)
            if not (o_am and c12 and last_cont):
                continue

            def _hh(r):
                return r[0][11:16] if len(r[0]) > 5 else r[0]
            rows.append({
                "event": event, "provider": prov, "code": code,
                "side": side, "t_day": day, "src": src,
                "auction_share": round(float(share), 3),
                "am_bps": sgn * (c12 / o_am - 1) * 1e4,
                "pm_bps": sgn * (last_cont / c12 - 1) * 1e4,
                "auction_gap_bps": sgn * (off / last_cont - 1) * 1e4,
                "abs_gap_bps": abs(off / last_cont - 1) * 1e4,
                "pm_vol_1300plus": sum(r[3] for r in b
                                       if _hh(r) >= "13:00"),
                "cont_vol": cont_vol})
    return pd.DataFrame(rows)


def violence_v2(df) -> dict:
    from agents.violence_curve import fit
    pts = df.rename(columns={"auction_share": "share",
                             "abs_gap_bps": "gap_bps"})[
        ["share", "gap_bps", "side", "provider"]].copy()
    res = {"n": len(pts)}
    m_all = fit(pts.assign(gap_bps=pts["gap_bps"]))
    res["all"] = {k: round(v, 3) if isinstance(v, float) else v
                  for k, v in m_all.items()}
    for prov, g in pts.groupby("provider"):
        if len(g) >= 10:
            m = fit(g)
            res[prov] = {"n": len(g), "r2": round(m["r2"], 3),
                         "b": round(m["b"], 1)}
    return res


def decompose(df) -> pd.DataFrame:
    return df.groupby(["provider", "side"]).agg(
        n=("code", "count"),
        am=("am_bps", "median"), pm=("pm_bps", "median"),
        auction=("auction_gap_bps", "median"),
        abs_gap=("abs_gap_bps", "median"),
        share=("auction_share", "median")).round(1)


def thin_rich(df) -> dict:
    """5m-covered days only: last-25-min continuous volume run-rate
    (x the day's per-5m average) vs the derived print size (x
    continuous volume). Spearman rank corr; small n stated."""
    g = df[df["src"].isin(("5m", "5m_ib"))].copy()
    if len(g) < 8:
        return {"n": len(g), "verdict": "DATA-GATED"}
    g["late_runrate"] = (g["pm_vol_1300plus"] / 5) / \
        (g["cont_vol"] / (g["cont_vol"] * 0 + 53))    # ~53 bars/day
    g["print_x_cont"] = (g["auction_share"]
                         / (1 - g["auction_share"]).clip(lower=1e-4))
    from scipy.stats import spearmanr
    rho, p = spearmanr(g["late_runrate"], g["print_x_cont"])
    return {"n": int(len(g)), "spearman_rho": round(float(rho), 3),
            "p_value": round(float(p), 4),
            "note": "late continuous run-rate vs relative print "
                    "size; proxy for the indicative read pending "
                    "the real archive (Aug-31)"}


def main():
    df = base_table()
    v2 = violence_v2(df)
    dec = decompose(df)
    tr = thin_rich(df)
    OUT.write_text(json.dumps(
        {"n_rows": len(df), "violence_v2": v2,
         "decompose": json.loads(dec.to_json()),
         "thin_rich": tr}, indent=1, default=str), encoding="utf-8")
    print(f"{len(df)} name-days joined")
    print("\nVIOLENCE V2:", json.dumps(v2))
    print("\nDECOMPOSITION:\n", dec.to_string())
    print("\nTHIN/RICH:", json.dumps(tr))
    L = ["# T-Day Execution Studies — violence v2, decomposition, "
         "THIN/RICH\n",
         f"*Session 9i. {len(df)} name-days (derived shares joined "
         "with TV intraday legs + official closes). Buy-side-TCA "
         "mirror: decomposition = attribution; violence = estimate "
         "accuracy; THIN/RICH = the real-time read. Gap definition "
         "identical to violence v1 (official close vs last "
         "continuous).*\n",
         "## 1. Violence curve v2 (v1 was NULL at n=17, pinned)\n",
         f"```json\n{json.dumps(v2, indent=1)}\n```\n",
         "## 2. Execution decomposition (favorable bps, medians)\n",
         dec.to_markdown(), "",
         "## 3. THIN/RICH proxy (5m days only)\n",
         f"```json\n{json.dumps(tr, indent=1)}\n```\n",
         "## Per-name table\n",
         df.round(1).to_markdown(index=False)]
    DOC.write_text("\n".join(L), encoding="utf-8")
    print("wrote", DOC)


if __name__ == "__main__":
    main()
