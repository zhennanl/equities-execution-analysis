#!/usr/bin/env python3
"""Patch tw_history/quotes.json with 6919 daily rows to Aug-11.

    py scripts\\quotes_patch_6919_aug26.py

WHY THIS EXISTS (c-397, Bill). The quotes cache ends 2026-06-18,
so the border deletion's vol input was struck on a window ending
mid-June — the tail of Caliway's squeeze era, with two ±10%
sessions inside it. The July/August tape is materially calmer,
and the P(delete) the page carries should price THIS tape, not
June's. Rows below are transcribed from TWSE's own STOCK_DAY
endpoint (fetched 2026-08-11):

    https://www.twse.com.tw/rwd/en/afterTrading/STOCK_DAY
        ?date=2026MM01&stockNo=6919&response=json

Idempotent: existing (date, code) entries are left untouched, so
a re-run cannot double-write. Only 6919 is patched — every other
name's window stays exactly as harvested.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
Q = ROOT / "data" / "tw_history" / "quotes.json"

# [date, volume shares, value TWD, close] — TWSE STOCK_DAY
ROWS = [
    ("20260622", 17823430, 2098353635, 119.5),
    ("20260623", 16274285, 1819952469, 108.0),
    ("20260624", 8998364, 942313631, 104.0),
    ("20260625", 6273666, 633876703, 99.3),
    ("20260626", 7474039, 734609309, 98.1),
    ("20260629", 3585293, 359256905, 99.0),
    ("20260630", 2533625, 253781151, 99.8),
    ("20260701", 2449787, 242950796, 98.7),
    ("20260702", 4207388, 411368788, 96.6),
    ("20260703", 5316027, 528480888, 99.7),
    ("20260706", 4440186, 450253332, 100.0),
    ("20260707", 10933457, 1171242263, 110.0),
    ("20260708", 15352892, 1632706998, 104.5),
    ("20260709", 5767335, 619251492, 107.5),
    ("20260713", 4953364, 530263459, 107.5),
    ("20260714", 6230412, 668820474, 107.5),
    ("20260715", 9851200, 1096900591, 109.5),
    ("20260716", 9172986, 1038923809, 113.5),
    ("20260717", 12681670, 1388224454, 103.5),
    ("20260720", 6411660, 687247192, 106.5),
    ("20260721", 3469239, 367279826, 105.0),
    ("20260722", 2708605, 283992329, 104.0),
    ("20260723", 5467257, 552242551, 100.5),
    ("20260724", 3349768, 330576369, 97.8),
    ("20260727", 3018357, 305237639, 102.0),
    ("20260728", 5644014, 575616934, 103.5),
    ("20260729", 8514916, 866169677, 102.0),
    ("20260730", 5196661, 523724035, 103.0),
    ("20260731", 4311191, 445752438, 103.0),
    ("20260803", 7516308, 811318566, 109.5),
    ("20260804", 6781755, 720143001, 108.0),
    ("20260805", 4434456, 483299480, 108.5),
    ("20260806", 3356916, 361650705, 107.5),
    ("20260807", 2996870, 317651981, 105.0),
    ("20260810", 5718488, 612833856, 111.0),
    ("20260811", 4082269, 447340351, 108.0),
]


def main():
    q = json.loads(Q.read_text(encoding="utf-8"))
    added = 0
    for d, vol, val, close in ROWS:
        day = q.setdefault(d, {})
        if "6919" not in day:
            day["6919"] = [float(vol), float(val), float(close)]
            added += 1
    Q.write_text(json.dumps(q), encoding="utf-8")
    print(f"6919: {added} sessions added "
          f"(cache now runs to {max(q)})")


if __name__ == "__main__":
    main()
