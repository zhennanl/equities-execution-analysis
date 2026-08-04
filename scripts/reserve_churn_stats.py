#!/usr/bin/env python3
"""TW50 reserve-list conversion & churn statistics (session 8z) —
factor 6 of the pitch, MEASURED on a decade of official keys
(data/ftse_tw50_changes.json, 2016-2026).

Client-quotable outputs:
  1. Reserve conversion: P(added within 1 / 2 reviews | on the
     official reserve list) — the reserve list is FTSE's own watch
     zone; its measured conversion rate prices it.
  2. New-add persistence: P(deleted within k reviews | just added)
     — the one-review-resident rate (the 康霈 6919 class).
  3. Deletion round-trips: P(re-added within 4 reviews | deleted).
Output: data/tw50_stats.json + docs/case_studies/TW50_RESERVE_CHURN_STATS.md
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

KEYS = json.loads(Path("data/ftse_tw50_changes.json").read_text())


def quarterly_series():
    """Ordered quarterly events (skip ad-hoc + NOT FOUND)."""
    out = []
    for k in sorted(KEYS):
        v = KEYS[k]
        if "adds" not in v or k.endswith("-adhoc"):
            continue
        out.append({
            "q": k,
            "adds": {x["code"] for x in v["adds"]},
            "dels": {x["code"] for x in v["dels"]},
            "reserve": {x["code"] for x in v.get("reserve", [])}})
    return out


def main():
    ev = quarterly_series()
    n = len(ev)
    # 1. reserve conversion within 1 and 2 reviews
    res_n = conv1 = conv2 = 0
    for i, e in enumerate(ev[:-1]):
        nxt1 = ev[i + 1]["adds"]
        nxt2 = nxt1 | (ev[i + 2]["adds"] if i + 2 < n else set())
        for c in e["reserve"]:
            res_n += 1
            conv1 += c in nxt1
            conv2 += c in nxt2
    # 2. new-add persistence: deleted within 2 / 4 reviews
    add_n = gone2 = gone4 = 0
    for i, e in enumerate(ev):
        d2 = set().union(*(x["dels"] for x in ev[i + 1:i + 3])) \
            if i + 1 < n else set()
        d4 = set().union(*(x["dels"] for x in ev[i + 1:i + 5])) \
            if i + 1 < n else set()
        for c in e["adds"]:
            if i + 4 < n:                 # full observation window
                add_n += 1
                gone2 += c in d2
                gone4 += c in d4
    # 3. deletion round-trips within 4 reviews
    del_n = back4 = 0
    for i, e in enumerate(ev):
        a4 = set().union(*(x["adds"] for x in ev[i + 1:i + 5])) \
            if i + 1 < n else set()
        for c in e["dels"]:
            if i + 4 < n:
                del_n += 1
                back4 += c in a4
    stats = {
        "events": n, "span": f"{ev[0]['q']} -> {ev[-1]['q']}",
        "reserve_slots_observed": res_n,
        "reserve_conv_1r": round(conv1 / res_n, 3) if res_n else None,
        "reserve_conv_2r": round(conv2 / res_n, 3) if res_n else None,
        "adds_observed": add_n,
        "add_deleted_within_2r": round(gone2 / add_n, 3)
        if add_n else None,
        "add_deleted_within_4r": round(gone4 / add_n, 3)
        if add_n else None,
        "dels_observed": del_n,
        "del_readded_within_4r": round(back4 / del_n, 3)
        if del_n else None}
    Path("data/tw50_stats.json").write_text(json.dumps(stats))
    L = ["# TW50 Reserve-Conversion & Churn — Measured on a Decade "
         "of Official Keys",
         f"*Session 8z. {n} quarterly reviews {stats['span']} "
         "(official TIP announcements). These are the numbers that "
         "price FTSE's own watch zone — factor 6 of the pitch, "
         "measured instead of asserted.*", "",
         f"| Statistic | Value | n |",
         f"|---|---|---|",
         f"| P(ADDED within 1 review \\| on official reserve list) "
         f"| **{stats['reserve_conv_1r']:.0%}** | "
         f"{res_n} reserve-slots |",
         f"| P(ADDED within 2 reviews \\| reserve) | "
         f"**{stats['reserve_conv_2r']:.0%}** | {res_n} |",
         f"| P(new add DELETED within 2 reviews) | "
         f"**{stats['add_deleted_within_2r']:.0%}** | {add_n} adds |",
         f"| P(new add DELETED within 4 reviews) | "
         f"**{stats['add_deleted_within_4r']:.0%}** | {add_n} |",
         f"| P(deletion RE-ADDED within 4 reviews) | "
         f"**{stats['del_readded_within_4r']:.0%}** | "
         f"{del_n} deletions |", "",
         "**How the client uses these:** the reserve list is not "
         "decoration — its conversion rate is the probability your "
         "reserve-name position becomes index flow next quarter. "
         "The one-review-resident rate prices the risk that a "
         "fresh add's flow REVERSES at the next review (the 6919 "
         "class: added 2025-09, deleted 2026-06). Round-trip rates "
         "price fade-the-deletion trades. All three feed the "
         "hazard framing the deletion watch zone already uses.",
         "",
         "*Basis: official adds/dels/reserve lists only; ad-hoc "
         "corporate-action changes excluded; persistence windows "
         "require full observation (last 4 reviews' adds are not "
         "graded for persistence).*"]
    Path("docs/case_studies/TW50_RESERVE_CHURN_STATS.md").write_text(
        "\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
