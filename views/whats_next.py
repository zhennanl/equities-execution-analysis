"""Agentic AI Workflow — how this site could run itself.

c-350, Bill: the page is cut to ONE section. The four agent
write-ups, the Jefferies comparison and the readiness table are
gone; what remains is the loop, explained well enough that a
program-trading dealer with no engineering background can read it
once and follow it.

THE AUDIENCE DECIDES THE VOCABULARY. A PT dealer does not care
what a scheduler is. They care that the files land at 18:00
Taipei, that somebody notices when a number moves, and that
nothing goes to a client unchecked. So every box on this page is
described by WHAT IT DOES TO THE WORK, not by what it is built
from — "downloads yesterday's exchange files" rather than "runs
the harvest layer".

ONE DIAGRAM IS NOT A PAGE. With the prose sections removed, a
single flowchart on white would read as a stub. So the section
carries three registers of the same four steps, in descending
abstraction:

  1. the loop itself, as a diagram — the shape;
  2. four cards — the detail a diagram box cannot hold;
  3. one evening on the clock — the same steps in the reader's
     own working hours, which is what makes an abstract loop
     concrete for a dealer who knows exactly which files land at
     18:00 Taipei.
"""
import streamlit as st

from views import design

NAVY, GREEN, RED = design.NAVY, design.GREEN, design.RED
AMBER, INK = design.AMBER, design.INK
FAINT, MUTED, RULE = design.FAINT, design.MUTED, design.RULE
RULE_L, PAPER, CARD = design.RULE_L, design.PAPER, design.CARD

# The four steps, in one place, so the diagram and the cards
# below it cannot describe them differently.
STEPS = [
    ("1 · COLLECT", "The Collector", NAVY,
     "Fetches the day's exchange files",
     "Taiwan publishes late in the evening — who bought, who "
     "sold, how much printed in the close."),
    ("2 · RECALCULATE", "The Analyst", NAVY,
     "Runs analysis, evaluates what moved",
     "It applies the same analytical framework to the new "
     "numbers and gives its own assessment of what changed."),
    ("3 · DRAFT", "The Author", GREEN,
     "Writes the morning note",
     "It turns analysis into a comment a desk would send to "
     "clients, in the desk's own voice, with every sentence "
     "pointing back at the file where its number came from."),
    ("4 · CHECK", "The Reviewer", AMBER,
     "Blocks anything it cannot prove",
     "Before the note leaves, a second agent re-reads it against "
     "the source files. Any figure it cannot trace goes back for "
     "a rerun and the note does not go out."),
]

EVENING = [
    ("18:00", "Taipei", "The exchange files publish. The "
     "collector pulls the day's trading, the investor-type flow "
     "and the weekly custody file."),
    ("18:10", "recalculate", "The pre-designed analytical "
     "framework reruns on the new data."),
    ("18:25", "draft", "Four names moved enough to mention. The "
     "author writes them up and cites the file behind each "
     "figure."),
    ("18:30", "check", "The reviewer ties every number back to a "
     "file. When numbers do not match, that section is rerun "
     "before anything is sent."),
    ("07:00", "next morning", "The note is ready to send to "
     "the client's inbox before the open."),
]


def _loop_svg():
    """The four agents as one cycle.

    Drawn as SVG rather than plotly because this is a diagram,
    not a chart — there is no data behind it and a reader should
    not be able to hover it expecting numbers."""
    W, H = 952, 268
    box_w, box_h, y = 208, 118, 18
    xs = [8, 246, 484, 722]
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" '
         f'xmlns="http://www.w3.org/2000/svg" '
         f'style="max-width:952px;display:block;margin:.2rem auto">']
    for i, (eyebrow, title, col, does, _why) in enumerate(STEPS):
        x = xs[i]
        p.append(
            f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" '
            f'rx="4" fill="{CARD}" stroke="{col}" stroke-width="1.5"/>')
        p.append(
            f'<rect x="{x}" y="{y}" width="{box_w}" height="3" '
            f'fill="{col}"/>')
        p.append(
            f'<text x="{x + 14}" y="{y + 26}" font-family="Inter,'
            f'sans-serif" font-size="9.5" letter-spacing="1.1" '
            f'fill="{FAINT}">{eyebrow}</text>')
        p.append(
            f'<text x="{x + 14}" y="{y + 48}" font-family="Inter,'
            f'sans-serif" font-size="15" font-weight="600" '
            f'fill="{INK}">{title}</text>')
        # the plain-English line, wrapped by hand because SVG has
        # no text wrapping and a PT reader should not meet a
        # clipped sentence
        words, line, lines = does.split(" "), "", []
        for w_ in words:
            if len(line) + len(w_) > 26:
                lines.append(line)
                line = w_
            else:
                line = (line + " " + w_).strip()
        lines.append(line)
        for j, ln in enumerate(lines[:3]):
            p.append(
                f'<text x="{x + 14}" y="{y + 70 + j * 14}" '
                f'font-family="Inter,sans-serif" font-size="11" '
                f'fill="{MUTED}">{ln}</text>')
        if i < 3:
            x1, x2 = x + box_w, xs[i + 1]
            p.append(f'<line x1="{x1 + 6}" y1="{y + box_h / 2}" '
                     f'x2="{x2 - 12}" y2="{y + box_h / 2}" '
                     f'stroke="{RULE}" stroke-width="1.5"/>')
            p.append(f'<path d="M{x2 - 12},{y + box_h / 2} '
                     f'l-7,-4 l0,8 z" fill="{RULE}"/>')
    # the failure arm — back to the start
    ymid = y + box_h + 52
    p.append(f'<path d="M{xs[3] + box_w / 2},{y + box_h} '
             f'L{xs[3] + box_w / 2},{ymid} L{xs[0] + box_w / 2},'
             f'{ymid} L{xs[0] + box_w / 2},{y + box_h + 10}" '
             f'fill="none" stroke="{RED}" stroke-width="1.4" '
             f'stroke-dasharray="4 3"/>')
    p.append(f'<path d="M{xs[0] + box_w / 2},{y + box_h + 8} '
             f'l-4,8 l8,0 z" fill="{RED}"/>')
    p.append(f'<text x="{(xs[0] + xs[3]) / 2 + box_w / 2}" '
             f'y="{ymid + 16}" text-anchor="middle" '
             f'font-family="Inter,sans-serif" font-size="11" '
             f'fill="{RED}">a number does not match '
             f'→ rerun</text>')
    # c-351, Bill: the "it ties / the note goes out" caption
    # comes off. The arrow alone carries it, and three lines of
    # text in the right margin were the busiest thing on an
    # otherwise clean diagram.
    p.append(f'<path d="M{xs[3] + box_w + 6},{y + box_h / 2} '
             f'l16,0" stroke="{GREEN}" stroke-width="1.5"/>')
    p.append(f'<path d="M{xs[3] + box_w + 24},{y + box_h / 2} '
             f'l-7,-4 l0,8 z" fill="{GREEN}"/>')
    p.append("</svg>")
    return "".join(p)


def _cards():
    """The same four steps in prose, at the length a diagram box
    cannot hold. Two registers for one idea: the picture for the
    shape, the cards for the detail."""
    out = []
    for eyebrow, title, col, does, why in STEPS:
        out.append(
            f"<div style='flex:1 1 210px;border-top:3px solid "
            f"{col};background:{CARD};padding:.7rem .85rem'>"
            f"<div style='font-size:.62rem;letter-spacing:.11em;"
            f"color:{FAINT};font-weight:600'>{eyebrow}</div>"
            f"<div style='font-size:.92rem;font-weight:600;"
            f"color:{INK};margin:.28rem 0 .1rem'>{title}</div>"
            f"<div style='font-size:.78rem;color:{col};"
            f"margin-bottom:.35rem'>{does}</div>"
            f"<div style='font-size:.81rem;color:#4a4038;"
            f"line-height:1.55'>{why}</div></div>")
    st.markdown("<div style='display:flex;flex-wrap:wrap;gap:.7rem;"
                "margin:1.1rem 0 1.3rem'>" + "".join(out) + "</div>",
                unsafe_allow_html=True)


def _evening():
    """One night, on the clock. The third register, and the one
    that makes the loop concrete — a dealer reads 18:00 Taipei
    and knows exactly which files that is."""
    rows = []
    for t, where, what in EVENING:
        rows.append(
            f"<div style='display:flex;gap:1rem;align-items:"
            f"baseline;padding:.5rem 0;border-top:1px solid "
            f"{RULE_L}'>"
            f"<div style='min-width:4.6rem;font-family:"
            f"{design.MONO};font-size:.92rem;color:{NAVY};"
            f"font-weight:600'>{t}</div>"
            f"<div style='min-width:6.5rem;font-size:.72rem;"
            f"letter-spacing:.09em;text-transform:uppercase;"
            f"color:{FAINT};padding-top:.15rem'>{where}</div>"
            f"<div style='font-size:.86rem;color:#4a4038;"
            f"line-height:1.55'>{what}</div></div>")
    st.markdown(
        f"<div style='font-size:.68rem;letter-spacing:.12em;"
        f"text-transform:uppercase;color:{FAINT};font-weight:600;"
        f"margin:.2rem 0 .1rem'>One evening, end to end</div>"
        + "".join(rows)
        + f"<div style='border-top:1px solid {RULE_L};"
          f"margin-bottom:1.2rem'></div>", unsafe_allow_html=True)


def render():
    design.css()
    st.markdown("# Agentic AI Workflow")
    design.sect(1, "A Workflow That Could Run Itself")
    st.markdown(_loop_svg(), unsafe_allow_html=True)
    _cards()
    _evening()
