"""Show the walk — the size-line computation, fully exposed (c-47).

Produces data/gmsr_walk_may26.json: every ingredient of the
May-2026 coverage walk so a user can judge the calculation:
  1. THE DENOMINATOR: named head (every tracked company's price x
     shares x float) + modeled body (construction parameters
     stated) -> the "free float-adjusted market capitalization of
     Taiwan" our walk divides by
  2. THE TARGET: denominator x 0.85
  3. THE WALK: companies largest-first, cumulative tradable value,
     the crossing -> the size line
  4. SENSITIVITY: how the line moves under body-float 0.5-0.8 and
     head-float +/-10% — the honesty band

Usage: python scripts/show_the_walk.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np                                     # noqa: E402

ASOF = "2026-05-01"
TAIL_SEED, TAIL_N, TAIL_HI = 11, 400, 10e9


def frame(body_ff=0.7, head_ff_scale=1.0):
    from agents.pit_constituents import _data, ladder_asof
    L = ladder_asof(ASOF)
    _, _, _, names, pitc = _data()
    rows = []
    for r in L["ladder"]:
        ffv = None
        for suf in (".TW", ".TWO"):
            v = pitc.get(r["code"] + suf, {})
            if "ff" in v:
                ffv = min(v["ff"], 1.0)
        rows.append({"code": r["code"],
                     "company": names.get(r["code"], ""),
                     "cap_b": r["cap_usd_b"],
                     "ff": min((ffv if ffv else 0.7)
                               * head_ff_scale, 1.0),
                     "ff_source": ("holder filings (yfinance)"
                                   if ffv else
                                   "default 0.7 (estimated)"),
                     "kind": "named"})
    rng = np.random.default_rng(TAIL_SEED)
    caps = np.exp(rng.uniform(np.log(0.3e9), np.log(TAIL_HI),
                              TAIL_N)) / 1e9
    for i, c in enumerate(sorted(caps, reverse=True)):
        rows.append({"code": f"BODY{i:03d}", "company":
                     "(modeled mid-cap body)", "cap_b": round(c, 2),
                     "ff": body_ff, "ff_source":
                     f"body ratio {body_ff}", "kind": "body"})
    rows.sort(key=lambda r: -r["cap_b"])
    total_ff = sum(r["cap_b"] * r["ff"] for r in rows)
    target = 0.85 * total_ff
    cum = 0.0
    for i, r in enumerate(rows):
        cum += r["cap_b"] * r["ff"]
        r["cum_ff_b"] = round(cum, 1)
        r["cum_share"] = round(cum / total_ff, 4)
        if cum >= target and "cross" not in [k for row in rows
                                             for k in row]:
            cross_i = i
            break
    else:
        cross_i = len(rows) - 1
    return rows, total_ff, target, cross_i


def main():
    rows, total_ff, target, ci = frame()
    named = [r for r in rows if r["kind"] == "named"]
    body = [r for r in rows if r["kind"] == "body"]
    named_full = sum(r["cap_b"] for r in named)
    named_ff = sum(r["cap_b"] * r["ff"] for r in named)
    body_full = sum(r["cap_b"] for r in body)
    body_ff_sum = sum(r["cap_b"] * r["ff"] for r in body)
    # sensitivity: the line under alternative float assumptions
    sens = {}
    for tag, bff, hs in (("body_ff_0.5", 0.5, 1.0),
                         ("body_ff_0.8", 0.8, 1.0),
                         ("head_ff_-10%", 0.7, 0.9),
                         ("head_ff_+10%", 0.7, 1.1)):
        rr, tf, tg, cix = frame(body_ff=bff, head_ff_scale=hs)
        sens[tag] = {"denominator_b": round(tf, 0),
                     "size_line_b": rr[cix]["cap_b"]}
    # nearest real names around the crossing
    real_near = []
    for j in range(max(0, ci - 30), min(len(rows), ci + 30)):
        if rows[j]["kind"] == "named":
            real_near.append({k: rows[j][k] for k in
                              ("code", "company", "cap_b")})
    cross = rows[ci]
    curve = [{"rank": i + 1, "cap_b": r["cap_b"],
              "cum_share": r["cum_share"], "kind": r["kind"],
              "code": r["code"],
              "company": (r["company"][:30] if r["kind"] == "named"
                          else "(modeled body)")}
             for i, r in enumerate(rows) if "cum_share" in r]
    out = {
        "asof": ASOF, "event": "MSCI May-2026 frame",
        "denominator": {
            "named_head": {"n": len(named),
                           "full_b": round(named_full, 0),
                           "float_adj_b": round(named_ff, 0),
                           "how": "per-company price x shares "
                                  "(TWSE filings via FinMind, "
                                  "Apr-30) x per-company float "
                                  "estimate"},
            "modeled_body": {"n": len(body),
                             "full_b": round(body_full, 0),
                             "float_adj_b": round(body_ff_sum, 0),
                             "how": f"{TAIL_N} names, sizes drawn "
                                    "log-uniform $0.3-10B (seed "
                                    f"{TAIL_SEED}), float ratio "
                                    "0.7; stands in for the "
                                    "~1,700 listed companies we "
                                    "do not track by name"},
            "total_float_adj_b": round(total_ff, 0)},
        "target_b": round(target, 0),
        "walk": {"crossing_rank": ci + 1,
                 "crossing_kind": cross["kind"],
                 "size_line_b": cross["cap_b"],
                 "coverage_at_crossing": cross["cum_share"],
                 "honesty": ("the crossing lands in the MODELED "
                             "body, not at a nameable company — "
                             "the nearest real members bracket it"
                             if cross["kind"] == "body" else
                             f"crossing at real name "
                             f"{cross['code']}")},
        "nearest_real_names": real_near[:8],
        "sensitivity": sens,
        "curve": curve[::4],          # downsampled for the chart
        # animation frames (c-49, the one-by-one summation): every
        # rank for the giants, every 2nd to just past the crossing
        "anim": (curve[:20] + curve[20:ci + 12:2]),
        "consistency_check": "MSCI's published May-2026 numbers "
                             "(methodology worked example, Apr-20 "
                             "data): DM reference $15.75B -> EM "
                             "range ~$3.9-9.1B; our line must sit "
                             "inside it",
    }
    p = ROOT / "data" / "gmsr_walk_may26.json"
    p.write_text(json.dumps(out, indent=1))
    print(f"denominator: named {named_ff:,.0f} + body "
          f"{body_ff_sum:,.0f} = {total_ff:,.0f}B float-adj")
    print(f"target (85%): {target:,.0f}B")
    print(f"crossing at rank {ci+1} ({cross['kind']}): size line "
          f"${cross['cap_b']}B, coverage {cross['cum_share']:.1%}")
    print("sensitivity:", {k: v['size_line_b']
                           for k, v in sens.items()})
    print("wrote", p)


if __name__ == "__main__":
    main()
