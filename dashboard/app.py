import streamlit as st
import os

# Page configuration
st.set_page_config(
    page_title="QuadCast Homepage",
    page_icon="🎙️",
    layout="wide"
)

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
        value="0",
        delta="Coming soon"
    )

with col2:
    st.metric(
        label="Episodes Analyzed",
        value="0",
        delta="Coming soon"
    )

with col3:
    st.metric(
        label="Transcripts Generated",
        value="0",
        delta="Coming soon"
    )

# Footer
st.divider()
st.caption("QuadCast Dashboard | Built with Streamlit")
