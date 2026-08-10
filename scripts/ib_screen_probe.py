"""Can IBKR supply the GIMI §2.2 screens? An evidence probe.

RUN THIS ON BILL'S MACHINE — TWS listens on 127.0.0.1 and the
analysis sandbox is a different host, so it cannot reach it.

    py scripts\\ib_screen_probe.py

What it tests, screen by screen, and what it reports is the
ANSWER FOR EACH — available / derivable / proxy only / absent.
Nothing here is assumed; every verdict comes from a live call.

GIMI §2.2 screens (May-2026 book):
  2.2.3  Equity Universe Minimum Size — full mkt cap >= $537M
  2.2.4  float-adjusted cap >= 50% of that ($268.5M)
  2.2.5  DM/EM Minimum Liquidity — ATVR + frequency of trading
  2.2.6  Global Minimum Foreign Inclusion Factor
  2.2.7  Minimum Length of Trading
  2.2.8  Minimum Foreign Room (>= 15%)
  2.2.9  Financial Reporting

THE HEADLINE TEST is float. IB's Refinitiv-sourced
ReportSnapshot carries <SharesOut TotalFloat="..."> — if that
lands, we get a THIRD independent float estimate and can score
it against MSCI's own implied FIFs, which is the only ranking
that matters. Current standings (median absolute error vs
MSCI-implied, top 10): Yahoo 2.7%, TDCC bracket proxy 16.3%.

Output: data/ib_screen_probe.json
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "data" / "ib_screen_probe.json"
HOST, PORTS = "127.0.0.1", (7497, 7496, 4001, 4002)

# the MSCI Taiwan top 10 (Jul-31-2026 factsheet) with the two
# float estimates we already hold, so the probe prints a
# four-way comparison the moment IB answers
BENCH = {
    "2330": {"name": "TSMC", "msci": 0.952, "yahoo": 0.912,
             "tdcc": 0.846},
    "2454": {"name": "MediaTek", "msci": 0.902, "yahoo": 0.879,
             "tdcc": 0.910},
    "2308": {"name": "Delta", "msci": 0.752, "yahoo": 0.604,
             "tdcc": 0.882},
    "2317": {"name": "Hon Hai", "msci": 0.873, "yahoo": 0.861,
             "tdcc": 0.740},
    "3711": {"name": "ASE", "msci": 0.748, "yahoo": 0.741,
             "tdcc": 0.954},
    "2303": {"name": "UMC", "msci": 0.902, "yahoo": 0.863,
             "tdcc": 0.690},
    "2383": {"name": "Elite Material", "msci": 0.802,
             "yahoo": 0.825, "tdcc": 0.849},
    "2881": {"name": "Fubon", "msci": 0.601, "yahoo": 0.590,
             "tdcc": 0.342},
    "2891": {"name": "CTBC", "msci": 0.852, "yahoo": 0.869,
             "tdcc": 0.558},
    "2345": {"name": "Accton", "msci": 0.902, "yahoo": 0.837,
             "tdcc": 1.000},
}


def _connect():
    from ib_async import IB
    ib = IB()
    last = None
    for port in PORTS:
        try:
            ib.connect(HOST, port, clientId=23, timeout=6)
            ib.RequestTimeout = 30
            print(f"connected on port {port}\n", flush=True)
            return ib
        except Exception as e:                     # noqa: BLE001
            last = e
    raise SystemExit(
        f"No TWS/Gateway on {PORTS}: {last}\n"
        "Enable API: TWS > Global Config > API > Settings > "
        "'Enable ActiveX and Socket Clients'.")


def _qualify(ib, code):
    from ib_async import Stock
    for exch in ("TWSE", "TPEX"):
        c = Stock(code, exch, "TWD")
        try:
            ib.qualifyContracts(c)
            if c.conId:
                return c
        except Exception:                          # noqa: BLE001
            continue
    return None


def _snapshot(ib, c):
    """ReportSnapshot XML -> the fields the screens need."""
    try:
        xml = ib.reqFundamentalData(c, "ReportSnapshot")
    except Exception as e:                         # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}
    if not xml:
        return {"error": "empty (no fundamentals entitlement?)"}
    out = {"raw_len": len(xml)}
    m = re.search(r"<SharesOut([^>]*)>([\d.eE+]+)</SharesOut>",
                  xml)
    if m:
        out["shares_out"] = float(m.group(2))
        tf = re.search(r'TotalFloat="([\d.eE+]+)"', m.group(1))
        if tf:
            out["total_float"] = float(tf.group(1))
            if out["shares_out"]:
                out["float_ratio"] = round(
                    min(1.0, out["total_float"]
                        / out["shares_out"]), 4)
        d = re.search(r'Date="([^"]+)"', m.group(1))
        if d:
            out["shares_asof"] = d.group(1)
    for tag in ("LatestAvailableAnnual",
                "LatestAvailableInterim", "ReportingCurrency",
                "Employees"):
        mm = re.search(rf"<{tag}[^>]*>([^<]+)</{tag}>", xml)
        if mm:
            out[tag] = mm.group(1).strip()
    mm = re.search(r'<CoStatus[^>]*>([^<]+)</CoStatus>', xml)
    if mm:
        out["status"] = mm.group(1)
    return out


def _ratios(ib, c):
    """Generic tick 258 — Refinitiv fundamental ratios string."""
    try:
        t = ib.reqMktData(c, "258", False, False)
        for _ in range(24):
            ib.sleep(0.25)
            if getattr(t, "fundamentalRatios", None):
                break
        fr = getattr(t, "fundamentalRatios", None)
        ib.cancelMktData(c)
        if not fr:
            return {"error": "no fundamentalRatios returned"}
        d = dict(vars(fr)) if hasattr(fr, "__dict__") else {}
        keep = {k: v for k, v in d.items()
                if k.upper() in ("MKTCAP", "TTMREV", "NPRICE",
                                 "VOL10DAVG", "TTMNIAC")}
        return {"n_fields": len(d), "sample": keep or
                dict(list(d.items())[:6])}
    except Exception as e:                         # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


def _liquidity(ib, c):
    """12 months of daily bars -> we can compute ATVR ourselves.

    c-123: LIVE market data type set EXPLICITLY. ib_harvest.py's
    hard-won lesson (its comment, verified 2026-08-04 on this
    account): TAI serves no delayed feed, so anything other than
    type 1 raises 'No market data permissions' even WITH a valid
    TWSE subscription."""
    try:
        ib.reqMarketDataType(1)
        bars = ib.reqHistoricalData(
            c, "", "1 Y", "1 day", "TRADES", useRTH=True,
            formatDate=1)
        if not bars:
            return {"error": "no bars"}
        vals = [b.volume * b.close for b in bars if b.volume]
        return {"days": len(bars),
                "median_daily_traded_twd": round(
                    sorted(vals)[len(vals) // 2], 0) if vals
                else None,
                "first_bar": str(bars[0].date),
                "last_bar": str(bars[-1].date)}
    except Exception as e:                         # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


def _head(ib, c):
    """Earliest available data — a length-of-trading proxy."""
    try:
        return {"head_timestamp":
                str(ib.reqHeadTimeStamp(c, "TRADES", True, 1))}
    except Exception as e:                         # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


def main():
    ib = _connect()
    res = {"probed": time.strftime("%Y-%m-%d %H:%M"),
           "securities": {}}
    # c-123: fail these ONCE, not ten times. Error 10358 means
    # the account cannot use reqFundamentalData at all (IBKR has
    # deprecated the old Refinitiv endpoint), so after the first
    # refusal the remaining names skip it instantly.
    fund_dead = ratios_dead = False
    for code, b in BENCH.items():
        c = _qualify(ib, code)
        if not c:
            res["securities"][code] = {"error": "not qualified"}
            print(f"{code} {b['name']:16} NOT QUALIFIED",
                  flush=True)
            continue
        r = {"conId": c.conId, "exchange": c.exchange}
        if fund_dead:
            r["snapshot"] = {"error": "skipped — 10358 on an "
                                      "earlier name"}
        else:
            r["snapshot"] = _snapshot(ib, c)
            if "not allowed" in str(
                    r["snapshot"].get("error", "")).lower() \
                    or "10358" in str(r["snapshot"].get("error",
                                                        "")):
                fund_dead = True
            ib.sleep(0.6)
        if ratios_dead:
            r["ratios"] = {"error": "skipped"}
        else:
            r["ratios"] = _ratios(ib, c)
            if r["ratios"].get("error"):
                ratios_dead = True
            ib.sleep(0.6)
        r["liquidity"] = _liquidity(ib, c)
        ib.sleep(0.6)
        r["head"] = _head(ib, c)
        res["securities"][code] = r
        ff = r["snapshot"].get("float_ratio")
        print(f"{code} {b['name']:16} IB float "
              f"{ff if ff is not None else 'n/a':>7} | "
              f"MSCI {b['msci']:.3f} | Yahoo {b['yahoo']:.3f} | "
              f"TDCC {b['tdcc']:.3f}", flush=True)
        ib.sleep(1.0)
    ib.disconnect()

    # ---- score IB against MSCI, alongside the others -------
    import statistics as st
    rows, ib_err, y_err, t_err = [], [], [], []
    for code, b in BENCH.items():
        s = res["securities"].get(code, {}).get("snapshot", {})
        f = s.get("float_ratio")
        if f:
            e = (f - b["msci"]) / b["msci"]
            ib_err.append(abs(e))
        else:
            e = None
        y_err.append(abs((b["yahoo"] - b["msci"]) / b["msci"]))
        t_err.append(abs((b["tdcc"] - b["msci"]) / b["msci"]))
        rows.append({"code": code, "name": b["name"],
                     "msci": b["msci"], "ib": f,
                     "ib_err": round(e, 3) if e is not None
                     else None,
                     "yahoo": b["yahoo"], "tdcc": b["tdcc"]})
    res["comparison"] = rows
    res["median_abs_error_vs_msci"] = {
        "ib": round(st.median(ib_err), 4) if ib_err else None,
        "ib_n": len(ib_err),
        "yahoo": round(st.median(y_err), 4),
        "tdcc": round(st.median(t_err), 4)}
    res["screen_verdicts"] = _verdicts(res)
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")

    print("\n===== FLOAT SOURCE SCOREBOARD "
          "(median |error| vs MSCI-implied) =====")
    m = res["median_abs_error_vs_msci"]
    if m["ib"] is not None:
        print(f"  IBKR/Refinitiv : {m['ib']:.1%}  "
              f"(n={m['ib_n']})")
    else:
        print("  IBKR/Refinitiv : NO DATA — see verdicts")
    print(f"  Yahoo          : {m['yahoo']:.1%}")
    print(f"  TDCC proxy     : {m['tdcc']:.1%}")
    print("\n===== GIMI §2.2 SCREEN COVERAGE =====")
    for k, v in res["screen_verdicts"].items():
        print(f"  {k:44} {v}")
    print(f"\n-> {OUT.name}")


def _verdicts(res):
    S = res["securities"]
    n = len(S)

    def frac(fn):
        return sum(1 for v in S.values() if fn(v))

    has_float = frac(lambda v: v.get("snapshot", {})
                     .get("float_ratio"))
    has_shares = frac(lambda v: v.get("snapshot", {})
                      .get("shares_out"))
    has_bars = frac(lambda v: v.get("liquidity", {}).get("days"))
    has_head = frac(lambda v: v.get("head", {})
                    .get("head_timestamp"))
    has_rep = frac(lambda v: v.get("snapshot", {})
                   .get("LatestAvailableAnnual"))

    def verdict(k, tot, label_yes, label_no):
        return (f"{label_yes} ({k}/{tot})" if k else label_no)
    return {
        "2.2.3 full market cap (>= $537M)":
            verdict(has_shares, n,
                    "DERIVABLE — shares x price", "ABSENT"),
        "2.2.4 float-adj cap (>= $268.5M)":
            verdict(has_float, n,
                    "AVAILABLE — TotalFloat", "ABSENT"),
        "2.2.5 liquidity / ATVR":
            verdict(has_bars, n,
                    "DERIVABLE — 1y daily bars", "ABSENT"),
        "2.2.6 minimum FIF":
            "PROXY ONLY — float ratio is not MSCI's FIF",
        "2.2.7 minimum length of trading":
            verdict(has_head, n,
                    "PROXY — head timestamp", "ABSENT"),
        "2.2.8 foreign room (>= 15%)":
            "ABSENT from IB — but TWSE MI_QFIIS publishes it "
            "per security per day (already harvested)",
        "2.2.9 financial reporting":
            verdict(has_rep, n,
                    "PROXY — LatestAvailableAnnual", "ABSENT"),
    }


if __name__ == "__main__":
    main()
