import streamlit as st
import pandas as pd
from datetime import datetime
import math
import io
import os
import html as html_lib

# 1. Page Configuration
st.set_page_config(page_title="Sales Manager Live Monitoring Dashboard", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Dynamic & Attractive Modern Dark Theme Styling
st.markdown("""
    <style>
    .main, [data-testid="stAppViewContainer"] {
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

# ================= CONSTANTS =================
REQUIRED_COLUMNS = [
    'Lorry No.', 'Veh.Type', 'From', 'Destination', 'KM', 'Party', 'Desp. Date & Time',
    'Hrs. Given', '1st Touching', '1st Touching Reporting Date & Time', '1st Touching Delivery Date & Time', '1st Touching Hrs.',
    '2nd Touching', '2nd Touching Reporting Date & Time', '2nd Touching Delivery Date & Time', '2nd Touching Hrs', '2nd Touching Hrs.',
    'Final Touching Reporting Date & Time', 'Final Touching Delivery Date & Time',
    'Total Touching Hrs.', 'Hrs. Taken with touching', 'Hrs. Taken without touching (Dly.)',
    'Late Hrs', 'Tracking Remark', 'Group Name', 'Controlling Staff Name', 'Foreman Name'
]
ONTIME = 'On-Time Trip Closed'
DELAY = 'Delay Trip Closed'
EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# ================= HELPERS =================
def is_blank(v):
    if v is None:
        return True
    try:
        if pd.isna(v):
            return True
    except (TypeError, ValueError):
        pass
    return str(v).strip().lower() in ("", "nan", "nat", "none")


def first_valid(row, names):
    """Return first non-blank value from the given column names."""
    for n in names:
        if n in row.index and not is_blank(row[n]):
            return row[n]
    return None


def is_zero_late(v):
    """True if Late Hrs is empty / zero / negative (i.e. trip is on time)."""
    if is_blank(v):
        return True
    s = str(v).strip().lower()
    if s in ("0", "0.0", "00:00", "0:00", "00:00:00", "0:00:00", "0 days 00:00:00"):
        return True
    try:
        return pd.to_timedelta(s) <= pd.Timedelta(0)
    except Exception:
        pass
    try:
        return float(s) <= 0
    except Exception:
        return False


def clean_party(v, keep_other=False):
    v_str = str(v).upper().strip()
    if "DHL" in v_str:
        return "DHL"
    elif "BUSYBEES" in v_str:
        return "Busybees"
    elif "TRACKON" in v_str:
        return "Trackon"
    return str(v).strip() if keep_other else None


def find_col(df, exact=None, contains=None):
    """Find a column by exact (case-insensitive) names first, then by substring."""
    if exact:
        for c in df.columns:
            if c.lower().strip() in exact:
                return c
    if contains:
        for c in df.columns:
            if any(k in c.lower() for k in contains):
                return c
    return None


def get_lorry_col(df):
    """Always prioritize the exact 'Lorry No.' column."""
    if 'Lorry No.' in df.columns:
        return 'Lorry No.'
    return find_col(df, exact=('lorry no.', 'lorry no', 'vehicle no.', 'vehicle no'), contains=('lorry no', 'vehicle no'))


def vendor_column(df):
    return next((c for c in df.columns if any(k in c.lower() for k in ('vendor', 'party', 'client', 'customer'))), None)


def show_cols(df):
    cols = [c for c in REQUIRED_COLUMNS if c in df.columns]
    if not cols:
        cols = [c for c in df.columns if c not in ['Parsed_Date', 'VendorName', 'Status_Category', 'MonthKey']]
    return df[cols]


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
    safe_name = html_lib.escape(str(client_name))

    html_lines = [
        '<div class="metric-card" style="text-align: center; padding: 18px 15px;">',
        f'<div class="metric-title" style="margin-bottom: 8px;">🔥 {safe_name} PERFORMANCE</div>',
        '<svg viewBox="0 0 240 130" width="100%" style="max-width: 260px; margin: 0 auto; display: block;">',
        '<path d="M 40 110 A 80 80 0 0 1 200 110" fill="none" stroke="#0b132b" stroke-width="18" stroke-linecap="round"/>',
        '<path d="M 40 110 A 80 80 0 0 1 120 30" fill="none" stroke="#e63946" stroke-width="14" stroke-linecap="butt"/>',
        '<path d="M 120 30 A 80 80 0 0 1 184.72 62.98" fill="none" stroke="#ffb703" stroke-width="14" stroke-linecap="butt"/>',
        '<path d="M 184.72 62.98 A 80 80 0 0 1 200 110" fill="none" stroke="#2ec4b6" stroke-width="14" stroke-linecap="butt"/>',
        ticks_svg,
        labels_svg,
        f'<polygon points="{needle_points}" fill="#ffffff"/>',
        f'<circle cx="{cx}" cy="{cy}" r="8" fill="#ffffff"/>',
        f'<circle cx="{cx}" cy="{cy}" r="4" fill="#1c2541"/>',
        '</svg>',
        f'<div style="font-size: 34px; font-weight: 900; color: {val_color}; margin-top: 4px; text-shadow: 0 2px 4px rgba(0,0,0,0.4);">{rate}%</div>',
        '<div style="font-size: 13px; color: #90e0ef; margin-top: 6px; font-weight: 700;">',
        f'<span style="color:#2ec4b6;">On-Time: <b>{ontime}</b></span> &nbsp;|&nbsp; ',
        f'<span style="color:#e63946;">Delay: <b>{delay}</b></span> &nbsp;|&nbsp; ',
        f'<span style="color:#ffffff;">Total: <b>{total}</b></span>',
        '</div>',
        '</div>'
    ]
    return "".join(html_lines)


def render_html_table(df_to_show, max_rows=2000):
    clean_df = df_to_show.fillna("").astype(str)
    note = ""
    if len(clean_df) > max_rows:
        note = f'<div style="color:#ffb703; font-size:12px; margin-bottom:6px;">Showing first {max_rows} of {len(clean_df)} rows. Full data Excel download me milega.</div>'
        clean_df = clean_df.head(max_rows)
    headers = "".join([f"<th>{html_lib.escape(str(col))}</th>" for col in clean_df.columns])
    rows_html = []
    for _, row in clean_df.iterrows():
        cells = "".join([f"<td>{html_lib.escape('' if val.lower() in ('nan', 'nat') else val)}</td>" for val in row])
        rows_html.append(f"<tr>{cells}</tr>")
    body = "".join(rows_html)
    return f'{note}<div class="custom-table-container"><table class="custom-table"><thead><tr>{headers}</tr></thead><tbody>{body}</tbody></table></div>'


def to_excel_bytes(sheets):
    buffer_excel = io.BytesIO()
    with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, index=False, sheet_name=name)
    return buffer_excel.getvalue()


# ========== REPORTED VEHICLE TABLE (WITH DATE, DELAY & CONTROLLING STAFF FILTERS) ==========
def show_reported_vehicle_table(df, unique_key=""):
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## 📄 Reported Vehicle")

    # Find Final Touching Reporting Date & Time column
    final_rep_col = next(
        (c for c in ['Final Touching Reporting Date & Time', 'Reporting Date & Time', 'Reporting Date'] if c in df.columns),
        None
    )
    if not final_rep_col:
        final_rep_col = next((c for c in df.columns if 'final touching' in c.lower() and 'report' in c.lower()), None)

    if not final_rep_col:
        st.warning("Data mein 'Final Touching Reporting Date & Time' column nahi mila.")
        return

    temp_df = df.copy()

    # Sirf wahi data pick karna hai jisme Final Touching Reporting Date & Time mention ho
    reported_df = temp_df[~temp_df[final_rep_col].apply(is_blank)].copy()

    if reported_df.empty:
        st.warning("Selected data mein kisi bhi gaadi ke aage 'Final Touching Reporting Date & Time' mention nahi hai.")
        return

    # Parse Reporting Date for the Date Filter Button
    parsed_rep_dt = pd.to_datetime(reported_df[final_rep_col], errors='coerce', dayfirst=True)
    reported_df['_Rep_Date_Obj'] = parsed_rep_dt.dt.date
    reported_df['_Rep_Date_Str'] = parsed_rep_dt.dt.strftime('%d-%m-%Y')

    # Unique sorted dates for dropdown
    valid_dates = (
        reported_df[reported_df['_Rep_Date_Obj'].notna()]
        .drop_duplicates(subset=['_Rep_Date_Str'])
        .sort_values('_Rep_Date_Obj', ascending=False)
    )
    date_options = ["ALL"] + valid_dates['_Rep_Date_Str'].tolist()

    # Staff column identifier
    staff_col = next((c for c in reported_df.columns if 'controlling' in c.lower() or 'staff' in c.lower()), None)

    # Three Filter Buttons side-by-side: Reporting Date, Delay Filter & Controlling Staff
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        selected_date = st.selectbox(
            "📅 Filter by Reporting Date:",
            date_options,
            index=0,
            key=f"reported_date_filter_{unique_key}"
        )
    with f_col2:
        delay_filter = st.selectbox(
            "🚨 Filter by Delay Status:",
            ["ALL Reported Vehicles", "Only Delay Vehicles", "Only On-Time Vehicles"],
            index=0,
            key=f"reported_delay_filter_{unique_key}"
        )
    with f_col3:
        if staff_col:
            staff_list = ["ALL"] + sorted([str(x).strip() for x in reported_df[staff_col].dropna().unique() if str(x).strip() != ""])
        else:
            staff_list = ["ALL"]
        selected_staff = st.selectbox(
            "👨‍💼 Filter by Controlling Staff:",
            staff_list,
            index=0,
            key=f"reported_staff_filter_{unique_key}"
        )

    # 1. Apply Reporting Date Filter
    if selected_date != "ALL":
        filtered_report_df = reported_df[reported_df['_Rep_Date_Str'] == selected_date].copy()
    else:
        filtered_report_df = reported_df.copy()

    # 2. Apply Delay Filter (based on Late Hrs column)
    late_col = next((c for c in ['Late Hrs', 'Delay Hrs', 'Delay'] if c in filtered_report_df.columns), None)
    if late_col:
        if delay_filter == "Only Delay Vehicles":
            filtered_report_df = filtered_report_df[~filtered_report_df[late_col].apply(is_zero_late)].copy()
        elif delay_filter == "Only On-Time Vehicles":
            filtered_report_df = filtered_report_df[filtered_report_df[late_col].apply(is_zero_late)].copy()

    # 3. Apply Controlling Staff Filter
    if selected_staff != "ALL" and staff_col:
        filtered_report_df = filtered_report_df[filtered_report_df[staff_col].astype(str).str.strip() == selected_staff].copy()

    if filtered_report_df.empty:
        st.info(f"Selected filter ke liye koi Reported Vehicle data nahi mila.")
        return

    # Select Requested Columns
    requested_cols = [
        'Lorry No.', 'Veh.Type', 'From', 'Destination', 'Party', 'Desp. Date & Time',
        'Hrs. Given', '1st Touching', '1st Touching Reporting Date & Time', 
        '1st Touching Delivery Date & Time', '1st Touching Hrs.', '2nd Touching', 
        '2nd Touching Reporting Date & Time', '2nd Touching Delivery Date & Time', 
        '2nd Touching Hrs', '2nd Touching Hrs.', 'Final Touching Reporting Date & Time', 
        'Total Touching Hrs.', 'Hrs. Taken with touching', 'Hrs. Taken without touching (Dly.)', 
        'Late Hrs', 'Tracking Remark', 'Controlling Staff Name', 'Foreman Name'
    ]

    actual_cols = []
    rename_dict = {}

    for req_col in requested_cols:
        if req_col in filtered_report_df.columns and req_col not in actual_cols:
            actual_cols.append(req_col)
        elif req_col == 'Party' and 'Party' not in filtered_report_df.columns:
            vendor_c = vendor_column(filtered_report_df) or 'VendorName'
            if vendor_c in filtered_report_df.columns and vendor_c not in actual_cols:
                actual_cols.append(vendor_c)
                rename_dict[vendor_c] = 'Party'

    if not actual_cols:
        actual_cols = [c for c in filtered_report_df.columns if not c.startswith('_') and c not in ['Parsed_Date', 'VendorName', 'Status_Category', 'MonthKey']]

    final_report_df = filtered_report_df[actual_cols].copy()
    final_report_df.rename(columns=rename_dict, inplace=True)
    final_report_df.insert(0, 'S.No', range(1, 1 + len(final_report_df)))

    st.markdown(render_html_table(final_report_df), unsafe_allow_html=True)

    file_date_str = "All_Dates" if selected_date == "ALL" else selected_date.replace('-', '_')
    status_tag = "Delay_Only" if delay_filter == "Only Delay Vehicles" else ("OnTime_Only" if delay_filter == "Only On-Time Vehicles" else "All")
    staff_tag = f"_Staff_{selected_staff.replace(' ', '_')}" if selected_staff != "ALL" else ""
    
    st.download_button(
        label=f"📥 Download Reported Vehicles ({selected_date} - {delay_filter}) (Excel)",
        data=to_excel_bytes({'Reported_Vehicles': final_report_df}),
        file_name=f"Reported_Vehicles_{file_date_str}_{status_tag}{staff_tag}.xlsx",
        mime=EXCEL_MIME,
        type="primary",
        key=f"download_reported_{unique_key}"
    )


# ================= FILE PROCESSING =================
def process_uploaded_files(uploaded_files):
    callout_dfs = []
    mis_dfs = []
    current_year = datetime.now().year

    for uploaded_file in uploaded_files:
        try:
            if uploaded_file.name.lower().endswith('.csv'):
                temp_df = pd.read_csv(uploaded_file, low_memory=False)
            else:
                temp_df = pd.read_excel(uploaded_file)

            temp_df.columns = temp_df.columns.astype(str).str.strip()
            fname = uploaded_file.name.lower()
            has_category = any('category' in c.lower() for c in temp_df.columns)
            is_callout = ('callout' in fname) or (has_category and 'mis' not in fname)

            if is_callout:
                cat_col = next((c for c in temp_df.columns if 'category' in c.lower() or 'cat' in c.lower()), None)
                if cat_col:
                    temp_df = temp_df[temp_df[cat_col].astype(str).str.lower().str.contains('breakdown|accident', na=False)].copy()

                vendor_c = vendor_column(temp_df)
                if vendor_c:
                    temp_df['VendorName'] = temp_df[vendor_c].apply(clean_party)
                    temp_df = temp_df[temp_df['VendorName'].isin(['DHL', 'Busybees', 'Trackon'])].copy()

                date_col = next((c for c in temp_df.columns if 'date' in c.lower() or 'desp' in c.lower() or 'time' in c.lower()), None)
                if date_col:
                    temp_df['Parsed_Date'] = pd.to_datetime(temp_df[date_col], errors='coerce', dayfirst=True)
                    temp_df = temp_df[
                        temp_df['Parsed_Date'].dt.month.isin([8, 9, 10]) &
                        (temp_df['Parsed_Date'].dt.year == current_year)
                    ].copy()

                callout_dfs.append(temp_df)
            else:
                desp_col = next((c for c in temp_df.columns if 'desp' in c.lower() or 'dispatch' in c.lower()), None)
                if desp_col:
                    temp_df = temp_df[~temp_df[desp_col].apply(is_blank)].copy()

                vendor_c = vendor_column(temp_df)
                if vendor_c:
                    temp_df['VendorName'] = temp_df[vendor_c].apply(lambda v: clean_party(v, keep_other=True))
                else:
                    temp_df['VendorName'] = "TEJAS CARGO"

                date_col = (
                    next((c for c in temp_df.columns if 'desp' in c.lower() and 'date' in c.lower()), None)
                    or next((c for c in temp_df.columns if 'date' in c.lower()), None)
                    or next((c for c in temp_df.columns if 'desp' in c.lower() or 'time' in c.lower()), None)
                )
                if date_col:
                    temp_df['Parsed_Date'] = pd.to_datetime(temp_df[date_col], errors='coerce', dayfirst=True)

                status_col = next((c for c in temp_df.columns if 'status' in c.lower()), None)
                final_cols = [c for c in ['Final Touching Reporting Date & Time', 'Reporting Date', 'Reporting Date & Time'] if c in temp_df.columns]
                late_cols = [c for c in ['Late Hrs', 'Delay Hrs', 'Delay'] if c in temp_df.columns]

                def get_status(row):
                    late_val = first_valid(row, late_cols) if late_cols else None
                    if status_col and final_cols:
                        status_val = str(row.get(status_col, '')).lower()
                        final_rep = first_valid(row, final_cols)
                        if ("order done" in status_val) and final_rep is not None:
                            return ONTIME if is_zero_late(late_val) else DELAY
                        return "Invalid"
                    return ONTIME if is_zero_late(late_val) else DELAY

                temp_df['Status_Category'] = temp_df.apply(get_status, axis=1)
                mis_dfs.append(temp_df)
        except Exception as e:
            st.error(f"Error reading file {uploaded_file.name}: {e}")

    callout_df = pd.concat(callout_dfs, ignore_index=True) if callout_dfs else pd.DataFrame()
    mis_df = pd.concat(mis_dfs, ignore_index=True) if mis_dfs else pd.DataFrame()
    return callout_df, mis_df


# ================= MEMORY SETUP (Hard Persistence Logic) =================
DATA_FILE_CALLOUT = "saved_callout_data.pkl"
DATA_FILE_MIS = "saved_mis_data.pkl"

if 'callout_data' not in st.session_state or st.session_state.callout_data is None:
    if os.path.exists(DATA_FILE_CALLOUT):
        try:
            st.session_state.callout_data = pd.read_pickle(DATA_FILE_CALLOUT)
        except Exception:
            st.session_state.callout_data = None
    else:
        st.session_state.callout_data = None

if 'mis_data' not in st.session_state or st.session_state.mis_data is None:
    if os.path.exists(DATA_FILE_MIS):
        try:
            st.session_state.mis_data = pd.read_pickle(DATA_FILE_MIS)
        except Exception:
            st.session_state.mis_data = None
    else:
        st.session_state.mis_data = None

if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0


def save_or_delete(df, path):
    if df is not None and not df.empty:
        df.to_pickle(path)
    elif os.path.exists(path):
        os.remove(path)


# ================= SIDEBAR =================
st.sidebar.markdown("### Welcome, Tejas Cargo India Pvt Ltd")

current_time = datetime.now().strftime("%d %b %Y | %I:%M %p")
st.sidebar.markdown(f"<div style='color: #90e0ef; font-size: 13px; font-weight: bold; margin-top: -10px; margin-bottom: 5px;'>🕒 {current_time}</div>", unsafe_allow_html=True)

st.sidebar.markdown("<small style='color:gray'><b>ID:</b> <span style='color:green'>TEJAS</span> | <b>Role:</b> <span style='color:green'>Vendor</span></small>", unsafe_allow_html=True)
st.sidebar.markdown("---")

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

            save_or_delete(c_df, DATA_FILE_CALLOUT)
            save_or_delete(m_df, DATA_FILE_MIS)

            st.sidebar.success("✅ Data successfully processed and saved!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
    else:
        st.sidebar.warning("⚠️ Pehle files upload karein!")

st.sidebar.markdown("---")

if st.sidebar.button("🗑️ REMOVE DATA", use_container_width=True):
    if os.path.exists(DATA_FILE_CALLOUT):
        os.remove(DATA_FILE_CALLOUT)
    if os.path.exists(DATA_FILE_MIS):
        os.remove(DATA_FILE_MIS)
    st.session_state.callout_data = None
    st.session_state.mis_data = None
    st.session_state.uploader_key += 1
    st.rerun()

st.sidebar.markdown("Navigation:")
selected_nav = st.sidebar.radio("Navigation", [
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
        co_has_vendor = not filtered_callout.empty and 'VendorName' in filtered_callout.columns
        dhl_c = int((filtered_callout['VendorName'] == 'DHL').sum()) if co_has_vendor else 0
        busy_c = int((filtered_callout['VendorName'] == 'Busybees').sum()) if co_has_vendor else 0
        trk_c = int((filtered_callout['VendorName'] == 'Trackon').sum()) if co_has_vendor else 0

        if co_has_vendor and 'Parsed_Date' in filtered_callout.columns:
            aug_df = filtered_callout[filtered_callout['Parsed_Date'].dt.month == 8]
            sept_df = filtered_callout[filtered_callout['Parsed_Date'].dt.month == 9]
            oct_df = filtered_callout[filtered_callout['Parsed_Date'].dt.month == 10]

            aug_dhl, aug_busy, aug_trk = int((aug_df['VendorName'] == 'DHL').sum()), int((aug_df['VendorName'] == 'Busybees').sum()), int((aug_df['VendorName'] == 'Trackon').sum())
            sept_dhl, sept_busy, sept_trk = int((sept_df['VendorName'] == 'DHL').sum()), int((sept_df['VendorName'] == 'Busybees').sum()), int((sept_df['VendorName'] == 'Trackon').sum())
            oct_dhl, oct_busy, oct_trk = int((oct_df['VendorName'] == 'DHL').sum()), int((oct_df['VendorName'] == 'Busybees').sum()), int((oct_df['VendorName'] == 'Trackon').sum())
        else:
            aug_dhl, aug_busy, aug_trk, sept_dhl, sept_busy, sept_trk, oct_dhl, oct_busy, oct_trk = [0] * 9

        # Performance Metrics (Only closed trips)
        if not filtered_mis.empty and 'Status_Category' in filtered_mis.columns:
            perf_mis = filtered_mis[filtered_mis['Status_Category'].isin([ONTIME, DELAY])].copy()
        else:
            perf_mis = pd.DataFrame(columns=filtered_mis.columns)

        total_trips = len(perf_mis)
        ontime_trips = int((perf_mis['Status_Category'] == ONTIME).sum()) if not perf_mis.empty else 0
        delay_trips = int((perf_mis['Status_Category'] == DELAY).sum()) if not perf_mis.empty else 0

        ontime_pct = round((ontime_trips / total_trips) * 100, 1) if total_trips > 0 else 0
        delay_pct = round((delay_trips / total_trips) * 100, 1) if total_trips > 0 else 0

        col1, col2, col3 = st.columns([1.2, 1.8, 1])

        with col1:
            client_label = "ALL CLIENTS" if selected_client == "ALL" else html_lib.escape(str(selected_client).upper())
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
            lb_clients = perf_mis['VendorName'].value_counts().index.tolist() if not perf_mis.empty and 'VendorName' in perf_mis.columns else []
            lb_rows_html = ""
            for c_name in lb_clients[:4]:
                c_df = perf_mis[perf_mis['VendorName'] == c_name]
                c_tot = len(c_df)
                c_ontime = int((c_df['Status_Category'] == ONTIME).sum()) if 'Status_Category' in c_df.columns else 0
                c_delay = int((c_df['Status_Category'] == DELAY).sum()) if 'Status_Category' in c_df.columns else 0

                lb_rows_html += (
                    f'<div style="border-top: 1px solid #48cae4; padding-top: 8px; margin-top: 8px;">'
                    f'<div style="display: flex; justify-content: space-between; font-size: 14px; font-weight: 900;">'
                    f'<span style="color: #ffffff;">{html_lib.escape(str(c_name))}</span>'
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

        if not filtered_mis.empty:
            show_reported_vehicle_table(filtered_mis, unique_key="dash")
        else:
            st.warning("Is selection ke liye koi data available nahi hai.")
    else:
        st.info("👈 Kripya Sidebar se apni Callout aur MIS Performance files upload karein aur 'Process Data' par click karein.")

# ----------------- 2. CLIENT PERFORMANCE -----------------
elif "Client Performance" in selected_nav:
    st.title("🎯 Customer-wise Performance Speedometer")
    if st.session_state.mis_data is not None and not st.session_state.mis_data.empty:
        mis_df = st.session_state.mis_data

        client_list = ["ALL"] + sorted(list(mis_df['VendorName'].dropna().unique())) if 'VendorName' in mis_df.columns else ["ALL"]
        selected_client = st.selectbox("🏢 Filter by Customer (Party):", client_list)

        filtered_mis = mis_df.copy()
        if selected_client != "ALL":
            filtered_mis = filtered_mis[filtered_mis['VendorName'] == selected_client]

        if not filtered_mis.empty and 'Status_Category' in filtered_mis.columns:
            perf_mis = filtered_mis[filtered_mis['Status_Category'].isin([ONTIME, DELAY])].copy()
        else:
            perf_mis = pd.DataFrame(columns=filtered_mis.columns)

        unique_clients = perf_mis['VendorName'].dropna().unique() if 'VendorName' in perf_mis.columns else []

        if len(unique_clients) > 0:
            p_cols = st.columns(min(len(unique_clients), 3))
            for i, client_name in enumerate(unique_clients):
                client_df = perf_mis[perf_mis['VendorName'] == client_name]
                c_total = len(client_df)
                c_ontime = int((client_df['Status_Category'] == ONTIME).sum()) if 'Status_Category' in client_df.columns else 0
                c_delay = int((client_df['Status_Category'] == DELAY).sum()) if 'Status_Category' in client_df.columns else 0
                c_rate = round((c_ontime / c_total) * 100, 1) if c_total > 0 else 0

                with p_cols[i % len(p_cols)]:
                    st.markdown(
                        render_speedometer_html(client_name, c_rate, c_ontime, c_delay, c_total),
                        unsafe_allow_html=True
                    )
        else:
            st.warning("Koi Client data available nahi hai.")

        if not filtered_mis.empty:
            show_reported_vehicle_table(filtered_mis, unique_key="client_perf")
        else:
            st.warning("Is selection ke liye koi data available nahi hai.")
    else:
        st.info("👈 Kripya pehle MIS file upload karein.")

# ----------------- 3. BRANCHES -----------------
elif "Branches" in selected_nav:
    st.title("🏢 Controlling Staff Performance")
    st.info("Showing Performance Breakdown by Controlling Staff Name and Client.")

    if st.session_state.mis_data is not None and not st.session_state.mis_data.empty:
        mis_df = st.session_state.mis_data.copy()
        staff_col = next((c for c in mis_df.columns if 'controlling' in c.lower() or 'staff' in c.lower() or 'branch' in c.lower()), None)

        if staff_col:
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                client_list = ["ALL"] + sorted(list(mis_df['VendorName'].dropna().unique())) if 'VendorName' in mis_df.columns else ["ALL"]
                selected_client = st.selectbox("🏢 Filter by Customer (Party):", client_list, key="branch_client_filter")
            with f_col2:
                staff_list = ["ALL"] + sorted([str(x).strip() for x in mis_df[staff_col].dropna().unique() if str(x).strip() != ""])
                selected_staff = st.selectbox("👨‍💼 Filter by Controlling Staff:", staff_list, key="branch_staff_filter")

            filtered_df = mis_df.copy()
            if selected_client != "ALL":
                filtered_df = filtered_df[filtered_df['VendorName'] == selected_client]
            if selected_staff != "ALL":
                filtered_df = filtered_df[filtered_df[staff_col].astype(str).str.strip() == selected_staff]

            if not filtered_df.empty and 'Status_Category' in filtered_df.columns:
                perf_df = filtered_df[filtered_df['Status_Category'].isin([ONTIME, DELAY])].copy()
            else:
                perf_df = pd.DataFrame(columns=filtered_df.columns)

            staff_summary = []
            if not perf_df.empty:
                grouped = perf_df.groupby([staff_col, 'VendorName'])
                for (staff, client), s_df in grouped:
                    if pd.isna(staff) or str(staff).strip() == "":
                        continue
                    total = len(s_df)
                    ontime = int((s_df['Status_Category'] == ONTIME).sum())
                    delay = int((s_df['Status_Category'] == DELAY).sum())
                    ontime_pct = f"{round((ontime / total) * 100, 1)}%" if total > 0 else "0%"
                    staff_summary.append({
                        "Controlling Staff Name": str(staff).strip(),
                        "Client": str(client).strip(),
                        "Total Trips": total,
                        "On-Time Trips": ontime,
                        "Delay Trips": delay,
                        "Performance (%)": ontime_pct
                    })

            if staff_summary:
                staff_df = pd.DataFrame(staff_summary).sort_values(by="Total Trips", ascending=False)
                st.markdown(render_html_table(staff_df), unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("## 📄 Detailed Filtered Records")
                show_raw_df = show_cols(perf_df)
                st.markdown(render_html_table(show_raw_df), unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button(
                    label="📥 Download Summary & Detailed Data (Excel)",
                    data=to_excel_bytes({'Staff_Performance_Summary': staff_df, 'Detailed_Records': show_raw_df}),
                    file_name="Controlling_Staff_Performance_Report.xlsx",
                    mime=EXCEL_MIME,
                    type="primary"
                )
            else:
                st.warning("Is selection ke liye koi valid data nahi mila.")
        else:
            st.warning("Data mein 'Controlling Staff Name' column nahi mila.")
    else:
        st.info("👈 Kripya pehle MIS file upload karein.")

# ----------------- 4. VEHICLE UTILISATION -----------------
elif "Vehicle Utilisation" in selected_nav:
    st.title("🚚 Vehicle Utilisation")
    st.info("Closed trips (Status = 'Order Done' & Final Touching Time mentioned) vehicle-wise, route-wise aur client-wise.")

    if st.session_state.mis_data is not None and not st.session_state.mis_data.empty:
        mis_df = st.session_state.mis_data.copy()

        if 'Parsed_Date' not in mis_df.columns or mis_df['Parsed_Date'].notna().sum() == 0:
            st.warning("Date column sahi se read nahi hua. Despatch Date column check karein.")
        else:
            mis_df = mis_df[mis_df['Parsed_Date'].notna()].copy()

            if 'Status_Category' in mis_df.columns:
                mis_df = mis_df[mis_df['Status_Category'].isin([ONTIME, DELAY])]

            mis_df['MonthKey'] = mis_df['Parsed_Date'].dt.strftime('%Y-%m')
            month_options = sorted(mis_df['MonthKey'].unique(), reverse=True)

            if not month_options:
                st.warning("Koi closed trip data nahi mila.")
            else:
                current_key = datetime.now().strftime('%Y-%m')
                default_idx = month_options.index(current_key) if current_key in month_options else 0

                selected_month = st.selectbox(
                    "📅 Select Month:", month_options, index=default_idx,
                    format_func=lambda k: pd.Period(k).strftime('%B %Y').upper()
                )
                month_label = pd.Period(selected_month).strftime('%B %Y').upper()
                month_df = mis_df[mis_df['MonthKey'] == selected_month].copy()

                lorry_col = get_lorry_col(month_df)
                if lorry_col is None:
                    st.warning("'Lorry No.' column nahi mila.")
                else:
                    month_df[lorry_col] = month_df[lorry_col].astype(str).str.strip()
                    mask = (month_df[lorry_col] != "") & (month_df[lorry_col].str.upper() != "NAN")
                    mask &= ~month_df[lorry_col].str.upper().str.contains('TBC|TBA|DUMMY', na=False)
                    month_df = month_df[mask]

                    from_col = find_col(month_df, exact=('from',))
                    dest_col = find_col(month_df, exact=('destination', 'to'))
                    if from_col and dest_col:
                        month_df['Route'] = (
                            month_df[from_col].astype(str).str.upper().str.strip() + " ➔ " +
                            month_df[dest_col].astype(str).str.upper().str.strip()
                        )
                    else:
                        month_df['Route'] = "N/A"

                    km_col = next((c for c in month_df.columns if c.strip().upper() == 'KM'), None)
                    month_df['_KM'] = pd.to_numeric(month_df[km_col], errors='coerce').fillna(0) if km_col else 0

                    if 'VendorName' not in month_df.columns:
                        month_df['VendorName'] = "N/A"

                    vehicle_list = ["ALL"] + sorted(month_df[lorry_col].unique().tolist())
                    selected_vehicle = st.selectbox("🚛 Filter by Vehicle No.:", vehicle_list, key="veh_util_filter")

                    view_df = month_df if selected_vehicle == "ALL" else month_df[month_df[lorry_col] == selected_vehicle]

                    total_trips = len(view_df)
                    total_km = view_df['_KM'].sum()

                    colors = ["#2ec4b6", "#ffb703", "#e63946", "#90e0ef", "#f72585"]
                    chips = ""
                    for i, (c_name, c_val) in enumerate(view_df['VendorName'].value_counts().items()):
                        chips += (f'<span style="padding:5px 12px;">{html_lib.escape(str(c_name))}: '
                                  f'<b style="color:{colors[i % len(colors)]}; font-size:20px;">{c_val}</b></span>')

                    title = (f"TOTAL TRIP COUNT ({month_label})" if selected_vehicle == "ALL"
                             else f"{html_lib.escape(selected_vehicle)} - TOTAL CLOSED TRIPS ({month_label})")

                    card_html = (
                        '<div class="metric-card" style="text-align:center; padding:35px;">'
                        f'<div class="metric-title" style="font-size:18px;">{title}</div>'
                        f'<div class="metric-value" style="font-size:60px; color:#48cae4;">{total_trips}</div>'
                        '<div class="metric-sub-green" style="font-size:14px;">Closed Trips (Client-wise)</div>'
                        '<div style="display:flex; justify-content:space-around; flex-wrap:wrap; gap:10px; '
                        f'margin-top:15px; padding-top:15px; border-top:1px dashed #48cae4; color:#ffffff; font-weight:800;">{chips}</div>'
                        '<div style="font-size:16px; color:#90e0ef; margin-top:15px; font-weight:bold; '
                        'border-top:1px solid #3a506b; padding-top:15px;">TOTAL DISTANCE: '
                        f'<span style="color:#ffffff; font-size:26px;">{total_km:,.0f} KM</span></div>'
                        '</div>'
                    )
                    c1, c2, c3 = st.columns([1, 2.5, 1])
                    with c2:
                        st.markdown(card_html, unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    heading = "ALL Vehicles" if selected_vehicle == "ALL" else selected_vehicle
                    st.markdown(f"## 📍 Route & Client Summary ({heading})")

                    group_cols = ['Route', 'VendorName'] if selected_vehicle != "ALL" else [lorry_col, 'Route', 'VendorName']
                    if view_df.empty:
                        st.warning("Is selection ke liye koi closed trip nahi mila.")
                        summary = pd.DataFrame()
                    else:
                        summary = (view_df.groupby(group_cols)
                                   .agg(Trips=('Route', 'size'), Total_KM=('_KM', 'sum'))
                                   .reset_index()
                                   .rename(columns={lorry_col: 'Lorry No.', 'VendorName': 'Client'})
                                   .sort_values('Trips', ascending=False))
                        summary['Total_KM'] = summary['Total_KM'].round(0).astype(int)
                        summary.insert(0, 'S.No', range(1, 1 + len(summary)))
                        st.markdown(render_html_table(summary), unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("## 📄 Detailed Vehicle Utilisation Records")
                    veh_type_col = next((c for c in view_df.columns if 'veh' in c.lower() and 'type' in c.lower()), None)
                    detail = pd.DataFrame({'Lorry No.': view_df[lorry_col]})
                    if veh_type_col:
                        detail['Veh.Type'] = view_df[veh_type_col]
                    detail['Route'] = view_df['Route']
                    detail['KM'] = view_df['_KM']
                    detail['Client'] = view_df['VendorName']
                    detail.insert(0, 'S.No', range(1, 1 + len(detail)))
                    st.markdown(render_html_table(detail), unsafe_allow_html=True)

                    st.download_button(
                        label="📥 Download Utilisation Report (Excel)",
                        data=to_excel_bytes({'Route_Client_Summary': summary, 'Detailed_Records': detail}),
                        file_name="Vehicle_Utilisation_Report.xlsx",
                        mime=EXCEL_MIME,
                        type="primary"
                    )
    else:
        st.info("👈 Kripya pehle MIS file upload karein.")

# ----------------- 5. MONTHLY BREAKDOWN -----------------
elif "Monthly Breakdown" in selected_nav:
    st.title("📈 Monthly Breakdown")
    st.info("🔒 Showing monthly performance breakdown.")
    if st.session_state.mis_data is not None and not st.session_state.mis_data.empty:
        df = st.session_state.mis_data.copy()
        if 'Parsed_Date' in df.columns and 'Status_Category' in df.columns:
            try:
                df = df[df['Parsed_Date'].notna()].copy()
                df = df[df['Status_Category'].isin([ONTIME, DELAY])]
                df['Month'] = df['Parsed_Date'].dt.to_period('M')
                monthly_summary = (df.groupby(['Month', 'VendorName', 'Status_Category'])
                                   .size().unstack(fill_value=0).reset_index()
                                   .sort_values(['Month', 'VendorName']))
                monthly_summary['Month'] = monthly_summary['Month'].dt.strftime('%B %Y')
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
