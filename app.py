import streamlit as st
import pandas as pd
from datetime import datetime
import math
import io
import os

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

# Helper function to render Proper Speedometer
def render_speedometer_html(client_name, rate, ontime, delay, total):
    clamped_rate = max(0.0, min(100.0, float(rate)))
    
    if clamped_rate >= 80:
        val_color = "#2ec4b6"  # Green
    elif clamped_rate >= 50:
        val_color = "#ffb703"  # Yellow
    else:
        val_color = "#e63946"  # Red

    cx, cy = 120, 110
    
    ticks_svg = ""
    for p in range(0, 101, 10):
        rad = math.radians(180 - (p * 1.8))
        r_inner = 62 if p % 20 == 0 else 65
        r_outer = 70
        x1 = cx + r_inner * math.cos(rad)
        y1 = cy - r_inner * math.sin(rad)
        x2 = cx + r_outer * math.cos(rad)
        y2 = cy - r_outer * math.sin(rad)
        stroke_w = "2" if p % 20 == 0 else "1"
        ticks_svg += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#8d99ae" stroke-width="{stroke_w}"/>'

    labels_svg = ""
    for p in [0, 25, 50, 75, 100]:
        rad = math.radians(180 - (p * 1.8))
        r_lbl = 98
        lx = cx + r_lbl * math.cos(rad)
        ly = cy - r_lbl * math.sin(rad) + 4
        labels_svg += f'<text x="{lx:.1f}" y="{ly:.1f}" fill="#8d99ae" font-size="10" font-weight="bold" text-anchor="middle" font-family="Arial">{p}%</text>'

    n_rad = math.radians(180 - (clamped_rate * 1.8))
    tip_x = cx + 65 * math.cos(n_rad)
    tip_y = cy - 65 * math.sin(n_rad)
    
    perp_rad = n_rad + (math.pi / 2)
    b1_x = cx + 4.5 * math.cos(perp_rad)
    b1_y = cy - 4.5 * math.sin(perp_rad)
    b2_x = cx - 4.5 * math.cos(perp_rad)
    b2_y = cy + 4.5 * math.sin(perp_rad)
    tail_x = cx - 12 * math.cos(n_rad)
    tail_y = cy + 12 * math.sin(n_rad)

    needle_points = f"{b1_x:.1f},{b1_y:.1f} {tip_x:.1f},{tip_y:.1f} {b2_x:.1f},{b2_y:.1f} {tail_x:.1f},{tail_y:.1f}"

    html_lines = [
        f'<div class="metric-card" style="text-align: center; padding: 18px 15px;">',
        f'<div class="metric-title" style="margin-bottom: 8px;">{client_name} Performance</div>',
        f'<svg viewBox="0 0 240 130" width="100%" style="max-width: 260px; margin: 0 auto; display: block;">',
        f'<path d="M 40 110 A 80 80 0 0 1 200 110" fill="none" stroke="#0b132b" stroke-width="18" stroke-linecap="round"/>',
        f'<path d="M 40 110 A 80 80 0 0 1 120 30" fill="none" stroke="#e63946" stroke-width="14" stroke-linecap="butt"/>',
        f'<path d="M 120 30 A 80 80 0 0 1 184.72 62.98" fill="none" stroke="#ffb703" stroke-width="14" stroke-linecap="butt"/>',
        f'<path d="M 184.72 62.98 A 80 80 0 0 1 200 110" fill="none" stroke="#2ec4b6" stroke-width="14" stroke-linecap="butt"/>',
        ticks_svg,
        labels_svg,
        f'<polygon points="{needle_points}" fill="#ffffff"/>',
        f'<circle cx="{cx}" cy="{cy}" r="8" fill="#ffffff"/>',
        f'<circle cx="{cx}" cy="{cy}" r="4" fill="#1c2541"/>',
        f'</svg>',
        f'<div style="font-size: 32px; font-weight: bold; color: {val_color}; margin-top: 2px;">{rate}%</div>',
        f'<div style="font-size: 13px; color: #8d99ae; margin-top: 6px;">',
        f'<span style="color:#2ec4b6;">On-Time: <b>{ontime}</b></span> &nbsp;|&nbsp; ',
        f'<span style="color:#e63946;">Delay: <b>{delay}</b></span> &nbsp;|&nbsp; ',
        f'<span style="color:#ffffff;">Total: <b>{total}</b></span>',
        f'</div>',
        f'</div>'
    ]
    return "".join(html_lines)

# Helper function to process data columns safely according to strict Trip Closed rule
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

    def get_trip_closed_status(row):
        status_col = next((c for c in df.columns if 'status' in c.lower()), None)
        status_val = str(row.get(status_col, '')).lower() if status_col else ''
        
        final_rep = row.get('Final Touching Reporting Date & Time') or row.get('Reporting Date') or row.get('Reporting Date & Time')
        
        # Strict Condition: Status mein "order done" aur Final Touching Reporting Date & Time mention ho
        if ("order done" in status_val) and (pd.notna(final_rep) and str(final_rep).strip() != "" and str(final_rep).strip().lower() != "nan"):
            late_hrs = row.get('Late Hrs')
            if pd.isna(late_hrs) or str(late_hrs).strip() == "" or str(late_hrs).strip().lower() == "nan" or str(late_hrs).strip() == "0":
                return "On-Time Trip Closed"
            else:
                return "Delay Trip Closed"
        else:
            return "Invalid"
            
    df['Status_Category'] = df.apply(get_trip_closed_status, axis=1)
    
    # Only keep Trip Closed data, drop everything else
    df = df[df['Status_Category'].isin(['On-Time Trip Closed', 'Delay Trip Closed'])].copy()
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
    st.info("🔒 **Restricted Vendor View:** Live executive monitoring & Trip Closed tracking for TEJAS CARGO INDIA PVT LTD")

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
        ontime_trips = len(filtered_df[filtered_df['Status_Category'] == 'On-Time Trip Closed'])
        delay_trips = len(filtered_df[filtered_df['Status_Category'] == 'Delay Trip Closed'])
        
        ontime_pct = round((ontime_trips / total_trips) * 100, 1) if total_trips > 0 else 0
        delay_pct = round((delay_trips / total_trips) * 100, 1) if total_trips > 0 else 0

        # Top Row Widgets
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            col1_html = (
                f'<div class="metric-card" style="min-height: 155px;">'
                f'<div class="metric-title">Total Trip Closed</div>'
                f'<div class="metric-value">{total_trips}</div>'
                f'<div style="display: flex; justify-content: space-between; font-size: 13px; margin-top: 14px; padding-top: 10px; border-top: 1px solid #3a506b;">'
                f'<span style="color: #2ec4b6;">✔ On-Time: <b>{ontime_trips}</b></span>'
                f'<span style="color: #e63946;">✖ Delay: <b>{delay_trips}</b></span>'
                f'</div>'
                f'</div>'
            )
            st.markdown(col1_html, unsafe_allow_html=True)

        with col2:
            col2_html = (
                f'<div class="metric-card" style="min-height: 155px;">'
                f'<div class="metric-title">Trip Closed Performance (%)</div>'
                f'<div style="display: flex; justify-content: space-around; align-items: center; text-align: center; margin-top: 15px; padding-top: 12px; border-top: 1px solid #3a506b;">'
                f'<div>'
                f'<div style="font-size: 12px; color: #8d99ae; font-weight: 600; text-transform: uppercase;">Total Trip Count</div>'
                f'<div style="font-size: 28px; font-weight: bold; color: #ffffff; margin-top: 4px;">{total_trips}</div>'
                f'<div style="font-size: 12px; color: #8d99ae; margin-top: 2px;">100% Trips</div>'
                f'</div>'
                f'<div style="border-left: 1px solid #3a506b; height: 55px;"></div>'
                f'<div>'
                f'<div style="font-size: 12px; color: #8d99ae; font-weight: 600; text-transform: uppercase;">On-Time</div>'
                f'<div style="font-size: 28px; font-weight: bold; color: #2ec4b6; margin-top: 4px;">{ontime_trips}</div>'
                f'<div style="font-size: 13px; font-weight: bold; color: #2ec4b6; margin-top: 2px;">{ontime_pct}%</div>'
                f'</div>'
                f'<div style="border-left: 1px solid #3a506b; height: 55px;"></div>'
                f'<div>'
                f'<div style="font-size: 12px; color: #8d99ae; font-weight: 600; text-transform: uppercase;">Delay</div>'
                f'<div style="font-size: 28px; font-weight: bold; color: #e63946; margin-top: 4px;">{delay_trips}</div>'
                f'<div style="font-size: 13px; font-weight: bold; color: #e63946; margin-top: 2px;">{delay_pct}%</div>'
                f'</div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(col2_html, unsafe_allow_html=True)

        with col3:
            lb_clients = filtered_df['VendorName'].value_counts().index.tolist()
            lb_rows_html = ""
            for c_name in lb_clients[:4]:
                c_df = filtered_df[filtered_df['VendorName'] == c_name]
                c_tot = len(c_df)
                c_ontime = len(c_df[c_df['Status_Category'] == 'On-Time Trip Closed'])
                c_delay = len(c_df[c_df['Status_Category'] == 'Delay Trip Closed'])
                
                lb_rows_html += (
                    f'<div style="border-top: 1px solid #3a506b; padding-top: 8px; margin-top: 8px;">'
                    f'<div style="display: flex; justify-content: space-between; font-size: 14px; font-weight: bold;">'
                    f'<span style="color: #ffffff;">{c_name}</span>'
                    f'<span style="color: #ffffff;">Total: {c_tot}</span>'
                    f'</div>'
                    f'<div style="display: flex; justify-content: space-between; font-size: 12px; margin-top: 4px;">'
                    f'<span style="color: #2ec4b6;">On-Time: <b>{c_ontime}</b></span>'
                    f'<span style="color: #e63946;">Delay: <b>{c_delay}</b></span>'
                    f'</div>'
                    f'</div>'
                )

            if not lb_rows_html:
                lb_rows_html = '<div style="font-size: 13px; color: #8d99ae; margin-top: 8px;">No data available</div>'

            col3_html = (
                f'<div class="metric-card" style="min-height: 155px;">'
                f'<div class="metric-title">Today\'s Leaderboard (Client Trips)</div>'
                f'{lb_rows_html}'
                f'</div>'
            )
            st.markdown(col3_html, unsafe_allow_html=True)

        # ================= CLIENT-WISE SPEEDOMETER CARDS =================
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🎯 Client-wise Performance Speedometer")
        
        unique_clients = filtered_df['VendorName'].dropna().unique()
        if len(unique_clients) > 0:
            p_cols = st.columns(min(len(unique_clients), 3))
            for i, client_name in enumerate(unique_clients):
                client_df = filtered_df[filtered_df['VendorName'] == client_name]
                c_total = len(client_df)
                c_ontime = len(client_df[client_df['Status_Category'] == 'On-Time Trip Closed'])
                c_delay = len(client_df[client_df['Status_Category'] == 'Delay Trip Closed'])
                c_rate = round((c_ontime / c_total) * 100, 1) if c_total > 0 else 0
                
                with p_cols[i % 3]:
                    st.markdown(
                        render_speedometer_html(client_name, c_rate, c_ontime, c_delay, c_total),
                        unsafe_allow_html=True
                    )

        # Live Detailed Trip Records
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📄 Live Detailed Trip Closed Records")
        
        required_columns = [
            'Lorry No.', 'Veh.Type', 'From', 'Destination', 'KM', 'Party', 'Desp. Date & Time',
            '1st Touching', '1st Touching Reporting Date & Time', '1st Touching Delivery Date & Time', '1st Touching Hrs.',
            '2nd Touching', '2nd Touching Reporting Date & Time', '2nd Touching Delivery Date & Time', '2nd Touching Hrs',
            'Final Touching Reporting Date & Time', 'Final Touching Delivery Date & Time',
            'Total Touching Hrs.', 'Hrs. Taken with touching', 'Hrs. Taken without touching (Dly.)',
            'Late Hrs', 'Tracking Remark', 'Group Name', 'Controlling Staff Name', 'Foreman Name'
        ]
        available_cols = [c for c in required_columns if c in filtered_df.columns]
        show_df = filtered_df[available_cols] if available_cols else filtered_df
        
        if not show_df.empty:
            st.dataframe(show_df, use_container_width=True, hide_index=True)
        else:
            st.warning("Is selection ke liye koi Trip Closed data available nahi hai.")

        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
            export_df = filtered_df[available_cols] if available_cols else filtered_df
            export_df.to_excel(writer, index=False, sheet_name='Trip_Closed_Report')
        
        st.download_button(
            label="📥 Download Trip Closed Report (Excel)",
            data=buffer_excel.getvalue(),
            file_name="Trip_Closed_Report.xlsx",
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
