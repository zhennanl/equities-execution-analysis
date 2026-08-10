"""Resolve MSCI security names to tickers — and prove the
rest are delisted (c-160).

THE PROBLEM: 33 Taiwan securities carry no ticker in the
changes DB. Searching Yahoo by name failed badly — MSCI
abbreviates ("VANGUARD INT'L SEMICON"), and a short-prefix
search matched "CHUNGHWA PICTURE TUBES" to Chunghwa TELECOM,
a different company. A wrong ticker is worse than a blank
one, because the roster merges rows on ticker.

THE FIX — match against a COMPLETE index, offline:
  1. Harvest the English name of EVERY currently listed
     TWSE + TPEx code (yahoo_names.py, ~1,800 codes).
  2. Token-match each MSCI name against that index. Require
     >= 2 shared distinctive tokens AND a unique winner —
     ties are refused, not guessed.
  3. What is left is the payoff of completeness: a company
     that once sat in the MSCI index but matches NOTHING in
     the full listed universe is no longer listed. That is
     evidence, not assumption, so those are labelled
     "Delisted".

Run:  py scripts\\tw_ticker_resolve.py
Out:  data/yahoo_tickers.json   (Taiwan|NAME -> code or "")
      data/delisted_register.json  (auto entries merged with
      the curated ones, which keep their cited event)
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ROOT / "data" / "yahoo_names.json"
TOUT = ROOT / "data" / "yahoo_tickers.json"
DREG = ROOT / "data" / "delisted_register.json"

# words that carry no identifying power
_STOP = {"CO", "CORP", "CORPORATION", "INC", "LTD", "LIMITED",
         "COMPANY", "THE", "HOLDING", "HOLDINGS", "GROUP",
         "AND", "OF", "TAIWAN", "TECHNOLOGY", "TECHNOLOGIES",
         "INDUSTRIAL", "INDUSTRIES", "INTERNATIONAL",
         "ELECTRONICS", "ELECTRIC", "FINANCIAL", "BANK"}
_ABBR = {"INTL": "INTERNATIONAL", "INT'L": "INTERNATIONAL",
         "TECH": "TECHNOLOGY", "SEMICON": "SEMICONDUCTOR",
         "CHEM": "CHEMICAL", "IND": "INDUSTRIAL",
         "MFG": "MANUFACTURING", "FINL": "FINANCIAL",
         "COMM": "COMMUNICATIONS", "HLDG": "HOLDING",
         "HLDGS": "HOLDINGS", "PRO": "", "SCI": "SCIENCE"}


def toks(x, keep_stop=False):
    w = [_ABBR.get(t, t) for t in
         re.split(r"[^A-Z0-9']+", str(x).upper())]
    w = [t.replace("'", "") for t in w if t]
    return {t for t in w if len(t) > 1
            and (keep_stop or t not in _STOP)}


def resolve(market="Taiwan"):
    import pandas as pd
    names = json.loads(NAMES.read_text(encoding="utf-8"))
    idx = {k.split(".")[0]: v for k, v in names.items()
           if k.endswith((".TW", ".TWO"))}
    print(f"listed-name index: {len(idx)} codes")
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    sub = df[df.market == market]
    blank = sorted({s for s, t in zip(sub.security, sub.ticker)
                    if not str(t).strip()
                    or str(t).strip() in ("nan", "None")})
    tmap = json.loads(TOUT.read_text(encoding="utf-8")) \
        if TOUT.exists() else {}
    reg = json.loads(DREG.read_text(encoding="utf-8")) \
        if DREG.exists() else {}
    reg.setdefault(market, {})
    # document frequency: a token shared by many companies
    # ("LIFE", "CHEMICAL") proves nothing; a rare one
    # ("INNOLUX", "POWERCHIP") proves almost everything.
    from collections import Counter
    dfq = Counter()
    for cand in idx.values():
        dfq.update(toks(cand))
    hit = gone = 0
    for nm in blank:
        want, wide = toks(nm), toks(nm, keep_stop=True)
        head = next(iter([t for t in
                          re.split(r"[^A-Z0-9']+", nm.upper())
                          if t and t not in _STOP]), None)
        head = _ABBR.get(head, head)
        best, score, ties = None, 0, 0
        for code, cand in idx.items():
            got = toks(cand)
            # THE HEAD TOKEN MUST MATCH. Without this,
            # "CHINA LIFE INSURANCE" matched Mercuries LIFE
            # INSURANCE and "LEE CHANG YUNG CHEM" matched
            # YUNG Zip CHEMICAL — different companies sharing
            # generic words.
            if head and head not in got:
                continue
            sc = len(want & got)
            if sc > score:
                best, score, ties = code, sc, 1
            elif sc == score and sc > 0:
                if len(wide & toks(idx[best], True)) < \
                        len(wide & toks(cand, True)):
                    best = code
                else:
                    ties += 1
        # accept on two shared tokens, OR on one token so rare
        # it names the company by itself (INNOLUX, POWERCHIP)
        rare = head and dfq.get(head, 99) <= 2
        if best and (score >= 2 or rare) and ties <= 1:
            tmap[f"{market}|{nm}"] = best
            hit += 1
            print(f"  {nm[:30]:30} -> {best}  "
                  f"({idx[best][:34]})")
        else:
            tmap[f"{market}|{nm}"] = ""
            gone += 1
            reg[market].setdefault(
                nm.upper(),
                "no longer listed — absent from the full "
                "TWSE/TPEx listed universe")
            print(f"  {nm[:30]:30} -> DELISTED "
                  f"(no match in {len(idx)} listed codes)")
    TOUT.write_text(json.dumps(tmap, indent=1,
                               ensure_ascii=True),
                    encoding="utf-8")
    DREG.write_text(json.dumps(reg, indent=1,
                               ensure_ascii=True),
                    encoding="utf-8")
    print(f"\n{market}: {hit} resolved, {gone} delisted "
          f"(of {len(blank)})")


if __name__ == "__main__":
    resolve()
