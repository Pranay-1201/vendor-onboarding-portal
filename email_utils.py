import smtplib
from email.message import EmailMessage

# ── Email account that SENDS all mail (fill in your values) ──
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "parthipranay2001@gmail.com"
SMTP_PASS = "vkxlrrhbrkjzemyd"


def _send(to_addrs, subject, body):
    to_addrs = [a for a in to_addrs if a and str(a).strip() and str(a).upper() != "NA"]
    if not to_addrs:
        return
    if not (SMTP_USER and SMTP_PASS):
        raise RuntimeError("Email not configured. Set SMTP_USER and SMTP_PASS.")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(to_addrs)
    msg.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


def _details_block(vendor_details: dict) -> str:
    order = [
        "Vendor Type", "Vendor Name", "Vendor Category", "Assigned To",
        "Address Line 1", "Address Line 2", "City", "State", "Country", "Pincode",
        "Contact Person", "Mobile Number", "Email 1", "Email 2", "Email 3", "Website",
        "GST Number", "PAN Number",
        "Bank Name", "Account Number", "IFSC Code",
        "Payment Currency", "Credit Period", "Margin on MRP", "Status",
    ]
    lines = []
    for key in order:
        val = vendor_details.get(key, "")
        if val is None:
            continue
        val = str(val).strip()
        if val and val.upper() != "NA":
            lines.append(f"{key}: {val}")
    return "\n".join(lines) if lines else "(no details provided)"


# ── OTP login email ──
def send_otp_email(to_email, code):
    body = f"""Your one-time login code for the Vendor Onboarding Portal is:

    {code}

This code is valid for 5 minutes. Do not share it with anyone.

If you did not request this, please ignore this email.
"""
    _send([to_email], "Your Login Code - Vendor Onboarding Portal", body)


# ── 1) Vendor submitted → notify the assigned employee ──
def send_new_vendor_email(assigned_email, vendor_name, vendor_details):
    body = f"""Hello,

A new vendor has been submitted and assigned to you for review and approval.

Please log in to the Approver Portal to review the details and documents.

--------------------------------------------------
VENDOR DETAILS
--------------------------------------------------
{_details_block(vendor_details)}
--------------------------------------------------

This is an automated message from the Vendor Onboarding Portal.
"""
    _send([assigned_email], f"New Vendor Assigned to You: {vendor_name}", body)


# ── 2) Rejected / Pending → notify vendor ──
def send_vendor_status_email(vendor_email, vendor_name, status, remarks):
    if status == "Rejected":
        subject = f"Vendor Application Update: {vendor_name} - Rejected"
        intro = "We regret to inform you that your vendor onboarding application has been rejected."
        detail = f"Reason: {remarks}" if remarks else ""
    elif status == "Pending Documents":
        subject = f"Vendor Application Update: {vendor_name} - Documents Required"
        intro = "Your vendor onboarding application requires additional documents before it can proceed."
        detail = f"Documents required: {remarks}" if remarks else ""
    else:
        subject = f"Vendor Application Update: {vendor_name}"
        intro = f"Your vendor application status has been updated to: {status}."
        detail = remarks or ""
    body = f"""Hello,

{intro}

{detail}

This is an automated message from the Vendor Onboarding Portal.
"""
    _send([vendor_email], subject, body)


# ── 3) Accepted → notify vendor + finance ──
def send_accepted_email(vendor_email, finance_emails, approver_email, vendor_name, vendor_details):
    vendor_body = f"""Hello,

Good news! Your vendor onboarding application for "{vendor_name}" has been ACCEPTED after review.

Our Finance team will now create your vendor code in SAP. You will receive
another email with your vendor code once it is ready.

This is an automated message from the Vendor Onboarding Portal.
"""
    _send([vendor_email], f"Application Accepted: {vendor_name}", vendor_body)

    recipients = list(finance_emails) + ([approver_email] if approver_email else [])
    team_body = f"""Hello,

The vendor below has been ACCEPTED and is ready for vendor code creation in SAP.

--------------------------------------------------
VENDOR DETAILS
--------------------------------------------------
{_details_block(vendor_details)}
--------------------------------------------------
Approved by: {approver_email or '(unknown)'}

Finance team: please create the vendor in SAP and enter the vendor code in the
Approver Portal (Finance view) to notify the vendor.

This is an automated message from the Vendor Onboarding Portal.
"""
    _send(recipients, f"Vendor Accepted - Create SAP Code: {vendor_name}", team_body)


# ── 4) Finance created code → notify vendor ──
def send_code_created_email(vendor_email, vendor_name, vendor_code, finance_email):
    body = f"""Hello,

Good news! Your vendor onboarding is complete.

Vendor Name: {vendor_name}
Vendor Code: {vendor_code}

Created by: {finance_email or 'Finance Team'}

You can now use this vendor code for all future transactions.

This is an automated message from the Vendor Onboarding Portal.
"""
    _send([vendor_email], f"Vendor Code Created: {vendor_name}", body)


# ── 0) Vendor submitted → confirmation to the vendor ──
def send_submission_confirmation(vendor_email, vendor_name, vendor_details):
    from datetime import datetime
    submitted_on = datetime.now().strftime("%d %B %Y, %I:%M %p")
    body = f"""Hello,

Thank you for submitting your vendor onboarding application.

This email confirms that we have received your application. Please keep this
email for your records as proof of submission.

--------------------------------------------------
Vendor Name: {vendor_name}
Submitted On: {submitted_on}
Current Status: Pending Review
--------------------------------------------------

Your application is now under review. You will receive further updates by email
as it progresses.

This is an automated message from the Vendor Onboarding Portal.
"""
    _send([vendor_email], f"Application Received: {vendor_name}", body)


# ── Re-upload → notify the assigned approver ──
def send_reupload_email(assigned_email, vendor_name, new_docs_list):
    docs_text = "\n".join(f"- {d}" for d in new_docs_list) if new_docs_list else "- (documents)"
    body = f"""Hello,

The vendor "{vendor_name}" has re-uploaded the requested documents and the
application is ready for your review again.

Newly uploaded:
{docs_text}

Please log in to the Approver Portal to review.

This is an automated message from the Vendor Onboarding Portal.
"""
    _send([assigned_email], f"Documents Re-uploaded: {vendor_name}", body)


# ── Finance rejected / asked for documents → vendor + approver + finance ──
def send_finance_decision_email(vendor_email, approver_email, finance_email,
                                vendor_name, decision, remarks):
    """
    Finance is a second gate. When they reject or ask for documents, everyone
    involved is told: the vendor, the approver who originally passed it, and
    the finance person who made the call.
    """
    if decision == "Rejected":
        subject = f"Application Rejected at Finance Review: {vendor_name}"
        headline = ("This application was rejected during finance review, "
                    "after having passed the initial approval.")
    else:  # Pending Documents
        subject = f"Further Documents Required: {vendor_name}"
        headline = ("Finance has requested additional documents before the "
                    "vendor code can be created.")

    body = f"""Hello,

{headline}

--------------------------------------------------
Vendor: {vendor_name}
Decision: {decision}
Reason: {remarks or '(none given)'}
Reviewed by (Finance): {finance_email}
--------------------------------------------------

Vendor: please upload the requested documents through the portal's
Re-upload Documents page. The application will return to Finance for review.

This is an automated message from the Vendor Onboarding Portal.
"""
    _send([vendor_email, approver_email, finance_email], subject, body)