"""Normalize and hash customer data the way Meta's matching expects (lowercase, trimmed, SHA-256)."""
import hashlib
import re


def sha256(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest() if value else None


def email(raw):
    v = (raw or "").strip().lower()
    return sha256(v) if "@" in v else None


def phone(raw, default_country="1"):
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 10:
        digits = default_country + digits
    return sha256(digits) if len(digits) >= 11 else None


def name(raw):
    v = re.sub(r"[^a-z]", "", (raw or "").strip().lower())
    return sha256(v) if v else None


def zip_code(raw):
    v = (raw or "").strip().lower()[:5]
    return sha256(v) if v else None
