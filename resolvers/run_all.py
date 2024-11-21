def run_fetch_all(start_date, end_date, extended_end_date, token):
          return asyncio.run(fetch_all_data(start_date, end_date, extended_end_date, token))