import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import io

# Page config
st.set_page_config(page_title="Bible Reading Schedule", layout="wide")

def create_time_slots():
    """Create all possible 30-minute time slots"""
    slots = []
    for hour in range(24):
        for minute in [0, 30]:
            time = f"{hour:02d}:{minute:02d}"
            # Convert to 12-hour format
            dt = datetime.strptime(time, "%H:%M")
            slots.append(dt.strftime("%I:%M %p").lstrip("0").lower())
    return slots

def get_location(day, time_str):
    """Determine location based on day and time"""
    try:
        # Parse the time
        time = datetime.strptime(time_str, "%I:%M %p").time()
        hour = time.hour
        
        day = day.lower()
        
        # Torrance: Monday 9am to Wednesday 5pm
        if day == 'monday' and hour >= 9:
            return 'Torrance'
        if day == 'tuesday':
            return 'Torrance'
        if day == 'wednesday' and hour < 17:
            return 'Torrance'
        
        # Manhattan Beach: Wednesday 5pm through Saturday 2pm
        if day == 'wednesday' and hour >= 17:
            return 'Manhattan Beach'
        if day in ['thursday', 'friday']:
            return 'Manhattan Beach'
        if day == 'saturday' and hour < 14:
            return 'Manhattan Beach'
        
        return None
    except:
        return None

def process_registrations(df):
    """Process registration data into structured schedule"""
    # Create time slots
    time_slots = create_time_slots()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    # Initialize empty schedule
    schedule_data = []
    
    for time_slot in time_slots:
        row = {'Time': time_slot}
        
        for day in days:
            row[day] = ''
            location = get_location(day, time_slot)
            if location:
                # Find matching registration
                mask = (df['Time'].str.lower() == time_slot.lower()) & \
                       (df[day].notna())
                if any(mask):
                    row[day] = df.loc[mask, day].iloc[0]
        
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
        
        # Add color formatting
        format_torrance = writer.book.add_format({'bg_color': '#E6F3FF'})
        format_manhattan = writer.book.add_format({'bg_color': '#E6FFE6'})
        
        # Apply colors to locations
        for row_num in range(1, len(df) + 1):
            time = df.iloc[row_num-1]['Time']
            for col_num, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'], 1):
                location = get_location(day, time)
                if location == 'Torrance':
                    worksheet.write(row_num, col_num, df.iloc[row_num-1][day], format_torrance)
                elif location == 'Manhattan Beach':
                    worksheet.write(row_num, col_num, df.iloc[row_num-1][day], format_manhattan)
    
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
            
            # Process the schedule
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
            
            # Debug information
            if st.checkbox("Show Debug Info"):
                st.write("Sample Time Slots:", create_time_slots()[:10])
                st.write("Sample Row:", df.iloc[0].to_dict())
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.write("Error details:", e)
    else:
        st.info("Please upload a CSV file to view the schedule")

if __name__ == "__main__":
    main()
