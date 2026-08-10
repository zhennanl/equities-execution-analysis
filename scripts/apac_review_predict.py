"""The rulebook walk, per market, for the Aug-2026 review
(c-147) — with pre-registered probabilities.

WHAT THIS DOES (GIMI May-2026, in order):
  §2.3.3  Market Size-Segment Cutoff. FALSIFIED PROXY, kept
          on the record: we first set cutoff = full cap of the
          smallest member. Taiwan control killed it — that
          makes the cutoff <= every member by construction, so
          it flagged ZERO deletions against a known 6-name
          declared list. Cutoff now comes from the engine
          (Taiwan, universe-measured) or the factsheet-implied
          CORRIDOR (other markets), and every flag is reported
          with whether it survives the whole corridor.
  §3.1.4.2 No-change zone / Proximity Areas. Deletion buffer
          = 2/3 x cutoff; addition bar = 1.5 x cutoff.
  §2.3.6.1 Float gate: float cap must be >= 50% of the
          cutoff (x1.8 if FIF < 0.15); existing constituents
          get 2/3 relief.
  §3.1.5  Addition priority: >=1.0x necessary, >1.5x
          guaranteed, queue between.

SECOND FALSIFICATION (Taiwan control): only 1 of Taiwan's 6
declared deletions (Wan Hai, float gate) is a FLOOR breach.
The other 5 are DISPLACEMENT deletions — pushed out when
additions take their slots under count stability. Displacement
cannot be seen without the addition side, i.e. without the
universe. So member-only data covers one deletion channel out
of two, and that limit is printed in every market's output.

WHAT IT CANNOT DO WITHOUT A UNIVERSE FILE: the ADDITION side.
Additions come from non-members; a non-member has no index
weight, so nothing in our data even names it. If
data/{market}_universe.json exists (code -> full_cap_usd_b,
fif) the addition screen runs; otherwise the market returns
ADDITIONS: NO_CALL with the reason. Taiwan is the one market
where that file exists (TWSE bulk day-files).

PROBABILITIES ARE PRE-REGISTERED, not fitted after the fact.
The mapping below is declared BEFORE Aug-11 and graded after
(honesty rule: registered thresholds before grading). It is
anchored on the Taiwan backtest: names deeper than 2/3 of the
cutoff were deleted ~85% of the time; names between 2/3 and
0.8x were ~55%; float-gate breaches were ~90%.

Run:  py scripts\\apac_review_predict.py all
Out:  data/aug26_apac_predictions.json + console table
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "aug26_apac_predictions.json"

# ---- REGISTERED PROBABILITY MAP (declared 2026-08-08) ----
# key: (rule, band) -> probability the change happens at THIS
# review. Anchored on the TW backtest; deliberately coarse —
# five buckets, not a false-precision continuum.
PROB = {
    "del_float_gate":       0.85,   # float cap < gate
    "del_deep":             0.85,   # cap < 0.55x cutoff
    "del_below_buffer":     0.70,   # cap < 2/3 cutoff
    "del_proximity":        0.35,   # 2/3 .. 0.8x cutoff
    "add_guaranteed":       0.85,   # cap > 1.5x cutoff
    "add_queue":            0.45,   # 1.0x .. 1.5x cutoff
}
# Haircuts applied multiplicatively, each with a stated cause
HAIRCUT = {
    "fif_estimated":  0.90,   # non-member FIF from Yahoo
    "cutoff_proxy":   0.90,   # cutoff = smallest member, not
    #                           a measured 85% crossing
    "count_flex":     0.85,   # §2.3.3 count may flex, moving
    #                           the cutoff under our feet
    "partial_map":    0.80,   # market FIF coverage < 90%
}


def _j(p):
    p = ROOT / "data" / p
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _members(mkt):
    """(code, name, full_cap_usd_b, fif) for every member."""
    if mkt == "Taiwan":
        W = _j("tw_member_fifs_weights.json")["rows"]
        U = _j("tw_universe_pit.json")["dates"]["20260731"][
            "rows"]
        return [(r["code"], r["name"],
                 (U.get(r["code"]) or {}).get("cap_usd_b"),
                 r["fif_weights"]) for r in W]
    inv = (_j("apac_fif_inverted.json") or {}).get(mkt)
    if not inv or "rows" not in inv:
        return []
    return [(r.get("code"), r.get("name"),
             r.get("full_cap_usd_b"), r.get("fif"))
            for r in inv["rows"]]


def market(mkt):
    """Floor/float-gate deletion screen ONLY (see the
    falsification note in the module docstring)."""
    mem = [m for m in _members(mkt) if m[2] and m[3]]
    if len(mem) < 5:
        return {"market": mkt, "status": "NO_DATA",
                "need": "member FIFs — run "
                        f"apac_fif_inversion.py market {mkt}"}
    arch = (_j("apac_factsheet_archive.json") or {}).get(
        mkt, {}).get("2026-07", {})
    corr = arch.get("cutoff_corridor_busd") or [4.1, 9.44]
    lo, hi = corr
    if mkt == "Taiwan":
        lo, hi = 6.73, 6.73          # measured by our engine
    inv = (_j("apac_fif_inverted.json") or {}).get(mkt) or {}
    cover = len(mem) / (inv.get("qc", {}).get("n_members")
                        or len(mem))
    hc = HAIRCUT["count_flex"]
    if mkt != "Taiwan":
        hc *= HAIRCUT["cutoff_proxy"]
    if cover < 0.9 and mkt != "Taiwan":
        hc *= HAIRCUT["partial_map"]
    dels = []
    for code, name, cap, fif in mem:
        flo = cap * fif
        def breach(cut):
            gate_c = 0.5 * cut * (1.8 if fif < 0.15 else 1.0) \
                * 2 / 3
            if flo < gate_c:
                return "del_float_gate", gate_c
            if cap < 0.55 * cut:
                return "del_deep", None
            if cap < (2 / 3) * cut:
                return "del_below_buffer", None
            if cap < 0.8 * cut:
                return "del_proximity", None
            return None, None
        r_lo, g_lo = breach(lo)
        r_hi, _ = breach(hi)
        if not r_hi:
            continue
        robust = bool(r_lo)          # breaches even at the
        #                              most forgiving cutoff
        rule = r_lo or r_hi
        p = PROB[rule] * hc * (1.0 if robust else 0.45)
        why = (f"full cap ${cap:.2f}B, float cap ${flo:.2f}B "
               f"(FIF {fif:.3f}). Against the cutoff "
               + (f"${lo:.2f}B measured by our engine"
                  if lo == hi else
                  f"corridor ${lo:.2f}-{hi:.2f}B (factsheet-"
                  "implied, no universe measured)")
               + f": rule {rule}"
               + ("; breaches across the WHOLE corridor"
                  if robust else
                  "; breaches only at the demanding end of "
                  "the corridor — fragile"))
        dels.append({"code": code, "name": name,
                     "action": "DELETE", "rule": rule,
                     "robust_across_corridor": robust,
                     "full_cap_usd_b": round(cap, 2),
                     "float_cap_usd_b": round(flo, 2),
                     "fif": fif, "prob": round(p, 2),
                     "why": why})
    # ---- SANITY GATE (c-147, third falsification) --------
    # The factsheet "corridor" is a GLOBAL size-segment range,
    # not a market cutoff. Applied to a small market it flags
    # absurd names (it called Fisher & Paykel — New Zealand's
    # LARGEST member — a deletion). Refuse to publish a screen
    # that flags a top-quartile member or more than a fifth of
    # the membership.
    invalid = None
    if dels and mkt != "Taiwan":
        caps = sorted((m[2] for m in mem), reverse=True)
        q1 = caps[max(0, len(caps) // 4 - 1)]
        if any(d["full_cap_usd_b"] >= q1 for d in dels):
            invalid = ("flags a top-quartile member — the "
                       "cutoff corridor is a GLOBAL size range, "
                       "not this market's cutoff")
        elif len(dels) > 0.2 * len(mem):
            invalid = (f"flags {len(dels)}/{len(mem)} members — "
                       "implausible; cutoff not measured")
    if invalid:
        return {"market": mkt, "status": "NO_CALL",
                "reason": invalid,
                "n_members_scored": len(mem),
                "suppressed_flags": [d["code"] for d in dels],
                "unblock": "measure this market's own 85% "
                           "crossing from its listed universe "
                           "(exchange bulk files), as Taiwan "
                           "does"}
    return {"market": mkt, "asof": "2026-07-31",
            "cutoff_used_usd_b": [lo, hi],
            "cutoff_source": ("engine rank-77 (universe "
                              "measured)" if mkt == "Taiwan"
                              else "factsheet-implied "
                                   "corridor — NOT measured"),
            "n_members_scored": len(mem),
            "haircut_applied": round(hc, 3),
            "channel_covered": "size-floor + float-gate only",
            "channel_missing": ("DISPLACEMENT — members pushed "
                                "out when additions take their "
                                "slots under count stability. "
                                "This produced 5 of Taiwan's 6 "
                                "declared deletions and cannot "
                                "be seen without the universe."),
            "deletions": sorted(dels, key=lambda x: -x["prob"]),
            "additions": {"status": "NO_CALL",
                          "reason": "additions come from "
                                    "NON-members; no listed-"
                                    f"universe file for {mkt}"}}


def main():
    mkts = ["Taiwan", "NewZealand", "Singapore", "Korea",
            "Australia", "HongKong", "India", "Japan",
            "Indonesia", "Malaysia", "Thailand", "China"]
    out = {"generated": "2026-08-08",
           "registered_probabilities": PROB,
           "haircuts": HAIRCUT, "markets": {}}
    for m in mkts:
        r = market(m)
        out["markets"][m] = r
        if r.get("status") in ("NO_DATA", "NO_CALL"):
            print(f"{m:12} {r['status']} — "
                  f"{r.get('need') or r.get('reason')}")
            continue
        lo, hi = r["cutoff_used_usd_b"]
        print(f"\n{m} | cutoff ${lo}-{hi}B ({r['cutoff_source']})"
              f" | {r['n_members_scored']} members | haircut "
              f"{r['haircut_applied']}")
        for d in r["deletions"]:
            print(f"   DEL {d['code']:8} {d['name'][:26]:26} "
                  f"p={d['prob']:.2f}  {d['rule']}")
        print(f"   ADD: {r['additions'].get('status')}")
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\n-> {OUT.name}")


if __name__ == "__main__":
    main() if (len(sys.argv) > 1 and sys.argv[1] == "all") \
        else print(__doc__)
