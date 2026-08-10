"""Probe candidate alternative-data endpoints and record what
they ACTUALLY return (c-264).

WHY A PROBE AND NOT A HARVESTER.

Twice in a fortnight this project wrote a fetcher against an
assumed format and got silence that looked like absence:

  c-232/261  TPEx was sent the ROC year when the endpoint
             wanted the Gregorian one. Every request returned
             "parameter input error", every window returned
             zero rows, and eighteen live OTC names read as
             delisted for months.
  c-261      The same endpoint reports volume in LOTS where
             TWSE reports SHARES. Fixing only the date would
             have put every OTC volume 1,000x too small into a
             dataset built to measure trade size against ADV.

Both were one HTTP request away from being obvious. So the
rule now is: **look at the response before writing a parser.**
This script makes that cheap and repeatable.

WHAT IT DOES
  * reads a registry of candidate sources, one per market;
  * fires ONE request each, politely;
  * records status, content type, size, and — this is the
    point — the SHAPE: JSON keys, the first row, or the HTML
    table headers;
  * writes the evidence to disk so a harvester can be written
    against something real.

It never parses for meaning and never writes to a dataset. It
answers exactly one question: *what comes back?*

MANUAL SOURCES. Anything needing a login, a captcha or a
browser session is marked `manual` in the registry and is not
requested. The registry entry carries the steps for a human
instead; run `py scripts\\altdata_probe.py manual` to print
them.

Usage
  py scripts\\altdata_probe.py                 probe everything
  py scripts\\altdata_probe.py Korea           one market
  py scripts\\altdata_probe.py manual          the by-hand list
  py scripts\\altdata_probe.py registry        show the registry

Output
  data/altdata_probe.json      what each endpoint returned
  docs/ALTDATA_PROBE.md        the readable report
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "data" / "altdata_registry.json"
OUT = ROOT / "data" / "altdata_probe.json"
DOC = ROOT / "docs" / "ALTDATA_PROBE.md"
UA = {"User-Agent": "Mozilla/5.0 (compatible; research)",
      "Accept": "application/json, text/html;q=0.9"}

# The six data TYPES a rebalance desk needs. Taiwan publishes
# all six; the value of any new source is which type it fills
# for a market that lacks it. See the question bank, Part 6.2.
TYPES = {
    1: "closing-auction microstructure",
    2: "securities borrowing / short balance",
    3: "investor-type net flow PER STOCK",
    4: "foreign ownership / foreign room",
    5: "turnover ratio (ATVR)",
    6: "price limits and halts",
}

# Seed registry. `url` is a template; `sample` fills it for the
# probe. Everything unproven is marked so — a source we have
# not seen respond is a hypothesis, not a plan.
SEED = {
    "Taiwan": [
        {"id": "twse_t86", "type": 3, "status": "HAVE",
         "what": "Three primary institutions net buy/sell by "
                 "stock, daily",
         "url": "https://www.twse.com.tw/rwd/zh/fund/T86"
                "?date={date}&selectType=ALL&response=json",
         "sample": {"date": "20260512"}},
        {"id": "twse_twt38u", "type": 3, "status": "HAVE",
         "what": "Foreign & investment trust net by stock",
         "url": "https://www.twse.com.tw/en/fund/TWT38U"
                "?date={date}&response=json",
         "sample": {"date": "20260512"}},
        {"id": "twse_twt93u", "type": 2, "status": "HAVE",
         "what": "Securities borrowing and lending balance",
         "url": "https://www.twse.com.tw/en/exchangeReport/"
                "TWT93U?date={date}&response=json",
         "sample": {"date": "20260512"}},
        {"id": "twse_qfiis", "type": 4, "status": "HAVE",
         "what": "Foreign shareholding ratio and foreign room",
         "url": "https://www.twse.com.tw/rwd/zh/fund/MI_QFIIS"
                "?date={date}&selectType=ALL&response=json",
         "sample": {"date": "20260512"}},
        {"id": "twse_fmsrfk", "type": 5, "status": "HAVE",
         "what": "Monthly turnover ratio, the ATVR input",
         "url": "https://www.twse.com.tw/rwd/zh/afterTrading/"
                "FMSRFK?date={date}&stockNo={code}&response=json",
         "sample": {"date": "20260101", "code": "2330"}},
        {"id": "twse_mi5mins", "type": 1, "status": "HAVE",
         "what": "5-minute index series",
         "url": "https://www.twse.com.tw/en/exchangeReport/"
                "MI_5MINS?date={date}&response=json",
         "sample": {"date": "20260512"}},
        {"id": "twse_mi_index_allbut", "type": 6,
         "status": "HAVE",
         "what": "Whole-board daily quotes with high/low, used "
                 "to detect a limit-locked session. A print "
                 "that jams against a limit is a failure to "
                 "execute, not a cost — the client does not "
                 "get filled at all.",
         "url": "https://www.twse.com.tw/rwd/en/afterTrading/"
                "MI_INDEX?date={date}&type=ALLBUT0999"
                "&response=json",
         "sample": {"date": "20260512"}},
    ],
    "Korea": [
        {"id": "krx_investor_by_issue", "type": 3,
         "status": "LIKELY",
         "what": "Investor-type net by issue, daily. The "
                 "single highest-value non-Taiwan target: it "
                 "replicates N1-N2 in a second market.",
         "url": "http://data.krx.co.kr/comm/bldAttendant/"
                "getJsonData.cmd",
         "note": "POST with bld=dbms/MDC/STAT/standard/"
                 "MDCSTAT02401 and a trdDd param. Confirm the "
                 "bld code by watching the site's own network "
                 "calls before writing a parser.",
         "manual": True},
        {"id": "krx_short_balance", "type": 2,
         "status": "LIKELY",
         "what": "Short-selling balance by issue, daily",
         "url": "http://data.krx.co.kr/comm/bldAttendant/"
                "getJsonData.cmd",
         "note": "Same loader, different bld code.",
         "manual": True},
    ],
    "HongKong": [
        {"id": "hkex_ccass", "type": 3, "status": "LIKELY",
         "what": "CCASS shareholding by participant, daily, "
                 "per stock. Nothing else in the region shows "
                 "WHICH custodian's holding changed, so passive "
                 "accumulation is directly observable.",
         "url": "https://www3.hkexnews.hk/sdw/search/"
                "searchsdw.aspx",
         "note": "ASP.NET form with __VIEWSTATE — needs a "
                 "session, not a plain GET. Script it with a "
                 "session that first fetches the form.",
         "manual": True},
        {"id": "hkex_short_turnover", "type": 2,
         "status": "LIKELY",
         "what": "Short-selling turnover by stock, daily",
         "url": "https://www.hkex.com.hk/eng/stat/smstat/"
                "ssturnover/ncms/SS{date}.htm",
         "sample": {"date": "260512"}},
    ],
    "China": [
        {"id": "connect_northbound", "type": 3,
         "status": "LIKELY",
         "what": "Stock Connect Northbound holdings per "
                 "A-share, daily. The closest thing to a "
                 "foreign/passive positioning series for the "
                 "mainland.",
         "url": "https://www3.hkexnews.hk/sdw/search/"
                "mutualmarket.aspx?t=sh&d={date}",
         "sample": {"date": "2026/05/12"}},
    ],
    "Japan": [
        {"id": "jpx_short_balance", "type": 2,
         "status": "LIKELY",
         "what": "Short-selling balance ratio by issue",
         "url": "https://www.jpx.co.jp/markets/statistics-"
                "equities/short-selling/index.html",
         "note": "Landing page lists dated files; resolve the "
                 "file list first."},
        {"id": "jpx_investor_type", "type": 3,
         "status": "RESEARCH",
         "what": "Trading by type of investors",
         "url": "https://www.jpx.co.jp/markets/statistics-"
                "equities/investor-type/index.html",
         "note": "CHECK GRANULARITY FIRST. Believed weekly and "
                 "BY MARKET, not by stock. If so it fails the "
                 "granularity test, cannot answer N1, and "
                 "should be recorded as unusable rather than "
                 "harvested."},
    ],
    "India": [
        {"id": "nse_delivery", "type": 3, "status": "LIKELY",
         "what": "Security-wise delivery position, daily. No "
                 "Taiwan equivalent: traded volume with flat "
                 "delivery is churn, not accumulation.",
         "url": "https://nsearchives.nseindia.com/archives/"
                "equities/mto/MTO_{date}.DAT",
         "sample": {"date": "12052026"}},
        {"id": "nse_bulk_deals", "type": 3, "status": "LIKELY",
         "what": "Bulk and block deals — occasionally names "
                 "the tracker outright",
         "url": "https://nsearchives.nseindia.com/content/"
                "equities/bulk.csv"},
    ],
    "Australia": [
        {"id": "asic_short", "type": 2, "status": "HAVE",
         "what": "Daily aggregated short positions, "
                 "delisted-safe",
         "url": "https://download.asic.gov.au/short-selling/"
                "RR{date}-001-SSDailyAggShortPos.csv",
         "sample": {"date": "20260512"}},
    ],
    "Thailand": [
        {"id": "set_nvdr", "type": 3, "status": "LIKELY",
         "what": "NVDR trading by stock — Thailand's foreign "
                 "flow instrument. There is no substitute.",
         "url": "https://www.set.or.th/en/market/product/"
                "stock/quotation/{code}/nvdr",
         "sample": {"code": "PTT"}},
    ],
    "Indonesia": [
        {"id": "idx_foreign_net", "type": 3, "status": "LIKELY",
         "what": "Foreign net buy/sell by stock, daily. "
                 "Indonesia is the violence outlier (p90 "
                 "13.9%), so attribution matters more here.",
         "url": "https://www.idx.co.id/primary/TradingSummary/"
                "GetStockSummary?date={date}",
         "sample": {"date": "20260512"}},
    ],
    "Singapore": [
        {"id": "sgx_short", "type": 2, "status": "LIKELY",
         "what": "Daily short-sell report by counter",
         "url": "https://links.sgx.com/1.0.0/short-sell/"
                "{date}"},
    ],
    "Malaysia": [
        {"id": "bursa_short", "type": 2, "status": "RESEARCH",
         "what": "Daily short-selling report",
         "url": "https://www.bursamalaysia.com/market_"
                "information/equities_prices"},
    ],
}


def registry():
    if REG.exists():
        try:
            return json.loads(REG.read_text(encoding="utf-8"))
        except Exception:                          # noqa: BLE001
            pass
    REG.write_text(json.dumps(SEED, indent=1), encoding="utf-8")
    return SEED


def _shape(text, ctype):
    """What did we actually get? Keys, first row, or headers."""
    t = (text or "").strip()
    if not t:
        return {"kind": "empty"}
    if t[:1] in "{[":
        try:
            j = json.loads(t)
        except Exception:                          # noqa: BLE001
            return {"kind": "json-like but unparseable",
                    "head": t[:200]}
        if isinstance(j, dict):
            out = {"kind": "json object", "keys": list(j)[:14]}
            for k in ("stat", "status", "message"):
                if k in j:
                    out[k] = str(j[k])[:80]
            for k, v in j.items():
                if isinstance(v, list) and v:
                    out["first_row_of_" + k] = str(v[0])[:220]
                    out["rows_in_" + k] = len(v)
                    break
            return out
        return {"kind": "json array", "n": len(j),
                "first": str(j[0])[:220] if j else None}
    if "<" in t[:200]:
        import re
        th = re.findall(r"<th[^>]*>(.*?)</th>", t,
                        re.S | re.I)[:12]
        tr = re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S | re.I)
        return {"kind": "html",
                "headers": [re.sub(r"<[^>]+>", " ", x).strip()
                            [:40] for x in th],
                "rows": len(tr)}
    return {"kind": "text/csv",
            "first_lines": t.splitlines()[:3]}


def probe(market=None):
    import requests
    reg = registry()
    res = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for mkt, items in reg.items():
        if market and mkt != market:
            continue
        print(f"\n{mkt}")
        for it in items:
            if it.get("manual"):
                print(f"  {it['id']:26s} MANUAL — "
                      f"{it.get('note', '')[:60]}")
                res.setdefault(mkt, {})[it["id"]] = {
                    **it, "probe": {"kind": "manual"}}
                continue
            url = it["url"]
            try:
                url = url.format(**(it.get("sample") or {}))
            except KeyError:
                print(f"  {it['id']:26s} SKIP — template needs "
                      f"parameters with no sample")
                continue
            try:
                r = requests.get(url, headers=UA, timeout=25)
                sh = _shape(r.text, r.headers.get(
                    "content-type", ""))
                rec = {"http": r.status_code,
                       "bytes": len(r.content),
                       "content_type": r.headers.get(
                           "content-type", "")[:40],
                       **sh}
                print(f"  {it['id']:26s} {r.status_code} "
                      f"{len(r.content):>8,}B  {sh.get('kind')}"
                      + (f"  stat={sh['stat']}"
                         if "stat" in sh else ""))
            except Exception as e:                 # noqa: BLE001
                rec = {"error": f"{type(e).__name__}: {e}"[:140]}
                print(f"  {it['id']:26s} ERROR {rec['error']}")
            res.setdefault(mkt, {})[it["id"]] = {**it,
                                                "probe": rec}
            time.sleep(1.5)
    OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False),
                   encoding="utf-8")
    report(res)


def manual():
    reg = registry()
    print("Sources that need a human. Do NOT automate these "
          "blind — each needs a session, a form or a login.\n")
    for mkt, items in reg.items():
        for it in items:
            if it.get("manual"):
                print(f"{mkt} — {it['id']}  "
                      f"[type {it['type']}: "
                      f"{TYPES[it['type']]}]")
                print(f"   what: {it['what']}")
                print(f"   url : {it['url']}")
                print(f"   how : {it.get('note', '')}\n")


def report(res=None):
    res = res or (json.loads(OUT.read_text(encoding="utf-8"))
                  if OUT.exists() else {})
    L = ["# Alternative-data probe", "",
         "*Generated by `scripts/altdata_probe.py`. This records "
         "what each endpoint RETURNED — not what we hoped it "
         "would. Write harvesters against this file, never "
         "against an assumed format; see the script header for "
         "the two occasions that rule was learned.*", "",
         "| market | source | type | status | result |",
         "|---|---|---|---|---|"]
    for mkt, items in sorted(res.items()):
        for sid, it in sorted(items.items()):
            p = it.get("probe", {})
            r = (p.get("error") or p.get("kind") or "")
            if p.get("http"):
                r = f"HTTP {p['http']} · {p.get('kind', '')}"
            if p.get("stat"):
                r += f" · stat={p['stat']}"
            L.append(f"| {mkt} | {sid} | {it.get('type')} | "
                     f"{it.get('status', '')} | {r} |")
    L += ["", "## The six data types", ""]
    for k, v in TYPES.items():
        L.append(f"{k}. **{v}**")
    L += ["", "Taiwan publishes all six. The value of any new "
              "source is which type it fills for a market that "
              "lacks it — see the question bank, Part 6.2.", ""]
    DOC.write_text("\n".join(L), encoding="utf-8")
    print(f"\n-> {DOC.name}")


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else None
    if a == "manual":
        manual()
    elif a == "registry":
        print(json.dumps(registry(), indent=1)[:4000])
    else:
        probe(a)
