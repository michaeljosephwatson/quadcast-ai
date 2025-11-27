"""QuadCast Dashboard Application Homepage"""
import base64
import streamlit as st
from rds_queries import (
    get_rds_connection, get_all_podcasts, get_all_episodes)

# Page configuration
st.set_page_config(
    page_title="QuadCast Homepage",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add logo to sidebar using st.logo (appears at the very top)
st.logo("assets/logo.png")

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

# Header with logo using HTML for better alignment
with open("assets/logo.png", "rb") as f:
    logo_data = base64.b64encode(f.read()).decode()

st.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 0px;">
        <img src="data:image/png;base64,{logo_data}" style="width: 70px; height: 70px;">
        <h1 style="margin: 0; padding: 0;">QuadCast Dashboard</h1>
    </div>
    """,
    unsafe_allow_html=True
)

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
