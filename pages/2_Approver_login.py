import streamlit as st
from auth_utils import (
    is_allowed_domain, generate_and_store_otp, verify_otp, get_roles
)
from email_utils import send_otp_email

st.set_page_config(page_title="Approver Login", layout="wide")

with open("styles/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none; }
.block-container { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# Home button at the far LEFT edge
hl, hr = st.columns([1, 8])
with hl:
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("Home.py")

# Title + fields CENTERED on the page
left, center, right = st.columns([2, 3, 2])

with center:
    st.title("Approver Login")
    st.caption("Log in with your company email. We'll send a one-time code to verify.")

    # ── STEP 1: request OTP ──
    if not st.session_state.get("otp_email"):
        email = st.text_input("Company Email", placeholder="you@teampureplay.com").strip()
        if st.button("Send OTP", use_container_width=True):
            if not email:
                st.error("Please enter your email.")
            elif not is_allowed_domain(email):
                st.error("Please use your company email address.")
            else:
                try:
                    code = generate_and_store_otp(email)
                    send_otp_email(email, code)
                    st.session_state.otp_email = email
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not send OTP: {e}")

    # ── STEP 2: verify OTP ──
    else:
        st.success(f"Code sent to {st.session_state.otp_email} (valid 5 minutes).")
        otp_input = st.text_input("Enter the 6-digit code", max_chars=6, placeholder="******")

        if st.button("Verify & Login", use_container_width=True):
            ok, msg = verify_otp(st.session_state.otp_email, otp_input)
            if ok:
                user_email = st.session_state.otp_email
                roles = get_roles(user_email)
                st.session_state.logged_in = True
                st.session_state.user_email = user_email
                st.session_state.roles = roles          # every role they hold
                st.session_state.role = roles[0]        # the one currently in use
                st.session_state.pop("otp_email", None)
                st.switch_page("pages/3_Approver_Dashboard.py")
            else:
                st.error(msg)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Resend code", use_container_width=True):
                try:
                    code = generate_and_store_otp(st.session_state.otp_email)
                    send_otp_email(st.session_state.otp_email, code)
                    st.info("A new code has been sent.")
                except Exception as e:
                    st.error(f"Could not resend: {e}")
        with c2:
            if st.button("Change email", use_container_width=True):
                st.session_state.pop("otp_email", None)
                st.rerun()