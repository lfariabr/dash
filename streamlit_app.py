
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

# Configuração inicial da página
st.set_page_config(page_title="Dashboard de Dados", page_icon="🌟", layout="wide")

# Menu na barra lateral para navegação entre as páginas
st.sidebar.markdown("## Navegação")
page = st.sidebar.radio("Selecione uma página:", ["Conferir dados", "Baixar dados"])

# Seção de notas e filtros no sidebar
st.sidebar.markdown("### Notas")
st.sidebar.write("É possível fazer o download dos dados e visualizar os resultados em tempo real!")

# Condicional para mostrar os filtros apenas na página "Conferir Dados"
if page == "Conferir dados":
    # Supõe-se que df_leads está disponível globalmente ou carregado aqui
    df_leads = load_data()  # Assumindo que existe uma função para carregar dados

    # Criar filtros com seleção múltipla para 'source', 'store' e 'category'
    selected_sources = st.sidebar.multiselect('Select Source', options=df_leads['source'].unique(), default=df_leads['source'].unique())
    selected_stores = st.sidebar.multiselect('Select Store', options=df_leads['store'].unique(), default=df_leads['store'].unique())
    selected_categories = st.sidebar.multiselect('Select Category', options=df_leads['category'].unique(), default=df_leads['category'].unique())

    # Atualizar a exibição dos dados com base nos filtros
    df_filtered = df_leads[df_leads['source'].isin(selected_sources) & df_leads['store'].isin(selected_stores) & df_leads['category'].isin(selected_categories)]
    graphics.run(filtered_data=df_filtered)  # Certifique-se de que a página pode receber e usar 'filtered_data'
else:
    asyncdata.run()

# --- RUN NAVIGATION ---
page.run()
