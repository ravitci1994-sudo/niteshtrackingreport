import streamlit as st
import pandas as pd
from datetime import date, datetime
import io
import os
import urllib.parse

# 1. Page Configuration
st.set_page_config(page_title="Vendor Performance Dashboard", layout="wide", initial_sidebar_state="expanded")

DATA_FILE = "saved_vendor_data.pkl"

# Helper function to process data columns safely and flexibly
def process_dataframe(df):
    df.columns = df.columns.str.strip()
    
    ro_col = next((c for c in df.columns if 'ro' in c.lower() or 'origin' in c.lower() or 'from' in c.lower()), None)
    df['Origin RO'] = df[ro_col].astype(str).str.strip() if ro_col else "DELRO"
    
    from_c = next((c for c in df.columns if 'from' in c.lower() or 'origin' in c.lower()), None)
    dest_c = next((c for c in df.columns if 'dest' in c.lower() or 'to' in c.lower()), None)
    if from_c and dest_c:
        df['Route Path'] = df[from_c].astype(str).str.strip().str.upper() + "-" + df[dest_c].astype(str).str.strip().str.upper()
    else:
        df['Route Path'] = "BWNDLH-DELAP"

    if 'Legwise' not in df.columns:
        df['Legwise'] = "Leg1"
    
    if 'Legs' not in df.columns:
        df['Legs'] = df['Route Path']

    vendor_c = next((c for c in df.columns if 'vendor' in c.lower() or 'party' in c.lower() or 'client' in c.lower()), None)
    df['VendorName'] = df[vendor_c].astype(str).str.strip() if vendor_c else "TEJAS CARGO INDIA PVT LTD"

    def get_arrival_status(row):
        final_rep = row.get('Final Touching Reporting Date & Time') or row.get('Reporting Date') or row.get('Reporting Date & Time')
        exp_dly = row.get('Expected Dly. Date & Time') or row.get('Expected Date')
        
        if pd.notna(final_rep):
            if pd.notna(row.get('Late Hrs')):
                return "Late Arrival"
            else:
                return "Ontime Arrival"
        else:
            try:
                if pd.notna(exp_dly):
                    exp_dt = pd.to_datetime(exp_dly)
                    current_time = datetime.now()
                    if current_time > exp_dt:
                        return "Running Delay"
            except:
                pass
            return "In-Transit"
            
    df['Status_Category'] = df.apply(get_arrival_status, axis=1)
    return df

# ================= MEMORY SETUP =================
if 'vendor_data' not in st.session_state:
    if os.path.exists(DATA_FILE):
        try:
            df_loaded = pd.read_pickle(DATA_FILE)
            st.session_state.vendor_data = process_dataframe(df_loaded)
        except:
            st.session_state.vendor_data = None
    else:
        st.session_state.vendor_data = None

# ================= SIDEBAR =================
st.sidebar.markdown("### Welcome, Tejas Cargo India Pvt Ltd")
st.sidebar.markdown("<small style='color:gray'><b>ID:</b> <span style='color:green'>TEJAS</span> | <b>Role:</b> <span style='color:green'>Vendor</span></small>", unsafe_allow_html=True)

st.sidebar.markdown("---")

# Sidebar File Uploader
st.sidebar.markdown("📂 **Upload Vendor MIS Files**")
uploaded_files = st.sidebar.file_uploader(
    "Choose Excel/CSV files", 
    type=["xlsx", "csv"], 
    accept_multiple_files=True,
    label_visibility="collapsed"
)

# Process Data Button in Sidebar
if st.sidebar.button("🚀 Process Data", type="primary", use_container_width=True):
    if uploaded_files:
        try:
            df_list = []
            for uploaded_file in uploaded_files:
                if uploaded_file.name.endswith('.csv'):
                    temp_df = pd.read_csv(uploaded_file)
                else:
                    temp_df = pd.read_excel(uploaded_file)
                df_list.append(temp_df)
            
            df = pd.concat(df_list, ignore_index=True)
            df = process_dataframe(df)
            
            st.session_state.vendor_data = df
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            df.to_pickle(DATA_FILE) 
            
            st.sidebar.success("✅ Data successfully processed!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
    else:
        if st.session_state.vendor_data is None:
            st.sidebar.warning("⚠️ Pehle koi file upload karein!")

st.sidebar.markdown("---")

if st.sidebar.button("🔄 REFRESH / CLEAR DATA", use_container_width=True):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    st.session_state.vendor_data = None
    st.rerun()

st.sidebar.markdown("Navigation:")
selected_nav = st.sidebar.radio("", [
    "📊 Vendor Performance (Routewise/Legwise)",
    "🚚 Operations Summary",
    "💳 Payment Dashboard",
    "📱 Communication Hub",
    "💰 Network Utilization",
    "📝 Today's Call Action Plan",
    "🔐 User & Access Control"
], label_visibility="collapsed")

st.sidebar.markdown("---")
if st.sidebar.button("Logout", use_container_width=True):
    st.sidebar.warning("Logged out successfully!")


# ================= MAIN PAGE LOGIC =================
if selected_nav in ["📊 Vendor Performance (Routewise/Legwise)", "🚚 Operations Summary"]:
    st.title("Vendor Performance (Routewise/Legwise)")
    st.info("🔒 **Restricted Vendor View:** Showing exclusive performance records for TEJAS CARGO INDIA PVT LTD, TEJAS")

    # ================= DASHBOARD =================
    if st.session_state.vendor_data is not None:
        df = st.session_state.vendor_data
        st.markdown("---")
        
        # Date & Duration Row
        d1, d2, d3 = st.columns([1, 1, 2])
        with d1:
            start_date = st.date_input("🗓️ Start Date (MCD_StartDate):", date(2026, 10, 1))
        with d2:
            end_date = st.date_input("🗓️ End Date (MCD_EndDate):", date(2026, 10, 18))
        with d3:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info(f"⏱️ **Selected Duration:** 01 Oct 2026 to 18 Oct 2026 ({(end_date - start_date).days + 1} Days)")
            
        # ================= SEARCH / DROPDOWNS =================
        f1, f2, f3, f4 = st.columns(4)
        
        zone_col = next((c for c in df.columns if 'zone' in c.lower()), None)
        with f1:
            zone_list = ["ALL", "North", "East", "West", "South"]
            zone_filter = st.selectbox("Search by Zone:", zone_list)
            
        zone_filtered_df = df.copy()
        if zone_filter != "ALL" and zone_col and zone_col in df.columns:
            zone_filtered_df = zone_filtered_df[zone_filtered_df[zone_col] == zone_filter]

        ro_col = next((c for c in df.columns if 'ro' in c.lower() or 'origin' in c.lower()), None)
        with f2:
            ro_list = ["ALL"] + list(zone_filtered_df[ro_col].dropna().unique()) if ro_col else ["ALL"]
            ro_filter = st.selectbox("Search by RO:", ro_list)
            
        ro_filtered_df = zone_filtered_df.copy()
        if ro_filter != "ALL" and ro_col:
            ro_filtered_df = ro_filtered_df[ro_filtered_df[ro_col] == ro_filter]

        vendor_col = next((c for c in df.columns if 'vendor' in c.lower() or 'party' in c.lower() or 'client' in c.lower()), None)
        with f3:
            vendor_list = ["ALL"] + list(ro_filtered_df[vendor_col].dropna().unique()) if vendor_col else ["ALL"]
            vendor_filter = st.selectbox("Search by Vendor:", vendor_list)

        vendor_filtered_df = ro_filtered_df.copy()
        if vendor_filter != "ALL" and vendor_col:
            vendor_filtered_df = vendor_filtered_df[vendor_filtered_df[vendor_col] == vendor_filter]

        lorry_col = next((c for c in df.columns if 'lorry' in c.lower() or 'vehicle' in c.lower() or 'truck' in c.lower()), None)
        with f4:
            search_vehicle = st.text_input("🔍 Search by Vehicle No:", placeholder="Enter Vehicle No...")
            
        filtered_df = vendor_filtered_df.copy()
        if search_vehicle and lorry_col:
            filtered_df = filtered_df[filtered_df[lorry_col].astype(str).str.contains(search_vehicle, case=False, na=False)]
        
        if filtered_df.empty:
            filtered_df = df.copy()

        if not filtered_df.empty:
            group_cols = ['Origin RO', 'Route Path', 'Legwise', 'Legs', 'VendorName']
            summary_df = filtered_df.groupby(group_cols)['Status_Category'].value_counts().unstack(fill_value=0).reset_index()
            
            for col in ['Ontime Arrival', 'Late Arrival', 'In-Transit', 'Running Delay']:
                if col not in summary_df.columns:
                    summary_df[col] = 0
                    
            summary_df['Total_Trips'] = summary_df[['Ontime Arrival', 'Late Arrival', 'In-Transit', 'Running Delay']].sum(axis=1)

            def format_pct(count, total):
                if total > 0:
                    return f"{round((count/total)*100, 1)}% ({int(count)})"
                return "0.0% (0)"

            summary_df['Ontime Arrival_fmt'] = summary_df.apply(lambda x: format_pct(x['Ontime Arrival'], x['Total_Trips']), axis=1)
            summary_df['Late Arrival_fmt'] = summary_df.apply(lambda x: format_pct(x['Late Arrival'] + x['Running Delay'], x['Total_Trips']), axis=1)
            summary_df['In-Transit_fmt'] = summary_df.apply(lambda x: format_pct(x['In-Transit'], x['Total_Trips']), axis=1)

            final_summary = summary_df[['Origin RO', 'Route Path', 'Legwise', 'Legs', 'VendorName', 'Total_Trips', 'Ontime Arrival_fmt', 'Late Arrival_fmt', 'In-Transit_fmt']]
            final_summary.columns = ['Origin RO', 'Route Path', 'Legwise', 'Legs', 'VendorName', 'Total_Trips', 'Ontime Arrival', 'Late Arrival', 'In-Transit']

            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("Vendor Arrival Performance Summary")
            st.markdown("<small style='color:gray'>Click any trip count or performance rate to see the matching trip records.</small>", unsafe_allow_html=True)

            styled_df = final_summary.style.map(lambda x: 'color: #00ff00; font-weight: bold' if '0.0%' not in str(x) and '(' in str(x) else 'color: gray', subset=['Ontime Arrival']) \
                                           .map(lambda x: 'background-color: #3b1c1c; color: #ff6b6b; font-weight: bold' if '0.0%' not in str(x) and '0%' not in str(x) else '', subset=['Late Arrival']) \
                                           .map(lambda x: 'background-color: #3b2a1a; color: #ffa500; font-weight: bold' if '0.0%' not in str(x) and '0%' not in str(x) else '', subset=['In-Transit'])

            selection_event = st.dataframe(
                styled_df, 
                use_container_width=True, 
                hide_index=True,
                on_select="rerun",            
                selection_mode="single-row"  
            )

            st.markdown("<br>", unsafe_allow_html=True)
            
            # ================= 3 STATUS BUTTONS WITH COUNTS =================
            total_count = len(filtered_df)
            transit_count = len(filtered_df[filtered_df['Status_Category'] == 'In-Transit'])
            running_delay_count = len(filtered_df[filtered_df['Status_Category'] == 'Running Delay'])

            st.markdown("🚦 **Status Filters:**")
            status_filter = st.radio(
                "Filter Status:",
                [
                    f"All Data ({total_count})", 
                    f"In-Transit Vehicle ({transit_count})", 
                    f"Running Delay ({running_delay_count})"
                ],
                horizontal=True,
                label_visibility="collapsed"
            )

            display_detail_df = filtered_df.copy()
            if "In-Transit Vehicle" in status_filter:
                display_detail_df = display_detail_df[display_detail_df['Status_Category'] == 'In-Transit']
            elif "Running Delay" in status_filter:
                display_detail_df = display_detail_df[display_detail_df['Status_Category'] == 'Running Delay']

            st.markdown(f"### 📄 Trip Records ({status_filter})")
            if not display_detail_df.empty:
                st.dataframe(display_detail_df, use_container_width=True, hide_index=True)
            else:
                st.warning("Is status category mein koi data nahi hai.")

            st.markdown("<br>", unsafe_allow_html=True)
            buffer_excel = io.BytesIO()
            with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='Vendor_Performance_Report')
            
            st.download_button(
                label="📥 Download Filtered Vendor Performance Report (Styled Excel)",
                data=buffer_excel.getvalue(),
                file_name="Filtered_Vendor_Performance_Report.xlsx",
                mime="application/vnd.ms-excel",
                type="primary"
            )

            # ================= LAST 7 DAYS PERFORMANCE DATA =================
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.subheader("📍 Last 7 Days Route-wise Performance Data")
            st.markdown("<small style='color:gray'>Pichle 7 dino ka performance summary data</small>", unsafe_allow_html=True)
            
            last_week_df = filtered_df.copy()
            date_col = next((c for c in last_week_df.columns if 'date' in c.lower()), None)
            if date_col:
                try:
                    last_week_df['Temp_Date'] = pd.to_datetime(last_week_df[date_col], errors='coerce').dt.date
                    last_7_days_start = end_date - pd.Timedelta(days=7)
                    last_week_df = last_week_df[(last_week_df['Temp_Date'] > last_7_days_start) & (last_week_df['Temp_Date'] <= end_date)]
                except:
                    pass
            
            if not last_week_df.empty:
                week_summary = last_week_df.groupby('Route Path')['Status_Category'].value_counts().unstack(fill_value=0).reset_index()
                for col in ['Ontime Arrival', 'Late Arrival', 'In-Transit', 'Running Delay']:
                    if col not in week_summary.columns:
                        week_summary[col] = 0
                week_summary['Total_Trips'] = week_summary[['Ontime Arrival', 'Late Arrival', 'In-Transit', 'Running Delay']].sum(axis=1)
                st.dataframe(week_summary, use_container_width=True, hide_index=True)
            else:
                st.warning("Pichle 7 dino ka koi data available nahi hai.")

        else:
            st.warning("⚠️ Upload ki gayi file mein data nahi mila ya format galat hai.")
    else:
        st.info("👈 Kripya Sidebar se apni file upload karein aur 'Process Data' button par click karein.")
else:
    st.title(selected_nav)
    st.info("🚧 Yeh page abhi ban raha hai (Work in Progress).")
