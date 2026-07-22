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


# ─────────────────────────────────────────────
#  SEQUENTIAL ID  (VFY27001 / CFY27001)
# ─────────────────────────────────────────────
def _financial_year_label(when=None):
    """
    Indian financial year runs April to March, labelled by the ENDING year.
    Apr 2026 - Mar 2027  ->  FY27
    Apr 2027 - Mar 2028  ->  FY28
    """
    from datetime import datetime
    d = when or datetime.now()
    end_year = d.year + 1 if d.month >= 4 else d.year
    return f"FY{str(end_year)[-2:]}"


def next_party_id(party_type):
    """
    Return the next sequential ID, e.g. 'VFY27001' or 'CFY27001'.

    The counter never resets — it keeps climbing across financial years, so the
    number shows how many have been onboarded in total. Only the FY part changes.
    """
    from pymongo import ReturnDocument

    prefix = "V" if party_type == "Vendor" else "C"
    fy = _financial_year_label()

    counters = _get_db()["counters"]
    doc = counters.find_one_and_update(
        {"_id": f"{prefix}_seq"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    n = doc.get("value", 1)
    return f"{prefix}{fy}{n:03d}"


# ─────────────────────────────────────────────
#  DUPLICATE DETECTION  (PAN / GST)
# ─────────────────────────────────────────────
def check_duplicates(party_name, pan_number, gst_number):
    """
    Look for existing records sharing this PAN or GST.

    Returns:
      exact       -> True when name + PAN + GST all match an existing record
      pan_matches -> list of existing names sharing this PAN
      gst_matches -> list of existing names sharing this GST
    """
    result = {"exact": False, "pan_matches": [], "gst_matches": []}

    name = (party_name or "").strip().lower()
    pan  = (pan_number or "").strip().upper()
    gst  = (gst_number or "").strip().upper()

    for rec in _vendors().find({}, {"_id": 0, "Vendor Name": 1,
                                    "PAN Number": 1, "GST Number": 1}):
        r_name = str(rec.get("Vendor Name", "")).strip().lower()
        r_pan  = str(rec.get("PAN Number", "")).strip().upper()
        r_gst  = str(rec.get("GST Number", "")).strip().upper()

        pan_hit = bool(pan) and pan != "NA" and r_pan == pan
        gst_hit = bool(gst) and gst != "NA" and r_gst == gst

        if r_name == name and pan_hit and gst_hit:
            result["exact"] = True

        if pan_hit and r_name != name:
            result["pan_matches"].append(rec.get("Vendor Name", ""))
        if gst_hit and r_name != name:
            result["gst_matches"].append(rec.get("Vendor Name", ""))

    return result


def find_duplicate_pans():
    """
    Return {pan: [records...]} for every PAN used by more than one record.
    Used by the finance duplicate-PAN table.
    """
    by_pan = {}
    for rec in _vendors().find({}, {"_id": 0, "Vendor Name": 1, "PAN Number": 1,
                                    "Party ID": 1, "Party Type": 1, "Status": 1,
                                    "Submitted On": 1}):
        pan = str(rec.get("PAN Number", "")).strip().upper()
        if not pan or pan == "NA":
            continue
        by_pan.setdefault(pan, []).append(rec)

    return {pan: recs for pan, recs in by_pan.items() if len(recs) > 1}