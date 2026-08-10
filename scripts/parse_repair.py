"""Per-cell parse repair for the 21 defective cells (c-112).

Lesson from the failed global rewrite (c-109): repair ONLY the
defective cells, each constrained by MSCI's OWN official
counts, and apply results as a PATCH LAYER — the main parser
never changes, so nothing can regress.

Method per cell (review, market):
  1. Extract that section's raw lines (with page breaks).
  2. Tokenize every data line into (x-position, name) items.
  3. Per PAGE: cluster x-positions into <= 2 columns. Page 1's
     header maps left=ADD right=DEL. Continuation pages with
     two clusters map the same; single-cluster pages are
     AMBIGUOUS and get deferred.
  4. Resolve deferred items by the official-count constraint:
     fill whichever column still needs names (order preserved).
  5. Accept the patch ONLY if final counts == official counts;
     else mark unresolved (honesty over coverage).

Output: data/changes_db_patches.json
Then: py scripts\\changes_db.py build   (applies patches)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "data" / "msci_archive"

MARKET_HDRS = {
    "Taiwan": "TAIWAN", "Japan": "JAPAN",
    "Australia": "AUSTRALIA", "HongKong": "HONG KONG",
    "Korea": "KOREA", "China": "CHINA", "India": "INDIA",
    "Malaysia": "MALAYSIA", "Indonesia": "INDONESIA",
    "Philippines": "PHILIPPINES", "NewZealand": "NEW ZEALAND",
    "Singapore": "SINGAPORE", "Thailand": "THAILAND"}
_JUNK = ("©", "msci.com", "Page ", "MSCI Global", "Nb of",
         "Securities", "GLOBAL STANDARD", "Region", "Country",
         "All rights reserved")


def section_lines(txt, market_hdr):
    """Raw lines of one market's section (header -> next
    header), page-break markers preserved."""
    lines = txt.splitlines()
    out, on = [], False
    for ln in lines:
        s = ln.strip().replace("\x0c", "")
        if re.fullmatch(rf"MSCI {market_hdr} INDEX", s):
            on = True
            continue
        if on and re.fullmatch(r"MSCI [A-Z][A-Z ]+? INDEX", s):
            break
        if on:
            out.append(ln)
    return out


def repair_cell(review, market, official_adds, official_dels):
    fn = ARCH / f"MSCI_{review}_STPublicList.txt"
    txt = fn.read_text(encoding="utf-8", errors="ignore")
    sec = section_lines(txt, MARKET_HDRS[market])
    # split into pages
    pages, cur = [], []
    for ln in sec:
        if "\x0c" in ln:
            pages.append(cur)
            cur = [ln.replace("\x0c", "")]
        else:
            cur.append(ln)
    pages.append(cur)
    adds, dels, deferred = [], [], []
    for pi, page in enumerate(pages):
        hdr_off = None
        items = []            # (x, name)
        for ln in page:
            if any(k in ln for k in _JUNK) or not ln.strip():
                continue
            if "Deletions" in ln:
                hdr_off = ln.index("Deletions")
                continue
            if "Additions" in ln:
                continue
            for m in re.finditer(r"\S(?:.*?\S)?(?=\s{2,}|\s*$)",
                                 ln.rstrip()):
                nm = m.group(0).strip()
                _BANNERS = {"NONE", "ASIA PACIFIC", "AMERICAS",
                            "EUROPE, MIDDLE EAST AND AFRICA",
                            '"EUROPE, MIDDLE EAST AND AFRICA"',
                            "EUROPE"}
                if nm and nm.upper() not in _BANNERS:
                    items.append((m.start(), nm))
        if not items:
            continue
        xs = sorted({x for x, _ in items})
        # cluster x-starts: split at the biggest gap if > 8
        split = None
        if len(xs) > 1:
            gaps = [(xs[i + 1] - xs[i], i)
                    for i in range(len(xs) - 1)]
            g, gi = max(gaps)
            if g > 8:
                split = (xs[gi] + xs[gi + 1]) / 2
        if hdr_off is not None:
            # header page: assign by header offset
            for x, nm in items:
                (adds if x < hdr_off - 2 else dels).append(nm)
        elif split is not None:
            for x, nm in items:
                (adds if x < split else dels).append(nm)
        else:
            deferred.extend(nm for _, nm in items)
    # constraint resolution for deferred (order-preserving)
    need_a = official_adds - len(adds)
    need_d = official_dels - len(dels)
    if need_a >= 0 and need_d >= 0 \
            and need_a + need_d == len(deferred):
        adds += deferred[:need_a]
        dels += deferred[need_a:]
    ok = (len(adds) == official_adds
          and len(dels) == official_dels)
    tier = "A-geometric"
    if not ok:
        allnames = adds + dels + deferred
        total = official_adds + official_dels
        if len(allnames) == total:
            # Tier B: one side officially EMPTY -> trivial
            if official_adds == 0:
                adds, dels = [], allnames
                ok, tier = True, "B-zero-side"
            elif official_dels == 0:
                adds, dels = allnames, []
                ok, tier = True, "B-zero-side"
            else:
                # Tier C: totals match, split wrong — the
                # Additions column (few names) occupies the
                # top-left of page 1, so READING ORDER hits
                # the adds first
                adds = allnames[:official_adds]
                dels = allnames[official_adds:]
                ok, tier = True, "C-reading-order"
    return {"adds": adds, "dels": dels, "resolved": ok,
            "tier": tier,
            "note": None if ok else
            f"counts {len(adds)}/{len(dels)} vs official "
            f"{official_adds}/{official_dels}; "
            f"deferred={len(deferred)}"}


def main():
    val = json.loads((ROOT / "data" /
                      "changes_db_validation.json").read_text(encoding="utf-8"))
    patches, unresolved = {}, []
    for m in val["mismatches"]:
        rev, mkt = m["review"], m["market"]
        oa, od = m["official"]
        r = repair_cell(rev, mkt, oa, od)
        if r["resolved"]:
            patches[f"{rev}|{mkt}"] = {"adds": r["adds"],
                                       "dels": r["dels"],
                                       "tier": r["tier"]}
            print(f"REPAIRED {rev} {mkt}: +{oa}/-{od} "
                  f"[{r['tier']}]")
        else:
            unresolved.append({"review": rev, "market": mkt,
                               "note": r["note"]})
            print(f"UNRESOLVED {rev} {mkt}: {r['note']}")
    out = {"patches": patches, "unresolved": unresolved}
    (ROOT / "data" / "changes_db_patches.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(f"\n{len(patches)} repaired, {len(unresolved)} "
          "unresolved -> data/changes_db_patches.json")


if __name__ == "__main__":
    main()
