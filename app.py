import streamlit as st
import pandas as pd
from datetime import date
import io

# 1. Page Configuration (Wide layout, Dark Theme)
st.set_page_config(page_title="Client Performance Dashboard", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Dark Theme look
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stSelectbox label, .stDateInput label, .stTextInput label, .stFileUploader label { color: white; }
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
st.sidebar.radio("Navigation:", ["🔴 🚚 Client Performance"], label_visibility="collapsed")


# ================= MAIN PAGE HEADER =================
# Aapke request ke hisaab se naya Title
st.title("Client performance")

st.info("🔒 **Restricted View:** Showing exclusive performance records.")


# ================= FILE UPLOADER =================
# Yahan se aap apni daily file upload kar payenge
uploaded_file = st.file_uploader("📂 Apni 'MIS for Placement' Excel file yahan upload karein", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        # File Data Padhna
        df = pd.read_excel(uploaded_file)
        
        # On-time aur Late calculate karne ka logic
        def get_arrival_status(row):
            if pd.isna(row.get('Final Touching Reporting Date & Time')):
                return "In-Transit"
            elif pd.notna(row.get('Late Hrs')):
                return "Late Arrival"
            else:
                return "Ontime Arrival"
                
        df['Status_Category'] = df.apply(get_arrival_status, axis=1)
        
        # ================= FILTERS SECTION =================
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            start_date = st.date_input("🗓️ Start Date:", date(2026, 10, 1))
        with c2:
            end_date = st.date_input("🗓️ End Date:", date(2026, 10, 18))
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info(f"⏱️ **Selected Duration:** {(end_date - start_date).days} Days")
            
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            ro_list = ["ALL"] + list(df['From'].dropna().unique()) if 'From' in df.columns else ["ALL"]
            ro_filter = st.selectbox("Filter by Origin:", ro_list)
        with f2:
            dest_list = ["ALL"] + list(df['Destination'].dropna().unique()) if 'Destination' in df.columns else ["ALL"]
            dest_filter = st.selectbox("Filter by Destination:", dest_list)
        with f3:
            client_list = ["ALL"] + list(df['Party'].dropna().unique()) if 'Party' in df.columns else ["ALL"]
            client_filter = st.selectbox("Filter by Client:", client_list)
        with f4:
            search_query = st.text_input("🔍 Quick Search:", placeholder="Search Lorry...")

        # ================= DATA TABLE (Colored Report) =================
        # Destination ke hisaab se On-Time aur Late Trips ko count karna
        summary_df = pd.crosstab(df['Destination'], df['Status_Category']).reset_index()
        summary_df['Total_Trips'] = summary_df.sum(axis=1, numeric_only=True)
        
        # Ensure all columns exist
        for col in ['Ontime Arrival', 'Late Arrival', 'In-Transit']:
            if col not in summary_df.columns:
                summary_df[col] = 0
                
        # Numbers ko Percentage aur Count Format (e.g. "18.2% (2)") mein badalna
        for col in ['Ontime Arrival', 'Late Arrival', 'In-Transit']:
            summary_df[col] = summary_df.apply(lambda x: f"{round((x[col]/x['Total_Trips'])*100, 1)}% ({int(x[col])})" if x['Total_Trips'] > 0 else "0.0% (0)", axis=1)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Client Arrival Performance Summary")

        # ERROR FIX: 'applymap' ki jagah 'map' ka use kiya gaya hai
        styled_df = summary_df.style.map(lambda x: 'color: #00ff00; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['Ontime Arrival']) \
                                    .map(lambda x: 'color: #ff4b4b; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['Late Arrival']) \
                                    .map(lambda x: 'color: #ffa500; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['In-Transit'])

        # Dataframe ko screen par dikhana
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Download Button
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Client Report')
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📊 Download Full Client Performance Report",
            data=buffer.getvalue(),
            file_name="Client_Report.xlsx",
            mime="application/vnd.ms-excel",
            type="primary"
        )

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    # Agar file upload nahi hui hai toh ye warning dikhegi
    st.warning("⚠️ Please upload your 'MIS for Placement' Excel file to generate the dashboard.")
