
import streamlit as st

# --- PAGE SETUP ---
graphics = st.Page(
    "views/leads.py",
    title="Leads",
    icon="📊",  # Emoji padrão de gráfico de barra
)

asyncdata = st.Page(
    "views/asyncdata.py",
    title="Marketing Leads",
    icon="📈",  # Emoji padrão de gráfico de linha
)

# --- NAVIGATION SETUP [WITH SECTIONS] ---
pg = st.navigation(
    {
        "📁 Menu": [asyncdata, graphics],  # Incluindo um emoji de pasta para o menu principal
    }
)

st.sidebar.markdown("### Seções")
st.sidebar.write("Acesse rapidamente as seções principais e acompanhe o desempenho das campanhas!")

# --- RUN NAVIGATION ---
pg.run()
