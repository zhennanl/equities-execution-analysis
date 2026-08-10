"""Ticker map for the changes database (c-102).

Resolves every unique (market, security-name) in
msci_changes_db to a local ticker, three tiers:
  A. current member lists (apac_members.json names) — exact/
     fuzzy on normalized names (instant, ~11% — mostly recent)
  B. the TW event registry codes (already joined in the DB)
  C. Yahoo search backfill (this script's main job) — cleaned
     name + market suffix filter; RESUMABLE cache; unresolved
     stored as null and retried only with --retry-null

Cache: data/security_ticker_map.json  {"MKT|NORMNAME": ticker}
After running, rebuild the DB (py scripts\\changes_db.py build)
to join the map into the 'ticker' column.

c-113 CHINA CLASS RULE: share class is IDENTITY in China (A/H
are separate index lines). The Yahoo search filter is therefore
class-aware for China — A/B names only accept .SS/.SZ, H names
only .HK. `fix-china` nulls the mappings made before this rule
(e.g. "AIR CHINA A" -> 0753.HK, the H line — 60 such wrong
venues found by the off-cycle audit); rerun with --retry-null
to re-search them under the venue constraint.

Usage:
  py scripts\\ticker_backfill.py run [--limit N] [--retry-null]
  py scripts\\ticker_backfill.py fix-china
  py scripts\\ticker_backfill.py status
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "data" / "security_ticker_map.json"

SUFFIX = {"Taiwan": (".TW", ".TWO"), "Japan": (".T",),
          "Korea": (".KS", ".KQ"), "HongKong": (".HK",),
          "Australia": (".AX",), "India": (".NS", ".BO"),
          "Malaysia": (".KL",), "Indonesia": (".JK",),
          "Philippines": (".PS",), "Singapore": (".SI",),
          "Thailand": (".BK",), "NewZealand": (".NZ",),
          "China": (".SS", ".SZ", ".HK")}


def norm(s):
    s = re.sub(r"[^A-Z0-9 ]", " ", str(s).upper())
    return re.sub(r"\s+", " ", s).strip()


def clean_for_search(name):
    """Strip MSCI listing-class suffixes that confuse search."""
    s = re.sub(r"\s*\((HK-C|C|A|B|P|F)\)\s*$", "", str(name))
    s = re.sub(r"\s+(A|B|H)$", "", s)
    return s.strip()


def _china_class(name):
    """A / B / H / None from an MSCI China security name."""
    n = re.sub(r"[^A-Z0-9 ]", " ", str(name).upper())
    n = re.sub(r"\s+", " ", n).strip()
    if re.search(r"\bA( HK C)?$", n):
        return "A"
    if n.endswith(" B"):
        return "B"
    if n.endswith(" H"):
        return "H"
    return None


def _suffixes_for(mkt, name):
    """Venue filter for the Yahoo search — class-aware in
    China (c-113)."""
    if mkt != "China":
        return SUFFIX[mkt]
    c = _china_class(name)
    if c == "A":
        return (".SS", ".SZ")
    if c == "H":
        return (".HK",)
    # B is AMBIGUOUS in MSCI China naming: onshore B-shares
    # (900xxx.SS / 200xxx.SZ) but ALSO HK-listed Class B
    # ordinaries (XIAOMI CORP B = 1810.HK) — allow all venues
    return SUFFIX["China"]


_EQUITY_PFX = ("600", "601", "603", "605", "688", "689",  # SH
               "000", "001", "002", "003", "300", "301",  # SZ
               "900", "200")                              # B
# NOT equities: 51x/58x ETFs, 50x LOFs, 93x indexes, 11x/12x
# bonds — Yahoo search returned these for some A-names (c-113:
# 'PING AN INS A' -> 510590.SS, an ETF)


def _china_consistent(name, tick):
    """Does a mapped ticker sit on the right venue for the
    name's share class? Bare 6-digit = A/B onshore code;
    bare <=5-digit = HK code (tier-A member keys). Onshore
    codes must be in EQUITY ranges (not fund/index/bond)."""
    c = _china_class(name)
    t = str(tick)
    code6 = (t[:6] if re.match(r"\d{6}\.(SS|SZ)$", t)
             else t if re.fullmatch(r"\d{6}", t) else None)
    onshore = bool(code6) and code6.startswith(_EQUITY_PFX)
    hk = t.endswith(".HK") or re.fullmatch(r"\d{1,5}", t)
    if c == "A":
        return bool(onshore)
    if c == "H":
        return bool(hk)
    return True     # B ambiguous (HK Class B vs onshore B)


def fix_china():
    """Null every China mapping whose venue contradicts the
    name's share class (correction recorded, not silent: prints
    each). Then rerun `run --retry-null` under the class-aware
    filter."""
    cache = json.loads(MAP.read_text(encoding="utf-8"))
    nulled = 0
    for k, v in sorted(cache.items()):
        if not (k.startswith("China|") and v):
            continue
        nm = k.split("|", 1)[1]
        if not _china_consistent(nm, v):
            print(f"NULLED {nm!r}: {v} is the wrong venue for "
                  f"class {_china_class(nm)}")
            cache[k] = None
            nulled += 1
    MAP.write_text(json.dumps(cache), encoding="utf-8")
    print(f"\n{nulled} wrong-venue China mappings nulled; "
          "rerun: py scripts\\ticker_backfill.py run "
          "--retry-null, then changes_db.py build")


def prefix_match(msci_name, member_names, validate=None):
    """Tier A2 (c-113): MSCI truncates TOKENS ('CHINA MERCH
    SEC A' = 'CHINA MERCHANTS SECURITIES A'), so match each
    MSCI token as a PREFIX of the member tokens in order
    (subsequence; single-char tokens exact — class letters).
    Returns the unique match or None (ambiguous/none). Safer
    than ratio-fuzzy: 'SEC' can never match 'BANK'."""
    q = norm(msci_name).split()
    # trailing HK C marker from '(HK-C)' is not part of a name
    while q and q[-1] in ("HK", "C") and len(q) > 2:
        q.pop()

    def _sub(qt, nm):
        c = norm(nm).split()
        i = 0
        for t in qt:
            while i < len(c) and not (
                    c[i] == t if len(t) == 1
                    else c[i].startswith(t)):
                i += 1
            if i == len(c):
                return False
            i += 1
        return True
    hits = [t for nm, t in member_names.items() if _sub(q, nm)]
    if not hits and len(q) > 2 and q[-1] in ("A", "B", "H"):
        # member names are TRUNCATED at ~30 chars, which can
        # drop the trailing class letter ('PING AN INSURANCE
        # (GROUP) OF CHINA' = the A line, 601318). Retry
        # without the class token, but ONLY on long (i.e.
        # truncated) names — the class must then be verified
        # by VENUE (caller: _china_consistent)
        # venue validation BEFORE the uniqueness test: both
        # the A and H member lines lose their class letter to
        # truncation (PING AN 601318 vs 2318) — the validator
        # (venue = class) disambiguates them
        hits = [t for nm, t in member_names.items()
                if len(str(nm)) >= 28 and _sub(q[:-1], nm)]
    if validate:
        hits = [t for t in hits if validate(t)]
    return hits[0] if len(hits) == 1 else None


def tier_a():
    mem = json.loads((ROOT / "data" / "apac_members.json")
                     .read_text(encoding="utf-8"))["markets"]
    out = {}
    for mkt, v in mem.items():
        for tick, nm in (v.get("names") or {}).items():
            if nm:
                out.setdefault(f"{mkt}|{norm(nm)}", tick)
    return out


def run(limit=None, retry_null=False):
    import difflib

    import pandas as pd
    import requests
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    cache = json.loads(MAP.read_text(encoding="utf-8")) if MAP.exists() else {}
    ta = tier_a()
    mem = json.loads((ROOT / "data" / "apac_members.json")
                     .read_text(encoding="utf-8"))["markets"]
    todo = []
    for mkt, g in df.groupby("market"):
        namesd = {norm(v): k for k, v in
                  (mem.get(mkt, {}).get("names") or {}).items()
                  if v}
        keys = list(namesd)
        for s in g.security.unique():
            key = f"{mkt}|{norm(s)}"
            if key in cache and (cache[key] or not retry_null):
                continue
            # tier A first (free)
            if key in ta:
                cache[key] = ta[key]
                continue
            # fuzzy only among names sharing the first token
            # (difflib over full lists was the bottleneck)
            tok = norm(s).split(" ")[0]
            cand = [k for k in keys if k.startswith(tok)]
            m = difflib.get_close_matches(norm(s), cand, n=1,
                                          cutoff=0.87)
            if m:
                cache[key] = namesd[m[0]]
                continue
            # tier A2: token-prefix match vs member names
            # (MSCI truncation-aware; unique-hit only; China
            # results must sit on the class-implied venue)
            pm = prefix_match(
                s, {k: namesd[k] for k in cand},
                validate=((lambda t, _s=s: _china_consistent(
                    _s, t)) if mkt == "China" else None))
            if pm:
                cache[key] = pm
                continue
            todo.append((mkt, s, key))
    MAP.write_text(json.dumps(cache), encoding="utf-8")        # persist tier A
    print(f"tier A/fuzzy done; {len(todo)} need Yahoo search")
    if limit:
        todo = todo[:int(limit)]
    ok = 0
    for i, (mkt, s, key) in enumerate(todo):
        try:
            j = requests.get(
                "https://query1.finance.yahoo.com/v1/finance/"
                "search", params={"q": clean_for_search(s),
                                  "quotesCount": 6},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15).json()
            got = None
            for q in j.get("quotes", []):
                sym = q.get("symbol", "")
                if any(sym.endswith(x)
                       for x in _suffixes_for(mkt, s)):
                    got = sym
                    break
            cache[key] = got
            ok += bool(got)
        except Exception:                      # noqa: BLE001
            pass                               # not cached: retry
        if (i + 1) % 10 == 0:
            MAP.write_text(json.dumps(cache), encoding="utf-8")
            print(f"  {i+1}/{len(todo)} (resolved {ok})")
        time.sleep(0.5)
    MAP.write_text(json.dumps(cache), encoding="utf-8")
    res = sum(1 for v in cache.values() if v)
    print(f"map: {res}/{len(cache)} resolved "
          f"({res/max(len(cache),1):.0%}); rerun until stable, "
          "then: py scripts\\changes_db.py build")


def status():
    cache = json.loads(MAP.read_text(encoding="utf-8")) if MAP.exists() else {}
    res = sum(1 for v in cache.values() if v)
    print(f"{res}/{len(cache)} resolved"
          if cache else "not started")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    lim = (sys.argv[sys.argv.index("--limit") + 1]
           if "--limit" in sys.argv else None)
    if cmd == "run":
        run(lim, retry_null="--retry-null" in sys.argv)
    elif cmd == "fix-china":
        fix_china()
    else:
        status()
