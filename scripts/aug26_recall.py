"""Re-register the Aug-2026 Taiwan call on the CORRECTED
thresholds (c-253).

WHY THIS SCRIPT EXISTS, and why it is a new file rather than an
edit to the old one.

At c-253 the rulebook check found that three thresholds were
computed off the wrong base:

  1. The buffer zones were applied to the ceiling of the global
     EM size range ($9.44B) instead of to Taiwan's own Market
     Size-Segment Cutoff ($6.74B). GIMI May-2026 §3.1.5.1 p.44:
     "the buffer zones at Index Reviews are defined with
     boundaries of 2/3rd of and 1.5 times the MARKET
     SIZE-SEGMENT CUTOFF between two size-segments."

  2. The upper buffer used 1.8x, on the reading that August is
     a quarterly review. Footnote 24's 1.8x belongs to a
     "light rebalancing", which p.107 defines as a switch made
     by MSCI's Index Committees UNDER CONDITIONS OF MARKET
     STRESS, triggered by the Market Monitoring Framework. It
     has nothing to do with the review's cadence. Absent a
     declared light rebalancing the multiple is 1.5x.

  3. The minimum free-float test used half of the ADDITION BAR.
     §2.3.6.1 p.30 sets it at "at least 50% of the Market
     Size-Segment Cutoff for the Standard Index" when the
     cutoff sits inside the Global Minimum Size Range — which
     Taiwan's does. The old base was ~1.8x too strict.

THE INPUTS ARE UNCHANGED. Every cap, float and foreign-room
figure is read straight out of `aug26_cutoff_calc.json`; only
the thresholds applied to them move. That is the point — if
the call changes, it changes because of the rule reading and
nothing else, and anyone can diff the two files to see it.

THE ORIGINAL CALL IS NOT OVERWRITTEN. `aug26_cutoff_calc.json`
keeps the call declared on 2026-08-05 exactly as declared. This
writes a SECOND, dated call so both can be graded against the
12 August announcement. A prediction that gets quietly rewritten
after the fact is not a prediction.

Usage:  py scripts\\aug26_recall.py
Output: data/aug26_call_v2.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "aug26_cutoff_calc.json"
OUT = ROOT / "data" / "aug26_call_v2.json"

# ---- the rules, with their citations -------------------------
LOWER_BUFFER = 2 / 3      # §3.1.5.1 p.44
UPPER_BUFFER = 1.5        # §3.1.5.1 p.44
MIN_FLOAT_CAP = 0.5       # §2.3.6.1 p.30, cutoff inside range
FIF_FLOOR = 0.15          # §2.2.6 global minimum FIF
ROOM_FLOOR = 0.15         # §2.2.8 minimum foreign room

CITE = {
    "buffers": "GIMI May-2026 §3.1.5.1 p.44 — buffer zones of "
               "2/3 and 1.5 times the Market Size-Segment "
               "Cutoff",
    "light": "GIMI May-2026 fn24 p.44 with p.107 — the 1.8x "
             "buffer applies only under a declared 'light "
             "rebalancing' (market stress), not to quarterly "
             "reviews",
    "float_cap": "GIMI May-2026 §2.3.6.1 p.30 — free "
                 "float-adjusted cap of at least 50% of the "
                 "Market Size-Segment Cutoff",
    "fif": "GIMI May-2026 §2.2.6 — global minimum FIF of 0.15",
    "room": "GIMI May-2026 §2.2.8 — foreign room of at least "
            "15%",
    "cutoff": "GIMI May-2026 §2.3.3 p.26 — the 85% walk over "
              "the Market Investable Equity Universe, bounded "
              "into the Global Minimum Size Range",
}


def recall(declared):
    a = json.loads(SRC.read_text(encoding="utf-8"))
    cut = float(a["derivation"]["C_cutoff"]["cutoff_busd"])
    lo, hi = round(LOWER_BUFFER * cut, 2), round(
        UPPER_BUFFER * cut, 2)
    minff = round(MIN_FLOAT_CAP * cut, 2)

    adds = []
    for r in a["add_candidates"]:
        cap, ff = float(r["cap_usd_b"]), float(r.get("ff") or 0)
        room = float(r.get("foreign_room") or 0)
        fcap = round(cap * ff, 2)
        gates = {
            "above upper buffer": cap >= hi,
            "FIF >= 0.15": ff >= FIF_FLOOR,
            "float cap >= 50% of cutoff": fcap >= minff,
            "foreign room >= 15%": room >= ROOM_FLOOR,
        }
        adds.append({
            "code": r["code"], "name": r.get("company") or "",
            "cap_usd_b": cap, "ff": ff, "float_cap_usd_b": fcap,
            "foreign_room": room,
            "x_upper_buffer": round(cap / hi, 2),
            "gates": gates,
            "verdict": ("QUALIFIES" if all(gates.values())
                        else "blocked: " + ", ".join(
                            k for k, v in gates.items() if not v)),
            "was": r.get("verdict", ""),
        })

    dels = []
    for r in a["delete_candidates"]:
        cap = float(r["cap_usd_b"])
        dels.append({
            "code": r["code"], "name": r.get("company") or "",
            "cap_usd_b": cap,
            "x_lower_buffer": round(cap / lo, 2),
            "verdict": ("BELOW the lower buffer — deletion "
                        "candidate" if cap < lo else
                        "inside the buffer — held"),
            "was": r.get("tier", ""),
        })

    old = a["derivation"]["C_cutoff"]
    return {
        "declared": declared,
        "supersedes": ("the call declared 2026-08-05, which is "
                       "kept intact in aug26_cutoff_calc.json "
                       "and graded alongside this one"),
        "why": ("thresholds were computed off the ceiling of "
                "the global EM size range instead of Taiwan's "
                "Market Size-Segment Cutoff; the addition "
                "buffer used the market-stress 1.8x multiple; "
                "and the minimum float test used half the "
                "addition bar instead of half the cutoff"),
        "citations": CITE,
        "thresholds": {
            "market_size_segment_cutoff_busd": cut,
            "lower_buffer_busd": lo,
            "upper_buffer_busd": hi,
            "min_float_cap_busd": minff,
        },
        "superseded_thresholds": {
            "add_bar_busd": old.get("add_bar_busd"),
            "add_bar_rule": old.get("add_bar_rule"),
            "deletion_grace_busd": old.get("deletion_grace_busd"),
            "page_lower_from_em_ceiling_busd": 6.29,
            "page_upper_from_em_ceiling_busd": 14.16,
        },
        "adds": adds,
        "deletes": dels,
    }


def main():
    import datetime as dt
    today = dt.date.today().isoformat()
    out = recall(f"{today} (corrected thresholds; grades Aug-12)")
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    t = out["thresholds"]
    print(f"cutoff {t['market_size_segment_cutoff_busd']}  "
          f"lower {t['lower_buffer_busd']}  "
          f"upper {t['upper_buffer_busd']}  "
          f"min float cap {t['min_float_cap_busd']}")
    print("\nADDITIONS")
    for r in out["adds"]:
        print(f"  {r['code']:5s} cap {r['cap_usd_b']:6.2f}  "
              f"x{r['x_upper_buffer']:<5.2f} {r['verdict']}")
    print("\nDELETIONS")
    for r in out["deletes"]:
        print(f"  {r['code']:5s} cap {r['cap_usd_b']:6.2f}  "
              f"x{r['x_lower_buffer']:<5.2f} {r['verdict']}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
