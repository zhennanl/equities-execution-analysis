"""MSCI Taiwan, August 2026 — the mechanical call (c-273).

    py scripts\\aug26_predict.py

Bill: *"generate our prediction solely based on our cutoff point
and addition deletion floor."*

So this applies two thresholds to a universe and writes down
what falls out. No judgement, no conviction weighting, no
priority queue, no hand-picked names. If a name clears the bar
it is an addition; if a member falls under the floor it is a
deletion; everything else is silent.

THE THRESHOLDS, and where each comes from:

    Market Size-Segment Cutoff   $7.22B
        MSCI's own factsheet gives the index's free-float value
        at $3,183.01B on 31 Jul 2026 and states the index covers
        85% of Taiwan's investable market. $3,183.01 / 0.85 =
        $3,744.7B for that market. Ranking Taiwan's companies by
        size and accumulating free-float value, 85% of $3,744.7B
        is reached at the 69th company, whose full market value
        is $7.22B.

    Addition bar    1.5 x cutoff = $10.83B   §3.1.5.1
    Deletion floor  2/3 x cutoff = $4.81B    §3.1.5.1
    Minimum float   0.5 x cutoff = $3.61B    §2.3.6.1  (adds only)

WHAT THIS DELIBERATELY DOES NOT MODEL, because the evidence for
it is not there:

  - Any balancing of additions against deletions. Checked
    against eleven years: Taiwan's additions equal its deletions
    in only 14 of 34 reviews, and the index shrank from ~97
    names to 77 over the period. China's grew by 568 net. Member
    count is an OUTPUT of the thresholds, not a constraint on
    them.
  - Deletions for reasons other than size — liquidity failures,
    foreign-room breaches, mergers, delistings. Those are real
    and this file cannot see them, so the deletion list here is
    a FLOOR on the deletions, never a complete one.

KNOWN TENSION, stated rather than smoothed over. At a $7.22B
cutoff the floor is $4.81B and almost nothing breaches it, yet
Taiwan has deleted at least one name in every review since 2015
and averages 2.3. Either the cutoff is too low, our full-cap
estimates are too high, or most deletions are not size-driven.
The band column exists so that this is visible in the output
rather than resolved by assertion: every verdict is also run at
$5.89B and $8.79B, the edges implied by the factsheet's
"approximately 85%".
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "data" / "aug26_prediction.json"

CUTOFF = 7.22
BAND = (5.89, 8.79)          # 86% and 83% assumed coverage
ADD_MULT, DEL_MULT, FLOAT_MULT = 1.5, 2.0 / 3.0, 0.5


def members():
    """Constituents going INTO the August review."""
    import pandas as pd
    import review_reconstruct as RR
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    g = df[(df.market == "Taiwan") & (df.code != "")]
    order = [f"{m}{y % 100:02d}" for y in range(2015, 2027)
             for m in ("Feb", "May", "Aug", "Nov")]
    return {str(c) for c in RR.pit_members("Aug26", order, g)}


def main():
    uni = json.loads((ROOT / "data" / "tw_mieu_universe.json")
                     .read_text(encoding="utf-8"))
    U, mem = uni["universe"], members()
    bar, floor = CUTOFF * ADD_MULT, CUTOFF * DEL_MULT
    minfl = CUTOFF * FLOAT_MULT

    def verdict(code, v, cut):
        b, f, mf = cut * ADD_MULT, cut * DEL_MULT, cut * FLOAT_MULT
        if code in mem:
            return "DELETE" if v["cap"] <= f else "HOLD"
        return ("ADD" if v["cap"] >= b and v["fcap"] >= mf
                else "OUT")

    adds, dels = [], []
    for code, v in U.items():
        core = verdict(code, v, CUTOFF)
        if core not in ("ADD", "DELETE"):
            continue
        edges = [verdict(code, v, c) for c in BAND]
        row = {"code": code, "action": core,
               "full_cap_usd_b": round(v["cap"], 2),
               "float_cap_usd_b": round(v["fcap"], 2),
               "float_factor": round(v["ff"], 4),
               "float_source": v["src"], "board": v["mkt"],
               "robust_across_band": all(e == core for e in edges),
               "verdict_at_band_edges": edges}
        (adds if core == "ADD" else dels).append(row)
    adds.sort(key=lambda r: -r["full_cap_usd_b"])
    dels.sort(key=lambda r: r["full_cap_usd_b"])

    out = {
        "market": "Taiwan", "review": "Aug-2026",
        "generated": "2026-08-09",
        "announcement": "2026-08-12", "rebalance_close": "2026-08-31",
        "method": ("mechanical: two thresholds applied to the "
                   "screened universe. No count balancing, no "
                   "conviction weighting, no discretion."),
        "thresholds_usd_b": {
            "market_size_segment_cutoff": CUTOFF,
            "addition_bar_1.5x": round(bar, 2),
            "deletion_floor_2_3x": round(floor, 2),
            "minimum_float_cap_0.5x": round(minfl, 2),
            "band": list(BAND),
            "band_meaning": ("cutoff at 86% and 83% assumed "
                             "coverage; the factsheet says "
                             "'approximately 85%'"),
        },
        "cutoff_derivation": {
            "factsheet_index_float_usd_b": 3183.00839,
            "factsheet_asof": "2026-07-31",
            "stated_coverage": 0.85,
            "implied_investable_market_usd_b": 3744.7,
            "crossing_rank": 69,
            "source": ("MSCI Taiwan Index (USD) factsheet, "
                       "31 Jul 2026"),
        },
        "universe": {
            "screened_names": len(U),
            "priced_asof": uni["date"], "fx": uni["fx"],
            "members_entering_review": len(mem),
            "factsheet_constituents": 77,
        },
        "additions": adds,
        "deletions": dels,
        "limits": [
            "Deletions for liquidity, foreign room, mergers or "
            "delistings are invisible here. This deletion list "
            "is a floor, not a complete one.",
            "Taiwan has deleted at least one name in every "
            "review since 2015 (mean 2.3). A prediction of "
            f"{len(dels)} size-driven deletion(s) is below that "
            "run rate and should be read as evidence about the "
            "cutoff, not as a forecast of a quiet review.",
            "Additions equal deletions in only 14 of 34 Taiwan "
            "reviews; no count balancing is applied.",
            "Float factors are Yahoo-sourced for most names; "
            "only the index top-10 come from MSCI's own "
            "arithmetic.",
        ],
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")

    print(f"MSCI TAIWAN, AUGUST 2026 — MECHANICAL CALL")
    print(f"  cutoff ${CUTOFF}B   add bar ${bar:.2f}B   "
          f"delete floor ${floor:.2f}B   min float ${minfl:.2f}B")
    print(f"  universe {len(U)} screened, {len(mem)} members\n")
    for lab, rows in (("ADDITIONS", adds), ("DELETIONS", dels)):
        print(f"  {lab} — {len(rows)}")
        print(f"     {'code':<7}{'full $B':>9}{'float $B':>10}"
              f"{'ff':>6}{'board':>7}   robust across band?")
        for r in rows:
            print(f"     {r['code']:<7}{r['full_cap_usd_b']:>9.2f}"
                  f"{r['float_cap_usd_b']:>10.2f}"
                  f"{r['float_factor']:>6.2f}{r['board']:>7}"
                  f"   {'yes' if r['robust_across_band'] else 'NO'}")
        print()
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
