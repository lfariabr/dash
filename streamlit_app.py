
import os
import shutil
import subprocess
import pandas as pd
import os
import requests
import json
import streamlit as st
import pandas as pd # novo 3
import plotly.express as px

st.sidebar.title("Navigation") # Novo
page = st.sidebar.selectbox("Choose a page", ["Leads"]) # Novo


if page == "Leads":

  st.title("Leads!")

  leads = 'leads.xlsx'
  df_leads = pd.read_excel(leads)

  # Playing with dates
  df_leads['Dia da entrada'] = pd.to_datetime(df_leads['Dia da entrada']) # trata estes dados como texto
  df_leads['Dia do mês'] = df_leads['Dia da entrada'].dt.day_name()

  # Extract day of the month from 'Dia da entrada'
  df_leads['apenas_o_dia'] = df_leads['Dia da entrada'].dt.day

  # Deixando apenas Pró-Corpo
  lista_lojas_excluir = ['HOMA', 'PRAIA GRANDE', 'PLÁSTICA', 'CENTRAL']

  # Removendo as lojas
  df_leads = df_leads[~df_leads['Unidade'].isin(lista_lojas_excluir)]

  # Filter data for SP units
  df_leads_total = df_leads

  # Gráficos
  # Group by dia do mês and count unique leads
  groupby_leads_dia_do_mes = df_leads.groupby('apenas_o_dia').agg({'ID do lead': 'nunique'}).reset_index()
  groupby_leads_por_unidade = df_leads.groupby('Unidade').agg({'ID do lead': 'nunique'}).reset_index()
  groupby_leads_por_fonte = df_leads.groupby('Fonte').agg({'ID do lead': 'nunique'}).reset_index()
  groupby_leads_por_status = df_leads.groupby('Status').agg({'ID do lead': 'nunique'}).reset_index()

  # Tabela
  # Groupby unidade por dia / loja pivotado
  groupby_leads_por_unidade_dia = df_leads.groupby(['Unidade', 'apenas_o_dia']).agg({'ID do lead': 'nunique'}).reset_index()
  groupby_leads_por_unidade_dia_pivot = groupby_leads_por_unidade_dia.pivot(index='Unidade', columns='apenas_o_dia', values='ID do lead')

  st.write("Número de leads por dia")

  # Create line graph for leads by day of the month
  graph_dia_do_mes = px.line(
      groupby_leads_dia_do_mes,
      x='apenas_o_dia',
      y='ID do lead',
      title='Número de Leads por apenas_o_dia',
      labels={'ID do lead': 'Número de Leads', 'apenas_o_dia': 'Dia do mês'},
      markers=True  # Adiciona marcadores nos pontos da linha
  )
  # Display the graph
  st.plotly_chart(graph_dia_do_mes)

  # Create bar graph for leads by day of the month
  graph_por_loja = px.bar(
      groupby_leads_por_unidade,
      x='Unidade',
      y='ID do lead',
      title='Número de Leads por loja',
      labels={'ID do lead': 'Número de Leads', 'Unidade': 'Unidade'},
  )

  # Display the graph
  st.plotly_chart(graph_por_loja)

  # Create pizza chart for leads per font
  graph_por_fonte = px.pie(
      groupby_leads_por_fonte,
      names='Fonte',
      values='ID do lead',
      title='Número de Leads por Fonte',
      labels={'ID do lead': 'Número de Leads', 'Fonte': 'Fonte'},
  )

  # Display the graph
  st.plotly_chart(graph_por_fonte)

  # Create pizza graph for leads per status
  graph_por_status = px.pie(
      groupby_leads_por_status,
      names='Status',
      values='ID do lead',
      title='Número de Leads por Status',
      labels={'ID do lead': 'Número de Leads', 'Status': 'Status'},
  )

  # Reset index for better plotly interaction
  df_pivot_melted = groupby_leads_por_unidade_dia_pivot.reset_index().melt(id_vars=['Unidade'], var_name='Dia do mês', value_name='Número de Leads')

  # Create a line chart with multiple lines (one for each unit)
  graph_evolucao_leads = px.line(
      df_pivot_melted,
      x='Dia do mês',
      y='Número de Leads',
      color='Unidade',  # Different line for each unit
      title='Evolução dos Leads por Unidade e Dia do Mês',
      labels={'Número de Leads': 'Número de Leads', 'Dia do mês': 'Dia do Mês'},
      markers=True  # Adiciona marcadores nos pontos da linha
  )

  # Display the graph
  st.plotly_chart(graph_evolucao_leads)

  # Display pivotable with data
  st.write("Pivotable com dados")
  st.write(groupby_leads_por_unidade_dia_pivot)
