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


def clean_party(v, keep_other=True):
    if is_blank(v):
        return "Other"
    v_str = str(v).upper().strip()
    if "DHL" in v_str:
        return "DHL"
    elif "BUSYBEE" in v_str:
        return "Busybees"
    elif "TRACKON" in v_str:
        return "Trackon"
    return str(v).strip() if keep_other else "Other"


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


# ================= FILE PROCESSING =================
def process_uploaded_files(uploaded_files):
    callout_dfs = []
    mis_dfs = []

    for uploaded_file in uploaded_files:
        try:
            if uploaded_file.name.lower().endswith('.csv'):
                temp_df = pd.read_csv(uploaded_file, low_memory=False)
            else:
                temp_df = pd.read_excel(uploaded_file)

            temp_df.columns = temp_df.columns.astype(str).str.strip()
            fname = uploaded_file.name.lower()
            
            has_category = any(kw in c.lower() for c in temp_df.columns for kw in ['category', 'cat', 'callout', 'reason', 'breakdown', 'issue'])
            is_callout = ('callout' in fname) or has_category or ('breakdown' in fname)

            if is_callout:
                cat_col = next((c for c in temp_df.columns if any(kw in c.lower() for kw in ['category', 'cat', 'reason', 'issue'])), None)
                if cat_col:
                    allowed_keywords = ['breakdown', 'break down', 'accident', 'tyre', 'tire', 'puncture', 'puncher', 'blast']
                    def check_cat(val):
                        if is_blank(val):
                            return False
                        s = str(val).lower().strip()
                        return any(kw in s for kw in allowed_keywords)
                    temp_df = temp_df[temp_df[cat_col].apply(check_cat)].copy()

                vendor_c = vendor_column(temp_df)
                if vendor_c:
                    temp_df['VendorName'] = temp_df[vendor_c].apply(lambda x: clean_party(x, keep_other=True))

                date_col = next((c for c in temp_df.columns if 'date' in c.lower() or 'desp' in c.lower() or 'time' in c.lower()), None)
                if date_col:
                    temp_df['Parsed_Date'] = pd.to_datetime(temp_df[date_col], errors='coerce', dayfirst=True)

                callout_dfs.append(temp_df)
            else:
                desp_col = next((c for c in temp_df.columns if 'desp' in c.lower() or 'date' in c.lower() or 'time' in c.lower()), None)
                if desp_col:
                    temp_df['Parsed_Date'] = pd.to_datetime(temp_df[desp_col], errors='coerce', dayfirst=True)

                vendor_c = vendor_column(temp_df)
                if vendor_c:
                    temp_df['VendorName'] = temp_df[vendor_c].apply(lambda x: clean_party(x, keep_other=True))
                else:
                    temp_df['VendorName'] = "Other"

                late_col = next((c for c in ['Late Hrs', 'Delay Hrs', 'Delay'] if c in temp_df.columns), None)
                if late_col:
                    temp_df['Status_Category'] = temp_df[late_col].apply(lambda v: DELAY if not is_zero_late(v) else ONTIME)
                else:
                    temp_df['Status_Category'] = ONTIME

                mis_dfs.append(temp_df)

        except Exception as e:
            st.error(f"Error processing file {uploaded_file.name}: {e}")

    combined_callout = pd.concat(callout_dfs, ignore_index=True) if callout_dfs else pd.DataFrame()
    combined_mis = pd.concat(mis_dfs, ignore_index=True) if mis_dfs else pd.DataFrame()
    return combined_callout, combined_mis


# ================= MAIN APP =================
def main():
    st.title("🚀 Sales Manager Live Monitoring Dashboard")
    st.markdown("Upload your MIS or Callout files to view real-time trip performance and statistics.")

    # Initialize Session State for Data Persistence
    if 'stored_callout_df' not in st.session_state:
        st.session_state.stored_callout_df = pd.DataFrame()
    if 'stored_mis_df' not in st.session_state:
        st.session_state.stored_mis_df = pd.DataFrame()
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False

    # Sidebar Controls
    st.sidebar.header("📁 Data Management")
    uploaded_files = st.sidebar.file_uploader("Upload MIS / Callout Excel or CSV", type=["xlsx", "csv"], accept_multiple_files=True)

    if uploaded_files:
        if st.sidebar.button("💾 Process & Save Data", type="primary"):
            c_df, m_df = process_uploaded_files(uploaded_files)
            st.session_state.stored_callout_df = c_df
            st.session_state.stored_mis_df = m_df
            st.session_state.data_loaded = True
            st.sidebar.success("Data successfully loaded and saved!")

    if st.sidebar.button("🗑️ Remove Data", type="secondary"):
        st.session_state.stored_callout_df = pd.DataFrame()
        st.session_state.stored_mis_df = pd.DataFrame()
        st.session_state.data_loaded = False
        st.sidebar.warning("Data has been removed.")
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.header("📊 Dashboard Navigation")
    app_mode = st.sidebar.selectbox("Choose View", ["Main MIS Dashboard", "Callout Summary", "Staff Login Portal"])

    # Access stored data from session state
    callout_df = st.session_state.stored_callout_df
    mis_df = st.session_state.stored_mis_df

    if not st.session_state.data_loaded and mis_df.empty and callout_df.empty:
        st.info("Kripya sidebar mein files upload karke 'Process & Save Data' button par click karein.")
        return

    if app_mode == "Main MIS Dashboard":
        st.header("📈 Main MIS Performance Dashboard")
        if not mis_df.empty:
            show_reported_vehicle_table(mis_df, unique_key="main_dashboard")
        else:
            st.warning("Koi MIS data available nahi hai ya remove kiya ja chuka hai.")

    elif app_mode == "Callout Summary":
        st.header("⚠️ Callout / Breakdown Summary")
        if not callout_df.empty:
            st.metric("TOTAL CALLOUT COUNT (ALL)", len(callout_df))
            st.markdown(render_html_table(callout_df), unsafe_allow_html=True)
        else:
            st.info("Koi Callout data available nahi hai.")

    elif app_mode == "Staff Login Portal":
        st.header("🔒 Staff Login Portal")
        staff_col = next((c for c in mis_df.columns if 'controlling' in c.lower() or 'staff' in c.lower()), None)
        if staff_col and not mis_df.empty:
            staff_names = sorted([str(x).strip() for x in mis_df[staff_col].dropna().unique() if str(x).strip() != ""])
            selected_staff = st.selectbox("Select Staff Member", staff_names)
            if selected_staff:
                show_reported_vehicle_table(mis_df, unique_key="staff_portal", staff_filter=selected_staff)
        else:
            st.warning("Controlling Staff column nahi mila ya MIS data khali hai.")

if __name__ == '__main__':
    main()
