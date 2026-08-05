"""Step-2 liquidity-supply forecast — who will supply the close?
(session 9i c-36)

THE PT QUESTION: on the effective date the passive complex MUST
trade ~prior x ADV at the close. Who supplies it? Mostly arbitrageurs
who pre-positioned during the ann->eff window and unwind INTO the
print. So the supply forecast is an INVENTORY-ACCUMULATION
measurement problem, fully observable PIT:

  crowding_ratio = accumulated pre-positioning / expected passive flow

Observables per name (all daily, all free, all PIT at T-1):
  1. FLOW COMPLETION  cum abnormal volume since announcement /
     expected flow (expected = class-prior T-mult x baseline ADV)
  2. BORROW BUILD     SBL balance delta (deletes: arbs short the
     window, buy back at the print) — event_data_cache TWT93U
  3. FOREIGN FLOW     foreign-holding pp delta x shares (arbs and
     HFs run foreign books in TW) — FinMind Shareholding
  4. RETAIL SHORTS    margin short-sale balance delta — FinMind

Scenario map (advice is the deliverable, not the point forecast):
  UNDERSUPPLIED  ratio < 0.3   thin close, client flow moves the
                               print: start early (must-start-by),
                               spread across window + close, expect
                               a large toll if demanding at T
  BUILDING       0.3 - 0.7     normal accumulation: standard MOC
                               participation, monitor daily
  WELL-SUPPLIED  0.7 - 1.2     liquidity ample: lean on the close,
                               minimal pre-hedge
  OVERCROWDED    > 1.2         inventory EXCEEDS passive demand
                               (the Apple case): print may land
                               AGAINST the obligated side, T+1
                               reversal likely — cap MOC exposure,
                               split pre-close/next-day, consider
                               fading the print

Class priors (PIT-legal for May-26: measured on PRE-May events):
deletes ~16x ADV, adds ~8x ADV.
"""
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.finmindtrade.com/api/v4/data"
EXPECTED_TMULT = {"del": 16.0, "add": 8.0}
SCEN = [(0.3, "UNDERSUPPLIED"), (0.7, "BUILDING"),
        (1.2, "WELL-SUPPLIED"), (9e9, "OVERCROWDED")]
ADVICE = {
    "UNDERSUPPLIED": "Thin close coming — your flow WILL move the "
        "print. Start accumulating early in the window, spread "
        "across days + the close; demanding size at T pays a large "
        "toll.",
    "BUILDING": "Normal accumulation pace. Standard MOC "
        "participation; monitor the daily build for regime change.",
    "WELL-SUPPLIED": "Arb inventory near passive demand — lean on "
        "the close, minimal pre-hedging needed; the print should "
        "clear near fair.",
    "OVERCROWDED": "Pre-positioned inventory EXCEEDS passive "
        "demand (the Apple-2024 case): the print can land AGAINST "
        "the obligated side with next-day reversal. Cap MOC "
        "exposure, split pre-close/T+1, consider fading the print.",
}


def _series(code):
    import pandas as pd
    c = json.loads((ROOT / "data" / "tw_vintage_cache.json")
                   .read_text())
    px = pd.DataFrame(c[f"px|{code}"]).set_index("date")
    sh = pd.DataFrame(c[f"sh|{code}"]).set_index("date")
    return px, sh


def _margin_short(code, start, end):
    import requests
    try:
        rows = requests.get(API, params={
            "dataset": "TaiwanStockMarginPurchaseShortSale",
            "data_id": code, "start_date": start, "end_date": end},
            timeout=30).json().get("data", [])
        time.sleep(0.8)
        return rows
    except Exception:                          # noqa: BLE001
        return []


def name_forecast(code, side, ann, asof, shares_hint=None):
    """PIT liquidity-supply read for one name at `asof` (<= T-1)."""
    import pandas as pd
    px, sh = _series(code)
    px, sh = px[px.index <= asof], sh[sh.index <= asof]
    pre = px[px.index < ann]
    base_adv = float(pre["Trading_Volume"].tail(60).median())
    exp_flow = EXPECTED_TMULT[side] * base_adv
    win = px[px.index >= ann]
    cum_abn = float((win["Trading_Volume"] - base_adv).clip(
        lower=0).sum())
    completion = cum_abn / exp_flow if exp_flow else None
    # foreign
    shw = sh[sh.index >= ann]
    f_pp = (float(shw["ForeignInvestmentSharesRatio"].iloc[-1]
                  - shw["ForeignInvestmentSharesRatio"].iloc[0])
            if len(shw) > 1 else 0.0)
    n_sh = float(sh["NumberOfSharesIssued"].iloc[-1])
    f_flow = abs(f_pp) / 100 * n_sh / exp_flow if exp_flow else None
    f_dir_ok = (f_pp < 0) if side == "del" else (f_pp > 0)
    # SBL borrow build (institutional shorts — deletes' channel)
    sbl = json.loads((ROOT / "data" / "event_data_cache.json")
                     .read_text())["short"]
    days = sorted(d for d in sbl
                  if ann.replace("-", "") <= d
                  <= asof.replace("-", ""))
    bal = [sbl[d][code][1] for d in days
           if sbl.get(d, {}).get(code)]
    sbl_build = ((bal[-1] - bal[0]) / exp_flow
                 if len(bal) >= 2 and exp_flow else None)
    # retail margin shorts
    ms = _margin_short(code, ann, asof)
    ms_build = ((ms[-1]["ShortSaleTodayBalance"]
                 - ms[0]["ShortSaleTodayBalance"]) * 1000 / exp_flow
                if len(ms) >= 2 and exp_flow else None)
    # crowding = volume completion, corroborated by positioning legs
    ratio = completion
    scen = next(s for lim, s in SCEN if ratio < lim)
    return {"code": code, "side": side, "asof": asof,
            "baseline_adv_sh": int(base_adv),
            "expected_flow_x_adv": EXPECTED_TMULT[side],
            "flow_completion": round(completion, 2),
            "foreign_pp_since_ann": round(f_pp, 2),
            "foreign_leg_x_expflow": round(f_flow, 2)
            if f_flow is not None else None,
            "foreign_direction_consistent": bool(f_dir_ok),
            "sbl_build_x_expflow": round(sbl_build, 2)
            if sbl_build is not None else None,
            "retail_short_x_expflow": round(ms_build, 3)
            if ms_build is not None else None,
            "scenario": scen, "advice": ADVICE[scen]}


def realized(code, eff):
    """Post-hoc check (NOT part of the PIT frame): actual T-day
    volume multiple + T+3 close-to-close move."""
    import pandas as pd
    px, _ = _series(code)
    pre = px[px.index < eff]
    base = float(pre["Trading_Volume"].tail(80).head(60).median())
    if eff not in px.index:
        eff = px.index[px.index >= eff][0] if \
            len(px.index[px.index >= eff]) else None
        if eff is None:
            return None
    t_mult = float(px.loc[eff, "Trading_Volume"]) / base
    after = px[px.index > eff]
    rev = (float(after["close"].iloc[min(2, len(after) - 1)]
                 / px.loc[eff, "close"] - 1) * 100
           if len(after) else None)
    return {"t_mult": round(t_mult, 1),
            "t3_move_pct": round(rev, 1) if rev is not None
            else None}
