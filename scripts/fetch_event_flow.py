#!/usr/bin/env python3
"""Chunked, cached fetch of real 2026 Asia rebalance events -> per-name
flow metrics + realized strategy grades. Re-run until 'ALL CACHED'.
Cache: data/event_flow_study.json (derived data)."""
import datetime as dt
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
CACHE = Path("data/event_flow_study.json")

# (label, ticker_base, market, effective, ann_rel, side, provider)
EVENTS = [
 # FTSE Taiwan 50, effective close Jun 18 (announced Jun 5 ~ rel -9)
 ("TW50 add GUC",        "3443", "Taiwan (TWSE)", "2026-06-18", -9, "Buy",  "FTSE"),
 ("TW50 add BizLink",    "3665", "Taiwan (TWSE)", "2026-06-18", -9, "Buy",  "FTSE"),
 ("TW50 add NanYaPCB",   "8046", "Taiwan (TWSE)", "2026-06-18", -9, "Buy",  "FTSE"),
 ("TW50 add ZhenDing",   "4958", "Taiwan (TWSE)", "2026-06-18", -9, "Buy",  "FTSE"),
 ("TW50 del ChinaSteel", "2002", "Taiwan (TWSE)", "2026-06-18", -9, "Sell", "FTSE"),
 ("TW50 del FormosaPl",  "1301", "Taiwan (TWSE)", "2026-06-18", -9, "Sell", "FTSE"),
 ("TW50 del Hotai",      "2207", "Taiwan (TWSE)", "2026-06-18", -9, "Sell", "FTSE"),
 ("TW50 del Compermed",  "6919", "Taiwan (TWSE)", "2026-06-18", -9, "Sell", "FTSE"),
 # MSCI Taiwan SAIR, effective close May 29 (announced May 12 ~ rel -12)
 ("MSCI-TW del AsiaCem", "1102", "Taiwan (TWSE)", "2026-05-29", -12, "Sell", "MSCI"),
 ("MSCI-TW del Catcher", "2474", "Taiwan (TWSE)", "2026-05-29", -12, "Sell", "MSCI"),
 ("MSCI-TW del ChinaAir","2610", "Taiwan (TWSE)", "2026-05-29", -12, "Sell", "MSCI"),
 ("MSCI-TW del Compal",  "2324", "Taiwan (TWSE)", "2026-05-29", -12, "Sell", "MSCI"),
 ("MSCI-TW del THSR",    "2633", "Taiwan (TWSE)", "2026-05-29", -12, "Sell", "MSCI"),
 # MSCI Korea SAIR deletions, effective close May 29
 ("MSCI-KR del HanjinKAL","180640","Korea (KRX)", "2026-05-29", -12, "Sell", "MSCI"),
 ("MSCI-KR del HDMarine", "443060","Korea (KRX)", "2026-05-29", -12, "Sell", "MSCI"),
 ("MSCI-KR del SKBio",    "326030","Korea (KRX)", "2026-05-29", -12, "Sell", "MSCI"),
 # FTSE China A50, effective open Jun 22 -> use Jun 19 (last day traded at
 # old membership; T = last close before switch; disclosed)
 ("A50 add GigaDevice",  "603986","China-A Shanghai","2026-06-19", -11, "Buy","FTSE"),
 ("A50 add Montage",     "688008","China-A Shanghai","2026-06-19", -11, "Buy","FTSE"),
 ("A50 add DongshanPrec","002384","China-A Shenzhen","2026-06-19", -11, "Buy","FTSE"),
 ("A50 del Haier",       "600690","China-A Shanghai","2026-06-19", -11, "Sell","FTSE"),
 ("A50 del PingAnBank",  "000001","China-A Shenzhen","2026-06-19", -11, "Sell","FTSE"),
]

BATCH = (int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 4)


def main_traj():
    """Second pass: positioning trajectories (A->T day-by-day) for events
    already summary-cached. Run: fetch_event_flow.py traj [batch]."""
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    from agents.rebalancing_event_study import run_event_study
    from agents.event_flow_study import positioning_trajectory
    batch = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    done = 0
    for label, tkr, mkt, eff, ann, side, prov in EVENTS:
        if done >= batch or label not in cache:
            continue
        if not cache[label].get("available") or "traj" in cache[label]:
            continue
        try:
            es = run_event_study(tkr, mkt, dt.date.fromisoformat(eff), 12,
                                 f"{prov} review")
            t = positioning_trajectory(es, ann_rel=ann, side=side, label=label)
            cache[label]["traj"] = {k: v for k, v in t.items()}
            print(f"OK  {label}: shape {t.get('shape')}, T-day share "
                  f"{t.get('t_day_share')}, half-build rel {t.get('half_build_rel')}")
        except Exception as e:
            cache[label]["traj"] = {"available": False, "reason": str(e)[:100]}
            print(f"ERR {label}: {e}")
        done += 1
        CACHE.write_text(json.dumps(cache, indent=1), encoding="utf-8")
        time.sleep(1.2)
    rem = [e[0] for e in EVENTS if e[0] in cache
           and cache[e[0]].get("available") and "traj" not in cache[e[0]]]
    print(f"\ntraj remaining: {len(rem)}" + (" — ALL DONE" if not rem else ""))


def main():
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    from agents.rebalancing_event_study import run_event_study
    from agents.event_flow_study import summarize_event, grade_strategies
    done = 0
    for label, tkr, mkt, eff, ann, side, prov in EVENTS:
        if label in cache or done >= BATCH:
            continue
        try:
            es = run_event_study(tkr, mkt, dt.date.fromisoformat(eff), 12,
                                 f"{prov} review")
            s = summarize_event(es, side=side, ann_rel=ann, label=label)
            g = grade_strategies(es, side=side)
            cache[label] = {**s, "provider": prov, "market": mkt,
                            "grade": {k: v for k, v in g.items()
                                      if k != "frontier"},
                            "frontier": g["frontier"].to_dict(orient="records")}
            print(f"OK  {label}: T-mult {s.get('t_day_volume_multiple')}, "
                  f"best {g['realized_best']} vs ours {g['our_rule']} "
                  f"(regret {g['regret_bps']} bps)")
        except Exception as e:
            cache[label] = {"available": False, "reason": f"{type(e).__name__}: {e}",
                            "provider": prov, "market": mkt, "side": side}
            print(f"ERR {label}: {e}")
        done += 1
        CACHE.parent.mkdir(exist_ok=True)
        CACHE.write_text(json.dumps(cache, indent=1), encoding="utf-8")
        time.sleep(1.2)
    remaining = [e[0] for e in EVENTS if e[0] not in cache]
    print(f"\ncached {len(cache)}/{len(EVENTS)}"
          + (" — ALL CACHED" if not remaining else f"; next: {remaining[:3]}"))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "traj":
        main_traj()
    else:
        main()
