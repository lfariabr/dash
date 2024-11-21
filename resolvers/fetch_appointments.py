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