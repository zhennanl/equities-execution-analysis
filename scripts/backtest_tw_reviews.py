#!/usr/bin/env python3
"""TW index-review BACKTEST harness (session 8u) — the first slice
of the 2015->now program, built on the official history layer.

Honest architecture, stated up front:
- ANSWER KEYS: known for Feb/May-2026 (official MSCI lists). For
  earlier events, keys are RECONSTRUCTED by the event-print
  detector (names printing MSCI-class volume on the effective
  close) — so the detector is VALIDATED on the known events first,
  and its measured precision bounds every reconstructed grade.
- PIT CAPS: close(vintage) x shares(current) — share-count drift
  stated; acceptable at 1-2y lookback, degrading beyond.
- FTSE TW50: detector is UNRELIABLE for FTSE-class prints (2-5x
  daily, inside news-day noise) -> FTSE backtest waits for TIP
  answer keys (manual collection path). MSCI-class prints (>=6x)
  detect cleanly.

Usage: detect | shares | predict EVENT | report
Cache: data/tw_backtest.json
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.backfill_tw_history import load as load_hist  # noqa

CACHE = Path("data/tw_backtest.json")

# MSCI TW review events: (label, review_kind, print-day candidates)
EVENTS = [
    ("2025-08 QIR", "QIR", ["20250828", "20250829"]),
    ("2025-11 SAIR", "SAIR", ["20251127", "20251128"]),
    ("2026-02 QIR", "QIR", ["20260225", "20260226"]),   # KNOWN key
]
KNOWN_KEYS = {
    "2026-02 QIR": {"dels": {"2105", "1476", "9910", "8464"},
                    "adds": set()},     # add ticker unmapped (HONPRE)
}
# Detector rule, iterated on the KNOWN keys (log in backtest doc):
# it1: t>=6, val>=1B -> recall 4/4+7/7, precision poor (6 false+)
# it2: t>=12 REJECTED out-of-sample (3 true May dels at 8.4-11.9x)
# it3: t>=6 AND value>=4B (true names sit near the GMSR -> big
#      prints; smallcap flow is small) AND limit-locked names tagged
#      SUSPECT (a +-10% lock = news, not index flow) ->
#      Feb: exactly the 4 trues; May: 7/7 recall preserved
T_THR, VAL_THR, LIMIT_LOCK = 6.0, 4_000_000_000, 9.4


def _num(x):
    try:
        return float(x)
    except Exception:
        return None


def detect_event(quotes, candidates):
    """Pick the print day (max flagged names) and return detected
    change set with direction from the print-day close move."""
    dates = sorted(quotes)
    best = None
    for cand in candidates:
        if cand not in quotes:
            continue
        prior = [d for d in dates if d < cand][-6:-1]
        if len(prior) < 4:
            continue
        flags = {}
        day = quotes[cand]
        prev_day = quotes[[d for d in dates if d < cand][-1]]
        for code, (vol, val, close) in day.items():
            if code.startswith("00"):          # ETFs: own rebalances
                continue
            if not vol or not val or val < VAL_THR:
                continue
            med = pd.Series(
                [quotes[d][code][0] for d in prior
                 if code in quotes[d] and quotes[d][code][0]]
            ).median()
            if not med or vol / med < T_THR:
                continue
            pc = prev_day.get(code, [None, None, None])[2]
            ret = (close / pc - 1) if pc and close else None
            suspect = (ret is not None
                       and abs(ret * 100) >= LIMIT_LOCK)
            flags[code] = {"t_mult": round(vol / med, 1),
                           "ret_pct": round(ret * 100, 1)
                           if ret is not None else None,
                           "suspect_limit_lock": suspect}
        if best is None or len(flags) > len(best[1]):
            best = (cand, flags)
    return best


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "report"
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    quotes = load_hist("quotes")

    if mode == "detect":
        det = cache.setdefault("detected", {})
        for label, kind, cands in EVENTS:
            r = detect_event(quotes, cands)
            if r:
                det[label] = {"print_day": r[0], "names": r[1]}
                print(f"{label}: print {r[0]}, "
                      f"{len(r[1])} names: {sorted(r[1])}")
        # validation against the known key
        for label, key in KNOWN_KEYS.items():
            got = set(cache["detected"].get(label, {})
                      .get("names", {}))
            truth = key["dels"] | key["adds"]
            print(f"VALIDATION {label}: recall "
                  f"{len(got & truth)}/{len(truth)}, "
                  f"false+ {sorted(got - truth)}")
        CACHE.write_text(json.dumps(cache), encoding="utf-8")
        return

    if mode == "predict":
        # vintage prediction for the 2025 events, graded against the
        # reconstructed keys (within-universe, coverage stated)
        from scripts.pit_may2026_asia import UNIVERSES
        from scripts.run_full_review_asia import pit_screen
        shares = json.loads(Path("data/tw_shares.json").read_text(encoding="utf-8"))
        pitc = json.loads(
            Path("data/pit_may26_asia_cache.json").read_text(encoding="utf-8"))
        FX = 32.5
        # membership back-roll: pre-May-2026 state, reverse Feb-2026
        # (the four deletions were members before Feb; add unmapped)
        base_mem = {t: m for t, m in UNIVERSES["Taiwan"]}
        for t in ("9910.TW",):        # in-universe Feb deletion
            if t in base_mem:
                base_mem[t] = 1       # was a member before Feb
        VINTAGES = {"2025-08 QIR": ("20250804", "QIR", 86),
                    "2025-11 SAIR": ("20251103", "SAIR", 86)}
        out = cache.setdefault("predictions", {})
        for label, (vd, kind, count) in VINTAGES.items():
            day = quotes.get(vd)
            if not day:
                print(label, "no vintage quotes")
                continue
            rows = []
            for t, mem in base_mem.items():
                code = t.split(".")[0]
                q = day.get(code)
                sh = shares.get(t)
                if not q or not sh or not q[2]:
                    continue
                cap = q[2] * sh / FX
                ff = min(pitc.get(t, {}).get("ff", 0.7), 1.0)
                adv = q[1] / FX          # day value as ADV proxy
                rows.append(dict(ticker=t, full_mktcap_usd=cap,
                                 free_float_frac=ff, adv_usd=adv,
                                 atvr=min(adv * 250 / (cap * ff), 5.0)
                                 if cap * ff else 1.0, member=mem))
            u = pd.DataFrame(rows)
            import scripts.run_full_review_asia as rfa
            old = rfa.PRE_COUNT["Taiwan"]
            rfa.PRE_COUNT["Taiwan"] = count
            s = pit_screen("Taiwan", u, review=kind)
            rfa.PRE_COUNT["Taiwan"] = old
            adds = sorted(s["adds"]["ticker"]) if len(s["adds"]) else []
            dels = sorted(s["deletes"]["ticker"]) \
                if len(s["deletes"]) else []
            det = {k for k, v in cache["detected"]
                   .get(label, {}).get("names", {}).items()
                   if not v.get("suspect_limit_lock")}
            covered = {t.split(".")[0] for t in u["ticker"]}
            out[label] = {
                "universe_n": len(u), "adds": adds, "dels": dels,
                "reconstructed_key": sorted(det),
                "key_in_universe": sorted(det & covered),
                "hits": sorted({d.split(".")[0] for d in dels
                                + adds} & det)}
            print(label, out[label])
        CACHE.write_text(json.dumps(cache), encoding="utf-8")
        return

    if mode == "report":
        det = cache.get("detected", {})
        for label, d in det.items():
            df = pd.DataFrame(d["names"]).T
            print(f"\n{label} (print {d['print_day']}):")
            print(df.to_string())


if __name__ == "__main__":
    main()
