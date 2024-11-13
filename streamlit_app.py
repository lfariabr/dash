
import streamlit as st

# Configuração inicial da página
st.set_page_config(page_title="Dashboard", layout="wide")

# Importação dos scripts de página após a configuração inicial
from views import leads, asyncdata

# --- SIDEBAR SETUP ---
st.sidebar.markdown("# 📁 Menu")
# Criação dos botões de rádio para a navegação
choice = st.sidebar.radio("Escolha uma página:", ['Análise de dados', 'Fazer download'])

st.sidebar.markdown("### Notas")
st.sidebar.write("É possível fazer o download dos dados e visualizar os resultados em tempo real!")

# Condicional para executar páginas específicas com base na escolha
if choice == 'Análise de dados':
    leads.run()
elif choice == 'Fazer download':
    asyncdata.run()
