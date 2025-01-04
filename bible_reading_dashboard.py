import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
import io

# Page config
st.set_page_config(page_title="Bible Reading Schedule", layout="wide")

def get_location(day, time):
    """Determine location based on day and time"""
    # Convert time to 24-hour format for comparison
    try:
        time_str = time.lower()
        hour = int(time_str.split(':')[0])
        is_pm = 'pm' in time_str
        hour_24 = hour + 12 if (is_pm and hour != 12) else hour
        
        day = day.lower()
        
        # Torrance: Monday 9am to Wednesday 5pm
        if day == 'monday' and hour_24 >= 9:
            return 'Torrance'
        if day == 'tuesday':
            return 'Torrance'
        if day == 'wednesday' and hour_24 < 17:
            return 'Torrance'
        
        # Manhattan Beach: Wednesday 5pm through Saturday 2pm
        if day == 'wednesday' and hour_24 >= 17:
            return 'Manhattan Beach'
        if day in ['thursday', 'friday']:
            return 'Manhattan Beach'
        if day == 'saturday' and hour_24 < 14:
            return 'Manhattan Beach'
        
        return None
    except:
        return None

def process_registrations(df):
    """Process registration data into schedule format"""
    # Generate time slots
    time_slots = []
    for hour in range(24):
        for minute in [0, 30]:
            time_slots.append(f"{hour if hour <= 12 else hour-12}:{minute:02d} {'am' if hour < 12 else 'pm'}")
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    # Create empty schedule
    schedule_data = []
    
    for time_slot in time_slots:
        row = {'Time': time_slot}
        for day in days:
            row[day] = ''
            location = get_location(day, time_slot)
            if location:
                # Find all registrations for this day and time
                names = []
                for _, reg in df.iterrows():
                    if reg['Status'] == 'Active':
                        reg_day = reg['Selection'].split(' at ')[0]
                        reg_location = reg['Selection'].split(' at ')[1]
                        
                        if day in reg_day and location == reg_location:
                            time_col = time_slot.lower()
                            if time_col in reg and reg[time_col] == 1:
                                names.append(f"{reg['First Name']} {reg['Last Name']}")
                
                row[day] = ', '.join(names) if names else ''
        
        schedule_data.append(row)
    
    return pd.DataFrame(schedule_data)

def export_to_excel(df):
    """Create formatted Excel file"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Schedule', index=False)
        worksheet = writer.sheets['Schedule']
        
        # Format columns
        worksheet.set_column('A:A', 15)  # Time column
        worksheet.set_column('B:G', 30)  # Day columns
    
    return buffer

def main():
    st.title("Bible Reading Event Schedule")
    
    st.markdown("""
    #### Location Schedule
    - **Torrance**: Monday 9:00 AM - Wednesday 5:00 PM
    - **Manhattan Beach**: Wednesday 5:00 PM - Saturday 2:00 PM
    """)
    
    # File upload
    uploaded_file = st.file_uploader("Upload registration CSV file", type=['csv'])
    
    if uploaded_file:
        try:
            # Read and process data
            df = pd.read_csv(uploaded_file)
            schedule_df = process_registrations(df)
            
            # Display schedule
            st.markdown("### Current Schedule")
            st.dataframe(
                schedule_df,
                hide_index=True,
                use_container_width=True
            )
            
            # Export buttons
            col1, col2 = st.columns([1, 5])
            with col1:
                excel_file = export_to_excel(schedule_df)
                st.download_button(
                    label="Download Excel",
                    data=excel_file.getvalue(),
                    file_name="bible-reading-schedule.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # Show last update time
            st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    else:
        st.info("Please upload a CSV file to view the schedule")

if __name__ == "__main__":
    main()
