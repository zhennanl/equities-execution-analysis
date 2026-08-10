#!/usr/bin/env python3
"""Aug-2026 MSCI QIR pre-run — the pre-registration draft, run on
whatever markets have a validated boundary universe (honesty rule: no
universe file, no call).

Chunked + cached (45s sandbox limit): run repeatedly until ALL CACHED,
then with `report` to emit the per-market screen.

Markets covered live: Taiwan, Korea, Japan (boundary universes from the
graded May/June work, caps refreshed via yfinance TODAY).
Markets NOT covered: CN/HK/SG/IN/TH/MY/ID/PH -> explicit NO-CALL.

Usage:
  python scripts/run_qir_aug2026.py fetch [n]   # cache n tickers
  python scripts/run_qir_aug2026.py report      # run screens
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
CACHE = Path("data/qir_universe_cache.json")

# Boundary universes: members near the deletion zone + large non-members
# near the add zone + anchors, from the graded May/June reconstructions.
# (m = current Standard member, best knowledge post-May-SAIR)
UNIVERSES = {
    "Taiwan": [
        # anchors (members)
        ("2330.TW", 1), ("2317.TW", 1), ("2454.TW", 1), ("2308.TW", 1),
        ("2382.TW", 1), ("2303.TW", 1), ("3711.TW", 1), ("2891.TW", 1),
        # deletion-zone members (May survivors + boundary)
        ("1101.TW", 1), ("1326.TW", 1), ("2615.TW", 1), ("2002.TW", 1),
        ("1301.TW", 1), ("2207.TW", 1), ("9910.TW", 0), ("2801.TW", 1),
        # 9910 Feng Tay: DELETED at Feb-2026 QIR (our Feb truth set) —
        # corrected from member=1 after the May-list cross-check
        ("2409.TW", 1), ("2610.TW", 0),   # ChinaAir deleted in May
        # add candidates (non-members, big risers incl. Jun TW50 adds)
        ("3443.TW", 0), ("3665.TW", 0), ("8046.TW", 0), ("4958.TW", 0),
        ("3231.TW", 1), ("2379.TW", 1), ("3034.TW", 1), ("6669.TW", 1),
        ("1216.TW", 1), ("2912.TW", 1),
    ],
    "Korea": [
        ("005930.KS", 1), ("000660.KS", 1), ("373220.KS", 1),
        ("207940.KS", 1), ("005380.KS", 1), ("051910.KS", 1),
        # deletion zone (May survivors)
        ("003490.KS", 1), ("034730.KS", 1), ("011170.KS", 1),
        ("090430.KS", 1), ("086790.KS", 1),
        # add candidates incl. the May false-positive control
        ("277810.KS", 0),   # Rainbow Robotics (float-blocked in May)
        ("042700.KS", 1), ("112610.KS", 0), ("058470.KS", 0),
    ],
    "Japan": [
        ("7203.T", 1), ("8035.T", 1), ("6857.T", 1), ("6758.T", 1),
        ("8306.T", 1), ("9984.T", 1),
        # boundary members from the Aug screener case study
        ("6146.T", 1), ("6920.T", 1), ("8136.T", 1), ("9766.T", 1),
        ("7013.T", 1), ("6723.T", 1), ("5803.T", 1),
        # candidates
        ("285A.T", 0), ("4385.T", 0), ("3659.T", 0), ("4755.T", 0),
        ("6594.T", 1), ("4911.T", 1),
    ],
}

FX = {"Taiwan": 32.5, "Korea": 1385.0, "Japan": 155.0}  # local->USD approx


def fetch(n=8):
    import yfinance as yf
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    todo = [(mkt, t, m) for mkt, lst in UNIVERSES.items()
            for t, m in lst if t not in cache]
    done = 0
    for mkt, t, m in todo:
        if done >= n:
            break
        try:
            tk = yf.Ticker(t)
            info = tk.info
            cap = info.get("marketCap")
            ff, so = info.get("floatShares"), info.get("sharesOutstanding")
            if not cap:
                cache[t] = {"error": "no cap"}
            else:
                cache[t] = {"mkt": mkt, "member": m,
                            "cap_usd": float(cap),
                            "ff": (ff / so if ff and so else 0.7)}
            done += 1
            print(f"{t}: {cache[t]}")
            time.sleep(0.4)
        except Exception as e:                        # noqa: BLE001
            cache[t] = {"error": str(e)[:80]}
            done += 1
    CACHE.write_text(json.dumps(cache), encoding="utf-8")
    left = len([1 for mkt, lst in UNIVERSES.items()
                for t, m in lst if t not in cache])
    print("ALL CACHED" if not left else f"{left} remaining")


def report():
    import numpy as np
    import pandas as pd
    from agents.reconstitution import MSCIRules, predict_msci
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    out = {}
    for mkt, lst in UNIVERSES.items():
        rows = []
        fx = FX[mkt]
        for t, m in lst:
            c = cache.get(t, {})
            if "cap_usd" not in c:
                continue
            cap = c["cap_usd"] / fx        # yfinance returns LOCAL ccy
            rows.append(dict(ticker=t, full_mktcap_usd=cap,
                             free_float_frac=c["ff"],
                             adv_usd=cap * 0.004, atvr=1.0,
                             member=c["member"]))
        u = pd.DataFrame(rows)
        # model the full-universe tail (the recurring GMSR lesson)
        rng = np.random.default_rng(11)
        caps = np.exp(rng.uniform(np.log(0.3e9), np.log(8e9), 400))
        tail = pd.DataFrame([dict(ticker=f"TAIL{i:03d}",
                                  full_mktcap_usd=float(c),
                                  free_float_frac=0.7,
                                  adv_usd=float(c) * 0.004, atvr=1.0,
                                  member=int(c > 2.5e9))
                             for i, c in enumerate(caps)])
        u = pd.concat([u, tail], ignore_index=True)
        members = set(u.loc[u["member"] == 1, "ticker"])
        r = predict_msci(u.drop(columns="member"), members,
                         MSCIRules(review="QIR"))
        named = lambda d: (d[~d["ticker"].str.startswith("TAIL")]
                           if len(d) else d)
        out[mkt] = {"gmsr": r["gmsr_usd"],
                    "add_thr": r["add_threshold_usd"],
                    "adds": named(r["adds"]),
                    "deletes": named(r["deletes"]),
                    "watch": named(r["watchlist"]),
                    "n_real": len(rows)}
        print(f"\n===== {mkt} (QIR rules, {len(rows)} real names + "
              f"modeled tail) =====")
        print(f"GMSR ${r['gmsr_usd']/1e9:.1f}B | QIR add threshold "
              f"${r['add_threshold_usd']/1e9:.1f}B "
              f"(1.8x) | delete < ${0.5*r['gmsr_usd']/1e9:.1f}B")
        for k in ("adds", "deletes", "watch"):
            d = out[mkt][k]
            print(f"{k.upper()}: " +
                  (d.to_string(index=False) if len(d) else "(none)"))
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        report()
    else:
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
        fetch(n)


# ──────────────── 7x: verify mode (membership ledger reconciliation) ──
TW_ALIASES = {  # ticker -> name as it appears in MSCI public lists
    "9910.TW": "FENG TAY ENTERPRISE CO", "2610.TW": "CHINA AIRLINES",
    "1102.TW": "ASIA CEMENT CORP", "2474.TW": "CATCHER TECH CO",
    "2324.TW": "COMPAL ELECTRONICS", "2002.TW": "CHINA STEEL",
    "1301.TW": "FORMOSA PLASTICS", "2207.TW": "HOTAI MOTOR",
    "1101.TW": "TAIWAN CEMENT", "1326.TW": "FORMOSA CHEM & FIBRE",
}


def verify():
    from pathlib import Path
    from agents.reconstitution import (parse_msci_public_list,
                                       reconcile_membership)
    ledgers = [parse_msci_public_list(
        Path(f"data/msci_{p}_public_list.txt").read_text(encoding="utf-8"))
        for p in ("feb26", "may26")]
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    members = {}
    for t, m in UNIVERSES["Taiwan"]:
        if t in TW_ALIASES and "cap_usd" in cache.get(t, {}):
            members[TW_ALIASES[t]] = bool(cache[t]["member"])
    v = reconcile_membership(members, ledgers, "TAIWAN")
    if v:
        print("MEMBERSHIP VIOLATIONS (fix before committing calls):")
        for x in v:
            print(f"  {x['name']}: {x['type']} -> {x['fix']}")
    else:
        print("Taiwan membership reconciled vs Feb+May official lists "
              "— no violations.")


if "verify" in sys.argv:
    verify()
