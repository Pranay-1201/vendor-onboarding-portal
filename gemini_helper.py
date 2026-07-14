import os
import time
import random
import re
from google import genai
from google.genai import types


def _get_api_key():
    try:
        import streamlit as st
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.environ["GEMINI_API_KEY"]


VENDOR_RISK_PROMPT = """You are a Vendor Risk Assessment Assistant for vendor onboarding.
Analyze this company using publicly available information. Search across:
court cases, NCLT, insolvency/bankruptcy, GST/tax disputes, MCA compliance,
director disqualifications, director changes, environmental/labor violations,
fraud allegations, regulatory penalties, and negative news (last 5 years).

Company Name: {company_name}
Address: {company_address}
GST Number: {gst_number}

CRITICAL RULES:
- Output the section markers below EXACTLY as written, each on its own line.
- NEVER repeat a sentence or phrase. Write each point once.
- Do NOT use markdown tables anywhere. Use bullet points only.

===SCORECARD===
Output these fields, one per line, EXACTLY in this "Key: Value" format, nothing else:
RiskScore: <a number 0-100, where 100 = lowest risk / safest vendor>
Compliance: <Low/Medium/High>
Reputational: <Low/Medium/High>
Financial: <Low/Medium/High>
Operational: <Low/Medium/High>
YearsInBusiness: <integer number of years since incorporation, or Unknown>
CourtCases: <integer count of court cases/legal disputes found, or 0>
RedFlagCount: <integer count of material red flags, or 0>
OverallRisk: <Low/Medium/High>
Recommendation: <Approve / Approve with Conditions / Further Review Required / Reject>
Confidence: <High/Medium/Low>
Reason: <ONE sentence explaining the recommendation. No line breaks.>
Watch: <one short sentence: the single most important thing to verify. If nothing, write "Nothing significant.">

===SUMMARY===
Write nothing here. Leave this section empty.

===REDFLAGS===
List ONLY material red flags. For EACH, one line, this exact format:
- [Severity: High/Medium/Low] short description | Source: <full URL>
If a flag has no verifiable source, write "Source: not verified".
If none, write exactly: None found.

===DETAILS===
Full report using ONLY markdown headings and bullets (NO tables):

### Company Profile
- Legal Entity Name / Company Type / Industry / Registered Location /
  Year of Incorporation / Current Status / Key Directors (one bullet each).

### Key Findings
For each issue: - **Category** — summary (Date, Severity) — Source: <url>
If nothing found: "No significant publicly available information found."

### Risk Assessment
- **Compliance Risk:** Low/Med/High — one line
- **Reputational Risk:** Low/Med/High — one line
- **Financial Distress Risk:** Low/Med/High — one line
- **Operational Risk:** Low/Med/High — one line

### Due Diligence Recommendations
- **Strengths / Concerns / Recommended actions** as short bullets.

### Final Recommendation
One short paragraph: overall rating, confidence, decision, and why.
"""


def _split_sections(text: str) -> dict:
    out = {"scorecard": "", "summary": "", "redflags": "", "details": ""}
    cur = None
    buf = {k: [] for k in out}
    for line in text.splitlines():
        s = line.strip()
        if s == "===SCORECARD===":
            cur = "scorecard"; continue
        elif s == "===SUMMARY===":
            cur = "summary"; continue
        elif s == "===REDFLAGS===":
            cur = "redflags"; continue
        elif s == "===DETAILS===":
            cur = "details"; continue
        if cur:
            buf[cur].append(line)
    for k in out:
        out[k] = "\n".join(buf[k]).strip()
    if not any(out.values()):
        out["details"] = text.strip()
        out["summary"] = "The model did not return a structured summary. See the detailed report below."
    return out


def _parse_scorecard(block: str) -> dict:
    """Turn the SCORECARD lines into a dict."""
    fields = {}
    for line in block.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    return fields


def _dedupe_lines(text: str) -> str:
    cleaned, prev = [], None
    for line in text.splitlines():
        if line.strip() and line.strip() == prev:
            continue
        cleaned.append(line)
        prev = line.strip()
    return "\n".join(cleaned)


def analyze_vendor(company_name: str, company_address: str = "", gst_number: str = "") -> dict:
    client = genai.Client(api_key=_get_api_key())

    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        max_output_tokens=3000,
        temperature=0.3,
    )

    prompt = VENDOR_RISK_PROMPT.format(
        company_name=company_name or "N/A",
        company_address=company_address or "N/A",
        gst_number=gst_number or "N/A",
    )

    response = None
    last_err = None
    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )
            break
        except Exception as e:
            last_err = e
            msg = str(e)
            transient = any(c in msg for c in ("503", "UNAVAILABLE", "429", "overloaded", "500", "INTERNAL"))
            if transient and attempt < 3:
                time.sleep((2 ** attempt) + random.random())
                continue
            raise
    if response is None:
        raise last_err

    cleaned = _dedupe_lines(response.text)
    parsed = _split_sections(cleaned)
    parsed["scorecard_fields"] = _parse_scorecard(parsed.get("scorecard", ""))

    sources = []
    try:
        meta = response.candidates[0].grounding_metadata
        if meta and meta.grounding_chunks:
            seen = set()
            for chunk in meta.grounding_chunks:
                if chunk.web and chunk.web.uri not in seen:
                    seen.add(chunk.web.uri)
                    sources.append((chunk.web.title or chunk.web.uri, chunk.web.uri))
    except (AttributeError, IndexError):
        pass

    parsed["sources"] = sources
    parsed["source_count"] = len(sources)
    return parsed