"""Decade MSCI key statistics — all APAC markets, 44 quarters.

Session 9i, improvement plan item 2 (PREDICTION_ENGINE_REVIEW_2026
§6). Computable from ANSWER KEYS ALONE (no PIT universes needed):

  * CADENCE (validates L4 decade-wide): share of deletions/additions
    occurring at SAIRs vs QIRs, per market — the review-cadence rule
    predicts SAIR-heavy deletion batching.
  * CHURN (extends L5/L9 base rates): P(add is deleted within 4
    reviews), P(delete is re-added within 4 reviews) — measured per
    market on the full decade instead of one TW cohort.
  * BATCHING: the wave quarters (top deletion seasons) per market.
  * EXPECTED-COUNT DISTRIBUTIONS: per market x review type, the
    quartiles of add/del counts — the consistency check a fresh
    prediction pack is scored against (an Aug QIR pack calling 12
    TW deletions would sit far outside the decade distribution).

Output: data/msci_decade_stats.json + printed tables.
Usage: python scripts/msci_key_stats.py
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "data" / "msci_archive"
OUT = ROOT / "data" / "msci_decade_stats.json"

APAC = ["TAIWAN", "CHINA", "JAPAN", "HONG KONG", "KOREA", "INDIA",
        "MALAYSIA", "INDONESIA", "THAILAND", "PHILIPPINES",
        "SINGAPORE", "AUSTRALIA", "NEW ZEALAND"]
SAIR_MONTHS = ("May", "Nov")


def season_key(stem):
    s = stem.replace("MSCI_", "").replace("_STPublicList", "")
    mon, yy = s[:3], s[3:]
    order = {"Feb": 1, "May": 2, "Aug": 3, "Nov": 4}
    return (2000 + int(yy)) * 10 + order[mon], s, \
        ("SAIR" if mon in SAIR_MONTHS else "QIR")


def ledgers():
    from agents.reconstitution import parse_msci_public_list
    rows = []
    for t in sorted(ARCH.glob("*STPublicList.txt")):
        k, season, rtype = season_key(t.stem)
        led = parse_msci_public_list(t.read_text(errors="ignore"))
        for c in APAC:
            d = led.get(c, {})
            rows.append({"k": k, "season": season, "rtype": rtype,
                         "market": c, "adds": d.get("adds", []),
                         "dels": d.get("deletes", [])})
    return sorted(rows, key=lambda r: r["k"])


def cadence(rows):
    df = pd.DataFrame([{**r, "n_add": len(r["adds"]),
                        "n_del": len(r["dels"])} for r in rows])
    out = {}
    for m, g in df.groupby("market"):
        tot_d = g["n_del"].sum()
        tot_a = g["n_add"].sum()
        sair_d = g[g["rtype"] == "SAIR"]["n_del"].sum()
        sair_a = g[g["rtype"] == "SAIR"]["n_add"].sum()
        if tot_d + tot_a == 0:
            continue
        qs = {}
        for rt, gg in g.groupby("rtype"):
            qs[rt] = {"del_q": [int(x) for x in
                               gg["n_del"].quantile(
                                   [.25, .5, .75, .9]).values],
                      "add_q": [int(x) for x in
                               gg["n_add"].quantile(
                                   [.25, .5, .75, .9]).values],
                      # P(any change) — the shortlist layer's anchor
                      "p_any_add": round(float(
                          (gg["n_add"] > 0).mean()), 3),
                      "p_any_del": round(float(
                          (gg["n_del"] > 0).mean()), 3),
                      "n_reviews": len(gg)}
        out[m] = {"total_adds": int(tot_a), "total_dels": int(tot_d),
                  "sair_del_share": round(sair_d / tot_d, 3)
                  if tot_d else None,
                  "sair_add_share": round(sair_a / tot_a, 3)
                  if tot_a else None, "counts": qs}
    return out


def churn(rows, k=4):
    """P(add deleted within k reviews) and P(delete re-added)."""
    seqs = {}
    for r in rows:
        seqs.setdefault(r["market"], []).append(r)
    out = {}
    for m, seq in seqs.items():
        add_events = del_events = add_churned = del_reversed = 0
        for i, r in enumerate(seq):
            future = seq[i + 1:i + 1 + k]
            for nm in r["adds"]:
                if len(seq) - i > k:          # full window observable
                    add_events += 1
                    if any(nm in f["dels"] for f in future):
                        add_churned += 1
            for nm in r["dels"]:
                if len(seq) - i > k:
                    del_events += 1
                    if any(nm in f["adds"] for f in future):
                        del_reversed += 1
        if add_events + del_events == 0:
            continue
        out[m] = {
            "adds_observed": add_events, "dels_observed": del_events,
            "add_deleted_within_4": round(add_churned / add_events, 3)
            if add_events else None,
            "del_readded_within_4": round(del_reversed / del_events, 3)
            if del_events else None}
    return out


def waves(rows, top=3):
    df = pd.DataFrame([{"season": r["season"], "market": r["market"],
                        "n_del": len(r["dels"])} for r in rows])
    out = {}
    for m, g in df.groupby("market"):
        t = g.nlargest(top, "n_del")
        out[m] = [{"season": r["season"], "n_del": int(r["n_del"])}
                  for _, r in t.iterrows() if r["n_del"] > 0]
    return out


def main():
    rows = ledgers()
    n_seasons = len({r["season"] for r in rows})
    stats = {"n_reviews": n_seasons, "cadence": cadence(rows),
             "churn": churn(rows), "waves": waves(rows)}
    OUT.write_text(json.dumps(stats, indent=1), encoding="utf-8")
    c = stats["cadence"]
    print(f"{n_seasons} reviews parsed")
    print(f"{'market':13s} {'dels':>5s} {'SAIR%':>6s} "
          f"{'adds':>5s} {'SAIR%':>6s} {'add->del4':>9s} "
          f"{'del->add4':>9s}")
    for m in sorted(c, key=lambda x: -c[x]["total_dels"]):
        ch = stats["churn"].get(m, {})
        print(f"{m:13s} {c[m]['total_dels']:5d} "
              f"{(c[m]['sair_del_share'] or 0) * 100:5.0f}% "
              f"{c[m]['total_adds']:5d} "
              f"{(c[m]['sair_add_share'] or 0) * 100:5.0f}% "
              f"{str(ch.get('add_deleted_within_4')):>9s} "
              f"{str(ch.get('del_readded_within_4')):>9s}")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
