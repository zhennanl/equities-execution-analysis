"""Display the ENTIRE corrected walk (c-94) — every screened
company in rank order with cumulative float coverage, the 85%
crossing marked, the corridor ceiling marked, and CURRENT
MEMBERSHIP flagged so the §2.3.3 reconciliation is visible:

  members above the ceiling        (size alone keeps them)
  members in the buffer zone       (6.29-9.44: incumbency
                                    keeps them — the hysteresis)
  members below the delete floor   (the pool)
  non-members above the add bar    (the candidates)

Usage: py scripts\\walk_display.py
Output: reports/walk_display.html + printed reconciliation
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CEIL, FLOOR, ADDBAR = 9.44, 6.29, 14.16


def main():
    from scripts.cutoff_walk_v2 import build
    base, rows = build()
    members = set(json.loads(
        (ROOT / "data" / "apac_members.json").read_text())
        ["markets"]["Taiwan"]["standard_members"])
    D = sum(r["float_b"] for r in rows)
    target = 0.85 * D
    cum = 0.0
    out_rows = []
    zone_counts = {"mem_above_ceiling": 0, "mem_buffer": 0,
                   "mem_below_floor": 0, "mem_other": 0,
                   "non_above_bar": 0, "non_above_ceiling": 0}
    for i, r in enumerate(rows, 1):
        cum += r["float_b"]
        is_mem = r["code"] in members
        cap = r["cap_b"]
        if is_mem:
            zone = ("above ceiling" if cap > CEIL else
                    "BUFFER (incumbency)" if cap >= FLOOR else
                    "DELETE POOL")
            key = ("mem_above_ceiling" if cap > CEIL else
                   "mem_buffer" if cap >= FLOOR else
                   "mem_below_floor")
            zone_counts[key] += 1
        else:
            zone = ("ADD CANDIDATE" if cap >= ADDBAR else
                    "above ceiling (non-member)" if cap > CEIL
                    else "")
            if cap >= ADDBAR:
                zone_counts["non_above_bar"] += 1
            elif cap > CEIL:
                zone_counts["non_above_ceiling"] += 1
        out_rows.append(
            {"rank": i, "code": r["code"],
             "full_cap_b": round(cap, 2),
             "float_b": round(r["float_b"], 2),
             "ff": r["ff"], "ff_src": r["ff_src"],
             "cum_cov_pct": round(100 * cum / D, 2),
             "member": "M" if is_mem else "",
             "zone": zone})
    cross = next(r for r in out_rows
                 if r["cum_cov_pct"] >= 85.0)
    recon = {
        "n_screened": len(rows),
        "denominator_busd": round(D, 1),
        "crossing": {"rank": cross["rank"],
                     "code": cross["code"],
                     "full_cap_b": cross["full_cap_b"]},
        "companies_above_ceiling_9.44":
            sum(1 for r in out_rows
                if r["full_cap_b"] > CEIL),
        "zones": zone_counts,
        "member_total_check":
            zone_counts["mem_above_ceiling"]
            + zone_counts["mem_buffer"]
            + zone_counts["mem_below_floor"]
            + zone_counts["mem_other"],
        "note": "anchor member set = 79 (factsheet 77; known "
                "±2 share-class/timing reconciliation). "
                "Members in the BUFFER zone are kept by "
                "incumbency (2/3 rule), NOT by the ceiling — "
                "that is why membership exceeds the "
                "above-ceiling count.",
    }
    html = ["<html><head><meta charset='utf-8'><style>"
            "table{border-collapse:collapse;font:12px monospace}"
            "td,th{border:1px solid #ccc;padding:2px 7px}"
            ".cross{background:#ffe08a}.ceil{background:#cfe8ff}"
            ".mem{background:#e8f5e9}.del{background:#ffcdd2}"
            ".add{background:#d1c4e9}</style></head><body>"
            "<h1>The entire walk — Taiwan (census frame)</h1>"
            f"<pre>{json.dumps(recon, indent=1)}</pre>"
            "<table><tr><th>rank</th><th>code</th><th>full $B"
            "</th><th>float $B</th><th>ff</th><th>src</th>"
            "<th>cum cov %</th><th>member</th><th>zone</th>"
            "</tr>"]
    for r in out_rows:
        cls = ""
        if r["rank"] == cross["rank"]:
            cls = "cross"
        elif r["zone"] == "DELETE POOL":
            cls = "del"
        elif r["zone"] == "ADD CANDIDATE":
            cls = "add"
        elif r["member"]:
            cls = "mem"
        html.append(
            f"<tr class='{cls}'><td>{r['rank']}</td>"
            f"<td>{r['code']}</td><td>{r['full_cap_b']}</td>"
            f"<td>{r['float_b']}</td><td>{r['ff']:.2f}</td>"
            f"<td>{r['ff_src'][:12]}</td>"
            f"<td>{r['cum_cov_pct']}</td><td>{r['member']}</td>"
            f"<td>{r['zone']}</td></tr>")
    html.append("</table></body></html>")
    rep = ROOT / "reports"
    rep.mkdir(exist_ok=True)
    (rep / "walk_display.html").write_text("\n".join(html),
                                           encoding="utf-8")
    print(json.dumps(recon, indent=1))
    print("written: reports/walk_display.html "
          f"({len(out_rows)} rows)")


if __name__ == "__main__":
    main()
