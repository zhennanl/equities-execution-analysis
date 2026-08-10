"""Ticker maps for the three markets Yahoo symbol-lookup cannot
reach (c-165).

THE THREE PROBLEMS, which are not the same problem:

  MALAYSIA  Yahoo wants Bursa's NUMERIC code. "MAYBANK.KL"
            returns nothing; "1155.KL" is Malayan Banking.
  SINGAPORE Yahoo wants SGX's alphanumeric code. "CICT.SI"
            returns nothing; "C38U.SI" is CapitaLand
            Integrated Commercial Trust.
  PHILIPPINES Yahoo has PRICES (the chart endpoint serves
            AC.PS fine) but no NAMES — the search endpoint
            returns nothing and the screener reports region
            "ph" total = 0. So the name has to come from the
            exchange: PSE Edge's autocomplete returns
            {symbol, cmpyNm} and sweeping a-z enumerates the
            whole board (282 companies).

MY and SG are solved from data we already harvested: the stage-1
size files carry symbol -> longName for every listed name, so
this is a local name-match, no new requests.

MATCHING DISCIPLINE — carried over from the c-161 Taiwan
failure, where a loose matcher confidently mapped Chunghwa
Picture Tubes to Chunghwa TELECOM. A wrong ticker is worse than
a blank one because the roster merges rows on ticker. So:
  - the HEAD token must appear in the candidate, and
  - either two distinctive tokens overlap, or the head token is
    rare enough across the market to name the company alone.
Anything ambiguous is left unmapped and reported, not guessed.

Run:  py scripts\\apac_ticker_maps.py
Out:  data/apac_ticker_map.json   {"Malaysia|MAYBANK": "1155"}
      data/yahoo_names.json       (PH names merged in)
"""
import json
import re
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIZE = ROOT / "data" / "apac_size"
MAP = ROOT / "data" / "apac_ticker_map.json"
NAMES = ROOT / "data" / "yahoo_names.json"
UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://edge.pse.com.ph/"}

_STOP = {"CO", "CORP", "CORPORATION", "INC", "LTD", "LIMITED",
         "COMPANY", "THE", "HOLDING", "HOLDINGS", "GROUP",
         "AND", "OF", "BHD", "BERHAD", "PLC", "PUBLIC",
         "TBK", "PT", "REIT", "TRUST"}


def toks(x):
    w = [t.replace("'", "") for t in
         re.split(r"[^A-Z0-9']+", str(x).upper())]
    return {t for t in w if len(t) > 1 and t not in _STOP}


def head(x):
    for t in re.split(r"[^A-Z0-9']+", str(x).upper()):
        if t and t not in _STOP and len(t) > 1:
            return t
    return None


def _match(msci_names, idx):
    """idx: {symbol: longName}. Returns (map, unmatched)."""
    dfq = Counter()
    for nm in idx.values():
        dfq.update(toks(nm))
    out, miss = {}, []
    for nm in msci_names:
        want, h = toks(nm), head(nm)
        best, score, ties = None, 0, 0
        for sym, cand in idx.items():
            got = toks(cand)
            if h and h not in got:
                continue
            sc = len(want & got)
            if sc > score:
                best, score, ties = sym, sc, 1
            elif sc == score and sc:
                ties += 1
        rare = h and dfq.get(h, 99) <= 2
        if best and (score >= 2 or rare) and ties <= 1:
            out[nm] = best
        else:
            miss.append(nm)
    return out, miss


def _msci_names(market):
    import pandas as pd
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    g = df[df.market == market]
    return sorted({str(s).strip() for s in g.security
                   if str(s).strip()})


def pse_names():
    """Enumerate the Philippine board from PSE Edge."""
    import requests
    out = {}
    for ch in "abcdefghijklmnopqrstuvwxyz":
        try:
            j = requests.get(
                "https://edge.pse.com.ph/autoComplete/"
                f"searchCompanyNameSymbol.ax?term={ch}",
                headers=UA, timeout=25).json()
            for r in j:
                if r.get("symbol") and r.get("etfYn") == "0":
                    out[r["symbol"].strip()] = r["cmpyNm"].strip()
        except Exception as e:                     # noqa: BLE001
            print(f"  PSE '{ch}': {e}")
        time.sleep(0.3)
    return out


def run():
    m = json.loads(MAP.read_text(encoding="utf-8")) if MAP.exists() else {}
    report = {}
    # ---- Malaysia + Singapore, from stage-1 size files -------
    for market in ("Malaysia", "Singapore"):
        f = SIZE / f"{market}.json"
        if not f.exists():
            print(f"{market}: run apac_size_harvest.py first")
            continue
        rows = json.loads(f.read_text(encoding="utf-8"))["rows"]
        idx = {k.split(".")[0]: v["name"] for k, v in rows.items()
               if v.get("name")}
        got, miss = _match(_msci_names(market), idx)
        for nm, sym in got.items():
            m[f"{market}|{nm}"] = sym
        report[market] = (len(got), len(miss), miss[:8])
        print(f"{market}: {len(got)} mapped, {len(miss)} "
              f"unmatched  {miss[:6]}")
    # ---- Philippines, from the exchange itself ---------------
    pse = pse_names()
    print(f"Philippines: PSE Edge returned {len(pse)} companies")
    if pse:
        raw = NAMES.read_bytes().decode("utf-8", errors="replace")
        try:
            cache = json.loads(raw)
        except Exception:                          # noqa: BLE001
            cache = {}
        added = 0
        for sym, nm in pse.items():
            k = f"{sym}.PS"
            if k not in cache:
                cache[k] = nm
                added += 1
        NAMES.write_text(json.dumps(cache, indent=1,
                                    ensure_ascii=True),
                         encoding="utf-8")
        got, miss = _match(_msci_names("Philippines"),
                           {k: v for k, v in pse.items()})
        for nm, sym in got.items():
            m[f"Philippines|{nm}"] = sym
        report["Philippines"] = (len(got), len(miss), miss[:8])
        print(f"Philippines: +{added} names cached, "
              f"{len(got)} MSCI names mapped, {len(miss)} "
              f"unmatched  {miss[:6]}")
    MAP.write_text(json.dumps(m, indent=1, ensure_ascii=True),
                   encoding="utf-8")
    print(f"\n-> {MAP.name}: {len(m)} entries")
    return report


if __name__ == "__main__":
    run()
