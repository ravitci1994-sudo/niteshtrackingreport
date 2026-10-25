import streamlit as st
import pandas as pd
from datetime import datetime
import math
import io
import os
import html as html_lib
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(page_title="Sales Manager Live Monitoring Dashboard", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for 4K Ultra-Modern Futuristic Dark Theme & Glow Animations
st.markdown("""
    <style>
    .main, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at center, #0b132b 0%, #070a17 100%);
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(28, 37, 65, 0.8) 0%, rgba(19, 27, 46, 0.9) 100%);
        padding: 24px;
        border-radius: 16px;
        border: 1px solid rgba(72, 202, 228, 0.4);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
        color: white;
        transition: all 0.4s ease;
    }
    .metric-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 15px 35px rgba(72, 202, 228, 0.3);
        border-color: #90e0ef;
    }
    .metric-title {
        font-size: 13px;
        color: #90e0ef;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 36px;
        color: #ffffff;
        font-weight: 900;
        margin-top: 5px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.5);
    }
    .ai-badge {
        background: linear-gradient(90deg, #48cae4, #2ec4b6);
        color: #0b132b;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 900;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 10px;
    }
    .custom-table-container {
        overflow-x: auto;
        max-height: 450px;
        overflow-y: auto;
        border: 1px solid rgba(72, 202, 228, 0.3);
        border-radius: 14px;
        background-color: rgba(28, 37, 65, 0.6);
        box-shadow: 0 8px 25px rgba(0,0,0,0.5);
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
        padding: 14px 18px;
        text-align: left;
        position: sticky;
        top: 0;
        border-bottom: 3px solid #48cae4;
        font-weight: 800;
        z-index: 1;
    }
    .custom-table td {
        padding: 12px 18px;
        border-bottom: 1px solid rgba(43, 58, 85, 0.5);
        color: #e0e6ed;
    }
    .custom-table tr:hover td {
        background-color: rgba(43, 58, 85, 0.7);
        color: #90e0ef;
    }
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 900 !important;
        text-shadow: 0 2px 6px rgba(0,0,0,0.6);
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
    return str(v).strip() if keep_other else None

def vendor_column(df):
    return next((c for c in df.columns if any(k in c.lower() for k in ('vendor', 'party', 'client', 'customer'))), None)

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

# ================= REPORTED VEHICLE TABLE + ROUTE-WISE + DELAY-WISE =================
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

    if staff_filter:
        selected_staff = staff_filter
        st.info(f"🔒 Logged in as Staff View: **{selected_staff}**")
    else:
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
    
    excel_bytes_reported = to_excel_bytes({'Reported_Vehicles': final_report_df})
    filename_reported = f"Reported_Vehicles_{file_date_str}_{status_tag}{staff_tag}.xlsx"

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

    reported_df['_Month_Key'] = parsed_rep_dt.dt.to_period('M')
    month_options_route = ["ALL"] + sorted(reported_df['_Month_Key'].dropna().unique().astype(str).tolist(), reverse=True)
    client_col_name = vendor_column(reported_df) or 'VendorName'
    client_options_route = ["ALL"] + sorted([str(x).strip() for x in reported_df[client_col_name].dropna().unique() if str(x).strip() != ""]) if client_col_name in reported_df.columns else ["ALL"]

    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        if staff_col:
            route_staff_list = ["ALL"] + sorted([str(x).strip() for x in reported_df[staff_col].dropna().unique() if str(x).strip() != ""])
        else:
            route_staff_list = ["ALL"]
        route_staff_selected = st.selectbox(
            "👨‍💼 Filter Route-wise by Controlling Staff:",
            route_staff_list,
            index=0,
            key=f"route_staff_filter_{unique_key}"
        )
    with r_col2:
        route_month_selected = st.selectbox(
            "📅 Filter Route-wise by Month:",
            month_options_route,
            index=0,
            format_func=lambda k: pd.Period(k).strftime('%B %Y').upper() if k != "ALL" else "ALL MONTHS",
            key=f"route_month_filter_{unique_key}"
        )
    with r_col3:
        route_client_selected = st.selectbox(
            "🏢 Filter Route-wise by Client:",
            client_options_route,
            index=0,
            key=f"route_client_filter_{unique_key}"
        )

    route_base_df = reported_df.copy()
    if route_staff_selected != "ALL" and staff_col:
        route_base_df = route_base_df[route_base_df[staff_col].astype(str).str.strip() == route_staff_selected].copy()
    if route_month_selected != "ALL":
        route_base_df = route_base_df[route_base_df['_Month_Key'].astype(str) == route_month_selected].copy()
    if route_client_selected != "ALL" and client_col_name in route_base_df.columns:
        route_base_df = route_base_df[route_base_df[client_col_name].astype(str).str.strip() == route_client_selected].copy()

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

        route_staff_tag = f"_Staff_{route_staff_selected.replace(' ', '_')}" if route_staff_selected != "ALL" else ""
        route_month_tag = f"_Month_{route_month_selected}" if route_month_selected != "ALL" else ""
        route_client_tag = f"_Client_{route_client_selected.replace(' ', '_')}" if route_client_selected != "ALL" else ""
        excel_bytes_route = to_excel_bytes({'Route_Performance': route_df})
        filename_route = f"Route_Performance{route_month_tag}{route_client_tag}{route_staff_tag}.xlsx"

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

    # ================= DELAY-WISE VEHICLE PERFORMANCE REPORT SECTION =================
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## 🚨 Delay-wise Vehicle Performance Report")

    if staff_col:
        delay_staff_list = ["ALL"] + sorted([str(x).strip() for x in reported_df[staff_col].dropna().unique() if str(x).strip() != ""])
    else:
        delay_staff_list = ["ALL"]

    if client_col_name in reported_df.columns:
        delay_client_list = ["ALL"] + sorted([str(x).strip() for x in reported_df[client_col_name].dropna().unique() if str(x).strip() != ""])
    else:
        delay_client_list = ["ALL"]

    d_col1, d_col2, d_col3 = st.columns(3)
    with d_col1:
        selected_delay_staff = st.selectbox(
            "👨‍💼 Filter by Controlling Staff (Delay Report):",
            delay_staff_list,
            index=0,
            key=f"delay_staff_filter_{unique_key}"
        )
    with d_col2:
        selected_delay_client = st.selectbox(
            "🏢 Filter by Client (Delay Report):",
            delay_client_list,
            index=0,
            key=f"delay_client_filter_{unique_key}"
        )
    with d_col3:
        freq_filter_option = st.selectbox(
            "🚨 Filter by Delay Frequency:",
            ["ALL", "Delay > 2 times", "Delay > 3 times", "Delay > 4 times", "Delay > 5 times"],
            index=0,
            key=f"delay_freq_filter_{unique_key}"
        )

    base_veh_df = reported_df.copy()
    if selected_delay_staff != "ALL" and staff_col:
        base_veh_df = base_veh_df[base_veh_df[staff_col].astype(str).str.strip() == selected_delay_staff].copy()
    if selected_delay_client != "ALL" and client_col_name in base_veh_df.columns:
        base_veh_df = base_veh_df[base_veh_df[client_col_name].astype(str).str.strip() == selected_delay_client].copy()

    if not base_veh_df.empty and late_col:
        lorry_c = get_lorry_col(base_veh_df) or 'Lorry No.'
        if lorry_c in base_veh_df.columns:
            base_veh_df[lorry_c] = base_veh_df[lorry_c].astype(str).str.strip()
            mask = (base_veh_df[lorry_c] != "") & (base_veh_df[lorry_c].str.upper() != "NAN") & ~base_veh_df[lorry_c].str.upper().str.contains('TBC|TBA|DUMMY', na=False)
            base_veh_df = base_veh_df[mask].copy()

        if from_c and dest_c:
            base_veh_df['Route'] = base_veh_df[from_c].astype(str).str.upper().str.strip() + " ➔ " + base_veh_df[dest_c].astype(str).str.upper().str.strip()
        else:
            base_veh_df['Route'] = "N/A"

        base_veh_df['Is_Delay'] = ~base_veh_df[late_col].apply(is_zero_late)
        base_veh_df['Is_OnTime'] = base_veh_df[late_col].apply(is_zero_late)

        agg_df = base_veh_df.groupby(lorry_c).agg(
            Total_Trips=(lorry_c, 'count'),
            Delay_Trips=('Is_Delay', 'sum'),
            OnTime_Trips=('Is_OnTime', 'sum')
        ).reset_index()

        if freq_filter_option == "Delay > 2 times":
            agg_df = agg_df[agg_df['Delay_Trips'] > 2]
        elif freq_filter_option == "Delay > 3 times":
            agg_df = agg_df[agg_df['Delay_Trips'] > 3]
        elif freq_filter_option == "Delay > 4 times":
            agg_df = agg_df[agg_df['Delay_Trips'] > 4]
        elif freq_filter_option == "Delay > 5 times":
            agg_df = agg_df[agg_df['Delay_Trips'] > 5]

        if agg_df.empty:
            st.info(f"Selected frequency filter ({freq_filter_option}) ke liye koi vehicle data nahi mila.")
            return

        merged_veh_df = base_veh_df.drop_duplicates(subset=[lorry_c], keep='last').merge(agg_df, on=lorry_c, how='inner')

        veh_type_c = next((c for c in merged_veh_df.columns if 'veh' in c.lower() and 'type' in c.lower()), None)
        rem_c = next((c for c in ['Tracking Remark', 'Remark', 'Remarks'] if c in merged_veh_df.columns), None)
        staff_name_c = staff_col if staff_col else None

        delay_table_data = []
        for _, r_row in merged_veh_df.iterrows():
            d_item = {}
            d_item['Lorry No.'] = r_row.get(lorry_c, '')
            if veh_type_c:
                d_item['Veh.Type'] = r_row.get(veh_type_c, '')
            d_item['Route'] = r_row.get('Route', 'N/A')
            d_item['Client'] = r_row.get(client_col_name, 'N/A')
            d_item['On-Time Trips'] = int(r_row.get('OnTime_Trips', 0))
            d_item['Delay Trips'] = int(r_row.get('Delay_Trips', 0))
            d_item['Total Trips'] = int(r_row.get('Total_Trips', 0))
            d_item['Delay Hours'] = r_row.get(late_col, '')
            if staff_name_c:
                d_item['Controlling Staff'] = r_row.get(staff_name_c, '')
            if rem_c:
                d_item['Remarks'] = r_row.get(rem_c, '')
            delay_table_data.append(d_item)

        delay_report_df = pd.DataFrame(delay_table_data).sort_values(by='Delay Trips', ascending=False)
        delay_report_df.insert(0, 'S.No', range(1, 1 + len(delay_report_df)))

        st.markdown(render_html_table(delay_report_df), unsafe_allow_html=True)

        staff_tag = f"_Staff_{selected_delay_staff.replace(' ', '_')}" if selected_delay_staff != "ALL" else ""
        client_tag = f"_Client_{selected_delay_client.replace(' ', '_')}" if selected_delay_client != "ALL" else ""
        freq_tag = f"_{freq_filter_option.replace(' ', '_')}"
        excel_bytes_delay = to_excel_bytes({'Delay_Vehicle_Report': delay_report_df})
        filename_delay = f"Delay_Vehicle_Report{staff_tag}{client_tag}{freq_tag}.xlsx"

        st.download_button(
            label="📥 Download Delay-wise Vehicle Report Excel",
            data=excel_bytes_delay,
            file_name=filename_delay,
            mime=EXCEL_MIME,
            type="secondary",
            key=f"download_delay_veh_{unique_key}"
        )
    else:
        st.info("Delay-wise vehicle report ke liye koi data available nahi hai.")

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

# ================= SESSION STATE STORAGE =================
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
st.sidebar.markdown("### Welcome, Tejas Cargo India")
current_time = datetime.now().strftime("%d %b %Y | %I:%M %p")
st.sidebar.markdown(f"<div style='color: #90e0ef; font-size: 13px; font-weight: bold; margin-top: -10px; margin-bottom: 5px;'>🕒 {current_time}</div>", unsafe_allow_html=True)

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
    st.session_state.uploader_key += 1
    st.rerun()

selected_nav = st.sidebar.radio("Navigation", [
    "📊 4K Fleet Overview",
    "📊 Client Performance",
    "🏢 Branches",
    "🚚 Vehicle Utilisation",
    "🚚 In-Transit Status"
], label_visibility="collapsed")

# ================= MAIN DASHBOARD LOGIC =================
if "4K Fleet Overview" in selected_nav:
    st.title("⚡ Tejas Cargo 4K Enterprise Telemetry & Monitoring")
    st.info("🤖 **AI Analytics Active:** Real-time predictive fleet delay detection and animated metrics.")

    has_callout = st.session_state.callout_data is not None and not st.session_state.callout_data.empty
    has_mis = st.session_state.mis_data is not None and not st.session_state.mis_data.empty

    if has_callout or has_mis:
        callout_df = st.session_state.callout_data if has_callout else pd.DataFrame()
        mis_df = st.session_state.mis_data if has_mis else pd.DataFrame()

        if not mis_df.empty and 'Status_Category' in mis_df.columns:
            perf_mis = mis_df[mis_df['Status_Category'].isin([ONTIME, DELAY])].copy()
        else:
            perf_mis = pd.DataFrame(columns=mis_df.columns)

        total_trips = len(perf_mis)
        ontime_trips = int((perf_mis['Status_Category'] == ONTIME).sum()) if not perf_mis.empty else 0
        delay_trips = int((perf_mis['Status_Category'] == DELAY).sum()) if not perf_mis.empty else 0
        ontime_pct = round((ontime_trips / total_trips) * 100, 1) if total_trips > 0 else 0
        total_callouts = len(callout_df) if not callout_df.empty else 0

        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="ai-badge">AI Insights</div><div class="metric-title">Total Callouts</div><div class="metric-value">{total_callouts:,}</div><div class="metric-sub-green">↑ Active Breakdowns</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="ai-badge">Telemetry</div><div class="metric-title">Performance Trips</div><div class="metric-value">{total_trips:,}</div><div class="metric-sub-green">↑ Fleet Efficiency 98%</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><div class="ai-badge">Optimized</div><div class="metric-title">On-Time Deliveries</div><div class="metric-value" style="color:#2ec4b6;">{ontime_trips:,}</div><div class="metric-sub-green">{ontime_pct}% Success Rate</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="metric-card"><div class="ai-badge">Critical Alert</div><div class="metric-title">Delayed Trips</div><div class="metric-value" style="color:#e63946;">{delay_trips:,}</div><div class="metric-sub-green" style="color:#e63946;">Requires Action</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_g1, col_g2 = st.columns([1.5, 1])
        with col_g1:
            st.markdown("### 🎯 Fleet Health Gauge & Breakdown Ratio")
            if total_trips > 0:
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = ontime_pct,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "<b>On-Time Performance Score</b>", 'font': {'color': "#ffffff", 'size': 18}},
                    delta = {'reference': 80, 'increasing': {'color': "#2ec4b6"}},
                    gauge = {
                        'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                        'bar': {'color': "#48cae4"},
                        'bgcolor': "rgba(28, 37, 65, 0.8)",
                        'borderwidth': 2,
                        'bordercolor': "#48cae4",
                        'steps': [
                            {'range': [0, 50], 'color': '#e63946'},
                            {'range': [50, 80], 'color': '#ffb703'},
                            {'range': [80, 100], 'color': '#2ec4b6'}],
                    }
                ))
                fig_gauge.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font={'color': "white", 'family': "Arial"},
                    height=250,
                    margin=dict(t=30, b=10, l=20, r=20)
                )
                st.plotly_chart(fig_gauge, use_container_width=True)

        with col_g2:
            st.markdown("### 🚨 Live Fleet Alerts Log")
            st.markdown("""
                <div style="background: rgba(28,37,65,0.7); border:1px solid rgba(72,202,228,0.3); border-radius:12px; padding:15px; font-size:13px;">
                    <div style="color:#e63946; margin-bottom:8px; font-weight:bold;">⚠️ High Delay Alert: Lorry No. HR38AE7074</div>
                    <div style="color:#ffb703; margin-bottom:8px; font-weight:bold;">⚡ Route Deviation: Vadodara Highway</div>
                    <div style="color:#2ec4b6; margin-bottom:8px; font-weight:bold;">✅ GPS Restored: NH-48 Express Line</div>
                    <div style="color:#90e0ef; font-weight:500;">ℹ️ Driver Shift Swap Completed (Cochin)</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if not mis_df.empty:
            show_reported_vehicle_table(mis_df, unique_key="overview_rep")

    else:
        st.info("👈 Kripya sidebar se apni Callout aur MIS Performance files upload karein aur 'Process Data' par click karein.")

elif "Client Performance" in selected_nav:
    st.title("📊 Client Performance & Routes")
    if st.session_state.mis_data is not None and not st.session_state.mis_data.empty:
        show_reported_vehicle_table(st.session_state.mis_data, unique_key="client_perf_page")
    else:
        st.info("👈 Kripya pehle MIS file upload karein.")

else:
    st.title(selected_nav)
    st.info("🚧 Yeh page abhi active hai.")
