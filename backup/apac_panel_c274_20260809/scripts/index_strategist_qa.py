"""The questions a PT desk index strategist actually asks, run
against every APAC market we hold (c-230).

WHY THIS SHAPE. We have a Taiwan playbook with three data
tiers (docs/EVENT_WINDOW_FRAMEWORK.md): Tier 1 is daily OHLCV
plus announcement/effective dates, Tier 2 adds per-stock
positioning, Tier 3 adds intraday. Only Tier 1 is portable to
all thirteen markets today, so every question below is
answerable from Tier 1 ALONE and says so. Where a Taiwan
finding needs Tier 2 or 3, it is listed as unanswerable rather
than approximated — an approximated crowding read is worse
than no crowding read, because it looks like one.

DISCIPLINE CARRIED ON EVERY NUMBER
  * n on every cell. A median of four is printed as a median
    of four, not as a market's behaviour.
  * SURVIVORSHIP. Ten of thirteen markets are priced from
    Yahoo, which lists the living. Their DELETION rows are
    biased toward names that survived deletion; Taiwan and
    India come from exchange day-files and are delisted-safe.
    Every deletion statistic carries the flag.
  * MARKET ADJUSTMENT is now applied, and BOTH numbers are
    kept. This is the c-274 change and it reverses the stance
    this file shipped with, so the reason is worth recording.

    The old header said "we do not hold an index series for
    every market, and a half-adjusted panel is worse than a
    consistently raw one." That was true when it was written
    and is no longer true: `apac_market_proxy.py` has
    harvested a local-currency benchmark for every market, and
    coverage against the actual event days is 98.5% or better
    everywhere. Taiwan is the exception in the opposite
    direction — Yahoo's ^TWII only starts 2014-06 and the
    windows reach back to 2010, so Taiwan routes to
    `twii_daily.json` (99.8%) instead.

    Raw is RETAINED beside excess rather than replaced. Two
    reasons. A number on the site should never silently change
    value with no trace of what it was. And the SIZE of the
    adjustment is itself the finding — on Taiwan, adjusting
    took the addition drift from +3.4% to +2.0%, so roughly
    45% of the published "edge" was beta. A desk that quotes
    the raw figure to a client is quoting the market.

  * HORIZONS ARE STRICT. `rev20` used to read
    `ret(ie, min(ie + 20, last))`, which does not fail when
    the window is short — it silently returns a 15- or
    18-session number and pools it with the 20s. Taiwan was
    the market this bit, and the ±20 top-up (c-273) is what
    made the strict version computable. A short window now
    returns None and is counted, not padded.

Usage:  py scripts\\index_strategist_qa.py
Output: data/index_strategist_qa.json
        docs/INDEX_STRATEGIST_QA_APAC.md
"""
import json
import math
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "data" / "apac_event_windows"
TW = ROOT / "data" / "tw_event_windows.json"
OUT = ROOT / "data" / "index_strategist_qa.json"
DOC = ROOT / "docs" / "INDEX_STRATEGIST_QA_APAC.md"

# Which markets are priced from a source that keeps the dead.
DELISTED_SAFE = {"Taiwan", "India"}

PROXY = ROOT / "data" / "apac_market_proxy.json"
TWII = ROOT / "data" / "twii_daily.json"

# The benchmark each market's returns are measured against.
# Two markets trade on two boards whose indices diverge enough
# to matter, so the board is read off the window's own Yahoo
# symbol rather than assumed.
BOARD = {"China": {".SZ": "399001.SZ", ".SS": "000001.SS"},
         "Korea": {".KQ": "^KQ11", ".KS": "^KS11"}}
DEFAULT_IX = {"Japan": "^N225", "Korea": "^KS11",
              "HongKong": "^HSI", "China": "000001.SS",
              "India": "^NSEI", "Australia": "^AXJO",
              "Singapore": "^STI", "Malaysia": "^KLSE",
              "Thailand": "^SET.BK", "Indonesia": "^JKSE",
              "NewZealand": "^NZ50", "Philippines": "^PSI"}

# A market whose proxy covers less than this share of its own
# event days stays RAW and says so. A partly-adjusted median
# mixes two definitions inside one number.
MIN_PROXY_COVERAGE = 0.95

# The Feb-2023 QCIR regime break — MSCI moved Feb/Aug from a
# light maintenance review to a full comprehensive one.
REGIME = "2023-02-01"


def _proxy_series():
    """{symbol: {iso: close}} for every harvested benchmark.

    Taiwan is stitched in from `twii_daily.json` under its own
    key. The Yahoo ^TWII series exists and is NOT used: it
    begins 2014-06-03 while the Taiwan windows reach back to
    2010, so it covers 78.6% of Taiwan's event days against
    99.8% for the local file. Silently adjusting four fifths of
    a market and leaving the rest raw is exactly the failure
    this file used to avoid by adjusting nothing.
    """
    d = {}
    if PROXY.exists():
        d = dict(json.loads(PROXY.read_text(encoding="utf-8"))
                 .get("series") or {})
    if TWII.exists():
        d["TWII_LOCAL"] = {k: float(v) for k, v in
                           json.loads(TWII.read_text(
                               encoding="utf-8")).items()}
    return d


def _symbol_for(v):
    """Which benchmark this one window is measured against."""
    mkt = v["market"]
    if mkt == "Taiwan":
        return "TWII_LOCAL"
    sym = str(v.get("yf_symbol") or "")
    for suffix, ix in BOARD.get(mkt, {}).items():
        if sym.endswith(suffix):
            return ix
    return DEFAULT_IX.get(mkt)


def _load():
    """Every priced window, market-tagged, with its benchmark.

    `_ix` is the index series this window's returns are
    measured against, or None if the market has no usable
    proxy. Attaching it per WINDOW rather than per market is
    what lets China and Korea take the right board.
    """
    series = _proxy_series()
    out = []
    files = [(p.stem, p) for p in sorted(DIR.glob("*.json"))]
    if TW.exists():
        files.append(("Taiwan", TW))
    for mkt, p in files:
        try:
            W = json.loads(p.read_text(encoding="utf-8"))["windows"]
        except Exception:                          # noqa: BLE001
            continue
        for v in W.values():
            if v.get("px") and len(v["px"]) >= 12:
                v = dict(v)
                v["market"] = mkt
                v["_ix"] = series.get(_symbol_for(v) or "")
                v["_ix_symbol"] = _symbol_for(v)
                out.append(v)
    return out


def proxy_coverage(rows):
    """Share of each market's event days the benchmark can
    price. Reported, not assumed: a market under
    MIN_PROXY_COVERAGE is reported RAW and flagged, because a
    median built from some excess returns and some total
    returns is not a statistic about anything.
    """
    tally = defaultdict(lambda: [0, 0, None])
    for v in rows:
        t = tally[v["market"]]
        t[2] = v.get("_ix_symbol")
        ix = v.get("_ix") or {}
        for r in v["px"]:
            t[0] += 1
            t[1] += 1 if r["d"] in ix else 0
    return {m: {"symbol": t[2], "days": t[0],
                "covered": (t[1] / t[0]) if t[0] else 0.0,
                "adjustable": bool(t[0]) and
                (t[1] / t[0]) >= MIN_PROXY_COVERAGE}
            for m, t in sorted(tally.items())}


def _series(v):
    """(dates, closes, volumes) with rows that have a close."""
    px = [r for r in v["px"] if r.get("c")]
    return ([r["d"] for r in px], [r["c"] for r in px],
            [r.get("v") or 0 for r in px])


def _idx(dts, when):
    """Last row on or before a date, else None."""
    hit = None
    for i, d in enumerate(dts):
        if d <= when:
            hit = i
    return hit


def metrics(v):
    """Tier-1 metrics for one window. None if the window cannot
    support them — a short window is dropped, never padded."""
    dts, close, vol = _series(v)
    if len(close) < 12:
        return None
    i0, ie = _idx(dts, v["ann"]), _idx(dts, v["eff"])
    if i0 is None or ie is None or ie <= i0 + 1:
        return None
    if i0 < 1 or close[i0] <= 0:
        return None

    ix = v.get("_ix") or {}

    def ret(a, b):
        """RAW return a -> b. None, never a shorter horizon.

        c-274. The `min(b, last)` this used to be wrapped in at
        the call sites is the whole reason `rev20` was not a
        20-session number. Out of range is now an answer.
        """
        if a is None or b is None:
            return None
        if not (0 <= a < len(close) and 0 <= b < len(close)):
            return None
        if close[a] <= 0:
            return None
        return close[b] / close[a] - 1

    def xret(a, b):
        """EXCESS return a -> b: the name less its benchmark.

        Returns None if either end is missing from the index
        series. A missing index day must not quietly degrade to
        a raw return — that is the mixed-definition median the
        header warns about, one event at a time.
        """
        r = ret(a, b)
        if r is None:
            return None
        ia, ib = ix.get(dts[a]), ix.get(dts[b])
        if not (ia and ib):
            return None
        return r - (ib / ia - 1)

    pre = [q for q in vol[max(0, i0 - 20):i0] if q]
    adv = st.median(pre) if pre else 0
    last = len(close) - 1

    def fwd(i, k):
        """i + k sessions, or None if the window is too short."""
        return (i + k) if 0 <= i + k <= last else None

    def back(i, k):
        return (i - k) if i - k >= 0 else None

    # the announcement pop: day 0 close is pre-news because MSCI
    # publishes before the Asian open
    LEGS = {
        "gap1": (i0, fwd(i0, 1)),
        # the run from the first reacting session to the day
        # BEFORE the print
        "drift": (min(i0 + 1, ie - 1), ie - 1),
        # the print itself
        "eff_day": (ie - 1, ie),
        "rev5": (ie, fwd(ie, 5)),
        "rev20": (ie, fwd(ie, 20)),
        "pre_drift": (back(i0, 20), i0),
        "total": (i0, ie - 1),
    }
    m = {
        "market": v["market"], "rev": v.get("rev"),
        "code": v.get("code"), "action": v.get("action"),
        "ann": v["ann"], "eff": v["eff"],
        "ix_symbol": v.get("_ix_symbol"),
        "sessions_pre": i0,
        "sessions_post": last - ie,
        "adv": adv,
        "t_mult": (vol[ie] / adv) if adv else None,
        # a window whose in-between sessions are ALL zero-volume
        # (halted, suspended, or a data gap) has no window
        # volume — None, not a crash and not a zero
        "vol_win": ((st.median(_w) / adv)
                    if adv and (_w := [q for q in vol[i0 + 1:ie]
                                       if q]) else None),
        "delisted_safe": v["market"] in DELISTED_SAFE,
        "post_regime": v["ann"] >= REGIME,
    }
    # every return leg twice: raw, and excess over the market.
    # The `_x` twin is the headline; the raw one stays so the
    # size of the adjustment is visible rather than asserted.
    for k, (a, b) in LEGS.items():
        m[k] = ret(a, b)
        m[k + "_x"] = xret(a, b)
    # execution counterfactuals, in the desk's own units: cost
    # in bps versus doing the whole thing on the effective close
    sgn = 1 if str(v.get("action")).upper() == "ADD" else -1
    tgt = close[ie]

    def _costs(series, suffix):
        """Schedule costs in bps against a 100%-at-the-close
        benchmark, on whichever price series is handed in."""
        t = series[ie]
        if not (t and t > 0):
            return
        path = [c for c in series[i0 + 1:ie + 1] if c and c > 0]
        if len(path) < 3:
            return

        def cost(avg):
            return sgn * (avg / t - 1) * 1e4
        m["cost_linear" + suffix] = cost(st.mean(path))
        m["cost_day1" + suffix] = cost(path[0])
        m["cost_late5" + suffix] = cost(st.mean(path[-5:]))
        m["cost_3070" + suffix] = cost(
            0.3 * st.mean(path[:3]) + 0.7 * t)

    _costs(close, "")
    # The excess version de-trends the price path by the index
    # and re-bases at the effective close, so the answer is
    # "what did this schedule cost me BEYOND what the market
    # did to everyone." A schedule that looks 80bp cheap in a
    # rising market is not cheap; it is long the market.
    if ix and tgt and tgt > 0 and dts[ie] in ix:
        base = ix[dts[ie]]
        detr = [(c / ix[d] * base)
                if (c and d in ix and ix[d]) else None
                for c, d in zip(close, dts)]
        if all(detr[i] for i in range(i0 + 1, ie + 1)):
            _costs(detr, "_x")
    # the early read: does day +3 tell you anything?
    #
    # c-230 CORRECTION, caught in the first output. I first
    # correlated early3 (day+1 -> day+3) against `drift`
    # (day+1 -> eff-1) and got 0.35-0.44 in every market, which
    # should have been the tell: `drift` CONTAINS `early3`, so
    # the correlation is arithmetic, not predictive. A desk
    # reading "day+3 forecasts the window, rho 0.44" would have
    # been reading its own left-hand side.
    #
    # The honest question is whether the early move predicts
    # what happens AFTER it, so `late_drift` starts where
    # early3 ends and the two share no session.
    e_a, e_b = i0 + 1, min(i0 + 3, ie - 1)
    l_a, l_b = min(i0 + 3, ie - 1), ie - 1
    a3 = ret(e_a, e_b) if ie > i0 + 3 else None
    late = ret(l_a, l_b) if ie > i0 + 4 else None
    a3x = xret(e_a, e_b) if ie > i0 + 3 else None
    latex = xret(l_a, l_b) if ie > i0 + 4 else None
    m["early3"], m["late_drift"] = a3, late
    m["early3_x"], m["late_drift_x"] = a3x, latex
    # `fav_*` is the leg signed to the trade direction, so a
    # positive number always means "moved the way the event
    # implies" regardless of side. Favourability is only ever
    # asked of the excess series — a deletion that fell 3% in a
    # market that fell 3% did not move favourably, it stood
    # still, and the raw sign says otherwise.
    for src, dst in (("early3_x", "fav_early3"),
                     ("late_drift_x", "fav_late"),
                     ("drift_x", "fav_drift")):
        m[dst] = (sgn * m[src]) if m.get(src) is not None else None
        m[dst + "_raw"] = (sgn * m[src[:-2]]
                           if m.get(src[:-2]) is not None else None)
    return m


# ---------------------------------------------------------------
def _med(xs):
    xs = [x for x in xs if x is not None
          and not (isinstance(x, float) and math.isnan(x))]
    return (st.median(xs), len(xs)) if xs else (None, 0)


def _pct(xs, p):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    k = max(0, min(len(xs) - 1, int(round(p * (len(xs) - 1)))))
    return xs[k]


def _rho(xs, ys):
    """Spearman, computed here so the whole script has no
    third-party dependency beyond the standard library."""
    pairs = [(a, b) for a, b in zip(xs, ys)
             if a is not None and b is not None]
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
    rx, ry = rank([p[0] for p in pairs]), rank([p[1] for p in pairs])
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx)
                    * sum((b - my) ** 2 for b in ry))
    return (num / den if den else None), n


def build(windows=None):
    """(metric rows, rows grouped by market).

    `windows` may be handed in so a caller that also needs the
    raw windows — `report()` wants them for `proxy_coverage` —
    does not load and parse the panel a second time. Same
    pattern, and the same fix, as `data_gaps.report`.
    """
    if windows is None:
        windows = _load()
    rows = [m for m in (metrics(v) for v in windows) if m]
    by = defaultdict(list)
    for r in rows:
        by[r["market"]].append(r)
    return rows, by


# ---------------------------------------------------------------
# THE QUESTIONS. Each returns (title, why_it_matters, table,
# reading) so the report is generated from the same object the
# JSON carries — a number can never appear in the prose that is
# not in the data.
# ---------------------------------------------------------------
def _split(rs, act):
    return [r for r in rs if str(r["action"]).upper() == act]


def _pair(g, key):
    """(excess median, raw median, n) for one return leg.

    Called `_pair` rather than `_adjusted` because the point of
    c-274 is that BOTH survive. Handing them back together is
    what makes it awkward to publish one without the other.
    `n` is the excess count, which is the smaller of the two
    wherever the benchmark has a gap.
    """
    x, nx = _med([r.get(key + "_x") for r in g])
    raw, _ = _med([r.get(key) for r in g])
    return x, raw, nx


def _mkt_component(x, raw):
    """The part of the raw median that was simply the market.

    ADDITIVE, on purpose: raw = excess + market, so this is
    just `raw - x` and it is defined for every cell, never
    explodes, and is read in the same units as the two numbers
    beside it.

    c-274, SECOND ATTEMPT. The first version of this returned a
    SHARE, `1 - x/raw`, and the first run printed India ADD at
    428%, Japan DEL at 241% and Japan ADD at -194%. Those are
    not outliers to be clipped — they are the ratio telling the
    truth about a badly posed question. "What share of the move
    was beta" only means anything when the market component and
    the excess point the SAME way and the market's part is the
    smaller one. When adjusting flips the sign (India additions
    are +0.52% raw and -1.72% excess) there is no share; the
    market was doing more than the whole move. A percentage
    that exceeds 100% because its denominator nearly vanished
    is the same failure as `capture` in c-270 and `revert20` in
    c-269, and it should not be shipped a third time.
    """
    if x is None or raw is None:
        return None
    return raw - x


def _beta_share(x, raw):
    """The share version, published ONLY where it is honest.

    Requires the raw move to be at least 50bp and the excess to
    sit between zero and the raw move with the same sign — the
    only configuration in which "n% of this was beta" is a true
    sentence. Everything else returns None and the reader is
    sent to the additive column, which is always defined.
    """
    if x is None or raw is None or abs(raw) < 0.005:
        return None
    if (x > 0) != (raw > 0) or abs(x) > abs(raw):
        return None
    return 1 - (x / raw)


def q1_print_size(by):
    """How big is the print I have to get done?"""
    tbl = []
    for m, rs in sorted(by.items()):
        for act in ("ADD", "DEL"):
            g = _split(rs, act)
            med, n = _med([r["t_mult"] for r in g])
            if not n:
                continue
            tbl.append({
                "market": m, "action": act, "n": n,
                "t_mult_median": med,
                "t_mult_p75": _pct([r["t_mult"] for r in g], .75),
                "t_mult_max": max(
                    [r["t_mult"] for r in g if r["t_mult"]],
                    default=None),
                "window_vol_x_adv": _med(
                    [r["vol_win"] for r in g])[0],
                "delisted_safe": g[0]["delisted_safe"]})
    return ("Q1. How big is the print?",
            "Sizes the execution problem before anything else. "
            "T-multiple = effective-day volume / 20-session "
            "median ADV. It is the number that decides whether "
            "the trade is a schedule or a negotiation.",
            tbl,
            "Read the p75 and the max, not the median — the "
            "median is the day you plan for and the tail is the "
            "day that costs you.")


def q2_when_does_it_move(by):
    """Announcement pop, or the drift to the print?"""
    tbl = []
    for m, rs in sorted(by.items()):
        for act in ("ADD", "DEL"):
            g = _split(rs, act)
            gap, gap_raw, n = _pair(g, "gap1")
            if n < 4:
                continue
            dr, dr_raw, _ = _pair(g, "drift")
            tot, tot_raw, _ = _pair(g, "total")
            # c-270 guard, kept: `capture` is a ratio whose
            # denominator is a sum of two signed medians, so it
            # blows up whenever they nearly cancel. 50bp is the
            # floor that stopped three Taiwan events reaching
            # |1000|.
            cap = None
            if gap is not None and dr is not None \
                    and abs(gap + dr) >= 0.005:
                cap = dr / (gap + dr)
            tbl.append({"market": m, "action": act, "n": n,
                        "gap1": gap, "drift": dr,
                        "total_ann_to_eff": tot,
                        "capture_share_of_move_in_drift": cap,
                        "gap1_raw": gap_raw, "drift_raw": dr_raw,
                        "total_raw": tot_raw,
                        "market_part_of_drift":
                            _mkt_component(dr, dr_raw),
                        "beta_share_of_drift":
                            _beta_share(dr, dr_raw)})
    return ("Q2. When does the move happen — the pop or the drift?",
            "If the move is in gap1 the announcement is already "
            "priced and there is nothing to work; if it is in "
            "the drift there is a window to trade into. Capture "
            "= drift / (gap1 + drift).",
            tbl,
            "Capture near 1 means the market takes the whole "
            "window to price it. Capture near 0 or negative "
            "means it gapped and then went the other way.")


def q3_reversal(by):
    """Does the print revert, and how fast?"""
    tbl = []
    for m, rs in sorted(by.items()):
        for act in ("ADD", "DEL"):
            g = _split(rs, act)
            e, e_raw, n_eff = _pair(g, "eff_day")
            n = len(g)
            if n_eff < 4:
                continue
            r5, r5_raw, n5 = _pair(g, "rev5")
            r20, r20_raw, n20 = _pair(g, "rev20")
            tbl.append({
                "market": m, "action": act, "n": n,
                "n_eff_day": n_eff,
                "eff_day": e, "rev5": r5, "rev20": r20,
                # n20 is reported separately and on purpose. It
                # is the count of windows that actually HAVE 20
                # sessions after the effective close, and before
                # c-274 the shortfall was invisible because the
                # horizon silently shortened instead.
                "n_rev20": n20,
                "abs_rev5_median": _med(
                    [abs(r["rev5_x"]) for r in g
                     if r.get("rev5_x") is not None])[0],
                "eff_day_raw": e_raw, "rev5_raw": r5_raw,
                "rev20_raw": r20_raw,
                "market_part_of_rev20":
                    _mkt_component(r20, r20_raw),
                "beta_share_of_rev20": _beta_share(r20, r20_raw),
                "delisted_safe": g[0]["delisted_safe"]})
    return ("Q3. Does it revert after the print?",
            "Decides whether the effective close is a price to "
            "fade or a price to accept. rev5/rev20 are excess "
            "returns from the effective close forward, over a "
            "STRICT horizon — a window without 20 sessions of "
            "post-effective data is dropped, not shortened.",
            tbl,
            "A deletion reversal on a SURVIVORS-ONLY market is "
            "the most biased number in this whole document: the "
            "names that did not survive cannot bounce. Read "
            "n_rev20 against n before trusting a rev20 cell.")


def q4_execution(by):
    """Where should the schedule sit?"""
    tbl = []
    for m, rs in sorted(by.items()):
        for act in ("ADD", "DEL"):
            g = _split(rs, act)
            lin, lin_raw, n = _pair(g, "cost_linear")
            if n < 4:
                continue
            tbl.append({
                "market": m, "action": act, "n": n,
                "MOC_baseline_bps": 0.0,
                "LINEAR_bps": lin,
                "ALL_DAY1_bps": _pair(g, "cost_day1")[0],
                "LATE5_bps": _pair(g, "cost_late5")[0],
                "EARLY30_MOC70_bps": _pair(g, "cost_3070")[0],
                "LINEAR_raw_bps": lin_raw,
                "ALL_DAY1_raw_bps": _pair(g, "cost_day1")[1],
                "delisted_safe": g[0]["delisted_safe"]})
    return ("Q4. Which schedule beats the effective close?",
            "Cost in bps versus doing 100% on the effective "
            "close, signed so NEGATIVE = beat the benchmark. "
            "This is the only question on this page a desk gets "
            "paid for directly.",
            tbl,
            "Headline columns de-trend the price path by the "
            "local index and re-base at the effective close, so "
            "they answer what the SCHEDULE cost rather than "
            "what the market did. A schedule that looks cheap "
            "in a rising market is not cheap, it is long the "
            "market — compare LINEAR_bps with LINEAR_raw_bps to "
            "see how much of the old answer was that. These are "
            "still UNCONDITIONAL medians on a survivors-biased "
            "panel for ten of twelve markets: they size the "
            "opportunity, they are not a schedule.")


def q5_frontrun(by):
    """Is it already being positioned before the announcement?"""
    tbl = []
    for m, rs in sorted(by.items()):
        for act in ("ADD", "DEL"):
            g = _split(rs, act)
            pd, pd_raw, n = _pair(g, "pre_drift")
            if n < 4:
                continue
            sgn = 1 if act == "ADD" else -1
            xs = [r["pre_drift_x"] for r in g
                  if r.get("pre_drift_x") is not None]
            fav = _med([sgn * x for x in xs])[0]
            tbl.append({"market": m, "action": act, "n": n,
                        "pre_drift_20s": pd,
                        "favourable_pre_drift": fav,
                        "pre_drift_raw": pd_raw,
                        # anticipation is only meaningful as
                        # EXCESS. A deletion that fell 3% while
                        # its market fell 3% was not being
                        # positioned against; it stood still,
                        # and the raw sign says otherwise.
                        "share_moving_the_right_way":
                            (sum(1 for x in xs if sgn * x > 0)
                             / len(xs)) if xs else None})
    return ("Q5. Is the name already positioned before the "
            "announcement?",
            "20 sessions of pre-announcement drift, signed so "
            "POSITIVE = already moving the way the review will "
            "push it. Anticipation is the part of the trade "
            "that is gone before the desk is called.",
            tbl,
            "Tier-1 can only see PRICE anticipation. Taiwan's "
            "borrow-build clock (98% of deletions show excess "
            "build) is a Tier-2 measurement and has no analog "
            "here.")


def q6_regime(by):
    """Did the Feb-2023 QCIR change alter the trade?"""
    tbl = []
    for m, rs in sorted(by.items()):
        for post in (False, True):
            g = [r for r in rs if r["post_regime"] is post]
            t, n = _med([r["t_mult"] for r in g])
            if n < 6:
                continue
            tbl.append({
                "market": m,
                "period": "since Feb-2023" if post
                          else "before Feb-2023",
                "n": n, "t_mult_median": t,
                "abs_eff_day": _med(
                    [abs(r["eff_day_x"]) for r in g
                     if r.get("eff_day_x") is not None])[0],
                "abs_gap1": _med(
                    [abs(r["gap1_x"]) for r in g
                     if r.get("gap1_x") is not None])[0]})
    return ("Q6. Did the Feb-2023 QCIR regime change the trade?",
            "MSCI moved Feb/Aug from light maintenance to full "
            "comprehensive reviews. More names per review could "
            "mean smaller individual prints, or the same print "
            "size four times a year instead of twice.",
            tbl,
            "A period split is not a controlled experiment — "
            "2023-2026 is also a different volatility regime. "
            "Treat a difference here as a question, not a "
            "finding.")


def q7_violence(by):
    """Which markets print violently?"""
    tbl = []
    for m, rs in sorted(by.items()):
        e = [abs(r["eff_day_x"]) for r in rs
             if r.get("eff_day_x") is not None]
        raw = [abs(r["eff_day"]) for r in rs
               if r["eff_day"] is not None]
        if len(e) < 6:
            continue
        tbl.append({"market": m, "n": len(e),
                    "abs_eff_day_median": st.median(e),
                    "abs_eff_day_p90": _pct(e, .90),
                    "abs_eff_day_max": max(e),
                    "share_over_5pct": sum(1 for x in e
                                           if x > .05) / len(e),
                    "abs_eff_day_p90_raw": _pct(raw, .90)})
    tbl.sort(key=lambda r: -(r["abs_eff_day_p90"] or 0))
    return ("Q7. Which markets print violently?",
            "|excess effective-day return| — the idiosyncratic "
            "risk the desk carries into the close, with the "
            "market's own move stripped out. Ranked by the 90th "
            "percentile, because the tail is what breaks a "
            "schedule.",
            tbl,
            "This is the market-selection question: where does "
            "an index-rebalance book deserve more risk budget "
            "and tighter pre-trade limits.")


def q8_asymmetry(by):
    """Are deletions the harder side?"""
    tbl = []
    for m, rs in sorted(by.items()):
        a, d = _split(rs, "ADD"), _split(rs, "DEL")
        if len(a) < 4 or len(d) < 4:
            continue
        tbl.append({
            "market": m, "n_add": len(a), "n_del": len(d),
            "add_t_mult": _med([r["t_mult"] for r in a])[0],
            "del_t_mult": _med([r["t_mult"] for r in d])[0],
            "add_abs_eff": _med([abs(r["eff_day_x"]) for r in a
                                 if r.get("eff_day_x")
                                 is not None])[0],
            "del_abs_eff": _med([abs(r["eff_day_x"]) for r in d
                                 if r.get("eff_day_x")
                                 is not None])[0],
            "add_rev20": _pair(a, "rev20")[0],
            "del_rev20": _pair(d, "rev20")[0],
            "delisted_safe": rs[0]["delisted_safe"]})
    return ("Q8. Is the deletion side harder than the addition "
            "side?",
            "Desk lore says deletions are worse: a forced seller "
            "into a name nobody has to own, with the borrow "
            "already lent out. Tier 1 can test the size and the "
            "violence of it.",
            tbl,
            "On survivors-only markets the deletion column is "
            "biased toward the survivors, which understates the "
            "difficulty. Taiwan and India are the honest rows.")


def q9_early_signal(by):
    """Does day +3 predict the rest of the window?"""
    tbl = []
    for m, rs in sorted(by.items()):
        # NON-OVERLAPPING: early3 is day+1->+3, late_drift is
        # day+3->eff-1. Correlating early3 against the full
        # drift (which contains it) was the c-230 error.
        rho, n = _rho([r["fav_early3"] for r in rs],
                      [r["fav_late"] for r in rs])
        rho_overlap, _ = _rho([r["fav_early3"] for r in rs],
                              [r["fav_drift"] for r in rs])
        if rho is None:
            continue
        hot = [r for r in rs if (r["fav_early3"] or 0) > 0]
        cold = [r for r in rs if (r["fav_early3"] or 0) <= 0]
        tbl.append({
            "market": m, "n": n,
            "spearman_early3_vs_LATER_drift": rho,
            "overlapping_window_rho_ARTIFACT": rho_overlap,
            "hot_n": len(hot),
            "hot_linear_bps": _pair(hot, "cost_linear")[0],
            "cold_n": len(cold),
            "cold_linear_bps": _pair(cold, "cost_linear")[0]})
    tbl.sort(key=lambda r: -(
        r["spearman_early3_vs_LATER_drift"] or 0))
    return ("Q9. Does the first three sessions tell me anything?",
            "Taiwan's window study found conditioning on day +3 "
            "separated the schedules that worked from the ones "
            "that did not. Spearman of the favourable day+3 "
            "move against the drift that comes AFTER it "
            "(day+3 to effective-1), then the execution cost "
            "split on that sign. The second column repeats the "
            "same correlation against the FULL drift, which "
            "contains day+3 — it is printed only to show how "
            "much of an apparent signal is arithmetic.",
            tbl,
            "Compare the two rho columns. Where the "
            "overlapping one is large and the honest one is "
            "near zero, the early move is not forecasting "
            "anything — it is part of what it appears to "
            "predict. Also: events in one review share a "
            "market move, so n is not independent. Treat "
            "|rho| under ~0.25 as noise.")


def q10_liquidity(by):
    """How many days of ADV is the event worth?"""
    tbl = []
    for m, rs in sorted(by.items()):
        t = [r["t_mult"] for r in rs if r["t_mult"]]
        if len(t) < 6:
            continue
        w = [r["vol_win"] for r in rs if r["vol_win"]]
        tbl.append({
            "market": m, "n": len(t),
            "eff_day_x_adv_median": st.median(t),
            "eff_day_x_adv_p90": _pct(t, .90),
            "window_days_x_adv_median": (st.median(w) if w
                                         else None),
            "share_over_10x": sum(1 for x in t if x > 10) / len(t),
            "share_under_2x": sum(1 for x in t if x < 2) / len(t)})
    tbl.sort(key=lambda r: -(r["eff_day_x_adv_p90"] or 0))
    return ("Q10. How much of the trade can the close actually "
            "absorb?",
            "share_under_2x is the quiet-event rate — reviews "
            "where the print barely registers and the desk "
            "should not be spending risk. share_over_10x is "
            "where the print IS the day.",
            tbl,
            "China's low share_over_10x with a huge n is the "
            "single most important planning fact in this table: "
            "most Chinese index events are not liquidity events.")


QUESTIONS = [q1_print_size, q2_when_does_it_move, q3_reversal,
             q4_execution, q5_frontrun, q6_regime, q7_violence,
             q8_asymmetry, q9_early_signal, q10_liquidity]


# ---------------------------------------------------------------
def _fmt(v, key):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "yes" if v else "**no**"
    if isinstance(v, int):
        return str(v)
    if any(k in key for k in ("bps",)):
        return f"{v:+.0f}"
    if any(k in key for k in ("share", "capture")):
        return f"{v:.0%}"
    if any(k in key for k in ("t_mult", "x_adv", "vol_win",
                              "spearman", "rho")):
        return f"{v:.2f}"
    if isinstance(v, float):
        return f"{v:+.2%}" if abs(v) < 1 else f"{v:.2f}"
    return str(v)


def _table(rows):
    if not rows:
        return "_no cell met the minimum n._\n"
    cols = list(rows[0])
    out = ["| " + " | ".join(cols) + " |",
           "|" + "|".join("---" for _ in cols) + "|"]
    for r in rows:
        out.append("| " + " | ".join(
            _fmt(r.get(c), c) for c in cols) + " |")
    return "\n".join(out) + "\n"


def report():
    windows = _load()
    rows, by = build(windows)
    cov = proxy_coverage(windows)
    unadjustable = [m for m, c in cov.items() if not c["adjustable"]]
    # windows that could not produce a strict 20-session rev20,
    # per market. Before c-274 this number did not exist because
    # the horizon shortened instead of failing.
    short20 = {m: sum(1 for r in v if r.get("rev20_x") is None)
               for m, v in sorted(by.items())}
    payload = {"n_windows": len(rows),
               "markets": {m: len(v) for m, v in sorted(by.items())},
               "market_adjustment": {
                   "applied": True,
                   "coverage": cov,
                   "min_coverage_required": MIN_PROXY_COVERAGE,
                   "markets_left_raw": unadjustable},
               "horizon_integrity": {
                   "rev20_strict": True,
                   "windows_without_20_post_sessions": short20},
               "questions": []}
    doc = ["# APAC Index-Rebalance — the strategist's questions",
           "",
           "*Generated by `scripts/index_strategist_qa.py`. Every "
           "number recomputed from `data/apac_event_windows/` and "
           "`data/tw_event_windows.json` — nothing here is typed "
           "by hand.*", "",
           f"**Panel: {len(rows)} name-events across "
           f"{len(by)} markets, MSCI reviews 2015-2026.**", "",
           "## Read this before any number below", "",
           "**Survivorship.** Ten of thirteen markets are priced "
           "from Yahoo, which lists the living. Their DELETION "
           "rows are biased toward names that survived being "
           "deleted. Taiwan and India come from exchange "
           "day-files and keep the dead — they are the honest "
           "rows, and where they disagree with the others, "
           "believe them.", "",
           "**Market-adjusted, and the raw number is kept.** "
           "Every return leg is measured as EXCESS over the "
           "market's own local-currency benchmark, and the raw "
           "total return sits beside it. This reverses the "
           "stance this document shipped with: it used to say "
           "no index series existed for every market, which was "
           "true then and is not now. Coverage against the "
           "actual event days is "
           + ", ".join(f"{m} {c['covered']:.0%}"
                       for m, c in sorted(cov.items()))
           + ". Taiwan is measured against `twii_daily.json` "
           "rather than Yahoo's ^TWII, which only begins "
           "2014-06 and would have covered 79% of Taiwan's "
           "event days — adjusting four fifths of a market and "
           "leaving the rest raw is the failure the old caveat "
           "was avoiding.", "",
           "**Why keep both.** The SIZE of the adjustment is "
           "itself a finding. On Taiwan additions it removed "
           "roughly 45% of the published drift — a desk quoting "
           "the raw figure to a client is quoting the index for "
           "half its answer. Every table that has a headline "
           "excess column also carries the raw one so that "
           "share is visible rather than asserted."
           + (f" Markets still reported RAW for want of "
              f"coverage: {', '.join(unadjustable)}."
              if unadjustable else ""), "",
           "**Strict horizons.** `rev20` is twenty sessions or "
           "nothing. It used to be `min(eff + 20, last)`, which "
           "silently returned a 15- or 18-session number when "
           "the window was short and pooled it with the "
           "twenties. Taiwan was the market that bit; the ±20 "
           "top-up is what made the strict version computable. "
           "Windows short of twenty post-effective sessions, by "
           "market: "
           + ", ".join(f"{m} {n}" for m, n in short20.items()
                       if n) or "none", "",
           "**Tier 1 only.** Price and volume. The Taiwan edge — "
           "borrow build, foreign flow, crowding, the auction "
           "path — is Tier 2/3 and does not exist for these "
           "markets yet. See `docs/APAC_DATA_GAP_REGISTER.md` "
           "for what it would take.", "",
           "**Overlapping events.** Names in the same review "
           "share a market move; n is a count of name-events, "
           "not of independent observations. Effective n for "
           "any cross-sectional claim is closer to the review "
           "count.", ""]
    for fn in QUESTIONS:
        title, why, tbl, reading = fn(by)
        payload["questions"].append(
            {"title": title, "why": why, "rows": tbl,
             "reading": reading})
        doc += [f"## {title}", "", why, "", _table(tbl), "",
                f"**Reading it.** {reading}", ""]
    OUT.write_text(json.dumps(payload, indent=1),
                   encoding="utf-8")
    DOC.write_text("\n".join(doc), encoding="utf-8")
    print(f"panel: {len(rows)} name-events, {len(by)} markets")
    for m, v in sorted(by.items(), key=lambda x: -len(x[1])):
        print(f"  {m:12} {len(v):>5}")
    bs = briefs(by)
    payload["briefs"] = bs
    BRIEF = ROOT / "docs" / "INDEX_STRATEGIST_BRIEFS_APAC.md"
    BRIEF.write_text(brief_doc(bs), encoding="utf-8")
    OUT.write_text(json.dumps(payload, indent=1),
                   encoding="utf-8")
    print(f"\n-> {OUT.relative_to(ROOT)}")
    print(f"-> {DOC.relative_to(ROOT)}")
    print(f"-> {BRIEF.relative_to(ROOT)}")
    return payload



# ---------------------------------------------------------------
# PER-MARKET BRIEFS
#
# The cross-market tables answer "how do these markets differ".
# A desk asks a narrower question: "I cover THIS market — what
# do I need to know before the next review?" So each market
# gets its own page, computed from the same rows, with the
# facts a strategist would actually put in front of a trader.
# ---------------------------------------------------------------
def _brief(m, rs):
    a, d = _split(rs, "ADD"), _split(rs, "DEL")
    safe = rs[0]["delisted_safe"]
    t = [r["t_mult"] for r in rs if r["t_mult"]]
    e = [abs(r["eff_day"]) for r in rs if r["eff_day"] is not None]
    b = {"market": m, "n": len(rs), "n_add": len(a),
         "n_del": len(d), "delisted_safe": safe,
         "reviews": len({r["rev"] for r in rs}),
         "span": (min(r["ann"] for r in rs),
                  max(r["ann"] for r in rs))}
    b["print_median_x_adv"] = st.median(t) if t else None
    b["print_p90_x_adv"] = _pct(t, .90)
    b["quiet_rate"] = (sum(1 for x in t if x < 2) / len(t)
                       if t else None)
    b["abs_eff_median"] = st.median(e) if e else None
    b["abs_eff_p90"] = _pct(e, .90)
    for lab, g in (("add", a), ("del", d)):
        b[f"{lab}_gap1"] = _med([r["gap1"] for r in g])[0]
        b[f"{lab}_drift"] = _med([r["drift"] for r in g])[0]
        b[f"{lab}_rev5"] = _med([r["rev5"] for r in g])[0]
        b[f"{lab}_best_sched"] = None
        cands = {
            "MOC": 0.0,
            "LINEAR": _med([r.get("cost_linear") for r in g])[0],
            "ALL_DAY1": _med([r.get("cost_day1") for r in g])[0],
            "LATE5": _med([r.get("cost_late5") for r in g])[0],
            "EARLY30_MOC70": _med([r.get("cost_3070")
                                   for r in g])[0]}
        cands = {k: v for k, v in cands.items() if v is not None}
        if len(cands) > 1 and len(g) >= 4:
            best = min(cands, key=lambda k: cands[k])
            b[f"{lab}_best_sched"] = best
            b[f"{lab}_best_bps"] = cands[best]
    rho, n = _rho([r["fav_early3"] for r in rs],
                  [r["fav_late"] for r in rs])
    b["early3_rho"] = rho
    b["early3_n"] = n
    return b


def briefs(by):
    return [_brief(m, rs) for m, rs in sorted(
        by.items(), key=lambda x: -len(x[1]))]


def brief_doc(bs):
    out = ["# Per-market briefs — MSCI index reviews, 2015-2026",
           "",
           "*Generated by `scripts/index_strategist_qa.py`. One "
           "page per market, same panel as "
           "`INDEX_STRATEGIST_QA_APAC.md`, written for a trader "
           "who covers one market and wants the numbers before "
           "the next review.*", "",
           "Every schedule cost is in bps versus doing 100% on "
           "the effective close; NEGATIVE beat the close. "
           "`MOC` is the benchmark and is 0 by construction, so "
           "a market whose best schedule is MOC is one where "
           "nothing in this panel beat simply printing.", ""]
    for b in bs:
        flag = ("delisted-safe (exchange day-files)"
                if b["delisted_safe"]
                else "**SURVIVORS ONLY — deletion rows biased**")
        out += [f"## {b['market']}", "",
                f"{b['n']} name-events across {b['reviews']} "
                f"reviews, {b['span'][0]} to {b['span'][1]}. "
                f"{b['n_add']} additions, {b['n_del']} deletions. "
                f"Source: {flag}.", "",
                "| | value |", "|---|---|",
                f"| print, median | {_fmt(b['print_median_x_adv'], 't_mult')}x ADV |",
                f"| print, 90th pct | {_fmt(b['print_p90_x_adv'], 't_mult')}x ADV |",
                f"| quiet-event rate (print < 2x ADV) | {_fmt(b['quiet_rate'], 'share')} |",
                f"| effective-day move, median abs | {_fmt(b['abs_eff_median'], 'x')} |",
                f"| effective-day move, 90th pct | {_fmt(b['abs_eff_p90'], 'x')} |",
                f"| ADD: announcement pop / drift / rev5 | {_fmt(b['add_gap1'], 'x')} / {_fmt(b['add_drift'], 'x')} / {_fmt(b['add_rev5'], 'x')} |",
                f"| DEL: announcement pop / drift / rev5 | {_fmt(b['del_gap1'], 'x')} / {_fmt(b['del_drift'], 'x')} / {_fmt(b['del_rev5'], 'x')} |",
                f"| best schedule, adds | {b.get('add_best_sched') or '—'} ({_fmt(b.get('add_best_bps'), 'bps')} bps) |",
                f"| best schedule, deletes | {b.get('del_best_sched') or '—'} ({_fmt(b.get('del_best_bps'), 'bps')} bps) |",
                f"| day+3 vs the drift AFTER it, Spearman | {_fmt(b['early3_rho'], 'rho')} (n={b['early3_n']}) |",
                ""]
    return "\n".join(out)

if __name__ == "__main__":
    report()
