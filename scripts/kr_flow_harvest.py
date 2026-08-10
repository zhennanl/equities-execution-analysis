"""Korea crowding overlays — KRX per-stock foreign holdings +
short balance for event windows (c-129). RUN ON BILL'S
TERMINAL: data.krx.co.kr's JSON gateway answers browsers and
residential sessions but returns LOGOUT to this sandbox
(probed 2026-08-07).

Two KRX daily day-file screens (delisted-safe by the same
day-file principle):
  MDCSTAT03501  foreign holding by stock (보유량/한도소진율)
  MDCSTAT30501  short-sale balance by stock (공매도 잔고)

RITUAL (the part that matters): GET the mdiLoader page first
to collect cookies, keep the Session, then POST getJsonData
with a Referer. If LOGOUT persists, open the screen once in a
browser, copy the exact 'bld' string from DevTools' network
tab into BLD below — KRX renames them occasionally.

Usage (terminal): py scripts\\kr_flow_harvest.py harvest
Output: data/kr_event_flows.json (resumable, day-cached)
"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "kr_event_flows.json"
PAD = 25
BLD = {"foreign": "dbms/MDC/STAT/standard/MDCSTAT03501",
       "short": "dbms/MDC/STAT/srt/MDCSTAT30501"}
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; "
       "x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
       "Referer": "http://data.krx.co.kr/contents/MDC/MDI/"
       "mdiLoader/index.cmd?menuId=MDC0201020103"}


def _session():
    import requests
    s = requests.Session()
    s.headers.update(HDR)
    s.get("http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/"
          "index.cmd?menuId=MDC0201020103", timeout=30)
    return s


def _day(s, which, d):
    r = s.post("http://data.krx.co.kr/comm/bldAttendant/"
               "getJsonData.cmd",
               data={"bld": BLD[which], "locale": "ko_KR",
                     "mktId": "ALL", "trdDd": d.strftime("%Y%m%d"),
                     "share": "1", "money": "1"}, timeout=30)
    if "LOGOUT" in r.text[:50]:
        raise SystemExit(
            "KRX still refuses this client. Open the screen in "
            "a browser once, copy the exact 'bld' from the "
            "network tab into BLD, and retry.")
    j = r.json()
    rows = j.get("OutBlock_1") or j.get("output") or []
    out = {}
    for x in rows:
        code = (x.get("ISU_SRT_CD") or x.get("ISU_CD") or
                "").strip()
        if code:
            out[code] = x
    return out


def harvest():
    sys.path.insert(0, str(ROOT / "scripts"))
    from apac_event_days import calendar, movers
    cal = calendar()
    byrev = {}
    for rev, tick, act, name in movers("Korea"):
        c = str(tick).split(".")[0]
        byrev.setdefault(rev, []).append(
            (f"{int(c):06d}" if c.isdigit() else c, act, name))
    cache = (json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists()
             else {"series": {}, "_days": {}})
    s = _session()
    for rev in sorted(byrev, key=lambda r: cal[r][0],
                      reverse=True):
        if all(f"{rev}|{c}" in cache["series"]
               for c, _, _ in byrev[rev]):
            continue
        a = (dt.date.fromisoformat(cal[rev][0])
             - dt.timedelta(days=PAD))
        b = (dt.date.fromisoformat(cal[rev][1])
             + dt.timedelta(days=PAD))
        ser = {c: [] for c, _, _ in byrev[rev]}
        d = a
        while d <= b:
            if d.weekday() < 5:
                k = d.isoformat()
                if k not in cache["_days"]:
                    day = {}
                    try:
                        f = _day(s, "foreign", d)
                        sh = _day(s, "short", d)
                        for c, _, _ in byrev[rev]:
                            rec = {}
                            if c in f:
                                rec["foreign"] = f[c]
                            if c in sh:
                                rec["short"] = sh[c]
                            if rec:
                                day[c] = rec
                    except SystemExit:
                        raise
                    except Exception:              # noqa: BLE001
                        pass
                    cache["_days"][k] = day
                    time.sleep(1.5)
                for c, _, _ in byrev[rev]:
                    if c in cache["_days"][k]:
                        ser[c].append({"d": k,
                                       **cache["_days"][k][c]})
            d += dt.timedelta(days=1)
        for c, act, name in byrev[rev]:
            cache["series"][f"{rev}|{c}"] = {
                "rev": rev, "code": c, "action": act,
                "name": name, "ann": cal[rev][0],
                "eff": cal[rev][1], "rows": ser[c]}
        OUT.write_text(json.dumps(cache), encoding="utf-8")
        print(f"KR flows {rev}: "
              f"{sum(1 for c, _, _ in byrev[rev] if ser[c])}"
              f"/{len(byrev[rev])}", flush=True)
    print(f"-> {OUT.name}")


if __name__ == "__main__":
    harvest()
