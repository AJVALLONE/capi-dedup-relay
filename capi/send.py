"""Send events to the Conversions API. DRY_RUN=1 (default) prints instead of sending."""
import json
import os
import urllib.request

GRAPH = "https://graph.facebook.com/v21.0/{pixel_id}/events"


def send(events, pixel_id=None, token=None, test_event_code=None, dry_run=None):
    pixel_id = pixel_id or os.environ.get("META_PIXEL_ID")
    token = token or os.environ.get("META_CAPI_TOKEN")
    dry_run = os.environ.get("DRY_RUN", "1") == "1" if dry_run is None else dry_run
    body = {"data": events}
    if test_event_code or os.environ.get("META_TEST_EVENT_CODE"):
        body["test_event_code"] = test_event_code or os.environ["META_TEST_EVENT_CODE"]
    if dry_run or not (pixel_id and token):
        print(json.dumps(body, indent=2))
        return {"dry_run": True, "events": len(events)}
    req = urllib.request.Request(GRAPH.format(pixel_id=pixel_id) + f"?access_token={token}",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)
