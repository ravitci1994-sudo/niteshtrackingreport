import streamlit as st
import pandas as pd
from datetime import date, datetime
import io
import os
import urllib.parse

# 1. Page Configuration
st.set_page_config(page_title="Client Performance Dashboard", layout="wide", initial_sidebar_state="expanded")

DATA_FILE = "saved_client_data.pkl"

# Helper function to process data columns safely
def process_dataframe(df):
    df.columns = df.columns.str.strip()
    
    from_col = next((c for c in df.columns if 'from' in c.lower() or 'origin' in c.lower()), None)
    dest_col = next((c for c in df.columns if 'dest' in c.lower() or 'to' in c.lower()), None)
    
    if from_col and dest_col:
        df['Route Path'] = df[from_col].astype(str).str.strip().str.upper() + " TO " + df[dest_col].astype(str).str.strip().str.upper()
    else:
        df['Route Path'] = "UNKNOWN ROUTE"

    def get_arrival_status(row):
        final_rep = row.get('Final Touching Reporting Date & Time') or row.get('Reporting Date')
        exp_dly = row.get('Expected Dly. Date & Time') or row.get('Expected Date')
        
        if pd.notna(final_rep):
            if pd.notna(row.get('Late Hrs')):
                return "Late Arrival"
            else:
                return "Ontime Arrival"
        else:
            try:
                if pd.notna(exp_dly):
                    exp_dt = pd.to_datetime(exp_dly)
                    current_time = datetime.now()
                    if current_time > exp_dt:
                        return "Running Delay"
            except:
                pass
            return "In-Transit"
            
    df['Status_Category'] = df.apply(get_arrival_status, axis=1)
    return df

# ================= MEMORY SETUP =================
if 'client_data' not in st.session_state:
    if os.path.exists(DATA_FILE):
        try:
            df_loaded = pd.read_pickle(DATA_FILE)
            st.session_state.client_data = process_dataframe(df_loaded)
        except:
            st.session_state.client_data = None
    else:
        st.session_state.client_data = None

# ================= SIDEBAR =================
st.sidebar.markdown("### Welcome, Tejas Cargo India Pvt Ltd")
st.sidebar.markdown("<small style='color:gray'><b>ID:</b> <span style='color:green'>TEJAS</span> | <b>Role:</b> <span style='color:green'>Vendor</span></small>", unsafe_allow_html=True)

st.sidebar.markdown("---")

if st.sidebar.button("🚀 PROCESS & REFRESH DATA", type="primary", use_container_width=True):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    st.session_state.client_data = None
    st.rerun()

st.sidebar.markdown("Navigation:")
selected_nav = st.sidebar.radio("", [
    "📊 Operations Summary",
    "🚚 Vendor Performance",
    "💳 Payment Dashboard",
    "📱 Communication Hub",
    "💰 Network Utilization",
    "📝 Today's Call Action Plan",
    "🔐 User & Access Control"
], label_visibility="collapsed")

st.sidebar.markdown("---")
if st.sidebar.button("Logout", use_container_width=True):
    st.sidebar.warning("Logged out successfully!")


# ================= MAIN PAGE LOGIC =================
if selected_nav in ["📊 Operations Summary", "🚚 Vendor Performance"]:
    st.title(selected_nav.replace("📊 ", "").replace("🚚 ", ""))
    st.info("🔒 **Restricted View:** Showing exclusive performance records.")

    # Auto-processing file uploader (No button needed)
    uploaded_files = st.file_uploader(
        "📂 Apni 'MIS for Placement' Excel/CSV files yahan upload karein", 
        type=["xlsx", "csv"], 
        accept_multiple_files=True
    )

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
            
            st.session_state.client_data = df
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            df.to_pickle(DATA_FILE) 
        except Exception as e:
            st.error(f"Error processing files: {e}")

    # ================= DASHBOARD =================
    if st.session_state.client_data is not None:
        df = st.session_state.client_data
        st.markdown("---")
        
        f1, f2, f3, f4, f5, f6 = st.columns(6)
        
        zone_col = next((c for c in df.columns if 'zone' in c.lower()), None)
        with f1:
            zone_list = ["ALL"] + list(df[zone_col].dropna().unique()) if zone_col else ["ALL"]
            zone_filter = st.selectbox("Filter by Zone:", zone_list)
            
        zone_filtered_df = df.copy()
        if zone_filter != "ALL" and zone_col:
            zone_filtered_df = zone_filtered_df[zone_filtered_df[zone_col] == zone_filter]

        client_col = next((c for c in df.columns if 'party' in c.lower() or 'client' in c.lower()), None)
        with f2:
            client_list = ["ALL"] + list(zone_filtered_df[client_col].dropna().unique()) if client_col else ["ALL"]
            client_filter = st.selectbox("Filter by Client:", client_list)
            
        client_filtered_df = zone_filtered_df.copy()
        if client_filter != "ALL" and client_col:
            client_filtered_df = client_filtered_df[client_filtered_df[client_col] == client_filter]

        staff_col = next((c for c in df.columns if 'staff' in c.lower() or 'controlling' in c.lower()), None)
        with f3:
            staff_list = ["ALL"] + list(client_filtered_df[staff_col].dropna().unique()) if staff_col else ["ALL"]
            staff_filter = st.selectbox("Filter by Staff:", staff_list)

        staff_filtered_df = client_filtered_df.copy()
        if staff_filter != "ALL" and staff_col:
            staff_filtered_df = staff_filtered_df[staff_filtered_df[staff_col] == staff_filter]

        with f4:
            ro_list = ["ALL"] + sorted(list(staff_filtered_df['Route Path'].dropna().unique()))
            ro_filter = st.selectbox("Filter by Route:", ro_list)
            
        route_filtered_df = staff_filtered_df.copy()
        if ro_filter != "ALL":
            route_filtered_df = route_filtered_df[route_filtered_df['Route Path'] == ro_filter]

        lorry_col = next((c for c in route_filtered_df.columns if 'lorry' in c.lower() or 'vehicle' in c.lower() or 'truck' in c.lower()), None)
        with f5:
            if lorry_col:
                lorry_list = ["ALL"] + sorted(list(route_filtered_df[lorry_col].dropna().astype(str).unique()))
            else:
                lorry_list = ["ALL"]
            lorry_filter = st.selectbox("Filter by Vehicle No:", lorry_list)

        with f6:
            search_query = st.text_input("🔍 Quick Search:", placeholder="Search...")
            
        filtered_df = route_filtered_df.copy()
        if lorry_filter != "ALL" and lorry_col:
            filtered_df = filtered_df[filtered_df[lorry_col].astype(str) == lorry_filter]
        
        if search_query and lorry_col:
            filtered_df = filtered_df[filtered_df[lorry_col].astype(str).str.contains(search_query, case=False, na=False)]
        # ===========================================================================

        if not filtered_df.empty:
            summary_df = pd.crosstab(filtered_df['Route Path'], filtered_df['Status_Category']).reset_index()
            
            for col in ['Ontime Arrival', 'Late Arrival', 'In-Transit', 'Running Delay']:
                if col not in summary_df.columns:
                    summary_df[col] = 0
                    
            summary_df['Total_Trips'] = summary_df[['Ontime Arrival', 'Late Arrival', 'In-Transit', 'Running Delay']].sum(axis=1)

            def format_pct(count, total):
                if total > 0:
                    return f"{round((count/total)*100, 1)}% ({int(count)})"
                return "0.0% (0)"

            for col in ['Ontime Arrival', 'Late Arrival', 'In-Transit', 'Running Delay']:
                summary_df[col] = summary_df.apply(lambda x: format_pct(x[col], x['Total_Trips']), axis=1)

            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("Client Arrival Performance Summary")
            st.markdown("*💡 Tip: Kisi bhi row (Route) par click karein aur uska detail niche dekhein.*")

            styled_df = summary_df.style.map(lambda x: 'color: #00ff00; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['Ontime Arrival']) \
                                        .map(lambda x: 'color: #ff4b4b; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['Late Arrival']) \
                                        .map(lambda x: 'color: #ffa500; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['In-Transit', 'Running Delay'])

            selection_event = st.dataframe(
                styled_df, 
                use_container_width=True, 
                hide_index=True,
                on_select="rerun",            
                selection_mode="single-row"  
            )

            if len(selection_event.selection.rows) > 0:
                selected_row_index = selection_event.selection.rows[0]
                clicked_route = summary_df.iloc[selected_row_index]['Route Path']
                
                detailed_data = filtered_df[filtered_df['Route Path'] == clicked_route].copy()
                total_trips = len(detailed_data)
                
                st.markdown("---")
                st.markdown(f"### 📄 <span style='color:#00ff00'>TEJAS CARGO INDIA PVT LTD</span> • <span style='color:#00ff00'>{clicked_route}</span> • {total_trips} trips", unsafe_allow_html=True)
                
                filter_option = st.radio(
                    "🚦 Data Filter Karein:",
                    ["ALL DATA", "RUNNING VEHICLE ONTIME", "RUNNING DELAY", "DELAY", "REPORTED VEHICLE"],
                    horizontal=True
                )
                
                if filter_option == "RUNNING VEHICLE ONTIME":
                    detailed_data = detailed_data[detailed_data['Status_Category'] == 'In-Transit']
                elif filter_option == "RUNNING DELAY":
                    detailed_data = detailed_data[detailed_data['Status_Category'] == 'Running Delay']
                elif filter_option == "DELAY":
                    detailed_data = detailed_data[detailed_data['Status_Category'] == 'Late Arrival']
                elif filter_option == "REPORTED VEHICLE":
                    detailed_data = detailed_data[detailed_data['Status_Category'].isin(['Late Arrival', 'Ontime Arrival'])]

                if detailed_data.empty:
                    st.warning(f"Is category ({filter_option}) mein abhi koi gaadi nahi hai.")
                else:
                    display_cols = [c for c in detailed_data.columns if c != 'Status_Category']
                    show_df = detailed_data[display_cols]
                    
                    st.dataframe(show_df, use_container_width=True, hide_index=True)
                    
                    buffer_selected = io.BytesIO()
                    with pd.ExcelWriter(buffer_selected, engine='openpyxl') as writer:
                        detailed_data.to_excel(writer, index=False, sheet_name='Selected_Records')
                    
                    st.download_button(
                        label="📥 Download Data",
                        data=buffer_selected.getvalue(),
                        file_name=f"Selected_{clicked_route}_{filter_option}.xlsx",
                        mime="application/vnd.ms-excel"
                    )
        else:
            st.warning("⚠️ Koi data available nahi hai. Kripya upar file upload karein.")
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Filtered Client Report')
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📊 Download All Data",
            data=buffer.getvalue(),
            file_name="Filtered_Client_Report.xlsx",
            mime="application/vnd.ms-excel",
            type="primary"
        )
else:
    st.title(selected_nav.replace("💳 ", "").replace("📱 ", "").replace("💰 ", "").replace("📝 ", "").replace("🔐 ", ""))
    st.info("🚧 Yeh page abhi ban raha hai (Work in Progress).")
