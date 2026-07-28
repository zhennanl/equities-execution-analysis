#!/usr/bin/env python3
"""Live-data version of the MSCI Japan screener example (needs network —
run locally). Fetches market cap / float / ADV via yfinance for a ticker
list, models the universe tail, runs predict_msci under SAIR and QIR
rules, prints adds/deletes/watch + flow estimate.

    python scripts/run_msci_japan_screener.py                # built-in list
    python scripts/run_msci_japan_screener.py --tickers file.txt
    python scripts/run_msci_japan_screener.py --aum 21.2e9   # tracking AUM
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DEFAULT_TICKERS = ["7203.T", "6758.T", "8306.T", "6501.T", "9983.T",
                   "8035.T", "6857.T", "8058.T", "7974.T", "8316.T",
                   "6861.T", "9984.T", "4063.T", "8001.T", "9433.T",
                   "7011.T", "6098.T", "8766.T", "6902.T", "6503.T",
                   "6146.T", "6723.T", "6594.T", "5803.T", "9766.T",
                   "7013.T", "6920.T", "8136.T", "3659.T", "4755.T",
                   "285A.T", "7201.T", "4911.T", "4385.T", "2413.T"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tickers", help="file with one ticker per line")
    ap.add_argument("--aum", type=float, default=21.2e9,
                    help="tracking AUM for flow estimate (default EWJ)")
    ap.add_argument("--nonmembers", nargs="*", default=["285A.T", "4385.T"],
                    help="tickers assumed NOT in the index (verify!)")
    a = ap.parse_args(argv)
    tickers = (Path(a.tickers).read_text().split() if a.tickers
               else DEFAULT_TICKERS)
    import numpy as np
    import pandas as pd
    import yfinance as yf
    from agents.reconstitution import predict_msci, expected_flow, MSCIRules

    rows = []
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            info = tk.info
            cap = info.get("marketCap")
            ff = info.get("floatShares")
            so = info.get("sharesOutstanding")
            h = tk.history(period="60d", interval="1d")
            adv = float((h["Close"] * h["Volume"]).mean())
            if not cap:
                print(f"  {t}: no cap — skipped"); continue
            rows.append(dict(ticker=t, full_mktcap_usd=float(cap),
                             free_float_frac=(ff / so if ff and so else 0.7),
                             adv_usd=adv, atvr=1.0))
            print(f"  {t}: cap {cap/1e9:.1f}B ff "
                  f"{rows[-1]['free_float_frac']:.2f} adv {adv/1e6:.0f}M")
        except Exception as e:
            print(f"  {t}: fetch failed ({e}) — skipped")
    u = pd.DataFrame(rows)
    # model the universe tail (the GMSR lesson: full universe or bust)
    rng = np.random.default_rng(7)
    caps = np.exp(rng.uniform(np.log(0.5e9), np.log(12e9), 350))
    tail = pd.DataFrame([dict(ticker=f"TAIL{i:03d}", full_mktcap_usd=float(c),
                              free_float_frac=0.7, adv_usd=float(c) * 0.004,
                              atvr=1.0) for i, c in enumerate(caps)])
    u = pd.concat([u, tail], ignore_index=True)
    members = set(u["ticker"]) - set(a.nonmembers) - set(
        tail.loc[tail.full_mktcap_usd < 3e9, "ticker"])
    for review in ("SAIR", "QIR"):
        r = predict_msci(u, members, MSCIRules(review=review))
        named = lambda d: d[~d["ticker"].str.startswith("TAIL")] if len(d) else d
        print(f"\n=== {review}: GMSR ${r['gmsr_usd']/1e9:.1f}B | add ≥ "
              f"${r['add_threshold_usd']/1e9:.1f}B ===")
        for k in ("adds", "deletes", "watchlist"):
            n = named(r[k])
            print(f"{k}: " + (n.to_string(index=False) if len(n) else "(none named)"))
    qir = predict_msci(u, members, MSCIRules(review="QIR"))
    chg = [t for t in list(qir["adds"].get("ticker", []))
           if not t.startswith("TAIL")]
    if chg:
        print("\nFlow (AUM lower bound):")
        print(expected_flow(u, chg, passive_aum_usd=a.aum).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
