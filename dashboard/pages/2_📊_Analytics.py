"""Analytics Page for QuadCast Dashboard"""
import streamlit as st
import pandas as pd
from rds_queries import get_rds_connection, get_num_episodes_per_podcast
from visualisations import create_episodes_per_podcast_bar

# Page configuration
st.set_page_config(
    page_title="Analytics - QuadCast",
    page_icon="📊",
    layout="wide"
)

# Cache the database connection


@st.cache_resource
def get_connection():
    """Get cached database connection"""
    return get_rds_connection()


# Title
st.title("📊 Analytics")
st.markdown("View insights and statistics about your podcast collection")

# Get connection
conn = get_connection()

# Sidebar
st.sidebar.markdown("## 🎛️ Filters")
st.sidebar.markdown("---")

# Main content area
st.markdown("### 📈 Overview")


# Tabs for different sections
tab1, tab2, tab3 = st.tabs(["Overview", "Podcasts", "Episodes"])

with tab1:
    st.markdown("#### Overview Section")

with tab2:
    st.markdown("#### Podcasts Analytics")

    # Get data
    episodes_per_podcast = get_num_episodes_per_podcast(conn)

    # Summary metrics at the top
    st.markdown("##### 📊 Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)

    total_episodes = episodes_per_podcast['episode_count'].sum()
    avg_episodes = episodes_per_podcast['episode_count'].mean()
    max_episodes = episodes_per_podcast['episode_count'].max()
    min_episodes = episodes_per_podcast['episode_count'].min()

    with col1:
        st.metric("Total Episodes", int(total_episodes))

    with col2:
        st.metric("Avg per Podcast", f"{avg_episodes:.1f}")

    with col3:
        st.metric("Most Episodes", int(max_episodes))

    with col4:
        st.metric("Least Episodes", int(min_episodes))

    st.divider()

    # Chart full width
    st.markdown("##### 📈 Episodes per Podcast")
    chart = create_episodes_per_podcast_bar(episodes_per_podcast)
    st.altair_chart(chart, use_container_width=True)


with tab3:
    st.markdown("#### Episodes Section")


st.divider()
st.caption("QuadCast Analytics | Built with Streamlit")

# tables:
# speakers per episode
# how often a podcast uploads new episodes
# topics covered in episodes/podcasts
# most active podcasts (by episode count)
# average episode length per podcast
# number of podcasts/episodes over time
