
import streamlit as st

# Configuração inicial da página
st.set_page_config(page_title="Dashboard de Leads", layout="wide")

# Importação dos scripts de página após a configuração inicial
from views import leads, asyncdata

# --- SIDEBAR SETUP ---
st.sidebar.markdown("# 📁 Menu")
# Criação dos botões de rádio para a navegação
choice = st.sidebar.radio("Escolha uma página:", ['Conferir dados', 'Baixar dados'])

st.sidebar.markdown("### Notas")
st.sidebar.write("É possível fazer o download dos dados e visualizar os resultados em tempo real!")

# Condicional para executar páginas específicas com base na escolha
if choice == 'Conferir dados':
    
  col5, col6, col7 = st.columns(3)
  with col5:
    selected_sources = st.multiselect('Select Source', options=df_leads['source'].unique(), default=df_leads['source'].unique())
  with col6:
    selected_stores = st.multiselect('Select Store', options=df_leads['store'].unique(), default=df_leads['store'].unique())
  with col7:
    selected_categories = st.multiselect('Select Category', options=df_leads['category'].unique(), default=df_leads['category'].unique())

    leads.run()
elif choice == 'Baixar dados':
    asyncdata.run()
