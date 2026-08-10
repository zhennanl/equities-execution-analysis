#!/usr/bin/env python3
"""The tape for the four August-2026 Taiwan calls.

    py scripts\\tw_watch_tape.py refresh    # network: top up bars
    py scripts\\tw_watch_tape.py build      # offline: metrics + doc
    py scripts\\tw_watch_tape.py status

WHAT THIS IS FOR. Every other Taiwan script in this project reads
HISTORY — what index events did between 2015 and 2026. This one
reads the PRESENT: where the four called names are trading right
now, on what volume, against what they normally do, and against
their peers over the same sessions. The August review announces
on 12 August 2026 and this is the file a desk would have open.

WHY A NEW SCRIPT AND NOT AN EXTENSION OF tw_prepositioning.py.
That script answers one question (has event money already bought)
with one instrument (T86 foreign net, cross-sectionally
controlled). This one is the tape underneath it: price, volume,
ADV over four horizons, turnover percentile, block prints. They
share the shortlist and nothing else, so merging them would make
one file that does two jobs badly.

────────────────────────────────────────────────────────────────
THE ADV PROBLEM THIS EXISTS TO FIX

The capacity ladder in tw_tracker_playbook.py divides demand by
`0.095 x ADV`, where ADV is a SHARE count and 9.5% is a
market-wide median auction share. Two weaknesses, both known:

  1. ADV in shares is horizon-dependent and nobody has said which
     horizon. A 20-day ADV struck through a violent July is a
     different number from a 250-day ADV, and the ladder's
     ranking can reorder between them. So this script computes
     20 / 60 / 120 / 250-session ADV in BOTH shares and TWD and
     reports the spread, rather than picking one silently.

  2. ADV in shares cannot be compared across names. 4m shares of
     Nan Ya PCB and 4m shares of Nanya Technology are not the
     same order. TWD ADV can be compared, and TWSE's STOCK_DAY
     gives traded VALUE directly rather than making us multiply
     close x volume, which is wrong on any day with a range.

────────────────────────────────────────────────────────────────
DATA SOURCES, AND WHICH ARE ALREADY ON DISK

  data/tw_vintage_cache.json   px|CODE, daily close + volume,
                               2015-01-05 -> 2026-07-31. Offline.
  data/tw_daily_turnover.json  {date: {code: shares}}, TWSE AND
                               TPEx merged, ~1,900 codes/day,
                               2025-08-01 -> 2026-08-07. This is
                               the peer cross-section, and it is
                               the only file here that carries
                               8299 (TPEx).
  data/t86_history.json        foreign / total net, 130 TWSE
                               names, -> 2026-08-05.
  data/blocks_history.json     block prints per code -> 2026-08-06
  data/sbl_history.json        borrow balance -> 2026-08-06

  NETWORK (refresh only):
  STOCK_DAY   one month of OHLCV + VALUE for one TWSE stock
  TPEx        the same for 8299, which STOCK_DAY never carries

THE GAP REFRESH CLOSES. The vintage cache stops 2026-07-31 and
the review announces 2026-08-12, so the last week and a half of
price — the most decision-relevant part — is missing offline.
`build` runs without `refresh` and says so in its output rather
than silently reporting a stale close as the latest.

────────────────────────────────────────────────────────────────
WHAT THE PERCENTILES MEAN, SO THEY ARE NOT OVER-READ

`turnover_pctile` places a name's traded shares against ITS OWN
history over the trailing year, not against other names. That is
the question a desk asks ("is this name unusually busy?") and it
survives the fact that share counts are not comparable across
names.

`peer_pctile` places the name's turnover RATIO (today's shares /
its own 250-day median) against the same ratio for every other
code trading that day. That IS comparable across names, and it is
what separates "this name is busy" from "the whole market is
busy" — the same control tw_prepositioning.py applies to flow.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import statistics as stats
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RAW = ROOT / "data" / "tw_watch_tape_raw.json"
OUT = ROOT / "data" / "tw_watch_tape.json"
DOC = ROOT / "docs" / "TW_WATCH_TAPE.md"

# c-328: the shortlist is NOT hard-coded here. It is read from
# data/aug26_scenarios.json so that a change to the call set
# propagates instead of leaving this file quietly describing an
# old shortlist. The fallback exists only so `status` works on a
# fresh clone.
FALLBACK = [("2408", "Nanya Technology", "TWSE"),
            ("8046", "Nan Ya PCB", "TWSE"),
            ("2344", "Winbond Electronics", "TWSE"),
            ("8299", "Phison Electronics", "TPEX")]

# 8299 is TPEx-listed; every TWSE endpoint in this project omits
# it. Recorded here rather than discovered again downstream.
TPEX_CODES = {"8299", "6274", "3529", "3293", "8069"}

WINDOWS = (20, 60, 120, 250)
UA = {"User-Agent": "Mozilla/5.0"}
PACE = 2.0


# ── shared small helpers (house style: no shared util module) ──

def _j(name):
    p = ROOT / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _num(x):
    try:
        return float(str(x).replace(",", "").replace("--", ""))
    except (TypeError, ValueError):
        return None


def _save(path, obj):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    tmp.replace(path)


def _pctl(xs, p):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    i = (len(xs) - 1) * p
    lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def _rank_pct(x, pool):
    """Share of the pool at or below x. Reported as 0-1."""
    pool = [v for v in pool if v is not None]
    if not pool or x is None:
        return None
    return sum(1 for v in pool if v <= x) / len(pool)


def shortlist():
    # aug26_scenarios.json keys `names` BY CODE, not as a list.
    rows = (_j("aug26_scenarios.json") or {}).get("names") or {}
    if not isinstance(rows, dict) or not rows:
        return list(FALLBACK)
    return [(code, r.get("name") or code,
             "TPEX" if code in TPEX_CODES else "TWSE")
            for code, r in sorted(rows.items())]


# ── network: top up the recent bars ────────────────────────────

def _months(back):
    """The YYYYMMDD first-of-month stamps STOCK_DAY wants."""
    today = dt.date.today()
    out, y, m = [], today.year, today.month
    for _ in range(back):
        out.append(dt.date(y, m, 1).strftime("%Y%m%d"))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(out))


def fetch_twse_month(code, stamp):
    """One month of daily bars for one TWSE name.

    Returns {YYYY-MM-DD: [open, high, low, close, shares, value]}.
    A month with no rows returns {} — an empty month is a real
    answer (the future), not a failure, and the caller caches it
    as such only for months that have already ended.
    """
    import requests
    url = ("https://www.twse.com.tw/en/exchangeReport/STOCK_DAY"
           f"?response=json&date={stamp}&stockNo={code}")
    d = requests.get(url, headers=UA, timeout=25).json()
    out = {}
    for row in d.get("data") or []:
        # ROC date "115/08/07" -> 2026-08-07
        try:
            y, m, dd = row[0].split("/")
            iso = f"{int(y) + 1911:04d}-{int(m):02d}-{int(dd):02d}"
        except (ValueError, IndexError):
            continue
        shares, value = _num(row[1]), _num(row[2])
        o, h, lo, c = (_num(row[3]), _num(row[4]),
                       _num(row[5]), _num(row[6]))
        if c is None:
            continue
        out[iso] = [o, h, lo, c, shares, value]
    return out


def fetch_tpex_month(code, stamp):
    """The TPEx equivalent. Separate function, not a branch,
    because the payload shape and the date format differ and a
    single function with two shapes is where parse bugs live."""
    import requests
    y, m = int(stamp[:4]), int(stamp[4:6])
    url = ("https://www.tpex.org.tw/www/zh-tw/afterTrading/"
           f"tradingStock?code={code}&date={y}/{m:02d}/01&id=&response=json")
    d = requests.get(url, headers=UA, timeout=25).json()
    rows = d.get("tables", [{}])[0].get("data") if d.get("tables") \
        else d.get("aaData") or d.get("data")
    out = {}
    for row in rows or []:
        try:
            yy, mm, dd = str(row[0]).split("/")
            yy = int(yy)
            yy = yy + 1911 if yy < 1911 else yy
            iso = f"{yy:04d}-{int(mm):02d}-{int(dd):02d}"
        except (ValueError, IndexError):
            continue
        shares, value = _num(row[1]), _num(row[2])
        o, h, lo, c = (_num(row[3]), _num(row[4]),
                       _num(row[5]), _num(row[6]))
        if c is None:
            continue
        out[iso] = [o, h, lo, c, shares, value]
    return out


def refresh(back=15):
    """Top up `back` months of bars for every shortlist name.

    Resumable by (code, month). A month that already has rows AND
    has ended is never refetched; the CURRENT month always is,
    because it grows every session."""
    store = json.loads(RAW.read_text(encoding="utf-8")) \
        if RAW.exists() else {}
    cur = dt.date.today().strftime("%Y%m")
    todo = []
    for code, name, board in shortlist():
        got = store.setdefault(code, {})
        for stamp in _months(back):
            ym = stamp[:6]
            done = any(k[:7].replace("-", "") == ym for k in got)
            if done and ym != cur:
                continue
            todo.append((code, name, board, stamp))
    print(f"{len(todo)} (code, month) fetches")
    fails = 0
    for i, (code, name, board, stamp) in enumerate(todo, 1):
        try:
            f = fetch_tpex_month if board == "TPEX" else fetch_twse_month
            got = f(code, stamp)
            store[code].update(got)
            print(f"  {i:>3}/{len(todo)} {code} {stamp} "
                  f"{len(got):>3} bars")
            fails = 0
        except Exception as ex:                     # noqa: BLE001
            fails += 1
            print(f"  {i:>3}/{len(todo)} {code} {stamp} ERR "
                  f"{str(ex)[:60]}"
                  + ("  — backing off 60s" if fails >= 3 else ""))
            if fails >= 3:
                time.sleep(60)
                fails = 0
        if i % 10 == 0:
            _save(RAW, store)
        time.sleep(PACE)
    _save(RAW, store)
    n = sum(len(v) for v in store.values())
    print(f"saved {RAW.name}: {len(store)} codes, {n} bars")


# ── offline: build the metrics ─────────────────────────────────

def _series(code, raw, vintage):
    """Daily rows for one code, freshest source winning.

    Returns [(iso, close, shares, value_or_None)] ascending.

    The vintage cache has no traded VALUE, so its rows carry None
    there rather than close x volume. Multiplying would produce a
    number that looks like the real thing and is wrong by the
    day's range — the kind of silent error this project has been
    bitten by before, so it is left missing instead.
    """
    rows = {}
    for iso, r in (vintage or {}).items():
        rows[iso] = (r[0], r[1], None)
    for iso, r in (raw.get(code) or {}).items():
        rows[iso] = (r[3], r[4], r[5])
    return [(k, *rows[k]) for k in sorted(rows)]


def _vintage_map(code, cache):
    out = {}
    for r in cache.get(f"px|{code}") or []:
        c, v = r.get("close"), r.get("Trading_Volume")
        if c:
            out[r["date"]] = (c, v)
    return out


def _adv(ser, n, idx):
    """Mean daily shares / value over the last n sessions."""
    tail = ser[-n:] if n <= len(ser) else ser
    xs = [t[idx] for t in tail if t[idx]]
    return (stats.fmean(xs) if xs else None), len(xs)


def build():
    raw = json.loads(RAW.read_text(encoding="utf-8")) \
        if RAW.exists() else {}
    cache = _j("tw_vintage_cache.json")
    turn = _j("tw_daily_turnover.json")
    t86 = _j("t86_history.json")
    blocks = _j("blocks_history.json")
    sbl = _j("sbl_history.json")

    tdays = sorted(k for k, v in turn.items() if v)
    t86days = sorted(k for k, v in t86.items() if v)

    # peer ratios: each code's turnover today / its own median
    # over the whole turnover file. Built once, used for every
    # name's cross-sectional placement.
    hist = {}
    for d in tdays:
        for c, s in turn[d].items():
            hist.setdefault(c, []).append(s)
    med = {c: stats.median(v) for c, v in hist.items()
           if len(v) >= 60 and stats.median(v) > 0}

    out = {"_built": dt.datetime.now().isoformat(timespec="seconds"),
           "_windows": list(WINDOWS),
           "coverage": {
               "vintage_last": max(
                   (r["date"] for r in cache.get("px|2408") or []),
                   default=None),
               "turnover_last": tdays[-1] if tdays else None,
               "t86_last": t86days[-1] if t86days else None,
               "refreshed": bool(raw),
               "refresh_last": max(
                   (max(v) for v in raw.values() if v), default=None),
           },
           "names": []}

    for code, name, board in shortlist():
        ser = _series(code, raw, _vintage_map(code, cache))
        if not ser:
            out["names"].append({"code": code, "name": name,
                                 "board": board, "_no_data": True})
            continue
        closes = [t[1] for t in ser]
        rec = {"code": code, "name": name, "board": board,
               "sessions_held": len(ser),
               "last_date": ser[-1][0], "last_close": ser[-1][1]}

        # price trend over the two horizons Bill asked for
        for n in (20, 30):
            if len(ser) > n:
                base = closes[-n - 1]
                rec[f"ret_{n}d"] = (closes[-1] / base - 1
                                    if base else None)
                seg = closes[-n:]
                rec[f"high_{n}d"], rec[f"low_{n}d"] = max(seg), min(seg)
                rec[f"drawdown_from_{n}d_high"] = (
                    closes[-1] / max(seg) - 1 if max(seg) else None)
                # realised vol, annualised on 252
                rets = [seg[i] / seg[i - 1] - 1
                        for i in range(1, len(seg)) if seg[i - 1]]
                rec[f"vol_{n}d"] = (stats.pstdev(rets) * (252 ** .5)
                                    if len(rets) > 2 else None)
        rec["trend_30d"] = [{"d": t[0], "c": t[1], "v": t[2]}
                            for t in ser[-30:]]

        # ADV on four horizons, shares and TWD
        rec["adv"] = {}
        for n in WINDOWS:
            sh, nsh = _adv(ser, n, 2)
            val, nval = _adv(ser, n, 3)
            rec["adv"][str(n)] = {
                "shares": sh, "shares_n": nsh,
                "value_twd": val, "value_n": nval}
        advs = [v["shares"] for v in rec["adv"].values() if v["shares"]]
        rec["adv_spread"] = (max(advs) / min(advs)
                             if len(advs) > 1 and min(advs) else None)

        # turnover percentile against the name's own year, and the
        # cross-sectional placement of its turnover ratio
        own = hist.get(code) or []
        if own:
            rec["turnover_pctile"] = _rank_pct(own[-1], own)
            rec["turnover_last"] = own[-1]
        if code in med and tdays:
            day = turn[tdays[-1]]
            mine = day.get(code)
            if mine:
                ratios = [day[c] / med[c] for c in day
                          if c in med and day[c] is not None]
                rec["peer_pctile"] = _rank_pct(mine / med[code], ratios)
                rec["peer_pool"] = len(ratios)
                rec["turnover_ratio"] = mine / med[code]

        # foreign net over the trailing windows, in days of ADV
        adv20 = rec["adv"]["20"]["shares"]
        for n in (5, 20, 60):
            days = t86days[-n:]
            xs = [t86[d].get(code, {}).get("f") for d in days]
            xs = [x for x in xs if x is not None]
            if not xs:
                continue
            rec[f"foreign_net_{n}d"] = sum(xs)
            rec[f"foreign_net_{n}d_of_adv"] = (
                sum(xs) / adv20 if adv20 else None)

        # block prints in the last 30 sessions
        bdays = sorted(k for k, v in blocks.items() if v)[-30:]
        bl = []
        for d in bdays:
            for r in blocks[d].get(code) or []:
                q, v = _num(r["raw"][3]), _num(r["raw"][4])
                bl.append({"d": d, "kind": r["raw"][1],
                           "shares": q, "value_twd": v})
        rec["blocks_30d"] = bl
        rec["blocks_30d_shares"] = sum(b["shares"] or 0 for b in bl)
        rec["blocks_30d_of_adv"] = (
            rec["blocks_30d_shares"] / adv20 if adv20 else None)

        sdays = sorted(k for k, v in sbl.items() if v)
        if sdays:
            cur = sbl[sdays[-1]].get(code)
            prv = sbl[sdays[max(0, len(sdays) - 21)]].get(code)
            if cur and prv:
                rec["sbl_balance"] = cur[1]
                rec["sbl_build_20d"] = cur[1] - prv[1]
                rec["sbl_build_20d_of_adv"] = (
                    (cur[1] - prv[1]) / adv20 if adv20 else None)

        out["names"].append(rec)

    _save(OUT, out)
    write_doc(out)
    print(f"wrote {OUT.name} and {DOC.name}")
    return out


def write_doc(o):
    L = ["# The tape for the August-2026 Taiwan calls", "",
         f"Built {o['_built']}.", "",
         "## Coverage", ""]
    c = o["coverage"]
    L += [f"- vintage price cache to **{c['vintage_last']}**",
          f"- turnover (TWSE+TPEx) to **{c['turnover_last']}**",
          f"- T86 foreign net to **{c['t86_last']}**",
          f"- live refresh: **{'yes, to ' + str(c['refresh_last']) if c['refreshed'] else 'NOT RUN — prices below are stale'}**",
          ""]
    L += ["## Per name", ""]
    for r in o["names"]:
        if r.get("_no_data"):
            L += [f"### {r['code']} {r['name']} — NO DATA", ""]
            continue
        L += [f"### {r['code']} {r['name']} ({r['board']})", "",
              f"- last close **{r['last_close']}** on {r['last_date']}",
              f"- 20d {r.get('ret_20d', 0) or 0:+.1%}, "
              f"30d {r.get('ret_30d', 0) or 0:+.1%}, "
              f"{r.get('drawdown_from_30d_high', 0) or 0:+.1%} from "
              f"the 30d high",
              f"- 30d realised vol {(r.get('vol_30d') or 0):.0%}"]
        a = r["adv"]
        L.append("- ADV shares: " + ", ".join(
            f"{w}d {a[w]['shares']:,.0f}" for w in ("20", "60", "120", "250")
            if a[w]["shares"]))
        if r.get("adv_spread"):
            L.append(f"- **ADV spread across horizons "
                     f"{r['adv_spread']:.2f}x** — the capacity "
                     f"ladder's answer moves by this much depending "
                     f"on which horizon it is struck on")
        if r.get("peer_pctile") is not None:
            L.append(f"- turnover ratio {r['turnover_ratio']:.2f}x its "
                     f"own median, **{r['peer_pctile']:.0%}** of "
                     f"{r['peer_pool']:,} codes trading that day")
        for n in (5, 20, 60):
            k = f"foreign_net_{n}d"
            if k in r:
                L.append(f"- foreign net {n}d {r[k]:+,.0f} sh "
                         f"({r[k + '_of_adv'] or 0:+.2f} days of 20d ADV)")
        if r.get("blocks_30d"):
            L.append(f"- {len(r['blocks_30d'])} block prints in 30 "
                     f"sessions, {r['blocks_30d_shares']:,.0f} sh "
                     f"({r['blocks_30d_of_adv'] or 0:.2f} days of ADV)")
        if r.get("sbl_build_20d") is not None:
            L.append(f"- borrow balance {r['sbl_balance']:,.0f}, "
                     f"20d change {r['sbl_build_20d']:+,.0f} "
                     f"({r['sbl_build_20d_of_adv'] or 0:+.2f} days)")
        L.append("")
    L += ["## What this cannot see", "",
          "- **Broker-branch (券商分點) is not here.** TWSE serves "
          "per-branch, per-stock buy/sell only through "
          "bsr.twse.com.tw, which is CAPTCHA-gated and holds the "
          "most recent session only. There is no historical "
          "endpoint and no lawful automated route, so this is a "
          "vendor purchase or a manual daily capture, not a "
          "harvest.",
          "- **Foreign net is a net**, and 8299 is TPEx-listed so "
          "T86 never carries it.",
          "- **Traded value is missing before the refresh.** The "
          "vintage cache has close and volume only; value is left "
          "null rather than approximated as close x volume.",
          ""]
    DOC.write_text("\n".join(L), encoding="utf-8")


def status():
    for p in (RAW, OUT, DOC):
        if p.exists():
            print(f"  {p.name:<28} {p.stat().st_size / 1024:>8,.0f} KB")
        else:
            print(f"  {p.name:<28} {'—':>8}")
    if RAW.exists():
        s = json.loads(RAW.read_text(encoding="utf-8"))
        for c, v in sorted(s.items()):
            if v:
                print(f"    {c}: {len(v):>4} bars, "
                      f"{min(v)} -> {max(v)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "refresh":
        n = int(sys.argv[sys.argv.index("--months") + 1]) \
            if "--months" in sys.argv else 15
        refresh(n)
    elif cmd == "build":
        build()
    else:
        status()
