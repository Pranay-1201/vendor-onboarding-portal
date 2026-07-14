import json
import os
import time
import random
import streamlit as st

ROLES_FILE = "roles.json"
OTP_TTL_SECONDS = 300  # OTP valid for 5 minutes


def load_roles():
    if not os.path.exists(ROLES_FILE):
        return {"allowed_domain": "", "finance": [], "admin": []}
    with open(ROLES_FILE, "r") as f:
        return json.load(f)


def is_allowed_domain(email):
    roles = load_roles()
    domain = (roles.get("allowed_domain") or "").strip().lower()
    if not domain:
        return True  # no restriction configured
    return email.strip().lower().endswith("@" + domain)


def get_roles(email):
    """
    Return EVERY role this person holds, e.g. ["admin", "finance"].
    Everyone on the domain is at least an approver, so that is always included.
    """
    roles = load_roles()
    e = email.strip().lower()
    held = []

    if e in [a.lower() for a in roles.get("admin", [])]:
        held.append("admin")
    if e in [f.lower() for f in roles.get("finance", [])]:
        held.append("finance")

    # Anyone with a company email can review what is assigned to them.
    held.append("approver")

    return held


def get_role(email):
    """The person's primary (highest) role. Kept for backwards compatibility."""
    return get_roles(email)[0]


def get_finance_emails():
    return load_roles().get("finance", [])


# ── OTP store (survives Streamlit reruns) ──
@st.cache_resource
def _otp_store():
    return {}   # {email: (code, expiry_timestamp)}


def generate_and_store_otp(email):
    code = f"{random.randint(0, 999999):06d}"
    _otp_store()[email.strip().lower()] = (code, time.time() + OTP_TTL_SECONDS)
    return code


def verify_otp(email, code):
    """Return (True, msg) if valid, else (False, msg)."""
    store = _otp_store()
    key = email.strip().lower()
    entry = store.get(key)
    if not entry:
        return False, "No OTP requested for this email. Please request a new code."
    saved_code, expiry = entry
    if time.time() > expiry:
        store.pop(key, None)
        return False, "OTP expired. Please request a new code."
    if code.strip() != saved_code:
        return False, "Incorrect OTP."
    store.pop(key, None)  # one-time use
    return True, "Verified."