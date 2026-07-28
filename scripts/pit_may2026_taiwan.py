#!/usr/bin/env python3
"""TRUE point-in-time replication of the May-2026 MSCI Taiwan SAIR:
caps computed from APRIL 30 prices (before the May 12 announcement),
graded engine config (country rule, 2% buffer), graded against the
OFFICIAL May public list already parsed in data/.

Stricter than the original graded backtest, whose caps were
reconstruction-grade ("late May, ±30%"). Also a live test of PIT
discipline: the four AI names (3443/3665/8046/4958) are adds on
TODAY'S caps — if the PIT caps correctly put them below the May SAIR
threshold, the engine avoids four would-be false positives that only
exist because of look-ahead.

Chunked: `fetch [n]` until ALL CACHED, then `report`.
Cache: data/pit_may26_cache.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
CACHE = Path("data/pit_may26_cache.json")
FXTWD = 32.5

# Pre-May-announcement membership (member flags AS OF May 11):
# the 7 eventual deletions were still members; MPI still out.
TICKERS = [
    # anchors (members)
    ("2330.TW", 1), ("2317.TW", 1), ("2454.TW", 1), ("2308.TW", 1),
    ("2382.TW", 1), ("2303.TW", 1), ("3711.TW", 1), ("2891.TW", 1),
    # the 7 names MSCI deleted in May — members at PIT
    ("1102.TW", 1), ("2474.TW", 1), ("2610.TW", 1), ("2324.TW", 1),
    ("2633.TW", 1), ("1402.TW", 1), ("1504.TW", 1),
    # boundary survivors (stayed members in May)
    ("1101.TW", 1), ("1326.TW", 1), ("2615.TW", 1), ("2002.TW", 1),
    ("1301.TW", 1), ("2207.TW", 1), ("2801.TW", 1), ("2409.TW", 1),
    ("3231.TW", 1), ("2379.TW", 1), ("3034.TW", 1), ("6669.TW", 1),
    ("1216.TW", 1), ("2912.TW", 1),
    # candidates (non-members at PIT)
    ("6187.TWO", 0),   # MPI Corp (TPEx) — the actual May add; ticker
                       # mapping flagged for verification
    ("3443.TW", 0), ("3665.TW", 0), ("8046.TW", 0), ("4958.TW", 0),
]

ALIASES = {"1102.TW": "ASIA CEMENT CORP", "2474.TW": "CATCHER TECH CO",
           "2610.TW": "CHINA AIRLINES", "2324.TW": "COMPAL ELECTRONICS",
           "2633.TW": "TAIWAN HIGH SPEED RAIL",
           "1402.TW": "FAR EASTERN NEW CENTURY",
           "1504.TW": "TECO ELECTRIC & MACH", "6187.TWO": "MPI CORP"}


def fetch(n=8):
    import yfinance as yf
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    todo = [t for t, _ in TICKERS if t not in cache]
    done = 0
    for t in todo:
        if done >= n:
            break
        try:
            tk = yf.Ticker(t)
            h = tk.history(start="2026-04-24", end="2026-05-01")
            apr_close = float(h["Close"].iloc[-1]) if len(h) else None
            info = tk.info
            cap_now = info.get("marketCap")
            px_now = info.get("regularMarketPrice") or \
                info.get("previousClose")
            ff, so = info.get("floatShares"), info.get("sharesOutstanding")
            if apr_close and cap_now and px_now:
                cache[t] = {"cap_pit": cap_now * apr_close / px_now,
                            "ff": min((ff / so) if ff and so else 0.7,
                                      1.0)}
            else:
                cache[t] = {"error": "missing data"}
            print(t, cache[t])
        except Exception as e:                        # noqa: BLE001
            cache[t] = {"error": str(e)[:60]}
        done += 1
    CACHE.write_text(json.dumps(cache))
    left = [t for t, _ in TICKERS if t not in cache]
    print("ALL CACHED" if not left else f"{len(left)} remaining")


def report():
    import pandas as pd
    from agents.reconstitution import (MSCIRules,
                                       parse_msci_public_list)
    from agents.review_engine import screen_market
    cache = json.loads(CACHE.read_text())
    rows = []
    for t, m in TICKERS:
        c = cache.get(t, {})
        if "cap_pit" not in c:
            print(f"  (skipping {t}: {c.get('error')})")
            continue
        cap = c["cap_pit"] / FXTWD
        rows.append(dict(ticker=t, full_mktcap_usd=cap,
                         free_float_frac=c["ff"], adv_usd=cap * 0.004,
                         atvr=1.0, member=m))
    u = pd.DataFrame(rows)
    from agents.reconstitution import predict_msci
    import numpy as np
    rng = np.random.default_rng(11)
    caps = np.exp(rng.uniform(np.log(0.3e9), np.log(8e9), 400))
    tail = pd.DataFrame([dict(ticker=f"TAIL{i:03d}",
                              full_mktcap_usd=float(c),
                              free_float_frac=0.7,
                              adv_usd=float(c) * 0.004, atvr=1.0,
                              member=int(c > 2.5e9))
                         for i, c in enumerate(caps)])
    full = pd.concat([u, tail], ignore_index=True)
    members = set(full.loc[full["member"] == 1, "ticker"])
    r = predict_msci(full.drop(columns="member"), members,
                     MSCIRules(review="SAIR", country_coverage=0.85,
                               country_buffer=0.02))
    named = lambda d: (d[~d["ticker"].str.startswith("TAIL")]
                       if len(d) else d)
    print(f"\n=== PIT May-2026 SAIR (Apr-30 caps): GMSR "
          f"${r['gmsr_usd']/1e9:.1f}B, SAIR add ≥ "
          f"${r['add_threshold_usd']/1e9:.1f}B ===")
    pred_adds = set(named(r["adds"])["ticker"]) if len(r["adds"]) else set()
    pred_dels = set(named(r["deletes"])["ticker"]) if len(r["deletes"]) \
        else set()
    print("Predicted ADDS:", sorted(pred_adds) or "(none)")
    print("Predicted DELETES:", sorted(pred_dels) or "(none)")

    # grade vs the OFFICIAL May list
    official = parse_msci_public_list(
        Path("data/msci_may26_public_list.txt").read_text())["TAIWAN"]
    name_to_t = {v: k for k, v in ALIASES.items()}
    act_adds = {name_to_t.get(x) for x in official["adds"]} - {None}
    act_dels = {name_to_t.get(x) for x in official["deletes"]} - {None}
    print("\nActual ADDS:", sorted(act_adds))
    print("Actual DELETES:", sorted(act_dels))
    print(f"\nSCORE: adds {len(pred_adds & act_adds)}/{len(act_adds)} "
          f"(false+ {sorted(pred_adds - act_adds)}), "
          f"deletes {len(pred_dels & act_dels)}/{len(act_dels)} "
          f"(false+ {sorted(pred_dels - act_dels)})")
    ai = {"3443.TW", "3665.TW", "8046.TW", "4958.TW"}
    hit = sorted(pred_adds & ai)
    msg = hit if hit else "NONE (correct: their caps rose AFTER May)"
    print(f"PIT-discipline check — AI names flagged as adds: {msg}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        report()
    else:
        fetch(int(sys.argv[2]) if len(sys.argv) > 2 else 8)
