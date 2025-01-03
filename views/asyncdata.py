import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import asyncio
import aiohttp
import nest_asyncio
import time

nest_asyncio.apply()

# Define the Streamlit page
st.title("Leads S.S. - Download")
st.write("v3.0.0")

def run():
  # Define layout em duas colunas
  col1, col2 = st.columns(2)

  with st.form("input_form"):
      with col1:
          start_date = st.date_input("Data inicial", value=datetime.today().replace(day=2))
          end_date = st.date_input("Data final", value=datetime.today() - timedelta(days=1))

      with col2:
          extended_end_date = st.date_input("Data da Agenda", value=datetime.today() + timedelta(days=15))
          token = st.text_input("Senha", type="password")

      # Submit button para o form
      submitted = st.form_submit_button("Pegar os Dados")

  # Placeholder for log area
  log_area = st.empty()  # This will be used to display real-time logs
  log_messages = []

  def update_log(message):
    log_messages.append(message)
    log_area.text("\n".join(log_messages))

  # If the form is submitted, run the fetching logic
  if submitted:
      # Format dates to match the required format
      start_date_str = start_date.strftime('%Y-%m-%d')
      end_date_str = end_date.strftime('%Y-%m-%d')
      extended_end_date_str = extended_end_date.strftime('%Y-%m-%d')

      # Update the log area with initial message
      update_log("Pedido recebido!")
      time.sleep(2)
      update_log("Processando os dados...")
      update_log(" ")
      time.sleep(2)

      update_log("Acompanhe o progresso abaixo:")
      update_log(" ")

      async def fetch_graphql(session, url, query, variables, token):
          headers = {
              'Content-Type': 'application/json',
              'Authorization': f'Bearer {token}',
          }
          payload = {
              'query': query,
              'variables': variables,
          }

          attempt = 0
          while True:
              try:
                  async with session.post(url, headers=headers, json=payload) as response:
                      if response.status == 200:
                          data = await response.json()
                          if 'errors' in data:
                              update_log(f"GraphQL errors: {data['errors']}")
                              return None
                          return data
                      else:
                          update_log(f"Ops... erro {response.status}!")
              except aiohttp.ClientError as e:
                  update_log(f"Request exception: {e}")

              # Exponential backoff and retry
              attempt += 1
              wait_time = min(5 * 2 ** attempt, 30)
              update_log(f"Tentando novamente em {wait_time} segundos... (Tentativa {attempt})")
              await asyncio.sleep(wait_time)

      async def fetch_all_leads(session, start_date, end_date, token):
          current_page = 1
          all_leads = []

          while True:
              query = '''query ($filters: LeadFiltersInput, $pagination: PaginationInput) {
                          fetchLeads(filters: $filters, pagination: $pagination) {
                              data {
                                  createdAt
                                  id
                                  source {
                                      title
                                  }
                                  store {
                                      name
                                  }
                                  status {
                                      label
                                  }
                                  customer {
                                      id
                                      name
                                  }
                                  name
                                  telephone
                                  email
                                  message
                                  utmMedium
                                  utmContent
                                  utmCampaign
                                  utmSearch
                                  utmTerm
                              }
                              meta {
                                  currentPage
                                  lastPage
                              }
                          }
                      }'''

              variables = {
                  'filters': {
                      'createdAtRange': {
                          'start': start_date,
                          'end': end_date,
                      },
                  },
                  'pagination': {
                      'currentPage': current_page,
                      'perPage': 80,
                  },
              }

              data = await fetch_graphql(session, 'https://open-api.eprocorpo.com.br/graphql', query, variables, token)

              if data is None:
                  update_log(f"Failed to fetch leads on page {current_page}. Retrying...")
                  continue

              leads_data = data['data']['fetchLeads']['data']
              all_leads.extend(leads_data)

              meta = data['data']['fetchLeads']['meta']
              last_page = meta['lastPage']

              update_log(f"Baixando Leads. Pág: {current_page}/{last_page}.") # De: {start_date} - Até: {end_date}

              if current_page >= last_page:
                  break

              current_page += 1
              await asyncio.sleep(5)

          return all_leads

      async def fetch_appointments(session, start_date, extended_end_date, token):
          current_page = 1
          all_appointments = []

          while True:
              query = '''query ($filters: AppointmentFiltersInput, $pagination: PaginationInput) {
                          fetchAppointments(filters: $filters, pagination: $pagination) {
                              meta {
                                  currentPage
                                  lastPage
                              }
                              data {
                                  id
                                  status {
                                      label
                                  }
                                  createdBy {
                                      name
                                      createdAt
                                  }
                                  store {
                                      name
                                  }
                                  customer {
                                      id
                                      name
                                      telephones {
                                          number
                                      }
                                  }
                                  procedure {
                                      name
                                      groupLabel
                                  }
                                  employee {
                                      name
                                  }
                                  startDate
                              }
                          }
                      }'''
              variables = {
                  'filters': {
                      'startDateRange': {
                          'start': start_date,
                          'end': extended_end_date,
                      },
                  },
                  'pagination': {
                      'currentPage': current_page,
                      'perPage': 100,
                  }
              }

              data = await fetch_graphql(session, 'https://open-api.eprocorpo.com.br/graphql', query, variables, token)

              if data is None:
                  update_log(f"Failed to fetch appointments on page {current_page}. Retrying...")
                  continue

              appointments_data = [
                  {
                      "id": row['id'],
                      "status_label": row.get('status', {}).get('label', 'N/A'),
                      "store_name": row.get('store', {}).get('name', 'N/A'),
                      "customer_id": row.get('customer', {}).get('id', 'N/A'),
                      "customer_name": row.get('customer', {}).get('name', 'N/A'),
                      "customer_telephone": (
                          row.get('customer', {}).get('telephones', [{}])[0].get('number', 'N/A')
                          if row.get('customer', {}).get('telephones') else 'N/A'
                      ),
                      "procedure_name": row.get('procedure', {}).get('name', 'N/A'),
                      "procedure_group": row.get('procedure', {}).get('groupLabel', 'N/A'),
                      "employee_name": row.get('employee', {}).get('name', 'N/A'),
                      "createdBy_name": row.get('createdBy', {}).get('name', 'N/A'),
                      "createdBy_createdAt": row.get('createdBy', {}).get('createdAt', 'N/A'),
                      "startDate": row.get('startDate', 'N/A'),
                  }
                  for row in data['data']['fetchAppointments']['data']
              ]
              all_appointments.extend(appointments_data)

              meta = data['data']['fetchAppointments']['meta']
              last_page = meta['lastPage']

              update_log(f"Baixando Agendamentos. Pág. {current_page}/{last_page}.") # De: {start_date} - Até: {extended_end_date}

              if current_page >= last_page:
                  break

              current_page += 1
              await asyncio.sleep(5)

          return all_appointments

      async def fetch_bill_charges(session, start_date, end_date, token):
          current_page = 1
          all_bill_charges = []

          while True:
              query = '''query ($filters: BillChargeFiltersInput, $pagination: PaginationInput) {
                      fetchBillCharges(filters: $filters, pagination: $pagination) {
                          data {
                              quote {
                                  id
                                  customer {
                                      id
                                      name
                                      taxvat
                                      email
                                  }
                                  status
                                  bill {
                                      total
                                      installmentsQuantity
                                      items {
                                          amount
                                          description
                                          quantity
                                      }
                                  }
                              }
                              store {
                                  name
                              }
                              amount
                              paidAt
                              dueAt
                              isPaid
                              paymentMethod {
                                  name
                              }
                          }
                          meta {
                              currentPage
                              lastPage
                          }
                      }
                  }'''
              variables = {
                  'filters': {
                      'paidAtRange': {
                          'start': start_date,
                          'end': end_date,
                      }
                  },
                  'pagination': {
                      'currentPage': current_page,
                      'perPage': 100,
                  }
              }

              data = await fetch_graphql(session, 'https://open-api.eprocorpo.com.br/graphql', query, variables, token)

              if data is None:
                  update_log(f"Failed to fetch bill charges on page {current_page}. Retrying...")
                  continue

              bill_charges_data = data['data']['fetchBillCharges']['data']
              all_bill_charges.extend(bill_charges_data)

              meta = data['data']['fetchBillCharges']['meta']
              update_log(f"Baixando Vendas. Pág. {current_page}/{meta['lastPage']}.") # De: {start_date} - Até: {end_date}
              last_page = meta['lastPage']

              if current_page >= last_page:
                  break

              current_page += 1
              await asyncio.sleep(5)

          return all_bill_charges

      # Função assíncrona principal para buscar todos os dados simultaneamente
      async def fetch_all_data(start_date, end_date, extended_end_date, token):
          async with aiohttp.ClientSession() as session:
              leads_task = fetch_all_leads(session, start_date, end_date, token)  # Para leads, usa end_date original
              appointments_task = fetch_appointments(session, start_date, extended_end_date, token)  # Usa extended_end_date para appointments
              bill_charges_task = fetch_bill_charges(session, start_date, end_date, token)  # Para bill charges, usa end_date original

              leads_data, appointments_data, bill_charges_data = await asyncio.gather(
                  leads_task, appointments_task, bill_charges_task
              )

              return leads_data, appointments_data, bill_charges_data

      # Função wrapper para executar as funções assíncronas no ambiente do Streamlit
      def run_fetch_all(start_date, end_date, extended_end_date, token):
          return asyncio.run(fetch_all_data(start_date, end_date, extended_end_date, token))

      # Executa a função assíncrona para buscar todos os dados
      leads_data, appointments_data, bill_charges_data = run_fetch_all(start_date_str, end_date_str, extended_end_date_str, token)

      # Exibir os dados obtidos no Streamlit
      if leads_data:
          df_leads = pd.DataFrame(leads_data)
          st.success(f"✅ Total de Leads: {df_leads.shape[0]} resultados")
      else:
          update_log("❌ Nenhum lead encontrado ou ocorreu um erro durante a busca.")

      if appointments_data:
          # Create DataFrame first
          df_appointments = pd.DataFrame(appointments_data)
          
          # Substituindo valores nulos por 'NA' nas colunas relevantes
          cols_to_convert_appointments = ['status_label', 'store_name', 'customer_id', 'customer_name', 'customer_telephone', 
                                          'procedure_name', 'procedure_group', 'employee_name', 'createdBy_name', 
                                          'createdBy_createdAt', 'startDate']
          
          df_appointments[cols_to_convert_appointments] = df_appointments[cols_to_convert_appointments].fillna('NA')
          df_appointments[cols_to_convert_appointments] = df_appointments[cols_to_convert_appointments].astype(str)
          
          st.success(f"✅ Total de Agendamentos: {df_appointments.shape[0]} resultados")
      else:
          update_log("❌ Nenhum agendamento encontrado ou ocorreu um erro durante a busca.")

      if bill_charges_data:
          df_bill_charges = pd.DataFrame(bill_charges_data)
          st.success(f"✅ Total de Vendas: {df_bill_charges.shape[0]} resultados")
      else:
          update_log("❌ Nenhuma venda encontrada ou ocorreu um erro durante a busca.")

      # Função principal para tratar e processar os dados
      def process_data(df_leads, df_appointments, df_bill_charges):
          # Extract nested fields from leads data
          df_leads['source'] = df_leads['source'].apply(lambda x: x.get('title') if x else 'NA')
          df_leads['store'] = df_leads['store'].apply(lambda x: x.get('name') if x else 'NA')
          df_leads['status'] = df_leads['status'].apply(lambda x: x.get('label') if x else 'NA')
          df_leads['customer_id'] = df_leads['customer'].apply(lambda x: x.get('id') if x else 'NA')
          df_leads['customer_name'] = df_leads['customer'].apply(lambda x: x.get('name') if x else 'NA')
          
          cols_to_convert = ['createdAt', 'source', 'store', 'status', 'name',
                           'telephone', 'email', 'utmMedium', 'utmCampaign',
                           'utmContent', 'utmSearch', 'utmTerm', 'message',
                           'customer_id', 'customer_name'
                          ]
          
          # First, handle missing or NaN values by replacing them with a placeholder
          df_leads[cols_to_convert] = df_leads[cols_to_convert].fillna('NA')
          # Convert the necessary columns to string
          df_leads[cols_to_convert] = df_leads[cols_to_convert].astype(str)

          update_log("Todos os dados foram baixados. com sucesso")
          update_log("___")
          time.sleep(10)

          update_log("Processando os dados...")
          time.sleep(10)
          update_log("___")

          # Tratando Leads
          update_log("Tratando leads...")
          leads_results_list = []
          for index, lead in df_leads.iterrows():
              formatted_row = {
                  'createdAt': lead['createdAt'],
                  'id': lead['id'],
                  'source': lead['source'],
                  'store': lead['store'],
                  'status': lead['status'],
                  'name': lead['name'],
                  'telephone': lead['telephone'],
                  'email': lead['email'],
                  'utmMedium': lead['utmMedium'],
                  'utmCampaign': lead['utmCampaign'],
                  'utmContent': lead['utmContent'],
                  'utmSearch': lead['utmSearch'],
                  'utmTerm': lead['utmTerm'],
                  'message': lead['message'],
                  'customer_id': lead['customer_id'],
                  'customer_name': lead['customer_name'],
              }
              leads_results_list.append(formatted_row)

          df_leads = pd.DataFrame(leads_results_list)

          # Handle customer_id conversion properly
          df_leads['customer_id'] = df_leads['customer_id'].replace('NA', pd.NA)  # Replace 'NA' string with pandas NA
          df_leads['customer_id'] = pd.to_numeric(df_leads['customer_id'], errors='coerce')  # Convert to numeric, invalid values become NaN
          df_leads['customer_id'] = df_leads['customer_id'].astype('Int64')  # Convert to nullable integer type

          # Tratamentos especiais para leads
          df_leads.loc[df_leads['customer_id'].isna(), 'customer_id'] = pd.NA  # Use pandas NA for missing values
          df_leads = df_leads[~df_leads['store'].isin(["CENTRAL", "HOMA", "PLÁSTICA", "PRAIA GRANDE"])]
          df_leads['is_customer'] = df_leads['customer_id'].notna().map({True: "True", False: "False"})
          df_leads['is_appointment'] = False
          df_leads['is_served'] = False
          df_leads['is_purchase'] = False

          df_leads_is_appointment = df_leads[df_leads['is_customer'] == 'True']

          # Tratando Appointments
          update_log("Tratando appointments...")
          df_appointments['is_assessment'] = df_appointments['procedure_name'].apply(lambda x: True if "AVALIAÇÃO" in x else False)
          df_assessments = df_appointments[(df_appointments['is_assessment']) & (~df_appointments['store_name'].isin(['PLÁSTICA', 'HOMA', 'PRAIA GRANDE']))]

          # Merge Leads with Appointments
          update_log("Mesclando leads com appointments...")

          reduced_assessment_columns = ['status_label', 'store_name', 'customer_id','startDate']
          df_assessments_reduced = df_assessments[reduced_assessment_columns]
          df_assessments_reduced.columns = ['status_apnt', 'store_apnt', 'customer_id','startDate_apnt']
          df_assessments_reduced['customer_id'] = pd.to_numeric(df_assessments_reduced['customer_id'], errors='coerce').astype('Int64')

          # Excluding status "REAGENDADO"
          # SERVED assessments
          # NOT SERVED assessments
          df_assessments_reduced = df_assessments_reduced.loc[df_assessments_reduced['status_apnt'] != "Reagendado"]
          df_assessments_reduced_served = df_assessments_reduced.loc[df_assessments_reduced['status_apnt'] == "Atendido"]
          df_assessments_reduced_not_served = df_assessments_reduced.loc[df_assessments_reduced['status_apnt'] != "Atendido"]

          # prep fields to merge
          df_leads['customer_id'] = pd.to_numeric(df_leads['customer_id'], errors='coerce').astype('Int64')
          df_assessments_reduced['customer_id'] = pd.to_numeric(df_assessments_reduced['customer_id'], errors='coerce').astype('Int64')

          # Merging df_leads + df_assessments_reduced_served (status = ATENDIDO)
          df_leads_apnt_served = pd.merge(df_leads, df_assessments_reduced_served, on='customer_id', how='left')
          df_leads_apnt_served.loc[df_leads_apnt_served['store_apnt'].notnull(), 'is_served'] = True

          # Merging df_leads_apnt_served with df_assessments_reduced_not_served, using suffixes to avoid column duplication
          df_leads_apnt_all = pd.merge(
              df_leads_apnt_served,
              df_assessments_reduced_not_served,
              on='customer_id',
              how='left',
              suffixes=('_served', '_not_served')  # Adding suffixes to avoid column duplication
          )

          ###############
          # Cleaning pt 1
          df_leads_apnt_all['store_apnt'] = "to fill"
          df_leads_apnt_all.loc[df_leads_apnt_all['status_apnt_served'] == "Atendido", 'store_apnt'] = df_leads_apnt_all['store_apnt_served']

          df_leads_apnt_all.loc[
            (df_leads_apnt_all['store_apnt'] == "to fill") &
            (df_leads_apnt_all['store_apnt_not_served'].notna()),
            'store_apnt'
          ] = df_leads_apnt_all['store_apnt_not_served']

          df_leads_apnt_all.loc[
            (df_leads_apnt_all['store_apnt'] == "to fill") &
            (df_leads_apnt_all['store_apnt_served'].notna()),
            'store_apnt'
          ] = df_leads_apnt_all['status_apnt_served']

          ###############
          # Cleaning pt 2
          df_leads_apnt_all['status_apnt'] = "to fill"
          df_leads_apnt_all.loc[df_leads_apnt_all['status_apnt_served'] == "Atendido", 'status_apnt'] = "Atendido"
          df_leads_apnt_all.loc[(df_leads_apnt_all['status_apnt_not_served'].isna()) & (df_leads_apnt_all['status_apnt'] != "Atendido"), 'status_apnt'] = "Não está na agenda"

          # For rows where 'status_apnt' is 'to fill' and 'status_apnt_not_served' is not NaN, update 'status_apnt' with 'status_apnt_not_served'
          df_leads_apnt_all.loc[
              (df_leads_apnt_all['status_apnt'] == "to fill") &
              (df_leads_apnt_all['status_apnt_not_served'].notna()),
              'status_apnt'
          ] = df_leads_apnt_all['status_apnt_not_served']

          df_leads_apnt_all.loc[df_leads_apnt_all['store_apnt'] == 'to fill', 'store_apnt'] = "Não está na agenda"

          # Initialize the 'startDate_apnt' column with a placeholder value
          df_leads_apnt_all['startDate_apnt'] = "to fill"

          # Step 1: If the status is 'Atendido', fill 'startDate_apnt' with 'startDate_apnt_served'
          df_leads_apnt_all.loc[df_leads_apnt_all['status_apnt_served'] == "Atendido", 'startDate_apnt'] = df_leads_apnt_all['startDate_apnt_served']

          # Step 2: For rows where 'startDate_apnt' is 'to fill' and 'startDate_apnt_not_served' is not NaN, update 'startDate_apnt' with 'startDate_apnt_not_served'
          df_leads_apnt_all.loc[
              (df_leads_apnt_all['startDate_apnt'] == "to fill") &
              (df_leads_apnt_all['startDate_apnt_not_served'].notna()),
              'startDate_apnt'
          ] = df_leads_apnt_all['startDate_apnt_not_served']

          # Step 3: For rows where 'startDate_apnt' is 'to fill' and 'startDate_apnt_served' is not NaN, update 'startDate_apnt' with 'startDate_apnt_served'
          df_leads_apnt_all.loc[
              (df_leads_apnt_all['startDate_apnt'] == "to fill") &
              (df_leads_apnt_all['startDate_apnt_served'].notna()),
              'startDate_apnt'
          ] = df_leads_apnt_all['startDate_apnt_served']

          # List of columns to drop (duplicates)
          columns_to_drop = [
              'status_apnt_served', 'store_apnt_served', 'startDate_apnt_served',
              'status_apnt_not_served', 'store_apnt_not_served', 'startDate_apnt_not_served'
          ]

          # Drop the columns from the DataFrame
          df_leads_apnt_all.drop(columns=columns_to_drop, inplace=True)

          # Tratando Bill Charges
          update_log("Tratando bill charges...")
          sales_results_list = []
          for data_row in bill_charges_data:
              # Extract relevant information
              quote_id = data_row["quote"]["id"]
              customer_data = data_row["quote"]["customer"]
              customer_id = customer_data["id"]  # Extracting customer_id
              customer_name = customer_data["name"]
              customer_taxvat = customer_data.get("taxvat", "N/A")  # Use get() to handle missing keys
              customer_email = customer_data["email"]

              store_name = data_row["store"]["name"]
              total_amount = data_row["quote"]["bill"]["total"]
              installments = data_row["quote"]["bill"].get("installmentsQuantity", "N/A")  # Handle missing keys
              paid_at = data_row.get("paidAt", "N/A")
              due_at = data_row.get("dueAt", "N/A")
              is_paid = data_row["isPaid"]
              payment_method = data_row["paymentMethod"]["name"]
              status = data_row["quote"]["status"]

              # Combine all items descriptions in one string
              items = data_row["quote"]["bill"]["items"]
              quote_items = "; ".join([f"{item['description']} (Qty: {item['quantity']}, Amount: {item['amount']})" for item in items])

              # Append the row to the results list
              results_row = [
                  quote_id, customer_id, customer_name, customer_taxvat, customer_email,
                  store_name, total_amount, installments, paid_at, due_at, is_paid,
                  payment_method, status, quote_items
              ]
              sales_results_list.append(results_row)

          # Create the DataFrame with the collected results
          df_bill_charges = pd.DataFrame(sales_results_list, columns=[
              "quote_id", "customer_id", "customer_name", "customer_taxvat", "customer_email",
              "store_name", "total_amount", "installments", "paid_at", "due_at", "is_paid",
              "payment_method", "status", "quote_items"
          ])

          # Merge Leads+Appointments com Bill Charges
          update_log("Mesclando leads e appointments com bill charges...")
          reduced_billcharges_columns = ['customer_id', 'total_amount', 'paid_at', 'quote_items', 'installments']
          df_bill_charges_reduced = df_bill_charges[reduced_billcharges_columns]

          df_leads_appointments_bill_charges = pd.merge(df_leads_apnt_all, df_bill_charges_reduced, on='customer_id', how='left')
          df_leads_appointments_bill_charges.loc[df_leads_appointments_bill_charges['total_amount'] > 0, "is_purchase"] = True
          df_leads_appointments_bill_charges['startDate_apnt'] = df_leads_appointments_bill_charges.get('startDate_apnt', pd.NaT)

          columns_to_keep = ['createdAt', 'id', 'source', 'store', 'message', 'utmMedium', 'utmCampaign', 'utmContent', 'utmSearch', 'utmTerm',
                            'customer_id', 'is_customer', 'is_appointment', 'is_served', 'is_purchase',
                            'startDate_apnt', 'status_apnt', 'store_apnt', 'total_amount', 'paid_at', 'quote_items', 'installments']

          df_mkt = df_leads_appointments_bill_charges[columns_to_keep]
          df_mkt.loc[df_mkt['store_apnt'].notnull(), 'is_appointment'] = True
          df_mkt.loc[df_mkt['status_apnt'] == "Atendido", 'is_served'] = True


          # Tratamentos finais
          df_mkt['createdAt'] = pd.to_datetime(df_mkt['createdAt']).dt.date
          df_mkt['startDate_apnt'] = pd.to_datetime(df_mkt['startDate_apnt'], errors='coerce').dt.date
              # Tratamentos finais - conversão e limpeza de dados
          df_mkt['paid_at'] = pd.to_datetime(df_mkt['paid_at'], errors='coerce').dt.date

          # Remover ".0" da coluna "total_amount" e dividir por 100 para representar valores corretos
          df_mkt['total_amount'] = df_mkt['total_amount'].astype(str).str.replace('.0', '', regex=False)
          df_mkt['installments'] = df_mkt['installments'].astype(str).str.replace('.0', '', regex=False)
          df_mkt['total_amount'] = df_mkt['total_amount'].astype(float) / 100

          # Remover duplicatas com base na coluna 'id'
          df_mkt.drop_duplicates(subset='id', keep='first', inplace=True)

          # Aplicar categoria aos leads com base em palavras-chave
          update_log("Aplicando categorias aos leads...")

          # Dicionário de mapeamento para categorização
          category_mapping = {
              'Preenchimento': 'Preenchimento',
              'Botox': 'Botox',
              'Ultraformer': 'Ultraformer',
              'Enzimas': 'Enzimas',
              'Lavieen': 'Lavieen',
              'Sculptra': 'Bioestimulador',
              'Bioestimulador': 'Bioestimulador',
              'Institucional': 'Institucional',
              'Crio': 'Crio',
              'Limpeza': 'Limpeza',
              'olheiras': 'Preenchimento',
              'prolipo': 'Enzimas',
              'Prolipo': 'Enzimas',
              'rugas': 'Botox'
          }

          # Função para categorizar com base nas palavras-chave
          def categorize(text):
              for keyword, category in category_mapping.items():
                  if pd.notna(text) and keyword.lower() in text.lower():
                      return category
              return 'Indefinido'

          # Aplicar a categorização na coluna 'utmContent' e depois 'message' para os 'Indefinidos'
          df_mkt['category'] = df_mkt['utmContent'].apply(categorize)
          df_mkt.loc[df_mkt['category'] == 'Indefinido', 'category'] = df_mkt['message'].apply(categorize)

          # Tratamento extra para leads específicos
          df_mkt.loc[(df_mkt['source'] == 'Indique e Multiplique') & (df_mkt['category'] == 'Indefinido'), 'category'] = 'Cortesia Indique'
          df_mkt.loc[(df_mkt['source'] == 'CRM BÔNUS') & (df_mkt['category'] == 'Indefinido'), 'category'] = 'Cortesia CRM Bônus'
          df_mkt.loc[(df_mkt['message'] == 'Lead Pop Up de Saída. Ganhou Peeling Diamante.') & (df_mkt['category'] == 'Indefinido'), 'category'] = 'Cortesia PopUpSaida Peeling_D'
          df_mkt.loc[(df_mkt['message'] == 'Lead Pop Up de Saída. Ganhou Massagem Modeladora.') & (df_mkt['category'] == 'Indefinido'), 'category'] = 'Cortesia PopUpSaida Mass_Mod'
          df_mkt.loc[(df_mkt['message'] == 'Lead salvo pelo modal de WhatsApp da Isa') & (df_mkt['category'] == 'Indefinido'), 'category'] = 'Quer Falar no Whatsapp'

          # Dados finais prontos
          update_log("Processamento concluído com sucesso.")
          return df_mkt

      # Exemplo de chamada da função de processamento, com logs sendo exibidos em tempo real
      df_mkt_result = process_data(df_leads, df_appointments, df_bill_charges)
      st.write(df_mkt_result)

      try:
        update_log("Salvando dados no Google Sheets...")
        # Google Sheets and Colab setup
        import gspread
        from google.oauth2.service_account import Credentials
        from gspread_dataframe import set_with_dataframe
        import json

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        # Assemble credentials from Streamlit secrets
        creds_dict = {
            "type": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["type"],
            "project_id": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["project_id"],
            "private_key_id": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["private_key_id"],
            "private_key": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["private_key"],
            "client_email": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["client_email"],
            "client_id": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["client_id"],
            "auth_uri": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["auth_uri"],
            "token_uri": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["GOOGLE_SERVICE_ACCOUNT"]["client_x509_cert_url"]
        }

        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)

        # Interact with Google Sheets
        url_to_paste = 'https://docs.google.com/spreadsheets/d/1Z5TaQavOU5GaJp96X_cR_TA-gw6ZTOjV4hYTqBQwwCc/'
        spreadsheet = gc.open_by_url(url_to_paste)
        sheet_data = spreadsheet.worksheet('data')

        # Clear the sheet and write the DataFrame
        sheet_data.clear()
        set_with_dataframe(sheet_data, df_mkt_result)

      except Exception as e:
        st.error(f"Failed to save data to Google Sheets: {e}")

if __name__ == "__main__":
    run()