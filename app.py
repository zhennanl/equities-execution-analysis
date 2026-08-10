"""Execution Analytics — website entry point.

c-87: blank canvas at the user's request — the site restarts
from scratch. Nothing was deleted; switch MODE to bring back
either previous version:

  MODE = "blank"   -> empty page (current)
  MODE = "aug26"   -> the Aug-2026 review page
                      (views/aug26_review.py, c-85)
  MODE = "legacy"  -> the full v1 platform via LEGACY backup
                      (backup/website_v1_20260806/)

Run: streamlit run app.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

MODE = "framework"   # c-88: page 1 of the new site

if MODE == "legacy":
    # LEGACY v1 site (8 modules)
    import runpy
    runpy.run_path(os.path.join(os.path.dirname(__file__),
                                "backup", "website_v1_20260806",
                                "app.py"), run_name="__main__")
elif MODE == "aug26":
    st.set_page_config(
        page_title="MSCI Aug-2026 Review — Taiwan",
        page_icon="🎯", layout="wide",
        initial_sidebar_state="collapsed")
    from views import aug26_review
    aug26_review.render()
elif MODE == "framework":
    st.set_page_config(page_title="Index Review Analytics",
                       page_icon="🧭", layout="wide",
                       initial_sidebar_state="expanded")
    # c-128: Cutoff Framework + Reconstruction (PIT) HIDDEN
    # per Bill (code intact — restore by re-adding to this list)
    # c-207: one design system, injected once. Every page
    # inherits the density, the tabular numerals and the
    # palette without importing anything.
    from views import design
    design.css()
    # c-275: the panel exists TWICE and that is deliberate.
    # Bill asked for a duplicate before the redesign so the
    # version he reviewed is never one edit away from gone —
    # which is exactly what happened to the pre-c-274 files,
    # untracked and overwritten in place with no copy.
    #
    #   "APAC Rebalance Panel"      -> views/apac_panel.py
    #        the interactive one, third in the list. Reads
    #        per-event rows and computes its own statistics.
    #   "APAC Rebalance Panel (v1)" -> views/apac_strategist.py
    #        frozen. Reads pre-aggregated cells and computes
    #        nothing, with the test that enforces it.
    # c-346, Bill: the site opens and closes on a page written
    # for a reader with five minutes. Everything between them was
    # already here.
    _page = st.sidebar.radio("Page", [
        "🚩 Start Here",
        "📜 MSCI Index Review Database",
        "🎯 Predict MSCI Index Changes",
        "🌏 Index Rebalance Daily Data",
        "🇹🇼 Taiwan Case Study",
        "🤖 Agentic AI Workflow"])
    # c-248: the nav label lost "— Taiwan" to match the page's
    # own title, so the route can no longer key off it.
    if _page.endswith("Start Here"):
        from views import opening
        opening.render()
    elif _page.endswith("AI Workflow"):
        from views import whats_next
        whats_next.render()
    elif _page.endswith("Changes"):
        from views import walkthrough
        walkthrough.render()
    elif _page.endswith("Database"):
        from views import history_explorer
        history_explorer.render()
    elif _page.endswith("(PIT)"):
        from views import reconstruction
        reconstruction.render()
    # c-303, Bill: "Announcement → Effective" and "APAC
    # Rebalance Panel (v1)" are off the site. views/
    # event_window_study.py and views/apac_strategist.py stay on
    # disk with their tests — the v1 panel in particular is the
    # frozen copy kept so the pre-redesign version is never one
    # edit from gone, which is the whole reason it exists.
    elif _page.endswith("Case Study"):
        # c-290: the borrow join. Reads data/tw_case_study.json.
        from views import tw_case_study
        tw_case_study.render()
    # c-321, Bill: the 5-Minute Data Analysis page is off the
    # nav — every one of its sections now runs inside the Taiwan
    # Case Study, numbered continuously with it. views/
    # intraday_panel.py stays on disk and still OWNS those section
    # bodies; the case study calls intraday_panel.sections(offset)
    # rather than holding a copy.
    elif _page.endswith("Daily Data"):
        from views import apac_panel
        apac_panel.render()
    # c-293, Bill: "Taiwan Rebalance Insights" and "Findings" are
    # off the site. views/rebalance_insights.py and views/findings.py
    # stay on disk — removing a route is one line to undo, deleting a
    # working module is not, and that asymmetry has already cost this
    # project two files.
    # c-255: "Ask the analyst" is off the site at Bill's
    # request. views/ask.py is left on disk rather than deleted
    # — it is a working page, and removing a route is
    # reversible in a line where deleting the module is not.
    else:
        from views import framework_cutoff
        framework_cutoff.render()
else:
    st.set_page_config(page_title="Execution Analytics",
                       layout="wide",
                       initial_sidebar_state="collapsed")
    # blank — build from here
