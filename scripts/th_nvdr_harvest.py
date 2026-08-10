"""Thailand crowding overlay — per-stock NVDR daily trading
for event windows (c-129). RUN ON BILL'S TERMINAL (set.or.th
403s the sandbox; the same session ritual that worked for the
float run applies).

NVDR volumes are Thailand's foreign-flow fingerprint: foreign
investors overwhelmingly buy via NVDRs, so daily per-stock
NVDR net buy ≈ the t86 analogue.

Endpoint (verify field names on first run — the profile api
worked with this ritual on 2026-08-07):
  warm-up: /en/market/product/stock/quote/{SYM}/price
  data:    /api/set/nvdr-trading/stock/{SYM}?lang=en   (probe;
           if 404, DevTools the NVDR page for the exact path
           and paste it into NVDR_API below)

Usage (terminal): py scripts\\th_nvdr_harvest.py harvest
Output: data/th_event_nvdr.json (resumable)
"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "th_event_nvdr.json"
PAD = 25
# c-131: the guessed path 404'd on Bill's live run. GET THE
# REAL ONE (2 minutes): open
#   https://www.set.or.th/en/market/statistics/nvdr/trading-by-stock
# in Chrome, F12 -> Network -> pick any request whose URL
# contains 'nvdr', copy the FULL url, and paste it here with
# the symbol replaced by {sym}. The session ritual + headers
# below already work (proven by the float run).
NVDR_API = ("PASTE_ME_{sym}")
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; "
       "x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
       "Accept-Language": "en-US,en;q=0.9"}


def harvest():
    import requests
    if NVDR_API.startswith("PASTE_ME"):
        raise SystemExit(
            "NVDR_API not set — see the comment above it "
            "(one DevTools copy from the SET NVDR page).")
    sys.path.insert(0, str(ROOT / "scripts"))
    from apac_event_days import calendar, movers
    cal = calendar()
    byrev = {}
    for rev, tick, act, name in movers("Thailand"):
        # census stores the NVDR line (TTB-R.BK): strip the
        # exchange suffix AND the -R marker — SET's API wants
        # the base symbol (c-131 fix)
        sym = str(tick).split(".")[0].upper()
        if sym.endswith("-R"):
            sym = sym[:-2]
        byrev.setdefault(rev, []).append((sym, act, name))
    cache = (json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists()
             else {"series": {}})
    s = requests.Session()
    s.headers.update(HDR)
    for rev in sorted(byrev, key=lambda r: cal[r][0],
                      reverse=True):
        for sym, act, name in byrev[rev]:
            key = f"{rev}|{sym}"
            prev = cache["series"].get(key)
            # retry anything that previously errored (c-131)
            praw = str(prev.get("raw", {})) if prev else ""
            if prev and "error" not in praw \
                    and "Not Found" not in praw:
                continue
            try:
                s.get("https://www.set.or.th/en/market/product/"
                      f"stock/quote/{sym}/price", timeout=25)
                r = s.get(NVDR_API.format(sym=sym),
                          headers={"Referer":
                                   "https://www.set.or.th/"},
                          timeout=25)
                j = (r.json() if "json" in
                     r.headers.get("content-type", "") else
                     {"error": f"non-json {r.status_code}"})
            except Exception as e:                 # noqa: BLE001
                j = {"error": type(e).__name__}
            cache["series"][key] = {
                "rev": rev, "code": sym, "action": act,
                "name": name, "ann": cal[rev][0],
                "eff": cal[rev][1], "raw": j}
            OUT.write_text(json.dumps(cache), encoding="utf-8")
            print(f"{rev} {sym}: "
                  f"{'ok' if 'error' not in j else j['error']}",
                  flush=True)
            time.sleep(2.0)
    print(f"-> {OUT.name}  (inspect one 'raw' payload, then "
          "we normalize the fields)")


if __name__ == "__main__":
    harvest()
