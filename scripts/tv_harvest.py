"""TradingView harvest — per-name intraday bars for TW event names.

Session 9i. Source: tvdatafeed anonymous (ToS-grey: research use,
cached aggressively, never a production dependency — see
HF_DATA_SOLUTIONS_TW.md). One call per code returns the FULL depth
(5000 bars): hourly reaches ~2022-06, 5m reaches ~2026-03.

Harvest set: every code in FTSE TW50 changes 2022-09 -> 2026-06
(codes from the official keys) + the MSCI TW registry (2025-26) +
the Aug-2026 shortlist names. 5m additionally for names in 2026
events.

Derived auction share (the method verified on 1102):
  auction_share = 1 - continuous_vol(TV, T-day) / official_daily_vol
Sanity per day: continuous < official (else the row is flagged and
EXCLUDED); official from STOCK_DAY cache (fetched on demand).

Usage: python scripts/tv_harvest.py [fetch|fetch5|derive|status]
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd                                    # noqa: E402

CACHE = ROOT / "data" / "tv_bars.json"
OUT = ROOT / "data" / "auction_shares_derived.json"
DOC = ROOT / "docs" / "case_studies" / "AUCTION_SHARES_DERIVED.md"

AUG_SHORTLIST = ["1101", "2207", "2002", "1326", "2324", "1504",
                 "2633", "1402"]


def event_set():
    """[(event, provider, eff_date, {code: side})] for 2022-06+."""
    from agents.time_machine import MSCI_TW
    keys = json.loads(
        (ROOT / "data" / "ftse_tw50_changes.json").read_text(
            encoding="utf-8"))     # Windows cp1252-safe
    out = []
    for k in sorted(keys):
        v = keys[k]
        if not v.get("effective") or v["effective"] < "2022-06":
            continue
        names = {a["code"]: "Buy" for a in v.get("adds", [])}
        names.update({d["code"]: "Sell" for d in v.get("dels", [])})
        if names:
            out.append((f"FTSE {k}", "FTSE", v["effective"], names))
    for k, v in MSCI_TW.items():
        names = {c: "Buy" for c in v["adds"]}
        names.update({c: "Sell" for c in v["dels"]})
        out.append((k, "MSCI", v["effective"], names))
    return out


def all_codes():
    codes = set(AUG_SHORTLIST)
    for _, _, _, names in event_set():
        codes |= set(names)
    return sorted(codes)


def codes_2026():
    codes = set(AUG_SHORTLIST)
    for _, _, eff, names in event_set():
        if eff >= "2026-01":
            codes |= set(names)
    return sorted(codes)


def _save(cache):
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache), encoding="utf-8")
    tmp.replace(CACHE)


def _fetch(codes, interval_key, budget=25):
    from tvDatafeed import Interval, TvDatafeed
    iv = {"60m": Interval.in_1_hour, "5m": Interval.in_5_minute}
    tv = TvDatafeed()
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    todo = [c for c in codes
            if interval_key not in cache.get(c, {})][:budget]
    print(f"{interval_key}: {len(todo)} codes to fetch")
    for c in todo:
        rows = None
        for exch in ("TWSE", "TPEX"):
            try:
                h = tv.get_hist(symbol=c, exchange=exch,
                                interval=iv[interval_key],
                                n_bars=5000)
                if h is not None and len(h):
                    rows = [[i.strftime("%Y-%m-%d %H:%M"),
                             float(r["open"]), float(r["close"]),
                             float(r["volume"])]
                            for i, r in h.iterrows()]
                    break
            except Exception:                          # noqa: BLE001
                continue
        cache.setdefault(c, {})[interval_key] = rows or []
        print(c, interval_key, len(rows or []), "bars", flush=True)
        _save(cache)
        time.sleep(0.8)


def fetch():
    _fetch(all_codes(), "60m")


def fetch5():
    _fetch(codes_2026(), "5m")


def status():
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    n60 = sum(1 for v in cache.values() if v.get("60m"))
    n5 = sum(1 for v in cache.values() if v.get("5m"))
    print(f"{len(cache)} codes cached; 60m: {n60}, 5m: {n5}; "
          f"targets: {len(all_codes())} / {len(codes_2026())}")


# ---------------------------------------------------------- derivation
def _official_vol(code, day):
    sd = json.loads(
        (ROOT / "data" / "tw_history" / "stock_day.json").read_text(encoding="utf-8"))
    for m in sd.get(code, {}):
        for r in sd[code][m]:
            if r[0] == day:
                return float(r[1])
    return None


def derive():
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    rows = []
    for event, prov, eff, names in event_set():
        for code, side in names.items():
            bars = cache.get(code, {})
            # prefer 5m where it covers the day; else hourly
            src, sel = None, None
            for k in ("5m", "60m"):
                b = [r for r in (bars.get(k) or [])
                     if r[0].startswith(eff)]
                if b:
                    src, sel = k, b
                    break
            if not sel:
                continue
            cont = sum(r[3] for r in sel)
            off = _official_vol(code, eff)
            if off is None:
                rows.append({"event": event, "provider": prov,
                             "code": code, "side": side,
                             "t_day": eff, "src": src,
                             "flag": "NO-OFFICIAL"})
                continue
            if cont >= off:
                rows.append({"event": event, "provider": prov,
                             "code": code, "side": side,
                             "t_day": eff, "src": src,
                             "flag": "SANITY-FAIL cont>=official"})
                continue
            rows.append({
                "event": event, "provider": prov, "code": code,
                "side": side, "t_day": eff, "src": src,
                "cont_vol": int(cont), "official_vol": int(off),
                "auction_share": round(1 - cont / off, 3),
                "flag": "OK"})
    df = pd.DataFrame(rows)
    OUT.write_text(df.to_json(orient="records"), encoding="utf-8")
    ok = df[df["flag"] == "OK"]
    agg = ok.groupby(["provider", "side"])["auction_share"].agg(
        ["count", "median", "min", "max"]).round(3)
    print(f"{len(ok)} derived OK / {len(df)} rows "
          f"({(df['flag'] != 'OK').sum()} flagged)")
    print(agg.to_string())
    L = ["# Derived Per-Name Auction Shares — TW event T-days "
         "2022-2026\n",
         "*Session 9i. METHOD (verified on 1102): official daily "
         "volume (STOCK_DAY) minus TV continuous volume = the "
         "closing-auction print. Sanity rule enforced per row "
         "(continuous < official, else EXCLUDED and flagged). "
         "Source greyness + block-trade caveat per "
         "HF_DATA_SOLUTIONS_TW.md. This table grows the measured "
         "auction-share dataset from 17 hand points to "
         f"{len(ok)}.*\n",
         "## By class\n", agg.to_markdown(), "",
         "## All rows\n", df.to_markdown(index=False)]
    DOC.write_text("\n".join(L), encoding="utf-8")
    print("wrote", DOC)


if __name__ == "__main__":
    {"fetch": fetch, "fetch5": fetch5, "derive": derive,
     "status": status}[sys.argv[1] if len(sys.argv) > 1
                       else "status"]()
