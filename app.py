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
st.title("Client performance")
st.info("🔒 **Restricted View:** Showing exclusive performance records.")


# ================= MEMORY SETUP (Taki data na hate) =================
# Streamlit ko sikhana ki data yaad rakhe
if 'client_data' not in st.session_state:
    st.session_state.client_data = None


# ================= FILE UPLOADER & BUTTON =================
uploaded_file = st.file_uploader("📂 Apni 'MIS for Placement' Excel file yahan upload karein", type=["xlsx", "csv"])

# Button tabhi dikhega jab file upload hogi
if uploaded_file is not None:
    if st.button("🚀 Process & Show Report", type="primary"):
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
            
            # ✅ DATA KO MEMORY MEIN SAVE KARNA
            st.session_state.client_data = df
            st.success("✅ File Data processed successfully! Niche report dekhein.")
            
        except Exception as e:
            st.error(f"Error processing file: {e}")


# ================= DASHBOARD (Filters & Table) =================
# Agar data memory mein save ho chuka hai, tabhi dashboard dikhana
if st.session_state.client_data is not None:
    df = st.session_state.client_data

    st.markdown("---")
    
    # Filters Section
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

    # Apply Filters
    filtered_df = df.copy()
    if ro_filter != "ALL":
        filtered_df = filtered_df[filtered_df['From'] == ro_filter]
    if dest_filter != "ALL":
        filtered_df = filtered_df[filtered_df['Destination'] == dest_filter]
    if client_filter != "ALL":
        filtered_df = filtered_df[filtered_df['Party'] == client_filter]
    if search_query:
        # Search for Lorry Number
        filtered_df = filtered_df[filtered_df['Lorry No.'].astype(str).str.contains(search_query, case=False, na=False)]


    # Data Table (Colored Report)
    if not filtered_df.empty:
        summary_df = pd.crosstab(filtered_df['Destination'], filtered_df['Status_Category']).reset_index()
        
        # Ensure all columns exist
        for col in ['Ontime Arrival', 'Late Arrival', 'In-Transit']:
            if col not in summary_df.columns:
                summary_df[col] = 0
                
        summary_df['Total_Trips'] = summary_df[['Ontime Arrival', 'Late Arrival', 'In-Transit']].sum(axis=1)

        # Numbers ko Percentage format mein badalna
        def format_pct(count, total):
            if total > 0:
                return f"{round((count/total)*100, 1)}% ({int(count)})"
            return "0.0% (0)"

        for col in ['Ontime Arrival', 'Late Arrival', 'In-Transit']:
            summary_df[col] = summary_df.apply(lambda x: format_pct(x[col], x['Total_Trips']), axis=1)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Client Arrival Performance Summary")

        # Colored formatting using map
        styled_df = summary_df.style.map(lambda x: 'color: #00ff00; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['Ontime Arrival']) \
                                    .map(lambda x: 'color: #ff4b4b; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['Late Arrival']) \
                                    .map(lambda x: 'color: #ffa500; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['In-Transit'])

        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.warning("Chune gaye Filters ke hisaab se koi data nahi mila.")
    
    # Download Button (sirf filtered data ke sath)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='Filtered Client Report')
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        label="📊 Download Filtered Client Performance Report",
        data=buffer.getvalue(),
        file_name="Filtered_Client_Report.xlsx",
        mime="application/vnd.ms-excel",
        type="primary"
    )
elif uploaded_file is None:
    st.warning("⚠️ Please upload your 'MIS for Placement' Excel file to generate the dashboard.")
