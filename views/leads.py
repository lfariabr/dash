
import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe
from streamlit_gsheets import GSheetsConnection

# Função para carregar dados do Google Sheets
@st.cache(allow_output_mutation=True)
def load_data_from_gsheet(worksheet_name='data'):
    # Autenticar com Google usando as credenciais do secrets
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_dict = {
        "type": "service_account",
        "project_id": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["project_id"],
        "private_key_id": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["private_key_id"],
        "private_key": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["private_key"].replace('\\n', '\n'),
        "client_email": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["client_email"],
        "client_id": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["client_id"],
        "auth_uri": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["auth_uri"],
        "token_uri": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["client_x509_cert_url"]
    }
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)

    # Abrir a planilha e ler os dados
    spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1Z5TaQavOU5GaJp96X_cR_TA-gw6ZTOjV4hYTqBQwwCc/')
    worksheet = spreadsheet.worksheet(worksheet_name)
    data = get_as_dataframe(worksheet, evaluate_formulas=True)
    return data.dropna(how='all', axis=1)  # Limpa colunas totalmente vazias

# Carregar dados
df_leads = load_data_from_gsheet()

# Filtrar os dados
source_filter = st.selectbox('Selecione a Fonte', df_leads['source'].unique())
store_filter = st.selectbox('Selecione a Loja', df_leads['store'].unique())
category_filter = st.selectbox('Selecione a Categoria', df_leads['category'].unique())

# Aplicar os filtros
filtered_data = df_leads[
    (df_leads['source'] == source_filter) &
    (df_leads['store'] == store_filter) &
    (df_leads['category'] == category_filter)
]

# Visualização dos dados
st.title("Visualização de Dados Filtrados")

# Gráfico de linhas para leads por dia
group_by_day = filtered_data.groupby('createdAt').size().reset_index(name='count')
fig = px.line(group_by_day, x='createdAt', y='count', title='Leads por Dia')
st.plotly_chart(fig)

# Gráfico de barras para leads por loja
group_by_store = filtered_data.groupby('store').size().reset_index(name='count')
fig_store = px.bar(group_by_store, x='store', y='count', title='Leads por Loja')
st.plotly_chart(fig_store)

# Gráfico de pizza para leads por fonte
group_by_source = filtered_data.groupby('source').size().reset_index(name='count')
fig_source = px.pie(group_by_source, names='source', values='count', title='Leads por Fonte')
st.plotly_chart(fig_source)

# Gráfico de pizza para leads por status
group_by_status = filtered_data.groupby('status_apnt').size().reset_index(name='count')
fig_status = px.pie(group_by_status, names='status_apnt', values='count', title='Leads por Status')
st.plotly_chart(fig_status)

# Tabela de leads por loja e dia
groupby_leads_por_store_dia = filtered_data.groupby(['store', 'Dia']).size().reset_index(name='count')
groupby_leads_por_store_dia_pivot = groupby_leads_por_store_dia.pivot(index='store', columns='Dia', values='count').fillna(0)
st.write("Leads por Loja por Dia", groupby_leads_por_store_dia_pivot)

# Execução do script
if __name__ == '__main__':
    st.write("Script executado com sucesso!")
