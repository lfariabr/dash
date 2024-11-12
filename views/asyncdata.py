
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
    st.write(f"### Start Date: {start_date_str}")
    st.write(f"### End Date: {end_date_str}")
    st.write(f"### Extended End Date: {extended_end_date_str}")

    # Update the log area with any other messages if needed
    log_area.text("Os dados foram recebidos e processados!")

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
        while True:  # Infinite retry loop
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
              print(f"Failed to fetch leads on page {current_page}. Retrying...")
              continue

          leads_data = data['data']['fetchLeads']['data']
          all_leads.extend(leads_data)

          meta = data['data']['fetchLeads']['meta']
          last_page = meta['lastPage']

          log_area.text(f"Querying Leads - Page: {current_page}/{last_page} - startDate: {start_date} - endDate: {end_date}")

          if current_page >= last_page:
              break

          current_page += 1
          await asyncio.sleep(5)  # Small delay to avoid hitting API complaints

      return all_leads

    async def fetch_all_data(start_date, end_date, extended_end_date, token):
        async with aiohttp.ClientSession() as session:
            leads_task = fetch_all_leads(session, start_date, end_date, token)
            leads_data = await asyncio.gather(leads_task)

            return leads_data

    # Wrapper function to run async functions
    def run_fetch_all(start_date, end_date, extended_end_date, token):
        return asyncio.run(fetch_all_data(start_date, end_date, extended_end_date, token))

    start_time = time.time()
    # Fetch all data
    leads_data = run_fetch_all(start_date_str, end_date_str, extended_end_date_str, token)
    end_time = time.time()

    # Convert to DataFrame and print results
    if leads_data and leads_data[0]:
        df_leads = pd.DataFrame(leads_data[0])
        st.write(f"Leads DataFrame: {df_leads.shape[0]} rows")
        st.write(df_leads)
    else:
        st.write("No data fetched or an error occurred during data fetching.")

    st.write(f"Total time taken: {end_time - start_time:.2f} seconds")
