"""Announcement -> effective event windows for MSCI Taiwan
(c-127).

TIMING CONVENTION (the answer to Bill's question, encoded):
MSCI announces from Geneva at ~23:00 CET on the announcement
date — that is ~05:00-06:00 Taipei the NEXT morning. Taiwan's
session on the announcement date itself therefore closes
PRE-NEWS. So:
    day 0  = the announcement date's Taipei close  (baseline,
             cumulative return := 0 — the last untainted print)
    day 1  = the first session that can react (ann date + 1)
Getting this wrong by one day contaminates the baseline with
the reaction jump, so it is a convention, pinned, not a detail.

COVERAGE (measured, not hoped):
  - TWSE STOCK_DAY serves DELISTED names (Inotera 2016 ✓,
    old ASE 2018 ✓) but its floor is 2010-01-04 (ROC 99) —
    RE-VERIFIED c-186: a query for 2009-12-15 returns the
    exchange's own refusal, "查詢日期小於99年1月4日,請重新查詢!"
    ("date earlier than 4 Jan ROC-99"). 2010-01-04 returns 20
    rows. This is TWSE's archive limit, not our choice.
    => full-fidelity windows 2010-2026; 2006-2009 = survivors
    only via Yahoo, NOT harvested here (registered gap).
  - announcement dates: exact from the TW registry 2015+
    ('ann'); 2010-2014 estimated as effective - 13 business
    days, labelled EST. (13, not 10 — see c-186 above.)
  - TPEx-listed movers need the TPEx per-stock endpoint —
    marked pending, not silently skipped.

Positioning overlays need NO new harvest — sbl_history (borrow
balance), t86_history (foreign net buy), margin_history all
cover 2015->2026 per stock per day already.

Usage:  py scripts\\tw_event_window.py harvest [RevLabel ...]
        py scripts\\tw_event_window.py status
Output: data/tw_event_windows.json   (resumable)
"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "tw_event_windows.json"
UA = {"User-Agent": "Mozilla/5.0"}
PAD_PRE = 25          # calendar days before announcement
PAD_POST = 25         # after effective


def _num(s):
    try:
        return float(str(s).replace(",", ""))
    except (ValueError, AttributeError):
        return None


def events():
    """{rev: {ann, ann_src, eff, moves:{code:(action,name)}}}
    for 2010+."""
    import pandas as pd
    ev = json.loads((ROOT / "data" / "msci_tw_events.json")
                    .read_text(encoding="utf-8"))
    out = {}
    for rev, v in ev.items():
        moves = {c: ("ADD", n) for c, n in v.get("adds", {}).items()}
        moves.update({c: ("DEL", n)
                      for c, n in v.get("dels", {}).items()})
        if moves and v.get("ann") and v.get("eff"):
            out[rev] = {"ann": v["ann"], "ann_src": "registry",
                        "eff": v["eff"], "moves": moves}
    # 2010-2014 from the changes DB, announcement estimated
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    # c-188: floor raised 2010 -> 2015. Pre-2015 reviews have no
    # registry announcement date, only an estimate that was
    # measured to be 3 sessions late. Harvesting them produces
    # windows whose day-0 is wrong, so they are not built.
    tw = df[(df.market == "Taiwan") & (df.year >= 2015)
            & (df.year <= 2014) & (df.ticker != "")]
    for rev, g in tw.groupby("review"):
        if rev in out:
            continue
        eff = g.eff_date_est.iloc[0]
        d = dt.date.fromisoformat(eff)
        n = 0
        while n < 10:                      # eff - 10 b-days
            d -= dt.timedelta(days=1)
            if d.weekday() < 5:
                n += 1
        out[rev] = {"ann": d.isoformat(),
                    # c-186: was 10 business days. MEASURED
                    # against the 34 real announcements in the
                    # registry, the true gap is a median of 13
                    # business days (mean 13.2, range 12-17).
                    # 10 placed day-0 THREE SESSIONS LATE, so
                    # part of the announcement reaction sat
                    # inside the baseline that is defined to be
                    # zero. Corrected to 13.
                    "ann_src": "EST (eff - 13 b-days)",
                    "eff": eff,
                    "moves": {r.ticker.split(".")[0]:
                              (r.action, r.security)
                              for _, r in g.iterrows()}}
    return out


def months_between(a, b):
    y, m = int(a[:4]), int(a[5:7])
    y2, m2 = int(b[:4]), int(b[5:7])
    while (y, m) <= (y2, m2):
        yield f"{y}{m:02d}01"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def _board(code):
    """'twse' | 'tpex' | None, from our own universe file."""
    p = ROOT / "data" / "tw_mieu_universe.json"
    if not p.exists():
        return None
    try:
        return ((json.loads(p.read_text(encoding="utf-8"))["universe"]
                 .get(str(code)) or {}).get("mkt"))
    except Exception:                              # noqa: BLE001
        return None


def fetch_tpex(code, start, end):
    """Daily rows for an OTC name from TPEx's own day-file.

    c-232: TAIWAN HAS TWO BOARDS AND THIS HARVESTER ONLY EVER
    READ ONE. Of 179 stored windows, 139 priced ones are TWSE
    and NOT A SINGLE PRICED WINDOW IS TPEx — 16 of the 22
    unpriced are TPEx names (Win Semiconductors, Parade, MPI,
    eMemory, Phison, PharmaEssentia and friends). STOCK_DAY is
    the TWSE file; asking it for an OTC code returns nothing,
    and nothing is exactly what a delisted name returns too, so
    the gap looked like ordinary attrition for years.

    It is the same one-board-per-market error as ib_5m_events
    c-195 (TWSE/TPEx), c-195 again (Korea KOSPI/KOSDAQ) and
    c-225 (China's four venues). Fourth time. The tell is always
    the same: a market with two boards and a map that names one.

    c-261: TWO BUGS, AND THE SECOND IS THE DANGEROUS ONE.

    **The date is AD on the way in and ROC on the way out.**
    c-232 assumed TPEx was "the same shape as TWSE" and sent
    the ROC year, so every request came back
    `{"stat":"參數輸入錯誤"}` — parameter input error — and
    every window returned zero rows. Eighteen live, well-known
    OTC names (E Ink, Phison, Aspeed, eMemory, Win Semi,
    PharmaEssentia) read as "no data" for months. The endpoint
    wants `date=YYYY/MM/DD` in the Gregorian year; the ROWS it
    returns are dated in ROC. Half the assumption was right,
    which is why it looked plausible.

    **The volume is in LOTS, not shares.** TWSE's STOCK_DAY
    returns 成交股數, shares. TPEx's tradingStock returns
    成交張數, LOTS — one lot is 1,000 shares. Storing both in
    one `v` field without conversion would have made every TPEx
    name's volume 1,000x too small, and this whole harvest
    exists to compute trade size against ADV. A silently
    thousand-fold ADV error is worse than the missing data it
    replaces.

    Checked on the response itself rather than assumed: E Ink
    on 2026-02-02 shows 2,610 lots and 448,660 thousand TWD of
    value at a 171.50 close. 2.61m shares x 171.50 = 448m TWD,
    so the units reconcile only if the figure is lots.

    Field order (from the endpoint's own `fields`):
        0 日期  1 成交張數  2 成交仟元  3 開盤
        4 最高  5 最低      6 收盤      7 漲跌  8 筆數
    """
    import requests
    LOT = 1000            # 張 -> shares, to match TWSE's unit
    rows = []
    for mo in months_between(start, end):
        u = ("https://www.tpex.org.tw/www/zh-tw/afterTrading/"
             f"tradingStock?code={code}"
             f"&date={mo[:4]}/{mo[4:6]}/01&response=json")
        try:
            j = requests.get(u, headers=UA, timeout=30).json()
        except Exception:                          # noqa: BLE001
            time.sleep(4)
            continue
        if str(j.get("stat", "")).lower() != "ok":
            # say so instead of returning an empty list that
            # reads as "this name did not trade"
            print(f"    TPEx {code} {mo}: {j.get('stat')}")
            time.sleep(2.2)
            continue
        for t in (j.get("tables") or [{}]):
            for r in (t.get("data") or []):
                try:
                    p = str(r[0]).split("/")
                    iso = (f"{1911 + int(p[0])}-{int(p[1]):02d}"
                           f"-{int(p[2]):02d}")
                except (ValueError, IndexError):
                    continue
                if start <= iso <= end:
                    v = _num(r[1])
                    # c-269: OPEN, HIGH AND LOW WERE BEING
                    # THROWN AWAY. Both day files carry them at
                    # indices 3/4/5 and both parsers read only
                    # the close, so all 176 Taiwan windows held
                    # close and volume while every Yahoo-sourced
                    # market held full OHLC. Nothing failed —
                    # the fields were fetched and dropped one
                    # line before they were stored.
                    rows.append({"d": iso, "o": _num(r[3]),
                                 "h": _num(r[4]), "l": _num(r[5]),
                                 "c": _num(r[6]),
                                 "v": v * LOT if v else v})
        time.sleep(2.2)
    return [r for r in rows if r["c"]]


def fetch_window(code, start, end):
    """Daily (date, close, volume), delisted-safe, from the
    board the code actually trades on."""
    import requests
    if _board(code) == "tpex":
        rows = fetch_tpex(code, start, end)
        if rows:
            return rows
        # fall through — our universe file is current-state and
        # a name may have moved boards since
    rows = []
    for mo in months_between(start, end):
        u = ("https://www.twse.com.tw/rwd/zh/afterTrading/"
             f"STOCK_DAY?date={mo}&stockNo={code}&response=json")
        try:
            j = requests.get(u, headers=UA, timeout=30).json()
        except Exception:                          # noqa: BLE001
            time.sleep(4)
            continue
        for r in j.get("data") or []:
            # ROC date '105/05/03'
            p = r[0].split("/")
            iso = f"{1911 + int(p[0])}-{int(p[1]):02d}-{int(p[2]):02d}"
            if start <= iso <= end:
                # STOCK_DAY field order, same shape as TPEx:
                # 0 日期 1 成交股數 2 成交金額 3 開盤價
                # 4 最高價 5 最低價 6 收盤價 7 漲跌 8 筆數
                rows.append({"d": iso, "o": _num(r[3]),
                             "h": _num(r[4]), "l": _num(r[5]),
                             "c": _num(r[6]), "v": _num(r[1])})
        time.sleep(2.2)
    rows = [r for r in rows if r["c"]]
    if not rows and _board(code) != "tpex":
        # c-232: and the reverse — a code our universe file does
        # not know, or knows as TWSE, may still be OTC. Trying
        # the other board costs one request and is the
        # difference between "delisted" and "wrong endpoint".
        rows = fetch_tpex(code, start, end)
    return rows


def harvest(only=None):
    ev = events()
    cache = (json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists()
             else {"convention":
                   "day0 = announcement-date Taipei close "
                   "(pre-news; Geneva ~23:00 CET = Taipei "
                   "+1d ~05:00); day1 = first reaction session",
                   "windows": {}})
    revs = only or sorted(ev, key=lambda r: ev[r]["ann"],
                          reverse=True)
    for rev in revs:
        e = ev.get(rev)
        if not e:
            print(f"{rev}: unknown review")
            continue
        a = (dt.date.fromisoformat(e["ann"])
             - dt.timedelta(days=PAD_PRE)).isoformat()
        b = (dt.date.fromisoformat(e["eff"])
             + dt.timedelta(days=PAD_POST)).isoformat()
        if b[:4] < "2010":
            continue
        for code, (act, name) in e["moves"].items():
            key = f"{rev}|{code}"
            old = cache["windows"].get(key)
            # c-232: an EMPTY window is not a finished one. The
            # old test was "is the key present", so the 22
            # windows that returned nothing were never asked
            # again — including the 16 TPEx names that were
            # empty because we asked the wrong board. A cache
            # that remembers failures as results cannot benefit
            # from a fix.
            if old and (old.get("px") or []):
                continue
            if old and old.get("confirmed_delisted"):
                continue
            px = fetch_window(code, a, b)
            cache["windows"][key] = {
                "rev": rev, "code": code, "action": act,
                "name": name, "ann": e["ann"],
                "ann_src": e["ann_src"], "eff": e["eff"],
                "px": px}
            OUT.write_text(json.dumps(cache), encoding="utf-8")
            print(f"{rev} {code} {act}: {len(px)} days",
                  flush=True)
    print(f"-> {OUT.name} "
          f"({len(cache['windows'])} windows)")


def status():
    if not OUT.exists():
        print("not started")
        return
    c = json.loads(OUT.read_text(encoding="utf-8"))["windows"]
    from collections import Counter
    print(f"{len(c)} windows |",
          dict(Counter(v["rev"] for v in c.values())))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "status":
        status()
    else:
        harvest(a[1:] if len(a) > 1 else None) if a and \
            a[0] == "harvest" else harvest()
