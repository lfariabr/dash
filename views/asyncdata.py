
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import asyncio
import aiohttp
import nest_asyncio
import time

nest_asyncio.apply()

# Define the Streamlit page
st.title("Leads Self Service 3.0")

# Create form for user inputs
with st.form("input_form"):
    start_date = st.date_input("Data inicial", value=datetime.today().replace(day=5))
    end_date = st.date_input("Data final", value=datetime.today() - timedelta(days=1))
    extended_end_date = st.date_input("Data agendamentos", value=datetime.today() + timedelta(days=15))
    
    token = st.text_input("Senha", type="password")

    # Submit button for the form
    submitted = st.form_submit_button("Pegar os Dados")

# Placeholder for log area
log_area = st.empty()  # This will be used to display real-time logs

# If the form is submitted, run the fetching logic
if submitted:
    # Format dates to match the required format
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    extended_end_date_str = extended_end_date.strftime('%Y-%m-%d')

    # Print formatted dates directly on the screen (outside log area)
    st.write(f"Data inicial: {start_date_str}")
    st.write(f"Data final: {end_date_str}")
    st.write(f"Data agendamentos: {extended_end_date_str}")

    # Update the log area with initial message
    log_area.text("Aguarde, os dados estão sendo processados...")

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
                            log_area.text(f"GraphQL errors: {data['errors']}")
                            return None
                        return data
                    else:
                        log_area.text(f"Request failed with status {response.status}")
            except aiohttp.ClientError as e:
                log_area.text(f"Request exception: {e}")

            # Exponential backoff and retry
            attempt += 1
            wait_time = min(5 * 2 ** attempt, 30)
            log_area.text(f"Retrying in {wait_time} seconds (attempt {attempt})...")
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
                    'perPage': 200,
                },
            }

            data = await fetch_graphql(session, 'https://open-api.eprocorpo.com.br/graphql', query, variables, token)

            if data is None:
                log_area.text(f"Failed to fetch leads on page {current_page}. Retrying...")
                continue

            leads_data = data['data']['fetchLeads']['data']
            all_leads.extend(leads_data)

            meta = data['data']['fetchLeads']['meta']
            last_page = meta['lastPage']

            log_area.text(f"Querying Leads - Page: {current_page}/{last_page} - startDate: {start_date} - endDate: {end_date}")

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
                    'perPage': 200,
                },
            }

            data = await fetch_graphql(session, 'https://open-api.eprocorpo.com.br/graphql', query, variables, token)

            if data is None:
                log_area.text(f"Failed to fetch appointments on page {current_page}. Retrying...")
                continue

            appointments_data = [
                {
                    "id": row['id'],
                    "status_label": row.get('status', {}).get('label', 'N/A'),
                    "store_name": row.get('store', {}).get('name', 'N/A'),
                    "customer_id": row.get('customer', {}).get('id', 'N/A'),
                    "customer_name": row.get('customer', {}).get('name', 'N/A'),
                    "customer_telephone": row.get('customer', {}).get('telephones', [{}])[0].get('number', 'N/A'),
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

            log_area.text(f"Querying Appointments - Page: {current_page}/{last_page} - startDate: {start_date} - endDate: {extended_end_date}")

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
                    'perPage': 200,
                }
            }

            data = await fetch_graphql(session, 'https://open-api.eprocorpo.com.br/graphql', query, variables, token)

            if data is None:
                log_area.text(f"Failed to fetch bill charges on page {current_page}. Retrying...")
                continue

            bill_charges_data = data['data']['fetchBillCharges']['data']
            all_bill_charges.extend(bill_charges_data)

            meta = data['data']['fetchBillCharges']['meta']
            log_area.text(f"Querying Bill Charges - Page: {current_page}/{meta['lastPage']} - startDate: {start_date} - endDate: {end_date}")
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
        st.write(f"Leads DataFrame: {df_leads.shape[0]} rows")
        st.write(df_leads)
    else:
        log_area.text("No leads data fetched or an error occurred during the fetch.")

    if appointments_data:
        df_appointments = pd.DataFrame(appointments_data)
        st.write(f"Appointments DataFrame: {df_appointments.shape[0]} rows")
        st.write(df_appointments)
    else:
        log_area.text("No appointments data fetched or an error occurred during the fetch.")

    if bill_charges_data:
        df_bill_charges = pd.DataFrame(bill_charges_data)
        st.write(f"Bill Charges DataFrame: {df_bill_charges.shape[0]} rows")
        st.write(df_bill_charges)
    else:
        log_area.text("No bill charges data fetched or an error occurred during the fetch.")
