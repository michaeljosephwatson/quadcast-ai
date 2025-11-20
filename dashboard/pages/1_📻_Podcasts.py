"""QuadCast Dashboard - Podcasts Page"""
import streamlit as st
import pandas as pd
from rds_queries import get_rds_connection, get_all_podcasts, get_episodes_with_podcast_info

# Page configuration
st.set_page_config(
    page_title="Podcasts - QuadCast",
    page_icon="🎙️",
    layout="wide"
)

# Cache the database connection


@st.cache_resource
def get_connection():
    """Get cached database connection"""
    return get_rds_connection()

# Cache the data


@st.cache_data(ttl=60)
def get_podcasts_data(_conn):
    """Get all podcasts data"""
    return get_all_podcasts(_conn)


@st.cache_data(ttl=60)
def get_episodes_data(_conn):
    """Get all episodes with podcast info"""
    return get_episodes_with_podcast_info(_conn)


conn = get_connection()
st.title("🎙️ Podcasts")
st.markdown("Browse and explore your podcast collection")

# Get all podcasts
podcasts_df = get_podcasts_data(conn)

if podcasts_df.empty:
    st.warning("No podcasts found. Please subscribe to podcasts first!")

# Get all episodes
episodes_df = get_episodes_data(conn)

st.sidebar.markdown("## 🎯 Select Content")
st.sidebar.markdown("---")

podcast_names = sorted(podcasts_df['podcast_name'].unique().tolist())

selected_podcast_name = st.sidebar.selectbox(
    "📻 Choose a Podcast:",
    options=podcast_names,
    key="podcast_selector"
)
