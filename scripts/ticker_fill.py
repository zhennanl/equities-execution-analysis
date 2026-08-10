"""Resolve the missing tickers — by asking, not by guessing
(c-239).

`ticker_audit.py` established that 1,534 of 4,403 rows carry no
ticker, that 621 predate our sources and 913 are live-era, and
that NOTHING INTERNAL can resolve them: every delisting test we
own needs a ticker to run first. So this reaches outside.

THE RULE THAT SHAPES THE WHOLE SCRIPT: a wrong ticker is worse
than a blank one. A blank is visibly missing; a wrong one
silently prices a different company, and every downstream
number — the T-multiple, the drift, the schedule cost — is then
about the wrong security while looking perfectly normal. So:

  * every proposal carries a CONFIDENCE and the evidence for it
  * anything below the bar is written to a review queue, not to
    the database
  * the changes DB is NEVER edited by this script. `apply`
    writes a separate overlay file that the loader merges, so
    the original stays inspectable and a bad batch is undone by
    deleting one file rather than by rebuilding from source

MATCHING. MSCI writes names in its own house style — "CHINA
MERCH BK A", "SAMSUNG ELEC PREF", "HYUNDAI MOTOR CO PREF" —
which is not what an exchange calls the company. Three passes,
strictest first:

  1. EXACT on a normalised name (case, punctuation, legal
     suffixes, and MSCI's abbreviations expanded).
  2. TOKEN-SUBSET: every significant token of the MSCI name
     appears in the candidate. Catches truncation, which is
     MSCI's most common deviation.
  3. FUZZY, scored, and only accepted well clear of the runner
     up — a near-tie between two candidates is exactly the case
     where a wrong answer is most likely, so it is refused.

Share-class markers (A/B/H/PREF/DVR) are checked SEPARATELY and
must agree. "SAMSUNG ELEC" and "SAMSUNG ELEC PREF" are
different securities with different prices, and a fuzzy matcher
left alone will happily map one to the other.

Usage:
  py scripts\\ticker_fill.py sources     what each market can use
  py scripts\\ticker_fill.py match       propose, write nothing
  py scripts\\ticker_fill.py apply       write the overlay
Output: data/ticker_overlay.json      accepted, merged by loaders
        data/ticker_review_queue.json  below the bar, for a human
        docs/TICKER_FILL.md
"""
import json
import re
import sys
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

DB = ROOT / "data" / "msci_changes_db.pkl"
OVERLAY = ROOT / "data" / "ticker_overlay.json"
QUEUE = ROOT / "data" / "ticker_review_queue.json"
DOC = ROOT / "docs" / "TICKER_FILL.md"

# Accept only well clear of the runner-up. A near-tie is the
# case where being wrong is most likely and least visible.
FUZZY_MIN = 0.90
FUZZY_MARGIN = 0.06

# MSCI's abbreviations, expanded so a house-style name can meet
# an exchange name in the middle. Extracted from the changes DB
# by frequency, not invented.
ABBREV = {
    "BK": "BANK", "BANKING": "BANK", "CORP": "", "CO": "",
    "LTD": "", "LIMITED": "", "INC": "", "PLC": "", "PT": "",
    "TBK": "", "BHD": "", "BERHAD": "", "AG": "", "SA": "",
    "NV": "", "GRP": "GROUP", "HLDG": "HOLDINGS",
    "HLDGS": "HOLDINGS", "HOLDING": "HOLDINGS",
    "INTL": "INTERNATIONAL", "INT'L": "INTERNATIONAL",
    "IND": "INDUSTRIES", "INDS": "INDUSTRIES",
    "MFG": "MANUFACTURING", "TECH": "TECHNOLOGY",
    "TECHNOLOGIES": "TECHNOLOGY", "PHARM": "PHARMACEUTICAL",
    "PHARMA": "PHARMACEUTICAL", "FIN": "FINANCIAL",
    "SEC": "SECURITIES", "INS": "INSURANCE",
    "ELEC": "ELECTRONICS", "CHEM": "CHEMICAL",
    "CONSTR": "CONSTRUCTION", "DEV": "DEVELOPMENT",
    "ENT": "ENTERPRISES", "MTLS": "MATERIALS",
    "RES": "RESOURCES", "SVCS": "SERVICES", "TELECOM":
    "TELECOMMUNICATIONS", "TRANSP": "TRANSPORT",
}

# Share-class and line markers. These must MATCH between the
# MSCI name and the candidate — they are the difference between
# two securities, not two spellings.
CLASS_TOKENS = {"A", "B", "H", "PREF", "PREFERRED", "DVR",
                "NVDR", "ADR", "GDR", "RIGHTS", "WARRANT"}


def _norm(name):
    """MSCI house style -> comparable tokens."""
    s = unicodedata.normalize("NFKD", str(name)).upper()
    s = re.sub(r"[^A-Z0-9' ]+", " ", s)
    out = []
    for tok in s.split():
        tok = tok.strip("'")
        if tok in CLASS_TOKENS:
            out.append(tok)
            continue
        tok = ABBREV.get(tok, tok)
        if tok:
            out.append(tok)
    return out


def _classes(tokens):
    return {t for t in tokens if t in CLASS_TOKENS}


def _score(a_tokens, b_tokens):
    """0..1 similarity, with the class markers held out."""
    a = [t for t in a_tokens if t not in CLASS_TOKENS]
    b = [t for t in b_tokens if t not in CLASS_TOKENS]
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, " ".join(a), " ".join(b)).ratio()


def match_one(name, candidates):
    """(ticker, confidence, why) or (None, 0, why-not).

    `candidates` is [(ticker, name)] for ONE market.
    """
    want = _norm(name)
    wcls = _classes(want)
    if not want:
        return None, 0.0, "name normalised to nothing"

    exact, subset, scored = [], [], []
    for tick, cname in candidates:
        got = _norm(cname)
        if _classes(got) != wcls:
            continue                       # different security
        if got == want:
            exact.append((tick, cname))
            continue
        w = {t for t in want if t not in CLASS_TOKENS}
        g = {t for t in got if t not in CLASS_TOKENS}
        if w and w <= g:
            subset.append((tick, cname))
        scored.append((_score(want, got), tick, cname))

    if len(exact) == 1:
        return exact[0][0], 1.0, f"exact name match: {exact[0][1]}"
    if len(exact) > 1:
        return None, 0.0, (f"AMBIGUOUS — {len(exact)} exact "
                           f"matches: "
                           f"{', '.join(t for t, _ in exact[:4])}")
    if len(subset) == 1:
        return subset[0][0], 0.92, (
            f"every MSCI token appears in: {subset[0][1]}")
    if len(subset) > 1:
        return None, 0.0, (f"AMBIGUOUS — {len(subset)} token "
                           f"matches")

    scored.sort(reverse=True)
    if not scored:
        return None, 0.0, "no candidate with the same share class"
    top = scored[0]
    runner = scored[1][0] if len(scored) > 1 else 0.0
    if top[0] >= FUZZY_MIN and (top[0] - runner) >= FUZZY_MARGIN:
        return top[1], round(top[0], 3), (
            f"fuzzy {top[0]:.3f} vs runner-up {runner:.3f}: "
            f"{top[2]}")
    return None, round(top[0], 3), (
        f"best {top[0]:.3f} ({top[2]}) but runner-up "
        f"{runner:.3f} — too close to call"
        if top[0] >= FUZZY_MIN else
        f"best {top[0]:.3f} ({top[2]}) below {FUZZY_MIN}")


# ---------------------------------------------------------------
def load_candidates():
    """{market: [(ticker, name)]} from every local roster we own.

    NOTE THE HONEST LIMIT: these are CURRENT-STATE rosters. They
    can resolve a live company and cannot resolve one that
    stopped trading before the roster was built, which is
    exactly the population `ticker_audit` could not classify.
    Whatever this leaves unresolved is a candidate for being
    genuinely delisted — but it is not proof, and the script
    does not claim it is.
    """
    out = defaultdict(list)
    seen = defaultdict(set)

    def add(mkt, tick, name):
        tick, name = str(tick or "").strip(), str(name or "").strip()
        if not tick or not name or (tick, name) in seen[mkt]:
            return
        seen[mkt].add((tick, name))
        out[mkt].append((tick, name))

    # 1. every name/ticker pair already in the changes DB
    import pandas as pd
    df = pd.read_pickle(DB)
    for _i, r in df.iterrows():
        if str(r.ticker or "").strip():
            add(r.market, r.ticker, r.security)
    # 2. the official constituent lists, where we have them
    p = ROOT / "data" / "msci_constituents.json"
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:                          # noqa: BLE001
            d = {}
        for mkt, blk in (d.get("markets") or {}).items():
            for c in (blk.get("constituents") or []):
                add(mkt, c.get("ticker") or c.get("code"),
                    c.get("security") or c.get("name"))
    # 3. harvested window files carry name + code together
    for sub in ("apac_event_windows",):
        for f in (ROOT / "data" / sub).glob("*.json"):
            try:
                W = json.loads(f.read_text(encoding="utf-8"))["windows"]
            except Exception:                      # noqa: BLE001
                continue
            for v in W.values():
                add(f.stem, v.get("yf_symbol") or v.get("code"),
                    v.get("name"))
    return out


def sources():
    cand = load_candidates()
    print(f"{'market':12} {'candidates':>11}")
    for m in sorted(cand):
        print(f"{m:12} {len(cand[m]):>11}")
    print("\n  Candidates are CURRENT-STATE rosters: they can "
          "resolve a live company and cannot resolve one that "
          "stopped trading before the roster was built.")


def match(write=False):
    import pandas as pd
    df = pd.read_pickle(DB)
    cand = load_candidates()
    accepted, queued = {}, []
    blanks = df[df.ticker.astype(str).str.strip() == ""]
    for _i, r in blanks.iterrows():
        tick, conf, why = match_one(r.security,
                                    cand.get(r.market, []))
        row = {"market": r.market, "review": r.review,
               "year": int(r.year), "security": r.security,
               "proposed": tick, "confidence": conf, "why": why}
        if tick and conf >= 0.90:
            accepted[f"{r.market}|{r.security}"] = {
                "ticker": tick, "confidence": conf, "why": why}
        else:
            queued.append(row)

    doc = ["# Filling the missing tickers", "",
           "*Generated by `scripts/ticker_fill.py`. A wrong "
           "ticker is worse than a blank one — it silently "
           "prices a different company — so anything not clearly "
           "resolved goes to a review queue rather than into the "
           "data.*", "",
           f"- **{len(blanks)}** rows with no ticker",
           f"- **{len(accepted)}** resolved at confidence "
           f"{FUZZY_MIN} or better",
           f"- **{len(queued)}** left for review", "",
           "## Accepted", "",
           "| market | security | ticker | conf | evidence |",
           "|---|---|---|---|---|"]
    for k, v in sorted(accepted.items())[:120]:
        mkt, nm = k.split("|", 1)
        doc.append(f"| {mkt} | {nm} | `{v['ticker']}` | "
                   f"{v['confidence']} | {v['why'][:70]} |")
    if len(accepted) > 120:
        doc.append(f"| … | {len(accepted) - 120} more | | | |")
    doc += ["", "## Why the rest were refused", "",
            "The reason matters more than the count: each of "
            "these is a case where a matcher left to its own "
            "devices would have produced something plausible "
            "and wrong.", ""]
    from collections import Counter
    kinds = Counter()
    for q in queued:
        w = q["why"]
        kinds["ambiguous — several equally good matches"
              if w.startswith("AMBIGUOUS") else
              "no candidate with the same share class"
              if "share class" in w else
              "too close to the runner-up"
              if "too close" in w else
              "nothing similar enough"] += 1
    for k, v in kinds.most_common():
        doc.append(f"- **{v}** — {k}")
    doc += ["", "**The share-class refusals are the ones worth "
            "reading.** 'SAMSUNG ELEC' and 'SAMSUNG ELEC PREF' "
            "are different securities with different prices; a "
            "fuzzy matcher with no class check maps one to the "
            "other and nothing downstream ever notices.", ""]
    DOC.write_text("\n".join(doc), encoding="utf-8")
    QUEUE.write_text(json.dumps(queued, indent=1),
                     encoding="utf-8")

    if write:
        # NEVER the changes DB. An overlay is inspectable, and a
        # bad batch is undone by deleting one file.
        OVERLAY.write_text(json.dumps(
            {"note": "Merged over msci_changes_db.pkl by the "
                     "loader. The database itself is untouched, "
                     "so this can be deleted to revert.",
             "min_confidence": FUZZY_MIN,
             "tickers": accepted}, indent=1), encoding="utf-8")
        print(f"-> {OVERLAY.relative_to(ROOT)} "
              f"({len(accepted)} tickers)")
    by = defaultdict(lambda: [0, 0])
    for k in accepted:
        by[k.split("|")[0]][0] += 1
    for q in queued:
        by[q["market"]][1] += 1
    print(f"{'market':12} {'filled':>7} {'queued':>7}")
    for m in sorted(by):
        print(f"{m:12} {by[m][0]:>7} {by[m][1]:>7}")
    print(f"{'TOTAL':12} {len(accepted):>7} {len(queued):>7}")
    print(f"\n-> {DOC.relative_to(ROOT)}")
    print(f"-> {QUEUE.relative_to(ROOT)}")
    if not write:
        print("\n  Nothing written to the data. "
              "`ticker_fill.py apply` writes the overlay.")
    return accepted, queued


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "match"
    if cmd == "sources":
        sources()
    elif cmd == "apply":
        match(write=True)
    else:
        match(write=False)
