"""Build Conversions API events.

Deduplication: the browser pixel and the server send the same event_name + event_id.
Meta keeps one and discards the other, so you get the server's reliability without
double-counting.

Sensitive mode (for health, finance, or other regulated funnels): only allowlisted
custom_data fields leave your server, URLs are reduced to scheme + host, and event names
can be mapped to neutral ones so nothing about a person's condition reaches the ad platform.
"""
import time
from urllib.parse import urlsplit

from . import normalize

SAFE_CUSTOM_FIELDS = {"value", "currency", "content_category"}
NEUTRAL_EVENT_NAMES = {"BookConsult": "Schedule", "CompleteIntake": "Lead", "StartTreatment": "Purchase"}


def strip_url(url):
    parts = urlsplit(url or "")
    return f"{parts.scheme}://{parts.netloc}/" if parts.netloc else None


def build_event(raw, sensitive=False, now=None):
    if not raw.get("event_id"):
        raise ValueError("event_id is required for deduplication with the browser pixel")
    name = raw["event_name"]
    if sensitive:
        name = NEUTRAL_EVENT_NAMES.get(name, name)

    user = {
        "em": [normalize.email(raw.get("email"))],
        "ph": [normalize.phone(raw.get("phone"))],
        "fn": [normalize.name(raw.get("first_name"))],
        "ln": [normalize.name(raw.get("last_name"))],
        "zp": [normalize.zip_code(raw.get("zip"))],
        "fbp": raw.get("fbp"),
        "fbc": raw.get("fbc"),
        "client_ip_address": raw.get("ip"),
        "client_user_agent": raw.get("user_agent"),
    }
    user = {k: v for k, v in user.items() if v and v != [None]}

    custom = raw.get("custom_data") or {}
    if sensitive:
        custom = {k: v for k, v in custom.items() if k in SAFE_CUSTOM_FIELDS}

    event = {
        "event_name": name,
        "event_time": int(now or time.time()),
        "event_id": raw["event_id"],
        "action_source": "website",
        "event_source_url": strip_url(raw.get("url")) if sensitive else raw.get("url"),
        "user_data": user,
    }
    if custom:
        event["custom_data"] = custom
    return {k: v for k, v in event.items() if v is not None}
