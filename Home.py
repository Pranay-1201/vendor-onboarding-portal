import streamlit as st

with open("styles/style.css") as f:
    st.markdown(
        f"<style>{f.read()}</style>",
        unsafe_allow_html=True
    )

st.set_page_config(
    page_title="onboarding portal",
    layout="wide"
)

# Hide Sidebar Navigation
st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div style="
padding:50px;
border-radius:55px;
background:linear-gradient(135deg,#4B0082,#7B2CBF);
color:white;
margin-bottom:20px;
">

<h1 style="font-size:55px;">
PLUM
</h1>

<h2>
Vendor & Customer Onboarding Portal
</h2>

<p style="font-size:20px;">
Streamline Onboarding, Compliance Verification
and Risk Assessment through a single platform.
</p>

</div>
""", unsafe_allow_html=True)

# Main Section
col1, col2 = st.columns([2,1])

with col1:

    st.markdown(
        "<h2 style='padding-left:20px;'>Welcome</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style='padding-left:20px;'>
        This portal enables vendors and customers to submit
        onboarding documents and allows internal teams to perform
        compliance verification, document review and
        approval.

        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)

# Three action cards
left, col1, gap1, col2, gap2, col3, right = st.columns([0.5, 6.5, 0.5, 6.5, 0.5, 6.5, 0.5])

with col1:
    st.markdown("""
    <div style="
    background:#E8F5E9;
    padding:20px;
    border-radius:35px;
    border-left:6px solid #4CAF50;
    min-height:120px;
    ">
    <h3>🏢 New Registration</h3>
    <p>Register vendors/customers and upload documents.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    if st.button("Register Vendor / Customer", use_container_width=True):
        st.switch_page("pages/1_Vendor_Portal.py")

with col2:
    st.markdown("""
    <div style="
    background:#FFF8E1;
    padding:20px;
    border-radius:35px;
    border-left:6px solid #FFB300;
    min-height:120px;
    ">
    <h3>📄 Re-upload Documents</h3>
    <p>Asked for more documents? Upload them here.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    if st.button("Re-upload Documents", use_container_width=True):
        st.switch_page("pages/4_Reupload_Documents.py")

with col3:
    st.markdown("""
    <div style="
    background:#E3F2FD;
    padding:20px;
    border-radius:35px;
    border-left:6px solid #2196F3;
    min-height:120px;
    ">
    <h3>🔐 Approver Portal</h3>
    <p>Review documents and approve applications.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    if st.button("Login as Approver", use_container_width=True):
        st.switch_page("pages/2_Approver_Login.py")

st.markdown("---")

st.info(
    "Please ensure all mandatory documents are uploaded for faster approval."
)


# Process Flow
st.markdown("## Onboarding Process")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
### 📄

**Upload Documents**

GST, PAN, Bank Details,
Compliance Certificates
""")

with col2:
    st.markdown("""
### 🔍

**Risk Assessment**

Review company profile,
compliance and history
""")

with col3:
    st.markdown("""
### ✅

**Approval Review**

Approver validates
all submitted documents
""")

with col4:
    st.markdown("""
### 🤝

**Onboarding Complete**

Approved partners
are created in the system
""")

st.markdown("---")

# Categories
st.markdown("## Supported Categories")

c1, c2, c3 = st.columns(3)

with c1:
    st.success("Raw Material Supplier")
    st.success("Packaging Supplier")
    st.info("Customer")

with c2:
    st.success("Logistics Provider")
    st.success("Warehouse Provider")

with c3:
    st.success("Contract Manufacturer")
    st.success("Service Provider")