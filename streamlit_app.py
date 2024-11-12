
import streamlit as st

# --- PAGE SETUP ---
graphics = st.Page(
    "views/leads.py",
    title="Leads",
    icon=":material/overview:",
)

asyncdata = st.Page(
    "views/asyncdata.py",
    title="Data Async",
    icon=":material/overview:",
)
# --- NAVIGATION SETUP [WITH SECTIONS]---
pg = st.navigation(
    {
        "Marketing": [asyncdata, graphics],
        # "Async": [asyncdata]
        # "Teste2": [test_page2],
    }
)


# --- SHARED ON ALL PAGES ---
# st.logo("assets/codingisfun_logo.png")

# --- RUN NAVIGATION ---
pg.run()
