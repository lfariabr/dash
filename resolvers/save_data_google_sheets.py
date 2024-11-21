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
