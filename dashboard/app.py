"""QuadCast Dashboard Application Homepage"""
import streamlit as st
from rds_queries import (get_rds_connection, get_number_of_podcasts,
                         get_number_of_episodes, get_number_of_transcripts)

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

# Cache the metrics (refresh every 60 seconds)


@st.cache_data(ttl=60)
def get_metrics(_conn) -> dict:
    """Get platform metrics with caching"""
    return {
        'podcasts': get_number_of_podcasts(_conn),
        'episodes': get_number_of_episodes(_conn),
        'transcripts': get_number_of_transcripts(_conn)
    }


# Get connection and metrics
conn = get_connection()
metrics = get_metrics(conn)

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
