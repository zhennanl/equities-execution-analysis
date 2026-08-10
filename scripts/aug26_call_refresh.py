"""Refresh the registered Aug-2026 Taiwan call (c-284).

    py scripts\\aug26_call_refresh.py

WHY. The call the site shows was declared against a $6.75B
cutoff, a $10.13B addition bar and a $4.50B incumbent floor.
c-273 retracted that frame: the cutoff of record is $7.22B,
derived by inverting MSCI's own factsheet, with the bar at
$10.83B and the floor at $4.81B. So the page has been
publishing a prediction built on thresholds this project no
longer stands behind.

WHAT CHANGES, AND WHAT DOES NOT.

  * The THRESHOLDS come from `aug26_cutoff_calc.json`.
  * The NAMES come from `aug26_prediction.json`, the mechanical
    call — two thresholds applied to the screened universe, no
    discretion.
  * The BASE RATES and HAIRCUTS are carried over unchanged.
    They were registered in advance and re-estimating them
    while restating a call is how a forecast quietly becomes a
    fit. If they are wrong they should be changed on their own
    evidence, not in the same commit as the numbers they score.

THE DELETION SIDE IS EMPTY, AND THAT IS THE FINDING.

At a $7.22B cutoff the deletion floor is $4.81B and no current
member breaches it. Taiwan has nevertheless deleted at least
one name in every review since 2015, averaging 2.3. The old
call listed eight deletions because its floor sat at $4.50B on
a frame we withdrew — it was not better information, it was a
lower bar. Publishing zero and saying why is the honest
position; publishing eight from a retracted frame is not.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
CALL = ROOT / "data" / "aug26_tw_call_v2.json"
PRED = ROOT / "data" / "aug26_prediction.json"
CALC = ROOT / "data" / "aug26_cutoff_calc.json"


def main():
    old = json.loads(CALL.read_text(encoding="utf-8"))
    pred = json.loads(PRED.read_text(encoding="utf-8"))
    calc = (json.loads(CALC.read_text(encoding="utf-8"))
            ["derivation"]["C_cutoff"])
    cut = calc["cutoff_busd"]
    bar = calc["addition_bar_busd"]
    floor = calc["deletion_floor_busd"]
    minfl = calc["min_float_busd"]
    br = old["registered_base_rates"]
    hc = old["registered_haircuts"]

    # the same product the step-5 waterfall draws, so the
    # figure and the call cannot disagree
    p_guaranteed = round(br["add_guaranteed"] * hc["count_flex"]
                         * hc["float_estimated"]
                         * hc["blind_band"], 4)

    calls = []
    for r in pred["additions"]:
        x = round(r["full_cap_usd_b"] / cut, 2)
        robust = r["robust_across_band"]
        prob = p_guaranteed if robust else round(
            p_guaranteed * 0.6, 4)
        caveats = ["§2.3.3 count-flex risk",
                   f"float from {r['float_source']}, not MSCI"]
        if not robust:
            caveats.append(
                "not robust across the cutoff band — the call "
                "flips at one edge")
        calls.append({
            "action": "ADD", "code": r["code"],
            "full_cap_usd_b": r["full_cap_usd_b"],
            "float_cap_usd_b": r["float_cap_usd_b"],
            "fif": r["float_factor"], "float_src": r["float_source"],
            "x_cutoff": x,
            "zone": ("guaranteed (>1.5x)" if x >= 1.5
                     else "queue (above cutoff, below bar)"),
            "prob": prob,
            "name": r["code"],
            "caveats": caveats,
            "why": (
                f"Not currently in the index. Its full market "
                f"cap of &#36;{r['full_cap_usd_b']}B is {x}x the "
                f"&#36;{cut}B cutoff"
                + (f", clearing the &#36;{bar}B addition bar, "
                   f"which §3.1.5 makes a guaranteed addition "
                   f"when a slot exists."
                   if x >= 1.5 else
                   f", above the cutoff but short of the "
                   f"&#36;{bar}B bar, so it joins the queue "
                   f"rather than qualifying outright.")
                + f" Free-float cap &#36;{r['float_cap_usd_b']}B "
                  f"(FIF {r['float_factor']}, "
                  f"{r['float_source']}) clears the §2.3.6.1 "
                  f"minimum of &#36;{minfl}B."
                + ("" if robust else
                   " The verdict does NOT hold across the "
                   "cutoff band, so it is carried at a reduced "
                   "probability.")),
        })
    for r in pred["deletions"]:
        calls.append({
            "action": "DELETE", "code": r["code"],
            "full_cap_usd_b": r["full_cap_usd_b"],
            "float_cap_usd_b": r["float_cap_usd_b"],
            "fif": r["float_factor"], "float_src": r["float_source"],
            "x_cutoff": round(r["full_cap_usd_b"] / cut, 2),
            "zone": "below the deletion floor",
            "prob": round(br["del_below_floor"] * hc["count_flex"]
                          * hc["float_estimated"], 4),
            "name": r["code"], "caveats": ["§2.3.3 count-flex risk"],
            "why": (f"A current member whose full cap of "
                    f"&#36;{r['full_cap_usd_b']}B is below the "
                    f"&#36;{floor}B deletion floor."),
        })

    out = dict(old)
    out.update({
        "declared": pred["generated"],
        "supersedes": (f"the {old['cutoff_usd_b']}B-cutoff call "
                       f"declared {str(old['declared'])[:10]}, "
                       f"withdrawn with that frame (c-273)"),
        "data_asof": pred["universe"]["priced_asof"],
        "cutoff_usd_b": cut,
        "cutoff_rule": pred["cutoff_derivation"]["source"],
        "addition_bar_usd_b": bar,
        "incumbent_floor_usd_b": floor,
        "mieu_n": pred["universe"]["screened_names"],
        "calls": calls,
        "limits": pred["limits"],
    })
    CALL.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print(f"  cutoff ${cut}B  bar ${bar}B  floor ${floor}B")
    print(f"  {sum(1 for c in calls if c['action'] == 'ADD')} "
          f"additions, "
          f"{sum(1 for c in calls if c['action'] != 'ADD')} "
          f"deletions")
    for c in calls:
        print(f"     {c['action']:<7}{c['code']:<7}"
              f"{c['x_cutoff']:>6}x cutoff   "
              f"{c['prob']:.0%}")
    print(f"-> {CALL.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
