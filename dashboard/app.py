"""QuadCast Dashboard Application Homepage"""
import streamlit as st
from rds_queries import (
    get_rds_connection, get_all_podcasts, get_all_episodes)

# Page configuration
st.set_page_config(
    page_title="QuadCast Homepage",
    page_icon="🎙️",
    layout="wide"
)

# Cache the database connection


@st.cache_resource
def get_connection():
    """Get cached database connection"""
    return get_rds_connection()

# Cache the data (refresh every 60 seconds)


@st.cache_data(ttl=60)
def get_all_data(_conn) -> dict:
    """Get all platform data with caching"""
    podcasts_df = get_all_podcasts(_conn)
    episodes_df = get_all_episodes(_conn)

    return {
        'podcasts_df': podcasts_df,
        'episodes_df': episodes_df
    }


@st.cache_data(ttl=60)
def calculate_metrics(data: dict) -> dict:
    """Calculate metrics from the cached data"""
    podcasts_df = data['podcasts_df']
    episodes_df = data['episodes_df']

    return {
        'podcasts': len(podcasts_df),
        'episodes': len(episodes_df),
        'transcripts': len(episodes_df[episodes_df['transcribed'] == True])
    }


# Get connection and data
conn = get_connection()
data = get_all_data(conn)
metrics = calculate_metrics(data)

# Header
st.title("🎙️ QuadCast Dashboard")
st.markdown("### AI-Powered Podcast Analytics Platform")

st.divider()

# Description section
st.markdown("""
## Welcome to QuadCast

QuadCast helps you manage and analyze your favorite podcasts with AI-powered insights.

**What you can do:**
- 🎙️ **Subscribe to Podcasts** - Add your favorite podcasts via RSS feed
- 📊 **View Episode Data** - Access detailed information about each episode
- 📝 **Read Transcripts** - Get full AI-generated transcripts of episodes
- 💡 **Explore Insights** - Discover trends, summaries, and analytics across your podcast library

Navigate through the pages to explore your podcasts and gain valuable insights!
""")

st.divider()

# Metrics section
st.subheader("📈 Platform Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Total Podcasts",
        value=metrics['podcasts']
    )

with col2:
    st.metric(
        label="Episodes Analyzed",
        value=metrics['episodes']
    )

with col3:
    st.metric(
        label="Transcripts Generated",
        value=metrics['transcripts']
    )

# Footer
st.divider()
st.caption("QuadCast Dashboard | Built with Streamlit")
