"""Off-cycle-exit verification (c-111) — classify every
'OUT — off-cycle exit (est.)' candidate.

Buckets (in resolution order):
  PARSE-ARTIFACT   its review-market cell is among the 21
                   defective cells (changes_db_validation) —
                   resolved by the per-cell parse repair
  STILL-TRADING    live quote exists -> REVIEW-MISS SUSPECT
                   (a deletion we failed to parse, or an
                   entity-resolution miss) -> manual/L4 queue
  DELISTED         no live quote -> consistent with a genuine
                   off-cycle exit (M&A/delisting)
  UNPROBEABLE      no resolved ticker yet (shrinks as the
                   ticker backfill completes)

Suffix handling: stored tickers may lack market suffixes; this
script tries the market's suffix list (from the member-census
conventions) before declaring dead.

Usage: py scripts\\offcycle_verify.py audit    (regenerate the
           candidate list from the current DB — run AFTER any
           ticker-map / DB rebuild; c-113: was ad-hoc in c-111)
       py scripts\\offcycle_verify.py run [--limit N]
       py scripts\\offcycle_verify.py status
Resumable: data/offcycle_verify_cache.json
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "offcycle_verify_cache.json"

SUFFIX = {"Taiwan": [".TW", ".TWO"], "Japan": [".T"],
          "Korea": [".KS", ".KQ"], "HongKong": [".HK"],
          "Australia": [".AX"], "India": [".NS", ".BO"],
          "Malaysia": [".KL"], "Indonesia": [".JK"],
          "Philippines": [".PS"], "Singapore": [".SI"],
          "Thailand": [".BK"], "NewZealand": [".NZ"],
          "China": [".SS", ".SZ", ".HK"]}


_ABBR = {"HLDG": "HOLDING", "HLDGS": "HOLDINGS",
         "INTL": "INTERNATIONAL", "GRP": "GROUP",
         "MFG": "MANUFACTURING", "SVCS": "SERVICES",
         "FINL": "FINANCIAL", "INDS": "INDUSTRIES",
         "TRANSP": "TRANSPORT"}
_DROP = {"CO", "LTD", "CORP", "INC", "COMPANY", "CORPORATION",
         "ADR", "THE", "LIMITED", "PLC", "HK"}


def audit():
    """Regenerate data/offcycle_exit_audit.csv from the current
    DB — the SAME entity/roster logic as history_explorer
    (ticker-first keys, China keeps share classes, strict
    standard_members). Candidate = last action ADD but NOT a
    current Standard member."""
    import pandas as pd
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    mem = json.loads((ROOT / "data" / "apac_members.json")
                     .read_text(encoding="utf-8"))["markets"]
    val = json.loads((ROOT / "data" /
                      "changes_db_validation.json").read_text(encoding="utf-8"))
    bad_cells = {(m["review"], m["market"])
                 for m in val["mismatches"]}
    rows = []
    for mkt in sorted(df.market.unique()):
        cls = {"A", "B", "H", "C"} if mkt != "China" else set()

        def _n(s, _cls=cls):
            s = re.sub(r"\(.*?\)", " ", str(s).upper())
            s = re.sub(r"[^A-Z0-9 ]", " ", s)
            toks = [_ABBR.get(t, t) for t in s.split()]
            while len(toks) > 1 and toks[-1] in (_DROP | _cls):
                toks.pop()
            return " ".join(toks)
        g = df[df.market == mkt].sort_values(["year", "month"])
        ent = {}
        for _, r in g.iterrows():
            t = str(r.get("ticker", "") or "")
            k = f"T:{t}" if t else _n(r.security)
            e = ent.setdefault(k, {"security": r.security,
                                   "ticker": t, "hist": []})
            e["security"] = r.security
            e["ticker"] = t or e["ticker"]
            e["hist"].append((r.review, r.action))
        _m = mem.get(mkt, {})
        _names = _m.get("names") or {}
        std = _m.get("standard_members", [])
        curn = {_n(_names.get(t) or t) for t in std}
        stdz = {s.lstrip("0") or "0" for s in std}
        for k, e in ent.items():
            rev, act = e["hist"][-1]
            if act != "ADD":
                continue
            tick = e["ticker"]
            root = tick.split(".")[0]
            # c-113 venue-aware member match: HK-listed codes
            # are stored zero-stripped in the member lists
            # ('0914.HK' must match '914'); onshore China
            # 6-digit codes keep their leading zeros (else
            # 000001 Ping An Bank would collide with 0001.HK)
            hk_form = (tick.endswith(".HK")
                       or (mkt in ("HongKong", "China")
                           and re.fullmatch(r"\d{1,5}", root)))
            is_mem = (_n(e["security"]) in curn
                      or tick in std
                      or root in std
                      or (hk_form
                          and (root.lstrip("0") or "0") in stdz))
            if is_mem:
                continue
            touches = any((rv, mkt) in bad_cells
                          for rv, _ in e["hist"])
            rows.append({"market": mkt,
                         "security": e["security"],
                         "last_add": rev, "ticker": tick,
                         "touches_defective_cell": touches})
    out = pd.DataFrame(rows).sort_values(
        ["market", "security"]).reset_index(drop=True)
    out.to_csv(ROOT / "data" / "offcycle_exit_audit.csv",
               index=False)
    n_t = int((out.ticker != "").sum())
    print(f"{len(out)} candidates | {n_t} with ticker | "
          f"{len(out) - n_t} unprobeable | "
          f"{int(out.touches_defective_cell.sum())} in "
          "defective cells -> data/offcycle_exit_audit.csv")
    print(out.groupby("market").size().to_string())
    return out


def run(limit=None):
    import pandas as pd
    import yfinance as yf
    oc = pd.read_csv(ROOT / "data" / "offcycle_exit_audit.csv"
                     ).fillna("")
    cache = (json.loads(CACHE.read_text(encoding="utf-8"))
             if CACHE.exists() else {})
    todo = []
    for _, r in oc.iterrows():
        key = f"{r.market}|{r.security}"
        if key in cache:
            continue
        if r.touches_defective_cell:
            cache[key] = {"bucket": "PARSE-ARTIFACT"}
            continue
        if not r.ticker:
            cache[key] = {"bucket": "UNPROBEABLE"}
            continue
        todo.append((key, r.market, str(r.ticker)))
    if limit:
        todo = todo[:int(limit)]
    print(f"{len(todo)} to probe "
          f"({sum(1 for v in cache.values() if v['bucket'] == 'PARSE-ARTIFACT')} parse-artifact, "
          f"{sum(1 for v in cache.values() if v['bucket'] == 'UNPROBEABLE')} unprobeable)")
    for i, (key, mkt, tick) in enumerate(todo):
        cands = ([tick] if "." in tick else
                 [tick + s for s in SUFFIX.get(mkt, [""])]
                 + [tick])
        bucket = "DELISTED"
        for sym in cands:
            try:
                px = yf.Ticker(sym).fast_info.get("lastPrice")
                if px and px > 0:
                    bucket = "STILL-TRADING (suspect)"
                    break
            except Exception:                  # noqa: BLE001
                continue
        cache[key] = {"bucket": bucket}
        if (i + 1) % 10 == 0:
            CACHE.write_text(json.dumps(cache), encoding="utf-8")
            print(f"  {i+1}/{len(todo)}")
        time.sleep(0.3)
    CACHE.write_text(json.dumps(cache), encoding="utf-8")
    status()


_EO_PATTERNS = ("AVIC", "AEROSPACE", "SPACESAT", "SHIPB",
                "DAWNING", "HIKVIS", "JIHUA", "CHONGQING CHANG",
                "RAIL HI TE", "CRRC", "SMIC",
                "SEMICONDUCTOR MFG", "CNOOC", "PANDA")


def classify():
    """c-113 final classification -> offcycle_exit_classified
    .csv. The EO-13959 tag marks names matching MSCI's OWN
    documented off-cycle sanction-deletion waves (close of Jan
    5/8/26 and Jul 26, 2021 — press release 02241939950);
    still-trading + valid ticker + not-a-member is exactly the
    sanction-exit signature. Tags are HYPOTHESES per name
    (TO_VERIFY); the mechanism is confirmed."""
    import pandas as pd
    oc = pd.read_csv(ROOT / "data" / "offcycle_exit_audit.csv"
                     ).fillna("")
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    rows = []
    for _, r in oc.iterrows():
        b = cache.get(f"{r.market}|{r.security}",
                      {}).get("bucket", "UNCLASSIFIED")
        note = ""
        if b.startswith("STILL"):
            if (r.market == "China" and any(
                    p in r.security.upper()
                    for p in _EO_PATTERNS)):
                note = ("EO-13959-pattern: matches MSCI's "
                        "documented 2021 sanction-deletion "
                        "waves (TO_VERIFY per name)")
            else:
                note = ("unexplained still-trading exit — "
                        "L4 queue (suspension/scandal/"
                        "entity-split candidates)")
        elif b == "UNPROBEABLE":
            note = ("no live ticker resolvable — consistent "
                    "with genuine delisting (Yahoo drops dead "
                    "symbols); NOT positively confirmed")
        rows.append({**r, "bucket": b, "note": note})
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "data" / "offcycle_exit_classified.csv",
               index=False)
    from collections import Counter
    c = Counter(out.bucket)
    eo = int(out.note.str.startswith("EO-13959").sum())
    print(f"{len(out)} rows -> offcycle_exit_classified.csv | "
          f"{dict(c)} | EO-pattern tagged: {eo}")
    return out


def status():
    if not CACHE.exists():
        print("not started")
        return
    from collections import Counter
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    c = Counter(v["bucket"] for v in cache.values())
    print(f"classified {len(cache)}: {dict(c)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    lim = (sys.argv[sys.argv.index("--limit") + 1]
           if "--limit" in sys.argv else None)
    if cmd == "run":
        run(lim)
    elif cmd == "audit":
        audit()
    elif cmd == "classify":
        classify()
    else:
        status()
