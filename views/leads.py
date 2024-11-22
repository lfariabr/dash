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
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
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
            "client_x509_cert_url": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["client_x509_cert_url"],
            "universe_domain": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["universe_domain"]
        }
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)

        try:
            # First try to open by URL
            spreadsheet_url = st.secrets["GOOGLE_SHEETS"]["url"]
            spreadsheet = client.open_by_url(spreadsheet_url)
        except Exception as url_error:
            st.error(f"Failed to open by URL: {str(url_error)}")
            # If URL fails, try to extract and open by key
            sheet_id = spreadsheet_url.split('/')[5]  # Extract ID from URL
            spreadsheet = client.open_by_key(sheet_id)
        
        worksheet_name = st.secrets["GOOGLE_SHEETS"].get("worksheet", "data")
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        data = get_as_dataframe(worksheet, evaluate_formulas=True)
        st.toast("✅ Dados carregados com sucesso do Google Sheets")
        return data.dropna(how='all', axis=1)
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados do Google Sheets: {str(e)}")
        # Print more detailed error information
        import traceback
        st.error(f"Detailed error: {traceback.format_exc()}")
        return None

def run():
    try:
        # Carregar os dados
        with st.spinner('🔄 Carregando dados...'):
            df_leads = load_data_from_gsheet()
        if df_leads is None:
            st.error("⚠️ Erro ao carregar dados. Por favor, tente novamente mais tarde.")
            return

        # Exibir os gráficos
        st.title("Leads S.S. - Gráficos")
        st.write("v1.0.0")
    
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
        groupby_leads_dia_do_mes = filtered_data.groupby(['Dia', 'category']).agg({'id': 'nunique'}).reset_index()
        groupby_leads_por_store = filtered_data.groupby(['store', 'category']).agg({'id': 'nunique'}).reset_index()
        groupby_leads_por_source = filtered_data.groupby('source').agg({'id': 'nunique'}).reset_index()
        groupby_leads_por_status_apnt = filtered_data.groupby(['status_apnt', 'category']).agg({'id': 'nunique'}).reset_index()

        # Tabela
        groupby_leads_por_store_dia = filtered_data.groupby(['store', 'Dia']).agg({'id': 'nunique'}).reset_index()
        groupby_leads_por_store_dia_pivot = groupby_leads_por_store_dia.pivot(index='store', columns='Dia', values='id').fillna(0)
        groupby_leads_por_store_dia_pivot_tabela = groupby_leads_por_store_dia.pivot(index='Dia', columns='store', values='id').fillna(0)

        # Nova tabela: Leads por categoria por unidade
        groupby_leads_por_categoria_unidade = filtered_data.groupby(['category', 'store']).agg({'id': 'nunique'}).reset_index()
        groupby_leads_por_categoria_unidade_pivot = groupby_leads_por_categoria_unidade.pivot(index='category', columns='store', values='id').fillna(0)

        # Tabelas finais
        sources_pagas = ['Facebook Leads', 'Google Pesquisa', 'Facebook Postlink']
        sources_org = ['Instagram', 'Facebook', 'CRM Bônus', 'Busca Orgânica', 'Acesso Direto ao Site']

        df_leads_pagas = filtered_data.loc[filtered_data['source'].isin(sources_pagas)]
        df_leads_org = filtered_data.loc[filtered_data['source'].isin(sources_org)]

        groupby_leads_pagos_por_store_dia = df_leads_pagas.groupby(['store', 'source']).agg({'id': 'nunique'}).reset_index()
        groupby_leads_pagos_por_store_dia_pivot_tabela = groupby_leads_pagos_por_store_dia.pivot(index='source', columns='store', values='id').fillna(0)

        groupby_leads_orgs_por_store_dia = df_leads_org.groupby(['store', 'source']).agg({'id': 'nunique'}).reset_index()
        groupby_leads_orgs_por_store_dia_pivot_tabela = groupby_leads_orgs_por_store_dia.pivot(index='source', columns='store', values='id').fillna(0)



        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Leads por dia do mês")
            fig_dia_do_mes = px.bar(groupby_leads_dia_do_mes, x='Dia', y='id', color='category',
                                  
                                  labels={'id': 'Número de Leads', 'Dia': 'Dia do Mês'})
            st.plotly_chart(fig_dia_do_mes)

        with col2:
            st.subheader("Leads por unidade")
            fig_store = px.bar(groupby_leads_por_store, x='store', y='id', color='category',
                            
                             labels={'id': 'Número de Leads', 'store': 'Unidade'})
            st.plotly_chart(fig_store)

        col3, col4 = st.columns(2)
        with col3:
            st.subheader("Leads por fonte")
            fig_source = px.pie(groupby_leads_por_source, values='id', names='source',
                              labels={'id': 'Número de Leads', 'source': 'Fonte'})
            fig_source.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_source)

        with col4:
            st.subheader("Leads por status")
            
            # Change checkbox label and key
            show_absolute = st.checkbox('Ver números absolutos', key='status_absolute')
            
            # Calculate percentages within each status
            total_by_status = groupby_leads_por_status_apnt.groupby('status_apnt')['id'].sum().reset_index()
            total_by_status.columns = ['status_apnt', 'total']
            
            # Merge with original dataframe to calculate percentages
            groupby_leads_por_status_apnt = groupby_leads_por_status_apnt.merge(total_by_status, on='status_apnt')
            groupby_leads_por_status_apnt['percentage'] = (groupby_leads_por_status_apnt['id'] / groupby_leads_por_status_apnt['total'] * 100).round(1)
            
            # Create hover text
            groupby_leads_por_status_apnt['hover_text'] = (
                'Categoria: ' + groupby_leads_por_status_apnt['category'] + '<br>' +
                'Total: ' + groupby_leads_por_status_apnt['id'].astype(str) + '<br>' +
                'Porcentagem: ' + groupby_leads_por_status_apnt['percentage'].astype(str) + '%'
            )
            
            fig_status = px.bar(groupby_leads_por_status_apnt, 
                              x='status_apnt', 
                              y='id' if show_absolute else 'percentage',
                              color='category',
                              labels={'percentage': '% do Status', 
                                    'id': 'Número de Leads',
                                    'status_apnt': 'Status'},
                              custom_data=['hover_text'])
            
            # Set y-axis range only for percentage view
            if not show_absolute:
                fig_status.update_layout(yaxis_range=[0, 100])
                
            # Update hover template
            fig_status.update_traces(
                hovertemplate="%{customdata[0]}<extra></extra>"
            )
            
            st.plotly_chart(fig_status)

        # Exibir as tabelas
        st.subheader("Leads por unidade e dia")
        st.write(groupby_leads_por_store_dia_pivot_tabela)

        st.subheader("Leads por categoria por unidade")
        st.write(groupby_leads_por_categoria_unidade_pivot)

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
