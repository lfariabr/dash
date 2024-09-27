
import streamlit as st

# --- PAGE SETUP ---
test_page = st.Page(
    "views/teste.py",
    title="teste",
    icon=":material/overview:",
)

test_page2 = st.Page(
    "views/teste2.py",
    title="teste",
    icon=":material/overview:",
)

# --- NAVIGATION SETUP [WITH SECTIONS]---
pg = st.navigation(
    {
        "Teste": [test_page,test_page2],
        "Teste2": [test_page2],
    }
)


# --- SHARED ON ALL PAGES ---
# st.logo("assets/codingisfun_logo.png")

# --- RUN NAVIGATION ---
pg.run()
