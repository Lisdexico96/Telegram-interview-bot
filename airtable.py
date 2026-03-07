"""
Append chatter record to Airtable.
Field names: Name, Lastname, Replies, Status, Payment method, BTC address, wise name, Wise email, currency
Requires: AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME in .env
"""

import os
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

AIRTABLE_API_URL = "https://api.airtable.com/v0"


def append_chatter(row: dict) -> None:
    """
    Create one record in the configured Airtable table.
    row: dict with keys: name, lastname, replies, status, payment_method,
         btc_address (optional), wise_name (optional), wise_email (optional), currency (optional)
    """
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_name = os.getenv("AIRTABLE_TABLE_NAME", "Chatters")

    if not api_key or not base_id:
        raise ValueError(
            "Missing Airtable config. Set AIRTABLE_API_KEY and AIRTABLE_BASE_ID in .env"
        )

    # Airtable field names must match exactly
    fields = {
        "Name": (row.get("name") or ""),
        "Lastname": (row.get("lastname") or ""),
        "Replies": (row.get("replies") or ""),
        "Status": (row.get("status") or ""),
        "Payment method": (row.get("payment_method") or ""),
        "BTC address": (row.get("btc_address") or ""),
        "wise name": (row.get("wise_name") or ""),
        "Wise email": (row.get("wise_email") or ""),
        "currency": (row.get("currency") or ""),
    }

    table_id_encoded = urllib.request.quote(table_name, safe="")
    url = f"{AIRTABLE_API_URL}/{base_id}/{table_id_encoded}"
    data = json.dumps({"fields": fields}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status not in (200, 201):
                body = resp.read().decode()
                raise RuntimeError(f"Airtable API error {resp.status}: {body}")
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        logger.exception("Airtable HTTP error %s: %s", e.code, body)
        raise RuntimeError(f"Airtable error {e.code}: {body}") from e
    logger.info("Appended chatter record to Airtable")
