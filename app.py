import streamlit as st
import pandas as pd
from datetime import date, datetime

# 1. Page Configuration (Wide layout dark theme ke liye)
st.set_page_config(page_title="Vendor Performance Dashboard", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Dark Theme look
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stSelectbox label, .stDateInput label, .stTextInput label { color: white; }
    </style>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
st.sidebar.markdown("✨ **Choose your theme**")
theme = st.sidebar.selectbox("", ["🌌 Aurora Night", "Light", "Dark"])

st.sidebar.markdown("### Welcome, Tejas Cargo India Pvt Ltd")
st.sidebar.markdown("<small style='color:gray'><b>ID:</b> <span style='color:green'>TEJAS</span> | <b>Role:</b> <span style='color:green'>Vendor</span></small>", unsafe_allow_html=True)

if st.sidebar.button("Logout", use_container_width=True):
    st.sidebar.warning("Logged out successfully!")

st.sidebar.markdown("---")
st.sidebar.markdown("Navigation:")
st.sidebar.radio("", ["🔴 🚚 Vendor Performance"], label_visibility="collapsed")

# ================= MAIN PAGE HEADER =================
st.title("Vendor Performance (Routewise/Legwise)")

# Info Box (Restricted View)
st.info("🔒 **Restricted Vendor View:** Showing exclusive performance records for TEJAS CARGO INDIA PVT LTD, TEJAS")

# ================= FILTERS SECTION =================
# Date Filters
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    start_date = st.date_input("🗓️ Start Date (MCD_StartDate):", date(2026, 10, 1))
with c2:
    end_date = st.date_input("🗓️ End Date (MCD_StartDate):", date(2026, 10, 18))
with c3:
    # Duration Calculation
    duration = (end_date - start_date).days
    start_str = start_date.strftime("%d %b %Y")
    end_str = end_date.strftime("%d %b %Y")
    st.markdown("<br>", unsafe_allow_html=True)
    st.info(f"⏱️ **Selected Duration:** {start_str} to {end_str} ({duration} Days)")

# Dropdown Filters
f1, f2, f3, f4 = st.columns(4)
with f1:
    zone_filter = st.selectbox("Filter by Zone:", ["ALL"])
with f2:
    ro_filter = st.selectbox("Filter by RO:", ["ALL", "DELRO", "MUMRO"])
with f3:
    vendor_filter = st.selectbox("Filter by Vendor:", ["ALL"])
with f4:
    search_query = st.text_input("🔍 Quick Search:", placeholder="Search Route, Leg...")

# Download Button
st.download_button(
    label="📊 Download Filtered Vendor Performance Report (Styled Excel)",
    data="dummy data",
    file_name="Vendor_Report.csv",
    mime="text/csv",
    type="primary"
)

st.markdown("<br>", unsafe_allow_html=True)

# ================= DATA TABLE SECTION =================
st.subheader("Vendor Arrival Performance Summary")

# Dummy Data matching the image exactly
data = {
    "Select": [False, False, False, False],
    "Origin RO": ["MUMRO", "DELRO", "DELRO", "DELRO"],
    "Route Path": ["BWNDLH-DELAP", "DELAP-BKLH-BWNDLH", "DELAP-BKLH-BWNDLH", "DELAP-BWNDLH"],
    "Legwise": ["Leg1", "Leg1", "Leg2", "Leg1"],
    "Legs": ["BWNDLH to DELAP", "DELAP to BKLH", "BKLH to BWNDLH", "DELAP to BWNDLH"],
    "VendorName": ["TEJAS CARGO INDIA PVT LTD", "TEJAS CARGO INDIA PVT LTD", "TEJAS CARGO INDIA PVT LTD", "TEJAS CARGO INDIA PVT LTD"],
    "Total_Trips": [11, 10, 9, 1],
    "Ontime Arrival": ["18.2% (2)", "0.0% (0)", "33.3% (3)", "0.0% (0)"],
    "Late Arrival": ["72.7% (8)", "90.0% (9)", "66.7% (6)", "100.0% (1)"],
    "In-Transit": ["9.1% (1)", "10.0% (1)", "0.0% (0)", "0.0% (0)"]
}

df = pd.DataFrame(data)

# Table Styling Logic (Green for Ontime, Red for Late, Orange/Yellow for In-Transit)
def highlight_status(val):
    if isinstance(val, str) and '%' in val:
        num = float(val.split('%')[0])
        if num > 0:
            if 'Ontime' in val or float(val.split('%')[0]) == 18.2 or float(val.split('%')[0]) == 33.3: # Hack for demo
                return 'color: #00ff00; font-weight: bold' # Green
            elif 'Late' in val or float(val.split('%')[0]) > 60:
                return 'color: #ff4b4b; font-weight: bold' # Red
            else:
                return 'color: #ffa500; font-weight: bold' # Orange
    return ''

# Applying style only to specific columns to match image
styled_df = df.style.applymap(lambda x: 'color: #00ff00; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['Ontime Arrival']) \
                    .applymap(lambda x: 'color: #ff4b4b; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['Late Arrival']) \
                    .applymap(lambda x: 'color: #ffa500; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['In-Transit'])

# Displaying the styled dataframe
st.dataframe(styled_df, use_container_width=True, hide_index=False)
