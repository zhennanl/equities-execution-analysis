"""Securities sharing a ticker — the record, off the page.

c-218. This audit used to render as an expander on the Review
Database page. Bill asked for it to come off the site but be
kept on file, which is the right call: it is a DATA-QUALITY
record, and the page is for readers, not for auditors.

WHAT IT RECORDS. MSCI has spelled the same company several ways
over twenty years, so the roster collapses rows on the TICKER.
That is correct for a rename and wrong for two different
issuers, and the difference is not visible without checking
each case. Every ticker in the database carrying more than one
MSCI spelling is listed here with its disposition.

Two are NEVER merged, and the reasons are in
views/history_explorer.NEVER_MERGE — Siemens India vs Siemens
Energy India (separate companies after a 2025 demerger) and
Anhui Gujing A vs B (different share classes). Both also
indicate a wrong ticker upstream; see OPEN_ITEMS R9.

Usage:  py scripts\\ticker_collisions.py
Out:    docs/TICKER_COLLISIONS.md
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "TICKER_COLLISIONS.md"


def build():
    import datetime as dt
    import pandas as pd
    from views.history_explorer import NEVER_MERGE, _pretty

    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    g = df[df.ticker != ""].copy()
    g["root"] = (g.ticker.astype(str).str.split(".")
                 .str[0].str.upper())

    rows, kept_apart = [], 0
    for (mkt, root), sub in g.groupby(["market", "root"]):
        if sub.security.nunique() < 2:
            continue
        sep = (mkt, root) in NEVER_MERGE
        kept_apart += sep
        rows.append({
            "market": mkt, "root": root,
            "names": sorted(sub.security.unique()),
            "changes": len(sub),
            "handling": ("KEPT SEPARATE — " + NEVER_MERGE[
                (mkt, root)]) if sep else
            "merged; histories combined",
        })
    rows.sort(key=lambda r: (r["market"], r["root"]))

    out = [
        "# TICKER COLLISIONS — securities sharing a ticker",
        "",
        f"Generated {dt.date.today().isoformat()} by "
        "`py scripts\\ticker_collisions.py`.",
        "",
        "The Review Database collapses roster rows on the",
        "TICKER, because MSCI has spelled the same company",
        "several ways over twenty years. That is right for a",
        "rename and WRONG for two different issuers, so every",
        "collision is listed here with what was done to it.",
        "",
        f"**{len(rows)} colliding tickers. "
        f"{len(rows) - kept_apart} merged, {kept_apart} kept "
        f"separate.**",
        "",
        "| Market | Ticker | MSCI spellings | Changes | "
        "Handling |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        out.append(
            f"| {_pretty(r['market'])} | `{r['root']}` | "
            f"{' · '.join(r['names'])} | {r['changes']} | "
            f"{r['handling']} |")
    out += ["",
            "## Kept separate, and why", ""]
    for (mkt, root), why in NEVER_MERGE.items():
        out += [f"**{_pretty(mkt)} `{root}`** — {why}", ""]
    out += ["Both also point at a wrong ticker upstream — see",
            "OPEN_ITEMS R9. The display is honest; the data is",
            "still wrong."]
    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"{len(rows)} collisions, {kept_apart} kept separate")
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
