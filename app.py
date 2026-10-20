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
    if 'From' in df.columns and 'Destination' in df.columns:
        df['Route Path'] = df['From'].astype(str).str.strip().str.upper() + " TO " + df['Destination'].astype(str).str.strip().str.upper()
    else:
        df['Route Path'] = "UNKNOWN ROUTE"

    def get_arrival_status(row):
        final_rep = row.get('Final Touching Reporting Date & Time')
        exp_dly = row.get('Expected Dly. Date & Time')
        
        # 1. Agar report ho chuka hai
        if pd.notna(final_rep):
            if pd.notna(row.get('Late Hrs')):
                return "Late Arrival"
            else:
                return "Ontime Arrival"
        else:
            # 2. Agar abhi In-Transit hai, toh check karein ki Running Delay hai ya On-time
            try:
                if pd.notna(exp_dly):
                    exp_dt = pd.to_datetime(exp_dly)
                    current_time = datetime.now()
                    # Agar expected time nikal chuka hai aur abhi tak reporting nahi hui
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
        df_loaded = pd.read_pickle(DATA_FILE)
        st.session_state.client_data = process_dataframe(df_loaded)
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

    if st.session_state.client_data is None:
        uploaded_files = st.file_uploader(
            "📂 Apni 'MIS for Placement' Excel/CSV files yahan upload karein", 
            type=["xlsx", "csv"], 
            accept_multiple_files=True
        )

        if uploaded_files:
            if st.button("🚀 Process & Save Report permanently", type="primary"):
                try:
                    df_list = []
                    for uploaded_file in uploaded_files:
                        if uploaded_file.name.endswith('.csv'):
                            temp_df = pd.read_csv(uploaded_file)
                        else:
                            temp_df = pd.read_excel(uploaded_file)
                        df_list.append(temp_df)
                    
                    # Sabhi files ko combine karein
                    df = pd.concat(df_list, ignore_index=True)
                    df = process_dataframe(df)
                    
                    st.session_state.client_data = df
                    df.to_pickle(DATA_FILE) 
                    
                    st.success("✅ Sabhi files ka data successfully process aur save ho gaya!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error processing files: {e}")
    else:
        st.success("✅ Data saved hai! Nayi file upload karne ke liye Sidebar se 'PROCESS & REFRESH DATA' dabayein.")

    # ================= DASHBOARD =================
    if st.session_state.client_data is not None:
        df = st.session_state.client_data
        st.markdown("---")
        
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            start_date = st.date_input("🗓️ Start Date:", date(2026, 10, 1))
        with c2:
            end_date = st.date_input("🗓️ End Date:", date(2026, 10, 18))
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info(f"⏱️ **Selected Duration:** {(end_date - start_date).days} Days")
            
        # ================= 6 FILTERS INCLUDING VEHICLE NO =================
        f1, f2, f3, f4, f5, f6 = st.columns(6)
        
        with f1:
            zone_list = ["ALL"] + list(df['Zone'].dropna().unique()) if 'Zone' in df.columns else ["ALL", "NORTH", "SOUTH", "EAST", "WEST"]
            zone_filter = st.selectbox("Filter by Zone:", zone_list)
            
        zone_filtered_df = df.copy()
        if zone_filter != "ALL" and 'Zone' in df.columns:
            zone_filtered_df = zone_filtered_df[zone_filtered_df['Zone'] == zone_filter]

        with f2:
            client_list = ["ALL"] + list(zone_filtered_df['Party'].dropna().unique()) if 'Party' in zone_filtered_df.columns else ["ALL"]
            client_filter = st.selectbox("Filter by Client:", client_list)
            
        client_filtered_df = zone_filtered_df.copy()
        if client_filter != "ALL":
            client_filtered_df = client_filtered_df[client_filtered_df['Party'] == client_filter]

        with f3:
            staff_list = ["ALL"] + list(client_filtered_df['Controlling Staff Name'].dropna().unique()) if 'Controlling Staff Name' in client_filtered_df.columns else ["ALL"]
            staff_filter = st.selectbox("Filter by Staff:", staff_list)

        staff_filtered_df = client_filtered_df.copy()
        if staff_filter != "ALL":
            staff_filtered_df = staff_filtered_df[staff_filtered_df['Controlling Staff Name'] == staff_filter]

        with f4:
            ro_list = ["ALL"] + sorted(list(staff_filtered_df['Route Path'].dropna().unique())) if 'Route Path' in staff_filtered_df.columns else ["ALL"]
            ro_filter = st.selectbox("Filter by Route:", ro_list)
            
        route_filtered_df = staff_filtered_df.copy()
        if ro_filter != "ALL":
            route_filtered_df = route_filtered_df[route_filtered_df['Route Path'] == ro_filter]

        # Filter by Vehicle No (Lorry No.) instead of Destination
        with f5:
            lorry_list = ["ALL"] + sorted(list(route_filtered_df['Lorry No.'].dropna().astype(str).unique())) if 'Lorry No.' in route_filtered_df.columns else ["ALL"]
            lorry_filter = st.selectbox("Filter by Vehicle No:", lorry_list)

        with f6:
            search_query = st.text_input("🔍 Quick Search:", placeholder="Search...")
            
        filtered_df = route_filtered_df.copy()
        if lorry_filter != "ALL":
            filtered_df = filtered_df[filtered_df['Lorry No.'].astype(str) == lorry_filter]
        if search_query:
            filtered_df = filtered_df[filtered_df['Lorry No.'].astype(str).str.contains(search_query, case=False, na=False)]
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
                
                # ================= RUNNING DELAY BUTTON ADDED =================
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
                # ==============================================================

                if detailed_data.empty:
                    st.warning(f"Is category ({filter_option}) mein abhi koi gaadi nahi hai.")
                else:
                    display_cols = ['Date', 'Route Path', 'Lorry No.', 'Veh.Type', 'Expected Dly. Date & Time', 'Final Touching Reporting Date & Time', 'Late Hrs', 'Tracking Remark', 'Client Remarks', 'Status_Category']
                    show_df = detailed_data[[c for c in display_cols if c in detailed_data.columns]]
                    
                    def style_detailed_row(row):
                        if row.get('Status_Category') in ['Late Arrival', 'Running Delay']:
                            return ['background-color: #3b1c1c; color: #ff6b6b'] * len(row)
                        return [''] * len(row)
                        
                    styled_detail = show_df.style.apply(style_detailed_row, axis=1)
                    st.dataframe(styled_detail, use_container_width=True, hide_index=True)
                    
                    buffer_selected = io.BytesIO()
                    with pd.ExcelWriter(buffer_selected, engine='openpyxl') as writer:
                        detailed_data.to_excel(writer, index=False, sheet_name='Selected_Records')
                    
                    btn_col1, btn_col2 = st.columns([1, 3])
                    with btn_col1:
                        st.download_button(
                            label="📥 Download Data",
                            data=buffer_selected.getvalue(),
                            file_name=f"Selected_{clicked_route}_{filter_option}.xlsx",
                            mime="application/vnd.ms-excel"
                        )
                        
                    with btn_col2:
                        delay_mail_data = detailed_data[detailed_data['Status_Category'].isin(['Late Arrival', 'Running Delay'])]
                        if not delay_mail_data.empty:
                            mail_subject = f"Delay Report - {clicked_route}"
                            mail_body = "Dear Team,\n\nPlease find the details of delayed vehicles below:\n\n"
                            
                            for idx, row in delay_mail_data.iterrows():
                                lorry = row.get('Lorry No.', 'N/A')
                                delay_time = row.get('Late Hrs', 'N/A')
                                remark = row.get('Tracking Remark', 'N/A')
                                mail_body += f"🚛 Lorry No: {lorry} | Delay: {delay_time} | Remark: {remark}\n"
                                
                            mail_body += "\nRegards,\nTejas Cargo India Pvt Ltd"
                            mailto_link = f"mailto:?subject={urllib.parse.quote(mail_subject)}&body={urllib.parse.quote(mail_body)}"
                            
                            st.link_button("📧 Send Mail", mailto_link, type="secondary")
                
                # LAST 1 WEEK COMPARISON
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.subheader("📍 Last 1 Week Route-wise Performance")
                st.markdown("<small style='color:gray'>Aapke chune hue End Date se pichle 7 din ka data</small>", unsafe_allow_html=True)
                
                last_week_df = filtered_df.copy()
                if 'Date' in last_week_df.columns:
                    try:
                        last_week_df['Temp_Date'] = pd.to_datetime(last_week_df['Date'], errors='coerce').dt.date
                        last_7_days_start = end_date - pd.Timedelta(days=7)
                        last_week_df = last_week_df[(last_week_df['Temp_Date'] > last_7_days_start) & (last_week_df['Temp_Date'] <= end_date)]
                    except Exception as e:
                        pass
                        
                route_comp = pd.crosstab(last_week_df['Route Path'], last_week_df['Status_Category']).reset_index()
                
                for col in ['Ontime Arrival', 'Late Arrival', 'In-Transit', 'Running Delay']:
                    if col not in route_comp.columns:
                        route_comp[col] = 0
                        
                route_comp['Total_Trips'] = route_comp[['Ontime Arrival', 'Late Arrival', 'In-Transit', 'Running Delay']].sum(axis=1)
                
                def format_comp(count, total):
                    if total > 0:
                        return f"{int(count)} • {round((count/total)*100, 1)}%"
                    return "0 • 0.0%"
                    
                route_comp['On-Time'] = route_comp.apply(lambda x: format_comp(x['Ontime Arrival'], x['Total_Trips']), axis=1)
                route_comp['Late'] = route_comp.apply(lambda x: format_comp(x['Late Arrival'] + x['Running Delay'], x['Total_Trips']), axis=1)
                route_comp['Pending (In-Transit)'] = route_comp.apply(lambda x: format_comp(x['In-Transit'], x['Total_Trips']), axis=1)
                
                display_comp = route_comp[['Route Path', 'Total_Trips', 'On-Time', 'Late', 'Pending (In-Transit)']]
                
                def highlight_late(val):
                    if isinstance(val, str) and '•' in val:
                        pct = float(val.split('•')[1].strip('%').strip())
                        if pct > 0:
                            return 'background-color: #3b1c1c; color: #ff6b6b'
                    return ''
                    
                if display_comp.empty:
                    st.warning("Pichle 7 din (Last 1 Week) mein koi gaadi is route par nahi chali hai.")
                else:
                    styled_comp = display_comp.style.map(highlight_late, subset=['Late'])
                    st.dataframe(styled_comp, hide_index=True, use_container_width=True)

        else:
            st.warning("Chune gaye Filters ke hisaab se koi data nahi mila.")
        
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
