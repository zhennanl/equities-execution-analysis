"""Execution Analytics — Aug-2026 MSCI Review site (c-85).

The platform was refocused on 2026-08-06 to a single-purpose
site for the Aug-2026 MSCI Taiwan index review. The full
previous website (8 modules) is preserved at
backup/website_v1_20260806/ — to restore it, set LEGACY = True
(the old page modules still live in views/ untouched).

Run: streamlit run app.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

LEGACY = False

if LEGACY:
    import runpy
    runpy.run_path(os.path.join(os.path.dirname(__file__),
                                "backup", "website_v1_20260806",
                                "app.py"), run_name="__main__")
else:
    st.set_page_config(
        page_title="MSCI Aug-2026 Review — Taiwan",
        page_icon="🎯", layout="wide",
        initial_sidebar_state="collapsed")
    from views import aug26_review
    aug26_review.render()
