import os
import pickle
import gspread
import pandas as pd

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# Google scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


# -------------------------------
# Auth Helper
# -------------------------------

def get_gspread_client():

    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "oauth_credentials.json",
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as f:
            pickle.dump(creds, f)

    return gspread.authorize(creds)


# -------------------------------
# Data Cleaning
# -------------------------------

def flatten_value(val):
    """
    Convert complex objects into readable strings
    """

    if val is None:
        return ""

    # If list (line items)
    if isinstance(val, list):

        parts = []

        for item in val:

            if isinstance(item, dict):

                product = item.get("product", "")
                amount = item.get("amount", "")

                parts.append(f"{product} ({amount})")

            else:
                parts.append(str(item))

        return ", ".join(parts)

    # If dict
    if isinstance(val, dict):
        return str(val)

    # If NaN
    if pd.isna(val):
        return ""

    # Normal value
    return str(val)


def clean_dataframe_for_sheets(df):

    df = df.copy()

    for col in df.columns:
        df[col] = df[col].apply(flatten_value)

    return df


# -------------------------------
# Export Function
# -------------------------------

def export_to_sheets(df, sheet_name="Invoice Extraction"):

    client = get_gspread_client()

    # Clean data first
    clean_df = clean_dataframe_for_sheets(df)

    # Create sheet
    sheet = client.create(sheet_name)

    worksheet = sheet.sheet1

    # Prepare rows
    rows = [
        clean_df.columns.tolist()
    ] + clean_df.values.tolist()

    # Upload
    worksheet.update(rows)

    return sheet.url
