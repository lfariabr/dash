
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
def load_main_dataframe(worksheet):

  conn = st.connection("gsheets", type=GSheetsConnection)
  df_leads = conn.read(worksheet=worksheet) # dtype={"Ad ID": str}

  return df_leads

st.title("Pag 10 - Leads")

# leads = 'leads.xlsx'
df_leads = load_main_dataframe('worksheet')

# Trabalhando com datas
df_leads['Dia da entrada'] = pd.to_datetime(df_leads['Dia da entrada']) # trata estes dados como texto
df_leads['Dia do mês'] = df_leads['Dia da entrada'].dt.day_name()

# Extrair o dia do mês de 'Dia da entrada'
df_leads['Dia'] = df_leads['Dia da entrada'].dt.day

# Deixando apenas Pró-Corpo
lista_lojas_excluir = ['HOMA', 'PRAIA GRANDE', 'PLÁSTICA', 'CENTRAL']

# Remover as lojas
df_leads = df_leads[~df_leads['Unidade'].isin(lista_lojas_excluir)]

st.dataframe(df_leads)
