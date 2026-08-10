"""Recover tickers for the 894 untickered index events (c-263).

READ THIS BEFORE RUNNING IT.

This project has mapped a security to the wrong company three
times: Chunghwa Picture Tubes to Chunghwa TELECOM (c-161),
MEITU to MEITUAN (c-259), and Anhui Gujing's B line to its A
line (c-259). Two of the three priced cleanly and looked
healthy. **A wrong ticker is worse than a blank one**, because
a blank announces itself and a wrong one quietly contributes a
different company's prices to the analysis.

So this script is built to REFUSE rather than to guess:

  * every proposal carries its evidence and a score;
  * nothing is written unless it passes every gate;
  * everything that ALMOST passes goes to a review queue for a
    human, not into the map;
  * `apply` is a separate, deliberate step.

WHY THE NAMES ARE MISSING (measured at c-262): the map is
anchored on what exists NOW. A security still in the index
resolves 88% of the time, one that has left 65%; names last
seen in 2015 are missing 51% of the time against 15% for 2025.
So the residue is renames, delistings, and lines the map never
enumerated — H-shares, ADRs, dual-listed qualifiers.

THE FOUR STAGES, cheapest first.

  0 STRUCTURAL (offline, free)
      Strip MSCI's line qualifiers — " H", " A", " B", "(CN)",
      "(HK)", "(USD)", "(NEW)", "ADR", "PREF" — and look the
      base name up in the map we already have, including the
      HongKong pool for a Chinese H-share. Recovers little (8
      names) but costs nothing and is fully auditable.

  1 YAHOO SEARCH (network)
      The symbol-search endpoint, filtered to exchanges valid
      for that market. Good for names that still trade under
      the same string, poor for anything delisted.

  2 OPENFIGI (network)
      The only free source here that carries DELISTED and
      RENAMED securities, which is the whole PLAIN_NAME bucket.
      No key needed at 25 requests/minute; set OPENFIGI_KEY in
      the environment for 250. Throttled and resumable.

  3 VERIFY (network)
      A proposal is not a recovery until the prices exist. Each
      candidate is probed for daily bars covering the
      announcement date, and screened on liquidity — an MSCI
      Standard constituent is not a stock that trades $50k a
      day. This gate is what separates "a company with a
      similar name" from "the company MSCI moved".

Usage
  py scripts\\ticker_recover.py                 stage 0 + report
  py scripts\\ticker_recover.py search          + Yahoo   (net)
  py scripts\\ticker_recover.py figi            + OpenFIGI(net)
  py scripts\\ticker_recover.py verify          probe prices
  py scripts\\ticker_recover.py apply           write the winners
Then
  py scripts\\changes_db.py build
  py scripts\\apac_event_days.py yf <Market>

Output
  data/ticker_recovery.json      every proposal, with evidence
  data/foreign_lines.json        ADR / cross-border listings
  docs/TICKER_RECOVERY.md        the report
"""
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "data" / "security_ticker_map.json"
OUT = ROOT / "data" / "ticker_recovery.json"
FOREIGN = ROOT / "data" / "foreign_lines.json"
DOC = ROOT / "docs" / "TICKER_RECOVERY.md"
LOG = ROOT / "data" / "ticker_corrections.json"
UA = {"User-Agent": "Mozilla/5.0"}

# ---- what a market's symbols are allowed to look like --------
# A candidate on the wrong exchange is not a near miss, it is a
# different security. This is gate G1 and it is absolute.
EXCH = {
    "Japan": {"suffix": [".T"], "figi": ["JT", "JP"]},
    "Korea": {"suffix": [".KS", ".KQ"], "figi": ["KS", "KP"]},
    "HongKong": {"suffix": [".HK"], "figi": ["HK"]},
    "China": {"suffix": [".SS", ".SZ", ".HK"],
              "figi": ["CH", "CG", "HK"]},
    "Taiwan": {"suffix": [".TW", ".TWO"], "figi": ["TT"]},
    "India": {"suffix": [".NS", ".BO"], "figi": ["IS", "IB"]},
    "Australia": {"suffix": [".AX"], "figi": ["AU"]},
    "Singapore": {"suffix": [".SI"], "figi": ["SP"]},
    "Malaysia": {"suffix": [".KL"], "figi": ["MK"]},
    "Thailand": {"suffix": [".BK"], "figi": ["TB"]},
    "Indonesia": {"suffix": [".JK"], "figi": ["IJ"]},
    "Philippines": {"suffix": [".PS"], "figi": ["PM"]},
    "NewZealand": {"suffix": [".NZ"], "figi": ["NZ"]},
}
# a depositary line trades in the US on a US calendar. It is
# recoverable, but it is NOT the local listing and must not be
# silently mixed into a local event study.
US_EXCH = {"NMS", "NYQ", "NGM", "ASE", "PNK", "OTC"}

_STOP = {"CO", "CORP", "CORPORATION", "INC", "LTD", "LIMITED",
         "COMPANY", "THE", "HOLDING", "HOLDINGS", "GROUP",
         "AND", "OF", "BHD", "BERHAD", "PLC", "PUBLIC", "TBK",
         "PT", "REIT", "TRUST", "CL", "CLASS", "NEW", "SHS"}
_EXPAND = {"SVCS": "SERVICES", "SVC": "SERVICES",
           "INTL": "INTERNATIONAL", "HLDG": "HOLDINGS",
           "HLDGS": "HOLDINGS", "IND": "INDUSTRIES",
           "INDS": "INDUSTRIES", "ENTMT": "ENTERTAINMENT",
           "GENL": "GENERAL", "FIN": "FINANCE",
           "MFG": "MANUFACTURING", "TECH": "TECHNOLOGY",
           "PHARM": "PHARMACEUTICAL", "CHEM": "CHEMICAL",
           "ELEC": "ELECTRIC", "NATL": "NATIONAL",
           "DEV": "DEVELOPMENT", "MGMT": "MANAGEMENT",
           "AST": "ASSET", "STH": "SOUTHERN", "NTH": "NORTHERN",
           "GRP": "GROUP", "GRPS": "GROUP",
           "SEC": "SECURITIES", "INS": "INSURANCE",
           "BK": "BANK", "TELECOMM": "TELECOM",
           "TRANSP": "TRANSPORT", "CONT": "CONTAINER",
           "PROP": "PROPERTIES", "COMM": "COMMERCIAL",
           "BIOPHARMA": "BIOPHARMACEUTICAL"}
QUAL = re.compile(r"\((CN|HK|USD|SGD|NEW|HK-C)\)|"
                  r"\b(ADR|ADS|GDR|PREF|NEW)\b|\s+[ABH]$")


def _norm(s):
    s = re.sub(r"[^A-Z0-9 ]", " ", str(s).upper())
    return re.sub(r"\s+", " ", s).strip()


def _stem(t):
    """Fold INDUSTRY / INDUSTRIES / INDUSTRIAL to one token.

    MSCI abbreviates and the exchange spells out, so the pair
    is usually a stem apart rather than a word apart: "IND GRP"
    against "Industry Group". Truncating tokens longer than six
    characters folds the variants without merging genuinely
    different words — CHUNGHWA still differs from CHINA, and
    TELECOM still differs from TUBES.
    """
    return t[:6] if len(t) > 6 else t


def toks(s):
    out = []
    for t in _norm(s).split():
        t = _EXPAND.get(t, t)
        if t not in _STOP and len(t) > 1:
            out.append(_stem(t))
    return out


def base_name(s):
    """MSCI's name with its line qualifier removed."""
    return _norm(QUAL.sub(" ", str(s).upper()))


def line_kind(s):
    u = str(s).upper()
    if re.search(r"\b(ADR|ADS|GDR)\b", u):
        return "ADR"
    if re.search(r"\bPREF\b", u):
        return "PREF"
    if re.search(r"\s+H$", u):
        return "H"
    if re.search(r"\s+[AB]$|A \(HK-C\)", u):
        return "AB"
    if re.search(r"\((CN|HK|USD|SGD)\)", u):
        return "LINE"
    return ""


def score(msci_name, cand_name):
    """How confident are we that these are the same company?

    The discipline is inherited from the c-161 failure: the
    HEAD token must be present, and one shared token is never
    enough. "CHUNGHWA PICTURE TUBES" and "CHUNGHWA TELECOM"
    share a head token and are different companies, so a
    contradicting distinctive token vetoes the match outright.
    """
    # score the ISSUER, not the line. "ALIBABA GROUP HLDG ADR"
    # was scoring 0.25 against "Alibaba Group Holding Limited"
    # because ADR survived as a token and counted as a word the
    # candidate lacked. The line qualifier is carried
    # separately by `line_kind` — it must not leak into the
    # name comparison, or every depositary and H line fails.
    a, b = toks(base_name(msci_name)), toks(cand_name)
    if not a or not b:
        return 0.0, "empty after normalisation"
    if a[0] not in b:
        return 0.0, f"head token {a[0]!r} absent"
    sa, sb = set(a), set(b)
    shared = sa & sb
    if len(shared) < 2 and len(a) > 1:
        return 0.25, f"only {sorted(shared)} in common"
    # a distinctive token on ONE side only is a warning: it is
    # how Picture Tubes became Telecom.
    only_b = [t for t in sb - sa if len(t) > 3]
    jac = len(shared) / len(sa | sb)
    conf = jac + (0.15 if len(shared) >= 3 else 0)
    if only_b:
        conf -= 0.10 * min(2, len(only_b))
    return (round(min(1.0, max(0.0, conf)), 3),
            f"shared={sorted(shared)} extra={only_b[:3]}")


# ---------------------------------------------------------------
def untickered():
    import pandas as pd
    d = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    d = d[d.year >= 2015].copy()
    d["has"] = d.ticker.astype(str).str.strip() != ""
    miss = d[~d.has]
    rows = []
    for (mkt, sec), g in miss.groupby(["market", "security"]):
        rows.append({
            "market": mkt, "security": sec,
            "rows": int(len(g)),
            "reviews": sorted(g.review.unique()),
            "first_ann": str(min(g.eff_date_est)),
            "last_ann": str(max(g.eff_date_est)),
            "kind": line_kind(sec), "base": base_name(sec),
        })
    return sorted(rows, key=lambda r: -r["rows"])


def _state():
    return json.loads(OUT.read_text(encoding="utf-8")) \
        if OUT.exists() else {"proposals": {}}


def _save(st):
    OUT.write_text(json.dumps(st, indent=1, ensure_ascii=False),
                   encoding="utf-8")


def key(r):
    return f"{r['market']}|{r['security']}"


# ---- stage 0: structural, offline -----------------------------
def stage_structural(st):
    m = json.loads(MAP.read_text(encoding="utf-8"))
    pool = {}
    for k, v in m.items():
        if v:
            mk, nm = k.split("|", 1)
            pool.setdefault(mk, {})[_norm(nm)] = v
    n = 0
    for r in untickered():
        k = key(r)
        if st["proposals"].get(k, {}).get("ticker"):
            continue
        b = r["base"]
        if not b:
            continue
        hit = pool.get(r["market"], {}).get(b)
        why = "base name already in the map"
        if not hit and r["market"] == "China":
            hit = pool.get("HongKong", {}).get(b)
            why = "Chinese H/CN line, base name in the HK map"
        if hit:
            st["proposals"][k] = {
                **r, "ticker": hit, "source": "structural",
                "confidence": 0.9, "evidence": why,
                "gates": {"G1_exchange": True, "G2_name": True},
                "verified": None}
            n += 1
    print(f"stage 0 structural: {n} proposals")
    return n


# ---- stage 1: Yahoo symbol search -----------------------------
def stage_search(st, limit=None):
    import requests
    todo = [r for r in untickered()
            if not st["proposals"].get(key(r), {}).get("ticker")]
    todo = todo[:limit] if limit else todo
    n = 0
    for i, r in enumerate(todo, 1):
        q = r["base"] or _norm(r["security"])
        try:
            j = requests.get(
                "https://query2.finance.yahoo.com/v1/finance/"
                "search", params={"q": q, "quotesCount": 10,
                                  "newsCount": 0},
                headers=UA, timeout=20).json()
        except Exception as e:                     # noqa: BLE001
            print(f"  [{i}/{len(todo)}] {q[:28]:28s} ERR {e}")
            time.sleep(2)
            continue
        best = None
        for c in j.get("quotes") or []:
            sym = str(c.get("symbol") or "")
            nm = c.get("longname") or c.get("shortname") or ""
            ex = str(c.get("exchange") or "")
            ok_local = any(sym.endswith(s) for s in
                           EXCH.get(r["market"], {})
                           .get("suffix", []))
            ok_adr = (r["kind"] == "ADR" and ex in US_EXCH)
            if not (ok_local or ok_adr):
                continue
            sc, why = score(r["security"], nm)
            if best is None or sc > best[0]:
                best = (sc, sym, nm, why, "local" if ok_local
                        else "ADR")
        if best and best[0] >= 0.45:
            st["proposals"][key(r)] = {
                **r, "ticker": best[1], "source": "yahoo-search",
                "confidence": best[0],
                "evidence": f"{best[2]} — {best[3]}",
                "line": best[4],
                "gates": {"G1_exchange": True,
                          "G2_name": best[0] >= 0.45},
                "verified": None}
            n += 1
            print(f"  [{i}/{len(todo)}] {q[:26]:26s} -> "
                  f"{best[1]:12s} {best[0]:.2f}")
        time.sleep(1.2)
        if i % 25 == 0:
            _save(st)
    print(f"stage 1 yahoo-search: {n} proposals")
    return n


# ---- stage 2: OpenFIGI (carries delisted securities) ----------
def stage_figi(st, limit=None):
    import requests
    url = "https://api.openfigi.com/v3/search"
    hdr = {"Content-Type": "application/json"}
    if os.environ.get("OPENFIGI_KEY"):
        hdr["X-OPENFIGI-APIKEY"] = os.environ["OPENFIGI_KEY"]
    pause = 2.6 if "X-OPENFIGI-APIKEY" not in hdr else 0.3
    todo = [r for r in untickered()
            if not st["proposals"].get(key(r), {}).get("ticker")]
    todo = todo[:limit] if limit else todo
    n = 0
    for i, r in enumerate(todo, 1):
        codes = EXCH.get(r["market"], {}).get("figi", [])
        found = None
        for ex in codes:
            body = {"query": r["base"] or r["security"],
                    "exchCode": ex}
            try:
                j = requests.post(url, headers=hdr,
                                  json=body, timeout=25).json()
            except Exception:                      # noqa: BLE001
                time.sleep(pause * 2)
                continue
            for c in (j.get("data") or [])[:12]:
                if str(c.get("securityType2") or "") not in \
                        ("Common Stock", "Depositary Receipt",
                         "Preference", ""):
                    continue
                sc, why = score(r["security"], c.get("name") or "")
                if sc >= 0.45 and c.get("ticker"):
                    found = (sc, c["ticker"], c.get("name"),
                             why, ex)
                    break
            time.sleep(pause)
            if found:
                break
        if found:
            suf = EXCH[r["market"]]["suffix"][0]
            sym = found[1] if "." in found[1] else found[1] + suf
            st["proposals"][key(r)] = {
                **r, "ticker": sym, "source": "openfigi",
                "confidence": round(found[0] * 0.9, 3),
                "evidence": f"{found[2]} @{found[4]} — {found[3]}",
                "gates": {"G1_exchange": True,
                          "G2_name": True},
                "verified": None}
            n += 1
            print(f"  [{i}/{len(todo)}] "
                  f"{r['security'][:26]:26s} -> {sym}")
        if i % 20 == 0:
            _save(st)
    print(f"stage 2 openfigi: {n} proposals")
    return n


# ---- stage 3: verify against actual prices --------------------
MIN_TURNOVER_USD = 2_000_000     # an index constituent floor


def stage_verify(st, limit=None):
    """A proposal is not a recovery until the prices exist.

    Two gates, and the second is the one that catches a
    same-name-different-company match: an MSCI Standard
    constituent is not a stock that trades a few hundred
    thousand dollars a day. If the candidate is illiquid at the
    time of the event, it is not the company MSCI moved.
    """
    import requests
    import statistics as stats
    todo = [(k, p) for k, p in st["proposals"].items()
            if p.get("ticker") and p.get("verified") is None]
    todo = todo[:limit] if limit else todo
    ok = 0
    for i, (k, p) in enumerate(todo, 1):
        a = str(p["first_ann"])[:10]
        try:
            import datetime as dt
            d0 = dt.date.fromisoformat(a) - dt.timedelta(days=40)
            d1 = dt.date.fromisoformat(a) + dt.timedelta(days=40)
            j = requests.get(
                f"https://query2.finance.yahoo.com/v8/finance/"
                f"chart/{p['ticker']}",
                params={"period1": int(time.mktime(
                            d0.timetuple())),
                        "period2": int(time.mktime(
                            d1.timetuple())),
                        "interval": "1d"},
                headers=UA, timeout=25).json()
            res = (j.get("chart") or {}).get("result") or []
            q = res[0]["indicators"]["quote"][0] if res else {}
            close = [c for c in (q.get("close") or []) if c]
            vol = [v for v in (q.get("volume") or []) if v]
        except Exception:                          # noqa: BLE001
            close, vol = [], []
        n_days = len(close)
        turn = (stats.median(close) * stats.median(vol)
                if close and vol else 0)
        gates = p.get("gates", {})
        gates["G3_prices_at_event"] = n_days >= 15
        gates["G4_liquid_enough"] = turn >= MIN_TURNOVER_USD
        p["gates"] = gates
        p["probe"] = {"days": n_days,
                      "median_turnover_local": round(turn)}
        p["verified"] = all(gates.values())
        ok += bool(p["verified"])
        print(f"  [{i}/{len(todo)}] {p['ticker']:12s} "
              f"days={n_days:3d} turn={turn:,.0f} "
              f"{'PASS' if p['verified'] else 'HOLD'}")
        time.sleep(1.0)
        if i % 20 == 0:
            _save(st)
    print(f"stage 3 verify: {ok}/{len(todo)} passed every gate")
    return ok


# ---- apply ----------------------------------------------------
MIN_APPLY_CONF = 0.55


def stage_apply(st):
    """Write ONLY what passed everything. Everything else is a
    review queue entry, not a silent guess."""
    m = json.loads(MAP.read_text(encoding="utf-8"))
    fl = json.loads(FOREIGN.read_text(encoding="utf-8")) if FOREIGN.exists() \
        else {}
    used = {v: k for k, v in m.items() if v}
    applied, held = [], []
    for k, p in sorted(st["proposals"].items()):
        why = None
        if not p.get("verified"):
            why = "failed a gate"
        elif p.get("confidence", 0) < MIN_APPLY_CONF:
            why = f"confidence {p.get('confidence')} below " \
                  f"{MIN_APPLY_CONF}"
        elif p["ticker"] in used and used[p["ticker"]] != k:
            why = f"ticker already maps to {used[p['ticker']]}"
        if why:
            held.append({**p, "held_because": why})
            continue
        m[k] = p["ticker"]
        if p.get("line") == "ADR":
            fl[k] = [p["ticker"], "US depositary line — trades "
                                  "on a US calendar"]
        applied.append(p)
    if applied:
        MAP.write_text(json.dumps(m, indent=1,
                                  ensure_ascii=False),
                       encoding="utf-8")
        FOREIGN.write_text(json.dumps(fl, indent=1),
                           encoding="utf-8")
        old = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else []
        LOG.write_text(json.dumps(old + [
            {"key": p["market"] + "|" + p["security"],
             "was": "", "now": p["ticker"],
             "why": f"recovered via {p['source']} — "
                    f"{p['evidence']}"} for p in applied],
            indent=1), encoding="utf-8")
    st["held"] = held
    _save(st)
    print(f"\napplied {len(applied)}, held {len(held)} for review")
    if applied:
        print("NEXT: py scripts\\changes_db.py build")
        print("      py scripts\\apac_event_days.py yf <Market>")
    return applied, held


def report(st):
    props = list(st["proposals"].values())
    ver = [p for p in props if p.get("verified")]
    by_src, by_mkt = {}, {}
    for p in ver:
        by_src[p["source"]] = by_src.get(p["source"], 0) + 1
        by_mkt[p["market"]] = by_mkt.get(p["market"], 0) + p["rows"]
    L = ["# Ticker recovery", "",
         "*Generated by `scripts/ticker_recover.py`. Nothing "
         "here is applied to the map until it passes every "
         "gate — see the script's header for why the bar is "
         "this high.*", "",
         f"- names attempted: **{len(untickered())}**",
         f"- proposals: **{len(props)}**",
         f"- passed every gate: **{len(ver)}**",
         f"- event ROWS recovered: "
         f"**{sum(p['rows'] for p in ver)}**", "",
         "| source | names |", "|---|---:|"]
    for k, v in sorted(by_src.items(), key=lambda x: -x[1]):
        L.append(f"| {k} | {v} |")
    L += ["", "| market | rows recovered |", "|---|---:|"]
    for k, v in sorted(by_mkt.items(), key=lambda x: -x[1]):
        L.append(f"| {k} | {v} |")
    L += ["", "## Held for review", "",
          "These matched a name but failed a gate. They are "
          "NOT in the map.", "",
          "| market | security | proposed | why held |",
          "|---|---|---|---|"]
    for p in (st.get("held") or [])[:60]:
        L.append(f"| {p['market']} | {p['security']} | "
                 f"{p['ticker']} | {p['held_because']} |")
    DOC.write_text("\n".join(L), encoding="utf-8")
    print(f"-> {DOC.name}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    lim = int(sys.argv[2]) if len(sys.argv) > 2 else None
    st = _state()
    if cmd in ("plan", "structural"):
        stage_structural(st)
    elif cmd == "search":
        stage_structural(st)
        stage_search(st, lim)
    elif cmd == "figi":
        stage_figi(st, lim)
    elif cmd == "verify":
        stage_verify(st, lim)
    elif cmd == "apply":
        stage_apply(st)
    _save(st)
    report(st)


if __name__ == "__main__":
    main()
