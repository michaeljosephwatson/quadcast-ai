"""Analytics Page for QuadCast Dashboard"""
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Analytics - QuadCast",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Analytics")
st.markdown("View insights and statistics about your podcast collection")

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
    st.markdown("#### Podcasts Section")

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
