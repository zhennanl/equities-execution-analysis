"""Cross-listing check: whose company is it? (c-172)

THE PROBLEM THIS SOLVES. New Zealand's size ladder was topped
by Westpac ($91.8B) and ANZ ($80.2B) — Australian banks with a
secondary NZ listing, carrying their group market caps. MSCI
New Zealand does not hold them. Left in, they occupy the top
two ranks, and since the seed cutoff is the cap at rank N, two
foreign names shift the entire cutoff and therefore the whole
shortlist. The same shape appears in Singapore and Hong Kong.

WHAT IT DOES. Yahoo's quoteSummary carries
assetProfile.country, verified against known cases:
    WBC.NZ -> Australia      ANZ.NZ  -> Australia
    IFT.NZ -> New Zealand    D05.SI  -> Singapore
    0700.HK -> China
One call per symbol, so it is scoped to the names that can
actually move the cutoff — everything above a fraction of the
seed cutoff — not the whole market.

WHAT IT DELIBERATELY DOES NOT DO: exclude anything.

MSCI's country assignment is NOT country of incorporation. The
GIMI methodology assigns a company to a country using
incorporation AND primary listing together, with explicit
special cases, which is why Jardine (Bermuda-incorporated,
Singapore-listed) sits in MSCI Singapore and why most
HK-listed mainland companies sit in MSCI China rather than
MSCI Hong Kong. Auto-dropping on incorporation would
introduce a new error to fix an old one. So this FLAGS and
the analyst decides — the flag is written into the size file
so the shortlist carries it forward.

Run:  py scripts\\apac_country_check.py             (all)
      py scripts\\apac_country_check.py NewZealand  (one)
Out:  data/apac_size/<Market>.json gains `country` and
      `country_flag` per row, plus a `country_check` summary.
"""
import concurrent.futures as cf
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "apac_size"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# what assetProfile.country should say for a domestic name
EXPECT = {
    "Japan": {"Japan"}, "HongKong": {"Hong Kong"},
    "China": {"China", "Hong Kong"},
    "Korea": {"South Korea"}, "Thailand": {"Thailand"},
    "Malaysia": {"Malaysia"}, "Indonesia": {"Indonesia"},
    "Singapore": {"Singapore"}, "India": {"India"},
    "Australia": {"Australia"}, "NewZealand": {"New Zealand"},
    "Taiwan": {"Taiwan"},
}


def _session():
    import requests
    s = requests.Session()
    s.headers.update(UA)
    s.get("https://fc.yahoo.com", timeout=20)
    c = s.get("https://query1.finance.yahoo.com/v1/test/getcrumb",
              timeout=20).text.strip()
    if not c or "<" in c:
        raise SystemExit("no crumb — Yahoo refused the session")
    return s, c


def _country(s, crumb, sym):
    try:
        j = s.get("https://query1.finance.yahoo.com/v10/finance/"
                  f"quoteSummary/{sym}?modules=assetProfile"
                  f"&crumb={crumb}", timeout=25).json()
        res = (j.get("quoteSummary", {}).get("result") or [{}])[0]
        return sym, (res.get("assetProfile") or {}).get("country")
    except Exception:                              # noqa: BLE001
        return sym, None


def check(market, depth=200, floor_frac=0.35):
    f = OUT / f"{market}.json"
    if not f.exists():
        print(f"{market}: no size file — run apac_size_harvest")
        return
    d = json.loads(f.read_text(encoding="utf-8"))
    rows = d["rows"]
    # scope: only names big enough to influence the cutoff
    import importlib
    sys.path.insert(0, str(ROOT / "scripts"))
    ash = importlib.import_module("apac_size_harvest")
    seed, _ = ash.derive_cutoff(market)
    lim = (seed or 0) * floor_frac
    todo = [k for k, v in list(rows.items())[:depth]
            if v["cap_usd_b"] >= lim]
    if not todo:
        todo = list(rows)[:depth]
    print(f"\n{market}: checking {len(todo)} names above "
          f"${lim:.2f}B (seed cutoff ${seed or 0:.2f}B)")
    s, crumb = _session()
    got = {}
    with cf.ThreadPoolExecutor(6) as ex:
        for i, (sym, c) in enumerate(
                ex.map(lambda x: _country(s, crumb, x), todo), 1):
            got[sym] = c
            if i % 50 == 0:
                print(f"    {i}/{len(todo)}", flush=True)
    exp = EXPECT.get(market, set())
    flagged = []
    for sym, c in got.items():
        rows[sym]["country"] = c
        bad = bool(c) and c not in exp
        rows[sym]["country_flag"] = ("FOREIGN — verify against "
                                     "MSCI country assignment"
                                     if bad else None)
        if bad:
            flagged.append((sym, rows[sym]["name"][:34], c,
                            rows[sym]["cap_usd_b"]))
    flagged.sort(key=lambda x: -x[3])
    d["country_check"] = {
        "checked": len(todo), "flagged": len(flagged),
        "expected": sorted(exp),
        "policy": "FLAG ONLY — MSCI assigns country by "
                  "incorporation AND primary listing with "
                  "special cases, so incorporation alone must "
                  "not delete a name.",
        "names": [{"symbol": a, "name": b, "country": c,
                   "cap_usd_b": e} for a, b, c, e in flagged]}
    f.write_text(json.dumps(d, indent=1), encoding="utf-8")
    print(f"  {len(flagged)} flagged of {len(todo)}")
    for a, b, c, e in flagged[:8]:
        print(f"    {a:12} {b:34} {c:14} ${e:,.1f}B")
    return flagged


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "scripts"))
    from markets import is_active
    for m in (sys.argv[1:] or sorted(
            p.stem for p in OUT.glob("*.json"))):
        if not is_active(m):
            continue
        check(m)
        time.sleep(1)
