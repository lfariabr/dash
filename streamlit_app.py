
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
    # Carregar dados uma vez e usá-los para preencher as opções de filtro
    df_leads = leads.load_data_from_gsheet()

    # Criação de filtros no sidebar
    all_sources = df_leads['source'].dropna().unique()
    all_stores = df_leads['store'].dropna().unique()
    all_categories = df_leads['category'].dropna().unique()

    # Opções de filtro com 'Todos' incluído
    selected_sources = st.sidebar.multiselect('Select Source', options=all_sources, default=all_sources)
    selected_stores = st.sidebar.multiselect('Select Store', options=all_stores, default=all_stores)
    selected_categories = st.sidebar.multiselect('Select Category', options=all_categories, default=all_categories)

    # Executar a função run do módulo leads, passando os filtros selecionados
    leads.run(selected_sources, selected_stores, selected_categories)
elif choice == 'Baixar dados':
    asyncdata.run()
