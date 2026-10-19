import streamlit as st
import pandas as pd
import io

# Dashboard ki main settings
st.set_page_config(page_title="Daily Fleet Placement & Delay Report", page_icon="🚛", layout="wide")

st.title("🚛 Daily Fleet Placement & Delay Dashboard")
st.markdown("Is dashboard mein apni daily MIS file upload karein. Ye automatically trips ko analyze karke On-Time aur Delay ki summary aur charts bana dega.")

# File Uploader
uploaded_file = st.file_uploader("Upload 'MIS for Placement' Excel File", type=['xlsx'])

if uploaded_file:
    try:
        # File read karna
        df = pd.read_excel(uploaded_file)
        
        # Status nikalne ka logic
        def get_arrival_status(row):
            if pd.isna(row.get('Final Touching Reporting Date & Time')):
                return "In Transit / Pending"
            elif pd.notna(row.get('Late Hrs')):
                return "Delayed"
            else:
                return "On Time"
                
        df['Arrival Status'] = df.apply(get_arrival_status, axis=1)
        
        # ==== KPI METRICS CALCULATE KARNA ====
        total_trips = len(df)
        in_transit = len(df[df['Arrival Status'] == 'In Transit / Pending'])
        completed = total_trips - in_transit
        on_time = len(df[df['Arrival Status'] == 'On Time'])
        delayed = len(df[df['Arrival Status'] == 'Delayed'])
        
        on_time_pct = round((on_time / completed * 100), 1) if completed > 0 else 0
        delayed_pct = round((delayed / completed * 100), 1) if completed > 0 else 0
        
        # ==== TOP SUMMARY SECTION ====
        st.subheader("📈 Overall Performance Summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Trips Placed", total_trips)
        c2.metric("In Transit / Pending", in_transit)
        c3.metric("✅ On Time Arrivals", f"{on_time}", f"{on_time_pct}%")
        c4.metric("🚨 Delayed Arrivals", f"{delayed}", f"-{delayed_pct}%")
        
        st.markdown("---")
        
        # ==== CHARTS / VISUAL SUMMARY ====
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📍 Route-wise Performance (Destination)")
            route_df = df[df['Arrival Status'] != 'In Transit / Pending']
            if not route_df.empty:
                # Destination ke hisaab se On-time vs Delay ka graph
                dest_summary = pd.crosstab(route_df['Destination'], route_df['Arrival Status'])
                st.bar_chart(dest_summary, color=["#ff4b4b", "#00cc96"] if 'Delayed' in dest_summary else None)
            else:
                st.info("No completed trips available for route summary.")
                
        with col2:
            st.subheader("🚛 Lorry Type Performance")
            if not route_df.empty:
                # Gaadi ke type ke hisaab se graph
                veh_summary = pd.crosstab(route_df['Veh.Type'], route_df['Arrival Status'])
                st.bar_chart(veh_summary)
                
        st.markdown("---")
        
        # ==== ACTIONABLE DATA (FOCUS AREA) ====
        st.subheader("⏱️ Delayed Vehicles List (Action Required)")
        st.markdown("Yahan sirf wo gaadiyan dikhayi gayi hain jo late hui hain, taki aap unpar focus kar sakein.")
        delayed_df = df[df['Arrival Status'] == 'Delayed'][
            ['Lorry No.', 'From', 'Destination', 'Veh.Type', 'Expected Dly. Date & Time', 'Final Touching Reporting Date & Time', 'Late Hrs', 'Client Remarks']
        ]
        
        if not delayed_df.empty:
            st.dataframe(delayed_df, use_container_width=True)
        else:
            st.success("Badiya Kaam! Aaj koi bhi gaadi delay nahi hui hai.")
            
        st.markdown("---")
        
        # ==== DOWNLOAD SECTION ====
        st.subheader("📥 Download Full Processed Data")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Summary Report')
            
        st.download_button(
            label="Download Updated Report (Excel)",
            data=buffer.getvalue(),
            file_name="Daily_Placement_Summary.xlsx",
            mime="application/vnd.ms-excel",
            type="primary"
        )

    except Exception as e:
        st.error(f"File process karne mein dikkat aayi: {e}")
