# CAPI Dedup Relay

Send conversions to Meta from your server **and** the browser without double-counting, and keep sensitive data out of the ad platform. This is the pattern behind clean conversion signal on funnels where the browser pixel alone is unreliable: fast redirects, ad blockers, iOS restrictions, and regulated categories like health and finance.

Companion to [meta-pixel-race-condition](https://github.com/AJVALLONE/meta-pixel-race-condition), which diagnoses why the browser pixel silently misses events on fast-redirecting funnel pages. On a funnel using this approach, Meta-reported leads matched CRM records within 3%.

![deps](https://img.shields.io/badge/dependencies-zero-brightgreen) ![python](https://img.shields.io/badge/python-3.10%2B-blue)

## How deduplication works

```
user action
   ├── browser: fbq('track', 'Schedule', {}, {eventID: 'Schedule_1717_ab12'})   may be blocked or too late
   └── server:  POST /capi  {event_name: 'Schedule', event_id: 'Schedule_1717_ab12'}   reliable
                         │
                         ▼
          Meta keeps one event per (event_name, event_id) and discards the duplicate
```

The browser snippet in [`browser/pixel-with-event-id.html`](browser/pixel-with-event-id.html) generates one `event_id` per action, fires the pixel with it, and sends the same ID to your server with `fetch(..., {keepalive: true})` so the request survives a page redirect.

## What the server does

- **Normalizes and hashes customer data** to Meta's spec: trimmed lowercase email, phone with country code, letters-only names, 5-digit ZIP, all SHA-256. Invalid values are dropped rather than sent malformed.
- **Passes through `_fbp` / `_fbc` cookies**, IP, and user agent for match quality.
- **Requires `event_id`**, so you can't accidentally ship an event that won't dedupe.

## Sensitive mode (health, finance, regulated funnels)

Ad platforms restrict what health and financial advertisers may share. `build_event(raw, sensitive=True)`:

| Risk | What sensitive mode does |
| --- | --- |
| URL reveals a condition (`/booking?condition=fatigue`) | Sends only `https://example.com/` |
| Event name reveals a treatment (`StartTreatment`) | Maps to a neutral standard event (`Purchase`) |
| Custom fields carry health details (`symptom`) | Only allowlisted fields (`value`, `currency`, `content_category`) leave the server |

Pair it with the rule from the race-condition repo: the pixel runs on marketing pages only, never on clinical, intake, or scheduling surfaces. This is an engineering pattern, not legal advice; have your compliance team review your specific setup.

## Run it

```bash
git clone https://github.com/AJVALLONE/capi-dedup-relay
cd capi-dedup-relay
python -m unittest discover -s tests -v     # 6 tests: hashing, dedup requirement, sensitive mode
```

```python
from capi.payload import build_event
from capi.send import send

event = build_event({"event_name": "BookConsult", "event_id": "Schedule_1717_ab12",
                     "email": "dana@gmail.com", "phone": "(757) 555-0142",
                     "url": "https://example.com/booking?condition=fatigue"}, sensitive=True)
send([event])   # DRY_RUN=1 by default: prints the payload. Set META_PIXEL_ID + META_CAPI_TOKEN to send.
```

Use `META_TEST_EVENT_CODE` to watch events arrive in Events Manager's Test Events tab before going live, and confirm the "Deduplicated" status appears for browser + server pairs.

## Author

Anthony Vallone, growth leader who builds his own tracking and tooling. [LinkedIn](https://linkedin.com/in/ajvallone) · [Portfolio](https://anthonyvallone.netlify.app)
