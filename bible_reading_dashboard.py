import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Page config
st.set_page_config(page_title="Bible Reading Schedule", layout="wide")

def get_location(day, time_str):
    """Determine location based on day and time"""
    try:
        # Convert 12-hour time to 24-hour for comparison
        time_parts = time_str.replace("  ", " ").split()
        if len(time_parts) < 2:
            return None
            
        time = time_parts[0]
        ampm = time_parts[1].lower()
        
        hour = int(time.split(":")[0])
        if ampm == "pm" and hour != 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
            
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
    except Exception as e:
        print(f"Error in get_location: {e} for day={day}, time={time_str}")
        return None

def add_location_colors(df):
    """Add background colors based on location"""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    styled_df = df.style
    
    # Add background colors
    def apply_colors(row):
        colors = []
        for col in df.columns:
            if col == 'Time':
                colors.append('')
            else:
                location = get_location(col, row['Time'])
                if location == 'Torrance':
                    colors.append('background-color: #E6F3FF')
                elif location == 'Manhattan Beach':
                    colors.append('background-color: #E6FFE6')
                else:
                    colors.append('')
        return colors
    
    styled_df = df.style.apply(apply_colors, axis=1)
    return styled_df

def export_to_excel(df):
    """Create formatted Excel file"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Write the data
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
    uploaded_file = st.file_uploader("Upload schedule CSV file", type=['csv'])
    
    if uploaded_file:
        try:
            # Read CSV data
            df = pd.read_csv(uploaded_file)
            
            # Verify required columns
            required_columns = ['Time', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            if not all(col in df.columns for col in required_columns):
                st.error("CSV file must contain columns: Time, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday")
                return
            
            # Display schedule with colors
            st.markdown("### Current Schedule")
            styled_df = add_location_colors(df)
            st.dataframe(
                styled_df,
                hide_index=True,
                use_container_width=True
            )
            
            # Export button
            col1, col2 = st.columns([1, 5])
            with col1:
                excel_file = export_to_excel(df)
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
                st.write("Columns in file:", df.columns.tolist())
                st.write("First few rows:", df.head())
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.write("Error details:", e)
    else:
        st.info("Please upload a CSV file to view the schedule")

if __name__ == "__main__":
    main()
