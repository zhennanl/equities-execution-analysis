"""MSCI APAC index-review changes database (c-97).

Parses all 46 archived STPublicList texts (2015-02 -> 2026-05,
data/msci_archive/) into one tidy table — every ADD/DEL for the
13 APAC Standard country indexes — and writes it as CSV +
pickle for fast querying.

Row schema: review (Feb15...), review_type (QIR/SAIR), year,
month, eff_date_est (last weekday of the review month — the
standard effective-close convention), market, action (ADD/DEL),
security (name as MSCI published it), code (TW only, joined
from the event registry where known).

VALIDATION: Taiwan totals are asserted against the
independently built msci_tw_events.json registry — if the PDF
parser and the registry disagree, the build fails loudly.

Usage:
  py scripts\\changes_db.py build
  py scripts\\changes_db.py query NANYA          (name substring)
  py scripts\\changes_db.py query 2408           (TW code)
Output: data/msci_changes_db.csv / .pkl
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "data" / "msci_archive"

MARKET_HDRS = {
    "TAIWAN": "Taiwan", "JAPAN": "Japan",
    "AUSTRALIA": "Australia", "HONG KONG": "HongKong",
    "KOREA": "Korea", "CHINA": "China", "INDIA": "India",
    "MALAYSIA": "Malaysia", "INDONESIA": "Indonesia",
    "PHILIPPINES": "Philippines", "NEW ZEALAND": "NewZealand",
    "SINGAPORE": "Singapore", "THAILAND": "Thailand"}
MONTHS = {"Feb": 2, "May": 5, "Aug": 8, "Nov": 11}
_JUNK = ("©", "msci.com", "Page ", "MSCI Global", "Nb of",
         "Securities", "GLOBAL STANDARD", "Region", "Country")


def _eff_est(year, month):
    import datetime as dt
    d = (dt.date(year + (month == 12), month % 12 + 1, 1)
         - dt.timedelta(days=1))
    while d.weekday() > 4:
        d -= dt.timedelta(days=1)
    return d.isoformat()


def parse_file(path):
    m = re.match(r"MSCI_([A-Z][a-z]{2})(\d{2})_", path.name)
    mon, yy = m.group(1), int(m.group(2))
    year = 2000 + yy
    month = MONTHS[mon]
    review = f"{mon}{yy:02d}"
    rtype = "SAIR" if mon in ("May", "Nov") else "QIR"
    lines = path.read_text(encoding="utf-8",
                           errors="ignore").splitlines()
    rows = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        hm = re.fullmatch(r"MSCI ([A-Z][A-Z ]+?) INDEX", line)
        if hm and hm.group(1) in MARKET_HDRS:
            market = MARKET_HDRS[hm.group(1)]
            j = i + 1
            off = None
            while j < min(i + 6, len(lines)):
                if "Additions" in lines[j] or \
                        "Deletions" in lines[j]:
                    off = (lines[j].index("Deletions")
                           if "Deletions" in lines[j] else 9999)
                    break
                j += 1
            if off is None:
                i += 1
                continue
            j += 1
            while j < len(lines):
                raw = lines[j]
                s = raw.strip()
                if s.startswith("MSCI ") and s.endswith("INDEX"):
                    break
                if any(k in raw for k in _JUNK):
                    j += 1
                    continue
                if not s:
                    if j + 1 < len(lines) and \
                            not lines[j + 1].strip():
                        break
                    j += 1
                    continue
                toks = re.split(r"\s{2,}", s)
                if len(toks) == 2 and "None" in toks:
                    nm = toks[1] if toks[0] == "None" else toks[0]
                    act = "DEL" if toks[0] == "None" else "ADD"
                    rows.append((review, rtype, year, month,
                                 market, act, nm))
                    j += 1
                    continue
                left = raw[:off].strip()
                right = raw[off:].strip()
                if left and left.upper() != "NONE":
                    rows.append((review, rtype, year, month,
                                 market, "ADD", left))
                if right and right.upper() != "NONE":
                    rows.append((review, rtype, year, month,
                                 market, "DEL", right))
                j += 1
            i = j
        else:
            i += 1
    return rows


def build():
    import pandas as pd
    all_rows = []
    for p in sorted(ARCH.glob("*STPublicList.txt")):
        all_rows += parse_file(p)
    df = pd.DataFrame(all_rows, columns=[
        "review", "review_type", "year", "month", "market",
        "action", "security"])
    # c-112: apply the per-cell PATCH LAYER (21 defective
    # cells repaired against MSCI's own count tables; see
    # scripts/parse_repair.py — patches replace those cells'
    # rows wholesale, the parser itself stays untouched)
    pp = ROOT / "data" / "changes_db_patches.json"
    if pp.exists():
        patches = json.loads(pp.read_text(encoding="utf-8"))["patches"]
        drop = set()
        extra = []
        for key, p in patches.items():
            rev, mkt = key.split("|")
            drop.add((rev, mkt))
            row0 = df[(df.review == rev)]
            yr = int("20" + rev[3:])
            mo = MONTHS[rev[:3]]
            rt = "SAIR" if rev[:3] in ("May", "Nov") else "QIR"
            for nm in p["adds"]:
                extra.append((rev, rt, yr, mo, mkt, "ADD", nm))
            for nm in p["dels"]:
                extra.append((rev, rt, yr, mo, mkt, "DEL", nm))
        df = df[~df.apply(lambda r: (r.review, r.market)
                          in drop, axis=1)]
        df = pd.concat([df, pd.DataFrame(extra,
                        columns=df.columns)],
                       ignore_index=True)
    df["eff_date_est"] = [
        _eff_est(y, mo) for y, mo in zip(df.year, df.month)]
    # join TW codes from the independent registry
    ev = json.loads((ROOT / "data" / "msci_tw_events.json")
                    .read_text(encoding="utf-8"))
    name2code = {}
    for v in ev.values():
        for c, n in {**v.get("adds", {}),
                     **v.get("dels", {})}.items():
            if n:
                name2code[n.upper()] = c
    df["code"] = [
        name2code.get(s.upper(), "") if mk == "Taiwan" else ""
        for s, mk in zip(df.security, df.market)]
    # c-102: local tickers from the resolver map (all markets);
    # TW registry code wins where present
    tmap = {}
    tp = ROOT / "data" / "security_ticker_map.json"
    if tp.exists():
        tmap = json.loads(tp.read_text(encoding="utf-8"))
    import re as _re

    def _norm(s):
        s = _re.sub(r"[^A-Z0-9 ]", " ", str(s).upper())
        return _re.sub(r"\s+", " ", s).strip()
    df["ticker"] = [
        c or (tmap.get(f"{mk}|{_norm(s)}") or "")
        for c, s, mk in zip(df.code, df.security, df.market)]
    df = df.sort_values(["year", "month", "market", "action",
                         "security"]).reset_index(drop=True)

    # VALIDATION vs the TW registry (independent build).
    # KNOWN DIFF (c-97, found BY this validation): the Feb-2026
    # QIR added "HONPRECISION" ("Hon. Precision" per the QIRPR
    # — a late-2025 TW listing) which msci_tw_events.json
    # MISSED (+0/-4 vs MSCI's +1/-4). The DB carries the row as
    # published; the registry fix (local code resolution) is a
    # registered task — NOT silently patched here.
    KNOWN_REGISTRY_GAPS_ADDS = 1
    # c-104: archive extended to Feb-2006; the TW registry
    # covers 2015+ only, so validation scopes to that era
    tw = df[(df.market == "Taiwan") & (df.year >= 2015)]
    reg_adds = sum(len(v.get("adds", {})) for v in ev.values())
    reg_dels = sum(len(v.get("dels", {})) for v in ev.values())
    got_adds = int((tw.action == "ADD").sum())
    got_dels = int((tw.action == "DEL").sum())
    assert got_adds == reg_adds + KNOWN_REGISTRY_GAPS_ADDS, \
        f"TW adds {got_adds} != registry {reg_adds} + known 1"
    assert got_dels == reg_dels, \
        f"TW dels {got_dels} != registry {reg_dels}"

    df.to_csv(ROOT / "data" / "msci_changes_db.csv",
              index=False)
    df.to_pickle(ROOT / "data" / "msci_changes_db.pkl")
    print(f"{len(df)} rows | {df.review.nunique()} reviews | "
          f"markets: {df.market.nunique()} | TW validated "
          f"({got_adds} adds / {got_dels} dels == registry)")
    print(df.groupby("market").action.count().to_string())
    return df


def query(term):
    import pandas as pd
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    t = term.upper()
    hit = df[(df.security.str.upper().str.contains(t,
                                                   regex=False))
             | (df.code == term)]
    if hit.empty:
        print(f"no rows for {term!r}")
    else:
        print(hit[["review", "market", "action", "security",
                   "code", "eff_date_est"]].to_string(
            index=False))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        build()
    else:
        query(" ".join(sys.argv[2:]) if cmd == "query"
              else cmd)


def validate_counts():
    """c-109: exhaustive validation vs MSCI's OWN per-country
    count tables in every list — the systematic answer to 'did
    we omit review entries?'. Known state: 21 defective cells
    of 590 (3.6%), enumerated below; repair = careful per-cell
    re-parse (a naive page-aware rewrite REGRESSED to 93 and
    was reverted — c-109 lesson)."""
    import re as _re
    from pathlib import Path as _P

    import pandas as pd
    CN = {"TAIWAN": "Taiwan", "JAPAN": "Japan",
          "AUSTRALIA": "Australia", "HONG KONG": "HongKong",
          "KOREA": "Korea", "CHINA": "China", "INDIA": "India",
          "MALAYSIA": "Malaysia", "INDONESIA": "Indonesia",
          "PHILIPPINES": "Philippines",
          "NEW ZEALAND": "NewZealand",
          "SINGAPORE": "Singapore", "THAILAND": "Thailand"}
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    ours = df.groupby(["review", "market", "action"]).size()
    mism, checked = [], 0
    for p in sorted((ROOT / "data" / "msci_archive")
                    .glob("*STPublicList.txt")):
        rev = _re.match(r"MSCI_([A-Za-z]{3}\d{2})_",
                        p.name).group(1)
        for m in _re.finditer(
                r"^\s{4,}([A-Z][A-Z ]+?)\s{2,}(\d+)\s{2,}"
                r"(\d+)\s*$", p.read_text(errors="ignore"),
                _re.M):
            c = m.group(1).strip()
            if c not in CN:
                continue
            mkt = CN[c]
            oa, od = int(m.group(2)), int(m.group(3))
            pa = int(ours.get((rev, mkt, "ADD"), 0))
            pdd = int(ours.get((rev, mkt, "DEL"), 0))
            checked += 1
            if (oa, od) != (pa, pdd):
                mism.append({"review": rev, "market": mkt,
                             "official": [oa, od],
                             "parsed": [pa, pdd]})
    out = {"cells_checked": checked, "mismatches": mism,
           "n_mismatch": len(mism)}
    (ROOT / "data" / "changes_db_validation.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(f"{checked} cells | {len(mism)} mismatches "
          "-> data/changes_db_validation.json")
    return out
