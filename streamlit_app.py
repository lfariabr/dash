
import streamlit as st

# Importação dos scripts de página
from views import leads, asyncdata

# Configuração da página
st.set_page_config(page_title="Dashboard de Leads", layout="wide")

# --- SIDEBAR SETUP ---
st.sidebar.markdown("# 📁 Menu")
# Criação dos botões de rádio para a navegação
choice = st.sidebar.radio("Escolha uma página:", ['Conferir dados', 'Baixar dados'])

st.sidebar.markdown("### Notas")
st.sidebar.write("É possível fazer o download dos dados e visualizar os resultados em tempo real!")

# Condicional para executar páginas específicas com base na escolha
if choice == 'Conferir dados':
    leads.run()
elif choice == 'Baixar dados':
    asyncdata.run()

# As funções run() em leads.py e asyncdata.py precisarão ser definidas
# para incluir toda a lógica que estava anteriormente dentro do contexto da página.
