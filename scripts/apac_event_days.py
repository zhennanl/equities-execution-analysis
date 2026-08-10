"""APAC event-window price harvester (c-129) — the
survivorship fix, generalized.

DESIGN: per-stock APIs die with the listing; DAY-FILES do not.
Where an exchange publishes a daily all-stock file, we pull the
~45 files around each review and delisted names appear
automatically. Where it does not, we fall back to Yahoo's
chart endpoint (SURVIVORS ONLY, coverage % reported per
market, never hidden).

ADAPTERS (probed 2026-08-07 before writing — no imagined
endpoints):
  IN  NSE bhavcopy — VERIFIED both eras: the old
      cm{DD}{MON}{YYYY}bhav.csv.zip (pre-Jul-2024) and the new
      sec_bhavdata_full_{DDMMYYYY}.csv. Complete daily files ->
      India is fully DELISTED-SAFE.
  YF  yfinance BATCHED download per (review, market): one
      chart-API call for all of a review's movers. Survivors
      only. (Stooq probed as the delisted fallback: serves a
      robots block page from this host — dead, registered.)
  TW  already done via TWSE (tw_event_windows.json).
  KR/ID day-file adapters are TERMINAL-GATED (KRX getJsonData
      = LOGOUT here; IDX = Cloudflare) — stubs raise with
      instructions rather than pretending.

CONVENTION: identical to Taiwan — MSCI announces ALL markets in
one Geneva press release, so the TW registry's exact
announcement dates 2015+ apply to every market. Day 0 = the
announcement date's LOCAL close (pre-news for all Asian
sessions).

Usage:
  py scripts\\apac_event_days.py in            (India day-files)
  py scripts\\apac_event_days.py yf [MKT ...]  (survivor windows)
  py scripts\\apac_event_days.py status
Output: data/apac_event_windows/<MKT>.json  (same schema as
        tw_event_windows.json -> one analyzer serves all)
"""
import datetime as dt
import io
import json
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "data" / "apac_event_windows"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 Chrome/126 Safari/537.36"}
# c-192. Bill: "add 30 days before the index announcement day".
# 30 CALENDAR days is only ~21 trading sessions, which is thin
# for a month-of-behaviour read; 30 TRADING days needs ~45
# calendar days once weekends and holidays are removed. Fetching
# the wider span costs nothing extra (same request) and lets the
# ANALYSIS slice to either definition, so we fetch generously
# once and decide later.
PRE_ANN_DAYS = 45          # calendar, >= 30 trading sessions
POST_EFF_DAYS = 45         # c-193: matches the 5m
                           # harvester so the daily and
                           # intraday datasets slice on
                           # the SAME window
PAD = POST_EFF_DAYS        # legacy alias

sys.path.insert(0, str(ROOT / "scripts"))
from markets import is_active                      # noqa: E402

# A register returning fewer than this many codes is a failed
# call, not a market that delisted itself. See delisted().
MIN_REGISTER = 200

YF_SUFFIX = {"Japan": ".T", "Korea": ".KS", "HongKong": ".HK",
             "Australia": ".AX", "Singapore": ".SI",
             "Malaysia": ".KL", "Thailand": ".BK",
             "Indonesia": ".JK", "Philippines": ".PS",
             "NewZealand": ".NZ", "India": ".NS"}


# c-223: ONE LIST. There were two, and they disagreed.
#
# c-205 added China to harvest_all()'s market list and left the
# `yf` sub-command's list untouched, so `all` and `yf` harvested
# different sets of markets and neither said so. On disk the
# result is stark: China has 1,253 movers since 2015 and ZERO
# priced windows — 60% of the whole APAC sample, silently
# absent, while the run printed "all stages completed".
#
# A literal list repeated in two places is the same defect as a
# hardcoded market list in a view: it works until someone edits
# one copy.
YF_MARKETS = ["Japan", "Korea", "HongKong", "China", "Australia",
              "Singapore", "Thailand", "Malaysia", "Indonesia",
              "Philippines", "NewZealand"]

# Markets priced by their own harvester rather than by Yahoo,
# with the file each writes. Listed so `coverage` can tell
# "harvested elsewhere" apart from "never harvested" — Taiwan
# looked like a hole for exactly this reason.
ELSEWHERE = {
    "Taiwan": ("data/tw_event_windows.json",
               "scripts/tw_event_window.py (TWSE, delisted-safe)"),
}


def calendar():
    """{rev: (ann, eff)} — global dates from the TW registry
    (2015+ exact)."""
    ev = json.loads((ROOT / "data" / "msci_tw_events.json")
                    .read_text(encoding="utf-8"))
    return {r: (v["ann"], v["eff"]) for r, v in ev.items()
            if v.get("ann") and v.get("eff")}


def movers(market):
    """[(rev, code, ticker, action, name)] for one market,
    2015+ with tickers."""
    import pandas as pd
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    cal = calendar()
    g = df[(df.market == market) & (df.year >= 2015)
           & (df.ticker != "")]
    out = []
    for _, r in g.iterrows():
        if r.review in cal:
            out.append((r.review, r.ticker, r.action,
                        r.security))
    return out


def _win(rev, cal):
    """Window is ANNOUNCEMENT-anchored on the left, EFFECTIVE-
    anchored on the right — the two dates move independently
    (the gap runs 16-23 calendar days), so one pad cannot serve
    both ends."""
    a = (dt.date.fromisoformat(cal[rev][0])
         - dt.timedelta(days=PRE_ANN_DAYS))
    b = (dt.date.fromisoformat(cal[rev][1])
         + dt.timedelta(days=POST_EFF_DAYS))
    return a, b


def _short(w, want_start):
    """True if a stored window must be re-fetched: it starts too
    late for the wider pre-window, or predates the OHLC upgrade
    and carries close-only rows."""
    px = w.get("px") or []
    if not px:
        # c-194b, and this reverses a choice I made in c-192.
        # I skipped empty windows on the assumption they were
        # delisted names with nothing to fetch. The register
        # check proved otherwise: of Hong Kong's 10 unpriced
        # movers only ONE is genuinely gone, and the others are
        # Swire Properties, Hang Lung, Chow Tai Fook, Kerry
        # Properties — all live and listed. Japan's three are
        # Kawasaki Kisen, Mitsui OSK and Renesas, all trading.
        # Those were OUR fetch failures, and skipping them made
        # a fixable bug look like an unfixable data limit.
        # So empty windows are retried unless the exchange's own
        # register has confirmed the security is gone.
        return not w.get("confirmed_delisted")
    if px[0]["d"] > want_start.isoformat():
        return True
    return "o" not in px[0]


def _load(mkt):
    DIR.mkdir(parents=True, exist_ok=True)
    p = DIR / f"{mkt}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"market": mkt, "convention":
            "day0 = announcement-date local close (global "
            "Geneva announcement; TW registry dates)",
            "windows": {}}


def refuse_if_elsewhere(mkt):
    """Stop a market that has its own harvester (c-269).

    Taiwan is in ELSEWHERE and has no entry in YF_SUFFIX, so
    `yf Taiwan` sent BARE codes to Yahoo — "1504", "2610" — got
    136 404s, and wrote a Taiwan.json of 136 unpriced rows.
    Nothing errored; the run just reported 0/136, which reads
    as "Taiwan has no data" when the truth is 175/179 in
    tw_event_windows.json.

    The damage is not the wasted requests, it is that any
    coverage scan walking data/apac_event_windows/*.json then
    reports Taiwan at 0%. That is exactly how I misread this
    market's coverage an hour ago.

    A market in ELSEWHERE is not "not yet harvested", it is
    harvested by something else, and the two are only
    distinguishable if the code says so out loud.
    """
    if mkt in ELSEWHERE:
        path, who = ELSEWHERE[mkt]
        raise SystemExit(
            f"{mkt} is not harvested here.\n"
            f"  it is priced by {who}\n"
            f"  and stored in {path}\n"
            f"  (no Yahoo suffix exists for it; asking anyway "
            f"sends bare codes and writes an empty file)")


def _save(mkt, d):
    refuse_if_elsewhere(mkt)
    (DIR / f"{mkt}.json").write_text(json.dumps(d), encoding="utf-8")


# ---------------- India: NSE bhavcopy day-files -------------
_MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG",
        "SEP", "OCT", "NOV", "DEC"]


class BhavUnavailable(Exception):
    """NSE could not be reached — as opposed to reached and
    empty. c-200: the two must never collapse into the same
    value. A holiday is a fact worth caching forever; a timeout
    is a retry, and caching it as {} would silently blank a real
    trading day."""


def _get(url, tries=4, timeout=60):
    """One NSE fetch, with backoff.

    c-200: `py scripts\\apac_event_days.py all` died on a single
    read timeout from nsearchives.nseindia.com and took the
    ENTIRE run with it — India stopped after one review and the
    ten Yahoo markets never started. One flaky socket should
    not cost a whole harvest.
    """
    import requests
    last = None
    for k in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=timeout)
            if r.status_code == 404:
                return None            # no file = holiday
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}"
        except Exception as e:                     # noqa: BLE001
            last = f"{type(e).__name__}"
        if k < tries - 1:
            time.sleep(2 ** k * 3)
    raise BhavUnavailable(f"{last} after {tries} tries: "
                          f"{url.rsplit('/', 1)[-1]}")


def _bhav_day(d):
    """{symbol: (close, volume, open, high, low)} for one date.

    Returns {} for a day NSE confirms has no file (holiday), and
    raises BhavUnavailable if NSE could not be reached at all.

    c-192: widened from (close, volume). India is our only
    DELISTED-SAFE APAC source, so it would be perverse for it to
    carry less per row than the survivor-biased Yahoo path.
    """
    if d >= dt.date(2024, 7, 8):
        u = ("https://nsearchives.nseindia.com/products/content/"
             f"sec_bhavdata_full_{d:%d%m%Y}.csv")
        r = _get(u)
        if r is None or not r.text.startswith("SYMBOL"):
            return {}
        out = {}
        for ln in r.text.splitlines()[1:]:
            p = [x.strip() for x in ln.split(",")]
            if len(p) > 12 and p[1] == "EQ":
                try:
                    # full bhavcopy: 4=OPEN 5=HIGH 6=LOW
                    # 8=CLOSE 10=TTL_TRD_QNTY
                    out[p[0]] = (float(p[8]), float(p[10]),
                                 float(p[4]), float(p[5]),
                                 float(p[6]))
                except ValueError:
                    pass
        return out
    u = ("https://nsearchives.nseindia.com/content/historical/"
         f"EQUITIES/{d.year}/{_MON[d.month - 1]}/"
         f"cm{d:%d}{_MON[d.month - 1]}{d.year}bhav.csv.zip")
    r = _get(u)
    if r is None or r.content[:2] != b"PK":
        return {}
    z = zipfile.ZipFile(io.BytesIO(r.content))
    txt = z.read(z.namelist()[0]).decode()
    out = {}
    for ln in txt.splitlines()[1:]:
        p = ln.split(",")
        if len(p) > 8 and p[1] == "EQ":
            try:
                # c-200 — A BUG I SHIPPED IN c-198.
                #
                # This branch (dates before 2024-07-08, i.e. most
                # of the history) returned only (close, volume).
                # c-198 then added a cache rule that invalidates
                # any day whose rows are shorter than 5 fields,
                # to force the OHLC upgrade through. Together
                # those two make an INFINITE RE-DOWNLOAD: every
                # pre-2024 day is invalidated, re-fetched, comes
                # back 2-wide, is cached, and is invalidated
                # again on the next run. It would never converge
                # and never gain OHLC.
                #
                # The old zip has the columns all along —
                # SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,
                # PREVCLOSE,TOTTRDQTY — so 2=OPEN 3=HIGH 4=LOW
                # 5=CLOSE 8=TOTTRDQTY. They were simply not being
                # read.
                out[p[0]] = (float(p[5]), float(p[8]),
                             float(p[2]), float(p[3]),
                             float(p[4]))
            except ValueError:
                pass
    return out


def harvest_in():
    cal = calendar()
    mv = movers("India")
    d0 = _load("India")
    byrev = {}
    for rev, tick, act, name in mv:
        byrev.setdefault(rev, []).append(
            (tick.split(".")[0], act, name))
    days_cache = d0.setdefault("_days", {})
    for rev in sorted(byrev, key=lambda r: cal[r][0],
                      reverse=True):
        a, b = _win(rev, cal)
        # c-198: India was skipping on PRESENCE alone, never on
        # coverage — `if all(key in windows): continue`. So the
        # wider 45-day window and the OHLC upgrade never reached
        # it: Bill's full run printed "India done: 157/166" with
        # no per-review lines because every review was skipped.
        # The stored windows still carry 17 pre-announcement
        # sessions and close-only rows while every Yahoo market
        # now has 30 and full OHLC — which would have made India
        # quietly incomparable with the rest of APAC in exactly
        # the study that compares them. Same `_short` test as
        # the Yahoo path now.
        if all(f"{rev}|{c}" in d0["windows"]
               and not _short(d0["windows"][f"{rev}|{c}"], a)
               for c, _, _ in byrev[rev]):
            continue
        # c-223: ask the bhavcopy for the PREDECESSOR symbol too
        # where this window predates a rename. Eight of India's
        # windows were empty for this one reason — IDFCFIRSTB
        # did not exist before January 2019, TATAMTRDVR is what
        # MSCI's "TATA MOTORS A" traded as, and BANKBETF is a
        # ticker-map collision for Bajaj Finserv. The bhavcopy
        # is the referee: an alias only ever contributes rows it
        # actually returns, and which alias paid is recorded.
        alias = {}
        for c, _a2, _n in byrev[rev]:
            p = _predecessor("India", c, b.isoformat())
            if p:
                alias[c] = p
        series = {c: [] for c, _, _ in byrev[rev]}
        want = sorted({c for c, _, _ in byrev[rev]}
                      | {v[0] for v in alias.values()})
        d, failed = a, None
        while d <= b:
            if d.weekday() < 5:
                k = d.isoformat()
                cached = days_cache.get(k)
                # c-200: THE CACHE MUST REMEMBER WHAT IT WAS
                # ASKED FOR. Each day is stored filtered to the
                # movers of the review that fetched it, to keep
                # the file small. But review windows are ~108
                # days and reviews are ~90 days apart, so
                # CONSECUTIVE WINDOWS OVERLAP by two to three
                # weeks — and on those shared dates the second
                # review read a cached day that had been
                # filtered to the FIRST review's symbols. Its own
                # names were simply absent, and absent looks
                # exactly like "did not trade". Recording the
                # symbol list the day was filtered for turns
                # that into a cache miss instead of a silent gap.
                #
                # c-198's OHLC rule still applies: rows shorter
                # than 5 fields predate the upgrade.
                usable = (
                    cached is not None
                    and set(want) <= set(cached.get("_ask", []))
                    and all(len(r) >= 5
                            for s, r in cached.items()
                            if s != "_ask"))
                if usable:
                    day = cached
                else:
                    try:
                        full = _bhav_day(d)
                    except BhavUnavailable as e:
                        failed = f"{k}: {e}"
                        break
                    ask = sorted(set(want) |
                                 set((cached or {}).get("_ask",
                                                        [])))
                    day = {s: full[s] for s in ask if s in full}
                    day["_ask"] = ask
                    days_cache[k] = day
                    time.sleep(0.8)
                for c, _, _ in byrev[rev]:
                    # the live symbol wins; the alias is only
                    # consulted when the day has no row for it
                    s = (c if c in day else
                         alias[c][0] if c in alias
                         and alias[c][0] in day else None)
                    if s and s != "_ask":
                        row = day[s]
                        rec = {"d": k, "c": row[0], "v": row[1]}
                        if len(row) >= 5:
                            rec.update(o=row[2], h=row[3],
                                       l=row[4])
                        series[c].append(rec)
            d += dt.timedelta(days=1)
        if failed:
            # do NOT write partial windows — a half-filled window
            # that looks complete is worse than an absent one
            _save("India", d0)
            print(f"India {rev}: ABORTED, NSE unreachable "
                  f"({failed}). Progress saved; re-run to "
                  f"resume from here.", flush=True)
            continue
        for c, act, name in byrev[rev]:
            w = {"rev": rev, "code": c, "action": act,
                 "name": name, "ann": cal[rev][0],
                 "eff": cal[rev][1], "ann_src": "registry",
                 "px": series[c], "src": "NSE bhavcopy "
                 "(delisted-safe)"}
            if c in alias:
                w["tried_symbols"] = [c, alias[c][0]]
                if series[c]:
                    w["resolved_via"] = alias[c][0]
                    w["resolved_why"] = alias[c][1]
            d0["windows"][f"{rev}|{c}"] = w
        _save("India", d0)
        got = sum(1 for c, _, _ in byrev[rev] if series[c])
        print(f"India {rev}: {got}/{len(byrev[rev])} names",
              flush=True)
    n = len(d0["windows"])
    ok = sum(1 for v in d0["windows"].values() if v["px"])
    print(f"India done: {ok}/{n} windows with data", flush=True)


# Second listing venue per market, tried only when the primary
# suffix returns nothing. Korea .KQ = KOSDAQ; left empty where
# the market genuinely has one board — a guess here would
# manufacture false recoveries.
ALT_SUFFIX = {"Korea": ".KQ"}

# c-198: codes that are not the equity line Yahoo knows.
#
#   Thailand  TTB-R / IRPC-R are NVDR lines (foreign-investor
#             depositary receipts trading alongside the
#             ordinary share). Yahoo carries the ORDINARY.
#   NewZealand MCY040 / IFT340 are BOND tickers, not equities —
#             Mercury and Infratil debt lines that leaked into
#             the changes DB. The equity is MCY / IFT.
#   Singapore GRAB is NASDAQ-listed, not SGX. MSCI Singapore
#             includes it on domicile, so the ".SI" suffix was
#             never going to resolve.
#   HongKong  FUTU is a US ADR for the same reason.
#
# Each is a RULE plus its reason, not a silent string swap, so
# the recovered rows can be traced to why they were reachable.
FOREIGN_LINE = {("Singapore", "GRAB"): ("GRAB", "NASDAQ listing "
                                        "— Singapore by domicile"),
                ("HongKong", "FUTU"): ("FUTU", "US ADR — Hong "
                                       "Kong by domicile")}


def _load_foreign_lines():
    """c-263: recovered cross-border lines, from disk.

    `ticker_recover.py` can resolve an ADR — Alibaba, BeiGene,
    58.com — for a market whose symbols normally carry a local
    suffix. Appending ".SS" to "BABA" would produce a symbol
    that resolves to nothing, so those recoveries are recorded
    separately and merged here rather than being squeezed
    through the suffix rule.

    Keep in mind what an ADR line IS: the same issuer trading
    on a US calendar. Its "effective day" close is a US close,
    hours after the Asian one, so an event study that pools it
    with local lines is comparing different sessions.
    """
    p = ROOT / "data" / "foreign_lines.json"
    if not p.exists():
        return
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:                              # noqa: BLE001
        return
    for k, v in d.items():
        if "|" not in k or not v:
            continue
        mkt, sec = k.split("|", 1)
        sym = v[0] if isinstance(v, (list, tuple)) else v
        why = (v[1] if isinstance(v, (list, tuple)) and len(v) > 1
               else "recovered cross-border line")
        FOREIGN_LINE[(mkt, sec)] = (sym, why)
        FOREIGN_LINE.setdefault((mkt, sym), (sym, why))


_load_foreign_lines()


# c-223: THE TICKER MAP IS CURRENT-STATE; THE WINDOWS ARE
# HISTORICAL.
#
# Every unpriced Indian window and the one Korean one share a
# single cause: our changes DB carries the symbol the company
# trades under TODAY, and the window sits before the rename,
# demerger or spin-off that created it. Yahoo and the NSE
# bhavcopy both answer honestly — that symbol did not exist on
# that date — and the window looks like a delisting.
#
# Each entry is (market, current_code) -> (old_code, effective
# date of the change, one-line reason, source). The date matters
# as much as the symbol: the predecessor is tried ONLY for
# windows that close before it, so a rename cannot leak
# backwards into a period where the current symbol is right.
#
# These are HYPOTHESES. The referee is the data: the harvester
# only accepts a predecessor if rows actually come back, and it
# records which symbol paid out. Nothing here is asserted into
# the dataset on my say-so.
PREDECESSOR = {
    ("India", "IDFCFIRSTB"): (
        "IDFCBANK", "2019-01-12",
        "IDFC Bank renamed IDFC FIRST Bank after the Capital "
        "First merger completed 2018-12-18",
        "https://en.wikipedia.org/wiki/IDFC_First_Bank"),
    ("India", "TMCV"): (
        "TATAMTRDVR", "2024-09-01",
        "MSCI's 'TATA MOTORS A' is the DVR / 'A' Ordinary line, "
        "cancelled under the scheme effective 2024-09-01",
        "https://www.tatamotors.com/wp-content/uploads/2024/09/"
        "FAQs-Cancellation-of-A-Ordinary-Shares.pdf"),
    ("India", "ENRIN"): (
        "SIEMENS", "2025-06-19",
        "Siemens Energy India was demerged out of Siemens Ltd; "
        "before the demerger the index name is Siemens Ltd",
        "MSCI change list names the security SIEMENS INDIA"),
    ("India", "BANKBETF"): (
        "BAJAJFINSV", None,
        "TICKER-MAP COLLISION, not a rename — BANKBETF is a "
        "bank ETF. The security MSCI moved is Bajaj Finserv.",
        "docs/TICKER_COLLISIONS.md"),
    ("Korea", "456040"): (
        "010060", "2023-05-01",
        "OCI Company Ltd (KOSE A010060) spun off on 2023-05-01 "
        "into OCI Holdings and a new OCI; 456040 is the "
        "post-split line and did not exist in 2020",
        "https://www.oci.co.kr/en/newsroom/news/4"),
}


def _predecessor(mkt, code, window_end):
    """(old_code, why) if this window predates a symbol change."""
    hit = PREDECESSOR.get((mkt, str(code).strip()))
    if not hit:
        return None
    old, since, why, src = hit
    if since and str(window_end) >= since:
        return None
    return old, f"{why} [{src}]"


def _china_yf(code):
    """Yahoo symbol for an MSCI China mover, by listing venue.

    c-205: China was absent from the daily harvest entirely,
    while the 5-minute harvester now covers it. Two datasets
    that are supposed to slice the same window on the same
    events cannot cover different markets.

    MSCI China spans three venues and Yahoo names them
    differently from IBKR: Shanghai is ".SS", Shenzhen ".SZ",
    Hong Kong ".HK" — and unlike IBKR, Yahoo DOES want the HK
    code zero-padded to four digits. The A/B-share and ADR
    lines fall out of the same rule.
    """
    t = str(code).strip().upper()
    if t.endswith((".SS", ".SZ", ".HK")):
        base, suf = t[:-3], t[-3:]
        return f"{int(base):04d}{suf}" if (
            suf == ".HK" and base.isdigit()) else t
    if t.isdigit() and len(t) == 6:
        return t + (".SS" if t[:2] in ("60", "68") else ".SZ")
    if t.isdigit():
        return f"{int(t):04d}.HK"
    return t                                   # US ADR


def _candidates(mkt, code, window_end=None):
    """Yahoo symbols to try for one index mover, best first.

    c-223: `window_end` enables the predecessor lookup. It is
    optional so every existing caller keeps working — but a
    caller that does not pass it cannot recover a renamed name,
    which is why the harvester now passes it.
    """
    code = str(code).strip()
    fx = FOREIGN_LINE.get((mkt, code))
    if fx:
        return [(fx[0], fx[1])]
    pre = _predecessor(mkt, code, window_end) if window_end \
        else None
    if mkt == "China":
        return [(_china_yf(code), "listing venue from the "
                                  "ticker suffix")]
    suf = YF_SUFFIX.get(mkt, "")
    base = code
    if mkt == "HongKong" and base.isdigit():
        base = f"{int(base):04d}"
    if mkt == "Korea" and base.isdigit():
        base = f"{int(base):06d}"
    out = [(base + suf if "." not in code else code,
            "primary listing")]
    if mkt in ALT_SUFFIX:
        out.append((base + ALT_SUFFIX[mkt],
                    f"alternate board {ALT_SUFFIX[mkt]}"))
    if mkt == "Thailand" and code.endswith("-R"):
        out.append((code[:-2] + suf,
                    "ordinary share (the -R line is an NVDR)"))
    if mkt == "NewZealand":
        import re as _re
        stem = _re.sub(r"\d+$", "", code)
        if stem and stem != code:
            out.append((stem + suf,
                        "equity line (the numeric suffix is a "
                        "bond ticker)"))
    if pre:
        # after the mechanical fallbacks: a rename is rarer than
        # a second board, and trying it first would risk pulling
        # the predecessor's prices for a window where the
        # current line is the right one.
        out.append((pre[0] + suf, pre[1]))
    seen, uniq = set(), []
    for s, why in out:
        if s not in seen:
            seen.add(s)
            uniq.append((s, why))
    return uniq


def _rows(px, sym):
    """OHLCV rows out of a yfinance frame, whatever its shape.

    c-198 — THE BUG THAT ATE ~50 WINDOWS.

    yfinance 1.5.1: "multi_level_index: Always return a
    MultiIndex DataFrame? Default is True". So download()
    returns MultiIndex columns EVEN FOR ONE TICKER. The old
    parse was

        sub = px[sym] if len(syms) > 1 else px
        sub.dropna(subset=["Close"])

    For a single-symbol batch that left the ticker level in
    place, so "Close" was not a column, dropna raised KeyError,
    and a bare `except Exception: rows = []` swallowed it. The
    window was written empty with no error line printed — which
    is why Bill's console shows failures ONLY on reviews with
    exactly one mover, and never on reviews with two or more.

    Count in the stored files: 55 empty windows sat in
    one-symbol reviews, 11 in multi-symbol reviews. The
    one-symbol failures are this bug, not missing data — REECE,
    QANTAS, CATHAY PACIFIC, HANG LUNG, UOL, GENTING SINGAPORE,
    TOP GLOVE, RENESAS all trade today and Yahoo has every one.

    Two fixes: index by ticker whichever shape comes back, and
    stop swallowing the exception.
    """
    if px is None or getattr(px, "empty", True):
        return [], "empty frame"
    try:
        sub = px
        if getattr(px.columns, "nlevels", 1) > 1:
            lv0 = set(px.columns.get_level_values(0))
            if sym in lv0:                     # group_by="ticker"
                sub = px[sym]
            else:                              # group_by="column"
                sub = px.copy()
                sub.columns = sub.columns.get_level_values(0)
        if "Close" not in sub.columns:
            return [], f"no Close column in {list(sub.columns)[:4]}"
        out = []
        for idx, r in sub.dropna(subset=["Close"]).iterrows():
            out.append({"d": idx.strftime("%Y-%m-%d"),
                        "o": round(float(r["Open"]), 4),
                        "h": round(float(r["High"]), 4),
                        "l": round(float(r["Low"]), 4),
                        "c": round(float(r["Close"]), 4),
                        "v": float(r["Volume"] or 0)})
        return out, None
    except Exception as e:                         # noqa: BLE001
        return [], f"{type(e).__name__}: {str(e)[:80]}"


def _pull_one(yf, sym, a, b):
    """One symbol, OHLCV. Returns rows only."""
    try:
        px = yf.download(sym, start=a.isoformat(),
                         end=b.isoformat(), progress=False,
                         auto_adjust=False, threads=False)
    except Exception:                              # noqa: BLE001
        return []
    return _rows(px, sym)[0]


# ---------------- Yahoo survivors (batched) -----------------
def harvest_yf(markets):
    import yfinance as yf
    cal = calendar()
    for mkt in markets:
        d0 = _load(mkt)
        mv = movers(mkt)
        byrev = {}
        for rev, tick, act, name in mv:
            t = str(tick)
            # c-198: symbol construction now lives in
            # _candidates(), which also knows the fallbacks —
            # alternate board, NVDR-to-ordinary, bond-to-equity,
            # foreign primary listing.
            sym = _candidates(mkt, t)[0][0]
            byrev.setdefault(rev, []).append(
                (sym, t.split(".")[0], act, name))
        for rev in sorted(byrev, key=lambda r: cal[r][0],
                          reverse=True):
            a_chk, _ = _win(rev, cal)
            # c-198: a foreign primary listing was stamped
            # confirmed_delisted by the register sweep — FUTU is
            # absent from the HKEX register because it has never
            # been an HK listing, not because it died. The
            # register is right about the venue and wrong about
            # the company. Clear the stamp for names we now know
            # how to reach.
            for x in byrev[rev]:
                w = d0["windows"].get(f"{rev}|{x[1]}")
                if w and (mkt, x[1]) in FOREIGN_LINE:
                    w.pop("confirmed_delisted", None)
                    w.pop("delisted_evidence", None)
            todo = [x for x in byrev[rev]
                    if f"{rev}|{x[1]}" not in d0["windows"]
                    or _short(d0["windows"][f"{rev}|{x[1]}"],
                              a_chk)]
            if not todo:
                continue
            a, b = _win(rev, cal)
            syms = [x[0] for x in todo]
            try:
                px = yf.download(
                    syms, start=a.isoformat(),
                    end=b.isoformat(), progress=False,
                    auto_adjust=False, group_by="ticker",
                    threads=False)
            except Exception as e:                 # noqa: BLE001
                print(f"{mkt} {rev}: batch FAIL "
                      f"{type(e).__name__}", flush=True)
                time.sleep(10)
                continue
            for sym, code, act, name in todo:
                # c-192: OHLC, not close-only. An index trade
                # that gaps at the open behaves differently from
                # one that grinds through the session, and
                # close-only cannot tell them apart.
                rows, why = _rows(px, sym)
                d0["windows"][f"{rev}|{code}"] = {
                    "rev": rev, "code": code, "action": act,
                    "name": name, "ann": cal[rev][0],
                    "eff": cal[rev][1], "yf_symbol": sym,
                    "ann_src": "registry", "px": rows,
                    "parse_error": None if rows else why,
                    "src": "yahoo-chart (SURVIVORS ONLY)"}
            # c-195: SECOND VENUE PASS.
            #
            # Korea's 26 unpriced movers are not delistings. The
            # register run named them: Alteogen, Ecopro, JYP
            # Entertainment, Celltrion Pharm, CJ ENM — all
            # trading today. What they share is KOSDAQ, and this
            # harvester forced ".KS" (KOSPI) on every Korean
            # code. Yahoo has no ".KS" line for a KOSDAQ name, so
            # the request came back empty and the window looked
            # like a dead company.
            #
            # That is the same mistake as the Taiwan TWSE/TPEx
            # one found in ib_5m_events today: a market with two
            # boards, and a map that names only the larger. So
            # the alternate board is now retried before a window
            # is written off, and the suffix that worked is
            # recorded on the window.
            for sym, code, act, name in todo:
                w = d0["windows"].get(f"{rev}|{code}")
                if w and w.get("px"):
                    continue
                tried = []
                for cand, why in _candidates(
                        mkt, code, b.isoformat())[1:]:
                    rows = _pull_one(yf, cand, a, b)
                    tried.append(cand)
                    if rows:
                        w.update(px=rows, yf_symbol=cand,
                                 venue=why, parse_error=None)
                        print(f"    {mkt} {code}: recovered on "
                              f"{cand} — {why} ({len(rows)} days)",
                              flush=True)
                        break
                    time.sleep(0.8)
                if tried and not w.get("px"):
                    w["tried_symbols"] = [sym] + tried
            _save(mkt, d0)
            got = sum(1 for s, c, _, _ in todo
                      if d0["windows"][f"{rev}|{c}"]["px"])
            print(f"{mkt} {rev}: {got}/{len(todo)}", flush=True)
            time.sleep(2.5)
        n = len(d0["windows"])
        ok = sum(1 for v in d0["windows"].values() if v["px"])
        print(f"{mkt} done: {ok}/{n} windows", flush=True)


# ---------------- the delisted register --------------------
def delisted():
    """Every index mover we could NOT price, classified.

    WHY THIS EXISTS. Ten of the eleven daily markets are priced
    from Yahoo, which lists the LIVING. A company deleted from
    the index that later delisted is simply absent — and those
    are exactly the names MSCI removed, so the bias falls
    hardest on the deletion side. Silence in a dataset is the
    most dangerous kind of missing data because nothing marks
    it.

    So the gap is turned into an ARTIFACT: which company, which
    review, which action, and what evidence we have that it is
    delisted rather than merely mis-tickered. A deletion study
    can then state its own blind spot instead of discovering it
    later.

    EVIDENCE, strongest first:
      register  - absent from the exchange's own live listed
                  register (Taiwan, Japan, Hong Kong, Shanghai).
                  A positive statement by the exchange.
      weak      - no data and no reachable register. Could be a
                  delisting, could be a ticker we spelled wrong.
                  Labelled as weak, never as fact.
    """
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "scripts"))
    cal = calendar()
    regs = {}
    try:
        import requests
        from dead_ticker_sweep import REGISTERS
        sess = requests.Session()
        for m, fn in REGISTERS.items():
            try:
                got = fn(sess)[0]
            except Exception as e:                 # noqa: BLE001
                print(f"  register {m}: unreachable ({e})")
                continue
            # c-195 SAFETY FLOOR. China returned 0 live codes —
            # the SSE call fails without raising. An EMPTY
            # register is not a register: every code would test
            # as "absent", so the script would have declared an
            # entire market delisted and stamped
            # confirmed_delisted on all of it, permanently
            # stopping the harvester from retrying. China has no
            # window file yet, so nothing was harmed this time.
            # That is luck, not design, so the floor goes in.
            # No real APAC exchange lists under 200 companies.
            if len(got) < MIN_REGISTER:
                print(f"  register {m}: DISCARDED — returned "
                      f"{len(got)} codes, below the {MIN_REGISTER}"
                      f" floor. Treating as unreachable rather "
                      f"than as proof of mass delisting.")
                continue
            regs[m] = got
            print(f"  register {m}: {len(regs[m])} live codes")
    except Exception as e:                         # noqa: BLE001
        print(f"  registers unavailable: {e}")
    out, tally = {}, {}
    for f in sorted(DIR.glob("*.json")):
        mkt = f.stem
        # c-195: the Philippines file is still on disk from
        # before the market was excluded, and it was showing a
        # 100% deletion blind rate in this table — an alarming
        # number for a market we deliberately stopped
        # harvesting. Read the exclusion from one place rather
        # than deleting the file, so the history stays.
        if not is_active(mkt):
            continue
        w = json.loads(f.read_text(encoding="utf-8")).get("windows") or {}
        rows, n_del, n_del_blind = [], 0, 0
        for v in w.values():
            act = v.get("action")
            if act == "DEL":
                n_del += 1
            if v.get("px"):
                continue
            if act == "DEL":
                n_del_blind += 1
            code = str(v.get("code", "")).strip()
            base = code.lstrip("0") or code
            reg = regs.get(mkt)
            if reg is not None:
                gone = not (code in reg or base in reg)
                ev = ("absent from the exchange's live listed "
                      "register" if gone else
                      "STILL LISTED — the gap is ours, not a "
                      "delisting (ticker or source problem)")
                strength = "register"
            else:
                gone, strength = True, "weak"
                ev = ("no price data and no reachable exchange "
                      "register — could be a delisting OR a "
                      "ticker we spelled wrong")
            rev = v.get("rev")
            rows.append({
                "code": code, "name": v.get("name"),
                "review": rev, "action": act,
                "ann": cal.get(rev, (None, None))[0],
                "eff": cal.get(rev, (None, None))[1],
                "likely_delisted": gone,
                "evidence": ev, "evidence_strength": strength})
        # write the verdict back so the harvester knows what to
        # stop asking for — otherwise every run re-fetches names
        # the exchange has already told us are gone
        if regs.get(mkt) is not None:
            wj = json.loads(f.read_text(encoding="utf-8"))
            ch = 0
            for k, v in wj["windows"].items():
                if v.get("px"):
                    continue
                c2 = str(v.get("code", "")).strip()
                b2 = c2.lstrip("0") or c2
                if not (c2 in regs[mkt] or b2 in regs[mkt]):
                    v["confirmed_delisted"] = True
                    v["delisted_evidence"] = (
                        "absent from the exchange's live listed "
                        "register")
                    ch += 1
            if ch:
                f.write_text(json.dumps(wj), encoding="utf-8")
                print(f"  {mkt}: stamped {ch} confirmed-delisted")
        out[mkt] = rows
        tally[mkt] = {
            "movers_without_data": len(rows),
            "deletion_events": n_del,
            "deletion_events_blind": n_del_blind,
            "deletion_blind_rate": (round(n_del_blind / n_del, 3)
                                    if n_del else None)}
    p = ROOT / "data" / "apac_delisted_movers.json"
    p.write_text(json.dumps(
        {"generated": dt.date.today().isoformat(),
         "why": "movers we could not price. Kept as a list so a "
                "deletion study can state its blind spot rather "
                "than inherit it silently.",
         "summary": tally, "markets": out}, indent=1),
        encoding="utf-8")
    print(f"\n{'market':12} {'no data':>8} {'DEL blind':>10} "
          f"{'DEL rate':>9}")
    for m, t in sorted(tally.items()):
        r = t["deletion_blind_rate"]
        print(f"{m:12} {t['movers_without_data']:>8} "
              f"{t['deletion_events_blind']:>10} "
              f"{(f'{r:.0%}' if r is not None else '-'):>9}")
    print(f"\n-> {p.name}")
    return tally


def status():
    """Report only. c-196: this used to be the DEFAULT command,
    so `py scripts\\apac_event_days.py` with no argument printed
    a table and harvested nothing — while looking exactly like a
    finished run. I told Bill that bare command would re-harvest
    every market; it never did. The stored windows still carry
    ~18 pre-announcement sessions and close-only rows, i.e. the
    pre-c-192 shape, because no harvest has run since.
    The default is now `all`, and status says what it is."""
    print("STATUS ONLY — no data fetched. Use `all` to harvest.\n")
    print(f"{'market':12} {'w/ data':>9} {'pre-sess':>9} "
          f"{'OHLC':>6}  window shape")
    for p in sorted(DIR.glob("*.json")):
        if not is_active(p.stem):
            continue
        w = json.loads(p.read_text(encoding="utf-8"))["windows"]
        px = [v for v in w.values() if v.get("px")]
        if not px:
            print(f"{p.stem:12} {0:>4}/{len(w):<4}")
            continue
        pre = sorted(sum(1 for r in v["px"] if r["d"] <= v["ann"])
                     for v in px)
        med = pre[len(pre) // 2]
        ohlc = sum(1 for v in px if "o" in v["px"][0]) / len(px)
        shape = ("current" if med >= 28 and ohlc > 0.99
                 else "STALE — re-harvest for the 30-session "
                      "pre-window and OHLC")
        print(f"{p.stem:12} {len(px):>4}/{len(w):<4} {med:>9} "
              f"{ohlc:>5.0%}  {shape}")


def _windows_for(mkt):
    """Every stored window for a market, whoever harvested it."""
    if mkt in ELSEWHERE:
        p = ROOT / ELSEWHERE[mkt][0]
    else:
        p = DIR / f"{mkt}.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))["windows"]
    except Exception:                              # noqa: BLE001
        return {}


def coverage():
    """Do we have a daily window for every index mover? (c-223)

    Bill asked whether the daily OHLC harvest is complete, and
    the only way to answer it was to read several hundred lines
    of console output and notice what was NOT printed. That is
    not a check, it is a memory test, and it failed: China
    scrolled past by being absent.

    This compares the changes DB against what is on disk and
    prints the command that closes each gap.
    """
    import importlib
    sys.path.insert(0, str(ROOT / "scripts"))
    mkts = importlib.import_module("markets")
    rows, gap_cmd = [], []
    for m in sorted(set(YF_MARKETS) | set(ELSEWHERE)
                    | {"India"}):
        mv = movers(m)
        w = _windows_for(m)
        keys = {f"{rev}|{str(t).split('.')[0]}"
                for rev, t, _a, _n in mv}
        priced = sum(1 for k in keys if (w.get(k) or {}).get("px"))
        miss = len(keys) - priced
        why = ""
        if not mkts.is_active(m):
            why = f"EXCLUDED — {mkts.why_excluded(m) or ''}"[:44]
        elif m in ELSEWHERE:
            why = f"via {ELSEWHERE[m][1].split('(')[0].strip()}"
        elif miss == len(keys) and keys:
            why = "NEVER HARVESTED"
            gap_cmd.append(f"py scripts\\apac_event_days.py "
                           f"yf {m}")
        elif miss:
            why = "individual names — see `gaps`"
        rows.append((m, len(keys), priced, miss, why))
    print(f"{'market':12} {'movers':>7} {'priced':>7} "
          f"{'missing':>8}  note")
    for m, n, p, miss, why in rows:
        print(f"{m:12} {n:>7} {p:>7} {miss:>8}  {why}")
    # c-259: EXCLUDED MARKETS DO NOT SIT IN THE HEADLINE.
    # Bill: "Philippines stays excluded and should be named as
    # excluded wherever APAC totals are quoted, not folded into
    # a 97.6%." Folding 14 unreachable windows into the
    # denominator states a coverage rate for a market we have
    # decided not to cover, which flatters and misleads at the
    # same time — the rate looks worse than the harvest and
    # better than the truth for anyone reading it as "APAC".
    ex = [r for r in rows if r[4].startswith("EXCLUDED")]
    inc = [r for r in rows if not r[4].startswith("EXCLUDED")]
    tn = sum(r[1] for r in inc)
    tp = sum(r[2] for r in inc)
    if tn:
        print(f"{'TOTAL':12} {tn:>7} {tp:>7} {tn - tp:>8}  "
              f"{tp / tn:.0%} priced, EXCLUDED markets not "
              f"counted")
    for m, n, _p, _miss, _w in ex:
        print(f"  excluded from the total: {m} ({n} windows) "
              f"— no usable source")
    if gap_cmd:
        print("\nWHOLE MARKETS MISSING — run these:")
        for c in dict.fromkeys(gap_cmd):
            print(f"  {c}")
    print("\n  `movers` counts index changes since 2015 that "
          "carry a ticker. A window is `priced` when it holds "
          "at least one OHLC row.")
    print("  A missing window is not always missing DATA — see "
          "`gaps`, which separates a bad ticker from an absent "
          "price history.")


def gaps(market=None):
    """Every unpriced window, with what was already tried.

    c-223. The residue after a full run is a dozen individual
    names, and each needs a different answer — a predecessor
    ticker, a delisting, a hybrid line that is not really an
    equity. Printing them together with their attempted symbols
    is what makes that triage possible; a count does not.
    """
    tally = {}
    for m in ([market] if market else
              sorted(set(YF_MARKETS) | {"India"})):
        w = _windows_for(m)
        bad = [v for v in w.values() if not (v.get("px") or [])]
        if not bad:
            continue
        print(f"\n{m}: {len(bad)} unpriced of {len(w)}")
        first = _first_seen(m)
        for v in sorted(bad, key=lambda x: str(x.get("rev"))):
            tried = v.get("tried_symbols") or [v.get("yf_symbol")]
            flag = (" CONFIRMED-DELISTED"
                    if v.get("confirmed_delisted") else "")
            cls = _why_unpriced(m, v, tried, first)
            tally[cls] = tally.get(cls, 0) + 1
            print(f"    {str(v.get('rev')):6} "
                  f"{str(v.get('code'))[:14]:14} "
                  f"{str(v.get('action')):3} "
                  f"{str(v.get('name'))[:26]:26} "
                  f"tried {', '.join(str(t) for t in tried)}"
                  f"{flag}   [{cls}]")
    if tally:
        print("\n  by cause:")
        for c, n in sorted(tally.items(), key=lambda x: -x[1]):
            print(f"    {c:16} {n:>4}   {_CAUSE[c]}")


# c-259, Bill: "treat the 14 China missing rows as a ticker
# defect, not as absent market data, in every downstream
# count." Right, and the distinction is not cosmetic — one is
# a limit of the world and the other is a bug we own. Counting
# them together makes our own defects look like nature.
_CAUSE = {
    "TICKER_DEFECT": "the code we asked for is not this "
                     "company's — fixable by us",
    "NO_TICKER": "no code was ever resolved for the name",
    "DELISTED": "the security is gone and the vendor dropped "
                "its history",
    "NO_SOURCE": "the market has no usable source at all",
    "UNEXPLAINED": "attempted, empty, no cause established",
}
# boards that did not exist before these dates. A code from one
# of them, quoted for an earlier review, cannot be the right
# code — this is provable from the calendar alone and needs no
# external listings file.
_BOARD_BORN = {"688": "2019-07-22", "301": "2020-08-24",
               "689": "2019-07-22"}


def _first_seen(market):
    """{code: earliest date we hold ANY bar for it}.

    c-259. The board-birth rule below proves an anachronism
    only when the whole BOARD post-dates the review. It misses
    the commoner case: a code on an old board that simply
    listed later than the window. That is provable from our own
    files and needs no external listings source — if a code
    returns bars in a later review and its earliest bar starts
    after this window closed, the code did not exist yet, so it
    cannot be this row's security.
    """
    out = {}
    for k, v in (_windows_for(market) or {}).items():
        code = k.split("|", 1)[-1]
        rows = v.get("px") or []
        ds = [str(r.get("d"))[:10] for r in rows
              if isinstance(r, dict) and r.get("d")]
        if ds:
            d = min(ds)
            if code not in out or d < out[code]:
                out[code] = d
    return out


def _why_unpriced(market, v, tried, first=None):
    import markets as _mk
    if not _mk.is_active(market):
        return "NO_SOURCE"
    syms = [str(t) for t in tried if t and str(t) != "None"]
    if not syms:
        return "NO_TICKER"
    if v.get("confirmed_delisted"):
        return "DELISTED"
    rev = str(v.get("rev") or "")
    cal = calendar()
    ann, eff = (cal.get(rev) or ("", "", ""))[:2]
    for s in syms:
        head = s.split(".")[0][:3]
        born = _BOARD_BORN.get(head)
        if born and ann and ann < born:
            return "TICKER_DEFECT"          # board did not exist
        fs = (first or {}).get(s.split(".")[0])
        if fs and eff and fs > eff:
            return "TICKER_DEFECT"          # code listed later
    return "UNEXPLAINED"


def harvest_all():
    """Every market, each isolated from the others.

    c-200: the previous version called harvest_in() and then
    harvest_yf() with nothing between them, so a read timeout on
    ONE NSE day-file raised out of India, out of harvest_all,
    and out of the process — and the ten Yahoo markets never
    started. India is the slowest and most fragile stage AND it
    ran first, which is the worst possible ordering for that
    failure mode.

    Now each stage is caught and reported, the run continues,
    and a summary at the end names what did not finish rather
    than leaving it to be inferred from a stack trace.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    from markets import filter_markets
    # c-205: China added. It was the one MSCI APAC market with
    # no daily coverage at all, which left the website's
    # cross-market comparison silently missing the largest
    # sample in the database (1,431 movers) and the 5-minute
    # and daily datasets covering different markets.
    yf_markets = filter_markets(YF_MARKETS)
    print("markets this run: " + ", ".join(yf_markets)
          + "  (+ India via NSE bhavcopy)", flush=True)
    problems = []
    # Yahoo first: ten markets, fast, and independent of NSE.
    for mkt in yf_markets:
        try:
            harvest_yf([mkt])
        except Exception as e:                     # noqa: BLE001
            problems.append(f"{mkt}: {type(e).__name__} "
                            f"{str(e)[:90]}")
            print(f"!! {mkt} FAILED — continuing", flush=True)
    try:
        harvest_in()
    except Exception as e:                         # noqa: BLE001
        problems.append(f"India: {type(e).__name__} "
                        f"{str(e)[:90]}")
        print("!! India FAILED — continuing", flush=True)
    try:
        delisted()
    except Exception as e:                         # noqa: BLE001
        problems.append(f"delisted register: {type(e).__name__}")
    if problems:
        print("\nSTAGES THAT DID NOT COMPLETE — everything is "
              "resumable, re-run to pick up:")
        for p in problems:
            print(f"  {p}")
    else:
        print("\nall stages completed")


if __name__ == "__main__":
    a = sys.argv[1:]
    cmd = a[0] if a else "all"
    if cmd == "all":
        harvest_all()
    elif cmd == "delisted":
        delisted()
    elif cmd == "in":
        harvest_in()
    elif cmd == "yf":
        # c-194: market list comes from the CENTRAL exclusion
        # (scripts/markets.py), so the Philippines drops out
        # here for the same recorded reason it drops out of the
        # size screen — no usable data source — rather than by
        # someone remembering to delete it from a literal list.
        sys.path.insert(0, str(ROOT / "scripts"))
        from markets import filter_markets
        # c-269: refuse at the ARGUMENT, not just at the write.
        # `_save` catches it too, but by then the run has spent
        # 136 requests finding out.
        for m in a[1:]:
            refuse_if_elsewhere(m)
        harvest_yf(a[1:] or filter_markets(YF_MARKETS))
    elif cmd == "coverage":
        coverage()
    elif cmd == "gaps":
        gaps(a[1] if len(a) > 1 else None)
    else:
        status()
