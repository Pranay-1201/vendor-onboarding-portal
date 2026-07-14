import streamlit as st
import pandas as pd
import os
import base64

from gemini_helper import analyze_vendor
from auth_utils import get_finance_emails
from db_utils import get_all_vendors, update_vendor, list_documents, get_document_bytes, get_ai_report, save_ai_report
from email_utils import (
    send_vendor_status_email, send_accepted_email, send_code_created_email,
    send_finance_decision_email,
)

with open("styles/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="Approver Dashboard", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("logged_in", False):
    st.switch_page("pages/2_Approver_Login.py")

user_email = st.session_state.get("user_email", "")

# Every role this person holds. Older sessions may only have "role".
held_roles = st.session_state.get("roles")
if not held_roles:
    held_roles = [st.session_state.get("role", "approver")]
    st.session_state.roles = held_roles

# The role currently in use — must be one they actually hold.
role = st.session_state.get("role", held_roles[0])
if role not in held_roles:
    role = held_roles[0]
    st.session_state.role = role

col1, col2 = st.columns([10, 1])
with col1:
    if st.button("🏠 Home"):
        st.switch_page("Home.py")
with col2:
    if st.button("Logout"):
        for k in ["logged_in", "user_email", "role", "roles", "otp_email"]:
            st.session_state.pop(k, None)
        st.switch_page("pages/2_Approver_Login.py")

col1, col2 = st.columns([10, 1])
with col1:
    st.title("Approver Dashboard")
with col2:
    if st.button("Refresh"):
        st.rerun()

# ── Role switcher: only shown when they hold more than one ──
LABELS = {
    "admin":    "Admin — every application",
    "finance":  "Finance — create SAP codes",
    "approver": "Reviewer — assigned to me",
}

if len(held_roles) > 1:
    sw1, sw2 = st.columns([2, 5])
    with sw1:
        picked = st.selectbox(
            "View as",
            held_roles,
            index=held_roles.index(role),
            format_func=lambda r: LABELS.get(r, r),
        )
    if picked != role:
        st.session_state.role = picked
        st.rerun()
    st.caption(f"Logged in as **{user_email}** · you hold {len(held_roles)} roles · viewing as **{role}**")
else:
    st.caption(f"Logged in as **{user_email}** · role: **{role}**")


@st.cache_data(ttl=86400, show_spinner=False)
def cached_analysis(name, address, gst):
    return analyze_vendor(name, address, gst)


def safe_name(v):
    return "".join(c for c in str(v) if c.isalnum() or c in (" ", "-", "_"))


def risk_chip(label, level):
    level = (level or "Unknown").strip()
    st.caption(label)
    if level.lower() == "low":
        st.success(level)
    elif level.lower() in ("medium", "med"):
        st.warning(level)
    elif level.lower() == "high":
        st.error(level)
    else:
        st.info(level)


def _field(row, *names):
    for n in names:
        if n in row.index and pd.notna(row[n]):
            return str(row[n])
    return ""


vendors_list = get_all_vendors()
if not vendors_list:
    st.warning("No vendors submitted yet")
else:
    try:
        df = pd.DataFrame(vendors_list)
        for col in ["Status", "Remarks", "Vendor Code", "Assigned To", "Approved By"]:
            if col not in df.columns:
                df[col] = ""
        df["Status"] = df["Status"].fillna("Pending").astype(str)
        df["Assigned To"] = df["Assigned To"].fillna("").astype(str)

        # ── ROLE-BASED VIEW ──
        ue = user_email.strip().lower()
        if role == "admin":
            view_df = df                                   # everything
        elif role == "finance":
            # Accepted vendors awaiting a code, plus anything that came back
            # to this finance user after a re-upload.
            view_df = df[
                (df["Status"] == "Accepted")
                | (df["Assigned To"].str.strip().str.lower() == ue)
            ]
        else:  # approver: only vendors assigned to their email
            view_df = df[df["Assigned To"].str.strip().str.lower() == ue]

        if view_df.empty:
            if role == "finance":
                st.info("No accepted vendors awaiting SAP code creation.")
            elif role == "admin":
                st.info("No vendors in the system yet.")
            else:
                st.info("No vendors are assigned to you yet.")
            st.stop()

        st.subheader("Vendors")
        all_statuses = sorted(view_df["Status"].unique().tolist())
        fc, cc = st.columns([1, 1])
        with fc:
            sel = st.multiselect("Filter by status", options=all_statuses,
                                 default=all_statuses, placeholder="Choose statuses")
        filtered_df = view_df[view_df["Status"].isin(sel)] if sel else view_df
        with cc:
            st.metric("Showing", f"{len(filtered_df)} / {len(view_df)}")

        st.dataframe(filtered_df, use_container_width=True)
        st.markdown("---")
        if filtered_df.empty:
            st.warning("No vendors match the selected filter.")
            st.stop()

        vendor = st.selectbox("Select Vendor", filtered_df["Vendor Name"].unique())
        vendor_row = df[df["Vendor Name"] == vendor].iloc[0]

        vendor_type = _field(vendor_row, "Vendor Type")
        vendor_email1 = _field(vendor_row, "Email 1", "Email")
        addr = [_field(vendor_row, c) for c in
                ["Address Line 1", "Address Line 2", "City", "State", "Country", "Pincode"]]
        vendor_address = ", ".join(p for p in addr if p and p.upper() != "NA")
        vendor_gst = _field(vendor_row, "GST Number", "GST", "GSTIN")
        vendor_details = {c: _field(vendor_row, c) for c in df.columns}

        # ── DOCUMENTS (from MongoDB) ──
        docs = list_documents(vendor)
        if docs:
            st.subheader("📁 Uploaded Documents")
            doc_types = [d[0] for d in docs]
            selected_doc = st.radio("Documents", doc_types, horizontal=True)
            file_name = dict(docs)[selected_doc]
            st.write(f"Uploaded File: {file_name}")
            fb = get_document_bytes(vendor, file_name)
            if fb:
                st.download_button(f"Download {selected_doc}", fb, file_name=file_name)
                if file_name.lower().endswith(".pdf"):
                    st.markdown(
                        f'<iframe src="data:application/pdf;base64,{base64.b64encode(fb).decode()}" '
                        f'width="100%" height="800" type="application/pdf"></iframe>',
                        unsafe_allow_html=True)
                elif file_name.lower().endswith((".png", ".jpg", ".jpeg")):
                    st.image(fb, use_container_width=True)
            else:
                st.warning("File not found in database.")
        else:
            st.info("No documents uploaded for this vendor.")

        # ── AI RISK ASSESSMENT (everyone: approver, admin, finance) ──
        st.markdown("---")
        st.subheader("🔎 AI Vendor Risk Assessment")
        st.caption(f"Inputs → Name: {vendor}  |  Address: {vendor_address or '—'}  |  GST: {vendor_gst or '—'}")

        force_fresh = st.button("🔄 Re-run analysis (fresh)")

        # Try the saved report first (saves Gemini quota).
        result = None
        if not force_fresh:
            result = get_ai_report(vendor)

        if result is None:
            # No saved report (or user forced a fresh run) → call Gemini once.
            status = st.status(f"🔎 Searching public sources for {vendor}...", expanded=True)
            status.write("Identifying the legal entity...")
            status.write("Scanning court records, MCA, GST & NCLT...")
            status.write("Checking news & regulatory actions...")
            status.write("Compiling risk scorecard...")
            try:
                result = analyze_vendor(vendor, vendor_address, vendor_gst)
                save_ai_report(vendor, result)   # cache for next time
                status.update(label="✅ Analysis complete (saved)", state="complete", expanded=False)
            except Exception as e:
                status.update(label="❌ Analysis failed", state="error")
                st.error(f"AI analysis failed: {e}")
                result = None
        else:
            st.success("Showing saved AI report (no new analysis used).")

        if result:
            sc = result.get("scorecard_fields", {})
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Risk Score", f"{sc.get('RiskScore', '—')}/100")
            m2.metric("Years in Business", sc.get("YearsInBusiness", "—"))
            m3.metric("Court Cases", sc.get("CourtCases", "0"))
            m4.metric("Sources Checked", result.get("source_count", 0))
            c1, c2, c3, c4 = st.columns(4)
            with c1: risk_chip("Compliance", sc.get("Compliance"))
            with c2: risk_chip("Reputational", sc.get("Reputational"))
            with c3: risk_chip("Financial", sc.get("Financial"))
            with c4: risk_chip("Operational", sc.get("Operational"))
            st.markdown("### Summary")
            st.markdown(
                f"**Overall Risk:** {sc.get('OverallRisk','—')}  \n"
                f"**Recommendation:** {sc.get('Recommendation','—')}  \n"
                f"**Confidence:** {sc.get('Confidence','—')}  \n"
                f"**Why:** {sc.get('Reason','').strip() or '—'}")
            watch = sc.get("Watch", "").strip()
            if watch and watch.lower() != "nothing significant.":
                st.info(f"👁 **Watch:** {watch}")
            redflags = (result.get("redflags") or "").strip()
            st.markdown("### 🚩 Red Flags")
            if redflags and redflags.lower() != "none found.":
                st.markdown(redflags)
            else:
                st.success("No material red flags found in public sources.")
            if result.get("sources"):
                st.markdown("### 🔗 Sources")
                for item in result["sources"]:
                    title, uri = item[0], item[1]
                    st.markdown(f"- [{title}]({uri})")
            with st.expander("📄 Detailed report", expanded=True):
                st.markdown(result.get("details") or "_No detail returned._")

        st.markdown("---")

        # ── DECISION AREA ──
        if role == "finance":
            st.subheader("🏦 Finance Review")
            st.write(f"Vendor: **{vendor}**  |  Type: {vendor_type}")

            current_code = _field(vendor_row, "Vendor Code")
            if current_code:
                st.success(
                    f"Already created — Vendor Code: {current_code}"
                    f"  |  BP Code: {_field(vendor_row, 'BP Code') or '—'}"
                    f"  |  TDS Status: {_field(vendor_row, 'TDS Status') or '—'}"
                )

            approver_email = _field(vendor_row, "Assigned To")

            fin_decision = st.selectbox(
                "Finance Decision",
                ["Accepted", "Pending Documents", "Rejected"],
                key="fin_decision",
            )

            # ── Reject / ask for documents: reason required, submit sends mail ──
            if fin_decision in ("Rejected", "Pending Documents"):
                if fin_decision == "Rejected":
                    fin_remarks = st.text_area(
                        "Reason for Rejection *",
                        placeholder="Example: Bank details do not match the cancelled cheque",
                    )
                else:
                    fin_remarks = st.text_area(
                        "Documents Required *",
                        placeholder="Example: Upload a revised EFT form",
                    )

                if st.button(f"Submit — {fin_decision}"):
                    if not fin_remarks.strip():
                        st.error("Please give a reason before submitting.")
                    else:
                        # Route re-uploads straight back to finance
                        update_vendor(vendor, {
                            "Status": fin_decision,
                            "Remarks": fin_remarks.strip(),
                            "Reviewed By Finance": user_email,
                            "Assigned To": user_email,       # comes back to finance
                            "Original Approver": approver_email,
                        })
                        try:
                            send_finance_decision_email(
                                vendor_email1, approver_email, user_email,
                                vendor, fin_decision, fin_remarks.strip(),
                            )
                            st.success(
                                f"{vendor} → {fin_decision}. Vendor, approver and finance notified."
                            )
                        except Exception as e:
                            st.warning(f"Saved, but email failed: {e}")

            # ── Accept: reveal the code fields. Submitting the code sends the mail. ──
            else:
                st.markdown("**Accepted — enter the codes to complete onboarding.**")

                fc1, fc2, fc3 = st.columns(3)
                with fc1:
                    vendor_code = st.text_input("SAP Vendor Code / Customer ID *")
                with fc2:
                    bp_code = st.text_input("BP Code")
                with fc3:
                    tds_status = st.selectbox(
                        "TDS Status",
                        ["-- Select --", "Applicable", "Lower Rate", "Exempted"],
                    )

                if st.button("Submit & Notify Vendor"):
                    if not vendor_code.strip():
                        st.error("Please enter a vendor code.")
                    else:
                        update_vendor(vendor, {
                            "Vendor Code": vendor_code.strip(),
                            "BP Code": bp_code.strip(),
                            "TDS Status": "" if tds_status.startswith("--") else tds_status,
                            "Code Created By": user_email,
                            "Reviewed By Finance": user_email,
                            "Status": "Code Created",
                        })
                        try:
                            send_code_created_email(
                                vendor_email1, vendor, vendor_code.strip(), user_email
                            )
                            st.success(
                                f"Codes saved and vendor notified at {vendor_email1 or '(no email)'}"
                            )
                        except Exception as e:
                            st.warning(f"Codes saved, but email failed: {e}")
        else:
            st.subheader("Decision")
            decision = st.selectbox("Decision", ["Accepted", "Pending Documents", "Rejected"])
            remarks = ""
            if decision == "Pending Documents":
                remarks = st.text_area("Documents Required",
                                       placeholder="Example: Upload GST Certificate")
            elif decision == "Rejected":
                remarks = st.text_area("Reason for Rejection",
                                       placeholder="Example: GST Number Invalid")
            if st.button("Update Status"):
                update_vendor(vendor, {"Status": decision, "Remarks": str(remarks), "Approved By": user_email})
                vendor_details["Status"] = decision
                try:
                    if decision in ("Rejected", "Pending Documents"):
                        send_vendor_status_email(vendor_email1, vendor, decision, remarks)
                        st.success(f"{vendor} → {decision}. Vendor notified.")
                    elif decision == "Accepted":
                        fin = get_finance_emails()
                        send_accepted_email(vendor_email1, fin, user_email, vendor, vendor_details)
                        st.success(f"{vendor} → Accepted. Vendor and Finance notified.")
                except Exception as e:
                    st.warning(f"Status saved, but email failed: {e}")

    except Exception as e:
        st.error(f"Error: {e}")