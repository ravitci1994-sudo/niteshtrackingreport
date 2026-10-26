# Yeh code `show_reported_vehicle_table` function ke andar aayega jahan date processing hoti hai

    parsed_rep_dt = pd.to_datetime(reported_df[final_rep_col], errors='coerce', dayfirst=True)
    reported_df['_Rep_Date_Obj'] = parsed_rep_dt.dt.date
    reported_df['_Rep_Date_Str'] = parsed_rep_dt.dt.strftime('%d-%m-%Y')
    
    # NAYA: Month nikalne ke liye
    reported_df['_Rep_Month'] = parsed_rep_dt.dt.strftime('%b-%Y') 
    month_options = ["ALL"] + reported_df['_Rep_Month'].dropna().unique().tolist()

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
        selected_delay_hours = "ALL"
        selected_month = "ALL"
    else:
        # 5 columns ki jagah 6 columns banaye gaye hain Month filter ke liye
        f_col1, f_col2, f_col3, f_col4, f_col5, f_col6 = st.columns(6)
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
        with f_col5:
            selected_month = st.selectbox(
                "🗓️ Filter by Month:",
                month_options,
                index=0,
                key=f"reported_month_filter_{unique_key}"
            )
        with f_col6:
            selected_delay_hours = st.selectbox(
                "⏱️ Filter by Delay Hours:",
                ["ALL", "Delay < 10 mins", "Delay < 20 mins", "Delay < 30 mins", "Delay < 40 mins", "Delay <= 1 hour"],
                index=0,
                key=f"reported_delay_hours_filter_{unique_key}"
            )

        st.markdown("📅 **Filter by Week (Multiple Selection):**")
        
        # NAYA: Sirf 1 se 4 weeks ke option fix kar diye hain
        all_week_options = ["Last 1 Week", "Last 2 Weeks", "Last 3 Weeks", "Last 4 Weeks"]

        if all_week_options:
            chk_cols = st.columns(4) # 4 columns for 4 weeks
            selected_weeks = []
            for i, wk in enumerate(all_week_options):
                with chk_cols[i % len(chk_cols)]:
                    if st.checkbox(wk, value=False, key=f"chk_rel_week_{unique_key}_{wk}"):
                        selected_weeks.append(wk)
        else:
            selected_weeks = []

    filtered_report_df = reported_df.copy()
    late_col = next((c for c in ['Late Hrs', 'Delay Hrs', 'Delay'] if c in filtered_report_df.columns), None)

    if not staff_filter:
        if selected_date != "ALL":
            filtered_report_df = filtered_report_df[filtered_report_df['_Rep_Date_Str'] == selected_date].copy()
        
        # NAYA: Month filter logic apply karna
        if selected_month != "ALL":
            filtered_report_df = filtered_report_df[filtered_report_df['_Rep_Month'] == selected_month].copy()
            
        if selected_weeks:
            filtered_report_df = filtered_report_df[filtered_report_df['_Rel_Week'].isin(selected_weeks)].copy()
