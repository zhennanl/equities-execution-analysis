"""Canonical company names per ticker, from Yahoo (c-156).

WHY: the security roster is keyed on MSCI's own security
strings, and MSCI has spelled the same company several ways
over twenty years ("ACCTON TECHNOLOGY CORP" in a 2007 change
list, "Accton Technology" in the current constituent file).
That produced duplicate rows for one ticker. The ticker is
the stable identity; the name is not. So we resolve
ticker -> ONE canonical name and collapse on it.

SOURCE: Yahoo's search endpoint (query1/v1/finance/search),
which returns longname/shortname without a crumb and is not
throttled the way get_info is. One call per ticker, cached.

Run:  py scripts\\yahoo_names.py            (all markets)
      py scripts\\yahoo_names.py Taiwan     (one market)
Out:  data/yahoo_names.json  {"2345.TW": "Accton Technology
      Corporation", ...}  — re-run to fill gaps; existing
      entries are never re-fetched.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "yahoo_names.json"
UA = {"User-Agent": "Mozilla/5.0"}
SUFFIX = {"Australia": ".AX", "HongKong": ".HK",
          "India": ".NS", "Indonesia": ".JK", "Japan": ".T",
          "Korea": ".KS", "Malaysia": ".KL",
          "NewZealand": ".NZ", "Philippines": ".PS",
          "Singapore": ".SI", "Taiwan": ".TW",
          "Thailand": ".BK", "China": ".SS"}


def _cache():
    """Read tolerantly. This cache has repeatedly come back with
    a stray non-UTF8 byte (Yahoo returns CJK names and a partial
    write can split a multi-byte char). A hard crash here blocks
    every downstream harvest, so decode with replacement and drop
    the damaged rows instead."""
    if not OUT.exists():
        return {}
    raw = OUT.read_bytes().decode("utf-8", errors="replace")
    try:
        d = json.loads(raw)
    except Exception:                              # noqa: BLE001
        return {}
    return {k: v for k, v in d.items()
            if v and "\ufffd" not in str(v)}


# MSCI shorthand that Yahoo's search does not index at all.
# Each verified individually against the SGX code, c-167.
_HAND = {"CICT.SI": "C38U.SI",   # CapitaLand Int Commercial Tr
         "CLAR.SI": "A17U.SI",   # CapitaLand Ascendas REIT
         "GRAB.SI": "GRAB",      # NASDAQ, not SGX
         "SE.SI": "SE"}          # NYSE, not SGX


def variants(sym):
    """Yahoo symbol spellings to try, best first.

    c-164. A 438-name "unresolved" pile turned out to be almost
    entirely OUR formatting, not missing companies. Each rule
    below was verified against Yahoo before being written here:
      HK    1.HK -> 0001.HK          (zero-pad to 4)
      China 000333.SS -> 000333.SZ   (0/1/2/3 = Shenzhen,
                                      6/9 = Shanghai)
      Thai  ADVANC.R -> ADVANC.BK    (".R" is the NVDR line,
                                      not a Yahoo suffix)
      India 532483.NS -> 532483.BO   (6-digit = BSE code)
      Korea 028300.KS -> 028300.KQ   (KOSDAQ, not KOSPI)
    """
    base, _, sfx = sym.rpartition(".")
    if not base:
        return [sym]
    if sym in _HAND:
        return [_HAND[sym], sym]
    out = [sym]
    if sfx == "HK" and base.isdigit():
        out.insert(0, f"{int(base):04d}.HK")
    elif sfx in ("SS", "SZ") and base.isdigit():
        # c-167: 165 of China's "unresolved" were never A-shares.
        # MSCI China holds H-shares, and 1810 / 2318 / 9988 are
        # Xiaomi, Ping An and Alibaba in HONG KONG. Mainland A
        # codes are ALWAYS 6 digits, so anything shorter is a HK
        # listing and needs .HK zero-padded to 4.
        if len(base) < 6:
            out.insert(0, f"{int(base):04d}.HK")
        else:
            want = "SZ" if base[0] in "0123" else "SS"
            out.insert(0, f"{base}.{want}")
    elif sfx == "R":                       # SET NVDR line
        out = [f"{base}.BK"] + out
    elif sfx == "NS" and base.isdigit() and len(base) == 6:
        out.insert(0, f"{base}.BO")
    elif sfx == "HK" and not base.isdigit():
        # Jardine companies carry HK-style codes but list in
        # SINGAPORE (H78 = Hongkong Land, J36 = Jardine
        # Matheson); FUTU is a US listing.
        out += [f"{base}.SI", base]
    elif sfx in ("SS", "SZ") and not base.isdigit():
        # c-170: MSCI China includes US-listed ADRs — PDD, TME,
        # VIPS, HTHT, TAL, BZ, LEGN, YMM. They carry no Chinese
        # suffix at all, so the bare symbol is the right ask.
        out.append(base)
    elif sfx == "TW":
        # c-170: Taiwan has TWO boards. Codes default to .TW
        # (TWSE) but TPEx names live on .TWO — 8299 (Phison) is
        # the case that surfaced it: a real, live, large company
        # that looked "unresolvable" purely because we never
        # asked the other exchange.
        out.append(f"{base}.TWO")
    elif sfx in ("KS", "KQ"):
        out.append(f"{base}.{'KQ' if sfx == 'KS' else 'KS'}")
    return list(dict.fromkeys(out))


def lookup(sym, cache):
    if sym in cache:
        return cache[sym]
    import requests
    v = None
    for cand in variants(sym):
        try:
            # QUOTE the symbol. Unquoted, "M&M.NS" truncated the
            # query string at the ampersand and silently returned
            # nothing — Mahindra resolves fine once encoded.
            j = requests.get(
                "https://query1.finance.yahoo.com/v1/finance/"
                f"search?q={requests.utils.quote(cand)}"
                "&quotesCount=5",
                headers=UA, timeout=20).json()
            hit = next((q for q in j.get("quotes", [])
                        if q.get("symbol") == cand), None)
            v = (hit.get("longname") or hit.get("shortname")) \
                if hit else None
        except Exception:                          # noqa: BLE001
            v = None
        if v:
            if cand != sym:      # remember the spelling that won
                cache[cand] = v
            break
        time.sleep(0.2)
    _b, _, _sfx = sym.rpartition(".")
    if not v and _b and not _b.isdigit() and _sfx in _SEARCHABLE:
        # c-167: "MAYBANK.KL" is not a Yahoo symbol, but
        # searching "MAYBANK" returns 1155.KL. The exchange
        # filter is what keeps this safe — without it the same
        # query happily returns a US company.
        v = _by_shortname(_b, _sfx, cache)
    if v:                       # never cache a failure
        cache[sym] = v
    return v


_SEARCHABLE = {"KL": "KLS", "SI": "SES", "JK": "JKT",
               "BK": "SET", "AX": "ASX"}


def _by_shortname(base, sfx, cache):
    """Resolve a local short name via exchange-filtered search."""
    import requests
    want = _SEARCHABLE[sfx]
    try:
        j = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/search"
            f"?q={requests.utils.quote(base)}&quotesCount=10",
            headers=UA, timeout=20).json()
        for x in j.get("quotes", []):
            if x.get("quoteType") != "EQUITY" or \
                    x.get("exchange") != want:
                continue
            sym2 = x.get("symbol", "")
            nm = x.get("longname") or x.get("shortname")
            if sym2 and nm:
                cache[sym2] = nm      # remember the real symbol
                return nm
    except Exception:                              # noqa: BLE001
        pass
    return None


# Codes verified ABSENT from their exchange's live listed
# register (c-175). Yahoo will never return a name for these,
# so re-asking every run is wasted requests and makes the
# resolution rate look permanently broken. Evidence, not
# assumption: the TWSE + TPEx open-data registers list 1,983
# live codes and none of these is among them.
DEAD = {
    "1602.TW": "absent from the live TWSE/TPEx register",
    "2418.TW": "absent from the live TWSE/TPEx register",
    "2448.TW": "absent from the live register — Epistar, "
               "folded into Ennostar",
    "3682.TW": "absent from the live register — APT Telecom, "
               "merged into Far EasTone",
    "5264.TW": "absent from the live TWSE/TPEx register",
}


def market(name, cache):
    """Every ticker the roster knows for this market."""
    import pandas as pd
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    sub = df[df.market == name]
    ticks = {str(t).strip() for t in sub.ticker.dropna()
             if str(t).strip() and str(t).strip() != "nan"}
    # c-156b: also cover CURRENT members. A company that has
    # never changed (TSMC) never appears in the changes DB, so
    # the first pass missed exactly the largest names — which
    # are the ones the UI shows as the search example.
    try:
        mem = json.loads((ROOT / "data" / "apac_members.json")
                         .read_text(encoding="utf-8"))["markets"].get(name, {})
        ticks |= {str(t).strip() for t in
                  mem.get("standard_members", []) if t}
    except Exception:                              # noqa: BLE001
        pass
    sfx = SUFFIX.get(name, "")
    todo = [t if "." in t else t + sfx for t in sorted(ticks)]
    got = 0
    dead = 0
    for i, sym in enumerate(todo, 1):
        if sym in cache:
            continue
        if sym in DEAD:
            dead += 1
            continue
        if lookup(sym, cache):
            got += 1
        if i % 20 == 0:
            OUT.write_text(json.dumps(cache, indent=1,
                                      ensure_ascii=True),
                       encoding="utf-8")
            print(f"  {name}: {i}/{len(todo)}", flush=True)
        time.sleep(0.3)
    OUT.write_text(json.dumps(cache, indent=1,
                              ensure_ascii=True),
                   encoding="utf-8")
    # c-175: count a name as resolved if ANY of its spellings
    # is cached. The old counter checked the exact symbol only,
    # so every TPEx name resolved as .TWO and every China ADR
    # resolved as a bare symbol was reported missing. Taiwan
    # read "172/191" when the true figure was 186/191.
    have = sum(1 for t in todo
               if any(v in cache for v in variants(t)))
    print(f"{name}: {have}/{len(todo)} names resolved "
          f"(+{got} this run"
          + (f", {dead} known-delisted skipped" if dead else "")
          + ")")


if __name__ == "__main__":
    c = _cache()
    mkts = sys.argv[1:] or list(SUFFIX)
    for m in mkts:
        market(m, c)


# --------------------------------------------------------
# c-159: REVERSE lookup — MSCI security name -> ticker.
# 33 Taiwan names carry no ticker in the changes DB (the
# original backfill matched on ticker, so anything it could
# not map stayed blank). Yahoo's search endpoint accepts a
# company NAME, so we ask it directly and keep the first hit
# on the right exchange. Names that resolve to nothing after
# this are almost all companies that no longer trade —
# merged, acquired or delisted — and the page labels them
# "Delisted" rather than leaving an empty cell.
# Out: data/yahoo_tickers.json  {"WINTEK": "", ...}
TOUT = ROOT / "data" / "yahoo_tickers.json"
EXCH = {"Taiwan": {"TAI", "TWO"}, "Korea": {"KSC", "KOE"},
        "Japan": {"JPX"}, "HongKong": {"HKG"},
        "India": {"NSI", "BSE"}, "Australia": {"ASX"},
        "Singapore": {"SES"}, "Malaysia": {"KLS"},
        "Thailand": {"SET"}, "Indonesia": {"JKT"},
        "NewZealand": {"NZE"}, "China": {"SHH", "SHZ"}}


_ABBR = {"INT'L": "INTERNATIONAL", "INTL": "INTERNATIONAL",
         "TECH": "TECHNOLOGY", "SEMICON": "SEMICONDUCTOR",
         "CHEM": "CHEMICAL", "IND": "INDUSTRIAL",
         "MFG": "MANUFACTURING", "FINL": "FINANCIAL",
         "HLDG": "HOLDING", "HLDGS": "HOLDINGS",
         "COMM": "COMMUNICATIONS", "PRO": "",
         "COMMUNICATIONS": "COMMUNICATIONS"}
_DROP = {"CO", "CORP", "INC", "LTD", "COMPANY", "LIMITED",
         "CORPORATION", "THE"}


def _toks(x):
    return {t for t in
            [_ABBR.get(w, w) for w in
             str(x).upper().replace("'", "'").replace(",", " ")
             .replace(".", " ").split()]
            if t and t not in _DROP}


def _queries(name):
    """MSCI abbreviates ("VANGUARD INT'L SEMICON"); Yahoo
    search wants something closer. Expanded form first, then
    a 2-word prefix. NEVER a single word — that is what
    matched "CHUNGHWA PICTURE TUBES" to Chunghwa TELECOM."""
    w = [_ABBR.get(x, x) for x in
         name.replace("'", "'").upper().split()]
    w = [x for x in w if x and x not in _DROP]
    outs = [" ".join(w)]
    if len(w) > 2:
        outs.append(" ".join(w[:2]))
    return list(dict.fromkeys(outs))


def find_ticker(name, mkt, cache):
    key = f"{mkt}|{name}"
    if key in cache:
        return cache[key]
    import requests
    v = ""
    ok = EXCH.get(mkt, set())
    for q in _queries(name):
        try:
            j = requests.get(
                "https://query1.finance.yahoo.com/v1/finance/"
                f"search?q={requests.utils.quote(q)}"
                "&quotesCount=8", headers=UA, timeout=20).json()
            # VERIFY the hit is the same company: at least two
            # significant tokens must overlap (or every token
            # of a short name). A wrong ticker is worse than a
            # blank one — it would merge two companies in the
            # roster dedupe.
            want = _toks(name)
            for x in j.get("quotes", []):
                if x.get("exchange") not in ok or \
                        x.get("quoteType") != "EQUITY":
                    continue
                got = _toks(x.get("shortname") or "") | \
                    _toks(x.get("longname") or "")
                shared = want & got
                if len(shared) >= 2 or (len(want) <= 2
                                        and want <= got):
                    v = x.get("symbol", "").split(".")[0]
                    break
            if v:
                break
        except Exception:                              # noqa: BLE001
            pass
        time.sleep(0.25)
    cache[key] = v          # "" IS a result: nothing trades
    TOUT.write_text(json.dumps(cache, indent=1,
                               ensure_ascii=True),
                    encoding="utf-8")
    return v


def backfill(mkt):
    """Resolve every ticker-less security for one market."""
    import pandas as pd
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    sub = df[df.market == mkt]
    blank = sorted({s for s, t in zip(sub.security, sub.ticker)
                    if not str(t).strip()
                    or str(t).strip() in ("nan", "None")})
    cache = json.loads(TOUT.read_text(encoding="utf-8")) if TOUT.exists() \
        else {}
    hit = 0
    for i, nm in enumerate(blank, 1):
        v = find_ticker(nm, mkt, cache)
        hit += bool(v)
        print(f"  [{i}/{len(blank)}] {nm[:30]:30} -> "
              f"{v or 'no listing (delisted?)'}", flush=True)
        time.sleep(0.3)
    print(f"{mkt}: {hit}/{len(blank)} resolved; "
          f"{len(blank) - hit} look delisted")
