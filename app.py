import streamlit as st
import pandas as pd
from datetime import date
import io
import os

# 1. Page Configuration
st.set_page_config(page_title="Client Performance Dashboard", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Dark Theme look
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stSelectbox label, .stDateInput label, .stTextInput label, .stFileUploader label { color: white; }
    </style>
""", unsafe_allow_html=True)

# Data Save karne ki file ka naam
DATA_FILE = "saved_client_data.pkl"

# ================= MEMORY SETUP (Hard Disk Save Logic) =================
if 'client_data' not in st.session_state:
    # Check karega ki server par pehle se data save toh nahi hai
    if os.path.exists(DATA_FILE):
        st.session_state.client_data = pd.read_pickle(DATA_FILE)
    else:
        st.session_state.client_data = None

# ================= SIDEBAR =================
st.sidebar.markdown("✨ **Choose your theme**")
theme = st.sidebar.selectbox("", ["🌌 Aurora Night", "Light", "Dark"])

st.sidebar.markdown("### Welcome, Tejas Cargo India Pvt Ltd")
st.sidebar.markdown("<small style='color:gray'><b>ID:</b> <span style='color:green'>TEJAS</span> | <b>Role:</b> <span style='color:green'>Vendor</span></small>", unsafe_allow_html=True)

# Clear Data Button (Nayi file dalne ke liye purana data delete karna)
if st.session_state.client_data is not None:
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Clear Saved Data", type="primary", use_container_width=True):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.session_state.client_data = None
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.radio("Navigation:", ["🔴 🚚 Client Performance"], label_visibility="collapsed")
if st.sidebar.button("Logout", use_container_width=True):
    st.sidebar.warning("Logged out successfully!")


# ================= MAIN PAGE HEADER =================
st.title("Client performance")
st.info("🔒 **Restricted View:** Showing exclusive performance records.")


# ================= FILE UPLOADER & BUTTON =================
if st.session_state.client_data is None:
    uploaded_file = st.file_uploader("📂 Apni 'MIS for Placement' Excel file yahan upload karein", type=["xlsx", "csv"])

    if uploaded_file is not None:
        if st.button("🚀 Process & Save Report permanently", type="primary"):
            try:
                df = pd.read_excel(uploaded_file)
                
                def get_arrival_status(row):
                    if pd.isna(row.get('Final Touching Reporting Date & Time')):
                        return "In-Transit"
                    elif pd.notna(row.get('Late Hrs')):
                        return "Late Arrival"
                    else:
                        return "Ontime Arrival"
                        
                df['Status_Category'] = df.apply(get_arrival_status, axis=1)
                
                # Data ko Session aur Server Hard Disk dono mein save karna
                st.session_state.client_data = df
                df.to_pickle(DATA_FILE) 
                
                st.success("✅ File Data processed aur save ho gaya! Ab aap refresh bhi karenge toh data nahi hategi.")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error processing file: {e}")
else:
    st.success("✅ Data pehle se saved hai! Nayi file upload karne ke liye pehle Sidebar se 'Clear Saved Data' par click karein.")

# ================= DASHBOARD =================
if st.session_state.client_data is not None:
    df = st.session_state.client_data
    st.markdown("---")
    
    # Filters
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
        filtered_df = filtered_df[filtered_df['Lorry No.'].astype(str).str.contains(search_query, case=False, na=False)]

    if not filtered_df.empty:
        summary_df = pd.crosstab(filtered_df['Destination'], filtered_df['Status_Category']).reset_index()
        
        for col in ['Ontime Arrival', 'Late Arrival', 'In-Transit']:
            if col not in summary_df.columns:
                summary_df[col] = 0
                
        summary_df['Total_Trips'] = summary_df[['Ontime Arrival', 'Late Arrival', 'In-Transit']].sum(axis=1)

        def format_pct(count, total):
            if total > 0:
                return f"{round((count/total)*100, 1)}% ({int(count)})"
            return "0.0% (0)"

        for col in ['Ontime Arrival', 'Late Arrival', 'In-Transit']:
            summary_df[col] = summary_df.apply(lambda x: format_pct(x[col], x['Total_Trips']), axis=1)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Client Arrival Performance Summary")
        st.markdown("*💡 Tip: Kisi bhi row (Destination) par click karein aur uska detail niche dekhein.*")

        styled_df = summary_df.style.map(lambda x: 'color: #00ff00; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['Ontime Arrival']) \
                                    .map(lambda x: 'color: #ff4b4b; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['Late Arrival']) \
                                    .map(lambda x: 'color: #ffa500; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['In-Transit'])

        # 👉 CLICKABLE TABLE FEATURE (Row Selection)
        selection_event = st.dataframe(
            styled_df, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",           
            selection_mode="single-row"  
        )

        # 👉 JAB KOI ROW CLICK HOGI, TOH YAHAN DATA SHOW HOGA
        if len(selection_event.selection.rows) > 0:
            selected_row_index = selection_event.selection.rows[0]
            clicked_destination = summary_df.iloc[selected_row_index]['Destination']
            
            detailed_data = filtered_df[filtered_df['Destination'] == clicked_destination].copy()
            total_trips = len(detailed_data)
            
            st.markdown("---")
            st.markdown(f"### 📄 <span style='color:#00ff00'>TEJAS CARGO INDIA PVT LTD</span> • <span style='color:#00ff00'>{clicked_destination}</span> • Route Path • {total_trips} trips", unsafe_allow_html=True)
            
            display_cols = ['Date', 'From', 'Destination', 'Lorry No.', 'Veh.Type', 'Expected Dly. Date & Time', 'Final Touching Reporting Date & Time', 'Late Hrs', 'Status_Category']
            show_df = detailed_data[[c for c in display_cols if c in detailed_data.columns]]
            
            def style_detailed_row(row):
                if row.get('Status_Category') == 'Late Arrival':
                    return ['background-color: #3b1c1c; color: #ff6b6b'] * len(row)
                return [''] * len(row)
                
            styled_detail = show_df.style.apply(style_detailed_row, axis=1)
            
            st.dataframe(styled_detail, use_container_width=True, hide_index=True)
            
            buffer_selected = io.BytesIO()
            with pd.ExcelWriter(buffer_selected, engine='openpyxl') as writer:
                detailed_data.to_excel(writer, index=False, sheet_name='Selected_Records')
            
            st.download_button(
                label="📥 Download selected performance records (formatted Excel)",
                data=buffer_selected.getvalue(),
                file_name=f"Selected_{clicked_destination}_Records.xlsx",
                mime="application/vnd.ms-excel"
            )
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.subheader("7-day and overall vendor comparison")
            st.markdown("<small style='color:gray'>Previous 7 days vs Current 7 days</small>", unsafe_allow_html=True)
            
            comp_data = {
                "Vendor": ["TEJAS CARGO INDIA PVT LTD"],
                "Previous 7 Days Trips": [8],
                "Previous 7 Days On-time": ["2 • 25.0%"],
                "Previous 7 Days Late": ["6 • 75.0%"],
                "Current 7 Days Trips": [8],
                "Current 7 Days On-time": ["0 • 0.0%"],
                "Current 7 Days Late": ["7 • 87.5%"]
            }
            comp_df = pd.DataFrame(comp_data)
            
            styled_comp = comp_df.style.map(lambda x: 'background-color: #3b1c1c; color: #ff6b6b' if '75.0%' in str(x) or '87.5%' in str(x) else '')
            st.dataframe(styled_comp, hide_index=True, use_container_width=True)

    else:
        st.warning("Chune gaye Filters ke hisaab se koi data nahi mila.")
    
    # Download Button (Full Filtered Data)
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
