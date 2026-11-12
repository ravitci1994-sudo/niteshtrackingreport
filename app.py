import streamlit as st
import pandas as pd
import numpy as np

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

# Helper: Normalize Party Names
def normalize_party(name):
    if pd.isna(name) or name == "":
        return "Other"
    s = str(name).strip().upper()
    if "BUSYBEE" in s:
        return "Busybees"
    if "DHL" in s:
        return "DHL"
    if "TRACKON" in s:
        return "Trackon"
    return str(name).strip()

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
            "Lorry No.": "MH04AB1234", "Veh.Type": "15MT", "From": "Delhi", "Destination": "Vapi", "Party": "DHL",
            "Desp. Date & Time": "08/11/2026 13:04:00", "1st Touching": "Surat", "1st In Time": "09/11/2026 12:00",
            "1st Out Time": "09/11/2026 15:00", "1st Hours": "25h", "2nd Touching": "-",
            "2nd In Time": "-", "2nd Out Time": "-", "2nd Hours": "-",
            "Reported": "10/11/2026 14:00", "Total Touching Hrs.": "28h",
            "Hrs. Taken with touching": "52h", "Hrs. Taken without touching (Dly.)": "48h", "Late Hrs": "0",
            "Tracking Remark": "Delivered on time", "Controlling Staff Name": "Amit Kumar", "Foreman Name": "Rajesh"
        },
        {
            "Lorry No.": "GJ01XY5678", "Veh.Type": "16MT", "From": "Delhi", "Destination": "Vapi", "Party": "BUSYBEES LOGISTICS SOLUTIONS PRIVATE LIMITED",
            "Desp. Date & Time": "08/11/2026 04:56:00", "1st Touching": "Vadodara", "1st In Time": "09/11/2026 10:00",
            "1st Out Time": "09/11/2026 14:00", "1st Hours": "26h", "2nd Touching": "-",
            "2nd In Time": "-", "2nd Out Time": "-", "2nd Hours": "-",
            "Reported": "", "Total Touching Hrs.": "-",
            "Hrs. Taken with touching": "-", "Hrs. Taken without touching (Dly.)": "-", "Late Hrs": "2.5",
            "Tracking Remark": "", "Controlling Staff Name": "Nitesh", "Foreman Name": "Suresh"
        }
    ])

# Header Section
st.title("🚀 Fleet Analytics & MIS Dashboard")
st.markdown("Welcome back, **Nitesh** | Logistics Management System")

# Sidebar - Multiple File Upload
st.sidebar.header("📁 Data Source")
uploaded_files = st.sidebar.file_uploader(
    "Upload Multiple Excel/CSV Files", 
    type=["csv", "xlsx", "xls"], 
    accept_multiple_files=True
)

# Load Data
df_list = []
if uploaded_files:
    for file in uploaded_files:
        try:
            if file.name.endswith('.csv'):
                df_temp = pd.read_csv(file)
            else:
                df_temp = pd.read_excel(file)
            df_list.append(df_temp)
        except Exception as e:
            st.sidebar.error(f"Error loading {file.name}: {e}")
    if df_list:
        raw_df = pd.concat(df_list, ignore_index=True)
    else:
        raw_df = get_sample_data()
else:
    raw_df = get_sample_data()

# Process & Normalize Columns (Avoiding duplicates)
def process_data(df):
    processed = []
    for _, row in df.iterrows():
        new_row = {}
        for col in df.columns:
            clean_col = str(col).strip()
            val = row[col]
            
            # Normalize Party
            if any(k in clean_col.lower() for k in ["party", "client", "vendor"]):
                val = normalize_party(val)
            
            # Unique Column Renaming
            if "1st" in clean_col and "report" in clean_col.lower():
                new_row["1st In Time"] = val
            elif "1st" in clean_col and "deliver" in clean_col.lower():
                new_row["1st Out Time"] = val
            elif "1st" in clean_col and "hrs" in clean_col.lower():
                new_row["1st Hours"] = val
            elif "2nd" in clean_col and "report" in clean_col.lower():
                new_row["2nd In Time"] = val
            elif "2nd" in clean_col and "deliver" in clean_col.lower():
                new_row["2nd Out Time"] = val
            elif "2nd" in clean_col and "hrs" in clean_col.lower():
                new_row["2nd Hours"] = val
            elif any(k in clean_col.lower() for k in ["final touching reporting", "reporting date"]):
                new_row["Reported"] = val
            else:
                new_row[clean_col] = val
        processed.append(new_row)
    return pd.DataFrame(processed)

df = process_data(raw_df)

# Required Unique Display Columns
required_cols = [
    "Lorry No.", "Veh.Type", "From", "Destination", "Party", 
    "Desp. Date & Time", "1st Touching", "1st In Time", 
    "1st Out Time", "1st Hours", "2nd Touching", 
    "2nd In Time", "2nd Out Time", "2nd Hours", "Reported", "Total Touching Hrs.", 
    "Hrs. Taken with touching", "Hrs. Taken without touching (Dly.)", "Late Hrs", 
    "Tracking Remark", "Controlling Staff Name", "Foreman Name"
]

existing_cols = [c for c in required_cols if c in df.columns]

# Calculate Metrics
trip_closed = 0
in_transit = 0
delay_closed = 0

for _, row in df.iterrows():
    rep_val = row.get("Reported", "")
    late_val = row.get("Late Hrs", 0)
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
    st.metric(label="✅ Trip Closed", value=trip_closed, delta="Final Touching Reported")
with col2:
    st.metric(label="🚚 In-Transit", value=in_transit, delta="Pending Reported", delta_color="inverse")
with col3:
    st.metric(label="⚠️ Delay Closed", value=delay_closed, delta="Late Hrs > 0", delta_color="inverse")

st.markdown("---")

# ================= 7 ADVANCED FILTERS TOOLBAR =================
st.subheader("🔍 Advanced 7-Button Filters Toolbar")

dates_set = sorted(list({str(str(v)[:10]) for v in df.get("Desp. Date & Time", []) if not is_blank(v)}))
months_set = sorted(list({str(str(v)[3:10]) for v in df.get("Desp. Date & Time", []) if not is_blank(v) and len(str(v)) >= 10}))
staff_set = sorted(list({str(v).strip() for v in df.get("Controlling Staff Name", []) if not is_blank(v)}))
client_set = sorted(list({str(v).strip() for v in df.get("Party", []) if not is_blank(v)}))

fcol1, fcol2, fcol3, fcol4, fcol5, fcol6, fcol7 = st.columns(7)

with fcol1:
    sel_date = st.selectbox("Date", ["ALL"] + dates_set)
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
    sel_remarks = st.selectbox("Remarks", ["ALL", "With Remarks", "Without Remarks", "Delay + Without Remarks"])

search_query = st.text_input("🔎 Search Lorry No, Destination, Party...", "")

# Apply Filters Logic
filtered_df = df.copy()

if sel_date != "ALL":
    filtered_df = filtered_df[filtered_df["Desp. Date & Time"].astype(str).str.startswith(sel_date)]
if sel_month != "ALL":
    filtered_df = filtered_df[filtered_df["Desp. Date & Time"].astype(str).str.contains(sel_month)]
if sel_staff != "ALL":
    filtered_df = filtered_df[filtered_df["Controlling Staff Name"].astype(str).str.strip() == sel_staff]
if sel_client != "ALL":
    filtered_df = filtered_df[filtered_df["Party"].astype(str).str.strip() == sel_client]

if sel_status != "ALL":
    if sel_status == "Delay":
        filtered_df = filtered_df[filtered_df["Late Hrs"].apply(lambda x: not is_zero_late(x))]
    else:
        filtered_df = filtered_df[filtered_df["Late Hrs"].apply(lambda x: is_zero_late(x))]

if sel_delay != "ALL":
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
    filtered_df = filtered_df[filtered_df["Late Hrs"].apply(check_delay_range)]

if sel_remarks != "ALL":
    def check_remarks(row):
        rem = str(row.get("Tracking Remark", ""))
        has_rem = not is_blank(rem)
        is_late = not is_zero_late(row.get("Late Hrs", 0))
        if sel_remarks == "With Remarks":
            return has_rem
        elif sel_remarks == "Without Remarks":
            return not has_rem
        elif sel_remarks == "Delay + Without Remarks":
            return is_late and not has_rem
        return True
    filtered_df = filtered_df[filtered_df.apply(check_remarks, axis=1)]

if search_query:
    q = search_query.lower()
    filtered_df = filtered_df[filtered_df.astype(str).apply(lambda row: row.str.lower().str.contains(q).any(), axis=1)]

# Display Main Table
st.subheader(f"📋 Fleet Records ({len(filtered_df)} entries found)")
st.dataframe(filtered_df[existing_cols] if existing_cols else filtered_df, use_container_width=True)

st.markdown("---")

# ================= CLIENT-WISE PERFORMANCE REPORT =================
st.subheader("📊 Client-wise Performance Report")
client_filter = st.selectbox("Filter Client", ["ALL"] + client_set, key="client_perf_select")

client_stats = []
for client in client_set:
    if client_filter != "ALL" and client != client_filter:
        continue
    client_rows = df[df["Party"].astype(str).str.strip() == client]
    total = len(client_rows)
    closed = sum(1 for _, r in client_rows.iterrows() if not is_blank(r.get("Reported", "")))
    on_time = sum(1 for _, r in client_rows.iterrows() if not is_blank(r.get("Reported", "")) and is_zero_late(r.get("Late Hrs", 0)))
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
rcol1, rcol2 = st.columns(2)
with rcol1:
    route_staff = st.selectbox("Filter by Controlling Staff", ["ALL"] + staff_set)
with rcol2:
    route_client = st.selectbox("Filter by Client", ["ALL"] + client_set, key="route_client_select")

route_stats = {}
for _, row in df.iterrows():
    staff = str(row.get("Controlling Staff Name", "")).strip()
    client = str(row.get("Party", "")).strip()
    
    if route_staff != "ALL" and staff != route_staff:
        continue
    if route_client != "ALL" and client != route_client:
        continue
        
    frm = row.get("From", "Unknown")
    dest = row.get("Destination", "Unknown")
    route = f"{frm} → {dest}"
    
    if route not in route_stats:
        route_stats[route] = {"total": 0, "on_time": 0, "delay": 0}
        
    route_stats[route]["total"] += 1
    if is_zero_late(row.get("Late Hrs", 0)):
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
