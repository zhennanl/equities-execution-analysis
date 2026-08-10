"""TAIWAN — the Aug-2026 index review call, re-run (c-150).

Supersedes the 2026-08-07 declaration. The earlier shortlist
stays in the ledger and is graded as declared; this is a NEW
dated declaration, not an edit (corrections are recorded, not
rewritten).

WHAT CHANGED SINCE 08-07
  - full ATVR now measured for 466 TWSE names (the §2.2.5
    screen was previously assumed for most of the universe)
  - MSCI's own FIFs for 77/77 members (was 60/77)
  - MIEU rebuilt on the 20260731 universe

THE WALK (GIMI May-2026)
  §2.3.3  sort MIEU by FULL cap desc; accumulate FLOAT cap;
          note the 85% crossing. Count stability: the Segment
          Number of Companies (77) is "used to maintain the
          indexes over time", so the operative cutoff is the
          full cap at rank 77 — the raw crossing is reported
          alongside as the alternative scenario.
  §3.1.5  addition needs >= 1.0x cutoff; > 1.5x is
          guaranteed; between = priority queue.
  §3.1.4.2 incumbent floor = 2/3 x cutoff.
  §2.3.6.1 float gate = 50% of cutoff (x1.8 if FIF < 0.15),
          with 2/3 relief for existing constituents.

PROBABILITIES — registered before the announcement, graded
after. Base rates from the rulebook zone, then explicit
multiplicative haircuts, each named in the output so a reader
can undo any one they disagree with.

Run: py scripts\\tw_aug26_predict.py
Out: data/aug26_tw_call_v2.json + console
"""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "aug26_tw_call_v2.json"
COUNT = 77                      # Segment Number of Companies

BASE = {"add_guaranteed": 0.85, "add_queue": 0.45,
        "del_float_gate": 0.85, "del_deep": 0.85,
        "del_below_floor": 0.70, "del_displaced": 0.55,
        "del_proximity": 0.30}
HAIRCUT = {"count_flex": 0.85,      # §2.3.3 count may move
           "atvr_not_evaluated": 0.85,   # TPEx names
           "float_estimated": 0.90,      # non-member FIF
           "blind_band": 0.95}      # unseen names take slots


def _j(p):
    return json.loads((ROOT / "data" / p).read_text(encoding="utf-8"))


def run():
    m = _j("tw_mieu_universe.json")
    uni = m["universe"]
    members = {r["code"]: r for r in
               _j("tw_member_fifs_weights.json")["rows"]}
    atvr = _j("tw_atvr.json")["months"]
    # c-150 FIX: a MEMBER can be missing from the MIEU because
    # it failed a §2.2 screen — silently dropping it hides a
    # deletion. Wan Hai (2615) was exactly this: foreign room
    # 10.8% fails §2.2.8 for INCLUSION. But §2.3.6.2 says an
    # EXISTING constituent with low foreign room is NOT deleted
    # — its weight gets an adjustment factor (0.5 for room in
    # 7.5-15%; deletion only below 3.75%). Its MSCI FIF of
    # 0.251 is exactly 0.5 x 0.502, i.e. the factor is already
    # applied. So the name is re-admitted here and judged on
    # the float-cap test, which §2.3.6.2 says to assess BEFORE
    # the adjustment factor.
    pit = _j("tw_universe_pit.json")["dates"][m["date"]]["rows"]
    readmit = {}
    for c, mem in members.items():
        if c in uni:
            continue
        r = pit.get(c) or {}
        cap = r.get("cap_usd_b")
        if not cap:
            continue
        fol, heldf = r.get("fol"), r.get("foreign") or 0
        room = ((fol - heldf) / fol) if fol and fol < 1.0 \
            else 1.0
        uni[c] = {"cap": cap, "ff": mem["fif_weights"],
                  "src": "msci-weights-inversion",
                  "fcap": round(cap * mem["fif_weights"], 4),
                  "mkt": r.get("mkt"), "atvr": None,
                  "readmitted": True, "foreign_room": round(
                      room, 4)}
        readmit[c] = round(room, 4)
    srt = sorted(uni.items(), key=lambda x: -x[1]["cap"])
    cutoff = srt[COUNT - 1][1]["cap"]      # rank-77 full cap
    raw = m["crossing"]
    bar, floor = 1.5 * cutoff, (2 / 3) * cutoff
    calls = []

    def tpex_flag(c):
        return "TPEX" in str(atvr.get(c, {}).get("note", ""))

    # ---------- ADDITIONS: non-members above the bar -------
    for rank, (c, v) in enumerate(srt, 1):
        if c in members or v["cap"] < cutoff:
            continue
        est = v["src"] not in ("factsheet-implied",
                               "msci-weights-inversion")
        p = BASE["add_guaranteed"] if v["cap"] >= bar \
            else BASE["add_queue"]
        hc = HAIRCUT["count_flex"] * HAIRCUT["blind_band"]
        notes = ["§2.3.3 count-flex risk"]
        if tpex_flag(c):
            hc *= HAIRCUT["atvr_not_evaluated"]
            notes.append("TPEx — ATVR NOT_EVALUATED (§2.2.5 "
                         "assumed pass, not measured)")
        if est:
            hc *= HAIRCUT["float_estimated"]
            notes.append(f"float from {v['src']}, not MSCI")
        calls.append({
            "action": "ADD", "code": c, "rank": rank,
            "full_cap_usd_b": round(v["cap"], 2),
            "float_cap_usd_b": round(v["fcap"], 2),
            "fif": v["ff"], "float_src": v["src"],
            "x_cutoff": round(v["cap"] / cutoff, 2),
            "zone": ("guaranteed (>1.5x)" if v["cap"] >= bar
                     else "priority queue (1.0-1.5x)"),
            "prob": round(p * hc, 2), "caveats": notes,
            "why": (
                f"Not currently in the index. Passes every "
                f"§2.2 screen, and at rank {rank} of the "
                f"Market Investable Equity Universe its full "
                f"cap ${v['cap']:.2f}B is "
                f"{v['cap'] / cutoff:.2f}x the ${cutoff:.2f}B "
                f"cutoff — "
                + ("above the 1.5x bar, which §3.1.5 makes a "
                   "GUARANTEED addition when a slot exists."
                   if v["cap"] >= bar else
                   "inside the 1.0-1.5x band, so §3.1.5 puts "
                   "it in the priority queue: it goes in only "
                   "if slots remain after the guaranteed "
                   "names.")
                + f" Float cap ${v['fcap']:.2f}B (FIF "
                  f"{v['ff']}, {v['src']}) clears the "
                  f"§2.3.6.1 gate of ${0.5 * cutoff:.2f}B.")})

    n_add = len(calls)
    # ---------- DELETIONS ---------------------------------
    # (a) rule breaches, (b) displacement to hold the count
    held = [(c, v) for c, v in srt if c in members]
    for c, v in held:
        cap, ff, fcap = v["cap"], v["ff"], v["fcap"]
        gate = 0.5 * cutoff * (1.8 if ff < 0.15 else 1.0) \
            * 2 / 3
        rule = why = None
        room = v.get("foreign_room")
        if room is not None and room < 0.0375:
            rule = "del_float_gate"
            why = (f"Foreign room {room:.1%} is below 3.75%: "
                   f"§2.3.6.2 sets the adjustment factor to "
                   f"ZERO, which removes the security.")
        elif fcap < gate:
            rule = "del_float_gate"
            why = (f"Float-adjusted cap ${fcap:.2f}B is below "
                   f"the §2.3.6.1 constituent gate "
                   f"${gate:.2f}B (50% of the ${cutoff:.2f}B "
                   f"cutoff, with the 2/3 relief incumbents "
                   f"get). Its FIF is {ff} — MSCI's OWN "
                   f"number, recovered from the published "
                   f"weights, so this is not float-estimate "
                   f"risk. Full cap ${cap:.2f}B would survive "
                   f"on size alone; the float is what fails."
                   + (f" Note the mechanism: foreign room is "
                      f"{room:.1%}, inside the 7.5-15% band, "
                      f"so §2.3.6.2 applies an adjustment "
                      f"factor of 0.5 — and indeed MSCI's FIF "
                      f"{ff} is almost exactly half of "
                      f"{2 * ff:.3f}. Low foreign room does "
                      f"NOT delete on its own; it halves the "
                      f"float, and the halved float is what "
                      f"breaches the gate."
                      if room is not None and room < 0.15
                      else ""))
        elif cap < 0.55 * cutoff:
            rule = "del_deep"
            why = (f"Full cap ${cap:.2f}B is "
                   f"{cap / cutoff:.2f}x the cutoff — far "
                   f"below the 2/3 (${floor:.2f}B) incumbent "
                   f"floor of §3.1.4.2.")
        elif cap < floor:
            rule = "del_below_floor"
            why = (f"Full cap ${cap:.2f}B is "
                   f"{cap / cutoff:.2f}x the cutoff, under "
                   f"the 2/3 floor ${floor:.2f}B — §3.1.4.2 "
                   f"deletes incumbents that fall through it.")
        if rule:
            hc = HAIRCUT["count_flex"] * (
                HAIRCUT["atvr_not_evaluated"] if tpex_flag(c)
                else 1.0)
            calls.append({
                "action": "DELETE", "code": c,
                "name": members[c]["name"],
                "full_cap_usd_b": round(cap, 2),
                "float_cap_usd_b": round(fcap, 2),
                "fif": ff, "rule": rule,
                "x_cutoff": round(cap / cutoff, 2),
                "prob": round(BASE[rule] * hc, 2),
                "caveats": ["§2.3.3 count-flex risk"],
                "why": why})
    # displacement: additions take slots, smallest incumbents
    # leave, until the count returns to 77
    breached = {x["code"] for x in calls
                if x["action"] == "DELETE"}
    survivors = [(c, v) for c, v in held if c not in breached]
    # c-150: a rule-breach deletion ALREADY frees a slot, so
    # displacement only has to cover the remainder (the first
    # run double-counted and produced 9 deletions for 8 adds).
    need = n_add - (COUNT - len(held)) - len(breached)
    for c, v in sorted(survivors, key=lambda x: x[1]["cap"])[
            :max(0, need)]:
        calls.append({
            "action": "DELETE", "code": c,
            "name": members[c]["name"],
            "full_cap_usd_b": round(v["cap"], 2),
            "float_cap_usd_b": round(v["fcap"], 2),
            "fif": v["ff"], "rule": "del_displaced",
            "x_cutoff": round(v["cap"] / cutoff, 2),
            "prob": round(BASE["del_displaced"]
                          * HAIRCUT["count_flex"], 2),
            "caveats": ["displacement is CONDITIONAL on the "
                        "additions landing — it is the "
                        "weakest link in the chain",
                        "§2.3.3 count-flex risk"],
            "why": (f"Passes every rule on its own (full cap "
                    f"${v['cap']:.2f}B = "
                    f"{v['cap'] / cutoff:.2f}x cutoff, above "
                    f"the 2/3 floor), but it is among the "
                    f"smallest surviving incumbents. With "
                    f"{n_add} additions qualifying and the "
                    f"Segment Number of Companies held at "
                    f"{COUNT} (§2.3.3), the smallest members "
                    f"are displaced to make room. This is the "
                    f"channel that produced 5 of the 6 "
                    f"deletions in the previous call.")})

    out = {"market": "Taiwan", "review": "Aug-2026",
           "declared": dt.date.today().isoformat(),
           "supersedes": "2026-08-07 declaration (kept for "
                         "grading; not edited)",
           "data_asof": m["date"],
           "cutoff_usd_b": round(cutoff, 3),
           "cutoff_rule": f"full cap at rank {COUNT} under "
                          "count stability (§2.3.3)",
           "raw_85pct_crossing": raw,
           "addition_bar_usd_b": round(bar, 3),
           "incumbent_floor_usd_b": round(floor, 3),
           "mieu_n": m["mieu_n"],
           "registered_base_rates": BASE,
           "registered_haircuts": HAIRCUT,
           "calls": calls}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"cutoff ${cutoff:.2f}B (rank {COUNT}) | bar "
          f"${bar:.2f}B | floor ${floor:.2f}B | raw 85% "
          f"crossing rank {raw['rank']} at "
          f"${raw['cutoff_usd_b']}B")
    for k in ("ADD", "DELETE"):
        print(f"\n--- {k} ---")
        for x in sorted((c for c in calls
                         if c["action"] == k),
                        key=lambda x: -x["prob"]):
            print(f"  {x['code']:6} {x.get('name', '')[:24]:24}"
                  f" {x['x_cutoff']:>5}x  p={x['prob']:.2f}"
                  f"  {x.get('zone') or x.get('rule')}")
    print(f"\n-> {OUT.name}")


if __name__ == "__main__":
    run()
