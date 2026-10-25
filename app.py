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
        font-size: 42px;
        color: #ffffff;
        font-weight: 900;
        margin-top: 5px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .metric-sub-green {
        font-size: 13px;
        color: #2ec4b6;
        margin-top: 5px;
        font-weight: 700;
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
    for n in names:
        if n in row.index and not is_blank(row[n]):
            return row[n]
    return None


def is_zero_late(v):
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
    return None


def find_col(df, exact=None, contains=None):
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


# ================= REPORTED VEHICLE TABLE =================
def show_reported_vehicle_table(df, unique_key="", staff_filter=None):
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## 📄 Reported Vehicle")

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
    reported_df = temp_df[~temp_df[final_rep_col].apply(is_blank)].copy()

    if reported_df.empty:
        st.warning("Selected data mein kisi bhi gaadi ke aage 'Final Touching Reporting Date & Time' mention nahi hai.")
        return

    parsed_rep_dt = pd.to_datetime(reported_df[final_rep_col], errors='coerce', dayfirst=True)
    reported_df['_Rep_Date_Obj'] = parsed_rep_dt.dt.date
    reported_df['_Rep_Date_Str'] = parsed_rep_dt.dt.strftime('%d-%m-%Y')

    current_dt = datetime.now().date()
    def get_relative_week_label(row_date):
        if pd.isna(row_date):
            return None
        diff_days = (current_dt - row_date).days
        if diff_days < 0:
            return "Current / Future"
        elif diff_days <= 7:
            return "Last 1 Week"
        elif diff_days <= 14:
            return "Last 2 Weeks"
        elif diff_days <= 21:
            return "Last 3 Weeks"
        elif diff_days <= 28:
            return "Last 4 Weeks"
        else:
            w_num = (diff_days // 7) + 1
            return f"Last {w_num} Weeks"

    reported_df['_Rel_Week'] = reported_df['_Rep_Date_Obj'].apply(get_relative_week_label)

    valid_dates = (
        reported_df[reported_df['_Rep_Date_Obj'].notna()]
        .drop_duplicates(subset=['_Rep_Date_Str'])
        .sort_values('_Rep_Date_Obj', ascending=False)
    )
    date_options = ["ALL"] + valid_dates['_Rep_Date_Str'].tolist()

    staff_col = next((c for c in reported_df.columns if 'controlling' in c.lower() or 'staff' in c.lower()), None)
    client_col_name = vendor_column(reported_df) or 'VendorName'

    if staff_filter:
        selected_staff = staff_filter
        st.info(f"🔒 Logged in as Staff View: **{selected_staff}**")
        selected_client_report = "ALL"
    else:
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
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
        with f_col4:
            if client_col_name in reported_df.columns:
                client_list = ["ALL"] + sorted([str(x).strip() for x in reported_df[client_col_name].dropna().unique() if str(x).strip() != ""])
            else:
                client_list = ["ALL"]
            selected_client_report = st.selectbox(
                "🏢 Filter by Client:",
                client_list,
                index=0,
                key=f"reported_client_filter_{unique_key}"
            )

        st.markdown("📅 **Filter by Week (Multiple Selection):**")
        standard_weeks = ["Last 1 Week", "Last 2 Weeks", "Last 3 Weeks", "Last 4 Weeks"]
        available_weeks = [w for w in standard_weeks if w in reported_df['_Rel_Week'].unique()]
        other_weeks = sorted([w for w in reported_df['_Rel_Week'].unique() if w not in standard_weeks and w is not None])
        all_week_options = available_weeks + other_weeks

        if all_week_options:
            chk_cols = st.columns(min(len(all_week_options), 6))
            selected_weeks = []
            for i, wk in enumerate(all_week_options):
                with chk_cols[i % len(chk_cols)]:
                    if st.checkbox(wk, value=False, key=f"chk_rel_week_{unique_key}_{wk}"):
                        selected_weeks.append(wk)
        else:
            selected_weeks = []

    filtered_report_df = reported_df.copy()

    if not staff_filter:
        if selected_date != "ALL":
            filtered_report_df = filtered_report_df[filtered_report_df['_Rep_Date_Str'] == selected_date].copy()
        if selected_weeks:
            filtered_report_df = filtered_report_df[filtered_report_df['_Rel_Week'].isin(selected_weeks)].copy()
        late_col = next((c for c in ['Late Hrs', 'Delay Hrs', 'Delay'] if c in filtered_report_df.columns), None)
        if late_col:
            if delay_filter == "Only Delay Vehicles":
                filtered_report_df = filtered_report_df[~filtered_report_df[late_col].apply(is_zero_late)].copy()
            elif delay_filter == "Only On-Time Vehicles":
                filtered_report_df = filtered_report_df[filtered_report_df[late_col].apply(is_zero_late)].copy()
        if selected_staff != "ALL" and staff_col:
            filtered_report_df = filtered_report_df[filtered_report_df[staff_col].astype(str).str.strip() == selected_staff].copy()
        if selected_client_report != "ALL" and client_col_name in filtered_report_df.columns:
            filtered_report_df = filtered_report_df[filtered_report_df[client_col_name].astype(str).str.strip() == selected_client_report].copy()
    else:
        if staff_col:
            filtered_report_df = filtered_report_df[filtered_report_df[staff_col].astype(str).str.strip() == staff_filter].copy()

    if filtered_report_df.empty:
        st.info(f"Selected filter ke liye koi Reported Vehicle data nahi mila.")
        return

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

    file_date_str = "All_Dates" if (staff_filter or selected_date == "ALL") else selected_date.replace('-', '_')
    status_tag = "All" if staff_filter else ("Delay_Only" if delay_filter == "Only Delay Vehicles" else ("OnTime_Only" if delay_filter == "Only On-Time Vehicles" else "All"))
    staff_tag = f"_Staff_{selected_staff.replace(' ', '_')}" if (not staff_filter and selected_staff != "ALL") else (f"_Staff_{staff_filter.replace(' ', '_')}" if staff_filter else "")
    client_tag = f"_Client_{selected_client_report.replace(' ', '_')}" if (not staff_filter and selected_client_report != "ALL") else ""
    
    excel_bytes_reported = to_excel_bytes({'Reported_Vehicles': final_report_df})
    filename_reported = f"Reported_Vehicles_{file_date_str}_{status_tag}{staff_tag}{client_tag}.xlsx"

    st.download_button(
        label=f"📥 Download Reported Vehicles Excel",
        data=excel_bytes_reported,
        file_name=filename_reported,
        mime=EXCEL_MIME,
        type="primary",
        key=f"download_reported_{unique_key}"
    )

    if staff_filter:
        return

    # ================= ROUTE-WISE PERFORMANCE REPORT SECTION =================
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## 📍 Route-wise Performance Report")

    client_col_name = vendor_column(reported_df) or 'VendorName'
    route_client_options = ["ALL"] + sorted([str(x).strip() for x in reported_df[client_col_name].dropna().unique() if str(x).strip() != ""]) if client_col_name in reported_df.columns else ["ALL"]

    if staff_col:
        route_staff_list = ["ALL"] + sorted([str(x).strip() for x in reported_df[staff_col].dropna().unique() if str(x).strip() != ""])
    else:
        route_staff_list = ["ALL"]

    r_col1, r_col2 = st.columns(2)
    with r_col1:
        route_client_selected = st.selectbox(
            "🏢 Filter Route-wise by Client:",
            route_client_options,
            index=0,
            key=f"route_client_filter_{unique_key}"
        )
    with r_col2:
        route_staff_selected = st.selectbox(
            "👨‍💼 Filter Route-wise by Controlling Staff:",
            route_staff_list,
            index=0,
            key=f"route_staff_filter_{unique_key}"
        )

    route_base_df = reported_df.copy()
    if route_client_selected != "ALL" and client_col_name in route_base_df.columns:
        route_base_df = route_base_df[route_base_df[client_col_name].astype(str).str.strip() == route_client_selected].copy()
    if route_staff_selected != "ALL" and staff_col:
        route_base_df = route_base_df[route_base_df[staff_col].astype(str).str.strip() == route_staff_selected].copy()

    from_c = find_col(route_base_df, exact=('from',))
    dest_c = find_col(route_base_df, exact=('destination', 'to'))
    client_c = 'Party' if 'Party' in final_report_df.columns else client_col_name

    if from_c and dest_c:
        route_base_df['Route'] = route_base_df[from_c].astype(str).str.upper().str.strip() + " ➔ " + route_base_df[dest_c].astype(str).str.upper().str.strip()
    else:
        route_base_df['Route'] = "N/A"

    late_col = next((c for c in ['Late Hrs', 'Delay Hrs', 'Delay'] if c in route_base_df.columns), None)
    if 'Status_Category' not in route_base_df.columns and late_col:
        route_base_df['Status_Category'] = route_base_df[late_col].apply(lambda v: DELAY if not is_zero_late(v) else ONTIME)

    route_summary = []
    if not route_base_df.empty:
        group_keys = ['Route']
        if client_c and client_c in route_base_df.columns:
            group_keys.append(client_c)

        grouped = route_base_df.groupby(group_keys)
        for name, g_df in grouped:
            if isinstance(name, tuple):
                route, client = name
            else:
                route, client = name, "ALL"

            total = len(g_df)
            ontime = int((g_df['Status_Category'] == ONTIME).sum()) if 'Status_Category' in g_df.columns else total
            delay = int((g_df['Status_Category'] == DELAY).sum()) if 'Status_Category' in g_df.columns else 0
            perf_pct = f"{round((ontime / total) * 100, 1)}%" if total > 0 else "0%"

            route_summary.append({
                "Route": route,
                "Client": client,
                "Total Trips": total,
                "On-Time Trips": ontime,
                "Delay Trips": delay,
                "Performance (%)": perf_pct
            })

    if route_summary:
        route_df = pd.DataFrame(route_summary).sort_values(by="Total Trips", ascending=False)
        route_df.insert(0, 'S.No', range(1, 1 + len(route_df)))
        st.markdown(render_html_table(route_df), unsafe_allow_html=True)

        route_client_tag = f"_Client_{route_client_selected.replace(' ', '_')}" if route_client_selected != "ALL" else ""
        route_staff_tag = f"_Staff_{route_staff_selected.replace(' ', '_')}" if route_staff_selected != "ALL" else ""
        excel_bytes_route = to_excel_bytes({'Route_Performance': route_df})
        filename_route = f"Route_Performance{route_client_tag}{route_staff_tag}.xlsx"

        st.download_button(
            label="📥 Download Route-wise Performance Excel",
            data=excel_bytes_route,
            file_name=filename_route,
            mime=EXCEL_MIME,
            type="secondary",
            key=f"download_route_perf_{unique_key}"
        )
    else:
        st.info("Route-wise performance ke liye koi data available nahi hai.")


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
            is_callout = ('callout' in fname) or has_category or ('breakdown' in fname)

            if is_callout:
                cat_col = next((c for c in temp_df.columns if 'category' in c.lower() or 'cat' in c.lower()), None)
                if cat_col:
                    allowed_cats = ['breakdown', 'accident', 'tyre blast', 'tyre puncher', 'tyre blast / puncture', 'puncher']
                    def check_cat(val):
                        s = str(val).lower().strip()
                        return any(kw in s for kw in allowed_cats)
                    temp_df = temp_df[temp_df[cat_col].apply(check_cat)].copy()

                vendor_c = vendor_column(temp_df)
                if vendor_c:
                    temp_df['VendorName'] = temp_df[vendor_c].apply(clean_party)
                    temp_df = temp_df[temp_df['VendorName'].isin(['DHL', 'Busybees', 'Trackon'])].copy()

                date_col = next((c for c in temp_df.columns if 'date' in c.lower() or 'desp' in c.lower() or 'time' in c.lower()), None)
                if date_col:
                    temp_df['Parsed_Date'] = pd.to_datetime(temp_df[date_col], errors='coerce', dayfirst=True)

                callout_dfs.append(temp_df)
            else:
                desp_col = next((c for c in temp_df.columns if 'desp' in c.lower() or 'dispatch' in c.lower()), None)
                if desp_col:
                    temp_df = temp_df[~temp_df[desp_col].apply(is_blank)].copy()

                vendor_c = vendor_column(temp_df)
                if vendor_c:
                    temp_df['VendorName'] = temp_df[vendor_c].apply(lambda v: clean_party(v) if clean_party(v) else str(v).strip())
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


# ================= MEMORY SETUP =================
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

if 'logged_in_staff' not in st.session_state:
    st.session_state.logged_in_staff = None

st.sidebar.markdown("---")
if st.session_state.logged_in_staff is None:
    st.sidebar.markdown("🔐 **Login Portal**")
    login_mode = st.sidebar.radio("Login as:", ["Admin / Vendor", "Controlling Staff"], label_visibility="collapsed")
    
    if login_mode == "Controlling Staff":
        s_user = st.sidebar.text_input("Staff Username")
        s_pass = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Staff Login", use_container_width=True):
            user_key = s_user.strip().lower()
            if user_key in st.session_state.staff_users and st.session_state.staff_users[user_key]["pass"] == s_pass:
                st.session_state.logged_in_staff = st.session_state.staff_users[user_key]["staff_name"]
                st.sidebar.success(f"Welcome, {st.session_state.logged_in_staff}!")
                st.rerun()
            else:
                st.sidebar.error("Invalid Username or Password!")
        st.sidebar.markdown("---")

else:
    st.sidebar.success(f"Logged in as Staff: **{st.session_state.logged_in_staff}**")
    if st.sidebar.button("Logout Staff", use_container_width=True):
        st.session_state.logged_in_staff = None
        st.rerun()
    st.sidebar.markdown("---")

if st.session_state.logged_in_staff is None:
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
        "🚚 In-Transit Vehicle Status",
        "📈 Monthly Breakdown",
        "🔐 User & Access Control"
    ], label_visibility="collapsed")

else:
    selected_nav = "📊 Dashboard"
    st.sidebar.info("Controlling staff mode: View-only access enabled for assigned vehicles.")


# ================= MAIN PAGE LOGIC =================
if "Dashboard" in selected_nav:
    st.title("⚡ Sales Manager Live Monitoring Dashboard")
    st.info("🔒 **Restricted Vendor View:** Callout Count & Overall Performance")

    has_callout = st.session_state.callout_data is not None and not st.session_state.callout_data.empty
    has_mis = st.session_state.mis_data is not None and not st.session_state.mis_data.empty

    if has_callout or has_mis:
        callout_df = st.session_state.callout_data if has_callout else pd.DataFrame()
        mis_df = st.session_state.mis_data if has_mis else pd.DataFrame()

        st.markdown("---")
        
        # --- EXCLUSIVE CALLOUT FILTER DROPDOWN ---
        st.markdown("### 🔍 Filter Total Callout Count")
        callout_client_options = ["ALL", "DHL", "Busybees", "Trackon"]
        selected_callout_client = st.selectbox("🏢 Select Client for Callout Count:", callout_client_options, key="exclusive_callout_client_dropdown")

        filtered_callout = callout_df.copy()
        
        # Apply exclusive client filter to callout data only
        if selected_callout_client != "ALL" and not filtered_callout.empty and 'VendorName' in filtered_callout.columns:
            filtered_callout = filtered_callout[filtered_callout['VendorName'].str.upper() == selected_callout_client.upper()]

        total_callouts = len(filtered_callout)
        co_has_vendor = not filtered_callout.empty and 'VendorName' in filtered_callout.columns
        
        dhl_c = int((filtered_callout['VendorName'] == 'DHL').sum()) if co_has_vendor else 0
        busy_c = int((filtered_callout['VendorName'] == 'Busybees').sum()) if co_has_vendor else 0
        trk_c = int((filtered_callout['VendorName'] == 'Trackon').sum()) if co_has_vendor else 0

        def get_m_breakdown(m_num, c_name):
            if co_has_vendor and 'Parsed_Date' in filtered_callout.columns:
                return int(((filtered_callout['Parsed_Date'].dt.month == m_num) & (filtered_callout['VendorName'] == c_name)).sum())
            return 0

        aug_dhl, aug_busy, aug_trk = get_m_breakdown(8, 'DHL'), get_m_breakdown(8, 'Busybees'), get_m_breakdown(8, 'Trackon')
        sept_dhl, sept_busy, sept_trk = get_m_breakdown(9, 'DHL'), get_m_breakdown(9, 'Busybees'), get_m_breakdown(9, 'Trackon')
        oct_dhl, oct_busy, oct_trk = get_m_breakdown(10, 'DHL'), get_m_breakdown(10, 'Busybees'), get_m_breakdown(10, 'Trackon')

        filtered_mis = mis_df.copy()
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
            col1_html = (
                f'<div class="metric-card" style="min-height: 200px;">'
                f'<div class="metric-title">📊 TOTAL CALLOUT COUNT ({selected_callout_client.upper()})</div>'
                f'<div class="metric-value">{total_callouts}</div>'
                f'<div class="metric-sub-green" style="margin-bottom: 6px;">Breakdown, Accident, Tyre Blast & Puncher</div>'
                f'<div style="display: flex; justify-content: space-between; font-size: 13px; margin-top: 6px; padding-top: 6px; border-top: 1px solid #48cae4; color: #ffffff; font-weight:700;">'
                f'<span>DHL: <b style="color:#2ec4b6; font-size:16px;">{dhl_c}</b></span>'
                f'<span>Busybees: <b style="color:#ffb703; font-size:16px;">{busy_c}</b></span>'
                f'<span>Trackon: <b style="color:#e63946; font-size:16px;">{trk_c}</b></span>'
                f'</div>'
                f'<div style="font-size: 11px; color: #90e0ef; margin-top: 10px; font-weight: 800; text-transform: uppercase;">August Breakdown</div>'
                f'<div style="display: flex; justify-content: space-between; font-size: 12px; color: #ffffff; font-weight:600;">'
                f'<span>DHL: <b style="color:#2ec4b6;">{aug_dhl}</b></span>'
                f'<span>Busybees: <b style="color:#ffb703;">{aug_busy}</b></span>'
                f'<span>Trackon: <b style="color:#e63946;">{aug_trk}</b></span>'
                f'</div>'
                f'<div style="font-size: 11px; color: #90e0ef; margin-top: 8px; font-weight: 800; text-transform: uppercase;">September Breakdown</div>'
                f'<div style="display: flex; justify-content: space-between; font-size: 12px; color: #ffffff; font-weight:600;">'
                f'<span>DHL: <b style="color:#2ec4b6;">{sept_dhl}</b></span>'
                f'<span>Busybees: <b style="color:#ffb703;">{sept_busy}</b></span>'
                f'<span>Trackon: <b style="color:#e63946;">{sept_trk}</b></span>'
                f'</div>'
                f'<div style="font-size: 11px; color: #90e0ef; margin-top: 8px; font-weight: 800; text-transform: uppercase;">October Breakdown</div>'
                f'<div style="display: flex; justify-content: space-between; font-size: 12px; color: #ffffff; font-weight:600;">'
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
                f'<div style="font-size: 32px; font-weight: 900; color: #ffffff; margin-top: 4px;">{total_trips}</div>'
                f'<div style="font-size: 12px; color: #8d99ae; margin-top: 2px;">Performance Trips</div>'
                f'</div>'
                f'<div style="border-left: 1px solid #48cae4; height: 55px;"></div>'
                f'<div>'
                f'<div style="font-size: 12px; color: #90e0ef; font-weight: 800; text-transform: uppercase;">On-Time</div>'
                f'<div style="font-size: 32px; font-weight: 900; color: #2ec4b6; margin-top: 4px;">{ontime_trips}</div>'
                f'<div style="font-size: 14px; font-weight: 900; color: #2ec4b6; margin-top: 2px;">{ontime_pct}%</div>'
                f'</div>'
                f'<div style="border-left: 1px solid #48cae4; height: 55px;"></div>'
                f'<div>'
                f'<div style="font-size: 12px; color: #90e0ef; font-weight: 800; text-transform: uppercase;">Delay</div>'
                f'<div style="font-size: 32px; font-weight: 900; color: #e63946; margin-top: 4px;">{delay_trips}</div>'
                f'<div style="font-size: 14px; font-weight: 900; color: #e63946; margin-top: 2px;">{delay_pct}%</div>'
                f'</div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(col2_html, unsafe_allow_html=True)

        with col3:
            lb_clients = ['DHL', 'Busybees', 'Trackon']
            lb_rows_html = ""
            for c_name in lb_clients:
                c_df = perf_mis[perf_mis['VendorName'].str.upper() == c_name.upper()] if not perf_mis.empty else pd.DataFrame()
                c_tot = len(c_df)
                c_ontime = int((c_df['Status_Category'] == ONTIME).sum()) if not c_df.empty and 'Status_Category' in c_df.columns else 0
                c_delay = int((c_df['Status_Category'] == DELAY).sum()) if not c_df.empty and 'Status_Category' in c_df.columns else 0

                lb_rows_html += (
                    f'<div style="border-top: 1px solid #48cae4; padding-top: 8px; margin-top: 8px;">'
                    f'<div style="display: flex; justify-content: space-between; font-size: 14px; font-weight: 900;">'
                    f'<span style="color: #ffffff;">{c_name}</span>'
                    f'<span style="color: #90e0ef;">Total: <b>{c_tot}</b></span>'
                    f'</div>'
                    f'<div style="display: flex; justify-content: space-between; font-size: 13px; margin-top: 4px;">'
                    f'<span style="color: #2ec4b6;">On-Time: <b>{c_ontime}</b></span>'
                    f'<span style="color: #e63946;">Delay: <b>{c_delay}</b></span>'
                    f'</div>'
                    f'</div>'
                )

            col3_html = (
                f'<div class="metric-card" style="min-height: 200px;">'
                f'<div class="metric-title">🏆 TARGET CLIENTS LEADERBOARD</div>'
                f'{lb_rows_html}'
                f'</div>'
            )
            st.markdown(col3_html, unsafe_allow_html=True)

        if not mis_df.empty:
            show_reported_vehicle_table(mis_df, unique_key="dash")
        else:
            st.warning("Is selection ke liye koi data available nahi hai.")
    else:
        st.info("👈 Kripya Sidebar se apni Callout aur MIS Performance files upload karein aur 'Process Data' par click karein.")

# ----------------- OTHER PAGES -----------------
elif "Client Performance" in selected_nav:
    st.title("🎯 Customer-wise Performance Speedometer")
    if st.session_state.mis_data is not None and not st.session_state.mis_data.empty:
        show_reported_vehicle_table(st.session_state.mis_data, unique_key="client_perf")
    else:
        st.info("👈 Kripya pehle MIS file upload karein.")

else:
    st.title(selected_nav)
    st.info("🚧 Yeh page abhi active hai.")
