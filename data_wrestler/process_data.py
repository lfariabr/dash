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