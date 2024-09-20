
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

  # Filter data for SP units
  df_leads_total = df_leads

  # Group by dia do mês and count unique leads
  groupby_leads_dia_do_mes = df_leads.groupby('apenas_o_dia').agg({'ID do lead': 'nunique'}).reset_index()

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
