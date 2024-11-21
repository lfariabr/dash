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