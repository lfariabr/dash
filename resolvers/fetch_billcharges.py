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