
import streamlit as st

# --- PAGE SETUP ---
graphics = st.Page(
    "views/leads.py",
    title="💡 Análise de Leads",
    icon=":bar_chart:",
)

asyncdata = st.Page(
    "views/asyncdata.py",
    title="🔥 Marketing Leads",
    icon=":chart_with_upwards_trend:",
)

# --- CONFIGURAÇÃO DE NAVEGAÇÃO ---
pg = st.navigation(
    {
        "📊 Painel Principal": [asyncdata, graphics],
    }
)

st.sidebar.markdown("### Seções")
st.sidebar.write("Acesse rapidamente as seções principais e acompanhe o desempenho das campanhas!")

# --- RUN NAVIGATION ---
pg.run()
