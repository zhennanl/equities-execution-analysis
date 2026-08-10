"""EWT-holdings FIF vs weights-inversion FIF (c-141).

Bill's question: how different are FIFs recovered from an
index-tracking FUND's holdings vs from MSCI's own weights?

METHOD (QA Q77): for a replicating fund,
    shares_held_i / shares_outstanding_i
      = (TNA / IndexFloatCap) x FIF_i  =  c x FIF_i
so FIF_ewt_i = (Quantity_i / S_i) / c, with the constant c
calibrated as the median of (Quantity_i/S_i)/FIF_weights_i
over CLEAN names only.

TWO KNOWN DISTORTIONS, flagged not hidden:
  - CAP-DISTORTED: EWT tracks MSCI Taiwan 25/50 (IRS caps).
    Names with plain-index weight > 5% can be capped or
    rescaled non-proportionally -> excluded from calibration
    and flagged in the table.
  - Sampling/lending noise: EWT is allowed representative
    sampling; small names may be over/under-held.

Inputs: data/ewt_holdings_raw.csv (iShares latest-holdings
        endpoint, found via the page DOM: /us/products/
        239686/ishares-msci-taiwan-etf/latest-holdings.csv),
        tw_member_fifs_weights.json (77/77, c-140),
        tw_universe_pit.json 20260731 shares.
Run:  py scripts\\ewt_fif_compare.py
Out:  data/ewt_fif_compare.json + reports/ewt_fif_compare.csv
"""
import csv
import io
import json
import statistics as stx
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAP_COHORT_PCT = 5.0        # plain-index weight above which
#                             25/50 distortion is possible


def _num(s):
    try:
        return float(str(s).replace(",", ""))
    except ValueError:
        return None


def parse_holdings():
    raw = (ROOT / "data" / "ewt_holdings_raw.csv") \
        .read_text(encoding="utf-8-sig")
    # header block ends at the 'Ticker,Name,...' line
    i = raw.index("Ticker,")
    asof = raw.split('Fund Holdings as of,"')[1] \
        .split('"')[0] if "Fund Holdings as of" in raw \
        else "?"
    rows = {}
    for r in csv.DictReader(io.StringIO(raw[i:])):
        code = str(r.get("Ticker", "")).strip().strip('"')
        q = _num(r.get("Quantity"))
        if code.isdigit() and q:
            rows[code] = q
    return asof, rows


def build():
    asof, held = parse_holdings()
    w = json.loads((ROOT / "data" /
                    "tw_member_fifs_weights.json")
                   .read_text(encoding="utf-8"))
    uni = json.loads((ROOT / "data" / "tw_universe_pit.json")
                     .read_text(encoding="utf-8"))["dates"]["20260731"]["rows"]
    recs = []
    for r in w["rows"]:
        c = r["code"]
        S = (uni.get(c) or {}).get("shares")
        q = held.get(c)
        recs.append({
            "code": c, "name": r["name"],
            "weight_plain_pct": r["weight_pct"],
            "fif_weights": r["fif_weights"],
            "hold_ratio": (q / S if q and S else None),
            "in_ewt": q is not None,
            "cap_cohort": r["weight_pct"] > CAP_COHORT_PCT})
    # calibrate c on clean names only
    clean = [x["hold_ratio"] / x["fif_weights"] for x in recs
             if x["hold_ratio"] and not x["cap_cohort"]]
    c0 = stx.median(clean)
    for x in recs:
        x["fif_ewt"] = (round(x["hold_ratio"] / c0, 3)
                        if x["hold_ratio"] else None)
        x["diff_pp"] = (round(
            100 * (x["fif_ewt"] - x["fif_weights"]), 1)
            if x["fif_ewt"] else None)
        del x["hold_ratio"]
    diffs = [abs(x["diff_pp"]) for x in recs
             if x["diff_pp"] is not None
             and not x["cap_cohort"]]
    summary = {
        "ewt_asof": asof, "calib_c": round(c0, 6),
        "n_members": len(recs),
        "n_in_ewt": sum(1 for x in recs if x["in_ewt"]),
        "n_missing_from_ewt": [x["code"] for x in recs
                               if not x["in_ewt"]],
        "clean_median_abs_diff_pp": round(
            stx.median(diffs), 2) if diffs else None,
        "clean_p90_abs_diff_pp": round(sorted(diffs)[
            int(0.9 * len(diffs))], 2) if diffs else None,
        "within_2.5pp_one_grid_step": round(
            sum(1 for d in diffs if d <= 2.5) / len(diffs),
            3) if diffs else None}
    out = {"summary": summary, "rows": recs}
    (ROOT / "data" / "ewt_fif_compare.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    rep = ROOT / "reports"
    rep.mkdir(exist_ok=True)
    with open(rep / "ewt_fif_compare.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        wcsv = csv.DictWriter(f, fieldnames=list(recs[0]))
        wcsv.writeheader()
        wcsv.writerows(recs)
    print(json.dumps(summary, indent=1))
    print("\nworst clean-name gaps:")
    for x in sorted((x for x in recs
                     if x["diff_pp"] is not None
                     and not x["cap_cohort"]),
                    key=lambda x: -abs(x["diff_pp"]))[:8]:
        print(f"  {x['code']} {x['name'][:24]:24} "
              f"w-inv {x['fif_weights']:.3f} vs EWT "
              f"{x['fif_ewt']:.3f} ({x['diff_pp']:+.1f}pp)")
    print("\ncap cohort (25/50-distorted, EXCLUDED from "
          "calibration):")
    for x in (x for x in recs if x["cap_cohort"]):
        print(f"  {x['code']} {x['name'][:24]:24} "
              f"w-inv {x['fif_weights']:.3f} vs EWT "
              f"{x['fif_ewt']} ({x['diff_pp']}pp)")


if __name__ == "__main__":
    build()
