
import os
import shutil
import subprocess
import pandas as pd
import requests
import json
import streamlit as st
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# if page == "Leads":

@st.cache_data
def load_main_dataframe(data):
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.connect(spreadsheet_id="1Z5TaQavOU5GaJp96X_cR_TA-gw6ZTOjV4hYTqBQwwCc")  # Use o ID da sua planilha
    df_leads = conn.read(worksheet=data)  # lê os dados da aba "data"
    return df_leads

st.title("Leads Carregados")

# leads = 'leads.xlsx'
df_leads = load_main_dataframe('data')

# Extrair o Dia de 'Dia da entrada'
df_leads['Dia'] = df_leads['createdAt'].dt.day

# Deixando apenas Pró-Corpo
lista_lojas_excluir = ['HOMA', 'PRAIA GRANDE', 'PLÁSTICA', 'CENTRAL']

# Remover as lojas
df_leads = df_leads[~df_leads['Unidade'].isin(lista_lojas_excluir)]

# Gráficos
groupby_leads_dia_do_mes = df_leads.groupby('Dia').agg({'ID do lead': 'nunique'}).reset_index()
groupby_leads_por_unidade = df_leads.groupby('Unidade').agg({'ID do lead': 'nunique'}).reset_index()
groupby_leads_por_fonte = df_leads.groupby('Fonte').agg({'ID do lead': 'nunique'}).reset_index()
groupby_leads_por_status = df_leads.groupby('Status').agg({'ID do lead': 'nunique'}).reset_index()

# Tabela
groupby_leads_por_unidade_dia = df_leads.groupby(['Unidade', 'Dia']).agg({'ID do lead': 'nunique'}).reset_index()
groupby_leads_por_unidade_dia_pivot = groupby_leads_por_unidade_dia.pivot(index='Unidade', columns='Dia', values='ID do lead')
groupby_leads_por_unidade_dia_pivot_tabela = groupby_leads_por_unidade_dia.pivot(index='Dia', columns='Unidade', values='ID do lead')
groupby_leads_por_unidade_dia_pivot_tabela = groupby_leads_por_unidade_dia_pivot_tabela.fillna(0)

# Tabelas finais
fontes_pagas = ['Facebook Leads', 'Google Pesquisa', 'Facebook Postlink']
fontes_org = ['Instagram', 'Facebook', 'CRM Bônus', 'Busca Orgânica']

df_leads_pagas = df_leads.loc[df_leads['Fonte'].isin(fontes_pagas)]
df_leads_org = df_leads.loc[df_leads['Fonte'].isin(fontes_org)]

groupby_leads_pagos_por_unidade_dia = df_leads_pagas.groupby(['Unidade', 'Fonte']).agg({'ID do lead': 'nunique'}).reset_index()
groupby_leads_pagos_por_unidade_dia_pivot_tabela = groupby_leads_pagos_por_unidade_dia.pivot(index='Fonte', columns='Unidade', values='ID do lead')

groupby_leads_orgs_por_unidade_dia = df_leads_org.groupby(['Unidade', 'Fonte']).agg({'ID do lead': 'nunique'}).reset_index()
groupby_leads_orgs_por_unidade_dia_pivot_tabela = groupby_leads_orgs_por_unidade_dia.pivot(index='Fonte', columns='Unidade', values='ID do lead')

df_leads_concatenado = pd.concat([groupby_leads_pagos_por_unidade_dia_pivot_tabela, groupby_leads_orgs_por_unidade_dia_pivot_tabela], axis=0)
df_leads_concatenado = df_leads_concatenado.fillna(0)


# Dividindo a tela em duas colunas
col1, col2 = st.columns(2)

with col1:
    st.write("Número de leads por dia")
    graph_dia_do_mes = px.line(
        groupby_leads_dia_do_mes,
        x='Dia',
        y='ID do lead',
        title='Número de Leads por Dia',
        labels={'ID do lead': 'Número de Leads', 'Dia': 'Dia'},
        markers=True
    )
    st.plotly_chart(graph_dia_do_mes)

with col2:
    graph_por_loja = px.bar(
        groupby_leads_por_unidade,
        x='Unidade',
        y='ID do lead',
        title='Número de Leads por Loja',
        labels={'ID do lead': 'Número de Leads', 'Unidade': 'Unidade'},
    )
    st.plotly_chart(graph_por_loja)

    # Dividindo em duas colunas para os gráficos de pizza
col3, col4 = st.columns(2)

with col3:
    graph_por_fonte = px.pie(
        groupby_leads_por_fonte,
        names='Fonte',
        values='ID do lead',
        title='Leads por Fonte',
        labels={'ID do lead': 'Número de Leads', 'Fonte': 'Fonte'},
    )
    st.plotly_chart(graph_por_fonte)

with col4:
    graph_por_status = px.pie(
        groupby_leads_por_status,
        names='Status',
        values='ID do lead',
        title='Leads por Status',
        labels={'ID do lead': 'Número de Leads', 'Status': 'Status'},
    )
    st.plotly_chart(graph_por_status)

# Criar um gráfico de linhas com múltiplas linhas (uma para cada unidade)
df_pivot_melted = groupby_leads_por_unidade_dia_pivot.reset_index().melt(id_vars=['Unidade'], var_name='Dia', value_name='Número de Leads')

graph_evolucao_leads = px.line(
    df_pivot_melted,
    x='Dia',
    y='Número de Leads',
    color='Unidade',  # Diferenciar as linhas por unidade
    title='Evolução dos Leads por Unidade e Dia',
    labels={'Número de Leads': 'Número de Leads', 'Dia': 'Dia'},
    markers=True
)
st.plotly_chart(graph_evolucao_leads)

# Mostrar a tabela pivotada
st.write("Leads por Unidade por Dia")
st.dataframe(groupby_leads_por_unidade_dia_pivot_tabela)

# Mostrar a tabela pivotada
st.write("Leads por Fontes Marketing")
st.dataframe(df_leads_concatenado)
