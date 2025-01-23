import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Page config
st.set_page_config(page_title="Bible Reading Schedule", layout="wide")

def parse_time_column(col_name):
    """Extract time and date from column name like '5:00 pm Jan 29'"""
    try:
        parts = col_name.split()
        if len(parts) >= 4:  # Normal format "5:00 pm Jan 29"
            time = f"{parts[0]} {parts[1]}"
            date = f"{parts[2]} {parts[3]}"
            return time.lower(), date
        elif 'am' in col_name.lower() or 'pm' in col_name.lower():  # Handle any variations
            return col_name.lower(), ''
        return None, None
    except:
        return None, None

def get_day_of_week(date_str):
    """Convert 'Jan 29' to day of week"""
    try:
        # Add year 2025 since we know the dates
        full_date = f"{date_str} 2025"
        date_obj = datetime.strptime(full_date, '%b %d %Y')
        return date_obj.strftime('%A')
    except:
        return None

def process_registrations(df):
    """Convert registration data into schedule format"""
    # Initialize schedule structure
    schedule = {}
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    # Process each time slot column
    for col in df.columns:
        time, date = parse_time_column(col)
        if time and date:
            day = get_day_of_week(date)
            if day in days:
                # Find all people registered for this time slot
                registered = df[df[col] == 1]
                if not registered.empty:
                    names = [f"{row['First Name']} {row['Last Name']}" 
                            for _, row in registered.iterrows() 
                            if row['Status'] == 'Active']
                    
                    if time not in schedule:
                        schedule[time] = {d: '' for d in days}
                    schedule[time][day] = ', '.join(names)

    # Convert to DataFrame
    schedule_df = pd.DataFrame.from_dict(schedule, orient='index')
    schedule_df.index.name = 'Time'
    schedule_df.reset_index(inplace=True)
    
    # Sort by time
    def time_key(t):
        try:
            return datetime.strptime(t, '%I:%M %p')
        except:
            return datetime.strptime('12:00 AM', '%I:%M %p')
    
    schedule_df = schedule_df.sort_values(
        by='Time',
        key=lambda x: pd.Series(x).apply(time_key)
    )
    
    return schedule_df

def get_location(day, time_str):
    """Determine location based on day and time"""
    try:
        # Parse the time
        time = datetime.strptime(time_str.lower(), '%I:%M %p').time()
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

def export_to_excel(df):
    """Create formatted Excel file"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Schedule', index=False)
        worksheet = writer.sheets['Schedule']
        
        # Format columns
        worksheet.set_column('A:A', 15)  # Time column
        worksheet.set_column('B:G', 30)  # Day columns
        
        # Add formats
        format_torrance = writer.book.add_format({'bg_color': '#E6F3FF'})
        format_manhattan = writer.book.add_format({'bg_color': '#E6FFE6'})
        
        # Apply colors based on location
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
            # Read registration data
            df = pd.read_csv(uploaded_file)
            
            # Process into schedule format
            schedule_df = process_registrations(df)
            
            # Display schedule with formatting
            st.markdown("### Current Schedule")
            
            # Color formatting for display
            def color_cells(val, time, col_name):
                if col_name == 'Time':
                    return ''
                location = get_location(col_name, time)
                if location == 'Torrance':
                    return 'background-color: #E6F3FF'
                elif location == 'Manhattan Beach':
                    return 'background-color: #E6FFE6'
                return ''
            
            styled_df = schedule_df.style.apply(
                lambda row: [color_cells(val, row['Time'], col) for col in schedule_df.columns], 
                axis=1
            )
            
            st.dataframe(
                styled_df,
                hide_index=True,
                use_container_width=True
            )
            
            # Export button
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
            st.write("Error details:", e)
            
            # Debug information
            if st.checkbox("Show Debug Info"):
                st.write("Columns in file:", df.columns.tolist())
                time_cols = [col for col in df.columns if 'am' in col.lower() or 'pm' in col.lower()]
                st.write("Time columns found:", time_cols[:10], "...")
    else:
        st.info("Please upload a registration CSV file to view the schedule")

if __name__ == "__main__":
    main()
