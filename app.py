# 👉 JAB KOI ROW CLICK HOGI, TOH YAHAN DATA SHOW HOGA
        if len(selection_event.selection.rows) > 0:
            selected_row_index = selection_event.selection.rows[0]
            clicked_destination = summary_df.iloc[selected_row_index]['Destination']
            
            # Sirf us destination ka data filter karna
            detailed_data = filtered_df[filtered_df['Destination'] == clicked_destination].copy()
            total_trips = len(detailed_data)
            
            st.markdown("---")
            
            # 1. Custom Header (Image ki tarah)
            st.markdown(f"### 📄 <span style='color:#00ff00'>TEJAS CARGO INDIA PVT LTD</span> • <span style='color:#00ff00'>{clicked_destination}</span> • Route Path • {total_trips} trips", unsafe_allow_html=True)
            
            # 2. Columns set karna aur Table Style karna
            display_cols = ['Date', 'From', 'Destination', 'Lorry No.', 'Veh.Type', 'Expected Dly. Date & Time', 'Final Touching Reporting Date & Time', 'Late Hrs', 'Status_Category']
            show_df = detailed_data[[c for c in display_cols if c in detailed_data.columns]]
            
            # Late aane wali gaadiyon ki row ko RED color karna
            def style_detailed_row(row):
                if row.get('Status_Category') == 'Late Arrival':
                    # Dark red background with light red text
                    return ['background-color: #3b1c1c; color: #ff6b6b'] * len(row)
                return [''] * len(row)
                
            styled_detail = show_df.style.apply(style_detailed_row, axis=1)
            
            st.dataframe(styled_detail, use_container_width=True, hide_index=True)
            
            # 3. Selected Data Download Button
            buffer_selected = io.BytesIO()
            with pd.ExcelWriter(buffer_selected, engine='openpyxl') as writer:
                detailed_data.to_excel(writer, index=False, sheet_name='Selected_Records')
            
            st.download_button(
                label="📥 Download selected performance records (formatted Excel)",
                data=buffer_selected.getvalue(),
                file_name=f"Selected_{clicked_destination}_Records.xlsx",
                mime="application/vnd.ms-excel"
            )
            
            # 4. 7-Day Comparison Section
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.subheader("7-day and overall vendor comparison")
            st.markdown("<small style='color:gray'>Previous 7 days vs Current 7 days</small>", unsafe_allow_html=True)
            
            # Dummy data for comparison (Aap isko apne date logic se connect kar sakte hain)
            comp_data = {
                "Vendor": ["TEJAS CARGO INDIA PVT LTD"],
                "Previous 7 Days Trips": [8],
                "Previous 7 Days On-time": ["2 • 25.0%"],
                "Previous 7 Days Late": ["6 • 75.0%"],
                "Current 7 Days Trips": [8],
                "Current 7 Days On-time": ["0 • 0.0%"],
                "Current 7 Days Late": ["7 • 87.5%"]
            }
            comp_df = pd.DataFrame(comp_data)
            
            # Comparison table ko thoda dark aur highlight karna
            styled_comp = comp_df.style.map(lambda x: 'background-color: #3b1c1c; color: #ff6b6b' if '75.0%' in str(x) or '87.5%' in str(x) else '')
            st.dataframe(styled_comp, hide_index=True, use_container_width=True)
