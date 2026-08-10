"""Step 7 — the LIVE announcement->effective loop for Aug-2026
(c-128).

From the first reaction session (expected 2026-08-12) run daily
after the Taipei close:

    py scripts\\event_window_live.py pull
    py scripts\\event_window_live.py report

`pull` fetches the day's close/volume (TWSE), foreign net buy
(t86), SBL borrow balance and margin for every name on the
DECLARED shortlist, appending to data/aug26_live_ledger.json.
`report` scores each name against the HISTORICAL distribution
at the same day-offset (data/event_window_metrics.json) and
prints the stance table. Reports are APPENDED to the ledger —
never overwritten — so the whole window becomes a graded,
timestamped record by Sep-1.

THE SHORTLIST (declared 2026-08-07, before announcement; the
ledger tracks BOTH our calls and, after Aug-12, whatever MSCI
actually announced — mistakes stay visible):
    ADDS : 2408 8046 2344 8299 3189 6274   (6505 float-blocked)
    DELS : 2615 6919 2609 3529 2834 1101
    BUBBLE: 3293 8069 2356 5871
"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LED = ROOT / "data" / "aug26_live_ledger.json"
UA = {"User-Agent": "Mozilla/5.0"}

SHORTLIST = {
    "ADD": ["2408", "8046", "2344", "8299", "3189", "6274"],
    "DEL": ["2615", "6919", "2609", "3529", "2834", "1101"],
    "BUBBLE": ["3293", "8069", "2356", "5871"],
    "BLOCKED": ["6505"]}
ANN = "2026-08-11"          # announcement date (Geneva evening)
EFF = "2026-08-31"          # effective close


def _num(s):
    try:
        return float(str(s).replace(",", ""))
    except (ValueError, AttributeError):
        return None


def pull(date=None):
    """One day's data for every shortlist name. Run after the
    Taipei close. Uses the BULK endpoints (1 call each, not
    per-stock): MI_INDEX for closes, T86 for foreign, TWT93U/
    MI_MARGN for borrow+margin."""
    import requests
    d = date or dt.date.today().strftime("%Y%m%d")
    led = (json.loads(LED.read_text(encoding="utf-8")) if LED.exists()
           else {"shortlist": SHORTLIST, "ann": ANN, "eff": EFF,
                 "declared": "2026-08-07", "days": {}})
    if d in led["days"]:
        print(f"{d} already pulled")
        return
    names = [c for v in SHORTLIST.values() for c in v]
    day = {}

    def _get(url):
        """RUN FROM BILL'S TERMINAL. Endpoints throttle hard
        when the sandbox has other TWSE pulls running — one
        TWSE consumer per machine, the standing rule."""
        for i in range(3):
            try:
                return requests.get(url, headers=UA,
                                    timeout=60).json()
            except Exception:                      # noqa: BLE001
                time.sleep(8 * (i + 1))
        return {}
    # closes + volume — TWSE
    j = _get("https://www.twse.com.tw/rwd/zh/afterTrading/"
             f"MI_INDEX?date={d}&type=ALL&response=json")
    tb = [t for t in j.get("tables", [])
          if t.get("fields") and t["fields"][0] == "證券代號"]
    for r in (tb[0]["data"] if tb else []):
        c = r[0].strip()
        if c in names:
            day.setdefault(c, {})["close"] = _num(r[8])
            day[c]["vol"] = _num(r[2])
    time.sleep(3)
    # closes + volume — TPEx (c-131: 8299/6274/3529/3293/8069
    # are TPEx-listed; MI_INDEX never carries them)
    dd = f"{d[:4]}%2F{d[4:6]}%2F{d[6:]}"
    j = _get("https://www.tpex.org.tw/www/zh-tw/afterTrading/"
             f"otc?date={dd}&type=EW&id=&response=json")
    for t in j.get("tables", []):
        f = t.get("fields") or []
        if not f or "代號" not in f[0]:
            continue
        for r in t["data"]:
            c = str(r[0]).strip()
            if c in names and c not in day:
                day[c] = {"close": _num(r[2]),
                          "vol": _num(r[7]),
                          "mkt": "tpex"}
    time.sleep(3)
    # foreign net (T86)
    j = _get("https://www.twse.com.tw/rwd/zh/fund/T86"
             f"?date={d}&selectType=ALLBUT0999&response=json")
    for r in j.get("data", []):
        c = str(r[0]).strip()
        if c in names:
            day.setdefault(c, {})["foreign_net"] = _num(r[4])
    time.sleep(3)
    # SBL borrow balance (TWT93U)
    j = _get("https://www.twse.com.tw/rwd/zh/afterTrading/"
             f"TWT93U?date={d}&response=json")
    for r in j.get("data", []):
        c = str(r[0]).strip()
        if c in names:
            day.setdefault(c, {})["borrow_bal"] = _num(r[10])
    got = sum(1 for v in day.values() if v.get("close"))
    if got == 0:
        # c-138: never save an empty day — it blocks the
        # already-pulled guard from retrying (weekend/holiday
        # or data not yet published)
        print(f"{d}: nothing published (weekend/holiday/too "
              "early?) — NOT saved, retry later")
        return
    led["days"][d] = day
    LED.write_text(json.dumps(led, indent=1), encoding="utf-8")
    print(f"{d}: {got}/{len(names)} names pulled -> "
          f"{LED.name}")


def report():
    """Score today vs the historical distribution at the same
    day-offset and APPEND the stance block to the ledger."""
    led = json.loads(LED.read_text(encoding="utf-8"))
    hist = json.loads((ROOT / "data" /
                       "event_window_metrics.json").read_text(encoding="utf-8"))
    days = sorted(led["days"])
    if not days:
        print("nothing pulled yet")
        return
    ann = dt.date.fromisoformat(led["ann"])
    t = len([d for d in days
             if dt.date(int(d[:4]), int(d[4:6]), int(d[6:]))
             > ann])
    pb = hist["playbook"]
    lines = [f"=== Aug-26 live report, day +{t} after "
             f"announcement (pulled {days[-1]}) ==="]
    for act in ("ADD", "DEL"):
        med_drift = pb[act]["drift"]
        for c in led["shortlist"][act]:
            path = [led["days"][d].get(c, {}) for d in days]
            closes = [p.get("close") for p in path
                      if p.get("close")]
            if len(closes) < 2:
                lines.append(
                    f"{act} {c}: {len(closes)} day(s) pulled — "
                    "cumulative return needs 2+ (normal until "
                    "the second post-announcement session)")
                continue
            cum = closes[-1] / closes[0] - 1
            fsum = sum(p.get("foreign_net") or 0 for p in path)
            lines.append(
                f"{act} {c}: cum {cum:+.1%} vs hist median "
                f"drift {med_drift:+.1%} | cum foreign net "
                f"{fsum / 1e6:+.1f}M sh | borrow "
                f"{path[-1].get('borrow_bal', '—')}")
    block = {"generated": dt.datetime.now().isoformat(
        timespec="seconds"), "day_offset": t, "lines": lines}
    led.setdefault("reports", []).append(block)
    LED.write_text(json.dumps(led, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "pull":
        pull(a[1] if len(a) > 1 else None)
    elif a and a[0] == "report":
        report()
    else:
        print(__doc__)
