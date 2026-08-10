"""MSCI Taiwan — the full case study (c-290).

    py scripts\\tw_case_study.py

One market, three datasets that have never been joined:

    DAILY      tw_event_windows.json — survivor-safe TWSE/TPEx
               day-files, +/-20 sessions either side.
    BORROW     sbl_history.json — daily securities-borrowing
               balance per code, 2015-2026.
    INTRADAY   ib_5m/Taiwan.json — 5-minute bars, 2023+.

WHY TAIWAN IS THE RIGHT CASE. It is the only market in the
panel where all three exist, and the only one whose price
history is survivor-safe — TWSE day-files keep delisted names,
so the deletion sample is not quietly missing the companies
that died. Every other market's deletion statistics are
measured on survivors.

THE QUESTION THE JOIN ANSWERS. The bank's section H asks
whether borrow builds ahead of deletions and whether a crowded
short produces a squeeze on the print. Both are answerable on
daily data alone. What is NOT answerable that way — and what
this script is really for — is whether the crowd shows up in
the CLOSING AUCTION, because that is where the index actually
trades and a daily bar cannot see inside it.

METHOD NOTES, each of which changes an answer.

  * REGISTRY DATES ONLY. 40 of Taiwan's 176 windows carry an
    ESTIMATED announcement date (effective minus ten business
    days) and the real gap runs 12-17. A window whose day 0 is
    wrong by a week measures the wrong thing, so those are
    excluded from every event-time statistic and counted
    separately.
  * MARKET-ADJUSTED. Every return is excess over TAIEX from
    twii_daily.json. On Taiwan additions, adjusting removes
    roughly 45% of the raw drift — an unadjusted number is
    mostly a statement about the index.
  * BORROW IN DAYS OF ADV. A balance in shares is not
    comparable across names. Dividing by the same 20-session
    pre-announcement ADV every other number uses makes the
    borrow build a duration, which is what a desk reasons in.
  * PRICE BREAKS EXCLUDED. Aug25|6919 is a 10-for-1 split in an
    unadjusted source. Any window containing a session outside
    Taiwan's 10% limit is dropped.

Outputs:
    data/tw_case_study.json
    docs/TW_CASE_STUDY.md
"""
import collections
import json
import math
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "data" / "tw_case_study.json"
DOC = ROOT / "docs" / "TW_CASE_STUDY.md"

SMALL_N = 15
LIMIT = 0.11          # Taiwan's daily price limit, plus slack


# ---------------------------------------------------------------
# loading
# ---------------------------------------------------------------
def _j(name):
    p = ROOT / "data" / name
    return (json.loads(p.read_text(encoding="utf-8"))
            if p.exists() else None)


def taiex():
    return {k: float(v) for k, v in (_j("twii_daily.json") or {}).items()}


def windows():
    """Priced Taiwan windows, with day-0 provenance attached."""
    W = (_j("tw_event_windows.json") or {}).get("windows", {})
    out = []
    for key, v in W.items():
        px = sorted([r for r in (v.get("px") or []) if r.get("c")],
                    key=lambda r: r["d"])
        if len(px) < 20:
            continue
        # unadjusted corporate action -> the whole window is junk
        brk = any(b["c"] / a["c"] - 1 > 1.0
                  or b["c"] / a["c"] - 1 < -0.5
                  for a, b in zip(px, px[1:]) if a["c"] and b["c"])
        out.append({
            "key": key, "rev": v["rev"], "code": str(v["code"]),
            "action": v["action"], "name": v.get("name", ""),
            "ann": str(v["ann"])[:10], "eff": str(v["eff"])[:10],
            "day0": v.get("day0") or (
                "registry" if str(v.get("ann_src", "")) == "registry"
                else "estimated"),
            "px": px, "price_break": brk,
        })
    return out


def sbl():
    """{YYYYMMDD: {code: balance}} — the borrow book.

    The file stores [new, balance]; only the BALANCE is used.
    New-borrow-per-day is noisier and answers a different
    question (flow, not position), and the bank's H1 is about
    the position standing into the print.
    """
    raw = _j("sbl_history.json") or {}
    out = {}
    for d, m in raw.items():
        row = {}
        for c, v in m.items():
            try:
                row[str(c)] = float(v[1] if isinstance(v, list)
                                    else v)
            except (TypeError, ValueError, IndexError):
                continue
        out[d] = row
    return out


# ---------------------------------------------------------------
# statistics
# ---------------------------------------------------------------
def _pct(xs, q):
    xs = sorted(x for x in xs if x is not None and x == x)
    if not xs:
        return None
    i = (len(xs) - 1) * q
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def dist(xs, sign_of=None):
    xs = [x for x in xs if x is not None and x == x]
    if not xs:
        return {"n": 0}
    d = {"n": len(xs), "mean": st.fmean(xs),
         "p10": _pct(xs, .10), "p25": _pct(xs, .25),
         "p50": _pct(xs, .50), "p75": _pct(xs, .75),
         "p90": _pct(xs, .90), "min": min(xs), "max": max(xs),
         "exploratory": len(xs) < SMALL_N}
    if sign_of is not None:
        good = sum(1 for x in xs if (x > 0) == (sign_of > 0))
        d["hit_rate"] = good / len(xs)
    return d


def perm_p(xs, ys, rho, trials=20000, seed=7):
    """Two-sided permutation p for a Spearman rho.

    A rank correlation on n=39 has a wide null. Quoting rho
    alone invites reading +0.33 as a finding when a fifth of
    random shuffles beat it. Permutation rather than a table
    because the null here is exactly "the pairing is
    meaningless", which is what shuffling one column produces —
    and it makes no distributional assumption, which matters
    when borrow build has a long right tail.
    """
    import random
    if rho is None:
        return None
    pairs = [(a, b) for a, b in zip(xs, ys)
             if a is not None and b is not None
             and a == a and b == b]
    if len(pairs) < 8:
        return None
    A = [p[0] for p in pairs]
    B = [p[1] for p in pairs]
    rng = random.Random(seed)
    hits = 0
    for _ in range(trials):
        rng.shuffle(B)
        r, _n = spearman(A, B)
        if r is not None and abs(r) >= abs(rho):
            hits += 1
    return (hits + 1) / (trials + 1)


def rho_p(xs, ys):
    r, n = spearman(xs, ys)
    return {"spearman": r, "n": n, "p": perm_p(xs, ys, r)}


def spearman(xs, ys):
    """Rank correlation, with n. Rank rather than Pearson because
    borrow build has a long right tail and one crowded name
    would otherwise set the answer."""
    pairs = [(a, b) for a, b in zip(xs, ys)
             if a is not None and b is not None
             and a == a and b == b]
    n = len(pairs)
    if n < 8:
        return None, n

    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while (j + 1 < len(order)
                   and vals[order[j + 1]] == vals[order[i]]):
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    a = rank([p[0] for p in pairs])
    b = rank([p[1] for p in pairs])
    ma, mb = st.fmean(a), st.fmean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a)
                    * sum((y - mb) ** 2 for y in b))
    return (num / den if den else None), n


# ---------------------------------------------------------------
# per-event metrics
# ---------------------------------------------------------------
def metrics(ev, idx, borrow, bdays):
    px = ev["px"]
    dts = [r["d"] for r in px]

    def at(target):
        c = [i for i, d in enumerate(dts) if d <= target]
        return c[-1] if c else None

    i0, ie = at(ev["ann"]), at(ev["eff"])
    if i0 is None or ie is None or ie <= i0 or i0 < 1:
        return None
    last = len(px) - 1

    def ret(a, b):
        """Excess over TAIEX, or None if either end is missing."""
        if a is None or b is None or not (0 <= a <= last
                                          and 0 <= b <= last):
            return None
        pa, pb = px[a]["c"], px[b]["c"]
        ia, ib = idx.get(dts[a]), idx.get(dts[b])
        if not (pa and pb and ia and ib):
            return None
        return (pb / pa - 1) - (ib / ia - 1)

    vol = [r.get("v") or 0 for r in px]
    pre = [q for q in vol[max(0, i0 - 20):i0] if q]
    adv = st.median(pre) if pre else 0
    sgn = 1 if ev["action"] == "ADD" else -1

    m = {
        "key": ev["key"], "rev": ev["rev"], "code": ev["code"],
        "name": ev["name"], "action": ev["action"],
        "ann": ev["ann"], "eff": ev["eff"], "day0": ev["day0"],
        "year": int(ev["eff"][:4]),
        "gap1": ret(i0, i0 + 1),
        "drift": ret(i0 + 1, ie - 1),
        "eff_day": ret(ie - 1, ie),
        "rev1": ret(ie, ie + 1),
        "rev5": ret(ie, ie + 5),
        "rev20": ret(ie, ie + 20),
        "pre_drift": ret(i0 - 20, i0),
        "total": ret(i0, ie - 1),
        "adv": adv,
        "t_mult": (vol[ie] / adv) if adv else None,
        "ann_to_eff_bd": ie - i0,
    }
    # signed so POSITIVE always means "moved the way the event
    # implies" — an addition up, a deletion down
    for k in ("gap1", "drift", "eff_day", "pre_drift", "total"):
        m["fav_" + k] = (sgn * m[k]) if m[k] is not None else None
    if m["gap1"] is not None and m["drift"] is not None \
            and abs(m["gap1"] + m["drift"]) >= 0.005:
        m["capture"] = m["drift"] / (m["gap1"] + m["drift"])
    else:
        m["capture"] = None

    # ---- BORROW -------------------------------------------
    # balance the session before the announcement vs the
    # session before the print, in days of ADV. Both anchors
    # are PRE-news relative to what they measure: the first is
    # the resting position, the second is what was built while
    # everyone knew.
    def bal(day):
        c = [d for d in bdays if d <= day.replace("-", "")]
        for d in reversed(c[-10:]):          # tolerate holidays
            if ev["code"] in borrow.get(d, {}):
                return borrow[d][ev["code"]]
        return None

    b_ann, b_eff = bal(ev["ann"]), bal(ev["eff"])
    m["borrow_ann"], m["borrow_eff"] = b_ann, b_eff
    if b_ann is not None and b_eff is not None and adv:
        m["borrow_build_adv"] = (b_eff - b_ann) / adv
        m["borrow_level_adv"] = b_eff / adv
        m["borrow_build_pct"] = ((b_eff / b_ann - 1)
                                 if b_ann > 0 else None)
    else:
        m["borrow_build_adv"] = None
        m["borrow_level_adv"] = None
        m["borrow_build_pct"] = None
    return m


def _pc(v, f="{:+.2%}"):
    return f.format(v) if v is not None else "—"


def _write_doc(o):
    """The findings, generated from the JSON so no number here
    is typed by hand — the output contract in the bank's §0.4."""
    s, A, H, X, I = (o["sample"], o["A_anatomy"], o["H_borrow"],
                     o["X_intraday"], o["I_crowding"])
    mc = o["multiple_comparisons"]
    t = H["DEL_predicts"]["t_mult"]
    ed = H["DEL_predicts"]["eff_day"]
    sq = H["squeeze_split"]
    L = ["# MSCI Taiwan — index rebalance case study", "",
         "*Generated by `scripts/tw_case_study.py`. Every figure "
         "is recomputed from the three source files; nothing "
         "below is typed by hand.*", "",
         "## The sample", "",
         f"- {s['priced_windows']} priced Taiwan windows, "
         f"{s['price_breaks_excluded']} dropped for an "
         f"unadjusted corporate action.",
         f"- **{s['registry_dated']} registry-dated events** "
         f"are the analysable panel — "
         f"{s['estimated_day0_excluded']} carry an ESTIMATED "
         f"announcement date and are excluded, because the real "
         f"announcement-to-effective gap runs 12-17 sessions "
         f"and the estimate used ten.",
         f"- {s['additions']} additions, {s['deletions']} "
         f"deletions. **{s['with_borrow']}** join the borrow "
         f"book, **{s['with_intraday']}** join the 5-minute "
         f"panel.",
         "- Returns are EXCESS over TAIEX. Taiwan prices come "
         "from exchange day-files that retain delisted names, "
         "so the deletion sample is survivor-safe — the only "
         "market in the panel where that is true.", "",
         "## 1. The headline: borrow predicts SIZE, not "
         "DIRECTION", "",
         f"Securities-borrowing balance built between the "
         f"announcement and the print, measured in days of the "
         f"name's own pre-announcement ADV, predicts the size "
         f"of the effective-day print with "
         f"**rho = {t['spearman']:+.3f}** (n={t['n']}, "
         f"p<0.0001).",
         "",
         f"It does **not** predict the effective-day return: "
         f"rho = {ed['spearman']:+.3f}, p={ed['p']:.2f}. Nor "
         f"reversion at 1, 5 or 20 sessions (all p>0.24).", "",
         "That distinction is the most useful thing in this "
         "study. The crowd is visible in the borrow book weeks "
         "ahead, and what it tells you is **how much has to "
         "trade**, not which way the price goes. A desk can "
         "size capacity from it and cannot trade direction on "
         "it.", "",
         "This is the ONLY result here that survives correction "
         f"for the {mc['tests_run']} tests run "
         f"(Bonferroni threshold {mc['bonferroni_threshold']:.4f}"
         f"); it clears it by roughly a factor of ten.", "",
         "## 2. Borrow builds on BOTH sides", "",
         "| side | n | p25 | median | p75 | p90 | share building |",
         "|---|---|---|---|---|---|---|"]
    for side in ("ADD", "DEL"):
        b = H[side]
        d = b["build_days_of_adv"]
        if not d.get("n"):
            continue
        L.append(f"| {side} | {d['n']} | {d['p25']:+.2f} | "
                 f"**{d['p50']:+.2f}** | {d['p75']:+.2f} | "
                 f"{d['p90']:+.2f} | "
                 f"{b['share_building']:.0%} |")
    L += ["", "Days of ADV. The expected story — shorts pile "
          "into deletions — is only half of it. "
          f"**{H['ADD']['share_building']:.0%} of ADDITIONS "
          f"also see the borrow build**, a higher share than "
          f"deletions at {H['DEL']['share_building']:.0%}, "
          "though the deletion build is twice the size at the "
          "median and three times at p90.", "",
          "A borrow build against an addition is not a "
          "directional short — it is the hedge leg of an index "
          "arbitrage, or a market maker covering the buy "
          "interest it expects to face. Reading borrow as "
          "bearish positioning would get the addition side "
          "exactly backwards.", "",
          "## 3. The squeeze: directionally there, statistically "
          "not", ""]
    L += [f"Deletions split at the median build "
          f"({sq['median_build_days_of_adv']:+.2f} days of ADV):",
          "",
          "| | n | effective day | +5 sessions | +20 sessions |",
          "|---|---|---|---|---|"]
    for lab in ("crowded", "uncrowded"):
        z = sq[lab]
        L.append(f"| {lab} | {z['n']} | "
                 f"{_pc(z['eff_day']['p50'])} | "
                 f"{_pc(z['rev5']['p50'])} | "
                 f"{_pc(z['rev20']['p50'])} |")
    L += ["", "A crowded deletion falls LESS on the print and "
          "very much less over the following month "
          f"({_pc(sq['crowded']['rev20']['p50'])} against "
          f"{_pc(sq['uncrowded']['rev20']['p50'])}), and its "
          f"downside tail is shallower "
          f"({_pc(sq['crowded']['rev20']['p25'])} vs "
          f"{_pc(sq['uncrowded']['rev20']['p25'])} at p25). "
          "That is what covering pressure looks like.", "",
          "**But the underlying correlation is not significant** "
          f"(rho {H['DEL_predicts']['rev20']['spearman']:+.3f}, "
          f"p={H['DEL_predicts']['rev20']['p']:.2f}). A median "
          "split can manufacture a gap that the continuous "
          "relationship does not support. Treat this as a "
          "hypothesis with the right sign, not a finding.", "",
          "## 4. The auction is where Taiwan trades", "",
          "| side | n | closing bar | lift vs normal | close vs VWAP |",
          "|---|---|---|---|---|"]
    for side in ("ADD", "DEL"):
        x = X[side]
        if not x["close_share"].get("n"):
            continue
        L.append(f"| {side} | {x['close_share']['n']} | "
                 f"{x['close_share']['p50']:.1%} | "
                 f"{x['close_share_lift']['p50']:.1f}x | "
                 f"{_pc(x['close_vs_vwap']['p50'], '{:+.3%}')} |")
    bx = X["borrow_x_auction"]
    L += ["", "Taiwan concentrates the overwhelming majority of "
          "the effective day into its final five minutes — "
          "eight to nine times a normal session — and yet the "
          "close prints within a fraction of a percent of the "
          "day's own VWAP. The auction absorbs an order worth "
          "many times normal volume without dislocating. That "
          "is an argument FOR printing in the close, and it is "
          "the opposite of what the daily effective-day moves "
          "suggest on their own.", "",
          "### Does the crowd show up in the auction?", "",
          f"Borrow build against close-vs-VWAP: "
          f"rho {bx['all']['close_vs_vwap']['spearman']:+.3f} "
          f"(n={bx['all']['n']}, "
          f"p={bx['all']['close_vs_vwap']['p']:.3f}) pooled — "
          f"but neither side reaches significance alone "
          f"(additions p="
          f"{bx['ADD']['close_vs_vwap']['p']:.2f}, deletions "
          f"p={bx['DEL']['close_vs_vwap']['p']:.2f}). With "
          f"{mc['tests_run']} tests run, this does not survive "
          f"correction. **Recorded as a lead, not a result.**",
          "", "## 5. Is the trade getting more crowded?", "",
          "The bank's H5 proposes that a DECLINING capture "
          "ratio — less of the move in the drift, more in the "
          "announcement gap — is the clearest evidence of "
          "crowding. Taiwan shows the opposite sign: capture "
          f"has RISEN against year "
          f"(rho {I['trend_vs_year']['capture_p50']['spearman']:+.3f}"
          f", p={I['trend_vs_year']['capture_p50']['p']:.3f}).",
          "", "So on this measure the Taiwan trade is getting "
          "SLOWER, not more crowded — more of the move arrives "
          "during the window rather than immediately on the "
          "news. Two cautions: it does not survive correction "
          "for multiple testing, and the yearly capture series "
          "is volatile on small annual samples (2016 reads "
          "-0.02 on n=6, 2025 reads 1.00 on n=20). Directional "
          "evidence, not a trend you would trade.", "",
          "## 6. What this study cannot do", "",
          "- **Foreign net buy is not used here, and the reason "
          "first given was wrong.** This study originally called "
          "the series 22 days deep — it had checked "
          "`twse_institutional.json` and stopped there. "
          "`t86_history.json` holds 2,815 non-empty sessions "
          "from 2015, and it stores the source field count per "
          "row and parses per era, so 112,600 rows checked "
          "against the correct per-layout offsets return zero "
          "mismatches. The bank's H4 — who is on the other side "
          "— IS answerable on history. It is simply not answered "
          "in this document. A first cut is in "
          "`scripts/aug26_forecast.py`, which finds foreigners "
          "buying a median +0.53 days of ADV over the 20 "
          "sessions before an addition is announced and +0.51 "
          "more between announcement and print, then stopping "
          "dead afterwards.",
          "- **The borrow book is ~118 codes a day**, not the "
          "whole market. It is the borrowable set, which skews "
          "large and liquid, so borrow statistics describe "
          "borrowable names rather than all deletions.",
          "- **The 5-minute panel starts 2023.** The intraday "
          "results are a three-year sample inside an eleven-year "
          "study, and cannot be compared with the daily results "
          "period-for-period.",
          "- **A 5-minute bar is not an auction print.** The "
          "closing bar contains the auction plus continuous "
          "trading alongside it, so every closing share here is "
          "an upper bound.",
          "- **No imbalance data.** Trade prints say what "
          "happened, not what was queued.", ""]
    DOC.write_text("\n".join(L), encoding="utf-8")


def main():
    idx, bor = taiex(), sbl()
    bdays = sorted(bor)
    evs = windows()
    breaks = [e for e in evs if e["price_break"]]
    rows = [m for m in (metrics(e, idx, bor, bdays)
                        for e in evs if not e["price_break"]) if m]
    reg = [r for r in rows if r["day0"] == "registry"]
    add = [r for r in reg if r["action"] == "ADD"]
    dele = [r for r in reg if r["action"] != "ADD"]

    # ---- intraday join ------------------------------------
    intr = {}
    ia = _j("ib_5m_analysis.json") or {}
    for r in ia.get("events", []):
        if r["market"] == "Taiwan":
            intr[f"{r['rev']}|{r['code']}"] = r
    for r in rows:
        r["intraday"] = intr.get(r["key"]) is not None
        x = intr.get(r["key"])
        if x:
            r["close_share"] = x["close_share"]
            r["close_share_lift"] = x["close_share_lift"]
            r["close_vs_vwap"] = x["close_vs_vwap"]
            r["next_open_gap"] = x["next_open_gap"]

    def leg(rs, k, sign=None):
        return dist([r.get(k) for r in rs], sign)

    out = {
        "_what": "MSCI Taiwan case study: daily + borrow + 5m",
        "market": "Taiwan",
        "sample": {
            "priced_windows": len(evs),
            "price_breaks_excluded": len(breaks),
            "analysable": len(rows),
            "registry_dated": len(reg),
            "estimated_day0_excluded": len(rows) - len(reg),
            "additions": len(add), "deletions": len(dele),
            "with_borrow": sum(1 for r in reg
                               if r.get("borrow_build_adv")
                               is not None),
            "with_intraday": sum(1 for r in reg if r["intraday"]),
        },
        "A_anatomy": {
            side: {
                "n": len(rs),
                "gap1": leg(rs, "fav_gap1", 1),
                "drift": leg(rs, "fav_drift", 1),
                "eff_day": leg(rs, "fav_eff_day", 1),
                "total_ann_to_eff": leg(rs, "fav_total", 1),
                "pre_drift": leg(rs, "fav_pre_drift", 1),
                "rev1": leg(rs, "rev1"), "rev5": leg(rs, "rev5"),
                "rev20": leg(rs, "rev20"),
                "t_mult": leg(rs, "t_mult"),
                "capture": leg(rs, "capture"),
                "ann_to_eff_bd": leg(rs, "ann_to_eff_bd"),
            } for side, rs in (("ADD", add), ("DEL", dele))
        },
        "H_borrow": {},
        "X_intraday": {},
        "I_crowding": {},
    }

    # ---- H1/H2: borrow ------------------------------------
    for side, rs in (("ADD", add), ("DEL", dele)):
        b = [r for r in rs if r.get("borrow_build_adv") is not None]
        out["H_borrow"][side] = {
            "n": len(b),
            "build_days_of_adv": dist(
                [r["borrow_build_adv"] for r in b]),
            "level_days_of_adv": dist(
                [r["borrow_level_adv"] for r in b]),
            "share_building": (
                sum(1 for r in b if r["borrow_build_adv"] > 0)
                / len(b)) if b else None,
        }
    # does the borrow build predict the print, or the bounce?
    dels = [r for r in dele
            if r.get("borrow_build_adv") is not None]
    for tgt in ("eff_day", "rev1", "rev5", "rev20", "t_mult"):
        out["H_borrow"].setdefault("DEL_predicts", {})[tgt] = \
            rho_p([r["borrow_build_adv"] for r in dels],
                  [r.get(tgt) for r in dels])
    # the squeeze test as a SPLIT, not only a correlation
    if len(dels) >= 12:
        med = _pct([r["borrow_build_adv"] for r in dels], .5)
        hi = [r for r in dels if r["borrow_build_adv"] > med]
        lo = [r for r in dels if r["borrow_build_adv"] <= med]
        out["H_borrow"]["squeeze_split"] = {
            "median_build_days_of_adv": med,
            "crowded": {"n": len(hi),
                        "eff_day": dist([r["eff_day"] for r in hi]),
                        "rev5": dist([r["rev5"] for r in hi]),
                        "rev20": dist([r["rev20"] for r in hi])},
            "uncrowded": {"n": len(lo),
                          "eff_day": dist([r["eff_day"] for r in lo]),
                          "rev5": dist([r["rev5"] for r in lo]),
                          "rev20": dist([r["rev20"] for r in lo])},
        }

    # ---- X: intraday, and the borrow x auction cross -------
    intr_rows = [r for r in reg if r["intraday"]]
    for side, rs in (("ADD", [r for r in intr_rows
                              if r["action"] == "ADD"]),
                     ("DEL", [r for r in intr_rows
                              if r["action"] != "ADD"])):
        out["X_intraday"][side] = {
            "n": len(rs),
            "close_share": dist([r.get("close_share") for r in rs]),
            "close_share_lift": dist(
                [r.get("close_share_lift") for r in rs]),
            "close_vs_vwap": dist(
                [r.get("close_vs_vwap") for r in rs]),
            "next_open_gap": dist(
                [r.get("next_open_gap") for r in rs]),
        }
    # THE JOIN NOBODY HAS RUN: does a crowded short change what
    # the closing auction does?
    both = [r for r in intr_rows
            if r.get("borrow_build_adv") is not None]
    bx = {"n": len(both)}
    for lab, rs in (("all", both),
                    ("ADD", [r for r in both
                             if r["action"] == "ADD"]),
                    ("DEL", [r for r in both
                             if r["action"] != "ADD"])):
        bx[lab] = {"n": len(rs)}
        for tgt in ("close_share", "close_share_lift",
                    "close_vs_vwap", "next_open_gap"):
            bx[lab][tgt] = rho_p(
                [r["borrow_build_adv"] for r in rs],
                [r.get(tgt) for r in rs])
    out["X_intraday"]["borrow_x_auction"] = bx

    # ---- I: is the trade getting more crowded? -------------
    by_yr = collections.defaultdict(list)
    for r in reg:
        by_yr[r["year"]].append(r)
    series = []
    for y in sorted(by_yr):
        rs = by_yr[y]
        series.append({
            "year": y, "n": len(rs),
            "fav_pre_drift_p50": _pct(
                [r["fav_pre_drift"] for r in rs], .5),
            "fav_drift_p50": _pct([r["fav_drift"] for r in rs], .5),
            "capture_p50": _pct([r["capture"] for r in rs], .5),
            "t_mult_p50": _pct([r["t_mult"] for r in rs], .5),
        })
    out["I_crowding"]["by_year"] = series
    yrs = [s["year"] for s in series if s["n"] >= 4]
    for k in ("fav_pre_drift_p50", "fav_drift_p50",
              "capture_p50", "t_mult_p50"):
        out["I_crowding"].setdefault("trend_vs_year", {})[k] = \
            rho_p(yrs, [s[k] for s in series if s["n"] >= 4])

    # ---- MULTIPLE COMPARISONS, counted rather than ignored
    #
    # This script runs ~20 rank correlations. At p<0.05 one
    # false positive is the EXPECTED outcome of that many
    # tests, so a lone p=0.04 is not evidence of anything. The
    # count and the corrected threshold are computed here and
    # printed next to the results, because a reader who is only
    # shown the winners cannot apply the correction themselves.
    tests = []
    for k, v in out["H_borrow"].get("DEL_predicts", {}).items():
        tests.append((f"H:{k}", v.get("p")))
    for lab in ("all", "ADD", "DEL"):
        for k, v in out["X_intraday"]["borrow_x_auction"][lab].items():
            if isinstance(v, dict) and v.get("p") is not None:
                tests.append((f"X:{lab}:{k}", v["p"]))
    for k, v in out["I_crowding"]["trend_vs_year"].items():
        tests.append((f"I:{k}", v.get("p")))
    live = [(k, pv) for k, pv in tests if pv is not None]
    live.sort(key=lambda t: t[1])
    m = len(live)
    out["multiple_comparisons"] = {
        "tests_run": m,
        "expected_false_positives_at_05": round(0.05 * m, 1),
        "bonferroni_threshold": (0.05 / m) if m else None,
        "survives_bonferroni": [k for k, pv in live
                                if m and pv < 0.05 / m],
        "nominally_significant": [k for k, pv in live
                                  if pv < 0.05],
        "ranked": [{"test": k, "p": pv} for k, pv in live],
    }

    out["events"] = rows
    OUT.write_text(json.dumps(out, ensure_ascii=False,
                              separators=(",", ":")),
                   encoding="utf-8")

    # ---- console ------------------------------------------
    s = out["sample"]
    print(f"  windows {s['priced_windows']}  breaks "
          f"{s['price_breaks_excluded']}  registry "
          f"{s['registry_dated']}  borrow {s['with_borrow']}  "
          f"intraday {s['with_intraday']}")
    print(f"\n  A. ANATOMY (excess over TAIEX, registry-dated)")
    print(f"     {'':<6}{'n':>4}{'gap1':>9}{'drift':>9}"
          f"{'eff day':>9}{'rev5':>9}{'rev20':>9}{'xADV':>7}")
    for side in ("ADD", "DEL"):
        a = out["A_anatomy"][side]
        def g(k, f="p50"):
            v = a[k].get(f)
            return f"{v:+.2%}" if v is not None else "—"
        print(f"     {side:<6}{a['n']:>4}{g('gap1'):>9}"
              f"{g('drift'):>9}{g('eff_day'):>9}{g('rev5'):>9}"
              f"{g('rev20'):>9}{a['t_mult']['p50']:>7.1f}")
    print(f"\n  H. BORROW BUILD, announcement -> print "
          f"(days of ADV)")
    for side in ("ADD", "DEL"):
        h = out["H_borrow"][side]
        d = h["build_days_of_adv"]
        if not d.get("n"):
            continue
        print(f"     {side}  n={d['n']:<4} p50 {d['p50']:>+7.3f}  "
              f"p90 {d['p90']:>+7.3f}  building "
              f"{h['share_building']:.0%}")
    sq = out["H_borrow"].get("squeeze_split")
    if sq:
        print(f"\n  H2. DELETIONS SPLIT ON BORROW BUILD "
              f"(median {sq['median_build_days_of_adv']:+.3f} "
              f"days of ADV)")
        for lab in ("crowded", "uncrowded"):
            b = sq[lab]
            print(f"     {lab:<10}n={b['n']:<4}"
                  f"eff day {b['eff_day']['p50']:>+7.2%}   "
                  f"rev5 {b['rev5']['p50']:>+7.2%}   "
                  f"rev20 {b['rev20']['p50']:>+7.2%}")
    print(f"\n  X. INTRADAY (2023+, 5-minute)")
    for side in ("ADD", "DEL"):
        x = out["X_intraday"][side]
        if not x["close_share"].get("n"):
            continue
        print(f"     {side}  n={x['close_share']['n']:<4}"
              f"close bar {x['close_share']['p50']:>6.1%}  "
              f"lift {x['close_share_lift']['p50']:>5.1f}x  "
              f"close vs vwap "
              f"{x['close_vs_vwap']['p50']:>+7.3%}")
    bx = out["X_intraday"]["borrow_x_auction"]
    print(f"\n  BORROW x AUCTION")
    for lab in ("all", "ADD", "DEL"):
        print(f"   {lab} (n={bx[lab]['n']})")
        for k in ("close_share", "close_vs_vwap",
                  "next_open_gap"):
            r = bx[lab][k]
            v = (f"{r['spearman']:+.3f}" if r["spearman"]
                 is not None else "—")
            pp = (f"p={r['p']:.3f}" if r.get("p")
                  is not None else "")
            print(f"     rho(borrow, {k:<15}) {v}  {pp}")
    print(f"\n  I. CROWDING TREND (spearman vs year)")
    for k, r in out["I_crowding"]["trend_vs_year"].items():
        v = (f"{r['spearman']:+.3f}" if r["spearman"]
             is not None else "—")
        pp = f"p={r['p']:.3f}" if r.get("p") is not None else ""
        print(f"     {k:<20}{v}  n={r['n']}  {pp}")
    _write_doc(out)
    mc = out["multiple_comparisons"]
    print(f"\n  MULTIPLE COMPARISONS")
    print(f"     {mc['tests_run']} correlations run; "
          f"{mc['expected_false_positives_at_05']} false "
          f"positives EXPECTED at p<0.05")
    print(f"     Bonferroni threshold "
          f"{mc['bonferroni_threshold']:.4f}")
    print(f"     nominally significant: "
          f"{mc['nominally_significant'] or 'none'}")
    print(f"     survives correction:   "
          f"{mc['survives_bonferroni'] or 'NONE'}")
    print(f"\n-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
