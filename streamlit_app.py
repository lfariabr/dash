
import streamlit as st

# --- PAGE SETUP ---
leads = st.Page(
    "views/leads.py",
    title="Leads",
    icon=":material/overview:",
)

# test_page2 = st.Page(
#     "views/teste2.py",
#     title="teste",
#     icon=":material/overview:",
# )

# --- NAVIGATION SETUP [WITH SECTIONS]---
pg = st.navigation(
    {
        "Leads": [leads],
        # "Teste2": [test_page2],
    }
)


# --- SHARED ON ALL PAGES ---
# st.logo("assets/codingisfun_logo.png")

# --- RUN NAVIGATION ---
pg.run()
