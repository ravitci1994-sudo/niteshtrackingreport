import streamlit as st
import pandas as pd
import numpy as np
import os

# Page Configuration
st.set_page_config(
    page_title="Nitesh - Fleet Analytics & MIS Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Glassmorphism & Neon Styling
st.markdown("""
<style>
    .main {
        background: radial-gradient(circle at 50% 0%, #1e1145 0%, #0d0621 50%, #05020d 100%);
        color: #e2e8f0;
    }
    .stMetric {
        background: rgba(25, 15, 55, 0.65);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(168, 85, 247, 0.2);
        padding: 15px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Persistent Storage Folder Setup
UPLOAD_DIR = "saved_fleet_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Helper: Precise Client/Party Name Normalization
def normalize_party(name):
    if pd.isna(name) or name == "":
        return "Other"
    s = str(name).strip()
    s_upper = s.upper()
    
    # Strict Client Name Standardization as requested
    if "DHL" in s_upper:
        return "DHL"
    if "BUSYBEE" in s_upper:
        return "Busybees"
    if "TRACKON" in s_upper:
        return "Trackon"
    if "AMAZON" in s_upper:
        return "Amazon"
    
    # Clean up corporate suffixes for others
    for suffix in [" PRIVATE LIMITED", " PVT LTD", " LTD", " (INDIA)", " SOLUTIONS", " COURIERS PVT. LTD."]:
        if s_upper.endswith(suffix):
            s = s[:-len(suffix)].strip()
            
    return s

# Helper: Blank Check
def is_blank(val):
    if pd.isna(val) or val is None:
        return True
    s = str(val).strip().lower()
    return s in ["", "nan", "nat", "none", "-", "0", "0.0"]

# Helper: Zero Late Check
def is_zero_late(val):
    if is_blank(val):
        return True
    s = str(val).strip().lower()
    if s in ["0", "0.0", "00:00", "0:00", "00:00:00"]:
        return True
    try:
        num = float(s)
        return num <= 0
    except ValueError:
        return False

# Sample Default Dataset
@st.cache_data
def get_sample_data():
    return pd.DataFrame([
        {
            "Lorry No.": "MH04AB1234", "Veh.Type": "15MT", "From": "DELHI", "Destination": "BHIWANDI", "KM": "1200", "Party": "DHL SUPPLY CHAIN INDIA PVT LTD",
            "Desp. Date & Time": "08/11/2026 13:04:00", "Hrs. Taken": "48h", "Expected Dly. Date & Time": "10/11/2026 12:00", "Hrs. Given": "50h",
            "1st Touching": "Surat", "1st Touching Reporting Date & Time": "09/11/2026 11:00", "1st Touching Delivery Date & Time": "09/11/2026 14:00", "1st Touching Hrs.": "3h",
            "2nd Touching": "Mumbai", "2nd Touching Reporting Date & Time": "10/11/2026 08:00", "2nd Touching Delivery Date & Time": "10/11/2026 10:00", "2nd Touching Hrs.": "2h",
            "Final Touching Reporting Date & Time": "10/11/2026 14:00",
            "Total Touching Hrs.": "5h", "Hrs. Taken with touching": "52h", "Hrs. Taken without touching (Dly.)": "47h", "Late Hrs": "0", 
            "Tracking Remark": "Delivered on time", "Group Name": "G1", "Controlling Staff Name": "Amit Kumar", "Foreman Name": "Rajesh"
        }
    ])

# Header Section
st.title("🚀 Fleet Analytics & MIS Dashboard")
st.markdown("Welcome back, **Nitesh** | Logistics Management System")

def process_data(df):
    processed = []
    for _, row in df.iterrows():
        new_row = {}
        for col in df.columns:
            clean_col = str(col).strip()
            val = row[col]
            
            if any(k in clean_col.lower() for k in ["party", "client", "vendor"]):
                val = normalize_party(val)
            
            new_row[clean_col] = val
        processed.append(new_row)
    return pd.DataFrame(processed)

# Load data from disk folder if available, else sample data
def load_persisted_data():
    files = os.listdir(UPLOAD_DIR)
    if files:
        df_list = []
        for f in files:
            f_path = os.path.join(UPLOAD_DIR, f)
            try:
                if f.endswith('.csv'):
                    df_temp = pd.read_csv(f_path)
                else:
                    df_temp = pd.read_excel(f_path)
                df_list.append(df_temp)
            except Exception:
                pass
        if df_list:
            return pd.concat(df_list, ignore_index=True), ", ".join(files)
    return get_sample_data(), "Default Fleet Sample"

if "saved_data" not in st.session_state:
    initial_df, src_name = load_persisted_data()
    st.session_state.saved_data = initial_df
    st.session_state.source_name = src_name

# Sidebar - Multiple File Upload & Remove Button
st.sidebar.header("📁 Data Source")
uploaded_files = st.sidebar.file_uploader(
    "Upload Multiple Excel/CSV Files", 
    type=["csv", "xlsx", "xls"], 
    accept_multiple_files=True,
    key="file_uploader_key"
)

# Remove Data Button
if st.sidebar.button("🗑️ Remove Uploaded Data"):
    for f in os.listdir(UPLOAD_DIR):
        os.remove(os.path.join(UPLOAD_DIR, f))
    st.session_state.saved_data = get_sample_data()
    st.session_state.source_name = "Default Fleet Sample"
    st.sidebar.success("Uploaded data removed successfully!")
    st.rerun()

if uploaded_files:
    for f in os.listdir(UPLOAD_DIR):
        os.remove(os.path.join(UPLOAD_DIR, f))
    
    df_list = []
    file_names = []
    for file in uploaded_files:
        file_names.append(file.name)
        f_path = os.path.join(UPLOAD_DIR, file.name)
        with open(f_path, "wb") as f:
            f.write(file.getbuffer())
        
        try:
            if file.name.endswith('.csv'):
                df_temp = pd.read_csv(f_path)
            else:
                df_temp = pd.read_excel(f_path)
            df_list.append(df_temp)
        except Exception as e:
            st.sidebar.error(f"Error loading {file.name}: {e}")
            
    if df_list:
        raw_df = pd.concat(df_list, ignore_index=True)
        st.session_state.saved_data = process_data(raw_df)
        st.session_state.source_name = ", ".join(file_names)

df = st.session_state.saved_data
st.sidebar.info(f"Loaded: {st.session_state.source_name}")

# Column Mappings & Detection
rep_cols = [c for c in df.columns if 'final touching reporting' in c.lower() or ('report' in c.lower() and 'final' in c.lower()) or c.strip() == 'Reported']
rep_col_name = rep_cols[0] if rep_cols else next((c for c in df.columns if 'report' in c.lower()), None)

late_cols = [c for c in df.columns if 'late' in c.lower() or 'delay' in c.lower()]
late_col_name = late_cols[0] if late_cols else None

desp_cols = [c for c in df.columns if 'desp' in c.lower() or 'date' in c.lower()]
desp_col = desp_cols[0] if desp_cols else None

staff_cols = [c for c in df.columns if 'staff' in c.lower() or 'controlling' in c.lower()]
staff_col = staff_cols[0] if staff_cols else None

client_cols = [c for c in df.columns if 'party' in c.lower() or 'client' in c.lower() or 'vendor' in c.lower()]
client_col = client_cols[0] if client_cols else None

remark_cols = [c for c in df.columns if 'tracking remark' in c.lower() or 'remark' in c.lower()]
remark_col = remark_cols[0] if remark_cols else None

# Calculate Metrics
trip_closed = 0
in_transit = 0
delay_closed = 0

for _, row in df.iterrows():
    rep_val = row.get(rep_col_name, "") if rep_col_name else ""
    late_val = row.get(late_col_name, 0) if late_col_name else 0
    is_closed = not is_blank(rep_val)
    
    if is_closed:
        trip_closed += 1
        if not is_zero_late(late_val):
            delay_closed += 1
    else:
        in_transit += 1

# Metric Cards Display
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="✅ Trip Closed (Reported)", value=trip_closed, delta="Final Touching Mentioned")
with col2:
    st.metric(label="🚚 In-Transit (Not Reported)", value=in_transit, delta="Pending Reported", delta_color="inverse")
with col3:
    st.metric(label="⚠️ Delay Closed", value=delay_closed, delta="Late Hrs > 0", delta_color="inverse")

st.markdown("---")

# ================= 7 ADVANCED FILTERS TOOLBAR =================
st.subheader("🔍 Advanced Filters Toolbar")

dates_set = sorted(list({str(str(v)[:10]).strip() for v in df.get(rep_col_name, []) if rep_col_name and not is_blank(v)}))
months_set = sorted(list({str(str(v)[3:10]).strip() for v in df.get(desp_col, []) if desp_col and not is_blank(v) and len(str(v)) >= 10}))
staff_set = sorted(list({str(v).strip() for v in df.get(staff_col, []) if staff_col and not is_blank(v)}))
client_set = sorted(list({str(v).strip() for v in df.get(client_col, []) if client_col and not is_blank(v)}))

fcol1, fcol2, fcol3, fcol4, fcol5, fcol6, fcol7 = st.columns(7)

with fcol1:
    sel_date = st.selectbox("Reported Date", ["ALL"] + dates_set)
with fcol2:
    sel_month = st.selectbox("Month", ["ALL"] + months_set)
with fcol3:
    sel_status = st.selectbox("Status", ["ALL", "On Time", "Delay"])
with fcol4:
    sel_staff = st.selectbox("Staff", ["ALL"] + staff_set)
with fcol5:
    sel_client = st.selectbox("Client", ["ALL"] + client_set)
with fcol6:
    sel_delay = st.selectbox("Delay Range", ["ALL", "< 1 Hour", "< 30 Mins", "< 10 Mins"])
with fcol7:
    sel_remarks = st.selectbox("Remarks", ["ALL", "With Remarks", "Without Remarks"])

# Trip Type Filter (Reported vs In-Transit)
trip_type_filter = st.radio(
    "📌 View Mode:", 
    ["All Records", "Trip Closed (Reported Mentioned)", "In-Transit (Reported Not Mentioned)"],
    horizontal=True
)

search_query = st.text_input("🔎 Search in records...", "")

# Apply Filters Logic
filtered_df = df.copy()

if trip_type_filter == "Trip Closed (Reported Mentioned)" and rep_col_name:
    filtered_df = filtered_df[filtered_df[rep_col_name].apply(lambda x: not is_blank(x))]
elif trip_type_filter == "In-Transit (Reported Not Mentioned)" and rep_col_name:
    filtered_df = filtered_df[filtered_df[rep_col_name].apply(lambda x: is_blank(x))]

if sel_date != "ALL" and rep_col_name:
    filtered_df = filtered_df[filtered_df[rep_col_name].astype(str).str.startswith(sel_date)]

if sel_month != "ALL" and desp_col:
    filtered_df = filtered_df[filtered_df[desp_col].astype(str).str.contains(sel_month)]

if sel_staff != "ALL" and staff_col:
    filtered_df = filtered_df[filtered_df[staff_col].astype(str).str.strip() == sel_staff]

if sel_client != "ALL" and client_col:
    filtered_df = filtered_df[filtered_df[client_col].astype(str).str.strip() == sel_client]

if sel_status != "ALL" and late_col_name:
    if sel_status == "Delay":
        filtered_df = filtered_df[filtered_df[late_col_name].apply(lambda x: not is_zero_late(x))]
    else:
        filtered_df = filtered_df[filtered_df[late_col_name].apply(lambda x: is_zero_late(x))]

if sel_delay != "ALL" and late_col_name:
    def check_delay_range(val):
        try:
            hrs = float(val)
            mins = hrs * 60
            if sel_delay == "< 1 Hour":
                return 0 < mins < 60
            elif sel_delay == "< 30 Mins":
                return 0 < mins < 30
            elif sel_delay == "< 10 Mins":
                return 0 < mins < 10
        except:
            return False
        return False
    filtered_df = filtered_df[filtered_df[late_col_name].apply(check_delay_range)]

if sel_remarks != "ALL" and remark_col:
    if sel_remarks == "With Remarks":
        filtered_df = filtered_df[filtered_df[remark_col].apply(lambda x: not is_blank(x))]
    elif sel_remarks == "Without Remarks":
        filtered_df = filtered_df[filtered_df[remark_col].apply(lambda x: is_blank(x))]

if search_query:
    q = search_query.lower()
    filtered_df = filtered_df[filtered_df.astype(str).apply(lambda row: row.str.lower().str.contains(q).any(), axis=1)]

# ================= RENAME COLUMNS FOR DISPLAY =================
display_df = filtered_df.copy()
rename_mapping = {}

for col in display_df.columns:
    c_lower = col.strip().lower()
    if '1st touching reporting' in c_lower or (('1st' in c_lower or 'first' in c_lower) and 'report' in c_lower):
        rename_mapping[col] = '1st In time'
    elif '2nd touching reporting' in c_lower or (('2nd' in c_lower or 'second' in c_lower) and 'report' in c_lower):
        rename_mapping[col] = '2nd In time'
    elif '2nd touching delivery' in c_lower or (('2nd' in c_lower or 'second' in c_lower) and 'deliver' in c_lower):
        rename_mapping[col] = 'Out time'
    elif '2nd touching hrs' in c_lower or (('2nd' in c_lower or 'second' in c_lower) and 'hr' in c_lower):
        rename_mapping[col] = 'Hours'
    elif 'final touching reporting' in c_lower or c_lower == 'reported':
        rename_mapping[col] = 'Reported time'

display_df = display_df.rename(columns=rename_mapping)

# ================= EXACT USER-SPECIFIED COLUMNS =================
desired_columns = [
    "Lorry No.", "Veh.Type", "From", "Destination", "KM", "Party", "Desp. Date & Time", 
    "Hrs. Taken", "Expected Dly. Date & Time", "Hrs. Given", "1st Touching", "1st In time", 
    "1st Touching Delivery Date & Time", "1st Touching Hrs.", "2nd Touching", "2nd In time", 
    "Out time", "Hours", "Reported time", "Total Touching Hrs.", "Hrs. Taken with touching", 
    "Hrs. Taken without touching (Dly.)", "Late Hrs", "Tracking Remark", "Group Name", 
    "Controlling Staff Name", "Foreman Name"
]

final_display_cols = []
seen_cols = set()
for d_col in desired_columns:
    match = next((c for c in display_df.columns if c.strip().lower() == d_col.lower()), None)
    if match and match not in seen_cols:
        final_display_cols.append(match)
        seen_cols.add(match)

# Display Main Table
st.subheader(f"📋 Fleet Records ({len(filtered_df)} entries found)")
if final_display_cols:
    st.dataframe(display_df[final_display_cols], use_container_width=True)
else:
    st.dataframe(display_df, use_container_width=True)

st.markdown("---")

# ================= CLIENT-WISE PERFORMANCE REPORT =================
st.subheader("📊 Client-wise Performance Report")
if client_col:
    client_filter = st.selectbox("Filter Client", ["ALL"] + client_set, key="client_perf_select")

    client_stats = []
    for client in client_set:
        if client_filter != "ALL" and client != client_filter:
            continue
        client_rows = df[df[client_col].astype(str).str.strip() == client]
        total = len(client_rows)
        closed = sum(1 for _, r in client_rows.iterrows() if rep_col_name and not is_blank(r.get(rep_col_name, "")))
        on_time = sum(1 for _, r in client_rows.iterrows() if rep_col_name and not is_blank(r.get(rep_col_name, "")) and late_col_name and is_zero_late(r.get(late_col_name, 0)))
        delay = closed - on_time
        pct = round((on_time / closed * 100), 1) if closed > 0 else 0.0
        
        client_stats.append({
            "Client Name": client,
            "Total Trips": total,
            "Closed Trips": closed,
            "On-Time Trips": on_time,
            "Delay Trips": delay,
            "On-Time %": f"{pct}%"
        })

    if client_stats:
        st.dataframe(pd.DataFrame(client_stats), use_container_width=True)

st.markdown("---")

# ================= ROUTE-WISE PERFORMANCE REPORT & DRILL-DOWN =================
st.subheader("🗺️ Route-wise Performance Report")
from_cols = [c for c in df.columns if c.strip().lower() == 'from']
dest_cols = [c for c in df.columns if 'destination' in c.lower()]

if from_cols and dest_cols:
    rcol1, rcol2 = st.columns(2)
    with rcol1:
        route_staff = st.selectbox("Filter by Controlling Staff", ["ALL"] + staff_set)
    with rcol2:
        route_client = st.selectbox("Filter by Client", ["ALL"] + client_set, key="route_client_select")

    route_stats = {}
    for _, row in df.iterrows():
        staff = str(row.get(staff_col, "")).strip() if staff_col else ""
        client = str(row.get(client_col, "")).strip() if client_col else ""
        
        if route_staff != "ALL" and staff != route_staff:
            continue
        if route_client != "ALL" and client != route_client:
            continue
            
        frm = row.get(from_cols[0], "Unknown")
        dest = row.get(dest_cols[0], "Unknown")
        route = f"{frm} → {dest}"
        
        if route not in route_stats:
            route_stats[route] = {"total": 0, "on_time": 0, "delay": 0}
            
        route_stats[route]["total"] += 1
        if late_col_name and is_zero_late(row.get(late_col_name, 0)):
            route_stats[route]["on_time"] += 1
        else:
            route_stats[route]["delay"] += 1

    route_data = []
    for route, stats in route_stats.items():
        rate = round((stats["on_time"] / stats["total"] * 100), 1) if stats["total"] > 0 else 0.0
        route_data.append({
            "Route": route,
            "Total Trips": stats["total"],
            "On-Time Trips": stats["on_time"],
            "Delay Trips": stats["delay"],
            "Success Rate": f"{rate}%"
        })

    if route_data:
        route_df_summary = pd.DataFrame(route_data)
        st.dataframe(route_df_summary, use_container_width=True)
        
        # Route Drill-down Selector (Click/Select Route to view exact trips)
        st.markdown("#### 🔍 Route Drill-down Details")
        all_routes_list = sorted(list(route_stats.keys()))
        selected_drill_route = st.selectbox("Select Route to View Trips Data", ["SELECT ROUTE"] + all_routes_list)
        
        if selected_drill_route != "SELECT ROUTE":
            frm_name, dest_name = selected_drill_route.split(" → ")
            drill_df = df[(df[from_cols[0]].astype(str).str.strip() == frm_name) & (df[dest_cols[0]].astype(str).str.strip() == dest_name)]
            
            # Apply display column renaming & filtering
            drill_display_df = drill_df.copy()
            drill_rename_mapping = {}
            for col in drill_display_df.columns:
                c_lower = col.strip().lower()
                if '1st touching reporting' in c_lower or (('1st' in c_lower or 'first' in c_lower) and 'report' in c_lower):
                    drill_rename_mapping[col] = '1st In time'
                elif '2nd touching reporting' in c_lower or (('2nd' in c_lower or 'second' in c_lower) and 'report' in c_lower):
                    drill_rename_mapping[col] = '2nd In time'
                elif '2nd touching delivery' in c_lower or (('2nd' in c_lower or 'second' in c_lower) and 'deliver' in c_lower):
                    drill_rename_mapping[col] = 'Out time'
                elif '2nd touching hrs' in c_lower or (('2nd' in c_lower or 'second' in c_lower) and 'hr' in c_lower):
                    drill_rename_mapping[col] = 'Hours'
                elif 'final touching reporting' in c_lower or c_lower == 'reported':
                    drill_rename_mapping[col] = 'Reported time'
            
            drill_display_df = drill_display_df.rename(columns=drill_rename_mapping)
            
            drill_final_cols = []
            seen_drill_cols = set()
            for d_col in desired_columns:
                match = next((c for c in drill_display_df.columns if c.strip().lower() == d_col.lower()), None)
                if match and match not in seen_drill_cols:
                    drill_final_cols.append(match)
                    seen_drill_cols.add(match)
            
            st.info(f"Showing trips for route: **{selected_drill_route}** ({len(drill_df)} entries found)")
            if drill_final_cols:
                st.dataframe(drill_display_df[drill_final_cols], use_container_width=True)
            else:
                st.dataframe(drill_display_df, use_container_width=True)
    else:
        st.info("No route data available for the selected filters.")import streamlit as st
import pandas as pd
import numpy as np
import os

# Page Configuration
st.set_page_config(
    page_title="Nitesh - Fleet Analytics & MIS Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Glassmorphism & Neon Styling
st.markdown("""
<style>
    .main {
        background: radial-gradient(circle at 50% 0%, #1e1145 0%, #0d0621 50%, #05020d 100%);
        color: #e2e8f0;
    }
    .stMetric {
        background: rgba(25, 15, 55, 0.65);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(168, 85, 247, 0.2);
        padding: 15px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Persistent Storage Folder Setup
UPLOAD_DIR = "saved_fleet_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Helper: Smart Client/Party Name Normalization & Sanitization
def normalize_party(name):
    if pd.isna(name) or name == "":
        return "Other"
    s = str(name).strip()
    s_upper = s.upper()
    
    # Known key mappings
    if "BUSYBEE" in s_upper:
        return "Busybees"
    if "DHL" in s_upper:
        return "DHL"
    if "TRACKON" in s_upper:
        return "Trackon"
    if "AMAZON" in s_upper:
        return "Amazon"
    
    # For other clients, clean up excessively long corporate suffixes automatically for neat UI display
    for suffix in [" PRIVATE LIMITED", " PVT LTD", " LTD", " (INDIA)", " SOLUTIONS"]:
        if s_upper.endswith(suffix):
            s = s[:-len(suffix)].strip()
            
    return s

# Helper: Blank Check
def is_blank(val):
    if pd.isna(val) or val is None:
        return True
    s = str(val).strip().lower()
    return s in ["", "nan", "nat", "none", "-", "0", "0.0"]

# Helper: Zero Late Check
def is_zero_late(val):
    if is_blank(val):
        return True
    s = str(val).strip().lower()
    if s in ["0", "0.0", "00:00", "0:00", "00:00:00"]:
        return True
    try:
        num = float(s)
        return num <= 0
    except ValueError:
        return False

# Sample Default Dataset
@st.cache_data
def get_sample_data():
    return pd.DataFrame([
        {
            "Lorry No.": "MH04AB1234", "Veh.Type": "15MT", "From": "Delhi", "Destination": "Vapi", "KM": "1200", "Party": "DHL",
            "Desp. Date & Time": "08/11/2026 13:04:00", "Hrs. Taken": "48h", "Expected Dly. Date & Time": "10/11/2026 12:00", "Hrs. Given": "50h",
            "1st Touching": "Surat", "1st Touching Reporting Date & Time": "09/11/2026 11:00", "1st Touching Delivery Date & Time": "09/11/2026 14:00", "1st Touching Hrs.": "3h",
            "2nd Touching": "Mumbai", "2nd Touching Reporting Date & Time": "10/11/2026 08:00", "2nd Touching Delivery Date & Time": "10/11/2026 10:00", "2nd Touching Hrs.": "2h",
            "Final Touching Reporting Date & Time": "10/11/2026 14:00",
            "Total Touching Hrs.": "5h", "Hrs. Taken with touching": "52h", "Hrs. Taken without touching (Dly.)": "47h", "Late Hrs": "0", 
            "Tracking Remark": "Delivered on time", "Group Name": "G1", "Controlling Staff Name": "Amit Kumar", "Foreman Name": "Rajesh"
        }
    ])

# Header Section
st.title("🚀 Fleet Analytics & MIS Dashboard")
st.markdown("Welcome back, **Nitesh** | Logistics Management System")

def process_data(df):
    processed = []
    for _, row in df.iterrows():
        new_row = {}
        for col in df.columns:
            clean_col = str(col).strip()
            val = row[col]
            
            if any(k in clean_col.lower() for k in ["party", "client", "vendor"]):
                val = normalize_party(val)
            
            new_row[clean_col] = val
        processed.append(new_row)
    return pd.DataFrame(processed)

# Load data from disk folder if available, else sample data
def load_persisted_data():
    files = os.listdir(UPLOAD_DIR)
    if files:
        df_list = []
        for f in files:
            f_path = os.path.join(UPLOAD_DIR, f)
            try:
                if f.endswith('.csv'):
                    df_temp = pd.read_csv(f_path)
                else:
                    df_temp = pd.read_excel(f_path)
                df_list.append(df_temp)
            except Exception:
                pass
        if df_list:
            return pd.concat(df_list, ignore_index=True), ", ".join(files)
    return get_sample_data(), "Default Fleet Sample"

if "saved_data" not in st.session_state:
    initial_df, src_name = load_persisted_data()
    st.session_state.saved_data = initial_df
    st.session_state.source_name = src_name

# Sidebar - Multiple File Upload & Remove Button
st.sidebar.header("📁 Data Source")
uploaded_files = st.sidebar.file_uploader(
    "Upload Multiple Excel/CSV Files", 
    type=["csv", "xlsx", "xls"], 
    accept_multiple_files=True,
    key="file_uploader_key"
)

# Remove Data Button
if st.sidebar.button("🗑️ Remove Uploaded Data"):
    for f in os.listdir(UPLOAD_DIR):
        os.remove(os.path.join(UPLOAD_DIR, f))
    st.session_state.saved_data = get_sample_data()
    st.session_state.source_name = "Default Fleet Sample"
    st.sidebar.success("Uploaded data removed successfully!")
    st.rerun()

if uploaded_files:
    for f in os.listdir(UPLOAD_DIR):
        os.remove(os.path.join(UPLOAD_DIR, f))
    
    df_list = []
    file_names = []
    for file in uploaded_files:
        file_names.append(file.name)
        f_path = os.path.join(UPLOAD_DIR, file.name)
        with open(f_path, "wb") as f:
            f.write(file.getbuffer())
        
        try:
            if file.name.endswith('.csv'):
                df_temp = pd.read_csv(f_path)
            else:
                df_temp = pd.read_excel(f_path)
            df_list.append(df_temp)
        except Exception as e:
            st.sidebar.error(f"Error loading {file.name}: {e}")
            
    if df_list:
        raw_df = pd.concat(df_list, ignore_index=True)
        st.session_state.saved_data = process_data(raw_df)
        st.session_state.source_name = ", ".join(file_names)

df = st.session_state.saved_data
st.sidebar.info(f"Loaded: {st.session_state.source_name}")

# Column Mappings & Detection
rep_cols = [c for c in df.columns if 'final touching reporting' in c.lower() or ('report' in c.lower() and 'final' in c.lower()) or c.strip() == 'Reported']
rep_col_name = rep_cols[0] if rep_cols else next((c for c in df.columns if 'report' in c.lower()), None)

late_cols = [c for c in df.columns if 'late' in c.lower() or 'delay' in c.lower()]
late_col_name = late_cols[0] if late_cols else None

desp_cols = [c for c in df.columns if 'desp' in c.lower() or 'date' in c.lower()]
desp_col = desp_cols[0] if desp_cols else None

staff_cols = [c for c in df.columns if 'staff' in c.lower() or 'controlling' in c.lower()]
staff_col = staff_cols[0] if staff_cols else None

client_cols = [c for c in df.columns if 'party' in c.lower() or 'client' in c.lower() or 'vendor' in c.lower()]
client_col = client_cols[0] if client_cols else None

remark_cols = [c for c in df.columns if 'tracking remark' in c.lower() or 'remark' in c.lower()]
remark_col = remark_cols[0] if remark_cols else None

# Calculate Metrics
trip_closed = 0
in_transit = 0
delay_closed = 0

for _, row in df.iterrows():
    rep_val = row.get(rep_col_name, "") if rep_col_name else ""
    late_val = row.get(late_col_name, 0) if late_col_name else 0
    is_closed = not is_blank(rep_val)
    
    if is_closed:
        trip_closed += 1
        if not is_zero_late(late_val):
            delay_closed += 1
    else:
        in_transit += 1

# Metric Cards Display
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="✅ Trip Closed (Reported)", value=trip_closed, delta="Final Touching Mentioned")
with col2:
    st.metric(label="🚚 In-Transit (Not Reported)", value=in_transit, delta="Pending Reported", delta_color="inverse")
with col3:
    st.metric(label="⚠️ Delay Closed", value=delay_closed, delta="Late Hrs > 0", delta_color="inverse")

st.markdown("---")

# ================= 7 ADVANCED FILTERS TOOLBAR =================
st.subheader("🔍 Advanced Filters Toolbar")

dates_set = sorted(list({str(str(v)[:10]).strip() for v in df.get(rep_col_name, []) if rep_col_name and not is_blank(v)}))
months_set = sorted(list({str(str(v)[3:10]).strip() for v in df.get(desp_col, []) if desp_col and not is_blank(v) and len(str(v)) >= 10}))
staff_set = sorted(list({str(v).strip() for v in df.get(staff_col, []) if staff_col and not is_blank(v)}))
client_set = sorted(list({str(v).strip() for v in df.get(client_col, []) if client_col and not is_blank(v)}))

fcol1, fcol2, fcol3, fcol4, fcol5, fcol6, fcol7 = st.columns(7)

with fcol1:
    sel_date = st.selectbox("Reported Date", ["ALL"] + dates_set)
with fcol2:
    sel_month = st.selectbox("Month", ["ALL"] + months_set)
with fcol3:
    sel_status = st.selectbox("Status", ["ALL", "On Time", "Delay"])
with fcol4:
    sel_staff = st.selectbox("Staff", ["ALL"] + staff_set)
with fcol5:
    sel_client = st.selectbox("Client", ["ALL"] + client_set)
with fcol6:
    sel_delay = st.selectbox("Delay Range", ["ALL", "< 1 Hour", "< 30 Mins", "< 10 Mins"])
with fcol7:
    sel_remarks = st.selectbox("Remarks", ["ALL", "With Remarks", "Without Remarks"])

# Trip Type Filter (Reported vs In-Transit)
trip_type_filter = st.radio(
    "📌 View Mode:", 
    ["All Records", "Trip Closed (Reported Mentioned)", "In-Transit (Reported Not Mentioned)"],
    horizontal=True
)

search_query = st.text_input("🔎 Search in records...", "")

# Apply Filters Logic
filtered_df = df.copy()

if trip_type_filter == "Trip Closed (Reported Mentioned)" and rep_col_name:
    filtered_df = filtered_df[filtered_df[rep_col_name].apply(lambda x: not is_blank(x))]
elif trip_type_filter == "In-Transit (Reported Not Mentioned)" and rep_col_name:
    filtered_df = filtered_df[filtered_df[rep_col_name].apply(lambda x: is_blank(x))]

if sel_date != "ALL" and rep_col_name:
    filtered_df = filtered_df[filtered_df[rep_col_name].astype(str).str.startswith(sel_date)]

if sel_month != "ALL" and desp_col:
    filtered_df = filtered_df[filtered_df[desp_col].astype(str).str.contains(sel_month)]

if sel_staff != "ALL" and staff_col:
    filtered_df = filtered_df[filtered_df[staff_col].astype(str).str.strip() == sel_staff]

if sel_client != "ALL" and client_col:
    filtered_df = filtered_df[filtered_df[client_col].astype(str).str.strip() == sel_client]

if sel_status != "ALL" and late_col_name:
    if sel_status == "Delay":
        filtered_df = filtered_df[filtered_df[late_col_name].apply(lambda x: not is_zero_late(x))]
    else:
        filtered_df = filtered_df[filtered_df[late_col_name].apply(lambda x: is_zero_late(x))]

if sel_delay != "ALL" and late_col_name:
    def check_delay_range(val):
        try:
            hrs = float(val)
            mins = hrs * 60
            if sel_delay == "< 1 Hour":
                return 0 < mins < 60
            elif sel_delay == "< 30 Mins":
                return 0 < mins < 30
            elif sel_delay == "< 10 Mins":
                return 0 < mins < 10
        except:
            return False
        return False
    filtered_df = filtered_df[filtered_df[late_col_name].apply(check_delay_range)]

if sel_remarks != "ALL" and remark_col:
    if sel_remarks == "With Remarks":
        filtered_df = filtered_df[filtered_df[remark_col].apply(lambda x: not is_blank(x))]
    elif sel_remarks == "Without Remarks":
        filtered_df = filtered_df[filtered_df[remark_col].apply(lambda x: is_blank(x))]

if search_query:
    q = search_query.lower()
    filtered_df = filtered_df[filtered_df.astype(str).apply(lambda row: row.str.lower().str.contains(q).any(), axis=1)]

# ================= RENAME COLUMNS FOR DISPLAY (Ensuring Unique Names) =================
display_df = filtered_df.copy()
rename_mapping = {}

for col in display_df.columns:
    c_lower = col.strip().lower()
    if '1st touching reporting' in c_lower or (('1st' in c_lower or 'first' in c_lower) and 'report' in c_lower):
        rename_mapping[col] = '1st In time'
    elif '2nd touching reporting' in c_lower or (('2nd' in c_lower or 'second' in c_lower) and 'report' in c_lower):
        rename_mapping[col] = '2nd In time'
    elif '2nd touching delivery' in c_lower or (('2nd' in c_lower or 'second' in c_lower) and 'deliver' in c_lower):
        rename_mapping[col] = 'Out time'
    elif '2nd touching hrs' in c_lower or (('2nd' in c_lower or 'second' in c_lower) and 'hr' in c_lower):
        rename_mapping[col] = 'Hours'
    elif 'final touching reporting' in c_lower or c_lower == 'reported':
        rename_mapping[col] = 'Reported time'

display_df = display_df.rename(columns=rename_mapping)

# ================= EXACT USER-SPECIFIED COLUMNS (Unique Names) =================
desired_columns = [
    "Lorry No.", 
    "Veh.Type", 
    "From", 
    "Destination", 
    "KM", 
    "Party", 
    "Desp. Date & Time", 
    "Hrs. Taken", 
    "Expected Dly. Date & Time", 
    "Hrs. Given", 
    "1st Touching", 
    "1st In time", 
    "1st Touching Delivery Date & Time", 
    "1st Touching Hrs.", 
    "2nd Touching", 
    "2nd In time", 
    "Out time", 
    "Hours", 
    "Reported time", 
    "Total Touching Hrs.", 
    "Hrs. Taken with touching", 
    "Hrs. Taken without touching (Dly.)", 
    "Late Hrs", 
    "Tracking Remark", 
    "Group Name", 
    "Controlling Staff Name", 
    "Foreman Name"
]

final_display_cols = []
seen_cols = set()
for d_col in desired_columns:
    match = next((c for c in display_df.columns if c.strip().lower() == d_col.lower()), None)
    if match and match not in seen_cols:
        final_display_cols.append(match)
        seen_cols.add(match)

# Display Main Table
st.subheader(f"📋 Fleet Records ({len(filtered_df)} entries found)")
if final_display_cols:
    st.dataframe(display_df[final_display_cols], use_container_width=True)
else:
    st.dataframe(display_df, use_container_width=True)

st.markdown("---")

# ================= CLIENT-WISE PERFORMANCE REPORT =================
st.subheader("📊 Client-wise Performance Report")
if client_col:
    client_filter = st.selectbox("Filter Client", ["ALL"] + client_set, key="client_perf_select")

    client_stats = []
    for client in client_set:
        if client_filter != "ALL" and client != client_filter:
            continue
        client_rows = df[df[client_col].astype(str).str.strip() == client]
        total = len(client_rows)
        closed = sum(1 for _, r in client_rows.iterrows() if rep_col_name and not is_blank(r.get(rep_col_name, "")))
        on_time = sum(1 for _, r in client_rows.iterrows() if rep_col_name and not is_blank(r.get(rep_col_name, "")) and late_col_name and is_zero_late(r.get(late_col_name, 0)))
        delay = closed - on_time
        pct = round((on_time / closed * 100), 1) if closed > 0 else 0.0
        
        client_stats.append({
            "Client Name": client,
            "Total Trips": total,
            "Closed Trips": closed,
            "On-Time Trips": on_time,
            "Delay Trips": delay,
            "On-Time %": f"{pct}%"
        })

    if client_stats:
        st.dataframe(pd.DataFrame(client_stats), use_container_width=True)

st.markdown("---")

# ================= ROUTE-WISE PERFORMANCE REPORT =================
st.subheader("🗺️ Route-wise Performance Report")
from_cols = [c for c in df.columns if c.strip().lower() == 'from']
dest_cols = [c for c in df.columns if 'destination' in c.lower()]

if from_cols and dest_cols:
    rcol1, rcol2 = st.columns(2)
    with rcol1:
        route_staff = st.selectbox("Filter by Controlling Staff", ["ALL"] + staff_set)
    with rcol2:
        route_client = st.selectbox("Filter by Client", ["ALL"] + client_set, key="route_client_select")

    route_stats = {}
    for _, row in df.iterrows():
        staff = str(row.get(staff_col, "")).strip() if staff_col else ""
        client = str(row.get(client_col, "")).strip() if client_col else ""
        
        if route_staff != "ALL" and staff != route_staff:
            continue
        if route_client != "ALL" and client != route_client:
            continue
            
        frm = row.get(from_cols[0], "Unknown")
        dest = row.get(dest_cols[0], "Unknown")
        route = f"{frm} → {dest}"
        
        if route not in route_stats:
            route_stats[route] = {"total": 0, "on_time": 0, "delay": 0}
            
        route_stats[route]["total"] += 1
        if late_col_name and is_zero_late(row.get(late_col_name, 0)):
            route_stats[route]["on_time"] += 1
        else:
            route_stats[route]["delay"] += 1

    route_data = []
    for route, stats in route_stats.items():
        rate = round((stats["on_time"] / stats["total"] * 100), 1) if stats["total"] > 0 else 0.0
        route_data.append({
            "Route": route,
            "Total Trips": stats["total"],
            "On-Time Trips": stats["on_time"],
            "Delay Trips": stats["delay"],
            "Success Rate": f"{rate}%"
        })

    if route_data:
        st.dataframe(pd.DataFrame(route_data), use_container_width=True)
    else:
        st.info("No route data available for the selected filters.")
