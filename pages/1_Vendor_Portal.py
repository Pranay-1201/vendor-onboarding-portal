import streamlit as st
import os

st.set_page_config(
    page_title="Onboarding Portal",
    layout="wide"
)

with open("styles/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if st.button("🏠 Home"):
    st.switch_page("Home.py")

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
#  PARTY TYPE: Vendor or Customer
# ═══════════════════════════════════════════════
st.title("Account Opening Form")

party_type = st.selectbox(
    "Are you registering a Vendor or a Customer?",
    ["-- Select --", "Vendor", "Customer"]
)

if party_type == "-- Select --":
    st.info("Please select Vendor or Customer to continue.")
    st.stop()

is_vendor = (party_type == "Vendor")


# ── Vendor only: pick a vendor type ──
vendor_type = ""
if is_vendor:
    st.subheader("Vendor Type")
    vendor_type = st.selectbox(
        "Select Vendor Type",
        [
            "-- Select Vendor Type --",
            "Raw Material Supplier",
            "Packaging Supplier",
            "Logistics Provider",
            "Warehouse Provider",
            "Contract Manufacturer",
            "Service Provider"
        ]
    )
    if vendor_type == "-- Select Vendor Type --":
        st.info("Please select a vendor type to continue.")
        st.stop()
else:
    vendor_type = "Customer"


# ═══════════════════════════════════════════════
#  ASSIGN TO  (same for both)
# ═══════════════════════════════════════════════
st.subheader("Assign To")
assigned_to = st.text_input("Company Employee Email *")


# ═══════════════════════════════════════════════
#  NAME & BILLING ADDRESS  (same for both)
# ═══════════════════════════════════════════════
label = "Vendor" if is_vendor else "Customer"
st.subheader(f"{label} Name & Address")

vendor_name = st.text_input(f"{label} Name *")
address_line1 = st.text_input("Address Line 1 *")
address_line2 = st.text_input("Address Line 2")

col1, col2, col3, col4 = st.columns(4)
with col1:
    city = st.text_input("City *")
with col2:
    state = st.text_input("State *")
with col3:
    country = st.text_input("Country *")
with col4:
    pincode = st.text_input("Pin Code *")


# ── Customer only: shipping addresses (up to 5) ──
ship_different = False
shipping_addresses = []

if not is_vendor:
    ship_different = st.checkbox("Shipping address is different from billing address")

    if ship_different:
        st.subheader("Shipping Addresses")

        # How many shipping addresses to show (1-5)
        if "ship_count" not in st.session_state:
            st.session_state.ship_count = 1

        n = st.session_state.ship_count

        # Render them two per row
        for start in range(0, n, 2):
            cols = st.columns(2)
            for offset, col in enumerate(cols):
                idx = start + offset
                if idx >= n:
                    break
                with col:
                    st.markdown(f"**Shipping Address {idx + 1}**")
                    star = " *" if idx == 0 else ""
                    l1 = st.text_input(f"Address Line 1{star}", key=f"s_l1_{idx}")
                    l2 = st.text_input("Address Line 2", key=f"s_l2_{idx}")
                    c1, c2 = st.columns(2)
                    with c1:
                        cty = st.text_input(f"City{star}", key=f"s_city_{idx}")
                        cnt = st.text_input(f"Country{star}", key=f"s_country_{idx}")
                    with c2:
                        stt = st.text_input(f"State{star}", key=f"s_state_{idx}")
                        pin = st.text_input(f"Pin Code{star}", key=f"s_pin_{idx}")

                    shipping_addresses.append({
                        "Address Line 1": l1,
                        "Address Line 2": l2,
                        "City": cty,
                        "State": stt,
                        "Country": cnt,
                        "Pincode": pin,
                    })

        if n < 5:
            if st.button(f"+ Add Shipping Address {n + 1}"):
                st.session_state.ship_count = n + 1
                st.rerun()
        else:
            st.caption("Maximum of 5 shipping addresses.")


# ═══════════════════════════════════════════════
#  DETAILS SECTION  (different for Vendor vs Customer)
# ═══════════════════════════════════════════════
st.subheader(f"{label} Details")

# Initialise all so they always exist
vendor_category = Nature_of_Transaction = BP_code = payment_Terms = vendor_Group = ""
customer_category = margin_mrp = credit_period = customer_Group = ""
payment_currency = ""

if is_vendor:
    col1, col2, col3 = st.columns(3)
    with col1:
        vendor_category = st.selectbox(
            "Vendor Category *",
            ["-- Select Vendor Category --", "Proprietor", "Partnership Firm", "Company", "LLP"]
        )
        Nature_of_Transaction = st.text_input("Nature of Transaction ")
    with col2:
        payment_currency = st.selectbox("Payment Currency", ["INR", "USD", "EUR"])
        BP_code = st.text_input("BP Code ")
    with col3:
        payment_Terms = st.text_input("Payment Terms *")
        vendor_Group = st.text_input("Vendor Group ")

else:
    col1, col2, col3 = st.columns(3)
    with col1:
        customer_category = st.selectbox(
            "Customer Category *",
            ["-- Select Customer Category --", "Proprietor", "Partnership Firm", "Company", "LLP"]
        )
        credit_period = st.text_input("Credit Period *")
    with col2:
        margin_mrp = st.text_input("Margin on MRP *")
        customer_Group = st.text_input("Customer Group ")
    with col3:
        payment_currency = st.selectbox("Payment Currency", ["INR", "USD", "EUR"])


# ═══════════════════════════════════════════════
#  CONTACT DETAILS  (same for both)
# ═══════════════════════════════════════════════
st.subheader("Contact Details")

col1, col2, col3 = st.columns(3)
with col1:
    contact_person = st.text_input("Person Name *")
    email1 = st.text_input("Email 1 (primary) *")
    website = st.text_input("Website")
with col2:
    mobile_no = st.text_input("Mobile Number *")
    email2 = st.text_input("Email 2")
    fax_no = st.text_input("Fax Number")
with col3:
    alternate_contact = st.text_input("Alternate Contact Number")
    email3 = st.text_input("Email 3")
    pan_number = st.text_input("PAN Number *")


# ═══════════════════════════════════════════════
#  GST REGISTRATION
#  Vendor  → optional, behind an "applicable?" checkbox
#  Customer → always mandatory
# ═══════════════════════════════════════════════
st.subheader("GST Registration Details")

gst_applicable = True
gst_number = ""

if is_vendor:
    gst_applicable = st.checkbox("Is GST applicable?")
    if gst_applicable:
        gst_number = st.text_input("GST Number *")
else:
    gst_number = st.text_input("GST Number *")


# ═══════════════════════════════════════════════
#  BANK / RTGS  (same for both)
# ═══════════════════════════════════════════════
st.subheader("Bank / RTGS Details")
col1, col2 = st.columns(2)
with col1:
    bank_name = st.text_input("Bank Name *")
with col2:
    account_number = st.text_input("Bank Account Number *")

col1, col2 = st.columns(2)
with col1:
    ifsc_code = st.text_input("IFSC Code *")
with col2:
    beneficiary_name = st.text_input("Beneficiary Name")


# ═══════════════════════════════════════════════
#  MSME  (vendor: behind a checkbox; customer: optional)
# ═══════════════════════════════════════════════
st.subheader("MSME Details")

msme_applicable = False
msme_number = msme_date = ""

msme_applicable = st.checkbox("Is MSME applicable?")
if msme_applicable:
    col1, col2 = st.columns(2)
    with col1:
        msme_number = st.text_input("MSME Registration Number *")
    with col2:
        msme_date = st.text_input("MSME Registration Date *", placeholder="DD/MM/YYYY")

st.warning('If any of the fields above is not applicable, fill "NA". Do not leave any field blank.')


# ═══════════════════════════════════════════════
#  DOCUMENTS  (different for Vendor vs Customer)
# ═══════════════════════════════════════════════
st.subheader("Upload Documents")

# Initialise every uploader variable so none are ever undefined
gst_cert = pan_card = cancelled_cheque = msme = None
eft_form = None
company_reg = tax_registration = certificate_origin = None
export_license = bank_confirmation = import_export_doc = None
Pm_Agreement = Agreement = transport_license = fleet_details = None
warehouse_license = Quality_Audit_Report = fire_noc = None
ESG_Compliance_certificate = insurance = None
factory_license = manufacturing_license = Dept_Head_Approval = None

foreign_supplier = False


if not is_vendor:
    # ── CUSTOMER DOCUMENTS ──
    col1, col2, col3 = st.columns(3)
    with col1:
        pan_card = st.file_uploader("PAN Proof *")
        gst_cert = st.file_uploader("GST Proof *")
    with col2:
        cancelled_cheque = st.file_uploader("Cancelled Cheque *")
        Agreement = st.file_uploader("Agreement *")
    with col3:
        eft_form = st.file_uploader("EFT Form (if applicable)")
        msme = st.file_uploader("MSME Certificate (if applicable)")

else:
    # ── VENDOR DOCUMENTS (by vendor type) ──
    if vendor_type == "Raw Material Supplier":
        col1, col2, col3 = st.columns(3)
        with col1:
            gst_cert = st.file_uploader("GST Certificate *")
            pan_card = st.file_uploader("PAN Card *")
        with col2:
            cancelled_cheque = st.file_uploader("Cancelled Cheque *")
        with col3:
            msme = st.file_uploader("MSME Certificate")

        st.info("For suppliers located outside India.")
        foreign_supplier = st.checkbox("I am located outside India")

        if foreign_supplier:
            st.info("Please upload the following additional documents.")
            col4, col5, col6 = st.columns(3)
            with col4:
                company_reg = st.file_uploader("Company Registration Certificate *")
                tax_registration = st.file_uploader("Tax Registration Certificate *")
            with col5:
                certificate_origin = st.file_uploader("Certificate of Origin *")
                export_license = st.file_uploader("Export License / Trade License *")
            with col6:
                bank_confirmation = st.file_uploader("Bank Confirmation Letter / SWIFT Details *")
                import_export_doc = st.file_uploader("IEC / Import-Export Documents *")

    elif vendor_type == "Packaging Supplier":
        col1, col2, col3 = st.columns(3)
        with col1:
            gst_cert = st.file_uploader("GST Certificate *")
            pan_card = st.file_uploader("PAN Card *")
        with col2:
            cancelled_cheque = st.file_uploader("Cancelled Cheque *")
            Pm_Agreement = st.file_uploader("PM Agreement *")
        with col3:
            msme = st.file_uploader("MSME Certificate")

    elif vendor_type == "Logistics Provider":
        col1, col2, col3 = st.columns(3)
        with col1:
            gst_cert = st.file_uploader("GST Certificate *")
            cancelled_cheque = st.file_uploader("Cancelled Cheque *")
            Agreement = st.file_uploader("Agreement")
        with col2:
            pan_card = st.file_uploader("PAN Card *")
            transport_license = st.file_uploader("Transport License *")
        with col3:
            msme = st.file_uploader("MSME Certificate")
            fleet_details = st.file_uploader("Fleet Details *")

    elif vendor_type == "Warehouse Provider":
        col1, col2, col3 = st.columns(3)
        with col1:
            gst_cert = st.file_uploader("GST Certificate *")
            pan_card = st.file_uploader("PAN Card *")
            warehouse_license = st.file_uploader("Warehouse License *")
            Quality_Audit_Report = st.file_uploader("Quality Audit Report *")
        with col2:
            cancelled_cheque = st.file_uploader("Cancelled Cheque *")
            fire_noc = st.file_uploader("Fire NOC *")
            ESG_Compliance_certificate = st.file_uploader("ESG Compliance Certificate *")
        with col3:
            msme = st.file_uploader("MSME Certificate")
            insurance = st.file_uploader("Insurance Certificate *")
            Agreement = st.file_uploader("Agreement")

    elif vendor_type == "Contract Manufacturer":
        col1, col2, col3 = st.columns(3)
        with col1:
            gst_cert = st.file_uploader("GST Certificate *")
            pan_card = st.file_uploader("PAN Card *")
            cancelled_cheque = st.file_uploader("Cancelled Cheque *")
        with col2:
            Agreement = st.file_uploader("Agreement")
            ESG_Compliance_certificate = st.file_uploader("ESG Compliance Certificate *")
            Quality_Audit_Report = st.file_uploader("Quality Audit Report *")
        with col3:
            msme = st.file_uploader("MSME Certificate")
            factory_license = st.file_uploader("Factory License *")
            manufacturing_license = st.file_uploader("Manufacturing License *")

    elif vendor_type == "Service Provider":
        col1, col2, col3 = st.columns(3)
        with col1:
            gst_cert = st.file_uploader("GST Certificate *")
            pan_card = st.file_uploader("PAN Card *")
        with col2:
            cancelled_cheque = st.file_uploader("Cancelled Cheque *")
            Agreement = st.file_uploader("Agreement")
        with col3:
            msme = st.file_uploader("MSME Certificate")
            Dept_Head_Approval = st.file_uploader("Department Head Approval *")


# ═══════════════════════════════════════════════
#  SUBMIT
# ═══════════════════════════════════════════════
if st.button(f"Submit {label}"):

    # ── Required field checks ──
    if not assigned_to.strip():
        st.error("Please enter the Company Employee Email to assign this to.")
        st.stop()

    missing = []

    # Common mandatory fields
    if not vendor_name.strip():   missing.append(f"{label} Name")
    if not address_line1.strip(): missing.append("Address Line 1")
    if not city.strip():          missing.append("City")
    if not state.strip():         missing.append("State")
    if not country.strip():       missing.append("Country")
    if not pincode.strip():       missing.append("Pin Code")
    if not contact_person.strip():missing.append("Person Name")
    if not mobile_no.strip():     missing.append("Mobile Number")
    if not email1.strip():        missing.append("Email 1")
    if not bank_name.strip():     missing.append("Bank Name")
    if not account_number.strip():missing.append("Bank Account Number")
    if not ifsc_code.strip():     missing.append("IFSC Code")
    if not pan_number.strip():    missing.append("PAN Number")

    # MSME is behind the same checkbox for both
    if msme_applicable:
        if not msme_number.strip():
            missing.append("MSME Registration Number")
        if not msme_date.strip():
            missing.append("MSME Registration Date")

    if is_vendor:
        if not payment_Terms.strip():
            missing.append("Payment Terms")
        if gst_applicable and not gst_number.strip():
            missing.append("GST Number")
    else:
        if customer_category.startswith("--"):
            missing.append("Customer Category")
        if not credit_period.strip():
            missing.append("Credit Period")
        if not margin_mrp.strip():
            missing.append("Margin on MRP")
        if not gst_number.strip():
            missing.append("GST Number")
        # First shipping address is mandatory if the box is ticked
        if ship_different and shipping_addresses:
            a = shipping_addresses[0]
            if not a["Address Line 1"].strip(): missing.append("Shipping Address 1 - Line 1")
            if not a["City"].strip():           missing.append("Shipping Address 1 - City")
            if not a["State"].strip():          missing.append("Shipping Address 1 - State")
            if not a["Country"].strip():        missing.append("Shipping Address 1 - Country")
            if not a["Pincode"].strip():        missing.append("Shipping Address 1 - Pin Code")

    if missing:
        st.error("Please fill all mandatory (*) fields: " + ", ".join(missing))
        st.stop()

    # ── Document validation ──
    if not is_vendor:
        if not (pan_card and gst_cert and cancelled_cheque and Agreement):
            st.error("Please upload all mandatory (*) documents")
            st.stop()
    else:
        if vendor_type == "Raw Material Supplier":
            if not (gst_cert and pan_card and cancelled_cheque):
                st.error("Please upload all mandatory (*) documents")
                st.stop()
            if foreign_supplier:
                if not (company_reg and tax_registration and certificate_origin
                        and export_license and bank_confirmation and import_export_doc):
                    st.error("Please upload all mandatory Foreign Supplier documents")
                    st.stop()

        elif vendor_type == "Packaging Supplier":
            if not (gst_cert and pan_card and cancelled_cheque and Pm_Agreement):
                st.error("Please upload all mandatory (*) documents")
                st.stop()

        elif vendor_type == "Logistics Provider":
            if not (gst_cert and pan_card and cancelled_cheque and
                    transport_license and fleet_details):
                st.error("Please upload all mandatory (*) documents")
                st.stop()

        elif vendor_type == "Warehouse Provider":
            if not (gst_cert and pan_card and cancelled_cheque and warehouse_license
                    and fire_noc and insurance and Quality_Audit_Report
                    and ESG_Compliance_certificate):
                st.error("Please upload all mandatory (*) documents")
                st.stop()

        elif vendor_type == "Contract Manufacturer":
            if not (gst_cert and pan_card and cancelled_cheque and manufacturing_license
                    and factory_license and Quality_Audit_Report
                    and ESG_Compliance_certificate):
                st.error("Please upload all mandatory (*) documents")
                st.stop()

        elif vendor_type == "Service Provider":
            if not (gst_cert and pan_card and cancelled_cheque and
                    Dept_Head_Approval):
                st.error("Please upload all mandatory (*) documents")
                st.stop()

    # ── Map document type -> uploaded file ──
    _all_uploaders = {}

    if not is_vendor:
        _all_uploaders = {
            "PAN Proof": pan_card,
            "GST Proof": gst_cert,
            "Cancelled Cheque": cancelled_cheque,
            "Agreement": Agreement,
            "EFT Form": eft_form,
            "MSME Certificate": msme,
        }
    else:
        _all_uploaders = {
            "GST Certificate": gst_cert,
            "PAN Card": pan_card,
            "Cancelled Cheque": cancelled_cheque,
            "MSME Certificate": msme,
        }
        if foreign_supplier:
            _all_uploaders.update({
                "Company Registration Certificate": company_reg,
                "Tax Registration Certificate": tax_registration,
                "Certificate of Origin": certificate_origin,
                "Export License": export_license,
                "Bank Confirmation Letter": bank_confirmation,
                "Import Export Documents": import_export_doc,
            })
        if vendor_type == "Packaging Supplier":
            _all_uploaders["PM Agreement"] = Pm_Agreement
        elif vendor_type == "Logistics Provider":
            _all_uploaders.update({
                "Transport License": transport_license,
                "Fleet Details": fleet_details,
                "Agreement": Agreement,
            })
        elif vendor_type == "Warehouse Provider":
            _all_uploaders.update({
                "Warehouse License": warehouse_license,
                "Quality Audit Report": Quality_Audit_Report,
                "Fire NOC": fire_noc,
                "ESG Compliance Certificate": ESG_Compliance_certificate,
                "Insurance Certificate": insurance,
                "Agreement": Agreement,
            })
        elif vendor_type == "Contract Manufacturer":
            _all_uploaders.update({
                "Agreement": Agreement,
                "ESG Compliance Certificate": ESG_Compliance_certificate,
                "Quality Audit Report": Quality_Audit_Report,
                "Factory License": factory_license,
                "Manufacturing License": manufacturing_license,
            })
        elif vendor_type == "Service Provider":
            _all_uploaders.update({
                "Agreement": Agreement,
                "Department Head Approval": Dept_Head_Approval,
            })

    def safe_filename(name):
        name = os.path.basename(str(name).replace("\\", "/"))
        cleaned = "".join(c for c in name if c.isalnum() or c in (" ", ".", "-", "_")).strip()
        return cleaned or "file"

    from datetime import datetime
    from db_utils import (save_vendor, save_document, check_duplicates,
                          next_party_id)

    # ── Duplicate check on PAN / GST ──
    dup = check_duplicates(vendor_name, pan_number, gst_number)

    if dup["exact"]:
        st.error(
            f"This {label.lower()} already exists — the name, PAN and GST all "
            f"match an existing record. Nothing has been submitted."
        )
        st.stop()

    # PAN or GST already used by a different name: warn, but allow it through.
    warnings = []
    if dup["pan_matches"]:
        others = ", ".join(sorted(set(dup["pan_matches"])))
        warnings.append(f"This **PAN is already registered** under: {others}")
    if dup["gst_matches"]:
        others = ", ".join(sorted(set(dup["gst_matches"])))
        warnings.append(f"This **GST is already registered** under: {others}")

    for w in warnings:
        st.warning(f"⚠️ {w}")

    # Save documents to the database
    for doc_type, upload in _all_uploaders.items():
        if upload:
            fname = safe_filename(upload.name)
            save_document(vendor_name, doc_type, fname, upload.getbuffer().tobytes())

    # Sequential ID and submission timestamp
    party_id = next_party_id(party_type)
    submitted_on = datetime.now().strftime("%d-%m-%Y")

    # ── Build the record ──
    record = {
        "Party ID": party_id,                   # VFY27001 / CFY27001
        "Submitted On": submitted_on,
        "Party Type": party_type,               # "Vendor" or "Customer"
        "Vendor Type": vendor_type,             # vendor type, or "Customer"
        "Vendor Name": vendor_name,

        "Address Line 1": address_line1,
        "Address Line 2": address_line2,
        "City": city,
        "State": state,
        "Country": country,
        "Pincode": pincode,

        "Shipping Different": ship_different,
        "Shipping Addresses": shipping_addresses,

        # Vendor-specific
        "Vendor Category": vendor_category,
        "Nature of Transaction": Nature_of_Transaction,
        "BP Code": BP_code,
        "Payment Terms": payment_Terms,
        "Vendor Group": vendor_Group,

        # Customer-specific
        "Customer Category": customer_category,
        "Margin on MRP": margin_mrp,
        "Credit Period": credit_period,
        "Customer Group": customer_Group,

        # Common
        "Payment Currency": payment_currency,

        "Contact Person": contact_person,
        "Alternate Contact": alternate_contact,
        "Fax Number": fax_no,
        "Mobile Number": mobile_no,
        "Email 1": email1,
        "Email 2": email2,
        "Email 3": email3,
        "Website": website,
        "Assigned To": assigned_to.strip(),

        "GST Applicable": gst_applicable,
        "GST Number": gst_number,

        "Bank Name": bank_name,
        "Account Number": account_number,
        "IFSC Code": ifsc_code,
        "Beneficiary Name": beneficiary_name,

        "MSME Applicable": msme_applicable,
        "MSME Registration Number": msme_number,
        "MSME Registration Date": msme_date,

        "PAN Number": pan_number,
        "Foreign Supplier": foreign_supplier,

        "Vendor Code": "",
        "BP Code": "",
        "TDS Status": "",

        # Audit trail — filled in as the application progresses
        "Approved By": "",
        "Approved On": "",
        "Reviewed By Finance": "",
        "Code Created By": "",
        "Code Created On": "",

        "Status": "Pending",
        "Remarks": "",
    }

    save_vendor(record)

    # ── Emails ──
    try:
        from email_utils import send_new_vendor_email, send_submission_confirmation

        send_new_vendor_email(assigned_to.strip(), vendor_name, record)
        st.info(f"📧 Notification sent to: {assigned_to.strip()}")

        send_submission_confirmation(email1, vendor_name, {"Vendor Name": vendor_name})
    except Exception as e:
        st.warning(f"{label} saved, but notification email failed: {e}")

    st.success(f"{label} Submitted Successfully")
    st.info(f"Your reference ID is **{party_id}** — please keep it for your records.")