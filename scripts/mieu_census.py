"""MIEU census — the Market Investable Equity Universe, computed
EXACTLY per GIMI screens, every listed security (c-55).

The final answer to "what is the denominator": instead of 150
named + modeled body, CENSUS the whole market —

  PHASE A  universe    all TWSE+TPEx 4-digit common equities
                       (ETFs/warrants/DR excluded) — ~1,750 names
  PHASE B  fundamentals per name: shares outstanding, foreign
                       holding + FOL room (FinMind Shareholding,
                       latest rows)
  PHASE C  tape        per name: 12m daily close/volume (FinMind
                       Price) -> price, full cap, 12m/3m ATVR,
                       trading-frequency
  PHASE D  floats      per name: named-insider float (yfinance);
                       tail defaults BANDED 0.5/0.7 where missing
  PHASE E  screens+sum GIMI: min size, float>=0.15, 12m ATVR>=15%
                       & 3m>=15%, 3m trading freq>=70%, foreign
                       room>=15% (new names) -> sum(ff-adj caps)
                       vs the factsheet-implied $3,745B

All phases RESUMABLE (data/mieu_cache.json, atomic). Designed to
run unattended: `python scripts/mieu_census.py harvest` loops all
phases politely (~2-4h total on the free tiers); `report` computes
whenever, using whatever coverage exists (coverage stated).

Sandbox note: run in chunks via `harvest --limit N`.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

API = "https://api.finmindtrade.com/api/v4/data"
CACHE = ROOT / "data" / "mieu_cache.json"
FX = 32.5
MIN_SIZE_USD = 0.2e9          # equity-universe min size approx


def _load():
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def _save(c):
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(c))
    tmp.replace(CACHE)


def universe():
    import requests
    c = _load()
    if "universe" in c:
        return c["universe"]
    rows = requests.get(API, params={"dataset": "TaiwanStockInfo"},
                        timeout=60).json()["data"]
    seen = {}
    for x in rows:
        sid = x.get("stock_id", "")
        if (sid.isdigit() and len(sid) == 4
                and not sid.startswith("00")
                and x.get("type") in ("twse", "tpex")):
            seen[sid] = {"code": sid, "name": x.get("stock_name"),
                         "mkt": x["type"]}
    c["universe"] = sorted(seen.values(), key=lambda r: r["code"])
    _save(c)
    return c["universe"]


class RateLimited(Exception):
    pass


def _get(dataset, sid, start, end):
    import os
    import requests
    params = {"dataset": dataset, "data_id": sid,
              "start_date": start, "end_date": end}
    tok = os.environ.get("FINMIND_TOKEN")
    if tok:
        params["token"] = tok
    r = requests.get(API, params=params, timeout=30)
    j = r.json()
    data = j.get("data", [])
    if not data:
        msg = str(j.get("msg", "")).lower()
        if r.status_code in (402, 429) or "limit" in msg \
                or "level" in msg:
            raise RateLimited(msg or str(r.status_code))
    return data


def purge_failures():
    """c-63: remove failure entries that the old version cached as
    permanent (shares/close None) so harvest retries them."""
    c = _load()
    nf = {k: v for k, v in c.get("fund", {}).items()
          if v.get("shares")}
    nt = {k: v for k, v in c.get("tape", {}).items()
          if v.get("close")}
    rf = len(c.get("fund", {})) - len(nf)
    rt = len(c.get("tape", {})) - len(nt)
    c["fund"], c["tape"] = nf, nt
    _save(c)
    print(f"purged {rf} empty fund entries, {rt} empty tape "
          f"entries; {len(nf)} fund / {len(nt)} tape REAL entries "
          "kept")


def harvest(limit=None):
    import datetime as dt
    import os
    uni = universe()
    c = _load()
    fund = c.setdefault("fund", {})
    tape = c.setdefault("tape", {})
    today = dt.date.today()
    y1 = str(today - dt.timedelta(days=380))
    done, backoffs = 0, 0
    if not os.environ.get("FINMIND_TOKEN"):
        print("NOTE: no FINMIND_TOKEN set — anonymous rate limits "
              "are low; a free registered token "
              "(finmindtrade.com) raises them substantially")
    for u in uni:
        sid = u["code"]
        if sid in fund and sid in tape:
            continue
        if limit and done >= int(limit):
            break
        try:
            if sid not in fund:
                rows = _get("TaiwanStockShareholding", sid,
                            str(today - dt.timedelta(days=10)),
                            str(today))
                if rows:
                    r = rows[-1]
                    fund[sid] = {
                        "shares": r["NumberOfSharesIssued"],
                        "foreign": r.get(
                            "ForeignInvestmentSharesRatio"),
                        "fol": r.get(
                            "ForeignInvestmentUpperLimitRatio")}
                # empty-but-not-rate-limited: leave UNCACHED so a
                # later run retries (never cache a failure)
                time.sleep(0.35)
            if sid not in tape:
                px = _get("TaiwanStockPrice", sid, y1, str(today))
                if px:
                    tape[sid] = {
                        "close": px[-1]["close"],
                        "days": len(px),
                        "traded_days_3m": sum(
                            1 for r in px[-63:]
                            if r["Trading_Volume"] > 0),
                        "val_12m": sum(r["Trading_money"]
                                       for r in px),
                        "val_3m": sum(r["Trading_money"]
                                      for r in px[-63:])}
                time.sleep(0.35)
            done += 1
            if done % 10 == 0:
                _save(c)
                print(f"  {done} this run | REAL totals: "
                      f"{len(fund)} fund / {len(tape)} tape "
                      f"of {len(uni)}")
        except RateLimited as rl:
            _save(c)
            backoffs += 1
            if backoffs > 20:
                print("rate-limited 20x — stopping; rerun later "
                      "(progress saved)")
                break
            print(f"rate-limited ({str(rl)[:40]}) — sleeping "
                  "10 min, then continuing...")
            time.sleep(600)
        except Exception as ex:                # noqa: BLE001
            print(sid, "ERR", str(ex)[:60])
            time.sleep(2)
    _save(c)
    print(f"run fetched {done}; REAL coverage: fund "
          f"{len(fund)}/{len(uni)} tape {len(tape)}/{len(uni)}")
    if len(fund) < len(uni):
        print("-> rerun `harvest` until coverage ~complete "
              "(resumable; failures are never cached)")


def floats(limit=None):
    """Phase D: insider floats for names above the size screen
    (tail gets banded defaults — weight is negligible)."""
    import logging
    import yfinance as yf
    # silence Yahoo 404 spam — misses are cached and handled as
    # flagged default floats in the report (by design)
    for name in ("yfinance", "urllib3", "peewee"):
        logging.getLogger(name).setLevel(logging.CRITICAL)
    c = _load()
    fund, tape = c.get("fund", {}), c.get("tape", {})
    fl = c.setdefault("floats", {})
    big = []
    for sid, f in fund.items():
        t = tape.get(sid, {})
        if f.get("shares") and t.get("close"):
            cap = f["shares"] * t["close"] / FX
            if cap >= MIN_SIZE_USD:
                big.append((cap, sid))
    big.sort(reverse=True)
    todo = [sid for _, sid in big if sid not in fl]
    if limit:
        todo = todo[:int(limit)]
    print(f"floats: {len(todo)} to fetch "
          f"(of {len(big)} above size screen)")
    for i, sid in enumerate(todo):
        got = None
        for suf in (".TW", ".TWO"):
            try:
                info = yf.Ticker(sid + suf).info
                if info.get("sharesOutstanding"):
                    got = info.get("heldPercentInsiders")
                    break
            except Exception:                  # noqa: BLE001
                continue
        fl[sid] = got
        if (i + 1) % 10 == 0:
            _save(c)
            print(f"  floats {i + 1}/{len(todo)} "
                  f"(found {sum(1 for v in fl.values() if v is not None)})")
        time.sleep(0.4)
    _save(c)
    print("floats cached:", sum(1 for v in fl.values()
                                if v is not None))


def report():
    c = _load()
    uni = {u["code"]: u for u in c.get("universe", [])}
    fund, tape, fl = (c.get("fund", {}), c.get("tape", {}),
                      c.get("floats", {}))
    rows, excl = [], {"no_data": 0, "min_size": 0, "float": 0,
                      "liquidity": 0, "freq": 0}
    for sid in uni:
        f, t = fund.get(sid, {}), tape.get(sid, {})
        if not (f.get("shares") and t.get("close")):
            excl["no_data"] += 1
            continue
        cap = f["shares"] * t["close"] / FX
        if cap < MIN_SIZE_USD:
            excl["min_size"] += 1
            continue
        ins = fl.get(sid)
        ff = (max(min(1 - ins, 1.0), 0.05) if ins is not None
              else 0.6)                        # banded default
        if ff < 0.15:
            excl["float"] += 1
            continue
        ffcap = cap * ff
        atvr12 = (t["val_12m"] / FX) / ffcap if ffcap else 0
        atvr3 = ((t["val_3m"] / FX) * 4) / ffcap if ffcap else 0
        if atvr12 < 0.15 or atvr3 < 0.15:
            excl["liquidity"] += 1
            continue
        if t.get("traded_days_3m", 63) / 63 < 0.7:
            excl["freq"] += 1
            continue
        rows.append({"code": sid, "cap_usd_b": cap / 1e9,
                     "ff": ff, "ffcap_usd_b": ffcap / 1e9,
                     "ff_src": "insiders" if ins is not None
                     else "default0.6"})
    total = sum(r["ffcap_usd_b"] for r in rows)
    est = sum(r["ffcap_usd_b"] for r in rows
              if r["ff_src"] != "insiders")
    out = {"n_universe": len(uni),
           "n_pass": len(rows), "excluded": excl,
           "denominator_busd": round(total, 0),
           "of_which_default_float_busd": round(est, 0),
           "factsheet_implied_busd": 3745,
           "gap_vs_factsheet": f"{total/3745-1:+.1%}",
           "coverage": {
               "fund": f"{len(fund)}/{len(uni)}",
               "tape": f"{len(tape)}/{len(uni)}",
               "floats": f"{len(fl)}"}}
    (ROOT / "data" / "mieu_report.json").write_text(
        json.dumps({**out, "rows_top": sorted(
            rows, key=lambda r: -r["cap_usd_b"])[:120]}, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    lim = (sys.argv[sys.argv.index("--limit") + 1]
           if "--limit" in sys.argv else None)
    if cmd == "harvest":
        harvest(lim)
    elif cmd == "floats":
        floats(lim)
    elif cmd == "report":
        report()
    elif cmd == "purge":
        purge_failures()
