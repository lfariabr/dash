async def fetch_all_data(start_date, end_date, extended_end_date, token):
          async with aiohttp.ClientSession() as session:
              leads_task = fetch_all_leads(session, start_date, end_date, token)  # Para leads, usa end_date original
              appointments_task = fetch_appointments(session, start_date, extended_end_date, token)  # Usa extended_end_date para appointments
              bill_charges_task = fetch_bill_charges(session, start_date, end_date, token)  # Para bill charges, usa end_date original

              leads_data, appointments_data, bill_charges_data = await asyncio.gather(
                  leads_task, appointments_task, bill_charges_task
              )

              return leads_data, appointments_data, bill_charges_data