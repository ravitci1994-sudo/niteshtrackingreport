import streamlit as st
import pandas as pd
from datetime import datetime
import math
import io
import os

# 1. Page Configuration
st.set_page_config(page_title="Sales Manager Live Monitoring Dashboard", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Dynamic & Attractive Modern Dark Theme Styling
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #0b132b 0%, #1c2541 100%);
    }
    .metric-card {
        background: linear-gradient(145deg, #1c2541, #131b2e);
        padding: 22px;
        border-radius: 14px;
        border: 1px solid #48cae4;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
        margin-bottom: 15px;
        color: white;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 25px rgba(72, 202, 228, 0.25);
        border-color: #90e0ef;
    }
    .metric-title {
        font-size: 15px;
        color: #90e0ef;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        border-bottom: 2px solid rgba(72, 202, 228, 0.3);
        padding-bottom: 6px;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 36px;
        color: #ffffff;
        font-weight: 900;
        margin-top: 5px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .metric-sub-green {
        font-size: 12px;
        color: #2ec4b6;
        margin-top: 5px;
    }
    .custom-table-container {
        overflow-x: auto;
        max-height: 450px;
        overflow-y: auto;
        border: 1px solid #48cae4;
        border-radius: 12px;
        background-color: #1c2541;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        margin-bottom: 15px;
    }
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        color: #ffffff;
        font-size: 13px;
        font-family: Arial, sans-serif;
        white-space: nowrap;
    }
    .custom-table th {
        background: linear-gradient(90deg, #0b132b, #1c2541);
        color: #48cae4;
        padding: 12px 15px;
        text-align: left;
        position: sticky;
        top: 0;
        border-bottom: 3px solid #48cae4;
        font-weight: 800;
        z-index: 1;
    }
    .custom-table td {
        padding: 10px 15px;
        border-bottom: 1px solid #2b3a55;
        color: #e0e6ed;
    }
    .custom-table tr:hover td {
        background-color: #2b3a55;
        color: #90e0ef;
    }
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 900 !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
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
        ticks_svg += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#90e0ef" stroke-width="{stroke_w}"/>'

    labels_svg = ""
    for p in [0, 25, 50, 75, 100]:
        rad = math.radians(180 - (p * 1.8))
        r_lbl = 98
        lx = cx + r_lbl * math.cos(rad)
        ly = cy - r_lbl * math.sin(rad) + 4
        labels_svg += f'<text x="{lx:.1f}" y="{ly:.1f}" fill="#90e0ef" font-size="10" font-weight="bold" text-anchor="middle" font-family="Arial">{p}%</text>'

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
        f'<div class="metric-title" style="margin-bottom: 8px;">🔥 {client_name} PERFORMANCE</div>',
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
        f'<div style="font-size: 34px; font-weight: 900; color: {val_color}; margin-top: 4px; text-shadow: 0 2px 4px rgba(0,0,0,0.4);">{rate}%</div>',
        f'<div style="font-size: 13px; color: #90e0ef; margin-top: 6px; font-weight: 700;">',
        f'<span style="color:#2ec4b6;">On-Time: <b>{ontime}</b></span> &nbsp;|&nbsp; ',
        f'<span style="color:#e63946;">Delay: <b>{delay}</b></span> &nbsp;|&nbsp; ',
        f'<span style="color:#ffffff;">Total: <b>{total}</b></span>',
        f'</div>',
        f'</div>'
    ]
    return "".join(html_lines)

# Helper function to render crash-proof HTML table
def render_html_table(df_to_show):
    clean_df = df_to_show.fillna("").astype(str)
    headers = "".join([f"<th>{col}</th>" for col in clean_df.columns])
    rows_html = []
    for _, row in clean_df.iterrows():
        cells = "".join([f"<td>{val if val.lower() != 'nan' else ''}</td>" for val in row])
        rows_html.append(f"<tr>{cells}</tr>")
    body = "".join(rows_html)
    return f'<div class="custom-table-container"><table class="custom-table"><thead><tr>{headers}</tr></thead><tbody>{body}</tbody></table></div>'

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
            
            if 'callout' in uploaded_file.name.lower() or any('category' in c.lower() for c in temp_df.columns):
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
                desp_col = next((c for c in temp_df.columns if 'desp' in c.lower() or 'dispatch' in c.lower()), None)
                if desp_col:
                    temp_df = temp_df[pd.notna(temp_df[desp_col]) & (temp_df[desp_col].astype(str).str.strip() != "") & (temp_df[desp_col].astype(str).str.strip().str.lower() != "nan")].copy()

                vendor_c = next((c for c in temp_df.columns if 'vendor' in c.lower() or 'party' in c.lower() or 'client' in c.lower() or 'customer' in c.lower()), None)
                if vendor_c:
                    def clean_party_mis(v):
                        v_str = str(v).upper().strip()
                        if "DHL" in v_str: return "DHL"
                        elif "BUSYBEES" in v_str: return "Busybees"
                        elif "TRACKON" in v_str: return "Trackon"
                        return str(v).strip()
                    temp_df['VendorName'] = temp_df[vendor_c].apply(clean_party_mis)
                else:
                    temp_df['VendorName'] = "TEJAS CARGO"
                
                date_col = next((c for c in temp_df.columns if 'date' in c.lower() or 'desp' in c.lower() or 'time' in c.lower()), None)
                if date_col:
                    temp_df['Parsed_Date'] = pd.to_datetime(temp_df[date_col], errors='coerce')

                status_col = next((c for c in temp_df.columns if 'status' in c.lower()), None)
                def get_status(row):
                    status_val = str(row.get(status_col, '')).lower() if status_col else ''
                    final_rep = row.get('Final Touching Reporting Date & Time') or row.get('Reporting Date') or row.get('Reporting Date & Time')
                    
                    if status_col and final_rep is not None:
                        if ("order done" in status_val) and (pd.notna(final_rep) and str(final_rep).strip() != "" and str(final_rep).strip().lower() != "nan"):
                            late_hrs = row.get('Late Hrs')
                            if pd.isna(late_hrs) or str(late_hrs).strip() == "" or str(late_hrs).strip().lower() == "nan" or str(late_hrs).strip() == "0":
                                return "On-Time Trip Closed"
                            else:
                                return "Delay Trip Closed"
                        else:
                            return "Invalid"
                    else:
                        late_hrs = row.get('Late Hrs') or row.get('Delay Hrs') or row.get('Delay')
                        if pd.isna(late_hrs) or str(late_hrs).strip() == "" or str(late_hrs).strip().lower() == "nan" or str(late_hrs).strip() == "0":
                            return "On-Time Trip Closed"
                        else:
                            return "Delay Trip Closed"

                temp_df['Status_Category'] = temp_df.apply(get_status, axis=1)
                valid_mis = temp_df[temp_df['Status_Category'].isin(['On-Time Trip Closed', 'Delay Trip Closed'])].copy()
                mis_dfs.append(valid_mis if not valid_mis.empty else temp_df)
        except Exception as e:
            st.error(f"Error reading file {uploaded_file.name}: {e}")
            
    callout_df = pd.concat(callout_dfs, ignore_index=True) if callout_dfs else pd.DataFrame()
    mis_df = pd.concat(mis_dfs, ignore_index=True) if mis_dfs else pd.DataFrame()
    return callout_df, mis_df

# ================= MEMORY SETUP =================
DATA_FILE_CALLOUT = "saved_callout_data.pkl"
DATA_FILE_MIS = "saved_mis_data.pkl"

if 'callout_data' not in st.session_state:
    if os.path.exists(DATA_FILE_CALLOUT):
        try: st.session_state.callout_data = pd.read_pickle(DATA_FILE_CALLOUT)
        except: st.session_state.callout_data = None
    else:
        st.session_state.callout_data = None

if 'mis_data' not in st.session_state:
    if os.path.exists(DATA_FILE_MIS):
        try: st.session_state.mis_data = pd.read_pickle(DATA_FILE_MIS)
        except: st.session_state.mis_data = None
    else:
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
            
            if not c_df.empty: c_df.to_pickle(DATA_FILE_CALLOUT)
            if not m_df.empty: m_df.to_pickle(DATA_FILE_MIS)
            
            st.sidebar.success("✅ Data successfully processed!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
    else:
        st.sidebar.warning("⚠️ Pehle files upload karein!")

st.sidebar.markdown("---")

if st.sidebar.button("🗑️ REMOVE DATA", use_container_width=True):
    if os.path.exists(DATA_FILE_CALLOUT): os.remove(DATA_FILE_CALLOUT)
    if os.path.exists(DATA_FILE_MIS): os.remove(DATA_FILE_MIS)
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

# ----------------- 1. DASHBOARD -----------------
if "Dashboard" in selected_nav:
    st.title("⚡ Sales Manager Live Monitoring Dashboard")
    st.info("🔒 **Restricted Vendor View:** Callout Count & Overall Performance")

    has_callout = st.session_state.callout_data is not None and not st.session_state.callout_data.empty
    has_mis = st.session_state.mis_data is not None and not st.session_state.mis_data.empty

    if has_callout or has_mis:
        callout_df = st.session_state.callout_data if has_callout else pd.DataFrame()
        mis_df = st.session_state.mis_data if has_mis else pd.DataFrame()
        
        st.markdown("---")
        clients_set = set()
        if not mis_df.empty and 'VendorName' in mis_df.columns:
            clients_set.update(mis_df['VendorName'].dropna().unique())
        if not callout_df.empty and 'VendorName' in callout_df.columns:
            clients_set.update(callout_df['VendorName'].dropna().unique())
            
        client_list = ["ALL"] + sorted(list(clients_set))
        selected_client = st.selectbox("🏢 Filter by Customer (Party):", client_list)

        filtered_callout = callout_df.copy()
        filtered_mis = mis_df.copy()
        
        if selected_client != "ALL":
            if not filtered_callout.empty and 'VendorName' in filtered_callout.columns:
                filtered_callout = filtered_callout[filtered_callout['VendorName'] == selected_client]
            if not filtered_mis.empty and 'VendorName' in filtered_mis.columns:
                filtered_mis = filtered_mis[filtered_mis['VendorName'] == selected_client]

        # Callout Metrics
        total_callouts = len(filtered_callout)
        dhl_c = int((filtered_callout['VendorName'] == 'DHL').sum()) if not filtered_callout.empty and 'VendorName' in filtered_callout.columns else 0
        busy_c = int((filtered_callout['VendorName'] == 'Busybees').sum()) if not filtered_callout.empty and 'VendorName' in filtered_callout.columns else 0
        trk_c = int((filtered_callout['VendorName'] == 'Trackon').sum()) if not filtered_callout.empty and 'VendorName' in filtered_callout.columns else 0

        if not filtered_callout.empty and 'Parsed_Date' in filtered_callout.columns:
            aug_df = filtered_callout[filtered_callout['Parsed_Date'].dt.month == 8]
            sept_df = filtered_callout[filtered_callout['Parsed_Date'].dt.month == 9]
            oct_df = filtered_callout[filtered_callout['Parsed_Date'].dt.month == 10]

            aug_dhl, aug_busy, aug_trk = int((aug_df['VendorName'] == 'DHL').sum()), int((aug_df['VendorName'] == 'Busybees').sum()), int((aug_df['VendorName'] == 'Trackon').sum())
            sept_dhl, sept_busy, sept_trk = int((sept_df['VendorName'] == 'DHL').sum()), int((sept_df['VendorName'] == 'Busybees').sum()), int((sept_df['VendorName'] == 'Trackon').sum())
            oct_dhl, oct_busy, oct_trk = int((oct_df['VendorName'] == 'DHL').sum()), int((oct_df['VendorName'] == 'Busybees').sum()), int((oct_df['VendorName'] == 'Trackon').sum())
        else:
            aug_dhl, aug_busy, aug_trk, sept_dhl, sept_busy, sept_trk, oct_dhl, oct_busy, oct_trk = [0]*9
        
        # Performance Metrics
        total_trips = len(filtered_mis)
        ontime_trips = len(filtered_mis[filtered_mis['Status_Category'] == 'On-Time Trip Closed']) if not filtered_mis.empty and 'Status_Category' in filtered_mis.columns else 0
        delay_trips = len(filtered_mis[filtered_mis['Status_Category'] == 'Delay Trip Closed']) if not filtered_mis.empty and 'Status_Category' in filtered_mis.columns else 0
        
        ontime_pct = round((ontime_trips / total_trips) * 100, 1) if total_trips > 0 else 0
        delay_pct = round((delay_trips / total_trips) * 100, 1) if total_trips > 0 else 0

        col1, col2, col3 = st.columns([1.2, 1.8, 1])

        with col1:
            client_label = "ALL CLIENTS" if selected_client == "ALL" else selected_client.upper()
            col1_html = (
                f'<div class="metric-card" style="min-height: 200px;">'
                f'<div class="metric-title">📊 TOTAL CALLOUT COUNT ({client_label})</div>'
                f'<div class="metric-value">{total_callouts}</div>'
                f'<div class="metric-sub-green" style="margin-bottom: 6px; font-weight:700;">Breakdown & Accident</div>'
                f'<div style="display: flex; justify-content: space-between; font-size: 12px; margin-top: 6px; padding-top: 6px; border-top: 1px solid #48cae4; color: #ffffff;">'
                f'<span>DHL: <b style="color:#2ec4b6;">{dhl_c}</b></span>'
                f'<span>Busybees: <b style="color:#ffb703;">{busy_c}</b></span>'
                f'<span>Trackon: <b style="color:#e63946;">{trk_c}</b></span>'
                f'</div>'
                f'<div style="font-size: 11px; color: #90e0ef; margin-top: 8px; font-weight: 800; text-transform: uppercase;">August Breakdown</div>'
                f'<div style="display: flex; justify-content: space-between; font-size: 11px; color: #ffffff;">'
                f'<span>DHL: <b style="color:#2ec4b6;">{aug_dhl}</b></span>'
                f'<span>Busybees: <b
