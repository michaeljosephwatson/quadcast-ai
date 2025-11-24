"""Analytics Page for QuadCast Dashboard"""
import streamlit as st
import pandas as pd
from rds_queries import get_rds_connection, get_num_episodes_per_podcast, get_topics_per_podcast
from visualisations import create_episodes_per_podcast_bar, create_topics_by_podcast_stacked

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
tab1, tab2 = st.tabs(["Podcasts", "Episodes"])

with tab1:
    st.markdown("#### Podcasts Analytics")

    # Get data
    episodes_per_podcast = get_num_episodes_per_podcast(conn)

    col1, col2, col3, col4, col5 = st.columns(5)

    total_podcasts = len(episodes_per_podcast)
    total_episodes = episodes_per_podcast['episode_count'].sum()
    avg_episodes = episodes_per_podcast['episode_count'].mean()
    max_episodes = episodes_per_podcast['episode_count'].max()
    min_episodes = episodes_per_podcast['episode_count'].min()

    with col1:
        st.metric("Total Podcasts", int(total_podcasts))

    with col2:
        st.metric("Total Episodes", int(total_episodes))

    with col3:
        st.metric("Avg per Podcast", f"{avg_episodes:.1f}")

    with col4:
        st.metric("Most Episodes", int(max_episodes))

    with col5:
        st.metric("Least Episodes", int(min_episodes))

    st.divider()

    # Chart full width
    st.markdown("##### 📈 Episodes per Podcast")
    chart = create_episodes_per_podcast_bar(episodes_per_podcast)
    st.altair_chart(chart, use_container_width=True)

    st.divider()

    # Add the topics stacked chart
    st.markdown("##### 🏷️ Top 3 Topics per Podcast")
    topics_df = get_topics_per_podcast(conn)
    topics_chart = create_topics_by_podcast_stacked(topics_df)
    st.altair_chart(topics_chart, use_container_width=True)

with tab2:
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
