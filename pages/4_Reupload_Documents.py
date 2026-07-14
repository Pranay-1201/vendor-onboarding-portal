import streamlit as st
import os

from db_utils import find_vendor, save_document, update_vendor
from email_utils import send_reupload_email

st.set_page_config(page_title="Re-upload Documents", layout="centered")

with open("styles/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

# Small Home button at the left of the band
hcol, _ = st.columns([1, 4])
with hcol:
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("Home.py")

st.title("Re-upload Documents")
st.caption("If you were asked to provide additional documents, find your application below and upload them.")


def safe_filename(name):
    name = os.path.basename(str(name).replace("\\", "/"))
    cleaned = "".join(c for c in name if c.isalnum() or c in (" ", ".", "-", "_")).strip()
    return cleaned or "file"


# ── Step 1: find the application ──
st.markdown("#### Find your application")
c1, c2 = st.columns(2)
with c1:
    vendor_name = st.text_input("Vendor Name")
with c2:
    gst_number = st.text_input("GST Number")

if st.button("Find Application"):
    if not vendor_name.strip() or not gst_number.strip():
        st.error("Please enter both Vendor Name and GST Number.")
    else:
        vendor = find_vendor(vendor_name.strip(), gst_number.strip())
        if not vendor:
            st.error("No application found with that Vendor Name and GST Number.")
            st.session_state.pop("reupload_vendor", None)
        elif vendor.get("Status") != "Pending Documents":
            st.warning(
                f"This application's status is '{vendor.get('Status')}'. "
                "Re-upload is only allowed when documents have been requested "
                "(status 'Pending Documents')."
            )
            st.session_state.pop("reupload_vendor", None)
        else:
            st.session_state.reupload_vendor = vendor
            st.rerun()


# ── Step 2: show remarks + upload ──
if st.session_state.get("reupload_vendor"):
    vendor = st.session_state.reupload_vendor
    st.success(f"Application found: **{vendor['Vendor Name']}**")

    remarks = vendor.get("Remarks", "")
    if remarks:
        st.info(f"📝 Documents requested by reviewer: {remarks}")

    st.markdown("#### Upload the requested documents")
    st.caption("Add a short label for each document so the reviewer knows what it is.")

    uploads = []
    for i in range(1, 6):
        col1, col2 = st.columns([1, 2])
        with col1:
            label = st.text_input(f"Document {i} name", key=f"lbl_{i}",
                                  placeholder="e.g. GST Certificate")
        with col2:
            file = st.file_uploader(f"File {i}", key=f"file_{i}",
                                   label_visibility="collapsed")
        if label.strip() and file:
            uploads.append((label.strip(), file))

    if st.button("Submit Documents"):
        if not uploads:
            st.error("Please add at least one labelled document.")
        else:
            try:
                new_doc_names = []
                for label, file in uploads:
                    fname = safe_filename(file.name)
                    save_document(vendor["Vendor Name"], label, fname, file.getbuffer().tobytes())
                    new_doc_names.append(label)

                update_vendor(vendor["Vendor Name"], {"Status": "Pending"})

                assigned = vendor.get("Assigned To", "")
                if assigned:
                    send_reupload_email(assigned, vendor["Vendor Name"], new_doc_names)

                st.session_state.pop("reupload_vendor", None)
                st.success(
                    "Documents uploaded successfully. Your application is back "
                    "under review. You'll be notified of the outcome by email."
                )
            except Exception as e:
                st.error(f"Something went wrong: {e}")