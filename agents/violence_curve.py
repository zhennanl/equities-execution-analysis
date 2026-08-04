"""The auction VIOLENCE CURVE v1 (session 8z) — factor 5 of the
pitch, fitted on MEASURED per-name event points (China-A May-29
closing calls + Taiwan June TW50 prints; 17 points).

THE v1 FINDING IS A NULL RESULT, STATED: auction SHARE does not
predict gap magnitude (R2 ~ 0.00 on 17 points — the naive
"bigger footprint = bigger print move" hypothesis FAILS). What the
points support instead:
  1. An UNCONDITIONAL banded prior: event-name |gap| ~ 125 +- 85
     bps — that is the number a client should budget, share
     regardless (until n grows).
  2. The CROWDING-VIOLENCE link: the four TW adds — all CONSENSUS
     names with verified pre-event short builds — printed AT OR
     BELOW the last continuous price despite 54-71% auction shares
     (pre-positioned supply sells into the print); the CN adds at
     5-19% shares gapped +194..+239. Sign and size follow
     POSITIONING, not footprint — exactly the discretion matrix's
     premise, now with print-level evidence on one side (TW); the
     CN side's crowding was unmeasured, so the link is SUPPORTED,
     not proven. Each archived event adds points.
Sign convention: gap > 0 = print above last continuous price."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(__file__).resolve().parent.parent / "data" \
    / "auction_study_2026.json"


def load_points(cache: dict | None = None) -> pd.DataFrame:
    """Assemble measured (auction_share, gap_bps, side) points."""
    c = cache if cache is not None else json.loads(CACHE.read_text())
    rows = []
    for label, obj in c.get("cn", {}).items():
        d = obj["days"].get("2026-05-29")
        if not d or d.get("auction_share") is None \
                or d.get("auction_gap_bps") is None:
            continue
        if obj["side"] not in ("Buy", "Sell"):
            continue                       # control excluded from fit
        rows.append({"name": label, "market": "CN",
                     "share": d["auction_share"],
                     "gap_bps": d["auction_gap_bps"],
                     "side": obj["side"]})
    for t, days in c.get("names", {}).items():
        d = days.get("2026-06-18")
        if not d or d.get("auction_share") is None:
            continue
        gap = (d["official_close"] / d["last_bar_close"] - 1) * 1e4
        side = "Buy" if t != "2330.TW" else None   # adds; 2330 excl.
        if side:
            rows.append({"name": t, "market": "TW",
                         "share": d["auction_share"],
                         "gap_bps": gap, "side": side})
    return pd.DataFrame(rows)


def fit(points: pd.DataFrame) -> dict:
    """|gap| = a + b * share, with residual-std band."""
    x = points["share"].to_numpy(float)
    y = points["gap_bps"].abs().to_numpy(float)
    b, a = np.polyfit(x, y, 1)
    pred = a + b * x
    resid = y - pred
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - (resid ** 2).sum() / ss_tot if ss_tot else 0.0
    return {"a": float(a), "b": float(b),
            "resid_std": float(resid.std(ddof=2)),
            "r2": float(r2), "n": int(len(points))}


def expected_gap_bps(share: float, side: str,
                     model: dict) -> dict:
    """Banded expectation for a name whose order/flow is expected to
    be `share` of its closing auction. side signs the point."""
    mag = model["a"] + model["b"] * share
    lo = max(mag - model["resid_std"], 0.0)
    hi = mag + model["resid_std"]
    sgn = 1 if side == "Buy" else -1
    return {"point_bps": round(sgn * mag, 0),
            "band_bps": (round(sgn * lo, 0), round(sgn * hi, 0)),
            "basis": f"violence curve v1, n={model['n']}, "
                     f"R2={model['r2']:.2f} — banded prior, "
                     "not precision"}


def banded_table(model: dict) -> pd.DataFrame:
    rows = []
    for share in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
        e = expected_gap_bps(share, "Buy", model)
        rows.append({"auction_share": f"{share:.0%}",
                     "expected_|gap|_bps": abs(e["point_bps"]),
                     "band_bps": f"{abs(e['band_bps'][0]):.0f}-"
                                 f"{abs(e['band_bps'][1]):.0f}"})
    return pd.DataFrame(rows)
