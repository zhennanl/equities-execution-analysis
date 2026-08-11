#!/usr/bin/env python3
"""Tracker-by-tracker replication of the August order (c-375).

    py scripts\\tw_tracker_replication.py

WHAT THIS IS. The identity prices the whole USD 45bn named-ETF
pool at one weight per candidate. This file prices it FUND BY
FUND — each named tracker buys at the weight of ITS OWN index
variant — and sums, which is what an index desk's pro-forma
does. The mandate pool (the x1.33) has no fund list by
construction, so this replicates the ETF slice only.

THE ONE REAL DIFFERENCE FROM THE IDENTITY: CAPPING. USD 13.4bn
of the pool tracks capped MSCI Taiwan variants (25/50, 20/35).
Capping takes TSMC — 58.07% of the uncapped index, from the
factsheet on disk — down to the cap, and redistributes its
excess weight pro-rata across every other member. A non-TSMC
addition therefore enters a CAPPED variant at

    w_capped = w_uncapped x (1 - cap) / (1 - w_TSMC)

about 1.8x its uncapped weight for 25/50 and 1.9x for 20/35.
The identity prices those funds at the uncapped weight, so the
identity UNDERSTATES demand for non-TSMC additions — which is
the conservative direction, and this file measures by how much.

DECLARED ASSUMPTIONS (each carried in the output):
  * Taiwan's share of each Standard index, used to turn a
    fund's total AUM into its Taiwan sleeve: EM 21.5%,
    EM ex-China 28.5%, ACWI 2.3% (MSCI factsheets, Jul-2026 —
    read off the published sheets, not archived here).
  * the rule caps: 25% and 20% for the 25/50 and 20/35
    variants; custom variants treated as their base variant.
  * IMI funds are EXCLUDED, as in the AUM build — a Standard
    promotion is not a new holding for an IMI tracker.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUM = ROOT / "data" / "tw_tracking_aum.json"
PB = ROOT / "data" / "tw_tracker_playbook.json"
FS = ROOT / "data" / "msci_factsheet_archive.json"
MAND = ROOT / "data" / "tw_mandate_size.json"
OUT = ROOT / "data" / "tw_tracker_replication.json"

# Taiwan's share of each Standard index the named funds track —
# the declared assumption that turns total fund AUM into its
# Taiwan sleeve. Sources: MSCI index factsheets, Jul-2026.
TW_SHARE = {
    "MSCI Emerging Markets": 0.215,
    "MSCI EM ex China": 0.285,
    "MSCI ACWI": 0.023,
}
RULE_CAP = {"MSCI Taiwan 25/50": 0.25,
            "MSCI Taiwan 20/35": 0.20,
            "MSCI Taiwan 20/35 Custom": 0.20,
            "MSCI Taiwan (uncapped)": None}


def main():
    for p in (AUM, PB, FS, MAND):
        if not p.exists():
            raise SystemExit(f"missing {p.name}")
    funds = json.loads(AUM.read_text(encoding="utf-8"))[
        "method1_bottom_up"]["funds"]
    pb = json.loads(PB.read_text(encoding="utf-8"))
    fs = json.loads(FS.read_text(encoding="utf-8"))
    fs_month = sorted(fs)[-1]
    w_tsmc = next(r["weight_pct"] for r in fs[fs_month]["top10"]
                  if "SEMICONDUCTOR" in r["name"]) / 100.0
    mand = json.loads(MAND.read_text(encoding="utf-8"))
    basis = mand["taiwan"]["estimate_always_buys_usd_b"]
    etf_named = mand["taiwan"]["always_buys_named_etf_usd_b"]

    cands = sorted(
        ((c, r) for c, r in pb["names"].items()
         if r.get("capacity_rank")),
        key=lambda kv: kv[1]["capacity_rank"])

    fund_rows, per_cand = [], {c: 0.0 for c, _ in cands}
    for f in funds:
        if f["bucket"] == "imi":
            continue
        idx = f["index"]
        if idx in RULE_CAP:            # a Taiwan variant
            sleeve = f["usd_bn"]
            cap = RULE_CAP[idx]
            amp = ((1 - cap) / (1 - w_tsmc)) if cap else 1.0
        else:                          # a Standard index
            share = TW_SHARE.get(idx)
            if share is None:
                continue
            sleeve = f["usd_bn"] * share
            amp = 1.0
        row = {"fund": f["fund"], "index": idx,
               "taiwan_sleeve_usd_bn": round(sleeve, 2),
               "weight_amplifier": round(amp, 3),
               "buys_usd_m": {}}
        for c, r in cands:
            usd_m = (r["index_weight_pct"] / 100 * amp
                     * sleeve * 1000)
            row["buys_usd_m"][c] = round(usd_m, 1)
            per_cand[c] += usd_m
        fund_rows.append(row)

    sleeve_total = round(sum(r["taiwan_sleeve_usd_bn"]
                             for r in fund_rows), 1)
    cand_out = []
    for c, r in cands:
        ident = r["index_weight_pct"] / 100 * etf_named * 1000
        cand_out.append({
            "code": c, "name": r["name"],
            "replicated_etf_usd_m": round(per_cand[c], 1),
            "identity_etf_usd_m": round(ident, 1),
            "ratio": round(per_cand[c] / ident, 3),
        })

    # c-377, Bill: FOLD THE CAPPING INTO THE FLOOR. The
    # replication is not only a cross-check — its capping
    # arithmetic is a refinement the floor can legitimately
    # absorb, because it prices the same registered pool more
    # precisely. The mandate slice (basis − ETF pool) stays at
    # uncapped weights — mandates benchmark Standard indexes —
    # which keeps the refined number a floor.
    _ratio = (cand_out[0]["ratio"] if cand_out else 1.0)
    eff_floor = round(etf_named * _ratio
                      + (basis - etf_named), 1)

    out = {
        "_what": "the August order rebuilt fund by fund — each "
                 "named ETF buys at ITS OWN variant's weight",
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "assumptions": {
            "tw_share_of_index": TW_SHARE,
            "rule_caps": {k: v for k, v in RULE_CAP.items() if v},
            "tsmc_uncapped_weight": round(w_tsmc, 4),
            "tsmc_weight_source": f"factsheet {fs_month} on disk",
            "imi_funds_excluded": True},
        "fund_sleeves_total_usd_bn": sleeve_total,
        "identity_etf_pool_usd_bn": etf_named,
        "identity_full_basis_usd_bn": basis,
        "effective_floor_usd_bn": {
            "value": eff_floor,
            "for": "a non-TSMC Standard addition",
            "how": f"ETF pool {etf_named}bn x the fund-by-fund "
                   f"capping ratio {_ratio:.2f} + the mandate "
                   f"slice {basis - etf_named:.0f}bn at "
                   f"uncapped weights",
            "note": "still a floor: every dollar in it is the "
                    "registered pool, priced more precisely; "
                    "the mandate slice conservatively takes no "
                    "capping amplification"},
        "funds": fund_rows,
        "candidates": cand_out,
        "reading": [
            "the ratio above 1 is the capping effect: 13.4bn "
            "of capped Taiwan funds buy a non-TSMC addition at "
            "~1.8-1.9x its uncapped weight, which the identity "
            "does not price — the identity errs low, and this "
            "measures by how much",
            "the mandate pool (the x1.33) has no fund list by "
            "construction; this replicates the ETF slice only"],
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"sleeves total {sleeve_total}bn vs identity ETF pool "
          f"{etf_named}bn  (TSMC uncapped {w_tsmc:.2%})")
    for r in cand_out:
        print(f"  {r['code']} {r['name'][:22]:24} replicated "
              f"USD {r['replicated_etf_usd_m']:6.0f}m vs identity "
              f"{r['identity_etf_usd_m']:6.0f}m  x{r['ratio']:.2f}")
    print(f"effective floor (capping folded): USD {eff_floor}bn")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
