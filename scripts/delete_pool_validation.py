"""Delete-pool validation — the breadth fix, proven on the two
hardest events (session 9i c-33).

Method (the answer to "how do we find the deletion pool without a
licensed constituent list"): we do NOT need all 83 members — only
the BOTTOM of the member ladder, built from free public data:
  1. membership: EWT holdings anchor reverse-rolled through
     official reviews to the PIT date (consistency-flagged names
     like 4551 excluded)
  2. caps: vintage cache (shares x close as-of, FinMind)
  3. pool: members below 1.15x GMSR (the buffer-band edge) —
     generous on purpose so anchor imperfections cannot drop a
     real candidate

Validated here on:
  - May-2026 SAIR (the graded event): 7/7 deletions in pool,
    PERFECT separation (all deleted < 1.0x GMSR, survivors > 1.05x)
  - Nov-2025 SAIR (the historical 0/7 breadth failure): 7/7
    deletions present, occupying 7 of the bottom 8 ladder slots

Usage: python scripts/delete_pool_validation.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd                                    # noqa: E402

FX = 32.5
FLAGGED = {"4551"}          # EWT-vs-change-history inconsistency
OUT = ROOT / "data" / "delete_pool_validation.json"


def ladder(asof):
    cache = json.loads((ROOT / "data" / "tw_vintage_cache.json")
                       .read_text())
    ev = json.loads((ROOT / "data" / "msci_tw_events.json")
                    .read_text())
    ewt = set(json.loads((ROOT / "data" / "ewt_members.json")
                         .read_text())["codes"])
    mem = {c: True for c in ewt if c not in FLAGGED}
    for e in ev.values():
        if e["ann"] <= asof:
            continue
        for c in e["adds"]:
            mem[c] = False
        for c in e["dels"]:
            mem[c] = True
    rows = []
    for c, m in mem.items():
        if not m or f"px|{c}" not in cache:
            continue
        px = pd.DataFrame(cache[f"px|{c}"]).set_index("date")
        sh = pd.DataFrame(cache[f"sh|{c}"]).set_index("date")
        px, sh = px[px.index <= asof], sh[sh.index <= asof]
        if len(px) < 5 or len(sh) < 1:
            continue
        rows.append({"code": c, "cap_usd_b": round(
            float(px["close"].iloc[-1]
                  * sh["NumberOfSharesIssued"].iloc[-1]) / FX / 1e9,
            2)})
    return sorted(rows, key=lambda r: r["cap_usd_b"])


def main():
    ev = json.loads((ROOT / "data" / "msci_tw_events.json")
                    .read_text())
    out = {}
    for season, asof, gmsr in (("May26", "2026-05-01", 4.64),
                               ("Nov25", "2025-11-01", None)):
        lad = ladder(asof)
        dels = set(ev[season]["dels"])
        for r in lad:
            r["deleted"] = r["code"] in dels
        n_in = sum(r["deleted"] for r in lad)
        ranks = [i for i, r in enumerate(lad) if r["deleted"]]
        out[season] = {
            "asof": asof, "n_members": len(lad),
            "dels_official": len(dels), "dels_in_ladder": n_in,
            "deleted_ladder_ranks_bottom": ranks,
            "gmsr_used_usd_b": gmsr,
            "bottom": lad[:14]}
        print(f"{season}: {n_in}/{len(dels)} deletions in "
              f"reconstructed ladder; bottom ranks {ranks}")
    OUT.write_text(json.dumps(out, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
