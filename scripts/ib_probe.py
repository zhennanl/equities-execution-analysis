"""Does IBKR actually serve 5-minute bars for each APAC market?
A standalone diagnostic (c-185).

RUN THIS BEFORE PAYING FOR ANY SUBSCRIPTION.

WHAT IT ANSWERS, and why each part matters:

  1. CAN WE EVEN NAME THE CONTRACT? IB's exchange codes are not
     obvious (Shanghai A-shares are "SEHKNTL", not "SSE"). If
     the contract does not resolve, "no data" tells you nothing
     about entitlement — it just means we asked wrongly. So
     several candidate codes are tried per market and the one
     that resolves is recorded.

  2. TRADES OR ONLY QUOTES? Every APAC subscription on the IB
     price list is described as "top of book" — that is QUOTE
     data. Our bars use whatToShow="TRADES", i.e. last sale.
     On some exchanges a quote entitlement does NOT unlock
     trade history, and the failure is indistinguishable from
     "not subscribed" unless you test both. So both are tried.

  3. DO WE NEED TO PAY AT ALL? IB often serves HISTORICAL bars
     on a DELAYED entitlement, which is free. If the live
     request fails, the script retries with market data type 3
     (delayed) and 4 (delayed-frozen). A market that works
     delayed needs no subscription for back-study work — only
     for live trading. This is the single most valuable answer
     here and it costs nothing to get.

  4. HOW FAR BACK? A feed that only reaches one month cannot
     cover a 2023 event. Depth is probed with daily bars, which
     are cheap, and reported per market.

IB ERROR CODES you may see, and what they mean:
    200   no security definition -> wrong exchange code/symbol
    354   requested market data is not subscribed -> entitlement
    162   historical market data service error -> often pacing,
          sometimes "no data permission for this whatToShow"
    10197 no market data during competing live session -> you
          are logged into TWS elsewhere with the same user

SETUP
  1. Start TWS or IB Gateway and log in.
  2. File > Global Configuration > API > Settings:
     tick "Enable ActiveX and Socket Clients".
     Note the port: TWS live 7496, TWS paper 7497,
     Gateway live 4001, Gateway paper 4002.
  3. pip install ib_async
  4. python scripts\\ib_probe.py

Out: data/ib_probe_result.json + a summary table on stdout.
Read-only. It places no orders and changes no settings.
"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "ib_probe_result.json"
HOST = "127.0.0.1"
PORTS = (7497, 7496, 4001, 4002)

# Candidate IB exchange codes per market, tried in order, with a
# liquid probe symbol. Several are guesses — that is the point:
# the script reports which code actually resolved.
CANDIDATES = {
    "Taiwan":     ([("TWSE", "2330", "TWD"),
                    ("TAI", "2330", "TWD")], "TSMC"),
    "Japan":      ([("TSEJ", "7203", "JPY"),
                    ("SMART", "7203", "JPY")], "Toyota"),
    "HongKong":   ([("SEHK", "700", "HKD")], "Tencent"),
    # c-187: KSE/005930 did NOT resolve despite the account
    # holding the free Korea Equities Bundle. Entitlement and
    # CONTRACT RESOLUTION are different things — try the other
    # spellings IB uses for Korean listings.
    # c-190 MEASURED: "KSE" returns error 200 (no security
    # definition); "KRX" resolves and serves 390 bars with 15y
    # of daily depth. KRX first from now on.
    "Korea":      ([("KRX", "005930", "KRW"),
                    ("KSE", "005930", "KRW")], "Samsung Elec"),
    "Singapore":  ([("SGX", "D05", "SGD")], "DBS"),
    "Australia":  ([("ASX", "BHP", "AUD"),
                    ("CHIXAU", "BHP", "AUD")], "BHP"),
    "India":      ([("NSE", "RELIANCE", "INR")], "Reliance"),
    "Thailand":   ([("SET", "PTT", "THB")], "PTT"),
    "Malaysia":   ([("BURSA", "1155", "MYR"),
                    ("KLS", "1155", "MYR")], "Maybank"),
    "Indonesia":  ([("IDX", "BBCA", "IDR"),
                    ("JKT", "BBCA", "IDR")], "Bank Central Asia"),
    "NewZealand": ([("NZX", "SPK", "NZD"),
                    ("NZE", "SPK", "NZD")], "Spark NZ"),
    "China":      ([("SEHKNTL", "600519", "CNH"),
                    ("SEHKSZSE", "000333", "CNH")], "Moutai / Midea"),
}

# 1 live, 2 frozen, 3 delayed, 4 delayed-frozen
DATA_TYPES = [(1, "live"), (3, "delayed"), (4, "delayed-frozen")]


def connect():
    try:
        from ib_async import IB
    except ImportError:
        raise SystemExit(
            "ib_async is not installed.\n    pip install ib_async")
    ib = IB()
    errs = []
    for port in PORTS:
        try:
            ib.connect(HOST, port, clientId=91, timeout=8)
            print(f"connected: 127.0.0.1:{port}  "
                  f"server v{ib.client.serverVersion()}")
            return ib
        except Exception as e:                     # noqa: BLE001
            errs.append(f"{port}: {str(e)[:60]}")
    raise SystemExit(
        "could not reach TWS or IB Gateway on any of "
        f"{PORTS}\n  " + "\n  ".join(errs) +
        "\n\nStart TWS/Gateway, then File > Global Configuration"
        " > API > Settings > Enable ActiveX and Socket Clients.")


def _resolve(ib, cands):
    """First exchange code that yields a contract."""
    from ib_async import Stock
    for exch, sym, ccy in cands:
        try:
            det = ib.reqContractDetails(Stock(sym, exch, ccy))
            if det:
                return exch, sym, det[0].contract, None
        except Exception as e:                     # noqa: BLE001
            last = str(e)[:80]
        else:
            last = "no contract returned"
        time.sleep(0.6)
    return None, None, None, last


def _bars(ib, con, what, duration="5 D", size="5 mins"):
    try:
        b = ib.reqHistoricalData(
            con, endDateTime="", durationStr=duration,
            barSizeSetting=size, whatToShow=what,
            useRTH=True, formatDate=1)
        return (len(b), b[0].date if b else None,
                b[-1].date if b else None, None)
    except Exception as e:                         # noqa: BLE001
        return 0, None, None, str(e)[:110]


def probe_market(ib, market):
    cands, desc = CANDIDATES[market]
    rec = {"probe_company": desc, "tried_exchanges":
           [c[0] for c in cands]}
    exch, sym, con, err = _resolve(ib, cands)
    if not con:
        rec.update(contract="NOT RESOLVED", detail=err,
                   verdict="NO CONTRACT — exchange code or "
                           "symbol wrong, OR no trading "
                           "permission for this market")
        return rec
    rec.update(contract=f"{sym}@{exch}")
    # try live first, then delayed — the delayed result is what
    # tells us whether a subscription is actually required
    for mdt, label in DATA_TYPES:
        try:
            ib.reqMarketDataType(mdt)
        except Exception:                          # noqa: BLE001
            continue
        n, first, last, e = _bars(ib, con, "TRADES")
        rec[f"TRADES_{label}"] = (f"{n} bars" if n
                                  else f"none ({e or 'empty'})")
        time.sleep(1.0)
        if n:
            rec["works_with"] = label
            rec["first_bar"] = str(first)
            rec["last_bar"] = str(last)
            break
    # if TRADES never worked, is it a quote-only entitlement?
    if not rec.get("works_with"):
        ib.reqMarketDataType(3)
        n, _, _, e = _bars(ib, con, "MIDPOINT")
        rec["MIDPOINT_delayed"] = (f"{n} bars" if n
                                   else f"none ({e or 'empty'})")
        rec["verdict"] = (
            "QUOTE-ONLY — MIDPOINT bars exist but TRADES do "
            "not. A last-sale entitlement is needed; volume "
            "and auction prints will be missing."
            if n else
            "NO 5-MIN HISTORY on this account. See the error "
            "text: 354 = not subscribed, 162 = no permission "
            "for this data type or pacing.")
        return rec
    # DEPTH — a LADDER, not a single ask. c-187: the first
    # version asked for "5 Y" once. Five markets returned
    # exactly 5.00 years, i.e. they gave back the parameter,
    # not their limit. Taiwan returned EMPTY WITH NO ERROR,
    # because IB serves nothing at all when the requested
    # duration exceeds available history — it does not
    # truncate. So Taiwan looked broken when its data was
    # simply younger than the question.
    #
    # Walking DOWN finds any market whose history is short;
    # continuing UP past the first success finds the true edge
    # rather than stopping at whatever we happened to ask.
    rec["depth_ladder"] = {}
    best = None
    # c-190: HK/KR/SG/AU/IN all returned EXACTLY 15 years, i.e.
    # they hit the ceiling of the ladder, not their own limit.
    # Ceiling raised so the real edge can show itself.
    for dur in ("30 Y", "25 Y", "20 Y", "15 Y", "10 Y", "5 Y",
                "3 Y", "2 Y", "1 Y", "6 M", "3 M", "1 M"):
        n, first, _, e = _bars(ib, con, "TRADES",
                               duration=dur, size="1 day")
        rec["depth_ladder"][dur] = (f"{n} bars from {first}"
                                    if n else "empty")
        if n and best is None:
            best = (dur, str(first))
        time.sleep(1.0)
        if n and dur in ("2 Y", "1 Y", "6 M", "3 M", "1 M"):
            break        # short-history market: stop probing
    if best:
        rec["daily_depth_from"] = best[1]
        rec["depth_found_at"] = best[0]
        rec["depth_note"] = (
            "if this equals the duration asked, the TRUE depth "
            "may be longer — the ladder stopped at the first "
            "success from the top")
    else:
        rec["daily_depth_from"] = "no daily bars at any duration"
    rec["verdict"] = (
        f"OK via {rec['works_with']} data"
        + ("  (FREE — no subscription needed for history)"
           if rec["works_with"] != "live" else ""))
    return rec


def main():
    ib = connect()
    try:
        acct = ib.managedAccounts()
        print(f"accounts: {acct}")
    except Exception:                              # noqa: BLE001
        pass
    rows = {}
    for market in CANDIDATES:
        print(f"\n--- {market} ---", flush=True)
        try:
            rec = probe_market(ib, market)
        except Exception as e:                     # noqa: BLE001
            rec = {"verdict": f"PROBE CRASHED: {str(e)[:100]}"}
        rows[market] = rec
        for k, v in rec.items():
            print(f"    {k}: {v}")
        time.sleep(1.5)
    ib.disconnect()
    OUT.write_text(json.dumps(
        {"asof": dt.datetime.now().isoformat(timespec="seconds"),
         "note": "MEASURED on this account. Entitlements differ "
                 "by account and IB entity; re-run after any "
                 "subscription change.",
         "markets": rows}, indent=1), encoding="utf-8")
    print("\n" + "=" * 72)
    print(f"{'market':12} {'contract':16} {'works with':16} "
          f"{'history from':12}")
    print("-" * 72)
    for m, r in rows.items():
        print(f"{m:12} {str(r.get('contract', '--')):16} "
              f"{str(r.get('works_with', '--')):16} "
              f"{str(r.get('daily_depth_from', '--'))[:12]}")
    print("=" * 72)
    free = [m for m, r in rows.items()
            if r.get("works_with") in ("delayed", "delayed-frozen")]
    if free:
        print(f"\nNO SUBSCRIPTION NEEDED for history in: "
              f"{', '.join(free)}")
    print(f"\n-> {OUT.name}")


if __name__ == "__main__":
    main()
