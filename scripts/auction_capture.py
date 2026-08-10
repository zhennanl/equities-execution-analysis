"""Closing-auction snapshot capture — TWSE MIS feed (c-40, #4).

Captures the 5-SECOND indicative price/volume path during the
13:25–13:30 closing call — the imbalance forming in real time, the
dataset that is free live but unavailable historically. First live
run: Aug-31 (effective date). Capture-forward asset.

Commands:
  python scripts/auction_capture.py rehearse           (plumbing
      check off-hours: fetch + parse one snapshot per code)
  python scripts/auction_capture.py capture 2330 2454  (loop every
      5s until 13:31 Taipei; run from ~13:20)

Output: data/auction_snaps/{date}.json  (resumable, atomic)
"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "auction_snaps"
MIS = ("https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
       "?ex_ch={chs}&json=1&delay=0")


def _fetch(codes):
    import requests
    chs = "|".join(f"tse_{c}.tw" for c in codes)
    r = requests.get(MIS.format(chs=chs), headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"}, timeout=10)
    r.raise_for_status()
    js = r.json()
    out = []
    for a in js.get("msgArray", []):
        out.append({"code": a.get("c"), "time": a.get("t"),
                    "price": a.get("z") or a.get("b", "").split(
                        "_")[0],
                    "acc_vol": a.get("v"),
                    "bid1": a.get("b", "").split("_")[0],
                    "ask1": a.get("a", "").split("_")[0]})
    return out


def rehearse(codes):
    snaps = _fetch(codes)
    for s in snaps:
        print(f"  {s['code']}: t={s['time']} px={s['price']} "
              f"accvol={s['acc_vol']} bid={s['bid1']} "
              f"ask={s['ask1']}")
    print(f"REHEARSAL {'OK' if snaps else 'FAILED'}: "
          f"{len(snaps)}/{len(codes)} codes parsed "
          "(off-hours values are last session's — plumbing is what "
          "this validates)")
    return bool(snaps)


def capture(codes, until="13:31"):
    OUT.mkdir(exist_ok=True)
    day = dt.date.today().isoformat()
    f = OUT / f"{day}.json"
    snaps = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    print(f"capturing {codes} every 5s until {until} Taipei; "
          f"{len(snaps)} snaps already on file")
    while dt.datetime.now().strftime("%H:%M") <= until:
        try:
            batch = _fetch(codes)
            ts = dt.datetime.now().isoformat(timespec="seconds")
            snaps.append({"ts": ts, "snaps": batch})
            tmp = f.with_suffix(".tmp")
            tmp.write_text(json.dumps(snaps), encoding="utf-8")
            tmp.replace(f)
        except Exception as e:                 # noqa: BLE001
            print("snap failed:", e)
        time.sleep(5)
    print(f"done: {len(snaps)} snapshots -> {f}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "rehearse"
    codes = sys.argv[2:] or ["2330", "1101"]
    if cmd == "rehearse":
        sys.exit(0 if rehearse(codes) else 1)
    elif cmd == "capture":
        capture(codes)
