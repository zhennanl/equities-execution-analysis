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
    # c-369, Bill: "Collector" -> "Fetcher", "the day's" ->
    # "today's", and the Analyst subtitle says the run is
    # automatic and names what it analyses.
    ("1 · COLLECT", "The Fetcher", NAVY,
     "Fetches today's exchange files",
     # c-376, Bill: lead with the act, then the files.
     "Retrieves data published by TWSE — daily net buying "
     "by foreign investors per stock, securities borrowing "
     "and lending balances."),
    ("2 · RECALCULATE", "The Analyst", NAVY,
     # c-371, Bill: shortened — STEPS is the single source, so
     # the card and the diagram both pick this up.
     "Runs the analysis automatically",
     # c-377, Bill: data, and a read of market colour.
     "Applies the same analytical framework to the new "
     "data and gives its own read of the market colour."),
    ("3 · DRAFT", "The Author", GREEN,
     # c-377, Bill: report, not note.
     "Writes the analysis report",
     "Turns the analysis into a comment, in the format a desk "
     "would send to clients, with every data reference "
     "pointing back at the source."),
    ("4 · CHECK", "The Reviewer", AMBER,
     "Reviews the draft and refines it for production",
     # c-379, Bill: the body ends at the act — the flag itself.
     "A second agent re-reads the draft. Any mismatched number "
     "or flawed reasoning is flagged for a rerun."),
]

EVENING = [
    # c-371, Bill: the row label names the STEP, not the city,
    # and the body shortens to the act.
    ("18:00", "collect", "The exchange files publish. The "
     "fetcher pulls today's files."),
    ("18:10", "recalculate", "The pre-designed analytical "
     "framework reruns on the new data."),
    # c-371, Bill (paraphrased): the example is an addition
    # candidate moving unusually, not a count of names.
    ("18:25", "draft", "The analysis detects unusual price and "
     "volume movement in one of the candidates for addition. "
     "The author notes the observation and cites the source "
     "behind each figure."),
    # c-373, Bill's intent stated plainly: if the AI slips in a
    # calculation or its reasoning, a HUMAN looks before
    # anything leaves.
    ("18:30", "check", "The reviewer checks every number "
     "against the source file. Any calculation error or flawed "
     "reasoning is flagged for human review before anything "
     "is sent."),
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
        # c-375, Bill asked whether the fetcher's and analyst's
        # subtitles can sit on ONE line. They can: the box is
        # 208px with 14px padding, and 11px Inter runs ~5.4px a
        # character, so up to ~32 characters fit — both lines
        # ("Fetches today's exchange files", 30; "Runs the
        # analysis automatically", 31) clear it. The wrap
        # threshold moves 26 -> 32.
        words, line, lines = does.split(" "), "", []
        for w_ in words:
            if len(line) + len(w_) > 32:
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
    # c-375, Bill: the arm names BOTH gates — an untraceable
    # number and flawed reasoning.
    p.append(f'<text x="{(xs[0] + xs[3]) / 2 + box_w / 2}" '
             f'y="{ymid + 16}" text-anchor="middle" '
             f'font-family="Inter,sans-serif" font-size="11" '
             f'fill="{RED}">a number does not match, or the '
             f'reasoning is flawed → rerun</text>')
    # c-351 cut the exit caption; c-375, Bill: the green exit
    # arrow itself goes too — the loop simply ends at the
    # Reviewer, and the timeline below says what leaves.
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
    # c-377, Bill: *"Change the format to make it more aesthetic
    # and more readable."* A TIMELINE, not a table: a vertical
    # spine with a node per row, the time in the site's serif,
    # the step as a small chip, and the body given room. The
    # last row — the deliverable — gets the navy node.
    rows = []
    for i, (t, where, what) in enumerate(EVENING):
        last = i == len(EVENING) - 1
        node = NAVY if last else "#ffffff"
        rows.append(
            f"<div style='display:flex;gap:0'>"
            # the spine column: node + connecting line
            f"<div style='width:1.9rem;display:flex;"
            f"flex-direction:column;align-items:center'>"
            f"<div style='width:11px;height:11px;"
            f"border-radius:50%;border:2px solid {NAVY};"
            f"background:{node};margin-top:.34rem;"
            f"flex:0 0 auto'></div>"
            + (f"<div style='width:1px;flex:1 1 auto;"
               f"background:{RULE_L}'></div>" if not last else "")
            + "</div>"
            # the content column
            f"<div style='flex:1;padding:0 0 1.05rem .5rem'>"
            f"<div style='display:flex;gap:.6rem;"
            f"align-items:baseline'>"
            f"<span style='font-family:{design.SERIF};"
            f"font-size:1.05rem;color:{NAVY}'>{t}</span>"
            f"<span style='font-size:.62rem;letter-spacing:"
            f".11em;text-transform:uppercase;color:{FAINT};"
            f"border:1px solid {RULE_L};border-radius:2px;"
            f"padding:.06rem .34rem'>{where}</span></div>"
            f"<div style='font-size:.85rem;color:#4a4038;"
            f"line-height:1.55;margin-top:.18rem;"
            f"max-width:44rem'>{what}</div>"
            f"</div></div>")
    st.markdown(
        f"<div style='font-size:.68rem;letter-spacing:.12em;"
        f"text-transform:uppercase;color:{FAINT};font-weight:600;"
        f"margin:.2rem 0 .55rem'>Example workflow</div>"
        + "".join(rows), unsafe_allow_html=True)


def render():
    design.css()
    st.markdown("# Agentic AI Workflow")
    design.sect(1, "Agentic AI Workflow That Runs Itself")
    st.markdown(_loop_svg(), unsafe_allow_html=True)
    _cards()
    _evening()
