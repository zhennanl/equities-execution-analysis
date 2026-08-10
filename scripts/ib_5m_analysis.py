"""What the 5-minute bars say that daily bars cannot (c-286).

    py scripts\\ib_5m_analysis.py

The daily panel answers how big the print was and how far the
name moved. It cannot answer WHEN inside the day, and the index
trade is not a day — it is a closing auction. Three questions
follow from that, and all three are computable from what is on
disk today.

  A. THE INTRADAY VOLUME SHAPE. Share of the day's volume in
     each 5-minute bucket, effective day against the same
     name's ordinary days. A desk plans a schedule against the
     ordinary shape; on the effective date the shape is the
     schedule's problem.

  B. THE CLOSING BAR'S SHARE. What fraction of the day prints
     in the final bar. This is the capacity number for anyone
     deciding how much can go in the close, and it is the one
     number a daily bar can never contain.

  C. CLOSE AGAINST THE DAY'S VWAP, and what happens next.
     If the close prints through the day's own average and
     gives it back at the next open, the tracker paid for a
     dislocation and the arb was paid for supplying it.

BENCHMARKING IS PER NAME, NOT PER MARKET. Every share is
measured against THAT name's own ordinary days inside the same
window, so a wide market and a narrow one are comparable and no
cross-market volume normalisation is needed.

CONTROL DAYS EXCLUDE THE EVENT. Ordinary days are sessions in
the window that are not the effective date, not the two
sessions around it, and not the announcement date or the one
after it. Leaving the announcement in would put the pop into
the baseline the print is measured against.

Output: data/ib_5m_analysis.json
"""
import collections
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "ib_5m"
OUT = ROOT / "data" / "ib_5m_analysis.json"

MIN_BARS_PER_DAY = 12      # a stub session tells you nothing
MIN_CONTROL_DAYS = 5


def _by_day(px):
    """{date: [(hhmm, o, h, l, c, v)]} from the flat bar list."""
    days = collections.defaultdict(list)
    for b in px:
        ts = b[0]
        days[ts[:10]].append((ts[11:], b[1], b[2], b[3], b[4],
                              b[5] or 0))
    for d in days:
        days[d].sort()
    return days


def _trim(bars):
    """Drop trailing EMPTY bars.

    c-286, and this one nearly shipped a wrong headline. IB
    emits a bar for every 5-minute slot in the session
    template, including slots after the last trade. Singapore's
    closing auction prints in the 17:00 bar — 1,555,000 shares
    on the event checked — and IB then appends a 17:05 bar with
    zero volume. Taking "the last bar" as the closing bar
    therefore measured the empty slot, and the summary read
    "Singapore 0.0% of the day in the close" when the true
    figure is the largest bar of the session.

    Korea did the same. The tell was two markets reporting
    EXACTLY 0.0% while every other market reported something
    plausible — a clean zero across a whole market is almost
    never a market fact.
    """
    i = len(bars)
    while i and (bars[i - 1][5] or 0) <= 0:
        i -= 1
    return bars[:i]


def _shape(bars):
    """Share of the day's volume in each bar, by position."""
    tot = sum(b[5] for b in bars)
    if tot <= 0:
        return None
    return [b[5] / tot for b in bars]


def _vwap(bars):
    num = sum(((b[2] + b[3] + b[4]) / 3) * b[5] for b in bars)
    den = sum(b[5] for b in bars)
    return (num / den) if den > 0 else None


def analyse_window(v):
    """One event -> the three intraday measures, or None."""
    px, eff = v.get("px"), v.get("eff")
    if not px or not eff:
        return None
    days = _by_day(px)
    days = {d: t for d, b in days.items()
            if len(t := _trim(b)) >= MIN_BARS_PER_DAY}
    if eff not in days:
        return None
    dates = sorted(days)
    i = dates.index(eff)
    ann = v.get("ann") or ""
    # ordinary days: not the print, not its shoulders, not the
    # announcement or the session that reacts to it
    skip = set(dates[max(0, i - 1):i + 2])
    for k, d in enumerate(dates):
        if ann and d >= ann and k and dates[k - 1] < ann:
            skip.add(d)
            if k + 1 < len(dates):
                skip.add(dates[k + 1])
    ctrl = [d for d in dates if d not in skip]
    if len(ctrl) < MIN_CONTROL_DAYS:
        return None

    ebars = days[eff]
    eshape = _shape(ebars)
    if not eshape:
        return None
    # the control shape is built on the MODAL bar count, so a
    # half-day does not shift every bucket by one position
    n = collections.Counter(len(days[d]) for d in ctrl)
    modal = n.most_common(1)[0][0]
    cshapes = [s for d in ctrl if len(days[d]) == modal
               and (s := _shape(days[d]))]
    if len(cshapes) < MIN_CONTROL_DAYS or len(ebars) != modal:
        return None
    cmean = [st.mean(x) for x in zip(*cshapes)]

    e_last, c_last = eshape[-1], cmean[-1]
    vw = _vwap(ebars)
    close = ebars[-1][4]
    nxt = dates[i + 1] if i + 1 < len(dates) else None
    return {
        "market": v.get("market"), "rev": v.get("rev"),
        "code": v.get("code"), "action": v.get("action"),
        "eff": eff, "bars": modal, "control_days": len(cshapes),
        # A. the shape, kept for the chart
        "eff_shape": [round(x, 6) for x in eshape],
        "ctrl_shape": [round(x, 6) for x in cmean],
        # B. the closing bar
        "close_share": round(e_last, 6),
        "close_share_control": round(c_last, 6),
        "close_share_lift": (round(e_last / c_last, 3)
                             if c_last > 0 else None),
        # C. the close against the day it traded in
        "close_vs_vwap": (round(close / vw - 1, 6)
                          if vw else None),
        "next_open_gap": (
            round(days[nxt][0][1] / close - 1, 6)
            if nxt and days[nxt][0][1] and close else None),
        "day_volume": sum(b[5] for b in ebars),
    }


def _dist(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    def q(p):
        i = (len(xs) - 1) * p
        lo = int(i)
        hi = min(lo + 1, len(xs) - 1)
        return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)
    return {"n": len(xs), "p25": q(.25), "p50": q(.5),
            "p75": q(.75), "p90": q(.90),
            "mean": st.fmean(xs)}


def main():
    rows = []
    for f in sorted(D.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for k, v in (d.get("windows") or {}).items():
            v = dict(v)
            v["market"] = f.stem
            r = analyse_window(v)
            if r:
                rows.append(r)

    by = collections.defaultdict(list)
    for r in rows:
        by[r["market"]].append(r)

    summary = {}
    for m, rs in sorted(by.items()):
        summary[m] = {
            "n": len(rs),
            "close_share_eff": _dist(
                [r["close_share"] for r in rs]),
            "close_share_ctrl": _dist(
                [r["close_share_control"] for r in rs]),
            "close_share_lift": _dist(
                [r["close_share_lift"] for r in rs]),
            "close_vs_vwap": _dist(
                [r["close_vs_vwap"] for r in rs]),
            "next_open_gap": _dist(
                [r["next_open_gap"] for r in rs]),
            "by_side": {
                a: {"n": sum(1 for r in rs if r["action"] == a),
                    "close_share_lift": _dist(
                        [r["close_share_lift"] for r in rs
                         if r["action"] == a]),
                    "close_vs_vwap": _dist(
                        [r["close_vs_vwap"] for r in rs
                         if r["action"] == a])}
                for a in ("ADD", "DEL")},
        }

    payload = {
        "_what": "intraday measures the daily panel cannot "
                 "produce: the shape of the effective day, the "
                 "closing bar's share, and the close against "
                 "its own VWAP.",
        "_control": "ordinary sessions in the same window, "
                    "excluding the effective date and its "
                    "shoulders and the announcement reaction.",
        "n_events": len(rows), "markets": summary,
        "events": rows,
    }
    OUT.write_text(json.dumps(payload, separators=(",", ":")),
                   encoding="utf-8")
    print(f"  {len(rows)} events analysed, "
          f"{OUT.stat().st_size / 1e6:.1f} MB")
    print(f"\n  {'market':<11}{'n':>5}{'close bar %':>13}"
          f"{'normal %':>10}{'lift':>7}{'close vs vwap':>15}")
    for m, s in summary.items():
        ce, cc = s["close_share_eff"], s["close_share_ctrl"]
        lf, cv = s["close_share_lift"], s["close_vs_vwap"]
        # a market can have no lift at all: Singapore's control
        # sessions carry ZERO volume in the final bar, so the
        # ratio is undefined rather than large. Printing "—"
        # says that; a zero would have said the opposite.
        def f(d, k, fmt):
            return format(d[k], fmt) if d else "—"
        print(f"  {m:<11}{s['n']:>5}{f(ce, 'p50', '>11.1%')}"
              f"{f(cc, 'p50', '>10.1%')}"
              f"{f(lf, 'p50', '>6.1f')}x"
              f"{f(cv, 'p50', '>14.2%')}")
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
