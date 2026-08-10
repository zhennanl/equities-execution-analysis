#!/usr/bin/env python3
"""Re-harvest the closing auction for the markets that lost it.

    py scripts\\ib_auction_reharvest.py probe            # look first
    py scripts\\ib_auction_reharvest.py probe --market Korea
    py scripts\\ib_auction_reharvest.py discover         # no network
    py scripts\\ib_auction_reharvest.py harvest --market Japan
    py scripts\\ib_auction_reharvest.py verify           # no network

WHAT WENT WRONG. `ib_5m_events.py` fetches with `useRTH=True`, and
`ib_5m_analysis.py` then takes "the closing bar" to be the last bar
that traded. Those two choices agree only where the auction prints
INSIDE regular hours. Measured on the bars we hold:

    Taiwan     last bar 13:30  auction prints 13:30      ok
    HongKong   last bar 16:05  CAS 16:00-16:10           ok (post-2016)
    Singapore  last bar 17:00  closing routine           ok
    Japan      last bar 14:55  auction prints 15:00      MISSING
    Korea      last bar 15:15  auction 15:20-15:30       MISSING
    Australia  15:55 x154 / 16:10 x69                    INCONSISTENT
    India      last bar 15:25  close is a 30-min VWAP    NO COUNTERPART
    China      last bar 14:55, venue SEHKNTL             WRONG VENUE

So Japan and Korea report the last CONTINUOUS five minutes and call
it the close. Australia reports whichever of the two it happens to
have. That is why this project's chart shows the ASX close at 3.3%
of an ordinary day when published work puts developed-market closing
auctions near 20% and the ASX close among the largest anywhere.

THE DESIGN DECISION THAT MATTERS. This script does NOT hard-code
auction times. Encoding "Korea 15:30, Australia 16:10" would be me
asserting market microstructure from memory into a file nobody
re-checks — the same failure mode as reading a 2012 T86 response
with 2024 column offsets. Instead `discover` MEASURES the auction
bar: with `useRTH=0` the post-close prints are present, and on
ordinary days the auction is a volume spike at one fixed clock time
after the continuous session ends. The published times in EXPECTED
below are a CHECK printed next to the measurement, never an input to
it. When the two disagree the script says so and stops.

INDIA AND CHINA ARE NOT FIXED BY THIS. NSE's closing price is a
30-minute VWAP, not an auction, so there is nothing for a closing-bar
metric to point at — India should be dropped from the comparison
rather than re-harvested. China's rows were routed SEHKNTL, which is
Northbound Connect flow rather than SSE/SZSE volume; that needs a
venue change in ib_5m_events._china_venue and a full re-harvest, not
a `useRTH` flag. Both are reported by `verify` and left alone.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

SRC = ROOT / "data" / "ib_5m"
OUT = ROOT / "data" / "ib_5m_auction.json"

# Markets whose auction is missing or inconsistent in the RTH bars.
AFFECTED = ("Japan", "Korea", "Australia")

# NOT INPUTS. Published expectations, printed beside what `discover`
# measures so a silent disagreement becomes a loud one. Sources are
# in docs; the point of writing them down is to be contradicted.
EXPECTED = {
    "Japan": ("15:00 pre-2024-11-05, 15:30 after "
              "(TSE added a 15:25-15:30 closing auction and "
              "extended the session on 5 Nov 2024)"),
    "Korea": "15:30 (call auction 15:20-15:30)",
    "Australia": "~16:10-16:12 (CSPA, random start)",
    "Taiwan": "13:30 (call auction 13:25-13:30)",
    "HongKong": "16:00-16:10 CAS, from 25 Jul 2016 only",
    "Singapore": "17:00-17:06",
}

# An auction print has a SIGNATURE, and all three parts are needed.
#
# A first cut asked only for ">=1% of the day on >=20 days" and it
# was badly wrong: it named 16:10 for Korea and 18:55 for India,
# both from slots present on ~25 sessions out of many thousands —
# after-hours dribble and, for India, what looks like a timezone
# artefact on a handful of windows. An absolute day count means
# nothing against a market with 17,000 day-observations.
#
# So a candidate must (1) carry a real share of the day, (2) appear
# on a real FRACTION of sessions rather than a fixed number of them,
# and (3) be a SPIKE — several times the slots just before it.
# Condition 3 is what separates an auction from the last continuous
# bar: Japan's 14:55 is 4.6% against 2.6% before it, a slope; the
# ASX 16:10 is 12.6% against 0.01%, a wall.
MIN_SPIKE = 0.01
MIN_DAY_FRACTION = 0.15
MIN_SPIKE_RATIO = 2.5


def _rel(p):
    """A path for printing, never an exception.

    `Path.relative_to` raises when the target is outside ROOT, and
    it was doing that in a progress line that runs AFTER the data
    is safely written — so a completed harvest ended in a
    traceback and looked like a failure. A status message must not
    be able to fail the thing it is reporting on.
    """
    try:
        return p.relative_to(ROOT)
    except ValueError:
        return p


def _load(market):
    p = SRC / f"{market}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _by_day(px):
    d = collections.defaultdict(list)
    for b in px or []:
        d[str(b[0])[:10]].append(b)
    return d


# ── discover ─────────────────────────────────────────────────────────

def clock_profile(market, windows=None):
    """{clock: (n_days_present, mean share of day, n_days_nonzero)}.

    Built on ORDINARY days only — the effective date and the session
    either side are dropped, because an index print is exactly the
    day that would make a continuous bar look like an auction.
    """
    d = _load(market)
    if not d:
        return {}
    tot = collections.defaultdict(list)
    for key, w in (windows or d["windows"]).items():
        eff = w.get("eff")
        days = _by_day(w.get("px"))
        dates = sorted(days)
        if eff in days:
            i = dates.index(eff)
            skip = set(dates[max(0, i - 1):i + 2])
        else:
            skip = set()
        for day, bars in days.items():
            if day in skip:
                continue
            v = sum((b[-1] or 0) for b in bars)
            if v <= 0:
                continue
            for b in bars:
                tot[str(b[0])[11:16]].append((b[-1] or 0) / v)
    return {c: (len(xs), st.mean(xs), sum(1 for x in xs if x > 0))
            for c, xs in tot.items()}


def pick_auction(prof):
    """(clock, spike ratio) for the auction bar in one profile.

    THE THREE CONDITIONS, applied together — see the note on
    MIN_SPIKE above for why none of them can be dropped. An auction
    is the final SPIKE: continuous volume tails off into the close,
    then one slot prints large.

    c-314 SPLIT THIS OUT OF `discover`, and the reason is the bug
    it was hiding. `cmd_verify` had its own copy of the rule —
    "days >= MIN_DAYS and share >= MIN_SPIKE, take the latest
    slot" — which is the FIRST-CUT discriminator this module's own
    comments record as badly wrong. When `discover` was corrected
    to the day-fraction-plus-spike-ratio test, `verify` was left
    behind and `MIN_DAYS` was deleted from under it.

    The NameError is the lucky part. Had the constant survived,
    `verify` would have measured "before" with the good rule and
    "after" with the bad one and printed a comparison of two
    different instruments — which is exactly the shape of a result
    that looks fine and is meaningless. One function now, called
    from both sides.
    """
    if not prof:
        return None, None
    top = max(v[0] for v in prof.values())
    floor = top * MIN_DAY_FRACTION
    clocks = sorted(prof)
    best = None
    for i, c in enumerate(clocks):
        days, share, _nz = prof[c]
        if days < floor or share < MIN_SPIKE:
            continue
        # the five live slots before it — the run-in an auction
        # has to tower over
        prev = [prof[x][1] for x in clocks[max(0, i - 6):i]
                if prof[x][0] >= floor and prof[x][1] > 0]
        if len(prev) < 3:
            continue
        ratio = share / st.median(prev)
        if ratio >= MIN_SPIKE_RATIO and (best is None
                                         or c > best[0]):
            best = (c, ratio)
    return best if best else (None, None)


def discover(market):
    """The auction bar for a market, measured rather than assumed.

    Returns (clock, profile). The selection itself lives in
    `pick_auction` so that `verify` cannot drift away from it.
    """
    prof = clock_profile(market)
    if not prof:
        return None, {}
    clock, _ratio = pick_auction(prof)
    return clock, prof


def _mins(hhmm):
    h, m = str(hhmm).split(":")
    return int(h) * 60 + int(m)


def agrees(market, clock):
    """Does the MEASURED slot match published microstructure?

    The expectation text is parsed for clock times and the measured
    slot has to land inside that span (with 10 minutes of slack on
    the late side, since an auction can print a little after it
    opens). EARLY is never allowed: Japan's 14:55 sits five minutes
    BEFORE the 15:00 print, and treating that as agreement is
    exactly the mistake — it is the last continuous bar, and the
    end-of-day ramp makes it look like a spike.

    Returns True, False, or None when there is nothing to check.
    """
    import re
    exp = EXPECTED.get(market)
    if not exp or not clock:
        return None
    times = [_mins(t) for t in re.findall(r"\b(\d{1,2}:\d{2})\b", exp)]
    if not times:
        return None
    return min(times) <= _mins(clock) <= max(times) + 10


def spike_ratio(market, clock):
    """How far the named slot towers over its run-in. Published so
    a reader can judge the call rather than take it."""
    prof = clock_profile(market)
    clocks = sorted(prof)
    if clock not in prof:
        return None
    i = clocks.index(clock)
    top = max(v[0] for v in prof.values())
    prev = [prof[x][1] for x in clocks[max(0, i - 6):i]
            if prof[x][0] >= top * MIN_DAY_FRACTION
            and prof[x][1] > 0]
    if not prev:
        return None
    return prof[clock][1] / st.median(prev)


def cmd_discover(a):
    markets = [a.market] if a.market else sorted(
        p.stem for p in SRC.glob("*.json"))
    print("Auction bar, MEASURED from ordinary days "
          "(not assumed):\n")
    print(f"  {'market':<11}{'measured':<10}{'share':>8}   "
          f"published expectation")
    found = {}
    for m in markets:
        clock, prof = discover(m)
        if not clock:
            print(f"  {m:<11}{'NONE':<10}{'—':>8}   "
                  f"no slot spikes {MIN_SPIKE_RATIO}x over its "
                  f"run-in — auction absent")
            continue
        r = spike_ratio(m, clock)
        found[m] = {"clock": clock, "mean_share": prof[clock][1],
                    "days": prof[clock][0],
                    "spike_ratio": r}
        ok = agrees(m, clock)
        found[m]["agrees_with_published"] = ok
        mark = {True: "ok      ", False: "DISAGREES",
                None: "unchecked"}[ok]
        print(f"  {m:<11}{clock:<10}{prof[clock][1]:>7.1%}   "
              f"({r:.0f}x)  {mark}  {EXPECTED.get(m, '—')}")
    if a.show:
        m = a.show
        _clock, prof = discover(m)
        print(f"\n  tail of the session, {m} "
              f"(clock, days, mean share):")
        for c in sorted(prof)[-12:]:
            n, share, nz = prof[c]
            bar = "#" * max(0, int(share * 200))
            print(f"    {c}  n={n:<6}{share:>7.2%}  {bar}")
    bad = [m for m, v in found.items()
           if v.get("agrees_with_published") is False]
    if bad:
        print(f"\n  !! {', '.join(bad)}: the measured slot is NOT "
              f"where the exchange's auction runs.")
        print(f"     Almost always this means the auction is "
              f"absent from the data and the")
        print(f"     spike found is the end-of-day ramp in the "
              f"last CONTINUOUS bar. Do not")
        print(f"     use these markets until `harvest` + `verify` "
              f"say otherwise.")
    OUT.write_text(json.dumps(
        {"_what": "measured auction bar per market",
         "_method": "last clock slot holding >=1% of the day on "
                    ">=20 ordinary days, useRTH bars as held",
         "measured": found, "published_expectation": EXPECTED},
        indent=1), encoding="utf-8")
    print(f"\n-> {_rel(OUT)}")
    return 0


# ── probe ────────────────────────────────────────────────────────────

def cmd_probe(a):
    """Fetch the SAME days twice — useRTH=1 and useRTH=0 — and print
    both tails side by side.

    This is the whole question in one screen: does IB deliver the
    auction print at all when regular hours are switched off? If it
    does not, no amount of re-harvesting fixes these markets and the
    honest move is to drop them from the comparison.
    """
    from ib_5m_events import _con, _connect

    probes = {"Japan": "7203", "Korea": "005930",
              "Australia": "BHP", "Taiwan": "2330"}
    markets = [a.market] if a.market else list(probes)
    ib = _connect()
    try:
        for m in markets:
            sym = probes.get(m)
            if not sym:
                print(f"{m}: no probe symbol")
                continue
            con = _con(ib, m, sym)
            if not con:
                print(f"{m}: could not resolve {sym}")
                continue
            print(f"\n=== {m} {sym} — expectation: "
                  f"{EXPECTED.get(m, '—')}")
            for rth in (True, False):
                try:
                    bars = ib.reqHistoricalData(
                        con,
                        endDateTime=dt.datetime.now().strftime(
                            "%Y%m%d") + "-23:59:59",
                        durationStr=f"{a.days} D",
                        barSizeSetting="5 mins",
                        whatToShow="TRADES", useRTH=rth,
                        formatDate=1)
                except Exception as e:               # noqa: BLE001
                    print(f"  useRTH={int(rth)}: FAILED "
                          f"{type(e).__name__}: {e}")
                    continue
                days = _by_day([[str(b.date), b.volume]
                                for b in bars or []])
                if not days:
                    print(f"  useRTH={int(rth)}: no bars")
                    continue
                last = sorted(days)[-1]
                rows = [(str(b[0])[11:16], b[-1] or 0)
                        for b in days[last]]
                tot = sum(v for _c, v in rows) or 1
                tail = rows[-8:]
                print(f"  useRTH={int(rth)}  {last}  "
                      f"{len(rows)} bars, tail:")
                for c, v in tail:
                    print(f"     {c}  {v:>14,.0f}  "
                          f"{v / tot:>6.1%}")
    finally:
        ib.disconnect()
    print("\nRead the two tails: a clock slot present at useRTH=0 "
          "and absent at useRTH=1,\ncarrying a large share, IS the "
          "auction — and is what the RTH harvest dropped.")
    return 0


# ── harvest ──────────────────────────────────────────────────────────

def cmd_harvest(a):
    """Re-fetch the affected windows with useRTH=0.

    Writes data/ib_5m/<Market>.rth0.json rather than overwriting the
    original. The existing files are the evidence for the bug; an
    in-place rewrite would destroy the before-picture, and this
    project has already lost two files that way.
    """
    import ib_5m_events as E

    markets = [a.market] if a.market else list(AFFECTED)
    for m in markets:
        d = _load(m)
        if not d:
            print(f"{m}: no source file")
            continue
        dest = SRC / f"{m}.rth0.json"
        done = (json.loads(dest.read_text(encoding="utf-8"))
                if dest.exists() else
                {"market": m, "src": "IB 5m TRADES useRTH=0",
                 "windows": {}})
        skipped = done.setdefault("skipped", {})
        dead = _load_dead()
        deadm = dead["markets"].setdefault(m, {})
        if getattr(a, "retry_dead", False):
            deadm.clear()
            skipped.clear()

        # ── WHAT NOT TO ASK, AND WHY ────────────────────────────
        #
        # c-317, from Bill's Korea run: 25+ error-162 lines, most
        # of them KOSDAQ names, several of them the SAME symbol
        # in three different reviews.
        #
        # THE STRUCTURAL FILTER, and it is analytical before it is
        # economic. This script exists to test whether useRTH=0
        # surfaces a closing-auction bar that useRTH=1 dropped.
        # That question only has meaning for a window that HAS
        # bars. A window the original harvest left empty
        # contributes to neither clock profile, so re-asking it
        # cannot change any verdict — and Japan settled the
        # empirical half: all 247 windows came back byte-identical
        # under the flag, so useRTH=0 does not conjure a series
        # where there was none.
        #
        # Korea: 60 of 162 windows are empty at source, 33 of them
        # KOSDAQ. That is 37% of the request budget spent on
        # questions that have no answer, and every one of them
        # produces an error line indistinguishable from a real
        # fault — which is what made the run look broken.
        # `--include-empty` overrides this. It is a SEPARATE flag
        # from `--retry-dead` on purpose: a refused symbol is a
        # fact about the account and may change when a
        # subscription does, whereas an empty window is a fact
        # about the comparison and does not change at all. Merging
        # them into one switch would invite re-asking 60 windows
        # to clear 2 refusals.
        empty_at_source = ([] if getattr(a, "include_empty", False)
                           else [k for k in d["windows"]
                                 if not (d["windows"][k].get("px"))])
        for k in empty_at_source:
            skipped.setdefault(k, {
                "reason": "empty at source — the useRTH=1 harvest "
                          "returned no bars for this window, so "
                          "there is no auction bar to recover and "
                          "nothing to compare",
                "code": d["windows"][k].get("code")})

        todo = [k for k in d["windows"]
                if k not in done["windows"] and k not in skipped]
        # a symbol IB has already refused is not asked again
        pre_dead = [k for k in todo
                    if str(d["windows"][k].get("code")) in deadm]
        for k in pre_dead:
            skipped.setdefault(k, {
                "reason": f"symbol already refused: "
                          f"{deadm[str(d['windows'][k]['code'])]['kind']}",
                "code": d["windows"][k].get("code")})
        todo = [k for k in todo if k not in skipped]
        # GROUP BY SYMBOL. 50 of Korea's 103 codes appear in more
        # than one review, so processing a code's windows together
        # lets one refusal stop the rest immediately instead of
        # after another eighty windows.
        todo.sort(key=lambda k: (str(d["windows"][k].get("code")),
                                 k))
        if a.limit:
            todo = todo[:a.limit]
        print(f"{m}: {len(todo)} windows to re-fetch "
              f"({len(done['windows'])} already done, "
              f"{len(skipped)} skipped)")
        print(f"  skipped: {len(empty_at_source)} empty at source, "
              f"{len(pre_dead)} on already-refused symbols")
        if not todo:
            dest.write_text(json.dumps(done), encoding="utf-8")
            continue
        ib = E._connect()
        # Boards IB has explicitly refused this run, and a running
        # tally per localSymbol suffix. The suffix tally is the
        # ADAPTIVE half: nothing here assumes KOSDAQ is
        # unreachable, it measures it. After BOARD_MIN attempts on
        # a suffix with not one success, the suffix is dropped and
        # the reason is recorded.
        BOARD_MIN = 6
        refused_boards, tally = set(), collections.defaultdict(
            lambda: [0, 0])          # suffix -> [attempts, wins]
        try:
            for i, key in enumerate(todo, 1):
                w = d["windows"][key]
                code = str(w.get("code"))
                sfx = code.split(".")[-1] if "." in code else ""
                if code in deadm:
                    skipped[key] = {
                        "reason": f"symbol already refused: "
                                  f"{deadm[code]['kind']}",
                        "code": code}
                    continue
                att, win = tally[sfx]
                if sfx and att >= BOARD_MIN and win == 0:
                    skipped[key] = {
                        "reason": f"suffix .{sfx} refused on every "
                                  f"one of {att} attempts this run "
                                  f"— not asked again",
                        "code": code}
                    continue
                # `_con` returns (contract, venue), NOT a
                # contract. Passing the tuple to
                # reqHistoricalData made ib_async reach for
                # contract attributes on a tuple and raise
                # AttributeError on all 247 windows.
                #
                # And the old guard could never have caught it:
                # `if not con` on a 2-tuple is False even when
                # the tuple is (None, None), so an unresolved
                # symbol sailed through as well. Unpack, then
                # test the CONTRACT.
                con, venue = E._con(ib, m, w["code"])
                if con is None:
                    print(f"  {key}: contract not resolved "
                          f"({w['code']})")
                    continue
                # FOUR THINGS THIS HAS TO COPY FROM
                # ib_5m_events, and getting any of them wrong is
                # either a crash or worse:
                #
                # 1. _chunks takes dt.date, not the ISO STRINGS
                #    the window file stores. This one at least
                #    fails loudly ("unsupported operand type(s)
                #    for -: 'str' and 'str'").
                # 2. the timestamp is str(bar.date)[:16] —
                #    "2008-03-31 11:05". Keeping the seconds
                #    would make these rows sort and compare
                #    differently from every other file we hold.
                # 3. chunks tile BACKWARDS from the end date and
                #    overshoot the start, so bars outside the
                #    window have to be dropped.
                # 4. consecutive chunks OVERLAP at their seam.
                #    Without a dedupe the same bar is stored
                #    twice, and clock_profile divides each bar by
                #    the day's total — so a duplicated bar
                #    inflates the denominator and quietly moves
                #    every share on the chart. Silent, and the
                #    exact failure this whole re-harvest exists
                #    to undo.
                # c-314 BUG: these two were named `a` and `b`, and
                # `a` IS THE ARGPARSE NAMESPACE this function was
                # called with. Rebinding it to a date destroyed the
                # arguments — so the FIRST market completed and the
                # second died on `if a.limit` with "'datetime.date'
                # object has no attribute 'limit'".
                #
                # Which is why only Japan exists: a bare
                # `harvest` (no --market) walks Japan, Korea,
                # Australia in order, and it never reached Korea.
                # Bill's run looked like a success because he
                # passed --market Japan and there was no second
                # iteration to crash.
                d0 = dt.date.fromisoformat(w["start"])
                d1 = dt.date.fromisoformat(w["end"])
                chunks = E._chunks(d0, d1)
                rows, refusal = [], None
                tally[sfx][0] += 1
                for n, (end, span) in enumerate(chunks):
                    bars, err = _bars_rth0(ib, E, con, end, span)
                    kind, board = _classify(err)
                    if board:
                        refused_boards.add(board)
                    if err and not bars:
                        # ONE LINE PER SYMBOL, NOT PER CHUNK. The
                        # old loop printed every failing chunk, so
                        # a dead name produced two identical error
                        # lines and the log read as twice the
                        # problem it was.
                        if refusal is None:
                            print(f"  {key} [{code}]: "
                                  f"{kind} — {str(err[1])[:70]}")
                        refusal = refusal or kind
                        # EARLY ABORT. A permission refusal or an
                        # HMDS "no data" is a property of the
                        # SYMBOL, not of the date range — the same
                        # codes failed in 2018, 2020 and 2024
                        # windows alike. Once the first chunk has
                        # refused and nothing has been collected,
                        # the remaining chunks are known-futile
                        # requests.
                        if not rows and kind in ("permission",
                                                 "nodata",
                                                 "timeout"):
                            break
                    for x in bars:
                        ts = str(x.date)[:16]
                        if d0.isoformat() <= ts[:10] <= d1.isoformat():
                            rows.append([ts, x.open, x.high,
                                         x.low, x.close,
                                         x.volume])
                if rows:
                    tally[sfx][1] += 1
                elif refusal in ("permission", "nodata"):
                    # remember the symbol so no other review asks
                    deadm[code] = {"kind": refusal,
                                   "board": (sorted(refused_boards)[-1]
                                             if refused_boards else None),
                                   "first_seen_window": key}
                seen, px = set(), []
                for r in sorted(rows):
                    if r[0] not in seen:
                        seen.add(r[0])
                        px.append(r)
                if px:
                    nw = dict(w)
                    nw["px"] = px
                    nw["src"] = "IB 5m TRADES useRTH=0"
                    nw["venue"] = venue or nw.get("venue")
                    done["windows"][key] = nw
                if i == 10 and not done["windows"]:
                    # TEN FOR TEN IS NOT DATA, IT IS A BUG.
                    # The tuple mistake burned all 247 windows
                    # and printed 247 near-identical lines
                    # before writing an empty file that looked
                    # like a completed run.
                    print("\n  STOPPING: 10 of 10 windows "
                          "returned nothing.\n  That is a code "
                          "or entitlement fault, not thin data "
                          "— fix it before\n  spending the "
                          "other 237 requests.")
                    break
                if i % 5 == 0 or i == len(todo):
                    dest.write_text(json.dumps(done),
                                    encoding="utf-8")
                    DEAD.write_text(json.dumps(dead, indent=1),
                                    encoding="utf-8")
                    print(f"  {i}/{len(todo)}  "
                          f"({len(done['windows'])} with data, "
                          f"{len(deadm)} symbols refused)")
        finally:
            ib.disconnect()
        dest.write_text(json.dumps(done), encoding="utf-8")
        DEAD.write_text(json.dumps(dead, indent=1), encoding="utf-8")
        print(f"  -> {_rel(dest)}")
        if refused_boards:
            print(f"  IB named these boards as unpermissioned: "
                  f"{', '.join(sorted(refused_boards))}")
        quiet = [s for s, (att, win) in tally.items()
                 if s and att >= BOARD_MIN and win == 0]
        if quiet:
            print(f"  suffixes that never returned data: "
                  f"{', '.join('.' + s for s in quiet)} — recorded, "
                  f"not asked again")
        if deadm:
            print(f"  {len(deadm)} symbols in "
                  f"{_rel(DEAD)}; `--retry-dead` clears them")
    return 0


# How long to wait on one historical request before giving up.
# c-317: Bill's Korea run hit "reqHistoricalData: Timeout for
# Contract(... 00104K ...)" and then error 162 "query cancelled".
# ib_async's default is 60 seconds, and a symbol that is going to
# hang hangs on every chunk — so one bad name can cost minutes
# while returning nothing. 25 seconds is comfortably longer than
# any successful 5-minute request measured on this project and
# turns a hang into a skip.
REQ_TIMEOUT = 25


def _bars_rth0(ib, E, con, end_date, days):
    """E._bars with regular hours OFF — same pacing and the same
    error capture, so a failure here reads like every other IB
    failure in this project."""
    import time
    before = len(E._ERRORS)
    exc = None
    try:
        b = ib.reqHistoricalData(
            con, endDateTime=end_date.strftime("%Y%m%d")
            + "-23:59:59", durationStr=f"{days} D",
            barSizeSetting="5 mins", whatToShow="TRADES",
            useRTH=False, formatDate=1, timeout=REQ_TIMEOUT)
    except TypeError:
        # older ib_async/ib_insync without the kwarg — better to
        # run slowly than not at all, and the fallback is
        # announced rather than silent
        try:
            b = ib.reqHistoricalData(
                con, endDateTime=end_date.strftime("%Y%m%d")
                + "-23:59:59", durationStr=f"{days} D",
                barSizeSetting="5 mins", whatToShow="TRADES",
                useRTH=False, formatDate=1)
        except Exception as e:                      # noqa: BLE001
            b, exc = [], f"{type(e).__name__}: {str(e)[:120]}"
    except Exception as e:                          # noqa: BLE001
        b, exc = [], f"{type(e).__name__}: {str(e)[:120]}"
    time.sleep(E.PACE)
    err = (E._ERRORS[-1] if len(E._ERRORS) > before
           else (0, f"local {exc}") if exc else None)
    return list(b or []), err


# ── knowing what not to ask ──────────────────────────────────────────

DEAD = ROOT / "data" / "ib_dead_symbols.json"

# Messages that mean "this symbol will never answer", as opposed
# to "this date range is empty". IB uses error 162 for both, so
# the text is the only discriminator available.
_PERMANENT = ("no market data permissions",
              "hmds query returned no data")


def _load_dead():
    if DEAD.exists():
        try:
            return json.loads(DEAD.read_text(encoding="utf-8"))
        except Exception:                           # noqa: BLE001
            pass
    return {"_what": "symbols IB has refused, so they are not "
                     "asked again", "markets": {}}


def _classify(err):
    """(kind, board) for one IB error tuple.

    `board` is only set when IB names it — "No market data
    permissions for KOSDAQ STK" — which is the one time we learn
    something about a whole exchange rather than one symbol.
    """
    if not err:
        return "ok", None
    msg = str(err[1]).lower()
    board = None
    if "no market data permissions" in msg:
        # "...permissions for KOSDAQ STK"
        part = msg.split("permissions for", 1)[-1].strip()
        board = part.split()[0].upper() if part else None
        return "permission", board
    if "hmds query returned no data" in msg:
        return "nodata", None
    if "timeout" in msg or "cancelled" in msg:
        return "timeout", None
    return "other", None


# ── verify ───────────────────────────────────────────────────────────

def cmd_verify(_a):
    """Did the re-harvest actually recover an auction?

    Compares the measured auction bar before and after, per market,
    and states plainly where the answer is still no.
    """
    print("market      RTH bars           useRTH=0 bars      verdict")
    for m in AFFECTED:
        before_clock, before_prof = discover(m)
        p = SRC / f"{m}.rth0.json"
        if not p.exists():
            print(f"{m:<12}{str(before_clock):<19}"
                  f"{'not harvested':<19}run `harvest --market "
                  f"{m}`")
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        prof = clock_profile(m, windows=d["windows"])
        # c-314: the SAME rule as `before`. See `pick_auction`.
        after, ratio = pick_auction(prof)
        # DID THE RE-HARVEST RETURN DIFFERENT BARS AT ALL? This is
        # a separate question from "did the auction appear", and
        # the old code answered the second while printing a claim
        # about the first: it said "IB serves no auction print for
        # this venue" whenever the clock was unmoved.
        #
        # For Japan all 247 windows came back BYTE-IDENTICAL to the
        # useRTH=1 file. That supports "the flag changed nothing",
        # which is a statement about the request. It does not by
        # itself support a claim about what IB holds — and the two
        # are worth keeping apart, because identical output is also
        # what a harvest that silently re-saved its input looks
        # like.
        src = _load(m) or {"windows": {}}
        shared = set(src["windows"]) & set(d["windows"])
        ident = sum(1 for k in shared
                    if src["windows"][k].get("px")
                    == d["windows"][k].get("px"))
        same_bars = bool(shared) and ident == len(shared)
        if same_bars:
            print(f"{m:<12}{str(before_clock):<19}"
                  f"{str(after):<19}"
                  f"useRTH=0 returned IDENTICAL bars in all "
                  f"{len(shared)} windows")
            continue
        if after is None:
            verdict = ("no qualifying bar — useRTH=0 served "
                       "nothing that spikes")
        elif before_clock is None:
            verdict = (f"RECOVERED — {prof[after][1]:.1%} of the "
                       f"day at {after}, {ratio:.1f}x its run-in")
        elif _mins(after) > _mins(before_clock):
            # LATER is the only direction that counts. A different
            # slot EARLIER than the one RTH already served is not a
            # recovered auction — it is the discriminator picking a
            # different continuous bar, and calling that "recovered"
            # would be the second wrong answer in this function.
            verdict = (f"RECOVERED — {prof[after][1]:.1%} of the "
                       f"day at {after}, {ratio:.1f}x its run-in")
        elif after == before_clock:
            verdict = ("unchanged — IB serves no auction print "
                       "for this venue")
        else:
            verdict = (f"CHANGED BUT EARLIER than {before_clock} "
                       f"— not an auction, inspect by hand")
        print(f"{m:<12}{str(before_clock):<19}{str(after):<19}"
              f"{verdict}")
    print("\nNOT addressed here, and not by any useRTH flag:")
    print("  Japan   the sample straddles the TSE reform of "
          "2024-11-05, which moved the")
    print("          close from 15:00 to 15:30 and ADDED a closing "
          "auction. The 15:00-15:25")
    print("          slots exist on only ~21% of days for exactly "
          "that reason, so the")
    print("          pooled profile mixes two session structures "
          "and its 14:55 answer")
    print("          describes the OLD one. Split the sample at "
          "2024-11-05 before")
    print("          concluding anything about the post-reform "
          "auction.")
    print("  India   NSE's close is a 30-minute VWAP, not an "
          "auction — drop it from the comparison.")
    print("  China   rows are routed SEHKNTL (Northbound Connect "
          "flow, not SSE/SZSE volume);")
    print("          needs a venue fix in "
          "ib_5m_events._china_venue and a full re-harvest.")
    print("  HongKong  mixes pre/post-CAS eras (CAS began "
          "25 Jul 2016) — split the sample by date.")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("probe")
    p.add_argument("--market")
    p.add_argument("--days", type=int, default=3)
    d = sub.add_parser("discover")
    d.add_argument("--market")
    d.add_argument("--show", help="print the session tail for one "
                                  "market")
    h = sub.add_parser("harvest")
    h.add_argument("--market")
    h.add_argument("--limit", type=int, default=0)
    h.add_argument("--retry-dead", action="store_true",
                   dest="retry_dead",
                   help="clear the refused-symbol ledger for this "
                        "market — use after changing an IB market-"
                        "data subscription")
    h.add_argument("--include-empty", action="store_true",
                   dest="include_empty",
                   help="also re-ask windows the useRTH=1 harvest "
                        "left empty; they cannot change any "
                        "verdict, so this is for auditing only")
    sub.add_parser("verify")
    a = ap.parse_args()
    return {"probe": cmd_probe, "discover": cmd_discover,
            "harvest": cmd_harvest, "verify": cmd_verify}.get(
                a.cmd, cmd_discover)(a)


if __name__ == "__main__":
    raise SystemExit(main())
