"""Yahoo free-float harvest for the TW universe (c-122).

WHY: graded against the factsheet-implied FIFs, Yahoo's float
carries a 2.7% median absolute error vs 16.3% for the TDCC
bracket proxy (see MSCI_SIZE_SEGMENT_SPEC §3c). MSCI rounds FIF
to 2.5% steps above 25% float, so Yahoo is near the rulebook's
own resolution.

WHERE IT IS USED: only for the LARGE caps. §4b of the spec
measured that float error at the top of the ladder moves the
85%-coverage crossing hard, while tail error averages out.
Yahoo is per-name and rate-limited, so spending its cost on the
tail would be paying a lot for nothing.

Tier order in the final stack:
    factsheet-implied (top 10, exact)
  > Yahoo            (large caps, ~3%)
  > TDCC bracket-15  (everything else, complete)

CAVEAT: Yahoo's `float_shares` is a VENDOR ESTIMATE, not a
filing. It is wrong by 20% on Delta. Treat as a strong prior
that the factsheet overrides where the factsheet speaks.

Usage: py scripts\\tw_float_yahoo.py run [N]   (default 300)
Resumable: data/tw_float_yahoo.json
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "tw_float_yahoo.json"
UNI = ROOT / "data" / "tw_universe_pit.json"


def run(n=300, date="20260420"):
    import yfinance as yf
    u = json.loads(UNI.read_text(encoding="utf-8"))
    rows = u["dates"][date]["rows"]
    top = sorted(rows.items(),
                 key=lambda x: -(x[1].get("cap_usd_b") or 0))[:int(n)]
    cache = (json.loads(CACHE.read_text(encoding="utf-8"))
             if CACHE.exists() else {})
    todo = [(c, r) for c, r in top if c not in cache]
    print(f"{len(todo)} of {len(top)} to fetch", flush=True)
    ok = 0
    for i, (c, r) in enumerate(todo):
        sym = f"{c}.TW" if r["mkt"] == "twse" else f"{c}.TWO"
        val = None
        try:
            info = yf.Ticker(sym).get_info()
            fs = info.get("floatShares")
            so = info.get("sharesOutstanding") or r.get("shares")
            if fs and so:
                val = min(1.0, fs / so)
        except Exception:                          # noqa: BLE001
            pass
        cache[c] = round(val, 4) if val else None
        ok += bool(val)
        if (i + 1) % 20 == 0:
            CACHE.write_text(json.dumps(cache), encoding="utf-8")
            print(f"  {i+1}/{len(todo)} (resolved {ok})",
                  flush=True)
        time.sleep(0.35)
    CACHE.write_text(json.dumps(cache), encoding="utf-8")
    got = sum(1 for v in cache.values() if v)
    print(f"done: {got}/{len(cache)} resolved -> {CACHE.name}",
          flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    run(a[1] if len(a) > 1 else 300)
