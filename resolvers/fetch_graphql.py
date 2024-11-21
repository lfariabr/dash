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