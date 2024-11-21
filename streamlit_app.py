import streamlit as st

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="Dashboard de Leads",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

from views import leads, asyncdata
# from modules.utils.logging import setup_logging
import traceback

# Initialize logging
# logger = setup_logging()

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 1rem;
    }
    .stRadio > div {
        padding: 10px;
        background-color: transparent !important;
        border-radius: 5px;
    }
    .stSidebar .stRadio > div {
        margin-bottom: 10px;
    }
    div[data-testid="stSidebarNav"] {
        background-color: transparent !important;
    }
    .st-emotion-cache-1cypcdb {
        background-color: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar setup
st.sidebar.markdown("## 📁 Menu")

# Define available pages
PAGES = {
    "Fazer Download": asyncdata.run,
    "Visualizar Dados": leads.run,
}

# Radio button for page selection
page = st.sidebar.radio("Escolha uma página:", list(PAGES.keys()))

# Information section in sidebar
st.sidebar.markdown("___")
st.sidebar.markdown("### 💎 Observações")
st.sidebar.write("É possível fazer o download dos dados e visualizar os resultados em tempo real!")

# Version info
st.sidebar.markdown("___")
st.sidebar.markdown("### ℹ️ Versão")
st.sidebar.text("v3.0.0")

# Main content area
try:
    with st.spinner('Carregando...'):
        # Run the selected page
        PAGES[page]()
except Exception as e:
    # logger.error(f"Error loading page {page}: {str(e)}")
    st.error(f"""
        Ocorreu um erro ao carregar a página.
        Por favor, tente novamente ou contate o suporte se o problema persistir.
        
        Detalhes do erro: {str(e)}
    """)
    if st.sidebar.checkbox("Mostrar detalhes técnicos"):
        st.sidebar.code(traceback.format_exc())
