"""
Push interview results to a ClickUp task matched by Telegram handle.
Requires: CLICKUP_API_KEY, CLICKUP_LIST_ID in .env
"""
from __future__ import annotations

import os
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

CLICKUP_API_URL = "https://api.clickup.com/api/v2"

FIELD_TELEGRAM  = "Telegram @"
FIELD_DECISION  = "Hiring Decision"
FIELD_SCORE     = "Hiring Score"
FIELD_RESPONSES = "Responses From Test"


def _request(url: str, api_key: str, method: str = "GET", data: dict = None) -> dict:
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Authorization": api_key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        raise RuntimeError(f"ClickUp API error {e.code}: {body}") from e


def _get_fields(api_key: str, list_id: str) -> dict:
    """Returns {field_name: {id, type, options: {option_name: option_id}}}"""
    result = _request(f"{CLICKUP_API_URL}/list/{list_id}/field", api_key)
    fields = {}
    for f in result.get("fields", []):
        options = {
            opt["name"].upper(): opt["id"]
            for opt in f.get("type_config", {}).get("options", [])
        }
        fields[f["name"]] = {"id": f["id"], "type": f["type"], "options": options}
    return fields


def _find_task(api_key: str, list_id: str, telegram_handle: str, telegram_field_id: str) -> str | None:
    """Search list pages for a task whose Telegram @ field matches. Returns task_id or None."""
    handle = telegram_handle.lstrip("@").lower()
    page = 0
    while True:
        result = _request(
            f"{CLICKUP_API_URL}/list/{list_id}/task?page={page}&include_closed=true",
            api_key,
        )
        tasks = result.get("tasks", [])
        if not tasks:
            break
        for task in tasks:
            for field in task.get("custom_fields", []):
                if field.get("id") == telegram_field_id:
                    value = (field.get("value") or "").lstrip("@").lower()
                    if value == handle:
                        return task["id"]
        if result.get("last_page"):
            break
        page += 1
    return None


def _update_field(api_key: str, task_id: str, field_id: str, value) -> None:
    _request(f"{CLICKUP_API_URL}/task/{task_id}/field/{field_id}", api_key, method="POST", data={"value": value})


def push_interview_results(telegram_username: str, decision: str, score: int, responses: str) -> None:
    """
    Find the ClickUp task for this candidate by Telegram handle and update it
    with the interview decision, score, and responses.
    """
    api_key = os.getenv("CLICKUP_API_KEY")
    list_id = os.getenv("CLICKUP_LIST_ID")

    if not api_key or not list_id:
        raise ValueError("Missing CLICKUP_API_KEY or CLICKUP_LIST_ID in .env")

    fields = _get_fields(api_key, list_id)

    for name in (FIELD_TELEGRAM, FIELD_DECISION, FIELD_SCORE, FIELD_RESPONSES):
        if name not in fields:
            raise ValueError(f"ClickUp field not found: '{name}' — check field names match exactly")

    task_id = _find_task(api_key, list_id, telegram_username, fields[FIELD_TELEGRAM]["id"])
    if not task_id:
        raise LookupError(f"No ClickUp task found for Telegram handle: @{telegram_username}")

    # Decision is a single select — must pass the option ID, not the string
    decision_options = fields[FIELD_DECISION]["options"]
    decision_option_id = decision_options.get(decision.upper())
    if not decision_option_id:
        raise ValueError(f"Decision option '{decision}' not found in ClickUp field. Available: {list(decision_options.keys())}")

    _update_field(api_key, task_id, fields[FIELD_DECISION]["id"], decision_option_id)
    _update_field(api_key, task_id, fields[FIELD_SCORE]["id"], score)
    _update_field(api_key, task_id, fields[FIELD_RESPONSES]["id"], responses)

    logger.info(f"ClickUp task {task_id} updated for @{telegram_username}: {decision}, score={score}")
