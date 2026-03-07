"""
Append chatter row to Google Sheet.
Columns: Name, Lastname, Replies, Status, Payment method, BTC address, wise name, Wise email, currency
Requires: GOOGLE_SHEET_ID, GOOGLE_SERVICE_ACCOUNT_JSON in .env
Optional: GOOGLE_SHEET_TAB_NAME (default "Sheet1")
"""

import os
import json
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def append_chatter(row: dict) -> None:
    """
    Append one row to the configured Google Sheet.
    row: dict with keys: name, lastname, replies, status, payment_method,
         btc_address (optional), wise_name (optional), wise_email (optional), currency (optional)
    """
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    credentials_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    tab_name = os.getenv("GOOGLE_SHEET_TAB_NAME", "Sheet1")

    if not sheet_id or not credentials_json:
        raise ValueError(
            "Missing Google Sheet config. Set GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON in .env"
        )

    if isinstance(credentials_json, str):
        credentials_dict = json.loads(credentials_json)
    else:
        credentials_dict = credentials_json

    creds = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    body = {
        "values": [[
            (row.get("name") or ""),
            (row.get("lastname") or ""),
            (row.get("replies") or ""),
            (row.get("status") or ""),
            (row.get("payment_method") or ""),
            (row.get("btc_address") or ""),
            (row.get("wise_name") or ""),
            (row.get("wise_email") or ""),
            (row.get("currency") or ""),
        ]]
    }
    range_name = f"{tab_name}!A:I"
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()
    logger.info("Appended chatter row to Google Sheet")
