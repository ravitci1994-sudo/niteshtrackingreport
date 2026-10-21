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
        val_color = "#2ec4b6"
    elif clamped_rate >= 50:
        val_color = "#ffb703"
    else:
        val_color = "#e63946"

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

# Helper function to process uploaded files separately
def process_uploaded_files(uploaded_files):
    callout_dfs = []
    mis_dfs = []
    
    for uploaded_file in uploaded_files:
        try:
            if uploaded_file.name.endswith('.csv'):
                temp_df = pd.read_csv(uploaded_file, low_memory=False)
            else:
                temp_df = pd.read_excel(uploaded_file)
            
            temp_df.columns = temp_df.columns.str.strip()
            
            # Check if it's Callout file or MIS file based on columns or filename
            if 'callout' in uploaded_file.name.lower() or any('category' in c.lower() for c in temp_df.columns):
                # Callout specific processing: Breakdown & Accident only, Aug/Sept/Oct only
                cat_col = next((c for c in temp_df.columns if 'category' in c.lower() or 'cat' in c.lower()), None)
                if cat_col:
                    temp_df = temp_df[temp_df[cat_col].astype(str).str.lower().str.contains('breakdown|accident', na=False)].copy()
                
                vendor_c = next((c for c in temp_df.columns if 'vendor' in c.lower() or 'party' in c.lower() or 'client' in c.lower() or 'customer' in c.lower()), None)
                if vendor_c:
                    def clean_party(v):
                        v_str = str(v).upper().strip()
                        if "DHL" in v_str: return "DHL"
                        elif "BUSYBEES" in v_str: return "Busybees"
                        elif "TRACKON" in v_str: return "Trackon"
                        return None
                    temp_df['VendorName'] = temp_df[vendor_c].apply(clean_party)
                    temp_df = temp_df[temp_df['VendorName'].isin(['DHL', 'Busybees', 'Trackon'])].copy()
                
                date_col = next((c for c in temp_df.columns if 'date' in c.lower() or 'desp' in c.lower() or 'time' in c.lower()), None)
                if date_col:
                    temp_df['Parsed_Date'] = pd.to_datetime(temp_df[date_col], errors='coerce')
                    temp_df = temp_df[temp_df['Parsed_Date'].dt.month.isin([8, 9, 10])].copy()
                
                callout_dfs.append(temp_df)
            else:
                # MIS file processing for Performance
                vendor_c = next((c for c in temp_df.columns if 'vendor' in c.lower() or 'party' in c.lower() or 'client' in c.lower() or 'customer' in c.lower()), None)
                if vendor_c:
                    def clean_party(v):
                        v_str = str(v).upper().strip()
                        if "DHL" in v_str: return "DHL"
                        elif "BUSYBEES" in v_str: return "Busybees"
                        elif "TRACKON" in v_str: return "Trackon"
                        return None
                    temp_df['VendorName'] = temp_df[vendor_c].apply(clean_party)
                    temp_df = temp_df[temp_df['VendorName'].isin(['DHL', 'Busybees', 'Trackon'])].copy()
                
                date_col = next((c for c in temp_df.columns if 'date' in c.lower() or 'desp' in c.lower() or 'time' in c.lower()), None)
                if date_col:
                    temp_df['Parsed_Date'] = pd.to_datetime(temp_df[date_col], errors='coerce')
                    temp_df = temp_df[temp_df['Parsed_Date'].dt.month.isin([8, 9, 10])].copy()
                
                # Determine On-Time vs Delay status
                def get_status(row):
                    late_hrs = row.get('Late Hrs') or row.get('Delay Hrs') or row.get('Delay')
                    if pd.isna(late_hrs) or str(late_hrs).strip() == "" or str(late_hrs).strip().lower() == "nan" or str(late_hrs).strip() == "0":
                        return "On-Time Trip Closed"
                    else:
                        return "Delay Trip Closed"
                temp_df['Status_Category'] = temp_df.apply(get_status, axis=1)
                mis_dfs.append(temp_df)
        except Exception as e:
            st.error(f"Error reading file {uploaded_file.name}: {e}")
            
    callout_df = pd.concat(callout_dfs, ignore_index=True) if callout_dfs else pd.DataFrame()
    mis_df = pd.concat(mis_dfs, ignore_index=True) if mis_dfs else pd.DataFrame()
    return callout_df, mis_df

# ================= MEMORY SETUP =================
if 'callout_data' not in st.session_state:
    st.session_state.callout_data = None
if 'mis_data' not in st.session_state:
    st.session_state.mis_data = None

# ================= SIDEBAR =================
st.sidebar.markdown("### Welcome, Tejas Cargo India Pvt Ltd")
st.sidebar.markdown("<small style='color:gray'><b>ID:</b> <span style='color:green'>TEJAS</span> | <b>Role:</b> <span style='color:green'>Vendor</span></small>", unsafe_allow_html=True)

st.sidebar.markdown("---")

st.sidebar.markdown("📂 **Upload Callout & MIS Files**")
uploaded_files = st.sidebar.file_uploader(
    "Choose Excel/CSV files", 
    type=["xlsx", "csv"], 
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if st.sidebar.button("🚀 Process Data", type="primary", use_container_width=True):
    if uploaded_files:
        try:
            c_df, m_df = process_uploaded_files(uploaded_files)
            st.session_state.callout_data = c_df
            st.session_state.mis_data = m_df
            st.sidebar.success("✅ Data successfully processed!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
    else:
        st.sidebar.warning("⚠️ Pehle files upload karein!")

st.sidebar.markdown("---")

if st.sidebar.button("🗑️ REMOVE DATA", use_container_width=True):
    st.session_state.callout_data = None
    st.session_state.mis_data = None
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
    st.info("🔒 **Restricted Vendor View:** Breakdown & Accident Callout Count + MIS Performance (Aug, Sept, Oct)")

    if st.session_state.callout_data is not None and not st.session_state.callout_data.empty:
        callout_df = st.session_state.callout_data
        mis_df = st.session_state.mis_data if st.session_state.mis_data is not None else pd.DataFrame()
        
        st.markdown("---")

        client_list = ["ALL"] + list(callout_df['VendorName'].dropna().unique())
        selected_client = st.selectbox("🏢 Filter by Customer (Party):", client_list)

        filtered_callout = callout_df.copy()
        filtered_mis = mis_df.copy()
        
        if selected_client != "ALL":
            filtered_callout = filtered_callout[filtered_callout['VendorName'] == selected_client]
            if not filtered_mis.empty and 'VendorName' in filtered_mis.columns:
                filtered_mis = filtered_mis[filtered_mis['VendorName'] == selected_client]

        total_callouts = len(filtered_callout)
        
        # Month-wise Callout Count (Aug, Sept, Oct)
        if 'Parsed_Date' in filtered_callout.columns:
            aug_count = int((filtered_callout['Parsed_Date'].dt.month == 8).sum())
            sept_count = int((filtered_callout['Parsed_Date'].dt.month == 9).sum())
            oct_count = int((filtered_callout['Parsed_Date'].dt.month == 10).sum())
        else:
            aug_count, sept_count, oct_count = 0, 0, 0

        # Client-wise Callout Count (DHL, Busybees, Trackon)
        dhl_c = int((filtered_callout['VendorName'] == 'DHL').sum()) if 'VendorName' in filtered_callout.columns else 0
        busy_c = int((filtered_callout['VendorName'] == 'Busybees').sum()) if 'VendorName' in filtered_callout.columns else 0
        trk_c = int((filtered_callout['VendorName'] == 'Trackon').sum()) if 'VendorName' in filtered_callout.columns else 0
        
        # Performance metrics from MIS data
        total_trips = len(filtered_mis) if not filtered_mis.empty else len(filtered_callout)
        ontime_trips = len(filtered_mis[filtered_mis['Status_Category'] == 'On-Time Trip Closed']) if not filtered_mis.empty else len(filtered_callout[filtered_callout['Status_Category'] == 'On-Time Trip Closed'] if 'Status_Category' in filtered_callout.columns else [])
        delay_trips = len(filtered_mis[filtered_mis['Status_Category'] == 'Delay Trip Closed']) if not filtered_mis.empty else total_callouts - ontime_trips
        
        ontime_pct = round((ontime_trips / total_trips) * 100, 1) if total_trips > 0 else 0
        delay_pct = round((delay_trips / total_trips) * 100, 1) if total_trips > 0 else 0

        col1, col2, col3 = st.columns([1.1, 1.9, 1])

        with col1:
            client_label = "All Clients" if selected_client == "ALL" else selected_client
            col1_html = (
                f'<div class="metric-card" style="min-height: 175px;">'
                f'<div class="metric-title">Total Callout Count ({client_label})</div>'
                f'<div class="metric-value">{total_callouts}</div>'
                f'<div class="metric-sub-green">Breakdown & Accident</div>'
                f'<div style="display: flex; justify-content: space-between; font-size: 12px; margin-top: 10px; padding-top: 8px; border-top: 1px solid #3a506b; color: #ffffff;">'
                f'<span>DHL: <b style="color:#2ec4b6;">{dhl_c}</b></span>'
                f'<span>Busybees: <b style="color:#ffb703;">{busy_c}</b></span>'
                f'<span>Trackon: <b style="color:#e63946;">{trk_c}</b></span>'
                f'</div>'
                f'<div style="display: flex; justify-content: space-between; font-size: 12px; margin-top: 6px; padding-top: 6px; border-top: 1px dashed #3a506b; color: #ffffff;">'
                f'<span>Aug: <b style="color:#ffb703;">{aug_count}</b></span>'
                f'<span>Sept: <b style="color:#2ec4b6;">{sept_count}</b></span>'
                f'<span>Oct: <b style="color:#e63946;">{oct_count}</b></span>'
                f'</div>'
                f'</div>'
            )
            st.markdown(col1_html, unsafe_allow_html=True)

        with col2:
            col2_html = (
                f'<div class="metric-card" style="min-height: 175px;">'
                f'<div class="metric-title">Over All Performance</div>'
                f'<div style="display: flex; justify-content: space-around; align-items: center; text-align: center; margin-top: 22px; padding-top: 15px; border-top: 1px solid #3a506b;">'
                f'<div>'
                f'<div style="font-size: 12px; color: #8d99ae; font-weight: 600; text-transform: uppercase;">Total Count</div>'
                f'<div style="font-size: 28px; font-weight: bold; color: #ffffff; margin-top: 4px;">{total_trips}</div>'
                f'<div style="font-size: 12px; color: #8d99ae; margin-top: 2px;">Aug, Sept, Oct</div>'
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
            base_df = filtered_mis if not filtered_mis.empty else filtered_callout
            lb_clients = base_df['VendorName'].value_counts().index.tolist() if 'VendorName' in base_df.columns else []
            lb_rows_html = ""
            for c_name in lb_clients[:4]:
                c_df = base_df[base_df['VendorName'] == c_name]
                c_tot = len(c_df)
                c_ontime = len(c_df[c_df['Status_Category'] == 'On-Time Trip Closed']) if 'Status_Category' in c_df.columns else c_tot
                c_delay = c_tot - c_ontime
                
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
                f'<div class="metric-card" style="min-height: 175px;">'
                f'<div class="metric-title">Customer Leaderboard</div>'
                f'{lb_rows_html}'
                f'</div>'
            )
            st.markdown(col3_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🎯 Customer-wise Performance Speedometer")
        
        unique_clients = base_df['VendorName'].dropna().unique() if 'VendorName' in base_df.columns else []
        if len(unique_clients) > 0:
            p_cols = st.columns(min(len(unique_clients), 3))
            for i, client_name in enumerate(unique_clients):
                client_df = base_df[base_df['VendorName'] == client_name]
                c_total = len(client_df)
                c_ontime = len(client_df[client_df['Status_Category'] == 'On-Time Trip Closed']) if 'Status_Category' in client_df.columns else c_total
                c_delay = c_total - c_ontime
                c_rate = round((c_ontime / c_total) * 100, 1) if c_total > 0 else 0
                
                with p_cols[i % 3]:
                    st.markdown(
                        render_speedometer_html(client_name, c_rate, c_ontime, c_delay, c_total),
                        unsafe_allow_html=True
                    )

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📄 Live Detailed Callout Records (Breakdown & Accident)")
        
        available_cols = [c for c in filtered_callout.columns if c != 'Parsed_Date']
        show_df = filtered_callout[available_cols] if available_cols else filtered_callout
        
        if not show_df.empty:
            st.dataframe(show_df, use_container_width=True, hide_index=True)
        else:
            st.warning("Is selection ke liye koi callout data available nahi hai.")

        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
            export_df = filtered_callout[available_cols] if available_cols else filtered_callout
            export_df.to_excel(writer, index=False, sheet_name='Callout_Breakdown_Accident')
        
        st.download_button(
            label="📥 Download Callout Report (Excel)",
            data=buffer_excel.getvalue(),
            file_name="Callout_Breakdown_Accident_Report.xlsx",
            mime="application/vnd.ms-excel",
            type="primary"
        )
    else:
        st.info("👈 Kripya Sidebar se apni Callout aur MIS files upload karein aur 'Process Data' par click karein.")

elif selected_nav == "📈 Monthly Breakdown":
    st.title("📈 Monthly Breakdown")
    st.info("🔒 Showing monthly performance breakdown and trends for Aug, Sept, Oct.")
    if st.session_state.callout_data is not None and not st.session_state.callout_data.empty:
        df = st.session_state.callout_data
        if 'Parsed_Date' in df.columns:
            try:
                df['Month'] = df['Parsed_Date'].dt.strftime('%B %Y')
                monthly_summary = df.groupby(['Month', 'VendorName']).size().reset_index(name='Callout Count')
                st.dataframe(monthly_summary, use_container_width=True, hide_index=True)
            except Exception as e:
                st.warning(f"Could not parse monthly breakdown: {e}")
        else:
            st.warning("Date column not found for monthly breakdown.")
    else:
        st.info("👈 Kripya pehle files upload karein.")
else:
    st.title(selected_nav)
    st.info("🚧 Yeh page abhi ban raha hai (Work in Progress).")
