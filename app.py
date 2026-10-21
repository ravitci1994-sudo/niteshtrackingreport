import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(page_title="Sales Manager Live Monitoring Dashboard", layout="wide", initial_sidebar_state="expanded")

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
        status_col = next((c for c in df.columns if 'status' in c.lower()), None)
        status_val = str(row.get(status_col, '')).lower() if status_col else ''
        
        final_rep = row.get('Final Touching Reporting Date & Time') or row.get('Reporting Date') or row.get('Reporting Date & Time')
        
        # Check if Order Done and Final Touching Reporting Date & Time is present
        if ("order done" in status_val or status_val == "order done") and (pd.notna(final_rep) and str(final_rep).strip() != "" and str(final_rep).strip().lower() != "nan"):
            return "Trip Closed"
        elif "in-transit" in status_val or "intransit" in status_val:
            return "In-Transit"
        else:
            # Fallback logic if status column doesn't have exact text
            if pd.notna(final_rep) and str(final_rep).strip() != "" and str(final_rep).strip().lower() != "nan":
                return "Trip Closed"
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

        # Client Filter Dropdown on Dashboard
        client_list = ["ALL"] + list(df['VendorName'].dropna().unique())
        selected_client = st.selectbox("🏢 Filter by Client (Party):", client_list)

        filtered_df = df.copy()
        if selected_client != "ALL":
            filtered_df = filtered_df[filtered_df['VendorName'] == selected_client]

        total_trips = len(filtered_df)
        closed_trips = len(filtered_df[filtered_df['Status_Category'] == 'Trip Closed'])
        intransit_trips = len(filtered_df[filtered_df['Status_Category'] == 'In-Transit'])
        
        closure_rate = round((closed_trips / total_trips) * 100, 1) if total_trips > 0 else 0

        # Top Row Widgets
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
            
            g1, g2 = st.columns(2)
            with g1:
                st.metric(label="Trip Closure Rate", value=f"{closure_rate}%", delta="Stable")
            with g2:
                st.metric(label="Total Trip Closed", value=f"{closed_trips}", delta="Completed")
            
            st.markdown("</div>", unsafe_allow_html=True)

        with col3:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-title">Today's Leaderboard (Client Trips)</div>
            """, unsafe_allow_html=True)
            
            leaderboard = filtered_df['VendorName'].value_counts().reset_index()
            leaderboard.columns = ['Client', 'Trips']
            for idx, row in leaderboard.head(4).iterrows():
                st.markdown(f"<div style='display: flex; justify-content: space-between; font-size:14px; margin-top:6px;'><span>{row['Client']}</span><span style='color:#2ec4b6; font-weight:bold;'>{row['Trips']} Trips</span></div>", unsafe_allow_html=True)
                
            st.markdown("</div>", unsafe_allow_html=True)

        # ================= 3 SPEEDOMETERS FOR CLIENT-WISE PERFORMANCE =================
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🎯 Client-wise Performance Speedometers (Gauges)")
        
        # Get top 3 clients or unique clients
        unique_clients = df['VendorName'].dropna().unique()[:3]
        
        if len(unique_clients) > 0:
            gauge_cols = st.columns(len(unique_clients))
            for i, client_name in enumerate(unique_clients):
                client_df = df[df['VendorName'] == client_name]
                c_total = len(client_df)
                c_closed = len(client_df[client_df['Status_Category'] == 'Trip Closed'])
                c_rate = round((c_closed / c_total) * 100, 1) if c_total > 0 else 0
                
                with gauge_cols[i]:
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = c_rate,
                        title = {'text': f"{client_name} Performance", 'font': {'color': 'white', 'size': 16}},
                        number = {'suffix': "%", 'font': {'color': 'white'}},
                        gauge = {
                            'axis': {'range': [0, 100], 'tickcolor': "white"},
                            'bar': {'color': "#2ec4b6"},
                            'steps': [
                                {'range': [0, 50], 'color': "#1c2541"},
                                {'range': [50, 80], 'color': "#3a506b"},
                                {'range': [80, 100], 'color': "#0b132b"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90
                            }
                        }
                    ))
                    fig.update_layout(paper_bgcolor="#1c2541", font={'color': "white"}, height=250, margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig, use_container_width=True)

        # Live Detailed Trip Records (Only Trip Closed data)
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📄 Live Detailed Trip Records (Trip Closed Only)")
        
        closed_details_df = filtered_df[filtered_df['Status_Category'] == 'Trip Closed'].copy()

        required_columns = [
            'Lorry No.', 'Veh.Type', 'From', 'Destination', 'KM', 'Party', 'Desp. Date & Time',
            '1st Touching', '1st Touching Reporting Date & Time', '1st Touching Delivery Date & Time', '1st Touching Hrs.',
            '2nd Touching', '2nd Touching Reporting Date & Time', '2nd Touching Delivery Date & Time', '2nd Touching Hrs',
            'Final Touching Reporting Date & Time', 'Final Touching Delivery Date & Time',
            'Total Touching Hrs.', 'Hrs. Taken with touching', 'Hrs. Taken without touching (Dly.)',
            'Late Hrs', 'Tracking Remark', 'Group Name', 'Controlling Staff Name', 'Foreman Name'
        ]
        available_cols = [c for c in required_columns if c in closed_details_df.columns]
        show_df = closed_details_df[available_cols] if available_cols else closed_details_df
        
        if not show_df.empty:
            st.dataframe(show_df, use_container_width=True, hide_index=True)
        else:
            st.warning("Is client ke liye koi Trip Closed data available nahi hai.")

        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
            export_df = closed_details_df[available_cols] if available_cols else closed_details_df
            export_df.to_excel(writer, index=False, sheet_name='Live_Monitoring_Report')
        
        st.download_button(
            label="📥 Download Trip Closed Report (Excel)",
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
