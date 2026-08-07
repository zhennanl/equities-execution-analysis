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
    _page = st.sidebar.radio("Page", [
        "📜 Review History Explorer",
        "🧭 Cutoff Framework"])
    if _page.endswith("Explorer"):
        from views import history_explorer
        history_explorer.render()
    else:
        from views import framework_cutoff
        framework_cutoff.render()
else:
    st.set_page_config(page_title="Execution Analytics",
                       layout="wide",
                       initial_sidebar_state="collapsed")
    # blank — build from here
