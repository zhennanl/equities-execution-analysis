"""Start Here — what this project is, and how to read it.

c-346, Bill: the site opens on a database page and expects the
reader to work out the argument. A program-trading dealer has
five minutes. This page front-loads the whole thing: what was
built, what it is for, what the data will not support, and why
Taiwan.

WRITTEN FOR SOMEONE WHO WILL NOT SCROLL. Every page before the
Taiwan case study gets two or three sentences and no more. The
case study gets the room, because that is where the analysis is.
"""
from pathlib import Path

import streamlit as st

from views import design

ROOT = Path(__file__).resolve().parents[1]

NAVY, GREEN, RED = design.NAVY, design.GREEN, design.RED
FAINT, MUTED, RULE = design.FAINT, design.MUTED, design.RULE
RULE_L = design.RULE_L
INK = design.INK


def _route(rows):
    """The four pages as a ruled route, not a data table.

    c-348, Bill: the page map should be the FIRST thing on the
    site and should look like a route rather than a spreadsheet.
    A Streamlit table renders a header row, a border and a
    scrollbar — furniture that says "data" about four sentences
    of navigation. This is four ruled lines with a serif numeral,
    which is the same grammar the rest of the site uses for a
    sequence.
    """
    out = []
    for n, (title, blurb, lead) in enumerate(rows, 1):
        # c-350, Bill: all four rows carry the navy edge. The
        # muted rule on rows 1-3 read as "these are lesser", and
        # they are not — they are the same site. What marks the
        # case study is the tag, which is a label rather than a
        # ranking.
        num = NAVY
        edge = f"border-left:3px solid {NAVY};padding-left:.8rem;"
        tag = ("<span style='font-size:.6rem;letter-spacing:.1em;"
               f"text-transform:uppercase;color:{NAVY};"
               "border:1px solid " + RULE + ";border-radius:2px;"
               "padding:.08rem .32rem;margin-left:.5rem;"
               "vertical-align:.08rem'>the analysis</span>"
               if lead else "")
        out.append(
            f"<div style='display:flex;gap:.85rem;align-items:"
            f"baseline;padding:.6rem 0;border-top:1px solid "
            f"{RULE_L};{edge}'>"
            f"<div style='font-family:{design.SERIF};font-size:"
            f"1.3rem;color:{num};min-width:1.9rem;line-height:1'>"
            f"{n}</div><div style='min-width:0'>"
            f"<div style='font-size:.95rem;font-weight:600;"
            f"color:{INK}'>{title}{tag}</div>"
            f"<div style='font-size:.85rem;color:{MUTED};"
            f"margin-top:.15rem;line-height:1.5'>{blurb}</div>"
            f"</div></div>")
    st.markdown("".join(out) + f"<div style='border-top:1px solid "
                f"{RULE_L};margin-bottom:1.1rem'></div>",
                unsafe_allow_html=True)


def _cards(items, accent, tint):
    """A row of short cards — eyebrow, claim, consequence.

    c-348, Bill: *"instead of text, we can use more engaging
    format"*. Three paragraphs of prose about what the data
    cannot do is the least likely block on the page to be read,
    and it is the one that must be. Broken into cards, each limit
    is four lines and the reader can take one and leave the rest.

    AMBER is not decoration — it is this site's colour for
    degraded data (see design.py), the same one design.caveat
    uses, so a reader who has been through the other pages
    already knows what the tint means.
    """
    out = []
    for eyebrow, head, body in items:
        out.append(
            f"<div style='flex:1 1 230px;border-left:3px solid "
            f"{accent};background:{tint};padding:.65rem .85rem'>"
            f"<div style='font-size:.62rem;letter-spacing:.11em;"
            f"text-transform:uppercase;color:{accent};"
            f"font-weight:600'>{eyebrow}</div>"
            f"<div style='font-size:.9rem;font-weight:600;"
            f"color:{INK};margin:.3rem 0 .32rem;line-height:1.35'>"
            f"{head}</div>"
            f"<div style='font-size:.81rem;color:#4a4038;"
            f"line-height:1.55'>{body}</div></div>")
    st.markdown("<div style='display:flex;flex-wrap:wrap;gap:.7rem;"
                "margin:.15rem 0 .9rem'>" + "".join(out) + "</div>",
                unsafe_allow_html=True)


def render():
    design.css()
    st.markdown("# MSCI Index Review")

    # ── 1 · the route ─────────────────────────────────────────
    design.sect(1, "What Is on This Site")
    _route([
        ("MSCI Index Review Database",
         "Every MSCI Taiwan index change since 2006, rebuilt from "
         "press releases and factsheets.", False),
        ("Predict MSCI Index Changes",
         "The rulebook walked step by step \u2014 universe, "
         "liquidity, size cutoff, buffers \u2014 leading to a "
         "prediction for the August 2026 review.", False),
        ("Index Rebalance Daily Data",
         "The same event across twelve APAC markets: how big the "
         "print is, and how volume behaves around it.", False),
        ("Taiwan Case Study",
         "Where the volume prints, what the closing auction "
         "charges, whether anyone has positioned early, and how "
         "big the August order is.", True),
    ])

    # ── 2 · the limits ────────────────────────────────────────
    design.sect(2, "Analysis Limitations")
    _cards([
        ("No MSCI data licence",
         "Free float is an estimate",
         "MSCI sells the constituent and free-float files. "
         "Without the real free-float data, the size cutoff for a "
         "review can be calculated in the wrong place, which "
         "produces the wrong index change prediction."),
        ("No institutional data",
         "No access to positioning data",
         "No prime-broker borrow book, no live short interest, no "
         "vendor holdings feed. Positioning ahead of an index "
         "trade has to be pieced together from exchange "
         "disclosure and public data only."),
    ], design.AMBER, "#fdf8ee")

    # ── 3 · why Taiwan ────────────────────────────────────────
    design.sect(3, "Why Conduct a Case Study on the Taiwan Market")
    _cards([
        ("Reason one",
         "A prior project on this market",
         "I built an index-rebalancing analysis for Taiwan during "
         "a previous internship. This project continues that "
         "work."),
        ("Reason two",
         "Taiwan offers a wide range of alternative datasets",
         "TWSE publishes a comprehensive set of data: daily net "
         "buying by foreign, trust and dealer accounts per stock, "
         "alongside securities borrowing and lending balances."),
    ], NAVY, "#f7f9fb")
