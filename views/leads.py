
import os
import shutil
import subprocess
import pandas as pd
import requests
import json
import streamlit as st
import plotly.express as px
import gspread
from streamlit_gsheets import GSheetsConnection
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe


# Função para carregar dados do Google Sheets
@st.cache(allow_output_mutation=True)
def load_data_from_gsheet():
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
    worksheet = spreadsheet.worksheet('data')
    data = get_as_dataframe(worksheet, evaluate_formulas=True)
    return data.dropna(how='all', axis=1)  # Limpa colunas totalmente vazias

df_leads = load_data_from_gsheet()
st.title("Leads Self Service")
st.write("v1.0.0")

st.write(df_leads)

# Data Prep: Filtering
df_leads['createdAt'] = pd.to_datetime(df_leads['createdAt']) # trata estes dados como texto
df_leads['Dia do mês'] = df_leads['createdAt'].dt.day_name()
df_leads['Dia'] = df_leads['createdAt'].dt.day
lista_lojas_excluir = ['HOMA', 'PRAIA GRANDE', 'PLÁSTICA', 'CENTRAL']
df_leads = df_leads[~df_leads['store'].isin(lista_lojas_excluir)]

# Gráficos
groupby_leads_dia_do_mes = df_leads.groupby('Dia').agg({'id': 'nunique'}).reset_index()
groupby_leads_por_store = df_leads.groupby('store').agg({'id': 'nunique'}).reset_index()
groupby_leads_por_source = df_leads.groupby('source').agg({'id': 'nunique'}).reset_index()
groupby_leads_por_status_apnt = df_leads.groupby('status_apnt').agg({'id': 'nunique'}).reset_index()

# Tabela
groupby_leads_por_store_dia = df_leads.groupby(['store', 'Dia']).agg({'id': 'nunique'}).reset_index()
groupby_leads_por_store_dia_pivot = groupby_leads_por_store_dia.pivot(index='store', columns='Dia', values='id')
groupby_leads_por_store_dia_pivot_tabela = groupby_leads_por_store_dia.pivot(index='Dia', columns='store', values='id')
groupby_leads_por_store_dia_pivot_tabela = groupby_leads_por_store_dia_pivot_tabela.fillna(0)

# Tabelas finais
sources_pagas = ['Facebook Leads', 'Google Pesquisa', 'Facebook Postlink']
sources_org = ['Instagram', 'Facebook', 'CRM Bônus', 'Busca Orgânica']

df_leads_pagas = df_leads.loc[df_leads['source'].isin(sources_pagas)]
df_leads_org = df_leads.loc[df_leads['source'].isin(sources_org)]

groupby_leads_pagos_por_store_dia = df_leads_pagas.groupby(['store', 'source']).agg({'id': 'nunique'}).reset_index()
groupby_leads_pagos_por_store_dia_pivot_tabela = groupby_leads_pagos_por_store_dia.pivot(index='source', columns='store', values='id')

groupby_leads_orgs_por_store_dia = df_leads_org.groupby(['store', 'source']).agg({'id': 'nunique'}).reset_index()
groupby_leads_orgs_por_store_dia_pivot_tabela = groupby_leads_orgs_por_store_dia.pivot(index='source', columns='store', values='id')

df_leads_concatenado = pd.concat([groupby_leads_pagos_por_store_dia_pivot_tabela, groupby_leads_orgs_por_store_dia_pivot_tabela], axis=0)
df_leads_concatenado = df_leads_concatenado.fillna(0)


# Dividindo a tela em duas colunas
col1, col2 = st.columns(2)

with col1:
    graph_dia_do_mes = px.line(
        groupby_leads_dia_do_mes,
        x='Dia',
        y='id',
        title='Leads por Dia do Mês',
        labels={'id': 'Leads', 'Dia': 'Dia do mês'},
        markers=True
    )
    st.plotly_chart(graph_dia_do_mes)

with col2:
    graph_por_loja = px.bar(
        groupby_leads_por_store,
        x='store',
        y='id',
        title='Leads por Loja',
        labels={'id': 'Leads', 'store': 'store'},
    )
    st.plotly_chart(graph_por_loja)

    # Dividindo em duas colunas para os gráficos de pizza
col3, col4 = st.columns(2)

with col3:
    graph_por_source = px.pie(
        groupby_leads_por_source,
        names='source',
        values='id',
        title='Leads por source',
        labels={'id': 'Leads', 'source': 'source'},
    )
    st.plotly_chart(graph_por_source)

with col4:
    graph_por_status_apnt = px.pie(
        groupby_leads_por_status_apnt,
        names='status_apnt',
        values='id',
        title='Leads por status_apnt',
        labels={'id': 'Leads', 'status_apnt': 'status_apnt'},
    )
    st.plotly_chart(graph_por_status_apnt)

# Criar um gráfico de linhas com múltiplas linhas (uma para cada store)
df_pivot_melted = groupby_leads_por_store_dia_pivot.reset_index().melt(id_vars=['store'], var_name='Dia do mês', value_name='Leads')

graph_evolucao_leads = px.line(
    df_pivot_melted,
    x='Dia do mês',
    y='Lead',
    color='store',  # Diferenciar as linhas por store
    title='Evolução dos Leads por store e Dia do Mês',
    labels={'Lead': 'Número de Leads', 'Dia do mês': 'Dia do Mês'},
    markers=True
)
st.plotly_chart(graph_evolucao_leads)

# Mostrar a tabela pivotada
st.write("Leads por store por Dia")
st.dataframe(groupby_leads_por_store_dia_pivot_tabela)

# Mostrar a tabela pivotada
st.write("Leads por sources Marketing")
st.dataframe(df_leads_concatenado)
