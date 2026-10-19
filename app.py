import streamlit as st
import pandas as pd
from datetime import date
import io
import os
import urllib.parse

# 1. Page Configuration
st.set_page_config(page_title="Client Performance Dashboard", layout="wide", initial_sidebar_state="expanded")

DATA_FILE = "saved_client_data.pkl"

# ================= MEMORY SETUP =================
if 'client_data' not in st.session_state:
    if os.path.exists(DATA_FILE):
        st.session_state.client_data = pd.read_pickle(DATA_FILE)
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
        uploaded_file = st.file_uploader("📂 Apni 'MIS for Placement' Excel file yahan upload karein", type=["xlsx", "csv"])

        if uploaded_file is not None:
            if st.button("🚀 Process & Save Report permanently", type="primary"):
                try:
                    df = pd.read_excel(uploaded_file)
                    
                    # NAYA FEATURE: From aur Destination ko jod kar "Route Path" banana
                    if 'From' in df.columns and 'Destination' in df.columns:
                        df['Route Path'] = df['From'].astype(str).str.strip().str.upper() + " TO " + df['Destination'].astype(str).str.strip().str.upper()
                    else:
                        df['Route Path'] = "Unknown Route"

                    def get_arrival_status(row):
                        if pd.isna(row.get('Final Touching Reporting Date & Time')):
                            return "In-Transit"
                        elif pd.notna(row.get('Late Hrs')):
                            return "Late Arrival"
                        else:
                            return "Ontime Arrival"
                            
                    df['Status_Category'] = df.apply(get_arrival_status, axis=1)
                    
                    st.session_state.client_data = df
                    df.to_pickle(DATA_FILE) 
                    
                    st.success("✅ File Data processed aur save ho gaya!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error processing file: {e}")
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
            
        f1, f2, f3, f4, f5 = st.columns(5)
        
        with f1:
            client_list = ["ALL"] + list(df['Party'].dropna().unique()) if 'Party' in df.columns else ["ALL"]
            client_filter = st.selectbox("Filter by Client:", client_list)
            
        client_filtered_df = df.copy()
        if client_filter != "ALL":
            client_filtered_df = client_filtered_df[client_filtered_df['Party'] == client_filter]

        with f2:
            staff_list = ["ALL"] + list(client_filtered_df['Controlling Staff Name'].dropna().unique()) if 'Controlling Staff Name' in client_filtered_df.columns else ["ALL"]
            staff_filter = st.selectbox("Filter by Staff:", staff_list)

        staff_filtered_df = client_filtered_df.copy()
        if staff_filter != "ALL":
            staff_filtered_df = staff_filtered_df[staff_filtered_df['Controlling Staff Name'] == staff_filter]

        with f3:
            # Ab yahan 'From' ki jagah poora 'Route Path' aayega
            ro_list = ["ALL"] + sorted(list(staff_filtered_df['Route Path'].dropna().unique())) if 'Route Path' in staff_filtered_df.columns else ["ALL"]
            ro_filter = st.selectbox("Filter by Route:", ro_list)
            
        route_filtered_df = staff_filtered_df.copy()
        if ro_filter != "ALL":
            route_filtered_df = route_filtered_df[route_filtered_df['Route Path'] == ro_filter]

        with f4:
            dest_list = ["ALL"] + sorted(list(route_filtered_df['Destination'].dropna().unique())) if 'Destination' in route_filtered_df.columns else ["ALL"]
            dest_filter = st.selectbox("Filter by Destination:", dest_list)

        with f5:
            search_query = st.text_input("🔍 Quick Search:", placeholder="Search Lorry...")
            
        filtered_df = route_filtered_df.copy()
        if dest_filter != "ALL":
            filtered_df = filtered_df[filtered_df['Destination'] == dest_filter]
        if search_query:
            filtered_df = filtered_df[filtered_df['Lorry No.'].astype(str).str.contains(search_query, case=False, na=False)]

        if not filtered_df.empty:
            # Table ko bhi 'Destination' ki jagah 'Route Path' se group kiya hai
            summary_df = pd.crosstab(filtered_df['Route Path'], filtered_df['Status_Category']).reset_index()
            
            for col in ['Ontime Arrival', 'Late Arrival', 'In-Transit']:
                if col not in summary_df.columns:
                    summary_df[col] = 0
                    
            summary_df['Total_Trips'] = summary_df[['Ontime Arrival', 'Late Arrival', 'In-Transit']].sum(axis=1)

            def format_pct(count, total):
                if total > 0:
                    return f"{round((count/total)*100, 1)}% ({int(count)})"
                return "0.0% (0)"

            for col in ['Ontime Arrival', 'Late Arrival', 'In-Transit']:
                summary_df[col] = summary_df.apply(lambda x: format_pct(x[col], x['Total_Trips']), axis=1)

            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("Client Arrival Performance Summary")
            st.markdown("*💡 Tip: Kisi bhi row (Route) par click karein aur uska detail niche dekhein.*")

            styled_df = summary_df.style.map(lambda x: 'color: #00ff00; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['Ontime Arrival']) \
                                        .map(lambda x: 'color: #ff4b4b; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['Late Arrival']) \
                                        .map(lambda x: 'color: #ffa500; font-weight: bold' if x != "0.0% (0)" else 'color: gray', subset=['In-Transit'])

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
                    ["ALL DATA", "RUNNING VEHICLE ONTIME", "DELAY", "REPORTED VEHICLE"],
                    horizontal=True
                )
                
                if filter_option == "RUNNING VEHICLE ONTIME":
                    detailed_data = detailed_data[detailed_data['Status_Category'] == 'In-Transit']
                elif filter_option == "DELAY":
                    detailed_data = detailed_data[detailed_data['Status_Category'] == 'Late Arrival']
                elif filter_option == "REPORTED VEHICLE":
                    detailed_data = detailed_data[detailed_data['Status_Category'] != 'In-Transit']

                if detailed_data.empty:
                    st.warning(f"Is category ({filter_option}) mein abhi koi gaadi nahi hai.")
                else:
                    display_cols = ['Date', 'Route Path', 'Lorry No.', 'Veh.Type', 'Expected Dly. Date & Time', 'Final Touching Reporting Date & Time', 'Late Hrs', 'Tracking Remark', 'Client Remarks', 'Status_Category']
                    show_df = detailed_data[[c for c in display_cols if c in detailed_data.columns]]
                    
                    def style_detailed_row(row):
                        if row.get('Status_Category') == 'Late Arrival':
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
                        delay_mail_data = detailed_data[detailed_data['Status_Category'] == 'Late Arrival']
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
                
                for col in ['Ontime Arrival', 'Late Arrival', 'In-Transit']:
                    if col not in route_comp.columns:
                        route_comp[col] = 0
                        
                route_comp['Total_Trips'] = route_comp[['Ontime Arrival', 'Late Arrival', 'In-Transit']].sum(axis=1)
                
                def format_comp(count, total):
                    if total > 0:
                        return f"{int(count)} • {round((count/total)*100, 1)}%"
                    return "0 • 0.0%"
                    
                route_comp['On-Time'] = route_comp.apply(lambda x: format_comp(x['Ontime Arrival'], x['Total_Trips']), axis=1)
                route_comp['Late'] = route_comp.apply(lambda x: format_comp(x['Late Arrival'], x['Total_Trips']), axis=1)
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
