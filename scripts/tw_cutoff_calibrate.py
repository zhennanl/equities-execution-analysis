"""Calibrate the §2.3.3 cutoff on the full TW universe (c-120).

Uses data/tw_universe_pit.json (exchange bulk feeds) to run the
rulebook's own procedure and score it against MSCI's published
answer for the May-2026 review:

  ANCHORS (Jul-31-2026 Taiwan factsheet + the May-26 result)
    - 77 constituents  -> the Segment Number of Companies
    - smallest surviving constituent full cap $5.19B (Apr-20)
      -> the Market Size-Segment Cutoff
    - index float-adj cap $3,183.0B, which is ~85% of the
      universe -> universe float ~$3,745B
    - top-10 float caps -> factsheet-IMPLIED FIFs

The implied-FIF check is the reason to trust the rest: summing
the ten published float caps must reproduce the factsheet's own
total ($2,443.20B) from OUR full caps, which it does exactly.
That validates price x shares / FX before any float judgement
enters.

Usage: py scripts\\tw_cutoff_calibrate.py
"""
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
U = ROOT / "data" / "tw_universe_pit.json"
OUT = ROOT / "data" / "tw_cutoff_calibration.json"

# MSCI Taiwan factsheet, Jul 31 2026 — top 10 float-adj caps
FACTSHEET_TOP10 = {
    "2330": 1848.51, "2454": 158.78, "2308": 98.86,
    "2317": 94.71, "3711": 57.28, "2303": 42.38,
    "2383": 42.09, "2881": 33.81, "2891": 33.59,
    "2345": 33.20}
FACTSHEET_TOP10_TOTAL = 2443.20
FACTSHEET_INDEX_FFCAP = 3183.008
FACTSHEET_N = 77
EU_MIN = 0.537          # §2.2.3, May-26 value, USD billions
PRICE_DATE_MAY26 = "20260420"
FACTSHEET_DATE = "20260731"


def implied_fifs(u):
    """Bill's method: MSCI's published float cap / our full cap."""
    R = u["dates"][FACTSHEET_DATE]["rows"]
    out, chk = {}, 0.0
    for c, f in FACTSHEET_TOP10.items():
        if c in R and R[c].get("cap_usd_b"):
            out[c] = f / R[c]["cap_usd_b"]
            chk += f
    return out, chk


def crossing(rows, ff, coverage=0.85):
    """§2.3.3: sort by FULL cap desc, cumulate FLOAT-adj cap,
    the company at `coverage` defines the cutoff and its rank
    is the Segment Number of Companies."""
    scr = {c: r for c, r in rows.items()
           if r.get("cap_usd_b", 0) >= EU_MIN
           and r["cap_usd_b"] * ff(c, r) >= 0.5 * EU_MIN}
    srt = sorted(scr.items(), key=lambda x: -x[1]["cap_usd_b"])
    tot = sum(r["cap_usd_b"] * ff(c, r) for c, r in srt)
    run = 0.0
    for i, (c, r) in enumerate(srt, 1):
        run += r["cap_usd_b"] * ff(c, r)
        if run >= coverage * tot:
            return {"universe_n": len(srt), "rank": i,
                    "cutoff_usd_b": round(r["cap_usd_b"], 3),
                    "universe_float_usd_b": round(tot, 1),
                    "code_at_cutoff": c}
    return {"universe_n": len(srt), "rank": len(srt),
            "cutoff_usd_b": srt[-1][1]["cap_usd_b"],
            "universe_float_usd_b": round(tot, 1),
            "code_at_cutoff": srt[-1][0]}


def main():
    u = json.loads(U.read_text(encoding="utf-8"))
    imp, chk = implied_fifs(u)
    R = {c: r for c, r in u["dates"][PRICE_DATE_MAY26]["rows"].items()
         if r.get("ffcap_usd_b")}
    err = [(R[c]["ff"] - imp[c]) / imp[c] for c in imp if c in R]
    scen = {
        "A_tdcc_proxy": lambda c, r: r["ff"],
        "B_factsheet_top10": lambda c, r: imp.get(c, r["ff"]),
        "C_tail_flat_0.55": lambda c, r: imp.get(c, 0.55),
        "D_tail_flat_0.75": lambda c, r: imp.get(c, 0.75),
        "E_tail_flat_0.85": lambda c, r: imp.get(c, 0.85),
    }
    res = {k: crossing(R, f) for k, f in scen.items()}
    out = {
        "price_date": PRICE_DATE_MAY26,
        "implied_fif_check": {
            "sum_top10_float_usd_b": round(chk, 2),
            "factsheet_total": FACTSHEET_TOP10_TOTAL,
            "matches": abs(chk - FACTSHEET_TOP10_TOTAL) < 0.05,
            "note": "identity check on the inputs — if our full "
                    "caps and FX were wrong this would not tie"},
        "implied_fifs": {c: round(v, 3) for c, v in imp.items()},
        "tdcc_proxy_error_vs_implied": {
            "median": round(st.median(err), 3),
            "mean": round(st.mean(err), 3),
            "worst": sorted(
                ((c, round((R[c]["ff"] - imp[c]) / imp[c], 2))
                 for c in imp if c in R),
                key=lambda x: -abs(x[1]))[:4]},
        "targets": {"segment_number_of_companies": FACTSHEET_N,
                    "cutoff_usd_b": 5.19,
                    "universe_float_usd_b": round(
                        FACTSHEET_INDEX_FFCAP / 0.85, 0)},
        "scenarios": res}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("IMPLIED-FIF IDENTITY CHECK: our top-10 float sums to "
          f"${chk:,.2f}B vs factsheet ${FACTSHEET_TOP10_TOTAL:,.2f}B"
          f"  -> {'TIES' if out['implied_fif_check']['matches'] else 'MISMATCH'}")
    print(f"\nTDCC proxy vs MSCI-implied FIF: median "
          f"{st.median(err):+.0%}, worst "
          f"{out['tdcc_proxy_error_vs_implied']['worst']}")
    print(f"\nTARGET: rank {FACTSHEET_N}, cutoff $5.19B, "
          f"universe float ~${FACTSHEET_INDEX_FFCAP / 0.85:,.0f}B")
    for k, v in res.items():
        print(f"  {k:22} universe {v['universe_n']:4d} | rank "
              f"{v['rank']:3d} | cutoff ${v['cutoff_usd_b']:6.2f}B"
              f" | float ${v['universe_float_usd_b']:,.0f}B")
    print(f"\n-> {OUT.name}")
    return out


if __name__ == "__main__":
    main()
