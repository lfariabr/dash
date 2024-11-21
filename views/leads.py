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
def load_data_from_gsheet():
    try:
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
        spreadsheet_url = st.secrets["GOOGLE_SHEETS"]["url"]
        spreadsheet = client.open_by_url(spreadsheet_url)
        worksheet = spreadsheet.worksheet('data')  
        data = get_as_dataframe(worksheet, evaluate_formulas=True)
        st.toast("✅ Dados carregados com sucesso do Google Sheets")
        return data.dropna(how='all', axis=1)
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados do Google Sheets: {str(e)}")
        return None

def run():
    try:
        # Carregar os dados
        with st.spinner('🔄 Carregando dados...'):
            df_leads = load_data_from_gsheet()
        if df_leads is None:
            st.error("⚠️ Erro ao carregar dados. Por favor, tente novamente mais tarde.")
            return

        # Data Prep: Filtering
        df_leads['createdAt'] = pd.to_datetime(df_leads['createdAt']) 
        df_leads['Dia do mês'] = df_leads['createdAt'].dt.day_name()
        df_leads['Dia'] = df_leads['createdAt'].dt.day
        lista_lojas_excluir = ['HOMA', 'PRAIA GRANDE', 'PLÁSTICA', 'CENTRAL']
        df_leads = df_leads[~df_leads['store'].isin(lista_lojas_excluir)]

        # Criar filtros com seleção múltipla para 'source', 'store' e 'category'
        col5, col6, col7 = st.columns(3)
        with col5:
            all_sources = ['Todas'] + list(df_leads['source'].unique())
            selected_sources = st.multiselect('Filtro de Fonte', options=all_sources, default='Todas')
            if 'Todas' in selected_sources:
                selected_sources = all_sources[1:]  # Exclui "Todas" para usar todas as fontes

        with col6:
            all_stores = ['Todas'] + list(df_leads['store'].unique())
            selected_stores = st.multiselect('Filtro de Unidade', options=all_stores, default='Todas')
            if 'Todas' in selected_stores:
                selected_stores = all_stores[1:]  # Exclui "Todas" para usar todas as lojas

        with col7:
            all_categories = ['Todas'] + list(df_leads['category'].unique())
            selected_categories = st.multiselect('Filtro de Categoria', options=all_categories, default='Todas')
            if 'Todas' in selected_categories:
                selected_categories = all_categories[1:]  # Exclui "TUDO" para usar todas as categorias
        
        # Aplicar filtros
        filtered_data = df_leads.copy()
        if selected_sources:
            filtered_data = filtered_data[filtered_data['source'].isin(selected_sources)]
        if selected_stores:
            filtered_data = filtered_data[filtered_data['store'].isin(selected_stores)]
        if selected_categories:
            filtered_data = filtered_data[filtered_data['category'].isin(selected_categories)]

        # Gráficos
        groupby_leads_dia_do_mes = filtered_data.groupby('Dia').agg({'id': 'nunique'}).reset_index()
        groupby_leads_por_store = filtered_data.groupby('store').agg({'id': 'nunique'}).reset_index()
        groupby_leads_por_source = filtered_data.groupby('source').agg({'id': 'nunique'}).reset_index()
        groupby_leads_por_status_apnt = filtered_data.groupby('status_apnt').agg({'id': 'nunique'}).reset_index()

        # Tabela
        groupby_leads_por_store_dia = filtered_data.groupby(['store', 'Dia']).agg({'id': 'nunique'}).reset_index()
        groupby_leads_por_store_dia_pivot = groupby_leads_por_store_dia.pivot(index='store', columns='Dia', values='id')
        groupby_leads_por_store_dia_pivot_tabela = groupby_leads_por_store_dia.pivot(index='Dia', columns='store', values='id')
        groupby_leads_por_store_dia_pivot_tabela = groupby_leads_por_store_dia_pivot_tabela.fillna(0)

        # Tabelas finais
        sources_pagas = ['Facebook Leads', 'Google Pesquisa', 'Facebook Postlink']
        sources_org = ['Instagram', 'Facebook', 'CRM Bônus', 'Busca Orgânica', 'Acesso Direto ao Site']

        df_leads_pagas = filtered_data.loc[filtered_data['source'].isin(sources_pagas)]
        df_leads_org = filtered_data.loc[filtered_data['source'].isin(sources_org)]

        groupby_leads_pagos_por_store_dia = df_leads_pagas.groupby(['store', 'source']).agg({'id': 'nunique'}).reset_index()
        groupby_leads_pagos_por_store_dia_pivot_tabela = groupby_leads_pagos_por_store_dia.pivot(index='source', columns='store', values='id')

        groupby_leads_orgs_por_store_dia = df_leads_org.groupby(['store', 'source']).agg({'id': 'nunique'}).reset_index()
        groupby_leads_orgs_por_store_dia_pivot_tabela = groupby_leads_orgs_por_store_dia.pivot(index='source', columns='store', values='id')

        # Exibir os gráficos
        st.title("Leads S.S. - Gráficos")
        st.write("v1.0.0")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Leads por dia do mês")
            fig_dia_do_mes = px.bar(groupby_leads_dia_do_mes, x='Dia', y='id', title='Leads por dia do mês')
            st.plotly_chart(fig_dia_do_mes)

        with col2:
            st.subheader("Leads por unidade")
            fig_store = px.bar(groupby_leads_por_store, x='store', y='id', title='Leads por unidade')
            st.plotly_chart(fig_store)

        col3, col4 = st.columns(2)
        with col3:
            st.subheader("Leads por fonte")
            fig_source = px.bar(groupby_leads_por_source, x='source', y='id', title='Leads por fonte')
            st.plotly_chart(fig_source)

        with col4:
            st.subheader("Leads por status")
            fig_status = px.bar(groupby_leads_por_status_apnt, x='status_apnt', y='id', title='Leads por status')
            st.plotly_chart(fig_status)

        # Exibir as tabelas
        st.subheader("Leads por unidade e dia")
        st.write(groupby_leads_por_store_dia_pivot_tabela)

        st.subheader("Leads pagos por unidade")
        st.write(groupby_leads_pagos_por_store_dia_pivot_tabela)

        st.subheader("Leads orgânicos por unidade")
        st.write(groupby_leads_orgs_por_store_dia_pivot_tabela)
        
        st.toast("✨ Página de gráficos carregada com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao processar dados dos leads: {str(e)}")
        st.error("⚠️ Erro ao processar os dados. Por favor, tente novamente mais tarde.")

if __name__ == "__main__":
    run()
