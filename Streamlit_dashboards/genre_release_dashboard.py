import streamlit as st
import pandas as pd
import snowflake.connector
import plotly.express as px

# Set page layout
st.set_page_config(layout="wide")

# Main Heading
st.title("Genre Release Insights Dashboard")

# --- Database Connection & Data Loading ---
@st.cache_data
def load_data():
    conn = snowflake.connector.connect(**st.secrets["snowflake"])
    query = "SELECT * FROM GOLD.GENRE_RELEASE_TIMING_PERFORMANCE"
    df = pd.read_sql(query, conn)
    # Ensure column names are uppercase to match standard Snowflake output
    df.columns = df.columns.str.upper() 
    conn.close()
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

# Sidebar for interactive filtering
st.sidebar.header("Filters")
selected_genres = st.sidebar.multiselect(
    "Select Genre",
    options=df['GENRE_NAME'].unique(),
    default=df['GENRE_NAME'].unique()[:1]
)

if not selected_genres:
    st.warning("Please select at least one genre from the sidebar to view data.")
    st.stop()

# Filter data based on selection
filtered_df = df[df['GENRE_NAME'].isin(selected_genres)]
# Map integer months to string abbreviations for a cleaner x-axis
month_map = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 
             7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}

best_month_num = filtered_df.groupby('RELEASE_MONTH')['AVG_RATING'].mean().idxmax()
best_month_name = month_map[best_month_num]

# --- Section 1: Global Highlights ---
st.header("Global Highlights")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Best Month",best_month_name)
col2.metric("Total Titles", int(filtered_df['TOTAL_TITLES'].sum()))
col3.metric("Average Rating", round(filtered_df['AVG_RATING'].mean(), 2))
col4.metric("Total Votes", int(filtered_df['TOTAL_VOTES'].sum()))

st.markdown("---")

# --- Section 2: Month-wise Rating Performance ---
st.header("Month-wise Rating Performance")



plot_df = filtered_df.copy()
plot_df['MONTH_NAME'] = plot_df['RELEASE_MONTH'].map(month_map)

# Sort by the numeric month so the line chart plots chronologically
plot_df = plot_df.sort_values(by='RELEASE_MONTH')

fig_line = px.line(
    plot_df,
    x='MONTH_NAME',
    y='AVG_RATING',
    color='GENRE_NAME',
    markers=True,
    labels={'MONTH_NAME': 'Month', 'AVG_RATING': 'Average Rating', 'GENRE_NAME': 'Genre'}
)

st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")

# --- Section 3: Top 3 Performing Months ---
st.header("Top 3 Performing Months")

top_months_df = filtered_df.copy()

# Add the 7th column (Month Name) based on the numeric release month
top_months_df['MONTH_NAME'] = top_months_df['RELEASE_MONTH'].map(month_map)

# Sort by Average Rating (primary) and Total Votes (secondary) to get the true top 3
top_months_df = top_months_df.sort_values(
    by=['AVG_RATING', 'TOTAL_VOTES'], 
    ascending=[False, False]
).head(3)

# Select all 7 columns for the final dataframe
display_cols = [
    'GENRE_NAME', 
    'RELEASE_QUARTER', 
    'RELEASE_MONTH', 
    'MONTH_NAME', 
    'AVG_RATING', 
    'TOTAL_VOTES', 
    'TOTAL_TITLES'
]
display_df = top_months_df[display_cols].copy()

# Rename the columns to match a clean dashboard presentation
display_df.rename(columns={
    'GENRE_NAME': 'Genre',
    'RELEASE_QUARTER': 'Quarter',
    'RELEASE_MONTH': 'Month Number',
    'MONTH_NAME': 'Month Name',
    'AVG_RATING': 'Avg Rating',
    'TOTAL_VOTES': 'Total Votes',
    'TOTAL_TITLES': 'Total Titles'
}, inplace=True)

# Set the index to 1, 2, 3 to represent the ranking
display_df.index = [1, 2, 3]

# Display the full 7-column table
st.dataframe(display_df, use_container_width=True)