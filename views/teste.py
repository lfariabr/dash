
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
st.dataframe(df_leads)
