#!/usr/bin/env python3
"""Fetch today's exchange notices (TWSE zh / JPX ja / NSE en), triage
with the keyword engine, cache, and write the daily digest.

Usage: python scripts/fetch_reg_notices.py [--digest-only]
Cache: data/reg_notices_cache.json (gitignored)
Digest: data/reg_digest_YYYY-MM-DD.md (gitignored dir)

Run daily (schedule with the forward fetch). Blocked sources
(TPEx/HKEX/KRX/SGX/SET) are PROTOCOL — see reg_watch.NOTICE_SOURCES.
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.reg_watch import (cluster_stories, daily_digest,     # noqa: E402
                              fetch_jpx_news, fetch_nse_circulars,
                              fetch_sgx_circulars, fetch_twse_news,
                              flash_brief, load_registry, new_notices,
                              notice_id, triage_notices)

CACHE = Path("data/reg_notices_cache.json")
SEEN = Path("data/reg_seen_ids.json")

FEEDS = [("TWSE", fetch_twse_news), ("JPX", fetch_jpx_news),
         ("NSE", fetch_nse_circulars), ("SGX", fetch_sgx_circulars)]


def watch_mode():
    """The proactive loop: fetch -> diff vs seen -> cluster NEW notices
    into stories -> emit a flash brief ONLY when something scored
    FLASH/NOTABLE arrived. Run on a schedule; silence means no news."""
    seen = set(json.loads(SEEN.read_text())) if SEEN.exists() else set()
    fresh = []
    for name, fn in FEEDS:
        try:
            fresh.extend(new_notices(fn(), seen))
        except Exception as e:                        # noqa: BLE001
            print(f"{name}: FAILED ({e})")
    first_run = not seen
    seen |= {notice_id(n) for n in fresh}
    SEEN.write_text(json.dumps(sorted(seen)))
    if first_run:
        print(f"baseline established: {len(fresh)} notices marked seen "
              "(no brief on first run — everything is 'new' today)")
        return
    if not fresh:
        print("no new notices")
        return
    brief = flash_brief(cluster_stories(triage_notices(fresh)))
    if brief:
        out = Path(f"data/reg_flash_{dt.date.today().isoformat()}.md")
        out.write_text(brief, encoding="utf-8")
        print(f"⚡ FLASH BRIEF -> {out} ({len(fresh)} new notices)")
        print(brief[:600])
    else:
        print(f"{len(fresh)} new notices, none above ROUTINE — logged, "
              "no alert (alert fatigue is a design goal)")


def main():
    if "watch" in sys.argv:
        watch_mode()
        return
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    today = dt.date.today().isoformat()
    if "--digest-only" not in sys.argv:
        notices, errors = [], []
        for name, fn in FEEDS:
            try:
                got = fn()
                notices.extend(got)
                print(f"{name}: {len(got)} notices")
            except Exception as e:                    # noqa: BLE001
                errors.append(f"{name}: {e}")
                print(f"{name}: FAILED ({e})")
        cache[today] = {"notices": notices, "errors": errors}
        CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    day = cache.get(today, {"notices": []})
    tri = triage_notices(day["notices"])
    reg = load_registry()
    digest = daily_digest(tri, reg, date=today)
    out = Path(f"data/reg_digest_{today}.md")
    out.write_text(digest, encoding="utf-8")
    n_high = 0 if tri.empty else int((tri["relevance"] == "HIGH").sum())
    print(f"digest -> {out}  ({len(day['notices'])} notices, "
          f"{n_high} HIGH)")


if __name__ == "__main__":
    main()
