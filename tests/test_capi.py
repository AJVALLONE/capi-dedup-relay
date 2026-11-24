import hashlib
import unittest

from capi import normalize, payload

RAW = {"event_name": "BookConsult", "event_id": "Schedule_123", "email": "  Dana@Gmail.com ",
       "phone": "(757) 555-0142", "first_name": "Dana", "zip": "23320-1234",
       "url": "https://example.com/booking?condition=fatigue&utm_source=meta",
       "custom_data": {"value": 0, "currency": "USD", "symptom": "fatigue"}}


class NormalizeTest(unittest.TestCase):
    def test_email_is_trimmed_lowercased_hashed(self):
        self.assertEqual(normalize.email("  Dana@Gmail.com "), hashlib.sha256(b"dana@gmail.com").hexdigest())

    def test_phone_gets_country_code(self):
        self.assertEqual(normalize.phone("(757) 555-0142"), hashlib.sha256(b"17575550142").hexdigest())

    def test_invalid_values_dropped(self):
        self.assertIsNone(normalize.email("not-an-email"))
        self.assertIsNone(normalize.phone("555"))


class PayloadTest(unittest.TestCase):
    def test_event_id_required(self):
        with self.assertRaises(ValueError):
            payload.build_event({"event_name": "Lead"})

    def test_standard_mode_keeps_url_and_custom_data(self):
        e = payload.build_event(RAW, now=1)
        self.assertEqual(e["event_id"], "Schedule_123")
        self.assertIn("condition=fatigue", e["event_source_url"])
        self.assertIn("symptom", e["custom_data"])

    def test_sensitive_mode_strips_health_signals(self):
        e = payload.build_event(RAW, sensitive=True, now=1)
        self.assertEqual(e["event_name"], "Schedule")              # neutral event name
        self.assertEqual(e["event_source_url"], "https://example.com/")  # no path or query
        self.assertNotIn("symptom", e.get("custom_data", {}))      # allowlist only
        self.assertTrue(all(len(v[0]) == 64 for k, v in e["user_data"].items() if k in {"em", "ph", "fn", "zp"}))


if __name__ == "__main__":
    unittest.main()
