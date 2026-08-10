"""The weights inversion, as a reproducible script (c-140).

FIF_i = weight_i x IndexFloatCap / full_cap_i  (see QA Q76)

Inputs: msci_official_constituents.json (all 77 TW weights,
sum gated ~100%), the factsheet index float cap at Jun-01
($3,331.4B), and the 20260601 PIT universe full caps.

c-140: the earlier run mapped 60/77 — the 17 misses were
NAME-MATCHING failures (MSCI abbreviations like 'TAIWAN
SEMICONDUCTOR MFG', 'NOVATEK MICROELECTRS'), NOT names
missing from the page. OVERRIDES below closes the map by
hand: 77/77.

Validation: recovered FIFs should sit ON MSCI's rounding
grid (2.5% steps above 0.15 per Appendix VI) — the script
prints each name's distance to the nearest grid point.

Run: py scripts\\tw_fif_inversion.py
Out: data/tw_member_fifs_weights.json (overwrites; the old
     60-row file is superseded — recorded, not hidden)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDXCAP_JUN01_BUSD = 3331.4         # factsheet, Jun-01
UNI_DATE = "20260601"

# the 17 hand-mapped names (c-140)
OVERRIDES = {
    "TAIWAN SEMICONDUCTOR MFG": "2330",
    "HON HAI PRECISION IND CO": "2317",
    "UNITED MICROELECTRONICS": "2303",
    "CHUNGHWA TELECOM CO": "2412",
    "LARGAN PRECISION CO": "3008",
    "JENTECH PRECISION INDL": "3653",
    "FIRST FINANCIAL HLDG CO": "2892",
    "HUA NAN FINANCIAL HLDGS": "2880",
    "NOVATEK MICROELECTRS": "3034",
    "TAIWAN COPR FINL HLDG": "5880",
    "VANGUARD INTL SC": "5347",
    "GIGABYTE TECHNOLOGY CO": "2376",
    "INTL GAMES SYSTEM C": "3293",
    "FAR EASTONE TELECOM. CO": "4904",
    "SHANGHAI COMM & SAV BANK": "5876",
    "CHANG HWA COMMERCIAL BK": "2801",
    "HOTAI MOTOR COMPANY": "2207"}


def _grid_dist(f):
    """Distance to MSCI's FIF rounding grid (0.025 steps)."""
    g = round(f / 0.025) * 0.025
    return abs(f - g)


def build():
    cons = json.loads((ROOT / "data" /
                       "msci_official_constituents.json")
                      .read_text(encoding="utf-8"))["markets"]["Taiwan"][
                          "constituents"]
    old = json.loads((ROOT / "data" /
                      "tw_member_fifs_weights.json")
                     .read_text(encoding="utf-8"))
    name2code = {r["name"]: r["code"] for r in old["rows"]}
    name2code.update(OVERRIDES)
    uni = json.loads((ROOT / "data" / "tw_universe_pit.json")
                     .read_text(encoding="utf-8"))["dates"][UNI_DATE]["rows"]
    rows, unmapped = [], []
    for r in cons:
        code = name2code.get(r["security"])
        cap = (uni.get(code) or {}).get("cap_usd_b") \
            if code else None
        if not code or not cap:
            unmapped.append((r["security"], r["weight"],
                             code or "NO_TICKER",
                             "NO_CAP" if code else ""))
            continue
        flo = r["weight"] / 100 * IDXCAP_JUN01_BUSD
        fif = flo / cap
        rows.append({"code": code, "name": r["security"],
                     "weight_pct": r["weight"],
                     "fif_weights": round(fif, 3),
                     "full_jun1_b": cap,
                     "msci_float_b": round(flo, 2),
                     "grid_dist": round(_grid_dist(fif), 3)})
    rows.sort(key=lambda x: -x["msci_float_b"])
    out = {"idxcap_jun01_busd": IDXCAP_JUN01_BUSD,
           "n_index": len(cons), "n_mapped": len(rows),
           "unmapped": unmapped, "rows": rows}
    (ROOT / "data" / "tw_member_fifs_weights.json") \
        .write_text(json.dumps(out, indent=1), encoding="utf-8")
    on_grid = sum(1 for r in rows if r["grid_dist"] <= 0.01)
    print(f"mapped {len(rows)}/{len(cons)} | on-grid "
          f"(<=1pp): {on_grid}/{len(rows)}")
    for n, w, c, why in unmapped:
        print(f"  UNMAPPED {w:5.2f}% {n} [{c}{why}]")
    for r in rows[:6]:
        print(f"  {r['code']} {r['name'][:26]:26} "
              f"fif {r['fif_weights']:.3f} "
              f"(grid±{r['grid_dist']:.3f})")


if __name__ == "__main__":
    build()
    sys.exit(0)
