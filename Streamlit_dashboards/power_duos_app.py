import streamlit as st
import pandas as pd
import snowflake.connector
import plotly.express as px

st.set_page_config(layout="wide", page_title="Director and Writer Synergy")

# --- Database Connection & Data Loading ---
@st.cache_data
def load_impact_data():
    conn = snowflake.connector.connect(**st.secrets["snowflake"])
    query = "SELECT * FROM GOLD.V_DIRECTOR_WRITER_IMPACT"
    df = pd.read_sql(query, conn)
    df.columns = df.columns.str.upper()
    conn.close()
    return df

try:
    df = load_impact_data()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

# --- Page Title & Subtitle ---
st.title("🎬 Director and Writer Synergy Analysis")
st.write("Quantifying creative impact of writer-director partnerships")


# --- Sidebar Filters ---
st.sidebar.header("Filters")
available_types = sorted(df['TYPE_NAME'].dropna().unique())
selected_type = st.sidebar.selectbox("Select Content Format", available_types)

type_filtered_df = df[df['TYPE_NAME'] == selected_type]
available_directors = sorted(type_filtered_df['DIRECTOR_NAME'].dropna().unique())
selected_director = st.sidebar.selectbox("Select Director", available_directors)

# --- Section 1: Global Highlights ---
# Dynamic header based on the selected content format
st.header(f" Global Highlights: {selected_type}s")

# Find the overall top duo for the SPECIFIC content format chosen
format_top_duo = type_filtered_df.loc[type_filtered_df['RATING_IMPACT_SCORE'].idxmax()]

st.subheader(f"🏆 Best Power Duo: {format_top_duo['DIRECTOR_NAME']} & {format_top_duo['WRITER_NAME']}")

col1, col2, col3 = st.columns(3)
col1.metric("📈Rating Impact", f"+{format_top_duo['RATING_IMPACT_SCORE']:.2f}")
col2.metric("⭐Duo Average Rating", f"{format_top_duo['DUO_RATING']:.2f}")
col3.metric("♠️Projects Together", int(format_top_duo['DUO_PROJECTS']))

st.markdown("---")

# --- Section 2: Deep Dive ---
st.header(f"Deep Dive: {selected_director}")
st.markdown(f"Visualising every impact of writer who has worked with '{selected_director}'")

# Filter data for the chosen director
director_df = type_filtered_df[type_filtered_df['DIRECTOR_NAME'] == selected_director].copy()

if director_df.empty:
    st.warning("No data available for this selection.")
    st.stop()

# Extract key metrics and rows for the Best/Worst partners
baseline_rating = director_df['DIRECTOR_BASELINE'].iloc[0]
best_row = director_df.loc[director_df['RATING_IMPACT_SCORE'].idxmax()]
worst_row = director_df.loc[director_df['RATING_IMPACT_SCORE'].idxmin()]

colA, colB, colC = st.columns(3)
colA.metric("Director's Baseline Rating", f"{baseline_rating:.2f}")

# Using the 'delta' parameter to show the increase/decrease below the name
colB.metric(
    label="Best Partner", 
    value=best_row['WRITER_NAME'], 
    delta=f"{best_row['RATING_IMPACT_SCORE']:.2f} over baseline"
)

colC.metric(
    label="Lowest Impact", 
    value=worst_row['WRITER_NAME'], 
    delta=f"{worst_row['RATING_IMPACT_SCORE']:.2f} under baseline",
    delta_color="inverse" # Makes a negative number red, positive green
)

# --- The Diverging Bar Chart ---
director_df['BAR_COLOR'] = director_df['RATING_IMPACT_SCORE'].apply(
    lambda x: '#008080' if x >= 0 else '#F88379' # Teal Green for positive, Coral Pink for negative
)

director_df = director_df.sort_values(by='RATING_IMPACT_SCORE', ascending=True)

fig = px.bar(
    director_df,
    x='RATING_IMPACT_SCORE',
    y='WRITER_NAME',
    orientation='h'
)

fig.update_traces(marker_color=director_df['BAR_COLOR'])
fig.update_layout(
    xaxis_title="Rating Impact",
    yaxis_title="Writer",
    showlegend=False
)

fig.add_vline(x=0, line_width=2, line_dash="dash", line_color="black")

st.plotly_chart(fig, use_container_width=True)

# --- Section 3: Raw Data ---
with st.expander(f"📄View Raw Data for {selected_director}"):
    display_df = director_df[['WRITER_NAME', 'DUO_PROJECTS', 'DUO_RATING', 'RATING_IMPACT_SCORE']].sort_values(by='DUO_RATING', ascending=False)
    
    display_df.rename(columns={
        'WRITER_NAME': 'Writer Name',
        'DUO_PROJECTS': 'Projects Together',
        'DUO_RATING': 'Duo Average Rating',
        'RATING_IMPACT_SCORE': 'Impact on Baseline'
    }, inplace=True)
    
    st.dataframe(display_df, use_container_width=True)