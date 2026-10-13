"""Small data-contract helpers for the Smartly coursework API.

The Flask prototype currently keeps resource records as dictionaries for readability;
these helpers define the request validation contract in one reusable place.
"""
from datetime import datetime


def validate_booking_payload(data, rooms):
    errors = []
    if not isinstance(data, dict):
        return [{"field": "body", "reason": "must be a JSON object"}]
    if not isinstance(data.get("roomId"), int) or isinstance(data.get("roomId"), bool):
        errors.append({"field": "roomId", "reason": "must be an integer"})
    elif data["roomId"] not in rooms:
        errors.append({"field": "roomId", "reason": "does not identify an existing room"})
    if not isinstance(data.get("date"), str) or not data["date"].strip():
        errors.append({"field": "date", "reason": "is required as YYYY-MM-DD"})
    else:
        try:
            datetime.strptime(data["date"], "%Y-%m-%d")
        except ValueError:
            errors.append({"field": "date", "reason": "must use YYYY-MM-DD"})
    for field in ("startTime", "endTime", "purpose"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            errors.append({"field": field, "reason": "is required"})
    if isinstance(data.get("startTime"), str) and isinstance(data.get("endTime"), str):
        start, end = data["startTime"], data["endTime"]
        if start and end and end <= start:
            errors.append({"field": "endTime", "reason": "must be later than startTime"})
    return errors
