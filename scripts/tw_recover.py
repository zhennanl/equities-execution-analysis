"""Recover the remaining Taiwan event windows (c-269).

Bill: *"let's try first to recover all of Taiwan market data.
Is there a way to recover missing Taiwan market datapoints?"*

Measured before writing anything, because "Taiwan 0/136" in the
last harvest log was an artefact of running the wrong command
and the real gap is much smaller and of three different kinds:

    259  Taiwan movers with a ticker in the changes DB
    179  event windows built
    175  of those priced

    THE GAP, exactly:
      1  row with no window: Feb26|7769 HONPRECISION.
         Recoverable NOW, and the cause is not prices — see
         `reconcile` below.
      4  windows built but unpriced: May13|8069 E Ink,
         Nov12|6244 Motech, Nov11|5371 Coretronic,
         May11|3227 PIXART. All four were OTC names at the
         time, all four sit in 2011-2013 — see `legacy`.
     79  rows in 2006-2009 with no window. NOT recoverable
         from the exchange: TWSE's STOCK_DAY archive refuses
         any date before 2010-01-04 in its own words
         (查詢日期小於99年1月4日). Registered as a permanent
         hole, not a task.

So the ceiling on this script is 5 windows, 179 -> 184 built
and 175 -> 180 priced. That is worth having and it is worth
saying out loud, because "recover all of Taiwan" sounds like
there are dozens waiting.

THE FOURTH THING, and it matters more than the five windows.
44 of the 179 stored windows carry `ann_src = "EST (eff - 10
b-days)"` — a pre-2015 estimate of the announcement date. On
the 34 reviews where MSCI's real announcement date is known,
the announcement-to-effective gap is NOT fixed:

    12 bd   7 reviews          15 bd   2 reviews
    13 bd  19 reviews          17 bd   1 review
    14 bd   5 reviews

Mode 13, range 12-17, and the stored windows use 10. Day 0 is
the pre-news baseline this whole harvest is built around, so a
window whose day 0 is two to seven sessions out does not
measure the announcement effect at all — it measures whatever
happened that week. `flag` stamps every one of them so no
analysis pools them with registry-dated windows by accident.
Fetching more prices cannot fix those; only real announcement
dates can, and MSCI's pre-2015 press releases are the source.

Usage:
    py scripts\\tw_recover.py status      # the table above, live
    py scripts\\tw_recover.py reconcile   # registry vs changes DB
    py scripts\\tw_recover.py legacy      # the 4 old OTC names
    py scripts\\tw_recover.py flag        # stamp estimated day-0
    py scripts\\tw_recover.py ohlc [N]   # re-fetch open/high/low
    py scripts\\tw_recover.py run         # all four, in order
"""
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

WINDOWS = ROOT / "data" / "tw_event_windows.json"
REGISTRY = ROOT / "data" / "msci_tw_events.json"
UA = {"User-Agent": "Mozilla/5.0"}

# TWSE says so itself: a STOCK_DAY query before this date comes
# back "查詢日期小於99年1月4日,請重新查詢!". Re-verified c-186.
TWSE_FLOOR = "2010-01-04"

PAD_PRE = 25            # calendar days either side, matching
PAD_POST = 25           # tw_event_window.py so windows compare


def _load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def _save(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1),
                 encoding="utf-8")


# ---------------------------------------------------------------
# UNIT DETECTION — the trap this file exists not to fall into
# ---------------------------------------------------------------
def detect_volume_unit(rows, tol=0.15):
    """Return (multiplier, median error) for a TPEx day-file.

    c-269, and this is the FIFTH time a Taiwan/Korea/China
    harvester has had a units problem, so it is measured rather
    than assumed. c-261 found TPEx's modern endpoint returns
    成交張數 (LOTS, x1000) where TWSE returns 成交股數 (shares),
    and storing both in one field would have made every OTC
    name's ADV a thousand times too small. The legacy endpoint
    this module adds reports 成交仟股 — THOUSAND SHARES — which
    is the same x1000 but arrived at for a different reason, and
    there is no guarantee it is the same on every page.

    So do not trust the column header. Every day-file row also
    carries turnover in TWD, and turnover must reconcile:

        value ~= volume x multiplier x close

    Try each candidate multiplier, take the median relative
    error, and return the winner only if it is within `tol`.
    A caller that gets (None, err) must refuse to store the
    rows rather than guess — a silently wrong ADV is worse than
    a missing window, because the missing window is visible.

    `rows` are dicts with raw `v` (as published), `value` (TWD)
    and `c` (close).
    """
    best = (None, 1.0)
    usable = [r for r in rows
              if r.get("v") and r.get("value") and r.get("c")]
    if len(usable) < 5:
        return (None, 1.0)
    for mult in (1, 1000):
        errs = [abs(r["value"] - r["v"] * mult * r["c"])
                / r["value"] for r in usable if r["value"]]
        e = statistics.median(errs)
        if e < best[1]:
            best = (mult, e)
    return best if best[1] <= tol else (None, best[1])


# ---------------------------------------------------------------
# 1. RECONCILE — why Feb26|7769 has no window
# ---------------------------------------------------------------
def reconcile(apply=False):
    """Compare the review registry against the changes DB.

    `tw_event_window.events()` builds its move list from
    `msci_tw_events.json`, so a mover that reached the changes
    DB but never reached the registry gets no window and no
    error — it is simply not asked for. That is the whole story
    of Feb26|7769: the registry's Feb-2026 entry has four
    deletions and an EMPTY adds list, while the changes DB
    records HONPRECISION as an addition.

    One disagreement in 45 reviews, which is why it was never
    going to show up as a pattern in a coverage count.
    """
    import pandas as pd
    ev = _load(REGISTRY)
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    tw = df[(df.market == "Taiwan") & (df.ticker != "")].copy()
    tw["bare"] = tw.ticker.astype(str).str.split(".").str[0]

    only_db, only_reg = [], []
    for rev, g in tw.groupby("review"):
        e = ev.get(rev)
        if not e:
            continue
        reg = set(e.get("adds") or {}) | set(e.get("dels") or {})
        for _, r in g.iterrows():
            if r.bare not in reg:
                only_db.append((rev, r.bare, r.security, r.action))
        for c in sorted(reg - set(g.bare)):
            only_reg.append((rev, c))

    print(f"in the changes DB, missing from the registry: "
          f"{len(only_db)}")
    for rev, code, name, act in only_db:
        print(f"    {rev:>6}  {code:<7} {act:<4} {name}")
    print(f"in the registry, missing from the changes DB: "
          f"{len(only_reg)}")
    for rev, code in only_reg:
        print(f"    {rev:>6}  {code}")

    if not apply:
        if only_db:
            print("\n  rerun with `run` to add these to the "
                  "registry and build their windows.")
        return only_db

    for rev, code, name, act in only_db:
        side = "adds" if act == "ADD" else "dels"
        ev[rev].setdefault(side, {})[code] = name
        ev[rev].setdefault("_amended", []).append(
            f"{code} {act} added from msci_changes_db "
            f"(tw_recover c-269)")
    if only_db:
        _save(REGISTRY, ev)
        print(f"\n  registry amended: {len(only_db)} mover(s). "
              f"Now run:\n    py scripts\\tw_event_window.py "
              f"harvest " + " ".join(sorted({r for r, *_ in only_db})))
    return only_db


# ---------------------------------------------------------------
# 2. LEGACY TPEx — the only route to pre-2015 OTC prices
# ---------------------------------------------------------------
def fetch_tpex_legacy(code, start, end):
    """TPEx's OLD per-stock day file, which uses ROC dates.

    The modern path `www/zh-tw/afterTrading/tradingStock` (see
    tw_event_window.fetch_tpex, fixed at c-261) is what serves
    current data, and it is what returned nothing for the four
    2011-2013 names. Two explanations were possible — the names
    are genuinely absent, or the modern path does not reach
    that far back — and they are distinguishable only by asking
    the older endpoint, which predates it.

    `st43_result.php` takes `d=ROC/MM` — note ROC on the way IN
    here, the opposite of the modern path, which is exactly the
    kind of inconsistency that produced c-261. Rows come back in
    `aaData` as:

        0 日期  1 成交仟股  2 成交仟元  3 開盤
        4 最高  5 最低      6 收盤      7 漲跌  8 筆數

    The volume unit is NOT trusted from that header. Raw values
    go to `detect_volume_unit`, which reconciles them against
    turnover and refuses the batch if they do not tie.
    """
    import requests
    out = []
    y, m = int(start[:4]), int(start[5:7])
    y2, m2 = int(end[:4]), int(end[5:7])
    while (y, m) <= (y2, m2):
        u = ("https://www.tpex.org.tw/web/stock/aftertrading/"
             "daily_trading_info/st43_result.php"
             f"?l=zh-tw&d={y - 1911}/{m:02d}&stkno={code}")
        try:
            j = requests.get(u, headers=UA, timeout=30).json()
        except Exception as e:                     # noqa: BLE001
            print(f"    legacy {code} {y}-{m:02d}: {type(e).__name__}")
            time.sleep(4)
            m += 1
            if m == 13:
                y, m = y + 1, 1
            continue
        data = j.get("aaData") or []
        if not data:
            print(f"    legacy {code} {y}-{m:02d}: no rows "
                  f"(stat={j.get('stat')!r})")
        for r in data:
            try:
                p = str(r[0]).split("/")
                iso = (f"{1911 + int(p[0])}-{int(p[1]):02d}"
                       f"-{int(p[2]):02d}")
            except (ValueError, IndexError):
                continue
            if not (start <= iso <= end):
                continue

            def num(x):
                try:
                    return float(str(x).replace(",", ""))
                except ValueError:
                    return None
            out.append({"d": iso, "o": num(r[3]), "h": num(r[4]),
                        "l": num(r[5]), "c": num(r[6]),
                        "v": num(r[1]), "value": num(r[2])})
        time.sleep(2.2)
        m += 1
        if m == 13:
            y, m = y + 1, 1
    out = [r for r in out if r["c"]]
    if not out:
        return []
    # 成交仟元 is THOUSANDS of TWD; put turnover in TWD before
    # asking whether volume is shares or thousands of shares,
    # or the reconciliation is off by the same 1000 it is
    # trying to detect.
    for r in out:
        if r["value"]:
            r["value"] *= 1000
    mult, err = detect_volume_unit(out)
    if mult is None:
        print(f"    legacy {code}: turnover does not reconcile "
              f"at either unit (median error {err:.1%}). "
              f"REFUSED — see detect_volume_unit.")
        return []
    print(f"    legacy {code}: {len(out)} rows, volume unit "
          f"x{mult} (turnover ties to {err:.1%})")
    for r in out:
        if r["v"]:
            r["v"] *= mult
        r.pop("value", None)
    return out


def legacy():
    """Price the windows that exist but have no `px`."""
    w = _load(WINDOWS)
    win = w["windows"]
    todo = {k: v for k, v in win.items()
            if isinstance(v, dict) and not v.get("px")}
    if not todo:
        print("no unpriced windows.")
        return
    print(f"unpriced windows: {len(todo)}")
    import datetime as dt
    got = 0
    for k, v in todo.items():
        ann, eff = str(v["ann"])[:10], str(v["eff"])[:10]
        s = (dt.date(*map(int, ann.split("-")))
             - dt.timedelta(days=PAD_PRE)).isoformat()
        e = (dt.date(*map(int, eff.split("-")))
             + dt.timedelta(days=PAD_POST)).isoformat()
        if e < TWSE_FLOOR:
            print(f"  {k}: entirely before the TWSE archive "
                  f"floor {TWSE_FLOOR} — unreachable.")
            continue
        print(f"  {k}  {v.get('name')}  {s} -> {e}")
        rows = fetch_tpex_legacy(v["code"], s, e)
        if rows:
            v["px"] = rows
            v["px_src"] = ("TPEx st43_result (legacy per-stock "
                           "day file)")
            got += 1
    _save(WINDOWS, w)
    print(f"\npriced {got}/{len(todo)}. "
          f"{'Some names may simply predate TPEx web archive.' if got < len(todo) else ''}")


# ---------------------------------------------------------------
# 3. FLAG — day 0 provenance, so nothing pools silently
# ---------------------------------------------------------------
def flag():
    """Stamp every window whose day 0 is an estimate.

    A window with an estimated announcement date is not a worse
    version of a registry-dated one, it is a different object:
    its day 0 may be the pre-news close, or it may be three
    sessions into the reaction. Analysis has to be able to
    exclude them, and it can only do that if the file says so.

    The error band is measured, not asserted — it is the spread
    of the real announcement-to-effective gap over the 34
    reviews where MSCI's own date is known.
    """
    import datetime as dt
    ev = _load(REGISTRY)

    def bd(a, b):
        a = dt.date(*map(int, str(a)[:10].split("-")))
        b = dt.date(*map(int, str(b)[:10].split("-")))
        n, d = 0, a
        while d < b:
            d += dt.timedelta(days=1)
            n += d.weekday() < 5
        return n

    gaps = sorted(bd(v["ann"], v["eff"]) for v in ev.values()
                  if v.get("ann") and v.get("eff"))
    lo, hi = gaps[0], gaps[-1]
    mode = max(set(gaps), key=gaps.count)
    w = _load(WINDOWS)
    n = 0
    for k, v in w["windows"].items():
        if not isinstance(v, dict):
            continue
        if str(v.get("ann_src", "")).startswith("EST"):
            used = int(str(v["ann_src"]).split("-")[1].split()[0])
            v["day0"] = "estimated"
            v["day0_note"] = (
                f"announcement date estimated as effective minus "
                f"{used} business days. Measured on the {len(gaps)} "
                f"reviews where MSCI's date is known, the real gap "
                f"is {lo}-{hi} business days (mode {mode}), so day 0 "
                f"here is off by roughly {mode - used} sessions and "
                f"may be inside the reaction. Do not pool with "
                f"registry-dated windows.")
            n += 1
        else:
            v["day0"] = "registry"
    _save(WINDOWS, w)
    print(f"stamped {n} estimated-day0 window(s); "
          f"{len(w['windows']) - n} are registry-dated.")
    print(f"real ann->eff gap over {len(gaps)} known reviews: "
          f"{lo}-{hi} business days, mode {mode}.")


# ---------------------------------------------------------------
def status():
    import pandas as pd
    w = _load(WINDOWS)["windows"]
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    tw = df[(df.market == "Taiwan") & (df.ticker != "")].copy()
    tw["bare"] = tw.ticker.astype(str).str.split(".").str[0]
    tw["key"] = tw.review + "|" + tw.bare
    miss = tw[~tw.key.isin(set(w))]
    unp = [k for k, v in w.items()
           if isinstance(v, dict) and not v.get("px")]
    est = [k for k, v in w.items()
           if isinstance(v, dict)
           and str(v.get("ann_src", "")).startswith("EST")]
    allrows = df[(df.market == "Taiwan")]
    print(f"Taiwan movers in the changes DB : {len(allrows)}")
    print(f"  of which carry a ticker       : {len(tw)}")
    print(f"  windows built                 : {len(w)}")
    print(f"  windows priced                : "
          f"{sum(1 for v in w.values() if isinstance(v, dict) and v.get('px'))}")
    print(f"\nrows with no window            : {len(miss)}")
    by = miss.groupby(miss.year).size().to_dict()
    reach = {y: n for y, n in by.items() if y >= 2010}
    hole = {y: n for y, n in by.items() if y < 2010}
    print(f"  reachable (2010+)            : {sum(reach.values())} "
          f"{reach}")
    print(f"  below TWSE floor {TWSE_FLOOR}  : "
          f"{sum(hole.values())} {hole}  <- permanent")
    print(f"\nwindows built but unpriced     : {len(unp)}")
    for k in unp:
        print(f"    {k}  {w[k].get('name')}  ({w[k].get('ann_src')})")
    print(f"\nwindows with an ESTIMATED day 0: {len(est)}")
    print("    day 0 is the pre-news baseline; these are not "
          "comparable with registry-dated windows.")
    print(f"\nTaiwan rows with no ticker at all: "
          f"{len(allrows) - len(tw)}  (see scripts/untickered_audit.py)")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        status()
    elif cmd == "reconcile":
        reconcile(apply=False)
    elif cmd == "legacy":
        legacy()
    elif cmd == "flag":
        flag()
    elif cmd == "ohlc":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else None
        ohlc(n)
    elif cmd == "run":
        print("=" * 58, "\n1. registry vs changes DB\n", "=" * 58)
        added = reconcile(apply=True)
        if added:
            import subprocess
            revs = sorted({r for r, *_ in added})
            subprocess.run([sys.executable,
                            str(ROOT / "scripts" / "tw_event_window.py"),
                            "harvest", *revs], check=False)
        print("=" * 58, "\n2. legacy TPEx for unpriced windows\n",
              "=" * 58)
        legacy()
        print("=" * 58, "\n3. day-0 provenance\n", "=" * 58)
        flag()
        print("=" * 58, "\n4. where that leaves us\n", "=" * 58)
        status()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------
# 4. OHLC — the fields both parsers were dropping
# ---------------------------------------------------------------
def ohlc(limit=None):
    """Re-fetch any window stored without open/high/low.

    c-269. Bill asked for "more Taiwan OHLC daily data" and the
    honest answer turned out to be that Taiwan had NONE: all 176
    priced windows held `{d, c, v}` while every Yahoo-sourced
    market held `{d, o, h, l, c, v}`. Both Taiwan day files carry
    open, high and low at indices 3/4/5 and both parsers read
    only index 6. The fields were fetched and dropped one line
    before they were stored, so nothing ever failed and no
    coverage count could show it.

    That blocks more than it looks like: no overnight gap
    (open against the prior close), no intraday range, no
    close-to-open split of the announcement reaction — for the
    one market this whole project is actually about.

    The raw responses were not cached, so this re-fetches. The
    safety rule is that a window is only overwritten when the
    new series is at least as long as the old one; a throttled
    or half-answered request must not turn a good close-only
    window into a shorter OHLC one.
    """
    import tw_event_window as TW
    import datetime as dt
    w = _load(WINDOWS)
    win = w["windows"]
    todo = [k for k, v in win.items()
            if isinstance(v, dict) and v.get("px")
            and "o" not in v["px"][0]]
    print(f"windows without OHLC: {len(todo)} of {len(win)}")
    if limit:
        todo = todo[:limit]
        print(f"  this run: {len(todo)}")
    done = kept = 0
    for n, k in enumerate(todo, 1):
        v = win[k]
        a = (dt.date.fromisoformat(str(v["ann"])[:10])
             - dt.timedelta(days=PAD_PRE)).isoformat()
        b = (dt.date.fromisoformat(str(v["eff"])[:10])
             + dt.timedelta(days=PAD_POST)).isoformat()
        rows = TW.fetch_window(v["code"], a, b)
        old = len(v["px"])
        if rows and "o" in rows[0] and len(rows) >= old:
            v["px"] = rows
            v["px_src"] = "TWSE/TPEx day file, OHLC (c-269)"
            done += 1
        else:
            kept += 1
            print(f"  {k}: kept the close-only series "
                  f"({old} rows; refetch gave {len(rows)})")
        if n % 10 == 0 or n == len(todo):
            _save(WINDOWS, w)
            print(f"  {n}/{len(todo)}  upgraded {done}, "
                  f"kept {kept}", flush=True)
    _save(WINDOWS, w)
    print(f"\nupgraded {done} window(s) to OHLC; kept {kept} "
          f"unchanged.")
