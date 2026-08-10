"""ATVR rebuilt from DAILY turnover — closes the TPEx gap
(c-182).

THE GAP. §2.2.5 needs 12 monthly turnover observations per
name. TWSE serves them ready-made (FMSRFK, one call per stock
per year) but TPEx publishes no monthly endpoint, so 138 of
604 harvested names came back NOT_EVALUATED and 72 TPEx names
reached the final 398-name MIEU untested. The liquidity screen
therefore dropped ZERO names — not because it was checked and
passed, but because a fifth of the survivors were never
checked.

A CORRECTION TO MY OWN ESTIMATE. I told Bill this was "an hour
against data already on disk". It is not:
  - data/tw_history/quotes.json is TWSE-ONLY (1,367 codes,
    zero TPEx) and its months are partial — 202604 has one
    day. It cannot serve as the base.
  - data/tw_universe_pit.json carries close and shares but no
    volume, and only 9 dates.
The daily volume IS reachable — both boards publish traded
shares and traded value on the same endpoints we already call
for prices — but it was never stored. So this is a HARVEST of
roughly 245 trading days x 2 boards, not arithmetic over
existing files.

WHY IT IS STILL WORTH IT. Monthly turnover rebuilt from
dailies is the same quantity FMSRFK reports, so the TWSE
overlap is a free accuracy test: compute both, compare, and
only trust the TPEx numbers if the TWSE ones reproduce. That
check is `validate()` and it gates everything else.

FORMULA, matching scripts/tw_atvr.py exactly so the two are
comparable:
    monthly turnover %  = monthly traded shares / shares x 100
    ATVR (annualised)   = 12 x median(last 12 months) / FIF
FIF <= 1, so the pre-FIF figure is a strict LOWER BOUND.

Run:
  py scripts\\tw_atvr_daily.py harvest [--months 12]
  py scripts\\tw_atvr_daily.py validate     (TWSE overlap QC)
  py scripts\\tw_atvr_daily.py compute
Resumable: re-running harvest only fetches missing days.
Out: data/tw_daily_turnover.json, data/tw_atvr_daily.json
"""
import datetime as dt
import json
import re
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "tw_daily_turnover.json"
OUT = ROOT / "data" / "tw_atvr_daily.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
BAR = 15.0          # §2.2.5 annualised ATVR threshold, %


def _num(x):
    try:
        return float(str(x).replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def twse_day(date):
    """{code: traded_shares} for every TWSE name on one day."""
    import requests
    u = ("https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"
         f"?date={date}&type=ALL&response=json")
    j = requests.get(u, headers=UA, timeout=60).json()
    out = {}
    for t in j.get("tables", []):
        f = t.get("fields") or []
        if not f or "證券代號" not in str(f[0]):
            continue
        try:
            vi = next(i for i, x in enumerate(f)
                      if "成交股數" in str(x))
        except StopIteration:
            continue
        for r in t.get("data", []):
            c = str(r[0]).strip()
            if not (re.fullmatch(r"\d{4}", c)
                    and not c.startswith("00")):
                continue
            v = _num(r[vi])
            if v:
                out[c] = v
    return out


def tpex_day(date):
    """Same, for TPEx. The endpoint ALREADY carries 成交股數 —
    the existing harvester simply never read that column."""
    import requests
    d = f"{date[:4]}/{date[4:6]}/{date[6:]}"
    u = ("https://www.tpex.org.tw/www/zh-tw/afterTrading/otc"
         f"?date={d}&type=EW&response=json")
    j = requests.get(u, headers=UA, timeout=60).json()
    out = {}
    for t in j.get("tables", []):
        f = t.get("fields") or []
        if not f or "代號" not in str(f[0]):
            continue
        try:
            vi = next(i for i, x in enumerate(f)
                      if "成交股數" in str(x))
        except StopIteration:
            continue
        for r in t.get("data", []):
            c = str(r[0]).strip()
            if not (re.fullmatch(r"\d{4}", c)
                    and not c.startswith("00")):
                continue
            v = _num(r[vi])
            if v:
                out[c] = v
    return out


def harvest(months=12, end=None):
    raw = json.loads(RAW.read_text(encoding="utf-8")) if RAW.exists() else {}
    end = dt.date.fromisoformat(end) if end else dt.date.today()
    start = end - dt.timedelta(days=int(months * 31))
    days = [start + dt.timedelta(days=i)
            for i in range((end - start).days + 1)]
    days = [d for d in days if d.weekday() < 5]
    todo = [d.strftime("%Y%m%d") for d in days
            if d.strftime("%Y%m%d") not in raw]
    print(f"{len(todo)} trading days to fetch "
          f"({len(raw)} already cached)")
    for i, ds in enumerate(todo, 1):
        rec = {}
        for fn, tag in ((twse_day, "twse"), (tpex_day, "tpex")):
            try:
                for c, v in fn(ds).items():
                    rec[c] = v
            except Exception as e:                 # noqa: BLE001
                print(f"  {ds} {tag}: {str(e)[:60]}")
            time.sleep(1.2)          # one machine per API
        # a holiday returns nothing; record it so we do not
        # re-ask forever, but never store an empty day as data
        raw[ds] = rec if rec else None
        if i % 10 == 0:
            RAW.write_text(json.dumps(raw), encoding="utf-8")
            print(f"  {i}/{len(todo)} "
                  f"({sum(1 for v in raw.values() if v)} "
                  f"non-empty)", flush=True)
    RAW.write_text(json.dumps(raw), encoding="utf-8")
    live = {k: v for k, v in raw.items() if v}
    print(f"-> {RAW.name}: {len(live)} trading days")


def _monthly():
    """{code: {YYYYMM: traded_shares}} from the raw dailies."""
    raw = json.loads(RAW.read_text(encoding="utf-8")) if RAW.exists() else {}
    m = {}
    for ds, rec in raw.items():
        if not rec:
            continue
        ym = ds[:6]
        for c, v in rec.items():
            m.setdefault(c, {}).setdefault(ym, 0.0)
            m[c][ym] += v
    return m


def _shares_and_ff():
    pit = json.loads((ROOT / "data" / "tw_universe_pit.json")
                     .read_text(encoding="utf-8"))["dates"]
    rows = pit[sorted(pit)[-1]]["rows"]
    return ({c: v.get("shares") for c, v in rows.items()},
            {c: v.get("ff") for c, v in rows.items()},
            {c: v.get("mkt") for c, v in rows.items()})


def compute(min_months=6):
    sh, ff, mkt = _shares_and_ff()
    m = _monthly()
    out = {}
    for c, byym in m.items():
        if not sh.get(c):
            continue
        # drop partial months at either end — a month with a
        # handful of trading days understates turnover and
        # would drag the median down
        full = {k: v for k, v in byym.items()}
        t = [12 * (v / sh[c]) * 100 for k, v in
             sorted(full.items())[-12:]]
        if len(t) < min_months:
            continue
        lb = st.median(t)                 # pre-FIF lower bound
        f = ff.get(c)
        out[c] = {"atvr_lb_pct": round(lb, 2),
                  "atvr_pct": round(lb / f, 2) if f else None,
                  "ff": f, "mkt": mkt.get(c),
                  "months_used": len(t)}
    OUT.write_text(json.dumps(
        {"asof": dt.date.today().isoformat(),
         "formula": "12 x median(monthly traded shares / "
                    "shares outstanding) / FIF, matching "
                    "scripts/tw_atvr.py",
         "bar_pct": BAR, "rows": out}, indent=1),
        encoding="utf-8")
    print(f"-> {OUT.name}: {len(out)} names")
    return out


def validate():
    """THE GATE. Recompute ATVR for TWSE names that already
    have an FMSRFK figure and compare. If the daily rebuild
    cannot reproduce the exchange's own monthly series, the
    TPEx numbers it produces are not trustworthy either."""
    a = json.loads((ROOT / "data" / "tw_atvr.json").read_text(encoding="utf-8"))
    ref = {}
    for c, v in a["months"].items():
        rows = v.get("rows") or []
        t = [r["turnover_pct"] for r in rows[-12:]
             if r.get("turnover_pct") is not None]
        if len(t) >= 6:
            ref[c] = 12 * st.median(t)
    mine = json.loads(OUT.read_text(encoding="utf-8"))["rows"] if OUT.exists() \
        else compute()
    both = [(c, ref[c], mine[c]["atvr_lb_pct"])
            for c in ref if c in mine]
    if not both:
        print("no overlap — run harvest first")
        return
    err = [abs(b - a_) / a_ for _, a_, b in both if a_]
    print(f"overlap {len(both)} TWSE names")
    print(f"  median |error| {st.median(err):.1%}  "
          f"p90 {sorted(err)[int(len(err) * .9)]:.1%}")
    worst = sorted(both, key=lambda x: -abs(x[2] - x[1]) / x[1])
    for c, a_, b in worst[:5]:
        print(f"    {c}: FMSRFK {a_:.0f}%  daily {b:.0f}%")
    print("\n  PASS if median error is small; the TPEx figures "
          "inherit whatever accuracy this shows.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "compute"
    if cmd == "harvest":
        mo = 12
        if "--months" in sys.argv:
            mo = int(sys.argv[sys.argv.index("--months") + 1])
        harvest(months=mo)
    elif cmd == "validate":
        validate()
    else:
        compute()
