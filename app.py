import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os

# 1. Page Configuration
st.set_page_config(page_title="Live Monitoring Dashboard", layout="wide", initial_sidebar_state="expanded")

DATA_FILE = "saved_vendor_data.pkl"

# Custom CSS for Dark Theme Executive Dashboard Styling
st.markdown("""
    <style>
    .main {
        background-color: #0b132b;
    }
    .metric-card {
        background-color: #1c2541;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #3a506b;
        margin-bottom: 15px;
        color: white;
    }
    .metric-title {
        font-size: 14px;
        color: #8d99ae;
        font-weight: 600;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 32px;
        color: #ffffff;
        font-weight: bold;
        margin-top: 5px;
    }
    .metric-sub {
        font-size: 12px;
        color: #e63946;
        margin-top: 5px;
    }
    .metric-sub-green {
        font-size: 12px;
        color: #2ec4b6;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function to process data columns safely and flexibly
def process_dataframe(df):
    df.columns = df.columns.str.strip()
    
    desp_col = next((c for c in df.columns if 'desp' in c.lower() or 'dispatch' in c.lower()), None)
    if desp_col:
        df = df[pd.notna(df[desp_col]) & (df[desp_col].astype(str).str.strip() != "") & (df[desp_col].astype(str).str.strip().str.lower() != "nan")].copy()
    
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

    # Shorten Vendor/Party Names
    vendor_c = next((c for c in df.columns if 'vendor' in c.lower() or 'party' in c.lower() or 'client' in c.lower()), None)
    def clean_party_name(val):
        val_str = str(val).upper().strip()
        if "DHL" in val_str:
            return "DHL"
        elif "BUSYBEES" in val_str:
            return "Busybees"
        elif "TRACKON" in val_str:
            return "Trackon"
        return str(val).strip()

    if vendor_c:
        df['VendorName'] = df[vendor_c].apply(clean_party_name)
    else:
        df['VendorName'] = "TEJAS CARGO"

    def get_arrival_status(row):
        remark_col = next((c for c in df.columns if 'remark' in c.lower() or 'tracking' in c.lower()), None)
        if remark_col and pd.notna(row.get(remark_col)):
            if "breakdown" in str(row.get(remark_col)).lower():
                return "Breakdown"

        final_rep = row.get('Final Touching Reporting Date & Time') or row.get('Reporting Date') or row.get('Reporting Date & Time')
        
        if pd.notna(final_rep) and str(final_rep).strip() != "" and str(final_rep).strip().lower() != "nan":
            late_hrs = row.get('Late Hrs')
            if pd.notna(late_hrs) and str(late_hrs).strip() != "" and str(late_hrs).strip() != "0":
                return "Trip Closed (Delay)"
            else:
                return "Trip Closed (On-Time)"
        else:
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

st.sidebar.markdown("📂 **Upload Vendor MIS Files**")
uploaded_files = st.sidebar.file_uploader(
    "Choose Excel/CSV files", 
    type=["xlsx", "csv"], 
    accept_multiple_files=True,
    label_visibility="collapsed"
)

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

if st.sidebar.button("🗑️ REMOVE DATA", use_container_width=True):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    st.session_state.vendor_data = None
    st.rerun()

st.sidebar.markdown("Navigation:")
selected_nav = st.sidebar.radio("", [
    "📊 Dashboard",
    "📊 Client Performance",
    "🏢 Branches",
    "🚚 Vehicle Utilisation",
    "📝 Today call Action",
    "📈 Monthly Breakdown",
    "🔐 User & Access Control"
], label_visibility="collapsed")

st.sidebar.markdown("---")
if st.sidebar.button("Logout", use_container_width=True):
    st.sidebar.warning("Logged out successfully!")


# ================= MAIN PAGE LOGIC =================
if selected_nav == "📊 Dashboard":
    st.title("⚡ Sales Manager Live Monitoring Dashboard")
    st.info("🔒 **Restricted Vendor View:** Live executive monitoring & KPI tracking for TEJAS CARGO INDIA PVT LTD")

    if st.session_state.vendor_data is not None:
        df = st.session_state.vendor_data
        st.markdown("---")

        total_trips = len(df)
        ontime_trips = len(df[df['Status_Category'] == 'Trip Closed (On-Time)'])
        delay_trips = len(df[df['Status_Category'] == 'Trip Closed (Delay)'])
        intransit_trips = len(df[df['Status_Category'] == 'In-Transit'])
        breakdown_trips = len(df[df['Status_Category'] == 'Breakdown'])
        
        on_time_pct = round((ontime_trips / total_trips) * 100, 1) if total_trips > 0 else 0

        # Top Row Widgets (Metrics & Gauges style)
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Total Active Trips</div>
                    <div class="metric-value">{total_trips}</div>
                    <div class="metric-sub-green">Live Fleet Volume</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">In-Transit Fleet</div>
                    <div class="metric-value">{intransit_trips}</div>
                    <div class="metric-sub">Active on Route</div>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
                <div class="metric-card" style="min-height: 195px;">
                    <div class="metric-title">Today's Performance & KPIs</div>
            """, unsafe_allow_html=True)
            
            g1, g2, g3 = st.columns(3)
            with g1:
                st.metric(label="On-Time Rate", value=f"{on_time_pct}%", delta="Stable")
            with g2:
                st.metric(label="Closed Trips", value=f"{ontime_trips + delay_trips}", delta="Completed")
            with g3:
                st.metric(label="Breakdowns", value=f"{breakdown_trips}", delta="-2 vs yesterday", delta_color="inverse")
            
            st.markdown("</div>", unsafe_allow_html=True)

        with col3:
            # Leaderboard style client volume
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-title">Today's Leaderboard (Client Trips)</div>
            """, unsafe_allow_html=True)
            
            leaderboard = df['VendorName'].value_counts().reset_index()
            leaderboard.columns = ['Client', 'Trips']
            for idx, row in leaderboard.head(4).iterrows():
                st.markdown(f"<div style='display: flex; justify-content: space-between; font-size:14px; margin-top:6px;'><span>{row['Client']}</span><span style='color:#2ec4b6; font-weight:bold;'>{row['Trips']} Trips</span></div>", unsafe_allow_html=True)
                
            st.markdown("</div>", unsafe_allow_html=True)

        # Second Row - Trend / Line chart & Live Alerts
        col_chart, col_leads = st.columns([2, 1])

        with col_chart:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-title">Volume & Movement Trend (This Week vs Last Week)</div>
            """, unsafe_allow_html=True)
            
            # Simulated trend line chart for live monitoring feel
            trend_data = pd.DataFrame({
                'Mon': [120, 90], 'Tue': [105, 85], 'Wed': [115, 95], 'Thu': [140, 110], 'Fri': [130, 100]
            }, index=['This Week', 'Last Week']).T
            st.line_chart(trend_data)
            
            st.markdown("</div>", unsafe_allow_html=True)

        with col_leads:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Live Action Queue</div>
                    <div style="font-size: 24px; font-weight: bold; margin-top: 10px; color: #e63946;">{breakdown_trips} Breakdowns</div>
                    <div style="font-size: 13px; color: #8d99ae; margin-top: 5px;">Require immediate intervention & escalation.</div>
                    <hr style="border-color: #3a506b;">
                    <div style="font-size: 24px; font-weight: bold; color: #ffb703;">{delay_trips} Delayed Trips</div>
                    <div style="font-size: 13px; color: #8d99ae; margin-top: 5px;">Running behind expected delivery SLA.</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📄 Live Detailed Trip Records")
        
        required_columns = [
            'Lorry No.', 'Veh.Type', 'From', 'Destination', 'KM', 'Party', 'Desp. Date & Time',
            '1st Touching', '1st Touching Reporting Date & Time', '1st Touching Delivery Date & Time', '1st Touching Hrs.',
            '2nd Touching', '2nd Touching Reporting Date & Time', '2nd Touching Delivery Date & Time', '2nd Touching Hrs',
            'Final Touching Reporting Date & Time', 'Final Touching Delivery Date & Time',
            'Total Touching Hrs.', 'Hrs. Taken with touching', 'Hrs. Taken without touching (Dly.)',
            'Late Hrs', 'Tracking Remark', 'Group Name', 'Controlling Staff Name', 'Foreman Name'
        ]
        available_cols = [c for c in required_columns if c in df.columns]
        show_df = df[available_cols] if available_cols else df
        st.dataframe(show_df, use_container_width=True, hide_index=True)

        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
            export_df = df[available_cols] if available_cols else df
            export_df.to_excel(writer, index=False, sheet_name='Live_Monitoring_Report')
        
        st.download_button(
            label="📥 Download Live Monitoring Report (Excel)",
            data=buffer_excel.getvalue(),
            file_name="Live_Monitoring_Report.xlsx",
            mime="application/vnd.ms-excel",
            type="primary"
        )
    else:
        st.info("👈 Kripya Sidebar se apni file upload karein aur 'Process Data' button par click karein.")

elif selected_nav == "📈 Monthly Breakdown":
    st.title("📈 Monthly Breakdown")
    st.info("🔒 Showing monthly performance breakdown and trends.")
    if st.session_state.vendor_data is not None:
        df = st.session_state.vendor_data
        date_col = next((c for c in df.columns if 'date' in c.lower() or 'desp' in c.lower()), None)
        if date_col:
            try:
                df['Month'] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%B %Y')
                monthly_summary = df.groupby(['Month', 'Status_Category']).size().unstack(fill_value=0).reset_index()
                st.dataframe(monthly_summary, use_container_width=True, hide_index=True)
            except Exception as e:
                st.warning(f"Could not parse monthly breakdown: {e}")
        else:
            st.warning("Date column not found for monthly breakdown.")
    else:
        st.info("👈 Kripya pehle Sidebar se file upload karein.")
else:
    st.title(selected_nav)
    st.info("🚧 Yeh page abhi ban raha hai (Work in Progress).")
