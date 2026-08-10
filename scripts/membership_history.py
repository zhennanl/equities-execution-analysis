"""The membership time machine (c-114) — index composition at
ANY review back to 2006, by reverse-rolling the changes DB.

Bill's two proposed routes, both implemented / assessed:

  ROUTE A (fund holdings): historical ETF holdings files.
    ASSESSED, NOT USED as the spine: iShares serves only the
    LATEST holdings file publicly; dated historical files are
    not exposed for free, and an ETF's holdings are its
    portfolio (sampling, cash, fair-value lines), not the
    index. It IS used as the CROSS-CHECK anchor.

  ROUTE B (reverse-roll): start from a DATED, AUTHORITATIVE
    membership and undo one review at a time. IMPLEMENTED.
    The anchor is MSCI's OWN public constituent list
    (msci_official_constituents.json — the ESMA-mandated
    tool, ~2 months delayed, so it reflects the MAY-2026
    review), NOT the ETF census. Rolling back from MSCI's own
    list removes the ETF's tracking noise from the spine.

THE ERROR MODEL (why this is an estimate, and how wrong):
  Reverse-rolling is exact IF every membership change appears
  in a review change list. Two classes do not:
    - OFF-CYCLE EXITS (M&A, delisting, sanction deletions —
      GIMI "Early Deletions"). We MEASURED these: 466
      candidates in data/offcycle_exit_classified.csv. Each
      one is a name that was ADDed at a review and is gone
      today with no DEL on record, so rolling back past its
      ADD leaves it wrongly ABSENT... no: wrongly PRESENT is
      impossible (we never added it back), the roster is
      wrongly SHORT for the window between its exit and its
      last ADD. Direction: the estimate UNDERCOUNTS.
    - OFF-CYCLE ADDITIONS (large IPO fast-entries) — same
      mechanism in reverse; the estimate OVERCOUNTS those.
  Per review we report the count of off-cycle candidates whose
  last ADD precedes it = the UNCERTAINTY BAND. We never hide
  it behind a single number.

Usage:
  py scripts\\membership_history.py build          (all markets)
  py scripts\\membership_history.py at Taiwan May18
Output: data/membership_history.json
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "membership_history.json"

_ABBR = {"HLDG": "HOLDING", "HLDGS": "HOLDINGS",
         "INTL": "INTERNATIONAL", "GRP": "GROUP",
         "MFG": "MANUFACTURING", "SVCS": "SERVICES",
         "FINL": "FINANCIAL", "INDS": "INDUSTRIES",
         "TRANSP": "TRANSPORT"}
_DROP = {"CO", "LTD", "CORP", "INC", "COMPANY", "CORPORATION",
         "ADR", "THE", "LIMITED", "PLC", "HK"}


def reviews(start=2006, end=2027):
    out = []
    for y in range(start, end):
        for m in ("Feb", "May", "Aug", "Nov"):
            out.append(f"{m}{y % 100:02d}")
    return out


_PAREN_NOISE = re.compile(
    r"\((?:[A-Z]{2,3}|HK-?C|CN|AU|NZ|SG|TH|PH|ID|MY|KR|IN|JP|"
    r"NEW|OLD)\)")


def _key(name, mkt):
    """Entity key: normalized name (share class kept in
    China). Ticker keys are used where BOTH sides resolve —
    see build().

    c-114: parentheticals are NOT uniformly noise. MSCI's
    official list uses country markers ('BHP GROUP (AU)',
    'TENCENT HOLDINGS LI (CN)') which must go, but also
    IDENTITY qualifiers — 'VEDANTA (DETACHED)' is the
    demerged line, a SEPARATE index security from 'VEDANTA'.
    Blanket-stripping collapsed those two into one key (found
    by the anchor-collision gate). So: strip only recognized
    country/vintage markers, keep everything else."""
    cls = {"A", "B", "H", "C"} if mkt != "China" else set()
    s = _PAREN_NOISE.sub(" ", str(name).upper())
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    toks = [_ABBR.get(t, t) for t in s.split()]
    while len(toks) > 1 and toks[-1] in (_DROP | cls):
        toks.pop()
    return " ".join(toks)


def anchor(mkt):
    """The dated starting membership: MSCI's own public list
    where offered, else the ETF census (NZ only)."""
    op = ROOT / "data" / "msci_official_constituents.json"
    if op.exists():
        o = json.loads(op.read_text(encoding="utf-8"))
        if mkt in o["markets"]:
            m = o["markets"][mkt]
            return ({_key(c["security"], mkt): c["security"]
                     for c in m["constituents"]},
                    f"MSCI official public list ({m['n']} names, "
                    "ESMA-mandated, ~2mo delayed = the May-2026 "
                    "review membership)")
    cen = json.loads((ROOT / "data" / "apac_members.json")
                     .read_text(encoding="utf-8"))["markets"].get(mkt, {})
    names = cen.get("names") or {}
    return ({_key(names.get(t) or t, mkt): (names.get(t) or t)
             for t in cen.get("standard_members", [])},
            "iShares ETF census (MSCI does not offer this "
            "market in its public constituents tool)")


def build_market(mkt, df, oc, official_n=None):
    """Roll the anchor backwards one review at a time."""
    anc, src = anchor(mkt)
    # GATE 1 (halt-on-abnormal): the anchor must not collapse
    # two index securities into one key — that silently
    # shrinks every roster downstream. Caught VEDANTA /
    # VEDANTA (DETACHED) in India.
    if official_n and len(anc) != official_n:
        raise SystemExit(
            f"HALT: {mkt} anchor has {len(anc)} keys for "
            f"{official_n} published constituents — entity-key "
            "collision, fix _key() before trusting rosters")
    g = df[df.market == mkt]
    revs = reviews()
    # the anchor post-dates the last review in the DB
    last = max((r for r in revs
                if r in set(g.review)), key=revs.index,
               default=revs[0])
    hist, cur = {}, dict(anc)
    hist[last] = {"n": len(cur), "when": "AFTER " + last}
    members = {last: sorted(cur.values())}
    # DIAGNOSTIC (c-114): an ADD we cannot find in the roster
    # is a KEY MISS — the name we are undoing was spelled
    # differently in the anchor/earlier rows, so the roster
    # keeps a duplicate and drifts UP as we go back. Counting
    # them is the honest measure of reconstruction quality.
    miss_add = 0
    n_add = 0
    for rev in reversed(revs[:revs.index(last) + 1]):
        rows = g[g.review == rev]
        for _, r in rows.iterrows():
            k = _key(r.security, mkt)
            if r.action == "ADD":
                n_add += 1
                if cur.pop(k, None) is None:
                    miss_add += 1         # unresolvable name
            else:
                cur[k] = r.security       # restore the deletion
        prev_i = revs.index(rev) - 1
        if prev_i < 0:
            break
        prev = revs[prev_i]
        # uncertainty: off-cycle candidates already ADDed by
        # this point are missing from our roll-back
        band = int(sum(1 for _, o in oc.iterrows()
                       if o.market == mkt
                       and o.last_add in revs
                       and revs.index(o.last_add) <= prev_i))
        hist[prev] = {"n": len(cur), "when": "AFTER " + prev,
                      "offcycle_uncertainty": band}
        members[prev] = sorted(cur.values())
    return {"anchor_source": src, "anchor_n": len(anc),
            "add_key_misses": miss_add, "adds_processed": n_add,
            "counts": hist, "members": members}


def factsheet_counts():
    """GATE 2 — the THIRD independent MSCI publication.
    July-2026 country factsheets print 'Number of
    Constituents'. Anchor counts must equal them exactly:
    constituents tool + factsheet + our census are three
    separate MSCI artifacts, so agreement is real validation,
    not a tautology."""
    import subprocess
    d = ROOT / "data" / "factsheets"
    slug = {"australia": "Australia", "china": "China",
            "hongkong": "HongKong", "india": "India",
            "indonesia": "Indonesia", "japan": "Japan",
            "korea": "Korea", "malaysia": "Malaysia",
            "newzealand": "NewZealand",
            "philippines": "Philippines",
            "singapore": "Singapore", "taiwan": "Taiwan",
            "thailand": "Thailand"}
    out = {}
    for p in sorted(d.glob("msci_*_2026-07.pdf")):
        mkt = slug.get(p.stem.split("_")[1])
        if not mkt:
            continue
        txt = subprocess.run(["pdftotext", "-layout", str(p), "-"],
                             capture_output=True, text=True).stdout
        m = re.search(r"Number of\s*\n?\s*(?:Constituents\s*)?"
                      r"(\d+)", txt)
        if m:
            out[mkt] = int(m.group(1))
    return out


def build():
    import pandas as pd
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    fs = factsheet_counts()
    ocp = ROOT / "data" / "offcycle_exit_classified.csv"
    oc = (pd.read_csv(ocp).fillna("") if ocp.exists()
          else pd.DataFrame(columns=["market", "last_add"]))
    out = {"method": "reverse-roll from a dated authoritative "
                     "anchor; see module docstring for the "
                     "error model",
           "factsheet_gate": fs,
           "markets": {}}
    for mkt in sorted(df.market.unique()):
        m = build_market(mkt, df, oc, official_n=fs.get(mkt))
        out["markets"][mkt] = m
        c = m["counts"]
        first = min(c, key=lambda r: reviews().index(r))
        lastr = max(c, key=lambda r: reviews().index(r))
        band = max(v.get("offcycle_uncertainty", 0)
                   for v in c.values())
        mr = (m["add_key_misses"] / max(m["adds_processed"], 1))
        print(f"{mkt:12s} {lastr} {c[lastr]['n']:4d} -> "
              f"{first} {c[first]['n']:4d} names | off-cycle "
              f"band <={band} | ADD key misses "
              f"{m['add_key_misses']}/{m['adds_processed']} "
              f"({mr:.0%})")
    OUT.write_text(json.dumps(out), encoding="utf-8")
    print(f"\n-> {OUT.name}")
    return out


def at(mkt, rev):
    o = json.loads(OUT.read_text(encoding="utf-8"))["markets"][mkt]
    mem = o["members"].get(rev)
    if mem is None:
        raise SystemExit(f"no reconstruction for {mkt} {rev}")
    c = o["counts"][rev]
    print(f"{mkt} membership AFTER {rev}: {len(mem)} names "
          f"(off-cycle uncertainty +/-"
          f"{c.get('offcycle_uncertainty', 0)})")
    print(f"anchor: {o['anchor_source']}")
    for n in mem:
        print(" ", n)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "at":
        at(sys.argv[2], sys.argv[3])
    else:
        build()
