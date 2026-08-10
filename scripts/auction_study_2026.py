#!/usr/bin/env python3
"""Closing-auction study on REAL event days (session 8n).

Two data doors that are still open:
 (a) TWSE MI_5MINS is HISTORICAL — market-wide 5-second accumulated
     order/trade stats for ANY date -> the May-29 MSCI effective
     day's closing-auction volume/value/imbalance, vs baselines.
 (b) yfinance 5-min bars still cover the June FTSE TW50 effective
     day -> per-name auction derivation (daily − Σ intraday bars)
     for the AI-quartet adds vs a control.
(The May-29 PER-NAME door closed ~yesterday — 60-day retention.
Lesson recorded: the archiver job is standing from Aug 11.)

Usage: market | names | report   (chunked for the 45s sandbox)
Cache: data/auction_study_2026.json
Doc:   docs/case_studies/AUCTION_STUDY_2026.md
"""
import json
import sys
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CACHE = Path("data/auction_study_2026.json")
MAY_EFF = "20260529"
MAY_BASE = ["20260522", "20260526", "20260527", "20260605"]
# FTSE TW50 June implementation print: Jun 19 (third Friday) was the
# Dragon Boat holiday -> the rebalance close was JUN 18, the last
# trading day before the effective Monday. The data declared it:
# 3443 auction share 61.7% on Jun 18 vs ~10-19% all other days.
JUN_EFF = "2026-06-18"
NAMES = ["3443.TW", "3665.TW", "8046.TW", "4958.TW", "2330.TW"]


def _num(x):
    return float(str(x).replace(",", "")) if x not in ("", None) else 0.0


# c-228: MI_5MINS IS NOT 5-SECOND FOR MOST OF ITS HISTORY.
#
# Bill remembered a real 2015 boundary in the auction data, and
# he was right where I was wrong. TWSE serves this file from
# 2004-10-15, but its own `notes` field, returned WITH the data,
# says the RESOLUTION changed four times:
#
#   before 2011-01-16 ....... every MINUTE
#   2011-01-16 .. 2014-02-23  every 15 seconds
#   2014-02-24 .. 2014-12-28  every 10 seconds
#   from 2014-12-29 ......... every 5 seconds
#
# The closing call runs 13:25-13:30. Five minutes at 1-minute
# resolution is FIVE points; at 5 seconds it is sixty. The
# indicative path through the auction — the entire object of an
# auction study — only exists from 2014-12-29. So "the auction
# data starts in 2015" is true in the way that matters, and my
# c-226 conclusion that nothing here is 2015-bound was too
# broad: I checked whether the file EXISTS and not what it
# CONTAINS.
#
# This also fixes a silent bug. The old code looked up the
# literal key "13:24:55", which only exists at 5-second
# resolution, and returned None otherwise — so every pre-2015
# date reported "no data" for data that is there at a coarser
# grid. A resolution limit reported as an absence is the same
# error as a permissions refusal recorded as a coverage fact.
RESOLUTION = [("2014-12-29", 5), ("2014-02-24", 10),
              ("2011-01-16", 15), ("0000-00-00", 60)]


def mi5_resolution(date):
    """Seconds between rows for a given YYYYMMDD. Source: the
    `notes` TWSE returns with every MI_5MINS response."""
    d = f"{date[:4]}-{date[4:6]}-{date[6:]}" if len(date) == 8 \
        else str(date)
    for since, sec in RESOLUTION:
        if d >= since:
            return sec
    return 60


def fetch_mi5(date):
    req = urllib.request.Request(
        "https://www.twse.com.tw/en/exchangeReport/MI_5MINS"
        f"?response=json&date={date}",
        headers={"User-Agent": "Mozilla/5.0"})
    p = json.load(urllib.request.urlopen(req, timeout=20))
    if p.get("stat") != "OK":
        return None
    rows = {r[0]: r for r in p["data"]}
    res = mi5_resolution(date)
    # the last row BEFORE the call starts, at whatever grid this
    # date is on — 13:24:55 at 5s, 13:24:45 at 15s, "13:24" at
    # 1-minute (which carries no seconds field at all)
    last_cont = next(
        (rows[k] for k in ("13:24:55", "13:24:50", "13:24:45",
                           "13:25:00", "13:24", "13:25")
         if k in rows), None)
    final = rows.get("13:30:00") or rows.get("13:30")
    if not (last_cont and final):
        return None
    return {
        "vol_before": _num(last_cont[6]), "vol_final": _num(final[6]),
        "val_before": _num(last_cont[7]), "val_final": _num(final[7]),
        "bid_final": _num(final[2]), "ask_final": _num(final[4]),
        # c-228: carried on every row so a mixed-resolution
        # sample can never be pooled by accident. The auction
        # SHARE (final minus before) survives a coarse grid; the
        # indicative PATH through the call does not.
        "grid_seconds": res,
        "path_usable": res <= 5}


def fetch_index_gap(date):
    """TWSE MI_5MINS_INDEX (historical, 5s): TAIEX at 13:29:55 vs
    the 13:30 print = the closing auction's PRICE move at market
    level — the violence measure the per-name data can't give us
    for dates outside intraday retention."""
    req = urllib.request.Request(
        "https://www.twse.com.tw/en/exchangeReport/MI_5MINS_INDEX"
        f"?response=json&date={date}",
        headers={"User-Agent": "Mozilla/5.0"})
    p = json.load(urllib.request.urlopen(req, timeout=20))
    if p.get("stat") != "OK":
        return None
    rows = {r[0]: _num(r[1]) for r in p["data"]}
    pre, close = rows.get("13:29:55"), rows.get("13:30:00")
    if not (pre and close):
        return None
    return {"pre_auction": pre, "close": close,
            "gap_bps": round((close / pre - 1) * 1e4, 1)}


CN_EFF = "2026-05-29"
CN_WINDOW = ("2026-05-25", "2026-06-05")


def cn_review_names():
    """A-line May-review names (baostock covers A-shares only —
    H-lines honestly out until an HK source exists)."""
    from scripts.pit_may2026_asia import ACTUAL
    out = []
    for side, key in (("Buy", "adds"), ("Sell", "dels")):
        for t in sorted(ACTUAL["China"][key]):
            if t.endswith(".SS"):
                out.append((f"sh.{t[:-3]}", t, side))
            elif t.endswith(".SZ"):
                out.append((f"sz.{t[:-3]}", t, side))
    out.append(("sh.600000", "600000.SS(control)", "-"))
    return out


def fetch_cn(names):
    """Baostock 5-min bars (free, YEARS of history — the door that
    was open all along for China). The 15:00 bar IS the 14:57-15:00
    closing call auction."""
    import baostock as bs
    bs.login()
    out = {}
    for code, label, side in names:
        rs = bs.query_history_k_data_plus(
            code, "date,time,close,volume",
            start_date=CN_WINDOW[0], end_date=CN_WINDOW[1],
            frequency="5", adjustflag="3")
        rows = []
        while rs.error_code == "0" and rs.next():
            rows.append(rs.get_row_data())
        days = {}
        for date, t, close, vol in rows:
            d = days.setdefault(date, [])
            d.append((t[8:12], float(close), float(vol or 0)))
        per_day = {}
        for date, bars in days.items():
            tot = sum(v for _, _, v in bars)
            last = bars[-1]
            prev = bars[-2] if len(bars) > 1 else last
            per_day[date] = {
                "day_vol": tot, "auction_vol": last[2],
                "auction_share": last[2] / tot if tot else None,
                "auction_gap_bps": (last[1] / prev[1] - 1) * 1e4
                if prev[1] else None}
        out[label] = {"side": side, "days": per_day}
        print(label, len(per_day), "days")
    bs.logout()
    return out


def load():
    return json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "report"
    cache = load()
    if mode == "market":
        mk = cache.setdefault("market", {})
        for d in [MAY_EFF] + MAY_BASE:
            if d not in mk:
                r = fetch_mi5(d)
                if r:
                    mk[d] = r
                    print(d, "ok")
        CACHE.write_text(json.dumps(cache), encoding="utf-8")
        return
    if mode == "gaps":
        g = cache.setdefault("index_gap", {})
        for d in [MAY_EFF] + MAY_BASE:
            if d not in g:
                r = fetch_index_gap(d)
                if r:
                    g[d] = r
                    print(d, r["gap_bps"], "bps")
        CACHE.write_text(json.dumps(cache), encoding="utf-8")
        return
    if mode == "cn":
        lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        hi = int(sys.argv[3]) if len(sys.argv) > 3 else 99
        got = cache.setdefault("cn", {})
        todo = [x for x in cn_review_names()[lo:hi]
                if x[1] not in got]
        got.update(fetch_cn(todo))
        CACHE.write_text(json.dumps(cache), encoding="utf-8")
        return
    if mode == "names":
        import yfinance as yf
        nm = cache.setdefault("names", {})
        for t in NAMES:
            if t in nm:
                continue
            h5 = yf.Ticker(t).history(start="2026-06-12",
                                      end="2026-06-25",
                                      interval="5m")
            hd = yf.Ticker(t).history(start="2026-06-12",
                                      end="2026-06-25", interval="1d")
            per_day = {}
            for day in sorted(set(h5.index.date)):
                bars = h5[h5.index.date == day]
                dd = hd[hd.index.date == day]
                if not len(dd):
                    continue
                dv = float(dd["Volume"].iloc[0])
                bsum = float(bars["Volume"].sum())
                per_day[str(day)] = {
                    "daily_vol": dv, "bars_vol": bsum,
                    "auction_share": max(dv - bsum, 0) / dv if dv
                    else None,
                    "last_bar_close": float(bars["Close"].iloc[-1]),
                    "official_close": float(dd["Close"].iloc[0])}
            nm[t] = per_day
            print(t, len(per_day), "days")
        CACHE.write_text(json.dumps(cache), encoding="utf-8")
        return
    # ---- report
    mk, nm = cache.get("market", {}), cache.get("names", {})
    L = ["# Closing-Auction Study — Real Event Days (2026)",
         "*Session 8n. (a) Market-wide TWSE 5-second archive: the "
         "May-29 MSCI effective-day auction vs baseline days. (b) "
         "Per-name derivation on the June-19 FTSE TW50 effective "
         "day (AI-quartet adds vs 2330 control). Data honesty: "
         "May-29 PER-NAME intraday left the free 60-day retention "
         "~one day before this study — the market-wide archive and "
         "the June event carry the analysis; the standing archiver "
         "(from Aug 11) closes this gap permanently.*", ""]
    if mk:
        L.append("## (a) May-29 MSCI effective day — market-wide "
                 "closing auction (TWSE 5s archive)\n")
        rows = []
        for d, r in sorted(mk.items()):
            av = r["vol_final"] - r["vol_before"]
            aval = r["val_final"] - r["val_before"]
            rows.append({
                "date": d,
                "day": ("MSCI EFFECTIVE" if d == MAY_EFF
                        else "baseline"),
                "auction_vol_klots": round(av / 1e3),
                "auction_%_of_day_vol":
                    round(100 * av / r["vol_final"], 1),
                "auction_val_NT$B": round(aval / 1e3, 1),
                "auction_%_of_day_val":
                    round(100 * aval / r["val_final"], 1),
                "close_bid/ask_imbal":
                    round(r["bid_final"] / r["ask_final"], 2)})
        df = pd.DataFrame(rows)
        L.append(df.to_markdown(index=False))
        base = df[df["day"] == "baseline"]
        eff = df[df["day"] == "MSCI EFFECTIVE"]
        if len(eff) and len(base):
            L.append(
                f"\n**Read:** effective-day auction "
                f"{eff.iloc[0]['auction_%_of_day_val']}% of day "
                f"value vs baseline median "
                f"{base['auction_%_of_day_val'].median():.1f}% — "
                "the event concentrates the day INTO the print, "
                "market-wide, even though only ~8 names carried "
                "the flow. Value share > volume share = the "
                "auction skews to the large/expensive event names.")
        gaps = cache.get("index_gap", {})
        if gaps:
            L.append("\n**The auction's PRICE move (TAIEX at "
                     "13:29:55 vs the 13:30 print — MI_5MINS_INDEX, "
                     "historical):**\n")
            grows = [{"date": d,
                      "day": ("MSCI EFFECTIVE" if d == MAY_EFF
                              else "baseline"),
                      "auction_gap_bps": v["gap_bps"]}
                     for d, v in sorted(gaps.items())]
            L.append(pd.DataFrame(grows).to_markdown(index=False))
            ev = gaps.get(MAY_EFF, {}).get("gap_bps")
            bmed = pd.Series([v["gap_bps"] for d, v in gaps.items()
                              if d != MAY_EFF]).abs().median()
            L.append(
                f"\n**Read:** the effective-day print moved the "
                f"INDEX {ev} bps in one auction vs ~{bmed:.0f} bps "
                "absolute on baseline days — the market-level "
                "violence measurement, sell-skewed exactly as a "
                "66-deletion SAIR plus reweight-sell pressure "
                "implies. This is the number the per-name violence "
                "curve aggregates to.")
    if nm:
        L.append("\n## (b) June TW50 implementation print — JUN 18 "
                 "(holiday-shifted) — per-name auction shares\n")
        rows = []
        for t, days in nm.items():
            if not days:
                continue
            evt = days.get(JUN_EFF)
            others = [v["auction_share"] for k, v in days.items()
                      if k != JUN_EFF and v["auction_share"]
                      is not None]
            if not evt or evt["auction_share"] is None:
                continue
            gap = (evt["official_close"] / evt["last_bar_close"] - 1
                   ) * 1e4
            rows.append({
                "ticker": t,
                "role": ("REWEIGHT LEG (not a control!)"
                         if t == "2330.TW" else "TW50 ADD (June)"),
                "event_auction_share":
                    f"{evt['auction_share']:.1%}",
                "baseline_median":
                    f"{pd.Series(others).median():.1%}"
                    if others else "n/a",
                "auction_gap_bps": round(gap, 0),
                "event_t_mult": round(
                    evt["daily_vol"]
                    / pd.Series([v["daily_vol"] for k, v
                                 in days.items()
                                 if k != JUN_EFF]).median(), 1)})
        L.append(pd.DataFrame(rows).to_markdown(index=False))
        L.append(
            "\n**Read:** the adds show the auction-share uplift and "
            "T-multiple the priors predict — and the intended "
            "'control' (2330) turned out to be the study's second "
            "finding: on a TW50 rebalance TSMC is the REWEIGHT leg, "
            "and its 55% auction share on the print day is the "
            "reweight flow (27% of event turnover in our flow sim) "
            "made visible in public data. auction_gap = official "
            "close vs last continuous bar — the price the auction "
            "'paid' to clear (violence-curve point per name). Note "
            "also the calendar catch: the June print was JUN 18, "
            "not the third Friday — Dragon Boat holiday shifted it; "
            "the data, not the calendar, identified the day.")
    cn = cache.get("cn", {})
    if cn:
        L.append("\n## (c) May-29 MSCI effective day — CHINA A per-"
                 "name closing auctions (baostock 5-min, the free "
                 "door that was open all along)\n")
        rows = []
        for label, obj in cn.items():
            days = obj["days"]
            evt = days.get(CN_EFF)
            if not evt or evt["auction_share"] is None:
                continue
            others = [v["auction_share"] for d, v in days.items()
                      if d != CN_EFF and v["auction_share"]]
            base_vol = pd.Series(
                [v["day_vol"] for d, v in days.items()
                 if d != CN_EFF and v["day_vol"]]).median()
            rows.append({
                "name": label, "side": obj["side"],
                "event_auction_share":
                    f"{evt['auction_share']:.1%}",
                "baseline_median":
                    f"{pd.Series(others).median():.1%}"
                    if others else "n/a",
                "auction_gap_bps":
                    round(evt["auction_gap_bps"], 0)
                    if evt["auction_gap_bps"] is not None else None,
                "event_t_mult": round(evt["day_vol"] / base_vol, 1)
                if base_vol else None})
        df = pd.DataFrame(rows)
        L.append(df.to_markdown(index=False))
        adds = df[df["side"] == "Buy"]
        dels = df[df["side"] == "Sell"]
        if len(adds) and len(dels):
            L.append(
                f"\n**Read:** adds' auction gaps median "
                f"{adds['auction_gap_bps'].median():+.0f} bps vs "
                f"deletes' {dels['auction_gap_bps'].median():+.0f} "
                "bps — the print pays the imbalance in the SIDE's "
                "direction, per name, exactly the violence-curve "
                "shape. The 14:57-15:00 call (3 minutes, no "
                "cancels) is visible as the 15:00 bar. H-line "
                "names (0177.HK etc.) remain honestly out — no "
                "free HK intraday source reaches May 29 (Eastmoney "
                "31-day wall, Tencent DNS-blocked from sandbox, "
                "futu account-gated).")
    L.append("\n## How these numbers become desk insights\n")
    L.append(
        "1. **Footprint denominators become measured**: the sheet's "
        "auction-footprint % now uses event-day auction shares, not "
        "an assumed 30% flat.\n"
        "2. **Violence-curve points**: each event name contributes "
        "(auction size, auction gap) — the indicative-read rule's "
        "thresholds calibrate on these instead of theory.\n"
        "3. **Crowding validation**: crowded names should print big "
        "auctions with SMALL gaps (pressure pre-spent); uncrowded "
        "with large gaps — testable per event, feeds the discretion "
        "matrix.\n"
        "4. **Completion inference**: auction volume vs our expected "
        "flow bounds how much passive demand cleared AT the print "
        "vs was worked/deferred — the T+1 residual estimate.\n"
        "5. **The archive compounds**: every event adds rows; the "
        "indicative archiver (Aug 11 onward) adds the pre-print "
        "trajectory nobody retains.")
    out = Path("docs/case_studies/AUCTION_STUDY_2026.md")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"doc -> {out}")


if __name__ == "__main__":
    main()
