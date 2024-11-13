
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
    # Carregar dados antecipadamente para que os filtros possam usar dados atualizados
    df_leads = leads.load_data_from_gsheet()

    # Criação de filtros no sidebar
    selected_sources = st.sidebar.multiselect('Select Source', options=df_leads['source'].unique(), default=df_leads['source'].unique())
    selected_stores = st.sidebar.multiselect('Select Store', options=df_leads['store'].unique(), default=df_leads['store'].unique())
    selected_categories = st.sidebar.multiselect('Select Category', options=df_leads['category'].unique(), default=df_leads['category'].unique())
    
    # Executar a função run do módulo leads, passando os filtros selecionados
    leads.run(df_leads, selected_sources, selected_stores, selected_categories)
elif choice == 'Baixar dados':
    asyncdata.run()
