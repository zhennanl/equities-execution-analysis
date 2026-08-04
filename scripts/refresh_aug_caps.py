"""Aug-2026 cap refresh — reprice the APAC universes to CURRENT.

Session 9i. The zero-call Aug pack diagnosis: caps were April-vintage
(the May-PIT cache) — three-plus months of price drift means boundary
crossers since April were invisible. This executes the cap-refresh leg
of the Aug-11 protocol a week early: for every cached universe name,
cap_now = cap_pit x (px_now / px_apr30), from batched yfinance
closes. Ratios cached resumably; names that fail to fetch keep ratio
1.0 and are LISTED (stated staleness, not silent).

What this does NOT fix (stated): names outside the cached universes
(new listings since April, risers from below the real-name floor)
remain invisible — the L0-breadth / L6-fast-entry gap. The two-sided
decade-consistency verdict now EXPOSES that gap instead of the pack
silently asserting quiet.

Usage: python scripts/refresh_aug_caps.py [fetch|status]
Writes: data/aug26_cap_refresh.json {ticker: ratio}
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "aug26_cap_refresh.json"
APR = "2026-04-24"
APR_END = "2026-05-01"


def universe_tickers():
    cache = json.loads(
        (ROOT / "data" / "pit_may26_asia_cache.json").read_text())
    return sorted(t for t, v in cache.items() if "cap_pit" in v)


def fetch(batch=15):
    import yfinance as yf
    tickers = universe_tickers()
    done = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = [t for t in tickers if t not in done]
    print(f"{len(todo)} of {len(tickers)} tickers missing")
    for i in range(0, len(todo), batch):
        chunk = todo[i:i + batch]
        try:
            apr = yf.download(chunk, start=APR, end=APR_END,
                              interval="1d", progress=False,
                              auto_adjust=False)["Close"]
            now = yf.download(chunk, period="5d", interval="1d",
                              progress=False,
                              auto_adjust=False)["Close"]
        except Exception as e:                        # noqa: BLE001
            print("batch fail", str(e)[:60])
            continue
        for t in chunk:
            try:
                a = float(apr[t].dropna().iloc[-1])
                b = float(now[t].dropna().iloc[-1])
                done[t] = round(b / a, 4) if a > 0 else 1.0
            except Exception:                         # noqa: BLE001
                done[t] = 1.0                # stale — listed below
        OUT.write_text(json.dumps(done))
        print(f"  ...{min(i + batch, len(todo))}/{len(todo)}",
              flush=True)
    stale = [t for t, r in done.items() if r == 1.0]
    print(f"refreshed {len(done)}; stale(ratio=1.0): {len(stale)}")


def status():
    done = json.loads(OUT.read_text()) if OUT.exists() else {}
    import statistics
    rs = [r for r in done.values() if r != 1.0]
    if rs:
        print(f"{len(done)} ratios; moved median "
              f"{statistics.median(rs):.3f}, "
              f"p10 {sorted(rs)[len(rs)//10]:.3f}, "
              f"p90 {sorted(rs)[-len(rs)//10]:.3f}")


if __name__ == "__main__":
    {"fetch": fetch, "status": status}[
        sys.argv[1] if len(sys.argv) > 1 else "status"]()
