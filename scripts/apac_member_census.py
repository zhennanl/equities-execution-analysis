"""APAC member census — caps + floats for every member, any market
(c-62). The Taiwan calculation, generalized.

For a chosen market: harvest each member's price, shares
outstanding and named-insider float via Yahoo (works across all
ten markets' suffixes), then report the TW-style reconciliation:
bottom-up float-adjusted sum vs the factsheet-implied denominator,
plus the bottom-of-ladder table (deletion-candidate region) with
the global corridor overlaid.

Resumable per market (data/apac_caps_cache.json). Runtimes:
most markets 2-10 min; China ~25 min (576 names).

Usage:
  python scripts/apac_member_census.py harvest Japan [--limit N]
  python scripts/apac_member_census.py report Japan
  Markets: Taiwan Japan Australia HongKong Korea China India
           Malaysia Indonesia Philippines
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CACHE = ROOT / "data" / "apac_caps_cache.json"


def suffix(mkt, code):
    c = str(code).strip()
    if mkt == "Japan":
        return [c + ".T"]
    if mkt == "Australia":
        return [c + ".AX"]
    if mkt == "HongKong":
        if c.isdigit():
            return [f"{int(c):04d}.HK"]
        return [c + ".SI", c]      # SGX lines (Jardine) + US ADRs
    if mkt == "Korea":
        return [c + ".KS", c + ".KQ"]
    if mkt == "Taiwan":
        return [c + ".TW", c + ".TWO"]
    if mkt == "India":
        return [c + ".NS", c + ".BO"]
    if mkt == "Malaysia":
        return [c + ".KL"]
    if mkt == "Indonesia":
        return [c + ".JK"]
    if mkt == "Philippines":
        return [c + ".PS"]
    if mkt == "China":
        if c.isdigit():
            if len(c) <= 5:
                return [f"{int(c):04d}.HK"]
            if c.startswith("6"):
                return [c + ".SS"]
            return [c + ".SZ"]
        return [c]
    return [c]


def members(mkt):
    d = json.loads((ROOT / "data" / "apac_members.json")
                   .read_text())["markets"][mkt]
    return d["standard_members"], d.get("names", {})


def harvest(mkt, limit=None):
    import yfinance as yf
    codes, _ = members(mkt)
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    mc = cache.setdefault(mkt, {})
    todo = [c for c in codes if c not in mc]
    if limit:
        todo = todo[:int(limit)]
    print(f"{mkt}: {len(todo)} to fetch of {len(codes)} members")
    def _resolve_extra(c):
        """Yahoo search fallback for exchange mnemonics that are
        not Yahoo symbols (Malaysia's Bursa codes, odd lines)."""
        import requests
        try:
            j = requests.get(
                "https://query1.finance.yahoo.com/v1/finance/search",
                params={"q": c, "quotesCount": 6},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15).json()
            sufs = {"Malaysia": ".KL", "Indonesia": ".JK",
                    "Philippines": ".PS", "India": ".NS"}
            want = sufs.get(mkt)
            for q in j.get("quotes", []):
                s = q.get("symbol", "")
                if want and s.endswith(want):
                    return [s]
        except Exception:                      # noqa: BLE001
            pass
        return []

    for i, c in enumerate(todo):
        got = None
        for sym in suffix(mkt, c) + _resolve_extra(c):
            try:
                info = yf.Ticker(sym).info
                shares = info.get("sharesOutstanding")
                px = (info.get("currentPrice")
                      or info.get("regularMarketPrice"))
                mcap = info.get("marketCap")
                if not shares or not (px or mcap):
                    continue
                cap_local = float(mcap) if mcap else \
                    float(px) * float(shares)
                # sanity: cap in listing ccy must be plausible
                if cap_local <= 0 or cap_local > 1e16:
                    continue
                got = {"sym": sym,
                       "shares": shares,
                       "insiders": info.get("heldPercentInsiders"),
                       "ccy": info.get("currency"),
                       "cap_local": cap_local}
                break
            except Exception:                  # noqa: BLE001
                continue
        mc[c] = got or {"sym": None}
        if (i + 1) % 8 == 0:
            tmp = CACHE.with_suffix(".tmp")
            tmp.write_text(json.dumps(cache))
            tmp.replace(CACHE)
            print(f"  {i+1}/{len(todo)}")
        time.sleep(0.35)
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache))
    tmp.replace(CACHE)
    ok = sum(1 for v in mc.values() if v.get("shares"))
    print(f"{mkt}: {ok}/{len(codes)} priced")


FX = {"JPY": 148.0, "AUD": 0.66, "HKD": 7.80, "KRW": 1385.0,
      "TWD": 32.5, "INR": 87.0, "MYR": 4.25, "IDR": 16300.0,
      "PHP": 57.0, "CNY": 7.15, "USD": 1.0}


def to_usd(v, ccy):
    r = FX.get(ccy or "USD", 1.0)
    return v * r if ccy == "AUD" else v / r if r != 1.0 else v


def report(mkt):
    codes, names = members(mkt)
    cache = json.loads(CACHE.read_text()).get(mkt, {})
    fs = json.loads((ROOT / "data" / "apac_factsheet_archive.json")
                    .read_text())[mkt]
    fsm = fs[sorted(fs)[-1]]
    rows, unpriced = [], []
    for c in codes:
        v = cache.get(c) or {}
        if not v.get("shares"):
            unpriced.append(c)
            continue
        cap = to_usd(v["cap_local"], v.get("ccy"))
        ins = v.get("insiders")
        ff = (max(min(1 - ins, 1.0), 0.05) if ins is not None
              else 0.6)
        rows.append({"code": c, "company": (names.get(c) or "")[:24],
                     "cap_usd_b": round(cap / 1e9, 2),
                     "ff": round(ff, 3),
                     "ff_src": "insiders" if ins is not None
                     else "default0.6",
                     "ffcap_usd_b": round(cap * ff / 1e9, 2)})
    rows.sort(key=lambda r: -r["cap_usd_b"])
    total_ff = sum(r["ffcap_usd_b"] for r in rows)
    implied = fsm["implied_denominator_busd"]
    idx_cap = fsm["index_float_cap_musd"] / 1000
    mem_ff = total_ff
    out = {"market": mkt, "n_priced": len(rows),
           "unpriced": unpriced,
           "members_float_sum_busd": round(mem_ff, 0),
           "factsheet_index_cap_busd": round(idx_cap, 0),
           "members_vs_factsheet":
           f"{mem_ff/idx_cap-1:+.1%}" if idx_cap else None,
           "implied_denominator_busd": implied,
           "corridor_busd": fsm["cutoff_corridor_busd"],
           "observed_boundary_musd": fsm["smallest_musd"],
           "bottom_ladder": rows[-12:][::-1]}
    p = ROOT / "data" / f"member_census_{mkt.lower()}.json"
    p.write_text(json.dumps({**out, "rows": rows}, indent=1))
    print(json.dumps({k: v for k, v in out.items()
                      if k != "bottom_ladder"}, indent=1))
    print("bottom of ladder (deletion-candidate region):")
    for r in out["bottom_ladder"]:
        print(f"  {r['code']:8s} {r['company']:24s} "
              f"${r['cap_usd_b']:7.2f}B ff {r['ff']}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    mkt = sys.argv[2]
    lim = (sys.argv[sys.argv.index("--limit") + 1]
           if "--limit" in sys.argv else None)
    if cmd == "harvest":
        harvest(mkt, lim)
    elif cmd == "report":
        report(mkt)
