"""5-minute bars for every index mover, every market IB serves
(c-193).

WINDOW: announcement - 45 calendar days -> effective + 45.
Bill asked for "30 days" either side. 30 CALENDAR days is only
~21 trading sessions; 45 calendar delivers ~31 sessions. The
wider span costs nothing extra per request and lets the
ANALYSIS slice to either definition, so the harvest is generous
once and the decision is made later. This matches
apac_event_days.py exactly, so the 5-minute and daily datasets
line up bar-for-bar on the same window.

THE THING THAT DECIDES THE JOB SIZE: each market's own 5-MINUTE
edge. It is NOT the daily depth. The c-190 probe found 15 years
of DAILY bars for Hong Kong, Korea, Singapore, Australia and
India — that says nothing about how far back 5m bars go. Taiwan
is the proof: 15y of daily, but 5m stops at 2023-04-25
(bisected c-192, and the error text near the boundary changes
from "No market data permissions" to "HMDS query returned no
data", i.e. a real data edge rather than an entitlement wall).

So `edges` measures the 5m edge per market BEFORE any bulk
fetch — about 11 requests each, 15 minutes for all seven — and
`plan` then reports the true scope. Measuring first can save
hours of fetching against a floor that does not exist.

SCOPE, if every market's 5m edge matched Taiwan's:
    ~660 name-events x 3 chunks = ~2,000 requests = ~6 hours.
If the others reach back to 2015:
    ~1,700 name-events = ~5,200 requests = ~16 hours.
China alone is 1,253 name-events — it dominates, and it is the
one market where a 2014 edge is already proven.

PACING — see the PACE block below. The "60 requests per 10
minutes" rule I originally paced against applies to bars of 30
SECONDS OR LESS; for 5-minute bars IB has lifted the hard limit
and left only an unpublished soft throttle. `tune` measures it
rather than guessing, and the estimates above are ~7x too
pessimistic as a result. Everything is resumable at (market,
review, code) granularity, so stopping and restarting costs
nothing.

RUNS ON BILL'S MACHINE — TWS or IB Gateway, API enabled.

Usage:
  python scripts\\ib_5m_events.py tune             (pacing FIRST)
  python scripts\\ib_5m_events.py edges            (then edges)
  python scripts\\ib_5m_events.py plan
  python scripts\\ib_5m_events.py fetch Taiwan
  python scripts\\ib_5m_events.py fetch            (all markets)
Out: data/ib_5m/<Market>.json, data/ib_5m_edges.json,
     data/ib_pace.json
"""
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "data" / "ib_5m"
EDGES = ROOT / "data" / "ib_5m_edges.json"
HOST, PORTS = "127.0.0.1", (7497, 7496, 4001, 4002)

# c-197: PACING, corrected against IB's own documentation.
#
# I set 11 s from the "no more than 60 requests in any ten
# minute period" rule and told Bill a 35-minute Taiwan run was
# the price of doing business. That rule is real, but I did not
# read the footnote on the same page:
#
#   "At this time Historical Data Limitations for barSize =
#    '1 mins' and greater have been lifted. However ... we still
#    implement a 'soft' slow to load-balance client requests vs.
#    server response."
#   -- interactivebrokers.github.io/tws-api/historical_limitations
#
# The hard 60/10min cap governs bars of 30 SECONDS OR LESS. We
# request FIVE-MINUTE bars, which are above the line, so what
# remains is a soft throttle with no published number. I was
# pacing against the wrong rule and it cost roughly 7x.
#
# The same page also says the limits "apply to all our clients
# and it is not possible to overcome them" — so no amount of
# money raises them. Speed here is a measurement problem, not a
# purchasing one.
#
# Since IB publishes no number for the soft limit, `tune`
# measures it on Bill's own connection and writes the answer to
# data/ib_pace.json. Until it runs, 3 s is the default: well
# inside anything observed, still ~4x the old rate.
PACE_FILE = ROOT / "data" / "ib_pace.json"
PACE_DEFAULT = 3.0

# Days of 5-minute bars per request. 30 was a guess that worked,
# never a measured ceiling. IB's step-size guidance is "only a
# few thousand bars at a time"; a Taiwan session is ~54 five-
# minute bars, so 30 calendar days is ~1,100 bars — comfortably
# under. `tune` walks the ladder up to find the real limit,
# because every doubling halves the request count for the whole
# APAC harvest.
CHUNK_DEFAULT = 30
CONCURRENCY_DEFAULT = 1    # 1 = sequential, until measured


def _tuned(key, default):
    if PACE_FILE.exists():
        try:
            v = json.loads(PACE_FILE.read_text(encoding="utf-8")).get(key)
            if v:
                return v
        except Exception:                          # noqa: BLE001
            pass
    return default


def _pace():
    return float(_tuned("safe_seconds", PACE_DEFAULT))


def _chunk_days():
    return int(_tuned("chunk_days", CHUNK_DEFAULT))


def _concurrency():
    return int(_tuned("concurrency", CONCURRENCY_DEFAULT))


PACE = _pace()
CHUNK_DAYS = _chunk_days()

PRE_ANN_DAYS = 45          # ~31 trading sessions
POST_EFF_DAYS = 45

# c-222: HARD LEFT BOUNDARY, Bill's call. Several venues serve
# 5m bars well before this — Japan reaches 2004, Australia and
# Korea 2004, Hong Kong 2007 — and we are declining to use it.
#
# The reason is not storage. A 2007 Hong Kong window and a 2024
# Hong Kong window are not the same experiment: index-review
# mechanics, the passive share of the register, and the tick
# regime all changed in between. Splicing eighteen years into
# one distribution buys sample size at the cost of knowing what
# the sample is of. 2015 also happens to be where the daily
# harvest starts, so the two datasets line up.
#
# This is a POLICY, not a measurement. The measured floors stay
# in data/ib_5m_boundary.json untouched, so raising or lowering
# this line later costs one edit and a re-run, not a re-probe.
SINCE = os.environ.get("IB5M_SINCE", "2015-01-01")

# c-222: IB errors that mean STOP, not skip. 438 is the account
# lockout Bill hit — every subsequent request fails identically,
# so continuing writes hundreds of false "no data" verdicts into
# the file at full speed. The run must end and say why.
FATAL = {438: "the IB account is LOCKED (error 438). Log in to "
              "TWS and clear the lock, then re-run — progress "
              "is saved.",
         1100: "TWS lost its connection to IB (error 1100). "
               "Re-run once TWS reconnects.",
         504: "not connected to TWS (error 504)."}

# exchange, currency — codes MEASURED by ib_probe c-190
EXCH = {
    "Taiwan":    ("TWSE", "TWD"),
    "HongKong":  ("SEHK", "HKD"),
    "Korea":     ("KRX", "KRW"),      # NOT "KSE" — that fails
    "Singapore": ("SGX", "SGD"),
    "Australia": ("ASX", "AUD"),
    "India":     ("NSE", "INR"),
    "Japan":     ("TSEJ", "JPY"),     # c-199: Bill subscribed
    "China":     ("SEHKNTL", "CNH"),  # DEFAULT ONLY — see below
}


def _china_venue(ticker):
    """MSCI China spans THREE venues. One exchange code cannot
    serve it.

    c-199. MSCI's own description: the index "captures large and
    mid cap representation across China A shares, H shares, B
    shares, Red chips, P chips and foreign listings (e.g.
    ADRs)". Our changes DB agrees — 2015+ movers by venue:

        Shanghai  .SS   539
        Shenzhen  .SZ   530
        Hong Kong .HK   208
        A-share bare 6-digit (Stock Connect)  54
        US ADR            2

    EXCH pinned all 1,333 to SEHKNTL, which is Stock Connect
    SHANGHAI. That routes the .SS names correctly and misroutes
    roughly 80% of the rest — the same one-venue-per-market
    mistake as Taiwan TWSE/TPEx (c-195) and Korea KOSPI/KOSDAQ
    (c-195), now for the third time and at the largest scale.
    Fixing it before the run rather than after it.

    IB reaches mainland A-shares ONLY through Stock Connect
    Northbound, which Bill has accepted. Shanghai is SEHKNTL and
    Shenzhen is SEHKSZSE; both quote in offshore CNH.
    """
    # c-225: STRIP THE SUFFIX FIRST, THEN ROUTE ON THE NUMBER.
    #
    # I wrote this function with a branch per suffix and a
    # separate branch for bare codes, so the board logic below
    # only ever ran on bare codes — "688313.SS" returned from
    # the .SS branch before reaching it. That is the SAME
    # ordering bug as the Hong Kong zero-padding at c-222,
    # committed in the same file, three days later, while
    # writing the fix for the thing the padding bug taught me.
    # The suffix is decoration; the number is the fact.
    t = str(ticker).strip().upper()
    suf = t[-3:] if t[-3:] in (".HK", ".SS", ".SZ") else ""
    base = t[:-3] if suf else t
    if suf == ".HK" or (not suf and base.isdigit()
                        and len(base) < 6):
        return "SEHK", "HKD", (str(int(base)) if base.isdigit()
                               else base)
    if base.isdigit() and len(base) == 6:
        # FOUR BOARDS, NOT TWO — measured by the c-224
        # pre-flight, which is the only reason we know:
        #
        #   Stock('300620','SEHKSZSE','CNH') -> error 200,
        #     blank-exchange search resolved it on CHINEXT
        #   Stock('688313','SEHKNTL','CNH')  -> error 200,
        #     blank-exchange search resolved it on SEHKSTAR
        #
        # Both then served bars, so the venue was never the
        # problem — my code for it was. ChiNext (300/301) and
        # the STAR board (688/689) are separate IB exchanges,
        # not sub-boards of Shenzhen and Shanghai. 256 of
        # China's 1,333 windows sit on them, and each was paying
        # an extra failed request before the fallback rescued
        # it. Waste rather than loss — but the venue recorded on
        # the window would have been wrong, and wrong provenance
        # outlives a wasted request.
        pre = base[:3]
        return (("SEHKSTAR" if pre in ("688", "689")
                 else "CHINEXT" if pre in ("300", "301")
                 else "SEHKNTL" if base[:2] == "60"
                 else "SEHKSZSE"), "CNH", base)
    if base.isdigit():
        return "SEHK", "HKD", str(int(base))
    return "SMART", "USD", base       # ADR


# Legacy fallback only. Every real floor now comes from
# data/ib_5m_boundary.json via _boundary_edge().
KNOWN_EDGE = {"Taiwan": "2023-04-27"}

_ERRORS = []


def _hook(ib):
    def on_err(reqId, code, msg, contract=None):
        _ERRORS.append((code, str(msg)[:200]))
    try:
        ib.errorEvent += on_err
    except Exception:                              # noqa: BLE001
        pass


def _connect():
    """Connect, rotating the client id.

    c-208 — WHY THE LAST RUN FETCHED NOTHING. TWS answered
    "Error 326: Unable to connect as the client id is already in
    use", because a previous run's session for clientId 95 was
    still held. The old loop caught that, moved on to the next
    PORT, failed there for the same reason, exhausted the list
    and reported

        no TWS/Gateway on (7497, 7496, 4001, 4002)

    which is a diagnosis of the wrong thing entirely — TWS was
    running and listening the whole time. Bill would reasonably
    have gone looking at ports and firewalls.

    Two fixes. The id is now RANDOM per run, so a stale session
    cannot block a new one; and error 326 is recognised, so the
    failure message names the real cause instead of blaming the
    port list.
    """
    import random
    try:
        from ib_async import IB
    except ImportError:
        raise SystemExit("pip install ib_async")
    ib = IB()
    tried, saw_326 = [], False
    for attempt in range(4):
        cid = random.randint(200, 9990)
        for port in PORTS:
            try:
                ib.connect(HOST, port, clientId=cid, timeout=8)
                # c-222: ib_async's default request timeout is
                # short enough that a cold HMDS query on a thin
                # or newly-created contract loses the race —
                # eight Korean windows were written off that
                # way. Waiting two minutes for a request that
                # costs one is a good trade when the whole run
                # is hours long.
                try:
                    ib.RequestTimeout = float(
                        os.environ.get("IB5M_REQ_TIMEOUT", 120))
                except Exception:                  # noqa: BLE001
                    pass
                print(f"connected 127.0.0.1:{port} "
                      f"(clientId {cid})")
                _hook(ib)
                return ib
            except Exception as e:                 # noqa: BLE001
                msg = str(e)
                if "326" in msg or "already in use" in msg:
                    saw_326 = True
                tried.append(f"{port}/{cid}")
    if saw_326:
        raise SystemExit(
            "TWS is running but refused every client id "
            "(Error 326 — already in use).\n"
            "  A previous session is still held open. Fix by "
            "either:\n"
            "    * File > Global Configuration > API > Settings "
            "> 'Reset API order ID sequence' / restart TWS, or\n"
            "    * closing any other script still connected.\n"
            f"  tried: {', '.join(tried[:8])}")
    raise SystemExit(
        f"no TWS/Gateway listening on {PORTS}. Start TWS or IB "
        f"Gateway and enable File > Global Configuration > API "
        f"> Settings > 'Enable ActiveX and Socket Clients'.")


def _norm_sym(market, sym):
    """A source ticker as IB wants to hear it.

    c-222: pulled out of _con so the ORDER can be tested. The
    order was the bug — see the comment in _con.
    """
    sym = str(sym).strip()
    if "." in sym:
        sym = sym.split(".")[0]
    if market == "HongKong" and sym.isdigit():
        sym = str(int(sym))
    if market == "Korea" and sym.isdigit():
        sym = f"{int(sym):06d}"
    return sym


def _con(ib, market, symbol):
    """c-195: resolve on the primary code, then WITHOUT an
    exchange.

    3105 (Win Semiconductors) failed with error 200, "no security
    definition", because EXCH pins every Taiwan name to "TWSE" —
    and 3105 is TPEx-listed. Our own universe file says so:
        data/tw_mieu_universe.json -> 3105 -> "mkt": "tpex"
    Taiwan has TWO boards and this map only ever names one, so
    every TPEx mover was unreachable. The same shape of error
    will hit any market where a mover sits on a second venue.

    Rather than guess IB's code for the Taipei Exchange, the
    fallback asks with exchange="" and lets IB return whatever
    listings it has for that symbol and currency. If IB carries
    no TPEx line at all, we learn that as a fact instead of
    mistaking it for a typo. The venue that resolved is recorded
    on the window so coverage can be audited by board.
    """
    from ib_async import Stock
    sym = str(symbol).strip()
    if market == "China":
        exch, ccy, sym = _china_venue(sym)
    else:
        exch, ccy = EXCH[market]
        # c-225: same lesson as China, measured the same way.
        # Stock('6223','TWSE','TWD') errors and the blank search
        # resolves it on TPEX. Our own universe file already
        # knows 6223 is TPEx-listed, so asking TWSE first was a
        # request we always knew would fail.
        if market == "Taiwan" and _board(
                market, str(symbol).split(".")[0]) == "tpex":
            exch = "TPEX"
        # c-222: STRIP THE SUFFIX FIRST. This is the c-204 fix
        # in the wrong order, and the ordering cost 33 of Hong
        # Kong's 55 windows — including Tencent.
        #
        # c-204 removed Yahoo's zero-padding for IB, correctly:
        # Yahoo wants "0700.HK", IB wants "700". But it tested
        # `sym.isdigit()` BEFORE the suffix was removed, and
        # "0700.HK".isdigit() is False. So the de-padding never
        # ran on any suffixed code, the ".HK" came off after,
        # and IB was asked for "0700" — the exact string c-204
        # had proven does not resolve.
        #
        # The tell was in the log the whole time: every symbol
        # that failed began with a zero, every symbol that
        # succeeded did not. I fixed the transformation and not
        # the pipeline it sits in.
        sym = _norm_sym(market, sym)
    # c-229: IB TRUNCATES NSE SYMBOLS TO NINE CHARACTERS.
    #
    # `symbols India` separated 46 codes perfectly by LENGTH:
    #
    #   resolved   35 codes, longest 9 (EICHERMOT, LICHSGFIN,
    #              POWERGRID)
    #   unresolved 11 codes, every one exactly 10
    #
    # and IB's own search gave the mechanism away on the single
    # case where it returned anything at all: asked for
    # BAJAJ-AUTO it offered "BAJAJ-AUT/INR@NSE" — the same name,
    # nine characters. ASIANPAINT, BHARTIARTL, ULTRACEMCO,
    # BAJFINANCE and the rest are not missing from IB; they are
    # spelled shorter.
    #
    # This is a HYPOTHESIS with perfect separation, not a fact I
    # can cite, so IB stays the referee: the truncation is only
    # ever an extra candidate, and a window records which form
    # actually paid.
    _trunc = (sym[:9] if market == "India" and len(sym) > 9
              else None)
    # c-222: a US ADR carries a LETTER code and no local line.
    # FUTU was asked for as Stock("FUTU", "SEHK", "HKD") and of
    # course did not resolve — MSCI counts the ADR in the Hong
    # Kong index, but the security trades in New York in USD.
    tries = [(sym, exch, ccy), (sym, "", ccy)]
    if _trunc:
        tries.append((_trunc, exch, ccy))
    if not sym.isdigit() and ccy != "USD":
        tries.append((sym, "SMART", "USD"))
    for s, ex, cur in tries:
        try:
            det = ib.reqContractDetails(Stock(s, ex, cur))
        except Exception:                          # noqa: BLE001
            det = None
        if det:
            c = det[0].contract
            if s != sym:
                print(f" [{sym}->{s}]", end="", flush=True)
            return c, (c.primaryExchange or c.exchange or ex
                       or "?")
        time.sleep(0.4)
    # c-222: last resort — ASK IB what it calls this name.
    # India lost 11 symbols to "no security definition"
    # (ULTRACEMCO, ASIANPAINT, BHARTIARTL and friends), which
    # are not obscure companies. Guessing at IB's spelling would
    # be guessing; reqMatchingSymbols is IB's own search, so the
    # answer comes from IB rather than from me. Hits are cached
    # to disk so the search cost is paid once.
    alt = _symbol_search(ib, market, sym, ccy)
    if alt and alt != sym:
        try:
            det = ib.reqContractDetails(Stock(alt, exch, ccy))
        except Exception:                          # noqa: BLE001
            det = None
        if det:
            c = det[0].contract
            return c, (c.primaryExchange or c.exchange or "?")
    return None, None


SYMFILE = ROOT / "data" / "ib_5m_symbols.json"


def _symbol_search(ib, market, sym, ccy):
    """IB's own symbol search, cached. Returns a symbol or None.

    c-222. Only consulted after the direct lookups fail, so a
    working path never pays for it.
    """
    key = f"{market}|{sym}"
    cache = {}
    if SYMFILE.exists():
        try:
            cache = json.loads(SYMFILE.read_text(encoding="utf-8"))
        except Exception:                          # noqa: BLE001
            cache = {}
    if key in cache:
        return cache[key]
    if not hasattr(ib, "reqMatchingSymbols"):
        return None
    # c-227: SAY WHAT THE SEARCH FOUND.
    #
    # This ran on all 13 unresolved India codes and printed
    # nothing, so "the fallback found no match" and "the
    # fallback never ran" looked identical in the console. A
    # silent fallback is an untestable one. It now reports its
    # candidates, and the report is cached with the answer so a
    # later reader can see what IB was actually offering.
    hit, seen = None, []
    try:
        for d in (ib.reqMatchingSymbols(sym) or []):
            c = d.contract
            seen.append(f"{c.symbol}/{c.currency}/{c.secType}"
                        f"@{c.primaryExchange or ''}")
            if hit is None and c.currency == ccy \
                    and c.secType == "STK":
                hit = c.symbol
    except Exception as e:                         # noqa: BLE001
        seen.append(f"search failed: {type(e).__name__}")
    if hit:
        print(f" [search -> {hit}]", end="", flush=True)
    else:
        print(f" [search found {len(seen)}: "
              f"{', '.join(seen[:4]) or 'nothing'}]",
              end="", flush=True)
    cache[key] = hit
    cache[key + "|seen"] = seen[:8]
    try:
        SYMFILE.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    except Exception:                              # noqa: BLE001
        pass
    return hit


def _why_empty(end_date, span, err):
    """One line saying why a chunk came back with nothing.

    c-197: 160 characters of IB's message, not 60. IB sends
    "Historical Market Data Service error message:HMDS query
    returned no data: 4966@TPEX Trades" — the diagnostic half
    sits AFTER the boilerplate half, so a 60-character
    truncation stored the part that says nothing and discarded
    the part that names the venue. The audit then classified
    those windows as "unexplained" when the reason was in the
    message IB had already sent.
    """
    return (f"{end_date.isoformat()} ({span}D): "
            + (f"IB {err[0]} {err[1][:160]}" if err
               else "empty, IB reported no error"))


def _chunks(a, b, span_days=None):
    """The (end_date, duration) asks that tile [a, b] backwards.

    Split out of the fetch loop so `tune` can measure the chunk
    size and the fetcher can fire the whole tiling at once
    instead of one request at a time.
    """
    span_days = span_days or _chunk_days()
    out, cur = [], b
    while cur > a:
        d = max(1, min(span_days, (cur - a).days))
        out.append((cur, d))
        cur = cur - dt.timedelta(days=d)
    return out


MIN_SPLIT = 8          # days; below this a retry is not worth it


def _split_retry(ib, con, end_date, span, depth=0):
    """An empty chunk is not proof the period is empty.

    c-206 — A REGRESSION I CAUSED, and it destroyed real data.

    When `tune` raised the chunk size from 30 days to 120, a
    whole window became ONE request. That is faster and it is
    also all-or-nothing: IB does not truncate a request that
    reaches past its floor, it returns NOTHING. So an 80-day ask
    ending 2023-07-15, reaching back to Taiwan's 2023-04-26
    edge, came back empty — where the old 30-day walk had
    returned two full chunks (2,695 bars) and lost only the
    third.

    3443 and 3231 went from 2,695 bars to zero.

    Per-symbol coverage is the reason the big ask fails at all:
    the venue floor was measured on 1301/2317/2330, and c-204
    already proved with Australia's CSL that individual names
    can start later than their venue. A window clamped to the
    venue edge can therefore sit before a particular stock's
    own first bar.

    So an empty chunk is now HALVED and retried, recursively,
    down to about a week. Whatever part of the span exists comes
    back; only the part that genuinely does not is lost. Costs
    extra requests exactly where data is scarce and nothing
    where it is not.
    """
    bars, err = _bars(ib, con, end_date, days=span)
    if bars or span <= MIN_SPLIT or depth >= 5:
        return bars, err
    half = max(1, span // 2)
    newer, e1 = _split_retry(ib, con, end_date, half, depth + 1)
    older, e2 = _split_retry(
        ib, con, end_date - dt.timedelta(days=half),
        span - half, depth + 1)
    got = list(newer or []) + list(older or [])
    return got, (None if got else (e1 or e2 or err))


def _bars_many(ib, con, chunks):
    """Every chunk of one window, CONCURRENTLY.

    c-197. IB's own docs: "The maximum number of simultaneous
    open historical data requests from the API is 50. In
    practice, it will probably be more efficient to have a much
    smaller number of requests pending at a time."

    So concurrency is supported and expected — I had been
    issuing one request, sleeping, issuing the next. A window is
    ~4 chunks; firing them together collapses four serial waits
    into one. Combined with the corrected pacing this is where
    the bulk of the speedup comes from.

    Concurrency is MEASURED by `tune`, not assumed, and falls
    back to the old sequential path on any failure so a slow
    harvest is always still a working harvest.
    """
    import asyncio
    n = _concurrency()
    if n <= 1:
        return [_bars(ib, con, e, days=d) for e, d in chunks]

    async def _one(sem, end_date, days):
        async with sem:
            before = len(_ERRORS)
            exc = None
            try:
                b = await ib.reqHistoricalDataAsync(
                    con, endDateTime=end_date.strftime("%Y%m%d")
                    + "-23:59:59", durationStr=f"{days} D",
                    barSizeSetting="5 mins", whatToShow="TRADES",
                    useRTH=True, formatDate=1)
            except Exception as e:                 # noqa: BLE001
                b, exc = [], type(e).__name__
            # c-222: REPORT THE EXCEPTION. IB's "query cancelled"
            # (162) arrives asynchronously and often lands after
            # this line, so `err` was None and _why_empty wrote
            # "empty, IB reported no error" — which is how eight
            # Korean timeouts were filed as `unexplained` when
            # the word "Timeout" was on the previous line of the
            # console. The local exception is evidence too.
            err = (_ERRORS[-1] if len(_ERRORS) > before
                   else (0, f"local {exc}") if exc else None)
            await asyncio.sleep(PACE)
            return list(b or []), err

    async def _all():
        sem = asyncio.Semaphore(n)
        return await asyncio.gather(
            *[_one(sem, e, d) for e, d in chunks])

    try:
        return ib.run(_all())
    except Exception as e:                         # noqa: BLE001
        print(f"    (concurrent fetch failed — {type(e).__name__}"
              f", falling back to sequential)", flush=True)
        return [_bars(ib, con, e, days=d) for e, d in chunks]


def _bars(ib, con, end_date, days=None):
    days = days or _chunk_days()
    before = len(_ERRORS)
    exc = None
    try:
        b = ib.reqHistoricalData(
            con, endDateTime=end_date.strftime("%Y%m%d")
            + "-23:59:59", durationStr=f"{days} D",
            barSizeSetting="5 mins", whatToShow="TRADES",
            useRTH=True, formatDate=1)
    except Exception as e:                         # noqa: BLE001
        b, exc = [], type(e).__name__
    time.sleep(PACE)
    err = (_ERRORS[-1] if len(_ERRORS) > before
           else (0, f"local {exc}") if exc else None)
    return b, err


def _bdays_before(d, n):
    """n business days before d (holidays not modelled)."""
    k = 0
    while k < n:
        d -= dt.timedelta(days=1)
        if d.weekday() < 5:
            k += 1
    return d


def calendar(include_estimated=True):
    """{rev: (ann, eff, provenance)} collapsed to (ann, eff).

    c-199. Bill asked to fetch back to each market's 5m edge and
    to treat pre-2015 windows the same as the rest. Doing that
    exposed something my question to him did not say, because I
    did not know it at the time:

      msci_tw_events.json holds 34 reviews and ALL of them are
      2015 or later. There are no pre-2015 announcement dates on
      file at all.

    So pre-2015 is not "a registry date we chose to distrust",
    it is TWO estimates stacked:
      eff  = msci_changes_db.eff_date_est — month-end, itself an
             estimate (the column name says so)
      ann  = eff - 13 business days — the c-186 measured median
             gap, replacing the old 10-day estimator that ran 3
             sessions late

    That is worse than the one-estimate picture I described.
    The harvest still treats these windows equally, as asked —
    no filtering — but provenance is recorded on every window so
    the fact survives contact with the analysis. Recording it
    costs nothing; losing it cannot be undone.
    """
    ev = json.loads((ROOT / "data" / "msci_tw_events.json")
                    .read_text(encoding="utf-8"))
    cal = {r: (v["ann"], v["eff"], "registry")
           for r, v in ev.items()
           if v.get("ann") and v.get("eff")}
    if not include_estimated:
        return cal
    import pandas as pd
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    for rev, grp in df[df.eff_date_est.notna()].groupby("review"):
        if rev in cal:
            continue
        eff = str(grp.eff_date_est.iloc[0])[:10]
        try:
            e = dt.date.fromisoformat(eff)
        except ValueError:
            continue
        cal[rev] = (_bdays_before(e, 13).isoformat(), eff,
                    "ESTIMATED — eff from eff_date_est "
                    "(month-end), ann from eff-13 business days")
    return cal


def review_src(rev):
    c = calendar().get(rev)
    return c[2] if c else "unknown"


def movers(market):
    """Every mover with a ticker, at any date the calendar
    covers. c-199: the year>=2015 filter is gone — jobs() now
    drops what falls before each market's MEASURED 5m edge,
    which is the real constraint."""
    import pandas as pd
    cal = calendar()
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    g = df[(df.market == market) & (df.ticker != "")]
    return [(r.review, str(r.ticker).strip(), r.action,
             r.security) for _, r in g.iterrows()
            if r.review in cal]


# Probe symbol per venue. c-197: Taiwan appears TWICE, because
# TWSE and TPEx are not the same animal. My first reading of the
# fetch output was that TPEx has NO history — 4966 and 3293
# resolve on TPEX and answer "HMDS query returned no data". The
# completed run corrected me: 6223 returned a full 3,834-bar
# window on TPEX and 5274 returned 1,890 bars from 2025-11-19.
# TPEx has history, it just STARTS MUCH LATER. Bisecting it
# separately is the only way to find out where.
# ASPEED (5274) is the probe because it is the name that proved
# TPEx data exists at all.
PROBE = {
    "Taiwan":      ("TWSE", "TWD", "2330"),      # TSMC
    # c-199: Bill asked to TEST Japan before paying for the TSE
    # feed. The c-190 probe returned Error 162 "No market data
    # permissions for TSEJ STK" nine times, which I read as an
    # entitlement wall — but 162 is also what IB sends when a
    # request reaches past its history floor (proved on Taiwan
    # in c-195). The two look identical in the log and mean
    # opposite things for a JPY 3,000 decision. `edges Japan`
    # separates them: no bars AT THE PRESENT DAY is entitlement,
    # bars now but not earlier is a boundary.
    "Japan":       ("TSEJ", "JPY", "7203"),      # Toyota
    "Taiwan_TPEx": ("TPEX", "TWD", "5274"),      # ASPEED
    "HongKong":    ("SEHK", "HKD", "700"),
    "Korea":       ("KRX", "KRW", "005930"),
    "Singapore":   ("SGX", "SGD", "D05"),
    "Australia":   ("ASX", "AUD", "BHP"),
    "India":       ("NSE", "INR", "RELIANCE"),
    "China":       ("SEHKNTL", "CNH", "600519"),
}


def tune(seconds=(8.0, 5.0, 3.0, 2.0, 1.5, 1.0, 0.5, 0.25,
                  0.1)):
    """MEASURE the soft pacing limit instead of guessing it.

    Walks the interval down, firing 12 real 5-minute requests at
    each step against one liquid name, and watches for the three
    things IB does when pushed too hard: a pacing-violation
    error, an empty response where the previous identical
    request succeeded, or a dropped API connection.

    The fastest interval that survives a full clean pass, times
    a 1.5x safety margin, is written to data/ib_pace.json and
    picked up by every later run. If nothing fails, the floor of
    the ladder is recorded with a note saying the true limit is
    below what was tested.

    ~90 requests, a few minutes. It pays for itself on the first
    market.
    """
    ib = _connect()
    con, label = _probe_con(ib, "Taiwan")
    if not con:
        print("Taiwan probe contract did not resolve")
        ib.disconnect()
        return
    print(f"tuning against {label}\n")
    end = dt.date.today() - dt.timedelta(days=10)
    safe, log = None, []
    for gap in seconds:
        print(f"  {gap:>4.1f}s between requests ... ", end="",
              flush=True)
        ok, bad, t0 = 0, None, time.time()
        for k in range(12):
            # step the end date so no two requests are IDENTICAL
            # — repeating the same request inside 15 s is its own
            # violation and would confound the measurement.
            e = end - dt.timedelta(days=3 * k)
            before = len(_ERRORS)
            try:
                b = ib.reqHistoricalData(
                    con, endDateTime=e.strftime("%Y%m%d")
                    + "-23:59:59", durationStr="5 D",
                    barSizeSetting="5 mins", whatToShow="TRADES",
                    useRTH=True, formatDate=1)
            except Exception as ex:                # noqa: BLE001
                bad = f"raised {type(ex).__name__}"
                break
            err = _ERRORS[-1] if len(_ERRORS) > before else None
            if err and "pacing" in str(err[1]).lower():
                bad = f"PACING VIOLATION: {err[1][:60]}"
                break
            if not ib.isConnected():
                bad = "API DISCONNECTED"
                break
            if b:
                ok += 1
            time.sleep(gap)
        el = time.time() - t0
        if bad:
            print(f"FAILED after {ok} — {bad}")
            log.append({"gap": gap, "clean": False, "note": bad})
            break
        print(f"clean, {ok}/12 returned bars, {el:.0f}s")
        log.append({"gap": gap, "clean": True, "ok": ok})
        safe = gap
    if safe is None:
        print("\nnothing passed — leaving the default alone")
        ib.disconnect()
        return
    rec = round(safe * 1.5, 2)
    hit_floor = safe == seconds[-1]

    # ---- 1b. SOAK, because 12 requests is not a harvest ---
    #
    # The first run of this bottomed out: 12/12 clean at every
    # step down to 0.5 s, i.e. the ladder never found IB's
    # limit. That is a real result, but a 12-request burst is
    # not the thing IB throttles — its warning is about
    # "requesting large amounts of historical data", and a
    # Taiwan harvest is ~200 requests. A rate that survives 12
    # can still degrade at 100. So the winner is now confirmed
    # over a longer run before it is written down.
    print(f"\n  soak — 40 requests at {safe}s to confirm the "
          f"rate holds at length")
    soak_ok, soak_bad = 0, None
    for k in range(40):
        e = end - dt.timedelta(days=2 * k + 1)
        before = len(_ERRORS)
        try:
            b = ib.reqHistoricalData(
                con, endDateTime=e.strftime("%Y%m%d")
                + "-23:59:59", durationStr="5 D",
                barSizeSetting="5 mins", whatToShow="TRADES",
                useRTH=True, formatDate=1)
        except Exception as ex:                    # noqa: BLE001
            soak_bad = f"raised {type(ex).__name__}"
            break
        err = _ERRORS[-1] if len(_ERRORS) > before else None
        if err and "pacing" in str(err[1]).lower():
            soak_bad = f"PACING at request {k + 1}"
            break
        if not ib.isConnected():
            soak_bad = f"DISCONNECTED at request {k + 1}"
            break
        if b:
            soak_ok += 1
        time.sleep(safe)
    if soak_bad:
        # back off two rungs and say so, rather than recording a
        # rate that only looks safe in short bursts
        idx = seconds.index(safe)
        safe = seconds[max(0, idx - 2)]
        print(f"    {soak_bad} -> backing off to {safe}s")
    else:
        print(f"    clean, {soak_ok}/40 returned bars")

    # ---- 2. how many DAYS per request? -------------------
    # Every doubling here halves the request count for the whole
    # APAC harvest, so it is worth more than the interval.
    print("\n  chunk size — days of 5m bars per request")
    best_chunk, chunk_log = CHUNK_DEFAULT, []
    for days in (30, 45, 60, 90, 120):
        b, err = _bars(ib, con, end, days=days)
        n = len(b or [])
        chunk_log.append({"days": days, "bars": n,
                          "err": str(err)[:90] if err else None})
        print(f"    {days:>4} D -> {n:>5} bars"
              f"{'' if n else '   ' + str(err)[:70]}")
        if n:
            best_chunk = days
        else:
            break

    # ---- 3. how many requests AT ONCE? -------------------
    # IB documents a ceiling of 50 simultaneous open historical
    # requests and recommends "a much smaller number". A window
    # is ~4 chunks, so even 4-way concurrency collapses a
    # window's four serial waits into one.
    print("\n  concurrency — simultaneous requests")
    best_conc, conc_log = 1, []
    try:
        import asyncio

        def _try(k):
            async def _one(sem, i):
                async with sem:
                    e = end - dt.timedelta(days=7 * i)
                    r = await ib.reqHistoricalDataAsync(
                        con, endDateTime=e.strftime("%Y%m%d")
                        + "-23:59:59", durationStr="5 D",
                        barSizeSetting="5 mins",
                        whatToShow="TRADES", useRTH=True,
                        formatDate=1)
                    return len(r or [])

            async def _all():
                sem = asyncio.Semaphore(k)
                return await asyncio.gather(
                    *[_one(sem, i) for i in range(k)])
            return ib.run(_all())

        for k in (2, 4, 8):
            before = len(_ERRORS)
            t1 = time.time()
            got = _try(k)
            bad_err = [e for e in _ERRORS[before:]
                       if "pacing" in str(e[1]).lower()]
            good = sum(1 for g in got if g)
            conc_log.append({"n": k, "returned": good,
                             "seconds": round(time.time() - t1, 1),
                             "pacing_error": bool(bad_err)})
            print(f"    {k:>2} at once -> {good}/{k} returned, "
                  f"{time.time() - t1:.1f}s"
                  f"{'  PACING VIOLATION' if bad_err else ''}")
            if bad_err or good < k or not ib.isConnected():
                break
            best_conc = k
            time.sleep(safe)
    except Exception as e:                         # noqa: BLE001
        print(f"    concurrency test unavailable "
              f"({type(e).__name__}) — staying sequential")
    ib.disconnect()

    PACE_FILE.write_text(json.dumps({
        "measured": dt.date.today().isoformat(),
        "fastest_clean_seconds": safe,
        "safe_seconds": rec,
        "chunk_days": best_chunk,
        "concurrency": best_conc,
        "margin": "1.5x the fastest clean interval",
        "note": ("the ladder bottomed out without failing, so "
                 "the true limit is FASTER than anything tested "
                 "— this is a floor on our speed, not IB's"
                 if hit_floor else
                 "the next step down failed; this is a measured "
                 "boundary"),
        "ladder": log,
        "chunk_ladder": chunk_log,
        "concurrency_ladder": conc_log,
        "rule": "5-minute bars are above IB's 30-second "
                "threshold, so the hard 60-per-10-minutes cap "
                "does not apply — only an unpublished soft "
                "throttle, which is what this measures. IB "
                "documents 50 simultaneous open historical "
                "requests as the ceiling.",
    }, indent=1), encoding="utf-8")

    old_r, old_p = 198, 11.0
    new_r = old_r * CHUNK_DEFAULT / best_chunk
    print(f"\n  interval   {old_p}s -> {rec}s")
    print(f"  chunk      {CHUNK_DEFAULT}d -> {best_chunk}d "
          f"({old_r} requests -> {new_r:.0f})")
    print(f"  concurrent 1 -> {best_conc}")
    print(f"  Taiwan: {old_r * old_p / 60:.0f} min -> "
          f"{new_r * rec / best_conc / 60:.1f} min")
    print(f"-> {PACE_FILE.name}")


def _probe_con(ib, venue):
    from ib_async import Stock
    exch, ccy, sym = PROBE[venue]
    for ex in (exch, ""):
        try:
            det = ib.reqContractDetails(Stock(sym, ex, ccy))
        except Exception:                          # noqa: BLE001
            det = None
        if det:
            c = det[0].contract
            return c, f"{sym}@{c.primaryExchange or c.exchange}"
        time.sleep(0.4)
    return None, None


def edges(markets=None):
    """Bisect each venue's 5m edge. Cheap, and it decides
    everything downstream.

    c-197: same progress reporting as `fetch`. A bisection is
    ~12 requests at 11 s each, so a single market takes over two
    minutes during which the old version printed nothing at all.
    Every probe now announces the date it is testing and what
    came back, and the bracket narrows visibly.
    """
    venues = markets or list(PROBE)
    n_req = len(venues) * 14
    print(f"  {len(venues)} venues, up to ~{n_req} requests, "
          f"~{n_req * PACE / 60:.0f} min at {PACE}s each.")
    print("  Bisection: each line halves the unknown range. "
          "'DATA' = 5m bars exist on or before that date.\n",
          flush=True)
    t0 = time.time()
    ib = _connect()
    res = json.loads(EDGES.read_text(encoding="utf-8")) if EDGES.exists() else {}
    for vi, m in enumerate(venues, 1):
        print(f"\n[{vi}/{len(venues)}] {m}", flush=True)
        con, label = _probe_con(ib, m)
        if not con:
            print("    no contract — IB does not carry this "
                  "symbol on this venue")
            res[m] = {"edge": None,
                      "note": "contract did not resolve"}
            continue
        print(f"    contract {label}", flush=True)
        hi = dt.date.today() - dt.timedelta(days=7)
        # c-201: search floor 2010 -> 2004. Five markets came
        # back "reaches at least 2010-01-01", which is not a
        # measurement of IB — it is a measurement of where we
        # stopped looking. That artificial floor then became a
        # real one: jobs() drops any review announced before the
        # recorded edge, so 2006-2009 movers were being excluded
        # by our own search parameter while Bill had explicitly
        # asked to fetch back to whatever date is available.
        # At the measured pacing two extra bisection steps cost
        # under a second.
        lo = dt.date(2004, 1, 1)
        b, err = _bars(ib, con, hi, days=5)
        print(f"    {hi}  {'DATA' if b else 'none'}"
              f"{'' if b else '   ' + str(err)[:70]}", flush=True)
        if not b:
            # THE DISTINCTION THAT MATTERS. A resolvable contract
            # with no bars TODAY is not a short history — it is
            # a venue IB does not serve history for at all. TPEx
            # is expected to land here.
            res[m] = {"edge": None, "last_error": str(err),
                      "note": "contract resolves but NO 5m data "
                              "even at the present day — this "
                              "venue cannot support the study",
                      "measured": dt.date.today().isoformat()}
            print("    -> NO 5m HISTORY ON THIS VENUE AT ALL",
                  flush=True)
            EDGES.write_text(json.dumps(res, indent=1),
                             encoding="utf-8")
            continue
        b, _ = _bars(ib, con, lo, days=5)
        print(f"    {lo}  {'DATA' if b else 'none'}", flush=True)
        if b:
            res[m] = {"edge": lo.isoformat(),
                      "note": "reaches the 2010 search floor"}
            print(f"    -> reaches at least {lo}", flush=True)
            EDGES.write_text(json.dumps(res, indent=1),
                             encoding="utf-8")
            continue
        n = 0
        while (hi - lo).days > 5:
            mid = lo + (hi - lo) / 2
            b, _ = _bars(ib, con, mid, days=5)
            if b:
                hi = mid
            else:
                lo = mid
            n += 1
            el = (time.time() - t0) / 60
            print(f"    {mid}  {'DATA' if b else 'none'}"
                  f"   bracket {lo} .. {hi} "
                  f"({(hi - lo).days}d)  [{el:.0f}m elapsed]",
                  flush=True)
        res[m] = {"edge": hi.isoformat(),
                  "bracket": [lo.isoformat(), hi.isoformat()],
                  "requests": n,
                  "measured": dt.date.today().isoformat()}
        print(f"    -> EDGE {lo} .. {hi}  ({n} requests)",
              flush=True)
        EDGES.write_text(json.dumps(res, indent=1),
                         encoding="utf-8")
    ib.disconnect()
    print(f"\n-> {EDGES.name}")
    return res


def _board(market, code):
    """Which venue a Taiwan code trades on, from our own
    universe file. Other markets return None."""
    if market != "Taiwan":
        return None
    p = ROOT / "data" / "tw_mieu_universe.json"
    if not p.exists():
        return None
    try:
        return ((json.loads(p.read_text(encoding="utf-8"))["universe"]
                 .get(str(code)) or {}).get("mkt"))
    except Exception:                              # noqa: BLE001
        return None


def _edge_for_code(market, code):
    """c-197b: THE EDGE IS PER VENUE, NOT PER MARKET.

    I told Bill "IB carries TPEx contracts but serves no history
    for that venue — not retryable". The completed Taiwan run
    says otherwise:

        6223 MPI      May26  TPEX  3,834 bars   full window
        5274 ASPEED   Nov25  TPEX  1,890 bars   starts 2025-11-19
        3293 IGS      Nov24  TPEX      0 bars
        4966 Parade   May24  TPEX      0 bars

    That is not "no data", that is a LATER EDGE. TWSE reaches
    back to 2023-04-27; TPEx appears to begin somewhere around
    late 2025. I generalised from two failures and missed the
    two successes sitting in the same file.

    So a TPEx window is clamped to the TPEx edge once `edges
    Taiwan_TPEx` has measured it. Until then TPEx falls back to
    the market edge, which is too generous and simply produces
    empty chunks — the honest failure, not a silent one.
    """
    if _board(market, code) == "tpex":
        e = _boundary_edge("Taiwan_TPEx") or _edge_for(
            "Taiwan_TPEx")
        if e:
            return e
    # c-229: KOSDAQ IS MEASURED NOW — 2026-02-02, all three
    # probes agreeing. That is six months of history, so every
    # KOSDAQ review window in a 2015-2026 study is outside IB's
    # coverage and jobs() should stop asking for them rather
    # than fetch 28 windows and stamp each one an absence.
    #
    # Wiring this up is the point. c-224 added the venue, c-227
    # added the probe symbols, Bill measured it — and until this
    # line the answer sat in a JSON file that nothing read. A
    # measurement no code consumes is a note, not a control.
    if market == "Korea" and _probe_venue(market, code) \
            == "KRX_KOSDAQ":
        e = _boundary_edge("Korea_KOSDAQ")
        if e:
            return e
    if market == "China":
        # c-204: Shenzhen's floor is 2016-12-05, Shanghai's is
        # 2014-11-14 and the Hong Kong lines reach 2004. Three
        # venues, three floors — using one would silently drop
        # two years of Shenzhen events or waste requests on
        # Shanghai periods that do not exist.
        ex = _china_venue(code)[0]
        e = _boundary_edge({"SEHKSZSE": "China_SZ",
                            "SEHKNTL": "China_SH",
                            "CHINEXT": "China_ChiNext",
                            "SEHKSTAR": "China_STAR",
                            "SEHK": "HongKong"}.get(ex))
        if e:
            return e
    return _edge_for(market)


# c-204: the boundary probe supersedes `edges`. It uses three
# symbols per venue instead of one, walks back to 1998 instead
# of stopping at a hard-coded floor, and confirms each answer
# from both sides. Where the two disagree the boundary wins, and
# it disagrees usefully: `edges` reported "reaches at least
# 2010-01-01" for four markets, which was our search limit, and
# the boundary put Japan at 2004-03-12, Korea 2004-05-17,
# Australia 2004-05-06 and India 2008-06-11.
BOUNDARY = ROOT / "data" / "ib_5m_boundary.json"

# Venue name in the boundary file -> market name here. China is
# split because Shanghai and Shenzhen have different floors
# (2014-11-14 vs 2016-12-05), handled in _edge_for_code.
_BMAP = {"Taiwan": "Taiwan", "Japan": "Japan",
         "HongKong": "HongKong", "Korea": "Korea",
         "Singapore": "Singapore", "Australia": "Australia",
         "India": "India", "China": "China_SH"}


def _boundary_edge(venue):
    if not BOUNDARY.exists():
        return None
    try:
        r = json.loads(BOUNDARY.read_text(encoding="utf-8")).get(venue) or {}
    except Exception:                              # noqa: BLE001
        return None
    # a venue we could not bracket has no usable floor; saying
    # so is better than falling back to a worse measurement
    if r.get("edge_is_a_floor_we_hit"):
        return None
    return r.get("edge")


def _edge_for(market):
    e = _boundary_edge(_BMAP.get(market, market))
    if e:
        return e
    if EDGES.exists():
        e = json.loads(EDGES.read_text(encoding="utf-8")).get(market)
        if e:
            return e["edge"]
    return KNOWN_EDGE.get(market)


def jobs(market):
    """(review, code, action, name, start, end) after the edge."""
    cal = calendar()
    out = []
    for rev, tick, act, name in movers(market):
        # c-197b: per-VENUE edge. A TPEx name and a TWSE name in
        # the same review do not share a history floor.
        edge = _edge_for_code(market, tick)
        ann, eff, _src = cal[rev]
        # c-222: the policy floor. Applied to the ANNOUNCEMENT,
        # not to the window start — a review announced in
        # January 2015 keeps its full 45-day pre-window running
        # back into December 2014, because the event is what has
        # to be inside the study period, not the run-up.
        if SINCE and ann < SINCE:
            continue
        start = (dt.date.fromisoformat(ann)
                 - dt.timedelta(days=PRE_ANN_DAYS))
        end = (dt.date.fromisoformat(eff)
               + dt.timedelta(days=POST_EFF_DAYS))
        if edge and start.isoformat() < edge:
            # the window opens before IB has anything; keep it
            # only if the EVENT itself is inside coverage
            if ann < edge:
                continue
            start = dt.date.fromisoformat(edge)
        out.append((rev, tick, act, name, start, end))
    return out


def pre_days(rev, start):
    """Actual pre-announcement span. c-193b: clamping the start
    to IB's edge silently shortens the pre-window — Taiwan's
    May-2023 review gets 14 days instead of 45 because the edge
    (2023-04-27) lands inside it. A short pre-window is not
    wrong, but it is NOT comparable to a full one, so it is
    labelled rather than left to be discovered later."""
    cal = calendar()
    return (dt.date.fromisoformat(cal[rev][0]) - start).days


def _jobs_unused(market):
    out = []
    return out


def plan(markets=None):
    tot = 0
    conc = max(1, _concurrency())
    done = 0
    print(f"{'market':11} {'5m edge':12} {'src':9} {'events':>7} "
          f"{'have':>6} {'requests':>9} {'minutes':>8}")
    for m in (markets or list(EXCH)):
        e = _edge_for(m) or "UNMEASURED"
        # c-204: say WHERE the floor came from. "boundary" is
        # the 3-symbol, confirmed, walked-to-1998 measurement;
        # "edges" is the older single-symbol bisection that
        # stopped at a hard-coded 2010 and is therefore a
        # ceiling on what we looked for, not on what IB has.
        src = ("boundary" if _boundary_edge(_BMAP.get(m, m))
               else "EDGES?")
        js = jobs(m) if _edge_for(m) else []
        f = DIR / f"{m}.json"
        got = (len(json.loads(f.read_text(encoding="utf-8"))["windows"])
               if f.exists() else 0)
        done += got
        reqs = sum(len(_chunks(a, b)) for *_, a, b in js)
        tot += reqs
        print(f"{m:11} {e:12} {src:9} {len(js):>7} {got:>6} "
              f"{reqs:>9} {reqs * PACE / conc / 60:>8.1f}")
    print(f"{'TOTAL':11} {'':12} {'':9} {'':>7} {done:>6} "
          f"{tot:>9} {tot * PACE / conc / 60:>8.1f}")
    if any(not _boundary_edge(_BMAP.get(m, m))
           for m in (markets or list(EXCH))):
        print("  EDGES? = floor from the OLD single-symbol "
              "bisection, which stopped at a hard-coded 2010. "
              "Re-run ib_5m_boundary.py for those.")
    print(f"  at {PACE}s apart, {_chunk_days()}d chunks, "
          f"{conc} concurrent — pacing time only, IB's own "
          f"response time is on top")
    # c-222: the honest estimate, from windows already fetched.
    secs = []
    for p in DIR.glob("*.json"):
        try:
            for v in json.loads(p.read_text(encoding="utf-8"))["windows"].values():
                if v.get("fetch_secs"):
                    secs.append(v["fetch_secs"])
        except Exception:                          # noqa: BLE001
            pass
    # one read per market — the harvest files run to tens of MB,
    # so re-reading inside the loop would take longer than the
    # thing it is estimating
    todo_n = 0
    for m in (markets or list(EXCH)):
        p = DIR / f"{m}.json"
        have = set()
        if p.exists():
            try:
                have = {k for k, v
                        in json.loads(p.read_text(encoding="utf-8"))
                        ["windows"].items() if v.get("px")}
            except Exception:                      # noqa: BLE001
                have = set()
        todo_n += sum(1 for rev, tick, *_ in
                      (jobs(m) if _edge_for(m) else [])
                      if f"{rev}|{tick}" not in have)
    if secs:
        med = sorted(secs)[len(secs) // 2]
        print(f"  MEASURED {med:.0f}s per window over "
              f"{len(secs)} already fetched -> {todo_n} to go "
              f"= {todo_n * med / 3600:.1f} hours")
    else:
        print(f"  {todo_n} windows still to fetch. No timing "
              f"measured yet — run one market to get a real "
              f"per-window figure.")
    if SINCE:
        print(f"  left boundary capped at {SINCE} (c-222, "
              f"policy — measured floors are unchanged)")
    # c-225: name the venues whose floor is INHERITED rather
    # than measured, and how many windows ride on the guess.
    unmeasured = {}
    for m in (markets or list(EXCH)):
        for rev, tick, *_ in (jobs(m) if _edge_for(m) else []):
            ven = (_china_venue(str(tick))[0] if m == "China"
                   else None)
            key = {"CHINEXT": "China_ChiNext",
                   "SEHKSTAR": "China_STAR"}.get(ven)
            if key and not _boundary_edge(key):
                unmeasured[key] = unmeasured.get(key, 0) + 1
    for k, n in sorted(unmeasured.items()):
        print(f"  ! {k}: {n} windows on an INHERITED floor. "
              f"Run `py scripts\\ib_5m_boundary.py {k}` — an "
              f"inherited floor that is too early turns into "
              f"false `venue_no_history` records.")
    if any(not _edge_for(m) for m in (markets or list(EXCH))):
        print("\n! some markets UNMEASURED — run `edges` first, "
              "or the plan is fiction")
    return tot


# c-224: derived from the console of Bill's c-222 run, NOT
# measured by this code. His ETA lines give elapsed/i directly:
# Hong Kong ~12 s/window, Korea ~17, India ~22, Australia ~30.
# Quoted as a range because that is what the evidence supports;
# `fetch_secs` replaces it with a real median after one market.
LOG_SECS_PER_WINDOW = (12, 30)


# Korean codes our ticker map suffixes ".KQ" that are actually
# KOSPI listings. Both returned full 5m history while every
# genuinely KOSDAQ name returned none — the tell that made the
# mislabelling visible (c-227).
KOSPI_MISLABELLED = {"011200",   # HMM
                     "011210"}   # Hyundai Wia


def _probe_venue(market, tick):
    """The ENTITLEMENT a code sits behind, not the exchange code.

    c-224. IB names one exchange for Korea (KRX) and two boards
    live behind it — KOSPI is entitled on Bill's account and
    KOSDAQ measurably is not. A probe keyed on the exchange
    would test KOSPI, report Korea ready, and then lose every
    KOSDAQ window in the real run. Taiwan's TWSE/TPEx split is
    the same shape.
    """
    t = str(tick).upper()
    if market == "China":
        return _china_venue(t)[0]
    if market == "Korea":
        # c-227: the .KQ field is 17/19 right, not 19/19. HMM
        # and Hyundai Wia carry .KQ in our ticker map and are
        # KOSPI companies — which is why the harvest showed "two
        # KOSDAQ windows with bars" and I nearly read that as
        # KOSDAQ working. Named here so the next reader does not
        # repeat it.
        if t.split(".")[0] in KOSPI_MISLABELLED:
            return "KRX_KOSPI"
        return "KRX_KOSDAQ" if t.endswith(".KQ") else "KRX_KOSPI"
    if market == "Taiwan" and _board("Taiwan", t.split(".")[0]) \
            == "tpex":
        return "TPEX"
    return EXCH[market][0]


def ready(markets=None):
    """PRE-FLIGHT. One contract and one small bar request per
    venue, before committing ten hours to a full harvest.

    c-224. Bill asked whether we are ready to collect the rest.
    The plan table cannot answer that: it counts events and
    edges, both of which come from our own files. What it does
    NOT know is whether this ACCOUNT can see the data —
    Shanghai and Shenzhen reach IB only through Stock Connect,
    Japan needs the TSE subscription, and Korea has already
    shown that KOSDAQ is a separate entitlement. Those three
    cover 1,554 of the 1,770 remaining windows.

    The failure mode this exists to prevent is the one we hit
    twice already: a long run that returns "No market data
    permissions" for a thousand windows and writes each refusal
    into the file as though it were a measured absence.

    ~15 requests, under a minute, and it never writes anything.
    """
    mkts = markets or list(EXCH)
    cal = calendar()
    # one probe per VENUE, not per market — China's four venues
    # are four different entitlements wearing one market name.
    #
    # c-225: THREE codes per venue, not one. The first run
    # reported "India / NSE: NO CONTRACT" off a single symbol,
    # ADANIENSOL — a recent listing that IB may simply spell
    # differently — while India's own harvest file already holds
    # 50 windows of real NSE bars. A one-symbol probe cannot
    # tell "this venue is closed to us" from "this ticker is
    # odd", and that is precisely the error I made at c-197 when
    # two TPEx failures became "IB serves no TPEx history".
    # A venue passes if ANY of its probes returns bars.
    PER_VENUE = 3
    probes = []
    for m in mkts:
        js = jobs(m)
        if not js:
            probes.append((m, "?", None, None, "no jobs"))
            continue
        seen = {}
        for rev, tick, _a, name, start, end in sorted(
                js, key=lambda j: cal[j[0]][0], reverse=True):
            ven = _probe_venue(m, str(tick))
            if seen.get(ven, 0) >= PER_VENUE:
                continue
            seen[ven] = seen.get(ven, 0) + 1
            probes.append((m, ven, str(tick), end, name))
    print(f"pre-flight: {len(probes)} venue probes "
          f"(no data is written)\n")
    ib = _connect()
    verdict = []
    for m, ven, tick, end, name in probes:
        if tick is None:
            print(f"  {m:10} {ven:10} SKIPPED — {name}")
            continue
        print(f"  {m:10} {ven:10} {tick:12} ...",
              end="", flush=True)
        before = len(_ERRORS)
        con, got_ven = _con(ib, m, tick)
        if not con:
            err = (_ERRORS[-1][1] if len(_ERRORS) > before
                   else "no security definition")
            print(f" NO CONTRACT — {str(err)[:70]}")
            verdict.append((m, ven, "NO CONTRACT", err))
            continue
        bars, err = _bars(ib, con, min(end, dt.date.today()),
                          days=3)
        n = len(bars or [])
        print(f" contract ok ({got_ven}), {n} bars")
        if n:
            verdict.append((m, ven, "OK", ""))
        else:
            msg = str((err or (0, "no bars, no error"))[1])
            print(f"      ^ {msg[:110]}")
            verdict.append((m, ven, "NO BARS", msg))
    ib.disconnect()

    # c-225: the VERDICT IS PER VENUE, not per probe. One symbol
    # failing says nothing; all of a venue's symbols failing is
    # the finding.
    byven = {}
    for m, ven, st, msg in verdict:
        byven.setdefault((m, ven), []).append((st, msg))
    print("\n  VERDICT")
    blocked = []
    for (m, ven), res in byven.items():
        okn = sum(1 for st, _ in res if st == "OK")
        tag = (f"ready ({okn}/{len(res)} probes)" if okn
               else f"BLOCKED (0/{len(res)} probes)")
        print(f"    {m:10} {ven:12} {tag}")
        if not okn:
            blocked.append((m, ven, res))
    if not blocked:
        print("\n  Every venue answered with bars on at least "
              "one probe. The account sees what the plan asks "
              "for.")
    else:
        print("\n  BLOCKED VENUES — a full run would write these "
              "refusals into the harvest as if they were "
              "measured absences:")
        for m, ven, res in blocked:
            txt = " ".join(str(x[1]) for x in res).lower()
            kind = ("ENTITLEMENT — subscribe, then re-probe"
                    if "permission" in txt else
                    "SYMBOL RESOLUTION — every probe failed to "
                    "resolve, so this is our ticker map or IB's "
                    "spelling, not the venue"
                    if all(x[0] == "NO CONTRACT" for x in res)
                    else "NO HISTORY — contracts resolve and no "
                         "bars come back. MEASURE the venue edge "
                         "before reading it as absence")
            print(f"    {m} / {ven}: {kind}")
            for st, msg in res:
                print(f"        {st}: {str(msg)[:88]}")
    lo, hi = LOG_SECS_PER_WINDOW
    print(f"\n  Sizing: 1,770 windows at {lo}-{hi}s each is "
          f"{1770 * lo / 3600:.0f}-{1770 * hi / 3600:.0f} hours "
          f"(from the c-222 console; `plan` switches to a "
          f"measured median once one market has run).")
    return verdict


def fetch(market, cap=None):
    """One market. `cap` limits the run to the first N windows.

    c-258: the cap exists for the largest-first canary. It is
    NOT a sampling feature — a capped run writes the same
    records as an uncapped one and the next run resumes from
    them, so the probe is real work, not a throwaway.
    """
    edge = _edge_for(market)
    if not edge:
        print(f"{market}: 5m edge not measured. Run "
              f"`python scripts\\ib_5m_events.py edges` first.")
        return {"todo": 0, "got": 0,
                "fatal": f"{market} has no measured 5m edge"}
    DIR.mkdir(parents=True, exist_ok=True)
    f = DIR / f"{market}.json"
    d = json.loads(f.read_text(encoding="utf-8")) if f.exists() else \
        {"market": market, "edge": edge,
         "window": f"ann-{PRE_ANN_DAYS}d .. eff+{POST_EFF_DAYS}d",
         "windows": {}}
    js = jobs(market)
    cal_src = calendar()
    # c-206: a window recorded EMPTY before the split-retry
    # existed is not settled — it was written off by an
    # all-or-nothing request. Retry it unless the reason was a
    # venue with no history at all, which splitting cannot fix.
    # c-222: `timeout` and `no_contract` records are retried even
    # if split_tried was already set. A timeout is a statement
    # about one moment on one connection, and a no-contract
    # record written before the c-222 symbol fixes is a
    # statement about a bug — neither is a fact about IB's
    # archive. venue_no_history and no_permission still stand:
    # re-asking buys the same answer and costs two requests.
    _SETTLED = ("venue_no_history", "no_permission")

    def _retry(w):
        if w.get("px"):
            return False
        r = w.get("empty_reason")
        if r in _SETTLED:
            return False
        if r == "timeout":
            return True
        if str(w.get("note") or "").startswith("no contract"):
            return True
        return not w.get("split_tried")

    todo = [j for j in js
            if f"{j[0]}|{j[1]}" not in d["windows"]
            or _retry(d["windows"][f"{j[0]}|{j[1]}"])]
    if cap:
        # c-260: PREFER WINDOWS NOBODY HAS TRIED YET.
        #
        # The first probe took `todo[:5]` and drew five B-share
        # and truncated-A-share codes that IB has no contract
        # for — then declared the session broken while the same
        # market sat at 247/260 windows with bars.
        #
        # The sampling was the error. `todo` is not the market,
        # it is the RESIDUE: everything already fetched has
        # been removed, so what remains is weighted towards the
        # names that have failed before. Taking its head is
        # sampling the hardest end of the queue and calling it
        # representative.
        fresh = [j for j in todo
                 if f"{j[0]}|{j[1]}" not in d["windows"]]
        todo = (fresh or todo)[:cap]
        print(f"{market}: PROBE — {len(todo)} windows"
              + ("" if fresh else " (all previously attempted "
                                  "— no fresh ones left)"))
    print(f"{market}: {len(todo)} of {len(js)} windows to fetch")
    if not todo:
        return {"todo": 0, "got": 0, "fatal": None}
    # c-196: SAY SOMETHING WHILE IT WAITS.
    #
    # The old version printed only every 5th window, and each
    # window costs up to 3 requests at 11 s apart — so the first
    # line of output arrived ~3 minutes after the last connection
    # message. On a job this long that is indistinguishable from
    # a hang, and Bill reasonably read it as one. A harvester
    # that is deliberately slow has to prove it is alive.
    nreq = sum(len(_chunks(a, b)) for *_, a, b in todo)
    conc = _concurrency()
    est = nreq * PACE / max(1, conc)
    tuned = PACE_FILE.exists()
    print(f"  {len(todo)} windows, {nreq} requests, "
          f"~{est / 60:.0f} min "
          f"({PACE}s apart, {_chunk_days()}d chunks, "
          f"{conc} at a time)")
    if not tuned:
        print("  Pacing NOT measured on this connection — run "
              "`tune` once to go faster with evidence.")
    print("  Resumable — Ctrl-C is safe, progress is saved every "
          "5 windows.\n", flush=True)
    t0 = time.time()
    ib = _connect()
    for i, (rev, code, act, name, a, b) in enumerate(todo, 1):
        # c-222: STOP ON A FATAL ERROR.
        #
        # Bill's run hit error 438, "The application is now
        # locked". Every request after that fails the same way,
        # so the loop would have marched through the remaining
        # 152 India windows at full speed writing "no contract"
        # into each one — turning a two-minute account problem
        # into a file full of false verdicts that look exactly
        # like measured absences. He stopped it with Ctrl-C;
        # the script should not have needed him to.
        _fatal = next((c for c, _m in _ERRORS[-6:] if c in FATAL),
                      None)
        if _fatal:
            f.write_text(json.dumps(d), encoding="utf-8")
            print(f"\n  STOPPED: {FATAL[_fatal]}")
            print(f"  {i - 1} of {len(todo)} windows done this "
                  f"run, saved to {f.name}.")
            try:
                ib.disconnect()
            except Exception:                      # noqa: BLE001
                pass
            # c-226: the caller needs to know this was FATAL, not
            # finished. Without it `fetch_all` moves to the next
            # market and burns through every remaining one
            # against a locked account.
            return {"todo": len(todo), "got": _got(d, todo),
                    "fatal": FATAL[_fatal]}
        print(f"  [{i}/{len(todo)}] {code} {rev} {act} "
              f"{str(name)[:24]:24} ...", end="", flush=True)
        _tw = time.time()
        con, venue = _con(ib, market, code)
        if not con:
            d["windows"][f"{rev}|{code}"] = {
                "rev": rev, "code": code, "action": act,
                "name": name, "px": [],
                "note": "no contract on the primary code OR on a "
                        "blank-exchange search — genuinely not "
                        "carried by IB, delisted, or renamed"}
            print(" NO CONTRACT", flush=True)
            continue
        # c-195: CLAMP THE LAST CHUNK TO THE WINDOW START.
        #
        # This is the bug behind "Error 162: No market data
        # permissions for TAI STK" on 3443 and 3231 at
        # 2023-05-16, and it is NOT an entitlement problem.
        # Their window starts at Taiwan's 5m edge (2023-04-27).
        # Walking back in fixed 30-day chunks from 2023-07-15
        # lands on 2023-05-16, and a "30 D" ask from there
        # reaches 2023-04-16 — eleven days BEFORE any 5m data
        # exists. IB does not truncate such a request; it returns
        # nothing, and near the edge it dresses the refusal up as
        # a permissions error.
        #
        # The damage was silent: the loop broke on the empty
        # chunk, so 2023-04-27 .. 2023-05-16 was dropped — the
        # entire pre-announcement stretch — while pre_ann_days
        # still advertised 14 days of it.
        #
        # c-197: the tiling now lives in _chunks() and every
        # chunk is fired together. Note the early `break` is GONE
        # with it: it existed to stop walking past the edge, and
        # the clamp already guarantees that. Breaking also meant
        # one transient empty chunk discarded every older chunk
        # behind it, which is a data-loss mode we do not need.
        rows, stopped = [], None
        chunks = _chunks(a, b)
        for (cur, span), (bars, err) in zip(
                chunks, _bars_many(ib, con, chunks)):
            if not bars and span > MIN_SPLIT:
                # c-206: recover whatever part of the span does
                # exist before writing the chunk off
                bars, err = _split_retry(ib, con, cur, span)
                if bars:
                    print(f" [split-recovered {len(bars)}]",
                          end="", flush=True)
            if not bars:
                if stopped is None:
                    stopped = _why_empty(cur, span, err)
                continue
            for x in bars:
                ts = str(x.date)[:16]
                if a.isoformat() <= ts[:10] <= b.isoformat():
                    rows.append([ts, x.open, x.high, x.low,
                                 x.close, x.volume])
        seen, uniq = set(), []
        for r in sorted(rows):
            if r[0] not in seen:
                seen.add(r[0])
                uniq.append(r)
        # c-195: label the window from the BARS WE HOLD, not from
        # the dates we asked for. The old version computed
        # pre_ann_days off the requested start, so a window that
        # returned nothing before the announcement still claimed
        # 14 days of pre-announcement coverage. First bar wins.
        _first = uniq[0][0][:10] if uniq else None
        _pre_req = pre_days(rev, a)
        _pre = (pre_days(rev, dt.date.fromisoformat(_first))
                if _first else 0)
        d["windows"][f"{rev}|{code}"] = {
            "rev": rev, "code": code, "action": act,
            "name": name, "start": a.isoformat(),
            "end": b.isoformat(), "px": uniq,
            "venue": venue,
            "first_bar": _first,
            "last_bar": uniq[-1][0][:10] if uniq else None,
            "pre_ann_days_requested": _pre_req,
            "pre_ann_days": _pre,
            "pre_window": ("FULL" if _pre >= PRE_ANN_DAYS
                           else f"TRUNCATED at IB edge {edge} "
                                f"— only {_pre} days pre-ann"
                           if _pre > 0 else
                           "NO PRE-ANNOUNCEMENT DATA — this "
                           "window cannot support any before/"
                           "after test"),
            "ann": cal_src[rev][0], "eff": cal_src[rev][1],
            # c-199: pre-2015 reviews carry TWO estimates —
            # eff from eff_date_est (month-end) and ann from
            # eff-13 business days. Bill chose to treat them
            # equally in the analysis; recording where the dates
            # came from costs nothing and cannot be recovered
            # later if it is dropped now.
            "date_src": cal_src[rev][2],
            "stopped_early": stopped,
            "split_tried": True,
            # c-197: name WHY a window is empty, because the
            # three causes need different responses and they all
            # look identical in a px:[] record.
            #
            #   venue_no_history — IB resolved the contract and
            #     then served nothing. Measured on TPEx: 4966
            #     and 3293 return conIds and "HMDS query
            #     returned no data". No re-run fixes this and no
            #     subscription changes it; only another vendor
            #     does. These are a COVERAGE FACT to report, not
            #     a failure to retry.
            #   before_edge — the ask predates IB's 5m floor.
            #     Expected, already handled by the clamp.
            #   unexplained — genuinely unknown; worth a retry
            #     and worth looking at.
            # c-222: two reasons split out of the old three,
            # because both were being filed under a label that
            # implied the wrong response.
            #
            #   no_permission — "No market data permissions for
            #     KOSDAQ STK". This was landing in `before_edge`
            #     on a substring match for "permission", which
            #     says the data does not exist. It does exist;
            #     we are not entitled to it. One is a fact about
            #     IB's archive, the other is a line item on a
            #     subscription page, and only one of them can be
            #     fixed with a credit card.
            #   timeout — ib_async gave up waiting and cancelled
            #     the query. IB never said anything was wrong,
            #     so this was filed as "unexplained" when the
            #     explanation was on the first line of the log.
            #     Worth a retry; genuinely different from a
            #     venue that holds no history.
            "empty_reason": (
                None if uniq else
                "no_permission" if stopped and
                "permission" in str(stopped).lower() else
                "timeout" if stopped and
                ("timeout" in str(stopped).lower()
                 or "cancelled" in str(stopped).lower()) else
                "venue_no_history" if stopped and
                "no data" in str(stopped).lower() else
                "before_edge" if stopped and
                "before" in str(stopped).lower() else
                "unexplained"),
            # c-222: how long this window actually took. `plan`
            # estimated from PACE alone and printed "0.6 min"
            # for 1,969 windows — pacing is a floor, and IB's
            # own response time is the whole cost. Measuring it
            # turns the plan from arithmetic into evidence.
            "fetch_secs": round(time.time() - _tw, 1),
            "src": "IB 5m TRADES useRTH"}
        el = time.time() - t0
        eta = (el / i) * (len(todo) - i) / 60
        print(f" {len(uniq):>5} bars  {_first or '--'}"
              f"  pre={_pre}d  ETA {eta:.0f}m", flush=True)
        if stopped:
            print(f"        stopped early: {stopped}", flush=True)
        if i % 5 == 0 or i == len(todo):
            f.write_text(json.dumps(d), encoding="utf-8")
            done = sum(1 for v in d["windows"].values()
                       if v.get("px"))
            print(f"        [saved — {done} windows with data]",
                  flush=True)
    f.write_text(json.dumps(d), encoding="utf-8")
    ib.disconnect()
    audit(market)
    print(f"-> {f.name}")
    # c-260: the reasons for THESE windows, so a caller can tell
    # a broken session from a set of bad symbols.
    reasons = {}
    for rev, tick, *_ in todo:
        w = d["windows"].get(f"{rev}|{tick}") or {}
        if w.get("px"):
            continue
        r = w.get("empty_reason") or (
            "no_contract"
            if str(w.get("note") or "").startswith("no contract")
            else "unexplained")
        reasons[r] = reasons.get(r, 0) + 1
    return {"todo": len(todo), "got": _got(d, todo),
            "fatal": None, "reasons": reasons}


# c-260: which empty results prove the SESSION is broken, and
# which are IB answering a question definitively.
#
# "no contract" and "venue no history" are ANSWERS. IB resolved
# the request and told us the symbol does not exist, or that it
# holds no bars for that period. A session that can return
# those is a session that works — the symbols are wrong, which
# is a data problem, not a connection one.
#
# These, by contrast, mean nothing downstream will work either:
#   no_permission  the account is not entitled
#   timeout        requests are going out and nothing comes back
SYSTEMIC = {"no_permission", "timeout"}


def _session_looks_broken(r):
    """True only when the failures are systemic (c-260)."""
    if r.get("fatal"):
        return True
    if r.get("got"):
        return False
    reasons = r.get("reasons") or {}
    if not reasons:
        return bool(r.get("todo"))       # silence is systemic
    return any(k in SYSTEMIC for k in reasons)


# Below this many windows a shutout proves nothing — one or two
# names can legitimately be a delisting or a listing younger
# than its window.
CANARY_MIN = 5


def symbols(market):
    """Ask IB what it calls every code we could not resolve.

    c-227. India's unresolved list is not a list of obscure
    companies: Asian Paints, Bharti Airtel, UltraTech, Bajaj
    Finance, Federal Bank. Meanwhile HDFC Bank, Axis Bank, DLF
    and Canara Bank resolve fine on the same venue with the same
    code shape. Whatever separates the two groups, it is not
    "IB does not carry Indian equities".

    Guessing at IB's spelling would be guessing. This asks IB —
    reqContractDetails on the bare code, then reqMatchingSymbols
    — and writes what it says to data/ib_5m_symbols.json. One
    request or two per code, so the whole of India costs about
    thirty seconds.
    """
    from ib_async import Stock
    f = DIR / f"{market}.json"
    if not f.exists():
        print(f"{market}: nothing harvested yet")
        return
    W = json.loads(f.read_text(encoding="utf-8"))["windows"]
    codes = sorted({v["code"] for v in W.values()
                    if not v.get("px")
                    and str(v.get("note") or "")
                    .startswith("no contract")})
    if not codes:
        print(f"{market}: no unresolved codes")
        return
    print(f"{market}: asking IB about {len(codes)} unresolved "
          f"codes\n")
    exch, ccy = EXCH[market]
    ib = _connect()
    out = {}
    for code in codes:
        sym = _norm_sym(market, code)
        print(f"  {code:16} -> {sym:14}", end="", flush=True)
        det = None
        try:
            det = ib.reqContractDetails(Stock(sym, exch, ccy))
        except Exception:                          # noqa: BLE001
            det = None
        if det:
            c = det[0].contract
            print(f" RESOLVES NOW on {c.primaryExchange or exch}")
            out[code] = {"status": "resolves", "symbol": sym}
            continue
        found = []
        try:
            for d in (ib.reqMatchingSymbols(sym) or []):
                c = d.contract
                found.append(f"{c.symbol}/{c.currency}"
                             f"@{c.primaryExchange or '?'}")
        except Exception as e:                     # noqa: BLE001
            found = [f"search failed: {type(e).__name__}"]
        print(" no contract; IB search: "
              + (", ".join(found[:5]) if found else "NOTHING"))
        out[code] = {"status": "unresolved", "tried": sym,
                     "ib_search": found[:8]}
        time.sleep(0.4)
    ib.disconnect()
    cache = {}
    if SYMFILE.exists():
        try:
            cache = json.loads(SYMFILE.read_text(encoding="utf-8"))
        except Exception:                          # noqa: BLE001
            cache = {}
    cache[f"_report_{market}"] = out
    SYMFILE.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    n = sum(1 for v in out.values() if v["status"] == "resolves")
    print(f"\n  {n}/{len(codes)} now resolve; the rest are in "
          f"{SYMFILE.name} with what IB's own search returned.")
    if n < len(codes):
        print("  If IB's search returns NOTHING for names this "
              "liquid, the answer is about market-data or "
              "trading permissions for NSE on this account, not "
              "about spelling.")


def fetch_all(markets=None, order="largest"):
    """Every market, one command, LARGEST FIRST. (c-258)

    **Bill, c-258:** *"I want to start fetching the countries
    with largest missing events, which would be China."*

    THIS REVERSES c-226, and the reason c-226 chose smallest
    first is worth keeping in view rather than deleting. At
    that point the symbol fixes — Hong Kong's zero-padding, the
    ADR fallback, IB's symbol search — had passed unit tests
    and had never been put in front of IB. Running China's
    1,200+ windows first would have meant spending ten hours to
    discover that resolution was broken. Smallest-first made
    the cheapest run double as the test.

    That protection has since been paid for: Japan, Australia,
    Korea, Hong Kong, India, Singapore and Taiwan have all
    returned real bars, and the per-market 5m floors are
    measured. The symbol path is no longer unproven, so the
    argument for spending the first hours on one-window markets
    is gone — and China is where the missing events actually
    are.

    **The canary does not go away, it moves.** Smallest-first
    gave an implicit early warning; largest-first must make it
    explicit, or a broken session would burn the whole night on
    China before the SHUTOUT rule fired at the end of the
    market. So `fetch` is asked for a CANARY_MIN-window probe
    of the first market before the full run is committed. Same
    protection, a few minutes instead of a few hours.

    `order="smallest"` restores the old behaviour for the case
    it was designed for: a session where something in symbol
    resolution has changed and you want the cheap test back.

    Two stop conditions, because an unattended run that keeps
    going after it has stopped being useful is worse than one
    that halts:

      FATAL — a locked account or a dropped TWS connection makes
        every subsequent request fail identically. Without this
        the loop would march through all eight markets writing
        false "no contract" records at full speed.

      SHUTOUT — any market that asks for CANARY_MIN or more
        windows and gets bars for none of them. With the symbol
        fixes working, at least one of five liquid index movers
        returns data; zero out of five means resolution,
        entitlement or pacing is broken, and the markets behind
        it fail the same way.

        First written as "if the FIRST market comes back
        empty", which the dry-run immediately exposed as
        useless: smallest-first put Australia's single window
        in front, so the rule was armed on a sample of one and
        disarmed before Hong Kong's fourteen ever ran. A stop
        condition that only watches the first market is a stop
        condition that mostly does not.

    Everything stays resumable; re-running picks up where it
    left off.
    """
    todo = []
    for m in (markets or list(EXCH)):
        p = DIR / f"{m}.json"
        have = set()
        if p.exists():
            try:
                have = {k for k, v in json.loads(p.read_text(encoding="utf-8"))
                        ["windows"].items() if v.get("px")}
            except Exception:                      # noqa: BLE001
                have = set()
        n = sum(1 for rev, tick, *_ in
                (jobs(m) if _edge_for(m) else [])
                if f"{rev}|{tick}" not in have)
        todo.append((n, m))
    todo.sort(reverse=(order == "largest"))
    live = [(n, m) for n, m in todo if n]
    print(f"run order ({order} first — "
          + ("the biggest backlog goes first; a "
             f"{CANARY_MIN}-window probe runs before it"
             if order == "largest" else
             "the first market is the canary for the c-222 "
             "symbol fixes")
          + "):")
    for n, m in todo:
        print(f"  {m:10} {n:>5} windows"
              + ("" if n else "   (nothing to do)"))
    print(f"  TOTAL {sum(n for n, _ in todo)}\n", flush=True)

    # c-258: the canary, made explicit. Largest-first would
    # otherwise put China's whole backlog in front of any
    # evidence that the session works.
    if order == "largest" and live:
        big = live[0][1]
        print(f"\n{'=' * 58}\nPROBE — {big}, first {CANARY_MIN} "
              f"windows\n{'=' * 58}", flush=True)
        pr = fetch(big, cap=CANARY_MIN) or {"todo": 0, "got": 0}
        if _session_looks_broken(pr):
            print(f"\nSTOPPING BEFORE THE RUN — {big} returned "
                  f"bars for none of {pr.get('todo')} probe "
                  f"windows, for reasons that will not improve: "
                  f"{pr.get('fatal') or pr.get('reasons')}.\n"
                  f"  Check entitlements and the TWS session "
                  f"before spending hours on the full backlog.")
            return
        if not pr.get("got"):
            print(f"\nprobe returned no bars, but IB ANSWERED "
                  f"every request — {pr.get('reasons')}.\n"
                  f"  Those are bad symbols, not a bad session, "
                  f"so the run continues.\n", flush=True)
        else:
            print(f"\nprobe OK — {pr['got']}/{pr['todo']}. "
                  f"Continuing with the full run.\n", flush=True)

    done = []
    for n, m in live:
        print(f"\n{'=' * 58}\n{m}\n{'=' * 58}", flush=True)
        r = fetch(m) or {"todo": 0, "got": 0, "fatal": None}
        done.append((m, r))
        if r.get("fatal"):
            print(f"\nSTOPPING THE WHOLE RUN — {r['fatal']}")
            break
        if (r["todo"] >= CANARY_MIN and not r["got"]
                and _session_looks_broken(r)):
            print(f"\nSTOPPING — {m} asked for {r['todo']} "
                  f"windows and got bars for none of them.\n"
                  f"  Zero out of {r['todo']} liquid index "
                  f"movers is a systemic failure — symbol "
                  f"resolution, entitlement or pacing — not a "
                  f"property of {m}, and the markets behind it "
                  f"would fail the same way.\n"
                  f"  Read the audit above, then re-run. "
                  f"Nothing is lost.")
            break

    print(f"\n{'=' * 58}\nRUN SUMMARY")
    for m, r in done:
        print(f"  {m:10} {r['got']:>5}/{r['todo']:<5} windows "
              f"returned bars"
              + (f"   [{r['fatal']}]" if r.get("fatal") else ""))
    left = [m for _n, m in live
            if m not in {x for x, _ in done}]
    if left:
        print(f"  NOT REACHED: {', '.join(left)}")
    print()
    plan(markets)


def _got(d, todo):
    """How many of THIS RUN's windows came back with bars."""
    return sum(1 for rev, code, *_ in todo
               if (d["windows"].get(f"{rev}|{code}") or {})
               .get("px"))


def refetch(market, apply=False):
    """Classify stored windows and clear only the BUGGED ones.

    After the first complete Taiwan run, three windows were
    short or empty. They are not the same kind of problem and
    must not get the same treatment:

      OUR BUG — re-fetch. A window written by an older version
        of this script. Two tells: it starts materially later
        than the window we now ask for (the pre-c-195 unclamped
        chunk walk dropped its first chunk), or it says "no
        contract" from before the blank-exchange fallback
        existed. 3443 and 3231 hold 2,695 bars starting
        2023-05-05 where the clamped code asks from
        2023-04-27 — six pre-announcement sessions missing from
        the only May-2023 windows we have.

      IB'S LIMIT — keep the empty record. The contract resolved
        and IB answered "HMDS query returned no data". No
        re-run changes that. Clearing it would just buy the
        same answer again at the cost of two requests per run,
        and worse, would make a settled fact look unresolved.

    Nothing is deleted without printing the reason first, and
    `apply` is required to actually clear.
    """
    f = DIR / f"{market}.json"
    if not f.exists():
        print(f"{market}: nothing harvested")
        return
    d = json.loads(f.read_text(encoding="utf-8"))
    W = d["windows"]
    want = {f"{r}|{c}": (a, b)
            for r, c, _a2, _n, a, b in jobs(market)}
    bug, keep = [], []
    for k, v in W.items():
        px = v.get("px") or []
        a, _b = want.get(k, (None, None))
        note = str(v.get("note") or "")
        if k not in want:
            # c-198b: the measured TPEx edge (2025-11-21) puts
            # 3105, 4966, 3293 and 5274 outside IB's coverage
            # entirely, so jobs() no longer asks for them.
            # Clearing such a record would delete data we hold
            # and never re-request it — 5274 has 1,890 real
            # bars. Never clear what the fetcher will not
            # re-fetch.
            keep.append((k, v, "outside the measured 5m "
                               "coverage — jobs() no longer "
                               "requests it, so clearing it "
                               "would only lose what we have"))
            continue
        if px and not v.get("first_bar"):
            # written before c-195 added measured labels, so its
            # pre_window/pre_ann_days are computed from the
            # dates ASKED rather than the bars HELD. One request
            # each at 120-day chunks — cheaper than doubting it.
            bug.append((k, v, "no first_bar — labels are from "
                              "the pre-c-195 code and describe "
                              "the request, not the data"))
            continue
        if not px:
            if "no contract" in note.lower():
                # written before the blank-exchange fallback —
                # the verdict itself is untrustworthy
                bug.append((k, v, "recorded 'no contract' before "
                                  "the blank-exchange fallback "
                                  "existed"))
            else:
                keep.append((k, v, "IB resolved it and served "
                                   "nothing — venue/edge limit"))
            continue
        if a and px[0][0][:10] > (a + dt.timedelta(days=6)
                                  ).isoformat():
            late = (dt.date.fromisoformat(px[0][0][:10])
                    - a).days
            if _board(market, v["code"]) == "tpex":
                keep.append((k, v, f"starts {late}d late, but on "
                                   "TPEx — that is IB's venue "
                                   "edge, not our bug"))
            else:
                bug.append((k, v, f"starts {late}d after the "
                                  f"window we now ask for "
                                  f"({a}) — the unclamped "
                                  f"chunk walk dropped its "
                                  f"first chunk"))
    print(f"\n{market}: {len(W)} stored, "
          f"{len(bug)} to re-fetch, {len(keep)} to keep\n")
    for k, v, why in bug:
        print(f"  RE-FETCH  {v['code']:6} {v['rev']:6} "
              f"{v['action']:3} {str(v.get('name'))[:22]:22} "
              f"{len(v.get('px') or []):>5} bars")
        print(f"            {why}")
    for k, v, why in keep:
        print(f"  KEEP      {v['code']:6} {v['rev']:6} "
              f"{v['action']:3} {str(v.get('name'))[:22]:22} "
              f"{len(v.get('px') or []):>5} bars")
        print(f"            {why}")
    if not bug:
        print("\n  nothing to re-fetch")
        return
    if not apply:
        print(f"\n  dry run. To clear and re-fetch:\n"
              f"    python scripts\\ib_5m_events.py refetch "
              f"{market} apply")
        return
    # c-206: KEEP A COPY, AND PUT IT BACK IF THE RE-FETCH IS
    # WORSE.
    #
    # The first run of this deleted 3443 and 3231 — 2,695 bars
    # each — and the re-fetch returned zero, because the larger
    # chunk size made a single edge-straddling request
    # all-or-nothing. The data was simply gone, and only Bill's
    # console output showed it had ever existed.
    #
    # A cleanup step that can end with less data than it started
    # with must be able to undo itself. Nothing is deleted from
    # disk until the replacement is measured against it.
    backup = {k: dict(v) for k, v, _w in bug}
    for k in backup:
        del W[k]
    f.write_text(json.dumps(d), encoding="utf-8")
    print(f"\n  cleared {len(backup)} (backed up in memory) — "
          f"fetching them now")
    fetch(market)

    d2 = json.loads(f.read_text(encoding="utf-8"))
    restored = []
    for k, old in backup.items():
        new = d2["windows"].get(k) or {}
        if len(new.get("px") or []) < len(old.get("px") or []):
            d2["windows"][k] = old
            restored.append(
                f"{old.get('code')} {old.get('rev')}: kept the "
                f"original {len(old.get('px') or [])} bars — the "
                f"re-fetch returned "
                f"{len(new.get('px') or [])}")
    if restored:
        f.write_text(json.dumps(d2), encoding="utf-8")
        print("\n  ROLLED BACK — the re-fetch was worse than "
              "what was already on disk:")
        for r in restored:
            print(f"    {r}")
        print("    These windows keep their original bars. The "
              "labels stay stale, which is the lesser problem.")
    audit(market)


def audit(market):
    """What the harvested file can and cannot support.

    Printed after every fetch so coverage is stated at the point
    of collection rather than discovered later by whoever runs
    the analysis.
    """
    f = DIR / f"{market}.json"
    if not f.exists():
        print(f"{market}: nothing harvested")
        return
    W = json.loads(f.read_text(encoding="utf-8"))["windows"]
    ok = [v for v in W.values() if v.get("px")]
    bad = [v for v in W.values() if not v.get("px")]
    # c-208: count SESSIONS, not calendar days.
    #
    # The old line reported "full 45d pre-announcement: 7" out
    # of 45, which reads like a disaster and is an artefact. The
    # window is requested 45 CALENDAR days before the
    # announcement, but the first bar almost always lands a day
    # or two later because the boundary falls on a weekend — so
    # a perfectly complete window scores 43 and fails a ">= 45"
    # test. What the analysis actually consumes is TRADING
    # SESSIONS, and the target was 30 of them.
    cal = calendar()

    def _sessions(v):
        ann = cal.get(v["rev"], ("9999",))[0]
        return len({b[0][:10] for b in v["px"] if b[0][:10] <= ann})

    pre = sorted(_sessions(v) for v in ok)
    full = [v for v in ok if _sessions(v) >= 30]
    med = pre[len(pre) // 2] if pre else 0
    print(f"\n  {market}: {len(ok)}/{len(W)} windows with bars")
    print(f"    pre-announcement sessions: median {med}, "
          f"{len(full)}/{len(ok)} at 30+ (the study target)")
    print(f"    ADD {sum(1 for v in ok if v['action'] == 'ADD')}"
          f"  DEL {sum(1 for v in ok if v['action'] == 'DEL')}")
    reasons = {}
    for v in bad:
        # windows written before empty_reason existed still
        # carry stopped_early, so derive rather than showing
        # them as "?" forever and forcing a pointless re-fetch
        r = v.get("empty_reason")
        s = str(v.get("stopped_early") or v.get("note") or "")
        # c-222: re-derive on EVERY read, not only when the
        # stored label is missing. Records written before this
        # revision carry "before_edge" for a permissions refusal
        # and "unexplained" for a timeout, and a stored label
        # that is wrong is worse than no label — it looks
        # settled. The stored value is kept only when the text
        # gives no better answer.
        d2 = ("no_permission" if "permission" in s.lower()
              else "timeout" if ("timeout" in s.lower()
                                 or "cancelled" in s.lower()
                                 or "reported no error" in s.lower())
              else "no_contract" if "no contract" in s.lower()
              else "venue_no_history" if ("no data" in s.lower()
                                          or "hmds" in s.lower())
              else None)
        reasons[d2 or r or "unexplained"] = \
            reasons.get(d2 or r or "unexplained", 0) + 1
    for r, n in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"    empty — {r}: {n}")
    _NOTE = {
        "venue_no_history":
            "IB resolved the contract and served no bars for "
            "that period. Usually a SECOND BOARD with a later "
            "floor (Taiwan TPEx, Korea KOSDAQ) or a listing "
            "younger than the window. Place the board's edge "
            "before reading it as absence.",
        "no_permission":
            "IB HAS the data and this account is not entitled "
            "to it — a subscription line, not a coverage fact. "
            "Korea KOSDAQ is the live case.",
        "timeout":
            "ib_async gave up waiting; IB reported no error. "
            "Retried automatically on the next run.",
        "no_contract":
            "the symbol did not resolve. Since c-222 this is "
            "retried once with the suffix stripped, an ADR "
            "fallback, and IB's own symbol search.",
    }
    for r, txt in _NOTE.items():
        if reasons.get(r):
            print(f"    ^ {r}: {txt}")
    # by venue, because a board-level gap is a sampling problem
    # and not visible in a market-level count
    venues = {}
    for v in list(ok) + list(bad):
        b = (_board(market, v["code"]) or v.get("venue")
             or "?").lower()
        venues[b] = venues.get(b, 0) + (1 if v.get("px") else 0)
    if len(venues) > 1:
        print("    by venue: " + ", ".join(
            f"{k} {n}" for k, n in sorted(venues.items())))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    mkts = sys.argv[2:] or None
    if cmd == "refetch":
        refetch(mkts[0] if mkts else "Taiwan",
                apply=("apply" in sys.argv[2:]))
    elif cmd == "audit":
        for m in (mkts or [p.stem for p in DIR.glob("*.json")]):
            audit(m)
    elif cmd == "tune":
        tune()
    elif cmd == "ready":
        ready(mkts)
    elif cmd == "symbols":
        symbols(mkts[0] if mkts else "India")
    elif cmd == "edges":
        edges(mkts)
    elif cmd == "fetch":
        # c-205: China is back IN the default run. Bill's c-199
        # answer was "skip for now"; he has reversed it, and the
        # two reasons I gave for skipping have both been
        # addressed since — the venue routing is per-listing
        # (_china_venue) rather than everything through
        # Shanghai, and China now has a daily counterpart in
        # apac_event_days. What remains true is that IB reaches
        # mainland A-shares only through Stock Connect
        # Northbound, which is recorded on every window as the
        # venue so it can never pool silently with a locally
        # traded market.
        # c-226: `fetch` with no market is now ONE ORDERED RUN
        # with stop conditions, not a bare loop. `fetch Japan`
        # still does exactly one market.
        # c-258: LARGEST first by default, so China's backlog
        # runs before the one-window markets. `fetch smallest`
        # restores the c-226 order.
        order = "largest"
        if mkts and mkts[0] in ("largest", "smallest"):
            order, mkts = mkts[0], mkts[1:] or None
        if mkts and len(mkts) == 1:
            fetch(mkts[0])
        else:
            fetch_all(mkts, order=order)
    else:
        plan(mkts)
