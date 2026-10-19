import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Daily Fleet Placement & Delay Report", page_icon="🚛", layout="wide")

st.title("🚛 Daily Fleet Placement & Delay Dashboard")
st.markdown("Apni daily MIS file upload karein aur **'Process & Show Report'** button par click karein.")

# 1. State/Memory initialize karna (taki data na hate)
if 'report_data' not in st.session_state:
    st.session_state.report_data = None
    
# 2. File Uploader
uploaded_file = st.file_uploader("Upload 'MIS for Placement' Excel File", type=['xlsx'])

# 3. Naya Button (Jisko dabane se process hoga)
if uploaded_file is not None:
    if st.button("Process & Show Report"):
        try:
            # File Read
            df = pd.read_excel(uploaded_file)
            
            # Status Logic
            def get_arrival_status(row):
                if pd.isna(row.get('Final Touching Reporting Date & Time')):
                    return "In Transit / Pending"
                elif pd.notna(row.get('Late Hrs')):
                    return "Delayed"
                else:
                    return "On Time"
                    
            df['Arrival Status'] = df.apply(get_arrival_status, axis=1)
            
            # Data ko "Memory" mein save karna
            st.session_state.report_data = df
            st.success("✅ Data Process ho gaya!")
            
        except Exception as e:
            st.error(f"File process karne mein dikkat aayi: {e}")

st.markdown("---")

# 4. Agar Memory mein data hai, toh Dashboard dikhana (chahe page kuch der ruka rahe)
if st.session_state.report_data is not None:
    df = st.session_state.report_data
    
    # KPIs Calculate
    total_trips = len(df)
    in_transit = len(df[df['Arrival Status'] == 'In Transit / Pending'])
    completed = total_trips - in_transit
    on_time = len(df[df['Arrival Status'] == 'On Time'])
    delayed = len(df[df['Arrival Status'] == 'Delayed'])
    
    on_time_pct = round((on_time / completed * 100), 1) if completed > 0 else 0
    delayed_pct = round((delayed / completed * 100), 1) if completed > 0 else 0
    
    # Summary Boxes
    st.subheader("📈 Overall Performance Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Trips Placed", total_trips)
    c2.metric("In Transit / Pending", in_transit)
    c3.metric("✅ On Time Arrivals", f"{on_time}", f"{on_time_pct}%")
    c4.metric("🚨 Delayed Arrivals", f"{delayed}", f"-{delayed_pct}%")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📍 Route-wise Performance")
        route_df = df[df['Arrival Status'] != 'In Transit / Pending']
        if not route_df.empty:
            dest_summary = pd.crosstab(route_df['Destination'], route_df['Arrival Status'])
            st.bar_chart(dest_summary, color=["#ff4b4b", "#00cc96"] if 'Delayed' in dest_summary else None)
            
    with col2:
        st.subheader("🚛 Lorry Type Performance")
        if not route_df.empty:
            veh_summary = pd.crosstab(route_df['Veh.Type'], route_df['Arrival Status'])
            st.bar_chart(veh_summary)
            
    st.markdown("---")
    
    # Action Table
    st.subheader("⏱️ Delayed Vehicles List (Action Required)")
    delayed_df = df[df['Arrival Status'] == 'Delayed'][['Lorry No.', 'From', 'Destination', 'Veh.Type', 'Expected Dly. Date & Time', 'Final Touching Reporting Date & Time', 'Late Hrs', 'Client Remarks']]
    if not delayed_df.empty:
        st.dataframe(delayed_df, use_container_width=True)
    else:
        st.success("Koi gaadi delay nahi hui hai!")
        
    st.markdown("---")
    
    # Download Report Button
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
    
    # Clear Memory Button (taki naya data upload karna ho)
    if st.button("Clear Dashboard Data"):
        st.session_state.report_data = None
        st.rerun()
