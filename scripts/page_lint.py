"""Does the page still match its spec? (c-209)

BACKLOG item 2. The point of autonomous work is that I can
check my own output, and the only checks worth anything are the
ones a machine runs. This lints views/ against
docs/PAGE_SPEC_review_db.md so drift is caught by a command
rather than by Bill noticing.

It deliberately checks the things that DRIFT, not the things
that break — a broken page fails pytest already. What drifts is
section order, prose creeping back in, and hardcoded lists
quietly replacing the central ones.

Usage:  py scripts\\page_lint.py
Exit 0 clean, 1 with findings.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / "views" / "history_explorer.py"

# Section order from PAGE_SPEC section 3. The strip is item 1
# and is not a _sect() call, so the numbered rules start at 2.
# c-216: renumbered 1-6, contiguous. The dormant Membership
# time machine used to hold 4, so a reader saw section 3
# followed by section 5 — a gap the lint tolerated as a KNOWN
# GAP and the reader read as a mistake. It now sits at 9, out
# of the visible sequence, until it is either restored or
# deleted (PARKED P6).
# c-236: titles are Title Case now (DESIGN_DECISIONS D4) and
# section 5 was renamed. The match below is case-insensitive,
# so the capitalisation change alone would not have tripped it
# — the RENAME did, which is the lint working: a section that
# quietly changes what it claims to be is exactly the drift
# this file exists to catch.
EXPECTED = [
    (1, "Latest Review"),
    (2, "Index Review History"),
    (3, "Who Is in the Index Right Now"),
    (4, "Security Lookup"),
    (5, "Individual Index Review History"),
]

# Sections the spec wants that do NOT currently render, with
# why. Listed so the lint stays useful instead of failing
# forever on something Bill has not decided yet.
KNOWN_GAPS = {
    9: "_time_machine() is defined but never called; the call "
       "site is a bare comment. Parked at 9 so it is outside "
       "the reader's 1-6 sequence — see PARKED P6.",
}

MAX_LEAD = 200
MARKET_NAMES = ["Japan", "Korea", "HongKong", "Taiwan",
                "Australia", "Singapore", "Thailand",
                "Malaysia", "Indonesia", "NewZealand"]


def _sects(src):
    """(number, title, lead) for every _sect call in the view."""
    out = []
    # c-214: the title may be an f-string. Section 1's title
    # interpolates the review label, and the old pattern
    # required a bare quote right after the comma — so it saw
    # no section 1 and reported it missing. Right call, wrong
    # reason: the section was there, the reader could not.
    for m in re.finditer(
            r"_sect\(\s*(\d+)\s*,\s*f?(['\"])(.*?)\2\s*"
            r"(?:,\s*(.*?))?\)\s*\n", src, re.S):
        lead = (m.group(4) or "").strip()
        lead = " ".join(re.findall(r"['\"](.*?)['\"]", lead, re.S))
        out.append((int(m.group(1)), m.group(3), lead))
    return out


def _render_order():
    """Section numbers in the order they REACH THE SCREEN."""
    try:
        import warnings
        warnings.filterwarnings("ignore")
        from streamlit.testing.v1 import AppTest
    except Exception:                              # noqa: BLE001
        return None
    at = AppTest.from_string(
        "import sys\nsys.path.insert(0, '.')\n"
        "from views import history_explorer\n"
        "history_explorer.render()\n", default_timeout=240)
    at.run()
    if at.exception:
        print(f"  page raised: {at.exception[0].value[:120]}")
        return None
    out = []
    for m in at.markdown:
        # c-213: the eyebrow reads "Section 2" now, not "2".
        # The lint failing here was correct behaviour — the
        # markup it inspects changed and it said so rather than
        # silently matching nothing and reporting clean.
        for n in re.findall(r"class='n'>(?:Section\s*)?(\d+)"
                            r"</span>", str(m.value)):
            out.append(int(n))
    return out


def lint():
    src = VIEW.read_text(encoding="utf-8")
    bad = []
    secs = _sects(src)

    # ---- section order matches the spec -------------------
    #
    # Checked against the RENDERED page, not the source. The
    # first version of this lint read _sect() calls in file
    # order and reported [3, 4, 2, 5, 6] as "out of order" —
    # but sections 3 and 4 are defined inside helper functions
    # that render() calls later, so source order says nothing
    # about what a reader sees. A lint that is wrong about the
    # thing it exists to check is worse than no lint.
    got = [(n, t) for n, t, _ in secs]
    for want_n, want_t in EXPECTED:
        hit = [x for x in got if x[0] == want_n]
        if not hit:
            bad.append(f"SPEC 3: section {want_n} "
                       f"({want_t!r}) is missing")
        elif want_t.lower() not in hit[0][1].lower():
            bad.append(f"SPEC 3: section {want_n} should be "
                       f"{want_t!r}, found {hit[0][1]!r}")
    # c-214: DUPLICATE NUMBERS. Two sections both numbered 1
    # shipped past every other check — order was still sorted,
    # both existed, both rendered. A reader would simply see
    # "Section 1" twice and lose confidence in the numbering.
    _n = [n for n, _, _ in secs]
    _dupes = sorted({x for x in _n if _n.count(x) > 1})
    if _dupes:
        bad.append(f"SPEC 3: section number(s) {_dupes} used "
                   f"more than once — numbering must be unique")

    rendered = _render_order()
    if rendered is None:
        print("  (render check skipped — streamlit unavailable)")
    else:
        if rendered != sorted(rendered):
            bad.append(f"SPEC 3: sections appear on screen out "
                       f"of order {rendered}")
        # c-211: DOES IT ACTUALLY RENDER?
        #
        # The lint checked order and never checked PRESENCE, so
        # a section could exist in the source, satisfy every
        # rule, and never reach the screen. Section 4 has been
        # exactly that: _time_machine() is defined, contains
        # _sect(4, ...), and is never called — the call site is
        # a bare comment. Dead since before this lint existed,
        # and the lint reported CLEAN over it twice.
        #
        # Same family as the first bug in this file: I checked
        # the artefact I could read easily instead of the thing
        # I actually cared about.
        for want_n, want_t in EXPECTED:
            if want_n in rendered:
                continue
            if want_n in KNOWN_GAPS:
                print(f"  KNOWN GAP: section {want_n} "
                      f"({want_t}) — {KNOWN_GAPS[want_n]}")
                continue
            bad.append(f"SPEC 3: section {want_n} ({want_t!r}) "
                       f"never reaches the screen")

    # ---- voice: minimal ------------------------------------
    for n, t, lead in secs:
        if len(lead) > MAX_LEAD:
            bad.append(f"SPEC 4: lead on section {n} ({t!r}) is "
                       f"{len(lead)} chars, max {MAX_LEAD} — "
                       f"this page keeps text minimal")

    # ---- markets come from markets.py ----------------------
    # c-220: this page now shows ALL markets including the
    # Philippines, so it reads df.market directly rather than
    # calling filter_markets. The rule below still matters — it
    # bans a hand-typed LITERAL list, which is what would
    # actually rot.
    body = re.sub(r"#.*", "", src)          # ignore comments
    body = re.sub(r'"""(.*?)"""', "", body, flags=re.S)
    lists = re.findall(r"\[([^\[\]]{20,400}?)\]", body, re.S)
    for lst in lists:
        names = [m for m in MARKET_NAMES if f'"{m}"' in lst]
        if len(names) >= 4:
            bad.append(
                "SPEC 6: a market list is hardcoded in the view "
                f"({', '.join(names[:4])}…) — markets must come "
                "from scripts/markets.py so an exclusion is "
                "recorded in one place")
            break

    # ---- no Streamlit default headers ----------------------
    if "st.header(" in body:
        bad.append("SPEC 4: st.header() bypasses design.sect, "
                   "so the section rule and numbering are lost")

    # ---- the strip that leads the page ---------------------
    if "_apac_strip" not in src:
        bad.append("SPEC 3.1: the all-markets latest-review "
                   "strip must lead the page")

    print(f"page_lint: {VIEW.relative_to(ROOT)}")
    print(f"  sections found: "
          f"{', '.join(f'{n}.{t}' for n, t, _ in secs)}")
    if not bad:
        print("  CLEAN — matches PAGE_SPEC_review_db.md")
        return 0
    print(f"\n  {len(bad)} finding(s):")
    for b in bad:
        print(f"    - {b}")
    return 1


if __name__ == "__main__":
    sys.exit(lint())
