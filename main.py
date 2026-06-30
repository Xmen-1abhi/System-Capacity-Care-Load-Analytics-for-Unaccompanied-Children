import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
st.set_page_config(page_title="UAC Capacity Dashboard", layout="wide",page_icon="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQgpttUoDBFuTUVcxdk3ptJ_LMVsEq2IJwe2f42ieSfvg&s=10.png")
st.title(":red[HHS Unaccompanied Children Program Dashboard]",text_alignment="center")
st.subheader("A simple tool to track children in care pipeline facilities over time.")
#Load and Clean the Data safely
@st.cache_data
def load_data():
    # Read the uploaded CSV file
    df = pd.read_csv("HHS_Unaccompanied_Alien_Children_Program.csv")
    df.columns = df.columns.str.strip()
    # Convert 'Date' column to actual dates that Python can sort and filter
    df['Date'] = pd.to_datetime(df['Date'].str.strip(), format='%d-%b-%y', errors='coerce')
    df = df.dropna(subset=['Date']) # Remove rows with invalid dates
    df = df.sort_values('Date')     # Sort chronologically from oldest to newest
    # Clean up numeric columns (remove spaces and convert to numbers)
    cols_to_clean = [
        'Children apprehended and placed in CBP custody*', 
        'Children in CBP custody', 
        'Children transferred out of CBP custody', 
        'Children in HHS Care', 
        'Children discharged from HHS Care'
    ]
    for col in cols_to_clean:
        if col in df.columns:
            # Remove anything that isn't a digit, then convert to number
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce').fillna(0)
            
    return df
df = load_data()
st.sidebar.header("📅 Filter Options")
min_date = df['Date'].min().date()
max_date = df['Date'].max().date()

selected_dates = st.sidebar.date_input( "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Apply the date filter to the dataset
if len(selected_dates) == 2:
    start_date, end_date = selected_dates
    filtered_df = df[(df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)]
elif len(selected_dates) == 1: 
    start_date = selected_dates[0]
    filtered_df = df[df['Date'].dt.date == start_date]
    st.sidebar.info(f"Showing data for: {start_date}")
else:
    filtered_df = df
# Calculate Simple Metrics
filtered_df['Total System Load'] = filtered_df['Children in CBP custody'] + filtered_df['Children in HHS Care']
# Get the numbers from the most recent day in our selection to show at the top
if not filtered_df.empty:
    latest_day = filtered_df.iloc[-1]
else:
    st.error("No data found for the selected date range.")
    st.stop()
# Display Summary Metric Cards at the Top
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Active Children in System", f"{int(latest_day['Total System Load'])}")
with col2:
    st.metric("Children in HHS Care Facilities", f"{int(latest_day['Children in HHS Care'])}")
with col3:
    st.metric("Latest Daily HHS Discharges", f"{int(latest_day['Children discharged from HHS Care'])}")

st.markdown("---")
st.markdown(
    """
    <h3 style='color: #2E8B57; font-family: Arial, sans-serif; font-weight: bold;'>
        📈 Active Children Count Over Time
    </h3>
    """, 
    unsafe_allow_html=True)
fig_line = px.line(
    filtered_df, 
    x='Date', 
    y=['Children in CBP custody', 'Children in HHS Care', 'Total System Load'],
    labels={'value': 'Number of Children', 'variable': 'Facility Category'},
    title="Daily Occupancy Trends"
)
st.plotly_chart(fig_line, use_container_width=True)

#  Flow comparison chart (Daily Intake vs Outflow)
st.markdown(
    """
    <h3 style='color: #2E8B57; font-family: Arial, sans-serif; font-weight: bold;'>
        🔄 Daily System Flows(Inflows vs Outflows)
    </h3>
    """, 
    unsafe_allow_html=True)
fig_flow = px.line(
    filtered_df,
    x='Date',
    y=['Children transferred out of CBP custody', 'Children discharged from HHS Care'],
    labels={'value': 'Daily Count', 'variable': 'Flow Type'},
    title="Children Entering HHS Care vs. Children Discharged to Sponsors"
)
st.plotly_chart(fig_flow, use_container_width=True)

# Show Data Table at the bottom if the user wants to see it
if st.checkbox("Show Raw Filtered Data Table"):
   st.markdown(
    """<h3 style='color: #2E8B57; font-family: Arial, sans-serif; font-weight: bold;'>
        📋 Data View</h3> """, unsafe_allow_html=True)
   st.dataframe(filtered_df, use_container_width=True)
