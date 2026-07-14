"""
Database layer for the Vendor Onboarding Portal (MongoDB Atlas).

Collections:
  - vendors:  one document per vendor (all the form fields)
  - documents (GridFS): the uploaded files (PDFs/images)

The connection string is read from Streamlit secrets: MONGO_URI
"""

import streamlit as st
from pymongo import MongoClient
import gridfs


@st.cache_resource
def _get_db():
    """Connect once and reuse the connection across reruns."""
    uri = st.secrets["MONGO_URI"]
    client = MongoClient(uri)
    return client["vendor_portal"]      # database name


def _vendors():
    return _get_db()["vendors"]


def _fs():
    return gridfs.GridFS(_get_db())


# ─────────────────────────────────────────────
#  VENDOR RECORDS
# ─────────────────────────────────────────────
def vendor_exists(vendor_name, gst_number):
    return _vendors().find_one(
        {"Vendor Name": vendor_name, "GST Number": gst_number}
    ) is not None


def save_vendor(vendor_dict):
    """Insert a new vendor record."""
    _vendors().insert_one(vendor_dict)


def get_all_vendors():
    """Return all vendors as a list of dicts (without Mongo _id)."""
    return list(_vendors().find({}, {"_id": 0}))


def update_vendor(vendor_name, updates: dict):
    """Update fields for a vendor by name."""
    _vendors().update_one({"Vendor Name": vendor_name}, {"$set": updates})


# ─────────────────────────────────────────────
#  DOCUMENTS (GridFS)
# ─────────────────────────────────────────────
def save_document(vendor_name, doc_type, file_name, file_bytes):
    """Store one uploaded file, tagged with the vendor and doc type.
    The stored filename is 'vendor_name/file_name' so it reads like a folder."""
    _fs().put(
        file_bytes,
        filename=f"{vendor_name}/{file_name}",
        vendor_name=vendor_name,
        doc_type=doc_type,
        base_name=file_name,
    )


def list_documents(vendor_name):
    """Return [(doc_type, base_name), ...] for a vendor."""
    out = []
    for f in _fs().find({"vendor_name": vendor_name}):
        base = getattr(f, "base_name", f.filename)
        out.append((f.doc_type, base))
    return out


def get_document_bytes(vendor_name, file_name):
    """Return the raw bytes of one stored file (file_name is the base name)."""
    f = _fs().find_one({"vendor_name": vendor_name, "base_name": file_name})
    if not f:
        # fallback for older records stored by full path
        f = _fs().find_one({"filename": f"{vendor_name}/{file_name}"})
    return f.read() if f else None


# ─────────────────────────────────────────────
#  AI RISK REPORT (cached per vendor)
# ─────────────────────────────────────────────
def get_ai_report(vendor_name):
    """Return the saved AI report dict for a vendor, or None."""
    doc = _vendors().find_one(
        {"Vendor Name": vendor_name},
        {"_id": 0, "AI_Report": 1}
    )
    if doc and doc.get("AI_Report"):
        return doc["AI_Report"]
    return None


def save_ai_report(vendor_name, report: dict):
    """Save/overwrite the AI report for a vendor."""
    _vendors().update_one(
        {"Vendor Name": vendor_name},
        {"$set": {"AI_Report": report}}
    )


# ─────────────────────────────────────────────
#  FIND VENDOR (for re-upload)
# ─────────────────────────────────────────────
def find_vendor(vendor_name, gst_number):
    """Return a vendor dict matching name + GST, or None."""
    return _vendors().find_one(
        {"Vendor Name": vendor_name, "GST Number": gst_number},
        {"_id": 0}
    )
