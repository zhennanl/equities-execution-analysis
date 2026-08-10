"""Market caps for index members Yahoo cannot size (c-181).

WHY THIS EXISTS. The §2.2.3 size screen ranks a market by full
market cap. A member that cannot be sized is not a gap in a
table — it shifts every rank below it and therefore moves the
cutoff itself. Across the six markets at >=99% member coverage
(Japan, Taiwan, Korea, Thailand, Malaysia, Indonesia) exactly
FOUR members were unsizable, so they are resolved here by name
rather than by building four harvesters.

Shares outstanding changes a few times a year, so a cached
override with a recorded source and date is the proportionate
answer. Every entry below carries where the number came from
and when it was taken, and the loader refuses to apply an
entry older than `MAX_AGE_DAYS` without warning — a stale
share count is a silent error, which is the kind this project
tries hardest to avoid.

WHAT IS NOT HERE. Nothing inferred. LG Uplus (032640) could be
estimated by dividing Yahoo's floatShares by one minus the
insider percentage, but that would be a derived guess wearing
the costume of a data point, and it would sit in the same file
as four measured numbers. It stays listed as MISSING until a
published figure is available.

Run:  py scripts\\share_overrides.py          (verify/refresh)
Out:  data/share_overrides.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "share_overrides.json"
MAX_AGE_DAYS = 120

# "Market|code" -> the override. Either cap_usd_b directly, or
# shares + a price the harvester already has.
OVERRIDES = {
    "Japan|8951": {
        "name": "Nippon Building Fund REIT",
        "shares": 8815000,
        "cap_local": 1144186994688, "ccy": "JPY",
        "source": "Yahoo v7/quote — the batch miss was "
                  "TRANSIENT; a single re-ask returns both "
                  "shares and cap. Re-running the harvest may "
                  "resolve it without this entry.",
        "asof": "2026-08-08"},
    "Taiwan|3529": {
        "name": "eMemory Technology",
        "shares": 74686492,
        "cap_usd_b": 5.3026,
        "source": "OUR OWN exchange harvest — TPEx line in "
                  "data/tw_universe_pit.json at 2026-07-20. "
                  "Yahoo lacks it; the exchange does not.",
        "asof": "2026-07-20"},
    "Korea|015760": {
        "name": "Korea Electric Power (KEPCO)",
        "cap_usd_b": 16.036262912,
        "source": "Yahoo v7/quote on the NYSE ADR 'KEP', whose "
                  "marketCap is the WHOLE company in USD. The "
                  "Seoul line 015760.KS returns a price but no "
                  "share count.",
        "asof": "2026-08-08",
        "caveat": "ADR-derived. Yahoo's KEP sharesOutstanding "
                  "is in ADS units, not common shares, so only "
                  "the CAP is used — never the share count."},
}

MISSING = {
    "Korea|032640": {
        "name": "LG Uplus",
        "why": "no published share count reachable. Yahoo has "
               "price and floatShares (259,478,138) but no "
               "total; there is no US ADR to borrow a cap "
               "from; KRX returns 403 unauthenticated. Needs "
               "DART (Korean regulator, API key) or a manual "
               "lookup.",
        "impact": "Korea member coverage 76/77 instead of "
                  "77/77. One name below the top of the "
                  "ladder, so the cutoff moves by roughly one "
                  "rank."},
}


def load():
    """Overrides keyed 'Market|code', with staleness warnings."""
    import datetime as dt
    if not OUT.exists():
        save()
    d = json.loads(OUT.read_text(encoding="utf-8"))
    today = dt.date.today()
    for k, v in (d.get("overrides") or {}).items():
        try:
            age = (today - dt.date.fromisoformat(v["asof"])).days
        except Exception:                          # noqa: BLE001
            continue
        if age > MAX_AGE_DAYS:
            print(f"  ! {k}: override is {age} days old "
                  f"(limit {MAX_AGE_DAYS}) — re-verify")
    return d.get("overrides") or {}


def save():
    OUT.write_text(json.dumps(
        {"note": "Market caps for index members Yahoo cannot "
                 "size. Every entry carries its source; "
                 "nothing here is inferred.",
         "max_age_days": MAX_AGE_DAYS,
         "overrides": OVERRIDES,
         "still_missing": MISSING}, indent=1),
        encoding="utf-8")
    print(f"-> {OUT.name}: {len(OVERRIDES)} overrides, "
          f"{len(MISSING)} still missing")


if __name__ == "__main__":
    save()
    load()
    for k, v in OVERRIDES.items():
        cap = v.get("cap_usd_b")
        print(f"  {k:16} {v['name'][:30]:30} "
              f"{('$%.2fB' % cap) if cap else 'shares only'}")
    for k, v in MISSING.items():
        print(f"  {k:16} {v['name'][:30]:30} MISSING")
