
import streamlit as st

# --- PAGE SETUP ---
graphics = st.Page(
    "views/leads.py",
    title="Leads",
    icon=":material/overview:",
)

asyncdata = st.Page(
    "views/asyncdata.py",
    title="Marketing Leads",
    icon=":material/overview:",
)
# --- NAVIGATION SETUP [WITH SECTIONS]---
pg = st.navigation(
    {
        "Menu": [asyncdata, graphics],
        # "Async": [asyncdata]
        # "Teste2": [test_page2],
    }
)


# --- SHARED ON ALL PAGES ---
# st.logo("assets/codingisfun_logo.png")

# --- RUN NAVIGATION ---
pg.run()
