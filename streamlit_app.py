
import streamlit as st

# --- PAGE SETUP ---
graphics = st.Page(
    "views/leads.py",
    title="Conferir dados",
    icon="📊",
)

asyncdata = st.Page(
    "views/asyncdata.py",
    title="Baixar dados",
    icon="📈",
)

# --- NAVIGATION SETUP [WITH SECTIONS] ---
pg = st.navigation(
    {
        "📁 Menu": [asyncdata, graphics],
    }
)

st.sidebar.markdown("### Notas")
st.sidebar.write("É possível fazer o download dos dados e visualizar os resultados em tempo real!")

# --- RUN NAVIGATION ---
pg.run()
