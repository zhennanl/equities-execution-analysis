"""Separate DEAD tickers from real gaps, market by market
(c-178).

WHY. An unresolved ticker has two very different meanings and
the resolver cannot tell them apart on its own:
    "we failed to fetch this"     -> a bug to fix
    "there is nothing to fetch"   -> the company is delisted
Left mixed, the resolution rate never reaches 100%, and a
permanently-stuck counter is one you stop reading — which is
how a real regression slips past. Taiwan proved the point: 19
"missing" names were 14 counting artefacts and 5 genuine
delistings.

THE TEST, strongest evidence first:
  1. THE EXCHANGE'S OWN LIVE REGISTER, where one is reachable.
     Absence from it is a positive statement by the exchange
     that the security no longer trades. Available for Taiwan
     (TWSE + TPEx), Japan (JPX), Hong Kong (HKEX) and Shanghai
     (SSE — which even carries DELIST_DATE).
  2. Where no register is reachable, Yahoo silence is recorded
     as WEAK evidence and labelled as such. It is not proof;
     Yahoo's coverage has already been shown to be patchy in
     exactly the wrong places.

Run:  py scripts\\dead_ticker_sweep.py
Out:  data/dead_tickers.json  {market: {code: evidence}}
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "dead_tickers.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _reg_taiwan(s):
    out = set()
    for u, k in [("https://openapi.twse.com.tw/v1/opendata/"
                  "t187ap03_L", "公司代號"),
                 ("https://www.tpex.org.tw/openapi/v1/"
                  "mopsfin_t187ap03_O", "SecuritiesCompanyCode")]:
        for r in s.get(u, headers=UA, timeout=60).json():
            out.add(str(r[k]).strip())
    return out, "TWSE t187ap03_L + TPEx mopsfin_t187ap03_O"


def _reg_japan(s):
    import io
    import pandas as pd
    x = s.get("https://www.jpx.co.jp/markets/statistics-equities"
              "/misc/tvdivq0000001vg2-att/data_j.xls",
              headers=UA, timeout=90).content
    df = pd.read_excel(io.BytesIO(x))
    return ({str(c).strip() for c in df.iloc[:, 1]},
            "JPX data_j.xls")


def _reg_hk(s):
    import io
    import pandas as pd
    x = s.get("https://www.hkex.com.hk/eng/services/trading/"
              "securities/securitieslists/ListOfSecurities.xlsx",
              headers=UA, timeout=90).content
    df = pd.read_excel(io.BytesIO(x), header=2)
    col = df.columns[0]
    return ({str(v).strip().lstrip("0")
             for v in df[col].dropna()}, "HKEX ListOfSecurities")


def _reg_china(s):
    j = s.get("http://query.sse.com.cn/sseQuery/commonQuery.do"
              "?sqlId=COMMON_SSE_CP_GPJCTPZ_GPLB_GP_L"
              "&pageHelp.pageSize=10000",
              headers={**UA, "Referer": "http://www.sse.com.cn/"},
              timeout=60).json()
    rows = j.get("result") or []
    return ({str(r.get("A_STOCK_CODE", "")).strip()
             for r in rows if not r.get("DELIST_DATE")},
            "SSE commonQuery (Shanghai only)")


REGISTERS = {"Taiwan": _reg_taiwan, "Japan": _reg_japan,
             "HongKong": _reg_hk, "China": _reg_china}
SUFFIX = {"Australia": ".AX", "HongKong": ".HK", "India": ".NS",
          "Indonesia": ".JK", "Japan": ".T", "Korea": ".KS",
          "Malaysia": ".KL", "NewZealand": ".NZ",
          "Singapore": ".SI", "Taiwan": ".TW",
          "Thailand": ".BK", "China": ".SS"}


def sweep():
    import pandas as pd
    import requests
    sys.path.insert(0, str(ROOT / "scripts"))
    from yahoo_names import variants
    s = requests.Session()
    cache = json.loads((ROOT / "data" / "yahoo_names.json")
                       .read_bytes().decode("utf-8", "replace"))
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    mem = json.loads((ROOT / "data" / "apac_members.json")
                     .read_text(encoding="utf-8"))["markets"]
    out = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for market, sfx in SUFFIX.items():
        t = {str(x).strip() for x in
             df[df.market == market].ticker.dropna()
             if str(x).strip() not in ("", "nan")}
        t |= {str(x).strip() for x in
              mem.get(market, {}).get("standard_members", [])
              if x}
        todo = [x if "." in x else x + sfx for x in sorted(t)]
        # c-178b: consult the TICKER MAP first. Malaysia's
        # AMBANK / MAXIS / SDG / SWB / TM are Bursa SHORT NAMES,
        # not Yahoo symbols — every one is a live company mapped
        # to a numeric code in apac_ticker_map.json. Without this
        # the sweep labelled all five "dead", which would have
        # been a false statement about live index members and
        # exactly the kind of confident-but-wrong output this
        # script exists to prevent.
        tmap = {}
        f = ROOT / "data" / "apac_ticker_map.json"
        if f.exists():
            tmap = {k.split("|", 1)[1]: v
                    for k, v in json.loads(f.read_text(encoding="utf-8")).items()
                    if k.startswith(market + "|")}

        # liveness is tested against the SIZE FILE, not the name
        # cache. c-178c: all five Malaysian names mapped
        # correctly, but their numeric codes had never had a
        # NAME fetched, so a cache test still called them dead.
        # Presence in a cap-ranked universe is proof the company
        # trades; a missing English name is not proof it does not.
        szf = ROOT / "data" / "apac_size" / f"{market}.json"
        sz = set()
        if szf.exists():
            sz = {k.split(".")[0].lstrip("0") or k.split(".")[0]
                  for k in json.loads(szf.read_text(encoding="utf-8"))["rows"]}

        def _mapped(x):
            base = x.split(".")[0]
            code = tmap.get(base)
            if code and ((code.lstrip("0") or code) in sz
                         or any(v in cache
                                for v in variants(f"{code}{sfx}"))):
                return True
            return (base.lstrip("0") or base) in sz
        miss = [x for x in todo
                if not any(v in cache for v in variants(x))
                and not _mapped(x)]
        if not miss:
            print(f"{market:12} 0 unresolved")
            continue
        reg, src = set(), None
        if market in REGISTERS:
            try:
                reg, src = REGISTERS[market](s)
            except Exception as e:                 # noqa: BLE001
                print(f"{market}: register unreachable ({e})")
        dead, live = {}, []
        for x in miss:
            code = x.split(".")[0]
            if src:
                if code in reg or code.lstrip("0") in reg:
                    live.append(x)
                else:
                    dead[x] = f"absent from {src}"
            else:
                dead[x] = ("no Yahoo data and no reachable "
                           "exchange register — WEAK evidence")
        out.setdefault(market, {}).update(dead)
        strong = "register" if src else "WEAK (Yahoo silence)"
        print(f"{market:12} {len(miss):>3} unresolved -> "
              f"{len(dead):>3} dead [{strong}], "
              f"{len(live):>3} still listed {live[:5]}")
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=True),
                   encoding="utf-8")
    print(f"\n-> {OUT.name}: "
          f"{sum(len(v) for v in out.values())} dead tickers")


if __name__ == "__main__":
    sweep()
