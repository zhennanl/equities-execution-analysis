"""How far back does IBKR serve 5-minute bars? (c-201)

NOT MSCI. MSCI publishes the index changes — who was added,
who was deleted, on what date. It sells no price history at
all. Every bar in this project comes from IBKR, Yahoo, or an
exchange's own day-files, and the boundary being measured here
is IBKR's. Worth keeping straight, because the two have
completely different failure modes: an MSCI gap means we do not
know an event happened, an IBKR gap means we cannot see how it
traded.

WHY A SEPARATE SCRIPT FROM `ib_5m_events.py edges`. That one
bisects with ONE symbol per market between today and a
hard-coded floor. Three weaknesses, each of which can produce a
confident wrong answer:

  1. ONE SYMBOL CANNOT SEPARATE TWO THINGS. If Toyota returns
     nothing before 2010, that is either IBKR's floor or the
     limit of Toyota's own record. A single probe conflates the
     STOCK's history with the VENDOR's. Three symbols of
     different listing vintages separate them: if all three
     stop at the same date it is the vendor; if they stop at
     different dates the earliest is the vendor's floor and the
     others are listing dates.

  2. THE FLOOR WAS OUR OWN PARAMETER. Five markets reported
     "reaches at least 2010-01-01" — which measured where we
     stopped looking, not where IBKR stops. That artificial
     floor then became a real one downstream, because jobs()
     drops any review announced before the recorded edge. This
     script has no fixed floor: it walks BACKWARDS in doubling
     steps until a probe actually fails, and only then bisects.
     If nothing fails by 1998 it says so plainly rather than
     reporting the search limit as a finding.

  3. NO CONFIRMATION. A bisection returns a date whether or not
     the date means anything. Here the answer is re-tested from
     both sides — no bars shortly before, bars shortly after —
     and an edge that fails its own confirmation is recorded as
     UNCONFIRMED rather than published.

WHAT AN EMPTY RESPONSE MEANS, which is the trap this project
has fallen into twice. Near its boundary IBKR answers "No
market data permissions for TAI STK" and further back "HMDS
query returned no data" — the first reads like an entitlement
problem and is not one. So the raw error text at the boundary
is captured and reported, never summarised to "empty".

VENUES, not markets. Taiwan has two boards with edges two and a
half years apart, and MSCI China spans Shanghai, Shenzhen and
Hong Kong. Measuring per market would average away exactly the
differences that decide what the study can cover.

RUNS ON BILL'S MACHINE — TWS or IB Gateway, API enabled.
Read-only: it places no orders and changes no settings.

Usage:
  python scripts\\ib_5m_boundary.py                (every venue)
  python scripts\\ib_5m_boundary.py Japan HongKong
Out: data/ib_5m_boundary.json
"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "data" / "ib_5m_boundary.json"
HOST, PORTS = "127.0.0.1", (7497, 7496, 4001, 4002)

try:
    from ib_5m_events import _pace
    PACE = _pace()
except Exception:                                  # noqa: BLE001
    PACE = 1.0

# Three probes per venue, deliberately of DIFFERENT vintages so
# a listing date cannot masquerade as a vendor floor. The
# comment on each is its approximate listing year.
VENUES = {
    "Taiwan":       ("TWSE", "TWD",
                     [("1301", "Formosa Plastics ~1964"),
                      ("2317", "Hon Hai ~1991"),
                      ("2330", "TSMC ~1994")]),
    "Taiwan_TPEx":  ("TPEX", "TWD",
                     [("6488", "GlobalWafers ~2015"),
                      ("3105", "Win Semiconductors ~2011"),
                      ("5274", "ASPEED ~2013")]),
    "Japan":        ("TSEJ", "JPY",
                     [("7203", "Toyota ~1949"),
                      ("6758", "Sony ~1958"),
                      ("8306", "MUFG ~2001")]),
    # c-204: NOT zero-padded. All three probes came back "NO
    # CONTRACT" on 0005/0941/0700, while the c-190 probe
    # resolved plain "700". IB wants the bare number for SEHK;
    # YAHOO wants it padded to four digits ("0700.HK"). Two
    # systems, opposite conventions, and I carried the Yahoo
    # habit into the IB code.
    "HongKong":     ("SEHK", "HKD",
                     [("5", "HSBC ~1866"),
                      ("941", "China Mobile ~1997"),
                      ("700", "Tencent ~2004")]),
    "Korea":        ("KRX", "KRW",
                     [("005930", "Samsung Elec ~1975"),
                      ("005380", "Hyundai Motor ~1974"),
                      ("000660", "SK Hynix ~1996")]),
    "Singapore":    ("SGX", "SGD",
                     [("Z74", "Singtel ~1993"),
                      ("O39", "OCBC ~1970s"),
                      ("D05", "DBS ~1968")]),
    "Australia":    ("ASX", "AUD",
                     [("BHP", "BHP ~1885"),
                      ("CBA", "CommBank ~1991"),
                      ("CSL", "CSL ~1994")]),
    "India":        ("NSE", "INR",
                     [("RELIANCE", "Reliance ~1977"),
                      ("INFY", "Infosys ~1993"),
                      ("HINDUNILVR", "HUL ~1956")]),
    "China_SH":     ("SEHKNTL", "CNH",
                     [("600519", "Moutai ~2001"),
                      ("600036", "China Merchants Bk ~2002"),
                      ("601398", "ICBC ~2006")]),
    "China_SZ":     ("SEHKSZSE", "CNH",
                     [("000001", "Ping An Bank ~1991"),
                      ("000002", "Vanke ~1991"),
                      ("000333", "Midea ~2013")]),
    # c-225: two boards we did not know were separate IB venues
    # until the pre-flight resolved 300620 on CHINEXT and 688313
    # on SEHKSTAR rather than on Shenzhen and Shanghai. 256 of
    # China's 1,333 windows sit here with NO MEASURED FLOOR, so
    # they currently inherit Shanghai's (2014-11-14) — which is
    # certainly wrong for STAR, a board that did not open until
    # July 2019. An inherited floor that is too early produces
    # empty chunks that the audit files as `venue_no_history`:
    # a false measured-absence, the exact failure this whole
    # boundary file exists to prevent. Measure them.
    # c-227: 28 Korean windows ride on this, and the evidence so
    # far is suggestive rather than measured:
    #
    #   * all three pre-flight probes on genuinely KOSDAQ names
    #     (Enchem, Celltrion Pharm, Kumyang) resolved contracts
    #     and returned zero bars
    #   * every genuinely KOSDAQ window in the harvest is empty
    #   * the two ".KQ" windows that DID return bars — HMM and
    #     Hyundai Wia — are KOSPI companies mislabelled in our
    #     ticker map, so they are evidence about our suffix
    #     field, not about KOSDAQ
    #
    # That reads like "IB serves no KOSDAQ 5m history", which is
    # exactly the sentence I got wrong about TPEx at c-197 by
    # generalising from two failures. Measure it before 28
    # windows are stamped as absences.
    "Korea_KOSDAQ": ("KRX", "KRW",
                     [("035760", "CJ ENM ~1999"),
                      ("086520", "Ecopro ~2007"),
                      ("096530", "Seegene ~2010")]),
    "China_ChiNext": ("CHINEXT", "CNH",
                      [("300750", "CATL ~2018"),
                       ("300059", "East Money ~2010"),
                       ("300760", "Mindray ~2018")]),
    "China_STAR":   ("SEHKSTAR", "CNH",
                     [("688981", "SMIC ~2020"),
                      ("688111", "Kingsoft Office ~2019"),
                      ("688036", "Transsion ~2019")]),
}

# Doubling walk back from today, in years. Stops at the first
# step that returns nothing; 28 reaches 1998, older than any
# electronic intraday archive we have reason to expect.
STEPS_Y = [1, 2, 4, 8, 12, 16, 20, 24, 28]

_ERRORS = []


def _hook(ib):
    def on_err(reqId, code, msg, contract=None):
        _ERRORS.append((code, str(msg)[:200]))
    try:
        ib.errorEvent += on_err
    except Exception:                              # noqa: BLE001
        pass


def _connect():
    try:
        from ib_async import IB
    except ImportError:
        raise SystemExit("pip install ib_async")
    # c-208: random client id per run. A fixed id collides with
    # a session TWS is still holding from a previous script and
    # reports Error 326, which the old loop mistook for "no
    # gateway on this port" and then blamed the port list for.
    import random
    ib = IB()
    saw_326 = False
    for _ in range(4):
        cid = random.randint(200, 9990)
        for port in PORTS:
            try:
                ib.connect(HOST, port, clientId=cid, timeout=8)
                print(f"connected 127.0.0.1:{port} "
                      f"(clientId {cid})   pacing {PACE}s")
                _hook(ib)
                return ib
            except Exception as e:                 # noqa: BLE001
                if "326" in str(e) or "already in use" in str(e):
                    saw_326 = True
    raise SystemExit(
        "TWS refused every client id (Error 326 — a previous "
        "session is still held; restart TWS)." if saw_326 else
        f"no TWS/Gateway listening on {PORTS}")


def _contract(ib, exch, ccy, sym):
    from ib_async import Stock
    for ex in (exch, ""):
        try:
            det = ib.reqContractDetails(Stock(sym, ex, ccy))
        except Exception:                          # noqa: BLE001
            det = None
        if det:
            return det[0].contract
        time.sleep(0.3)
    return None


def _has(ib, con, on_date):
    """Any 5m bars in the 10 days ending on_date?

    TEN days, not one. A single date proves nothing — it may be
    a Sunday, Golden Week, Lunar New Year or Diwali. Ten
    calendar days always contains trading sessions in every
    market here, so an empty answer is about availability rather
    than the calendar.
    """
    before = len(_ERRORS)
    try:
        b = ib.reqHistoricalData(
            con, endDateTime=on_date.strftime("%Y%m%d")
            + "-23:59:59", durationStr="10 D",
            barSizeSetting="5 mins", whatToShow="TRADES",
            useRTH=True, formatDate=1)
    except Exception:                              # noqa: BLE001
        b = []
    time.sleep(PACE)
    err = _ERRORS[-1] if len(_ERRORS) > before else None
    return bool(b), len(b or []), err


def probe_symbol(ib, exch, ccy, sym, label, verbose=True):
    """Earliest date this ONE symbol returns 5m bars."""
    rec = {"symbol": sym, "note": label}
    con = _contract(ib, exch, ccy, sym)
    if not con:
        rec["result"] = "NO CONTRACT"
        return rec
    rec["resolved"] = (f"{con.symbol}@"
                       f"{con.primaryExchange or con.exchange}")
    today = dt.date.today() - dt.timedelta(days=7)
    ok, n, err = _has(ib, con, today)
    if not ok:
        # Not a boundary. A symbol with no bars AT THE PRESENT
        # DAY is an entitlement or contract problem, and no
        # amount of searching backwards will find an edge.
        rec.update(result="NO DATA EVEN NOW",
                   interpretation="entitlement or wrong "
                                  "contract, NOT a history "
                                  "boundary — the present day "
                                  "cannot be out of range",
                   error=str(err))
        if verbose:
            print(f"      {sym:11} no data even now — {err}")
        return rec

    # ---- 1. walk back until something fails --------------
    lo = hi = today
    walked = []
    for yrs in STEPS_Y:
        cand = today - dt.timedelta(days=365 * yrs)
        ok, n, err = _has(ib, con, cand)
        walked.append({"date": cand.isoformat(), "bars": n})
        if verbose:
            print(f"      {sym:11} -{yrs:>2}y {cand}  "
                  f"{'DATA ' + str(n) if ok else 'none'}")
        if ok:
            hi = cand
        else:
            lo = cand
            break
    else:
        rec.update(result="NO BOUNDARY FOUND",
                   reaches_at_least=hi.isoformat(),
                   walk=walked,
                   interpretation=f"still returning bars at "
                                  f"{hi} — the search stopped, "
                                  f"IBKR did not")
        if verbose:
            print(f"      {sym:11} -> no boundary by {hi}")
        return rec

    # ---- 2. bisect the bracket ---------------------------
    boundary_err = None
    steps = 0
    while (hi - lo).days > 3:
        mid = lo + (hi - lo) / 2
        ok, n, err = _has(ib, con, mid)
        if ok:
            hi = mid
        else:
            lo = mid
            boundary_err = err
        steps += 1
    if verbose:
        print(f"      {sym:11} -> edge {lo} .. {hi} "
              f"({len(walked) + steps} requests)")

    # ---- 3. confirm from both sides ----------------------
    before_ok, _, _ = _has(ib, con, lo - dt.timedelta(days=20))
    after_ok, _, _ = _has(ib, con, hi + dt.timedelta(days=20))
    confirmed = (not before_ok) and after_ok
    rec.update(
        result="EDGE" if confirmed else "EDGE UNCONFIRMED",
        no_data_on_or_before=lo.isoformat(),
        data_by=hi.isoformat(),
        walk=walked, bisection_steps=steps,
        confirmation={"20d_earlier_has_data": before_ok,
                      "20d_later_has_data": after_ok},
        boundary_error=str(boundary_err) if boundary_err
        else None)
    if not confirmed and verbose:
        print(f"      {sym:11} !! confirmation failed "
              f"(before={before_ok}, after={after_ok})")
    return rec


def boundary(venues=None, verbose=True):
    names = venues or list(VENUES)
    est = len(names) * 3 * 22
    print(f"  {len(names)} venues x 3 probe symbols, "
          f"~{est} requests, ~{est * PACE / 60:.0f} min pacing "
          f"(IB response time on top).")
    print("  Walking back in doubling steps, then bisecting, "
          "then confirming from both sides.\n", flush=True)
    ib = _connect()
    res = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for i, v in enumerate(names, 1):
        exch, ccy, probes = VENUES[v]
        print(f"\n[{i}/{len(names)}] {v}  ({exch}/{ccy})",
              flush=True)
        syms = []
        for sym, label in probes:
            syms.append(probe_symbol(ib, exch, ccy, sym, label,
                                     verbose))
        res[v] = _verdict(v, exch, syms)
        print(f"    => {res[v]['verdict']}", flush=True)
        OUT.write_text(json.dumps(res, indent=1),
                       encoding="utf-8")
    ib.disconnect()
    _report(res, names)
    print(f"\n-> {OUT.name}")
    return res


def _verdict(venue, exch, syms):
    """Turn three symbol results into one statement about IBKR.

    THE RULE, and why. The venue floor is the EARLIEST date any
    probe returns bars. A later date from another probe is
    evidence about that company, not about IBKR — a stock cannot
    have bars before it listed. So the minimum is the vendor
    floor and the spread between probes is the diagnostic: if
    all three agree, the floor is IBKR's and the answer is
    solid; if they disagree, the later ones are listing dates
    and should not be read as coverage limits.
    """
    edges = [s["data_by"] for s in syms if s.get("data_by")]
    none_now = [s for s in syms
                if s.get("result") == "NO DATA EVEN NOW"]
    unbounded = [s for s in syms
                 if s.get("result") == "NO BOUNDARY FOUND"]
    out = {"exchange": exch, "symbols": syms,
           "measured": dt.date.today().isoformat()}
    if len(none_now) == len(syms):
        out.update(edge=None, verdict=(
            "NO 5m DATA AT ALL on this venue — every probe "
            "failed at the PRESENT DAY, so this is entitlement "
            "or a wrong exchange code, not a history boundary"))
        return out
    if unbounded:
        deepest = min(s["reaches_at_least"] for s in unbounded)
        out.update(edge=deepest, edge_is_a_floor_we_hit=True,
                   verdict=(f"reaches at least {deepest} and "
                            f"was still returning bars when the "
                            f"search stopped — this is OUR "
                            f"limit, not IBKR's"))
        return out
    if not edges:
        out.update(edge=None,
                   verdict="inconclusive — no probe produced a "
                           "bracketed edge")
        return out
    first = min(edges)
    spread = (dt.date.fromisoformat(max(edges))
              - dt.date.fromisoformat(first)).days
    agree = spread <= 30
    unconf = [s["symbol"] for s in syms
              if s.get("result") == "EDGE UNCONFIRMED"]
    out.update(
        edge=first,
        per_symbol_edges={s["symbol"]: s.get("data_by")
                          for s in syms},
        spread_days=spread,
        verdict=(
            f"5m begins {first}"
            + ("  (all probes agree within a month — this is "
               "IBKR's floor)" if agree else
               f"  (probes disagree by {spread} days — the "
               f"earliest is the VENUE floor, but coverage "
               f"clearly varies by name, so per-window "
               f"coverage must be read from the bars, not "
               f"assumed from this date)")
            + (f"  UNCONFIRMED for {', '.join(unconf)}"
               if unconf else "")))
    return out


def _report(res, names):
    print("\n" + "=" * 74)
    print(f"{'venue':14}{'exchange':11}{'5m from':12}"
          f"{'spread':>7}  note")
    print("-" * 74)
    for v in names:
        r = res.get(v) or {}
        sp = r.get("spread_days")
        print(f"{v:14}{str(r.get('exchange','')):11}"
              f"{str(r.get('edge') or '--'):12}"
              f"{(str(sp) + 'd' if sp is not None else '--'):>7}"
              f"  {str(r.get('verdict',''))[:34]}")
    print("=" * 74)


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x in VENUES]
    bad = [x for x in sys.argv[1:] if x not in VENUES]
    if bad:
        raise SystemExit(f"unknown venue(s) {bad}. "
                         f"Choose from: {', '.join(VENUES)}")
    boundary(a or None)
