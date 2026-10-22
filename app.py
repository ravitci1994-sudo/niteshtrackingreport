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

# ================= MEMORY SETUP (Hard Persistence Logic) =================
DATA_FILE_CALLOUT = "saved_callout_data.pkl"
DATA_FILE_MIS = "saved_mis_data.pkl"

# Force load data from Pickle files if it's missing from current session
if 'callout_data' not in st.session_state or st.session_state.callout_data is None:
    if os.path.exists(DATA_FILE_CALLOUT):
        try: st.session_state.callout_data = pd.read_pickle(DATA_FILE_CALLOUT)
        except: st.session_state.callout_data = None
    else:
        st.session_state.callout_data = None

if 'mis_data' not in st.session_state or st.session_state.mis_data is None:
    if os.path.exists(DATA_FILE_MIS):
        try: st.session_state.mis_data = pd.read_pickle(DATA_FILE_MIS)
        except: st.session_state.mis_data = None
    else:
        st.session_state.mis_data = None

# Key for clearing file uploader
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# ================= SIDEBAR =================
st.sidebar.markdown("### Welcome, Tejas Cargo India Pvt Ltd")

# Show current Live Date & Time
current_time = datetime.now().strftime("%d %b %Y | %I:%M %p")
st.sidebar.markdown(f"<div style='color: #90e0ef; font-size: 13px; font-weight: bold; margin-top: -10px; margin-bottom: 5px;'>🕒 {current_time}</div>", unsafe_allow_html=True)

st.sidebar.markdown("<small style='color:gray'><b>ID:</b> <span style='color:green'>TEJAS</span> | <b>Role:</b> <span style='color:green'>Vendor</span></small>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Persistent Data Check Indicator
data_exists = (st.session_state.callout_data is not None and not st.session_state.callout_data.empty) or \
              (st.session_state.mis_data is not None and not st.session_state.mis_data.empty)

if data_exists:
    st.sidebar.markdown("""
        <div style="background-color: rgba(46, 196, 182, 0.15); border: 1px solid #2ec4b6; border-radius: 5px; padding: 10px; text-align: center; margin-bottom: 15px;">
            <span style="color: #2ec4b6; font-size: 14px; font-weight: 800;">🟢 Data Active in System</span><br>
            <span style="color: #90e0ef; font-size: 11px;">Aapko dobara file upload karne ki zaroorat nahi hai.</span>
        </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("📂 **Upload Callout & MIS Files**")
uploaded_files = st.sidebar.file_uploader(
    "Choose Excel/CSV files", 
    type=["xlsx", "csv"], 
    accept_multiple_files=True,
    label_visibility="collapsed",
    key=f"uploader_{st.session_state.uploader_key}"
)

if st.sidebar.button("🚀 Process Data", type="primary", use_container_width=True):
    if uploaded_files:
        try:
            c_df, m_df = process_uploaded_files(uploaded_files)
            st.session_state.callout_data = c_df
            st.session_state.mis_data = m_df
            
            if not c_df.empty: c_df.to_pickle(DATA_FILE_CALLOUT)
            if not m_df.empty: m_df.to_pickle(DATA_FILE_MIS)
            
            st.sidebar.success("✅ Data successfully processed and saved!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
    else:
        st.sidebar.warning("⚠️ Pehle files upload karein!")

st.sidebar.markdown("---")

if st.sidebar.button("🗑️ REMOVE DATA", use_container_width=True):
    # Hard Delete Files
    if os.path.exists(DATA_FILE_CALLOUT): os.remove(DATA_FILE_CALLOUT)
    if os.path.exists(DATA_FILE_MIS): os.remove(DATA_FILE_MIS)
    # Clear Session Memory
    st.session_state.callout_data = None
    st.session_state.mis_data = None
    # Reset File Uploader UI
    st.session_state.uploader_key += 1
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
                f'<span>Busybees: <b style="color:#ffb703;">{aug_busy}</b></span>'
                f'<span>Trackon: <b style="color:#e63946;">{aug_trk}</b></span>'
                f'</div>'
                f'<div style="font-size: 11px; color: #90e0ef; margin-top: 6px; font-weight: 800; text-transform: uppercase;">September Breakdown</div>'
                f'<div style="display: flex; justify-content: space-between; font-size: 11px; color: #ffffff;">'
                f'<span>DHL: <b style="color:#2ec4b6;">{sept_dhl}</b></span>'
                f'<span>Busybees: <b style="color:#ffb703;">{sept_busy}</b></span>'
                f'<span>Trackon: <b style="color:#e63946;">{sept_trk}</b></span>'
                f'</div>'
                f'<div style="font-size: 11px; color: #90e0ef; margin-top: 6px; font-weight: 800; text-transform: uppercase;">October Breakdown</div>'
                f'<div style="display: flex; justify-content: space-between; font-size: 11px; color: #ffffff;">'
                f'<span>DHL: <b style="color:#2ec4b6;">{oct_dhl}</b></span>'
                f'<span>Busybees: <b style="color:#ffb703;">{oct_busy}</b></span>'
                f'<span>Trackon: <b style="color:#e63946;">{oct_trk}</b></span>'
                f'</div>'
                f'</div>'
            )
            st.markdown(col1_html, unsafe_allow_html=True)

        with col2:
            col2_html = (
                f'<div class="metric-card" style="min-height: 200px;">'
                f'<div class="metric-title">⚡ OVER ALL PERFORMANCE</div>'
                f'<div style="display: flex; justify-content: space-around; align-items: center; text-align: center; margin-top: 35px; padding-top: 15px; border-top: 1px solid #48cae4;">'
                f'<div>'
                f'<div style="font-size: 12px; color: #90e0ef; font-weight: 800; text-transform: uppercase;">Total Count</div>'
                f'<div style="font-size: 28px; font-weight: 900; color: #ffffff; margin-top: 4px;">{total_trips}</div>'
                f'<div style="font-size: 12px; color: #8d99ae; margin-top: 2px;">Performance Trips</div>'
                f'</div>'
                f'<div style="border-left: 1px solid #48cae4; height: 55px;"></div>'
                f'<div>'
                f'<div style="font-size: 12px; color: #90e0ef; font-weight: 800; text-transform: uppercase;">On-Time</div>'
                f'<div style="font-size: 28px; font-weight: 900; color: #2ec4b6; margin-top: 4px;">{ontime_trips}</div>'
                f'<div style="font-size: 13px; font-weight: 900; color: #2ec4b6; margin-top: 2px;">{ontime_pct}%</div>'
                f'</div>'
                f'<div style="border-left: 1px solid #48cae4; height: 55px;"></div>'
                f'<div>'
                f'<div style="font-size: 12px; color: #90e0ef; font-weight: 800; text-transform: uppercase;">Delay</div>'
                f'<div style="font-size: 28px; font-weight: 900; color: #e63946; margin-top: 4px;">{delay_trips}</div>'
                f'<div style="font-size: 13px; font-weight: 900; color: #e63946; margin-top: 2px;">{delay_pct}%</div>'
                f'</div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(col2_html, unsafe_allow_html=True)

        with col3:
            lb_clients = filtered_mis['VendorName'].value_counts().index.tolist() if not filtered_mis.empty and 'VendorName' in filtered_mis.columns else []
            lb_rows_html = ""
            for c_name in lb_clients[:4]:
                c_df = filtered_mis[filtered_mis['VendorName'] == c_name]
                c_tot = len(c_df)
                c_ontime = len(c_df[c_df['Status_Category'] == 'On-Time Trip Closed']) if 'Status_Category' in c_df.columns else 0
                c_delay = len(c_df[c_df['Status_Category'] == 'Delay Trip Closed']) if 'Status_Category' in c_df.columns else 0
                
                lb_rows_html += (
                    f'<div style="border-top: 1px solid #48cae4; padding-top: 8px; margin-top: 8px;">'
                    f'<div style="display: flex; justify-content: space-between; font-size: 14px; font-weight: 900;">'
                    f'<span style="color: #ffffff;">{c_name}</span>'
                    f'<span style="color: #90e0ef;">Total: {c_tot}</span>'
                    f'</div>'
                    f'<div style="display: flex; justify-content: space-between; font-size: 12px; margin-top: 4px;">'
                    f'<span style="color: #2ec4b6;">On-Time: <b>{c_ontime}</b></span>'
                    f'<span style="color: #e63946;">Delay: <b>{c_delay}</b></span>'
                    f'</div>'
                    f'</div>'
                )

            if not lb_rows_html:
                lb_rows_html = '<div style="font-size: 13px; color: #90e0ef; margin-top: 8px;">No MIS performance data</div>'

            col3_html = (
                f'<div class="metric-card" style="min-height: 200px;">'
                f'<div class="metric-title">🏆 CUSTOMER LEADERBOARD</div>'
                f'{lb_rows_html}'
                f'</div>'
            )
            st.markdown(col3_html, unsafe_allow_html=True)

        # Dashboard Data Table
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("## 📄 Live Detailed Performance Records")
        required_columns = [
            'Lorry No.', 'Veh.Type', 'From', 'Destination', 'KM', 'Party', 'Desp. Date & Time',
            '1st Touching', '1st Touching Reporting Date & Time', '1st Touching Delivery Date & Time', '1st Touching Hrs.',
            '2nd Touching', '2nd Touching Reporting Date & Time', '2nd Touching Delivery Date & Time', '2nd Touching Hrs',
            'Final Touching Reporting Date & Time', 'Final Touching Delivery Date & Time',
            'Total Touching Hrs.', 'Hrs. Taken with touching', 'Hrs. Taken without touching (Dly.)',
            'Late Hrs', 'Tracking Remark', 'Group Name', 'Controlling Staff Name', 'Foreman Name'
        ]
        if not filtered_mis.empty:
            available_cols = [c for c in required_columns if c in filtered_mis.columns]
            if not available_cols:
                available_cols = [c for c in filtered_mis.columns if c not in ['Parsed_Date', 'VendorName']]
            show_df = filtered_mis[available_cols]
            
            st.markdown(render_html_table(show_df), unsafe_allow_html=True)
        else:
            st.warning("Is selection ke liye koi Performance (MIS) data available nahi hai.")
    else:
        st.info("👈 Kripya Sidebar se apni Callout aur MIS Performance files upload karein aur 'Process Data' par click karein.")

# ----------------- 2. CLIENT PERFORMANCE -----------------
elif "Client Performance" in selected_nav:
    st.title("🎯 Customer-wise Performance Speedometer")
    if st.session_state.mis_data is not None and not st.session_state.mis_data.empty:
        mis_df = st.session_state.mis_data
        
        client_list = ["ALL"] + list(mis_df['VendorName'].dropna().unique()) if 'VendorName' in mis_df.columns else ["ALL"]
        selected_client = st.selectbox("🏢 Filter by Customer (Party):", client_list)
        
        filtered_mis = mis_df.copy()
        if selected_client != "ALL":
            filtered_mis = filtered_mis[filtered_mis['VendorName'] == selected_client]

        unique_clients = filtered_mis['VendorName'].dropna().unique() if 'VendorName' in filtered_mis.columns else []
        
        if len(unique_clients) > 0:
            p_cols = st.columns(min(len(unique_clients), 3))
            for i, client_name in enumerate(unique_clients):
                client_df = filtered_mis[filtered_mis['VendorName'] == client_name]
                c_total = len(client_df)
                c_ontime = len(client_df[client_df['Status_Category'] == 'On-Time Trip Closed']) if 'Status_Category' in client_df.columns else 0
                c_delay = len(client_df[client_df['Status_Category'] == 'Delay Trip Closed']) if 'Status_Category' in client_df.columns else 0
                c_rate = round((c_ontime / c_total) * 100, 1) if c_total > 0 else 0
                
                with p_cols[i % 3]:
                    st.markdown(
                        render_speedometer_html(client_name, c_rate, c_ontime, c_delay, c_total),
                        unsafe_allow_html=True
                    )
        else:
            st.warning("Koi Client data available nahi hai.")

        # ================= ONLY PERFORMANCE DATA TABLE =================
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("## 📄 Live Detailed Performance Records")
        
        required_columns = [
            'Lorry No.', 'Veh.Type', 'From', 'Destination', 'KM', 'Party', 'Desp. Date & Time',
            '1st Touching', '1st Touching Reporting Date & Time', '1st Touching Delivery Date & Time', '1st Touching Hrs.',
            '2nd Touching', '2nd Touching Reporting Date & Time', '2nd Touching Delivery Date & Time', '2nd Touching Hrs',
            'Final Touching Reporting Date & Time', 'Final Touching Delivery Date & Time',
            'Total Touching Hrs.', 'Hrs. Taken with touching', 'Hrs. Taken without touching (Dly.)',
            'Late Hrs', 'Tracking Remark', 'Group Name', 'Controlling Staff Name', 'Foreman Name'
        ]
        
        if not filtered_mis.empty:
            available_cols = [c for c in required_columns if c in filtered_mis.columns]
            if not available_cols:
                available_cols = [c for c in filtered_mis.columns if c not in ['Parsed_Date', 'VendorName']]
            show_df = filtered_mis[available_cols]
            
            st.markdown(render_html_table(show_df), unsafe_allow_html=True)
            
            buffer_excel = io.BytesIO()
            with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                show_df.to_excel(writer, index=False, sheet_name='Performance_Report')
            
            st.download_button(
                label="📥 Download Performance Report (Excel)",
                data=buffer_excel.getvalue(),
                file_name="Client_Performance_Report.xlsx",
                mime="application/vnd.ms-excel",
                type="primary"
            )
        else:
            st.warning("Is selection ke liye koi Performance (MIS) data available nahi hai.")
    else:
        st.info("👈 Kripya pehle MIS file upload karein.")

# ----------------- 3. BRANCHES -----------------
elif "Branches" in selected_nav:
    st.title("🏢 Controlling Staff Performance")
    st.info("Showing Performance Breakdown by Controlling Staff Name.")
    
    if st.session_state.mis_data is not None and not st.session_state.mis_data.empty:
        mis_df = st.session_state.mis_data.copy()
        staff_col = next((c for c in mis_df.columns if 'controlling' in c.lower() or 'staff' in c.lower() or 'branch' in c.lower()), None)
        
        if staff_col:
            staff_summary = []
            staff_list = mis_df[staff_col].dropna().unique()
            for staff in staff_list:
                if pd.isna(staff) or str(staff).strip() == "": continue
                s_df = mis_df[mis_df[staff_col] == staff]
                total = len(s_df)
                ontime = len(s_df[s_df['Status_Category'] == 'On-Time Trip Closed'])
                delay = len(s_df[s_df['Status_Category'] == 'Delay Trip Closed'])
                ontime_pct = f"{round((ontime / total) * 100, 1)}%" if total > 0 else "0%"
                staff_summary.append({
                    "Controlling Staff Name": str(staff).strip(),
                    "Total Trips": total,
                    "On-Time Trips": ontime,
                    "Delay Trips": delay,
                    "Performance (%)": ontime_pct
                })
            
            if staff_summary:
                staff_df = pd.DataFrame(staff_summary).sort_values(by="Total Trips", ascending=False)
                st.markdown(render_html_table(staff_df), unsafe_allow_html=True)
            else:
                st.warning("Koi valid Controlling Staff ka data nahi mila.")
        else:
            st.warning("Data mein 'Controlling Staff Name' column nahi mila.")
    else:
        st.info("👈 Kripya pehle MIS file upload karein.")

# ----------------- 4. VEHICLE UTILISATION -----------------
elif "Vehicle Utilisation" in selected_nav:
    st.title("🚚 Vehicle Utilisation (Current Month)")
    st.info("Showing Total Trips valid for the Current Month (Status = 'Order Done' & Final Touching Time mentioned).")
    
    if st.session_state.mis_data is not None and not st.session_state.mis_data.empty:
        mis_df = st.session_state.mis_data.copy()
        
        current_month = datetime.now().month
        current_year = datetime.now().year
        month_name = datetime.now().strftime("%B %Y").upper()
        
        if 'Parsed_Date' in mis_df.columns:
            curr_month_df = mis_df[(mis_df['Parsed_Date'].dt.month == current_month) & (mis_df['Parsed_Date'].dt.year == current_year)]
            
            total_valid_trips = len(curr_month_df)
            
            client_counts_html = ""
            if 'VendorName' in curr_month_df.columns and total_valid_trips > 0:
                counts = curr_month_df['VendorName'].value_counts()
                colors = ["#2ec4b6", "#ffb703", "#e63946", "#90e0ef", "#f72585"]
                items = []
                for i, (c_name, c_val) in enumerate(counts.items()):
                    color = colors[i % len(colors)]
                    items.append(f'<span style="padding: 5px 10px;">{c_name}: <b style="color:{color}; font-size:18px;">{c_val}</b></span>')
                client_counts_html = f'<div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 10px; font-size: 14px; padding-top: 20px; border-top: 1px dashed #48cae4; color: #ffffff; font-weight: 800; margin-top: 20px;">{"".join(items)}</div>'
            
            col1, col2, col3 = st.columns([1, 2.5, 1])
            with col2:
                st.markdown(f"""
                    <div class="metric-card" style="text-align: center; padding: 40px;">
                        <div class="metric-title" style="font-size: 18px;">TOTAL TRIP COUNT ({month_name})</div>
                        <div class="metric-value" style="font-size: 60px; color: #48cae4; margin-bottom: 10px;">{total_valid_trips}</div>
                        <div class="metric-sub-green" style="font-size: 14px; margin-bottom: 10px;">Valid Trips Executed This Month</div>
                        {client_counts_html}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Data mein date column properly format nahi ho paya.")
    else:
        st.info("👈 Kripya pehle MIS file upload karein.")

# ----------------- 5. MONTHLY BREAKDOWN -----------------
elif "Monthly Breakdown" in selected_nav:
    st.title("📈 Monthly Breakdown")
    st.info("🔒 Showing monthly performance breakdown.")
    if st.session_state.mis_data is not None and not st.session_state.mis_data.empty:
        df = st.session_state.mis_data.copy()
        if 'Parsed_Date' in df.columns:
            try:
                df['Month'] = df['Parsed_Date'].dt.strftime('%B %Y')
                monthly_summary = df.groupby(['Month', 'VendorName', 'Status_Category']).size().unstack(fill_value=0).reset_index()
                st.markdown(render_html_table(monthly_summary), unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Could not parse monthly breakdown: {e}")
        else:
            st.warning("Date column not found for monthly breakdown.")
    else:
        st.info("👈 Kripya pehle MIS files upload karein.")

# ----------------- OTHER PAGES -----------------
else:
    st.title(selected_nav)
    st.info("🚧 Yeh page abhi ban raha hai (Work in Progress).")
