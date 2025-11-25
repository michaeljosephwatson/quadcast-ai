"""QuadCast Dashboard - Vector Search Page"""
import streamlit as st
import pandas as pd
from rds_queries import get_rds_connection
from search_queries import search_episodes_by_embedding

# Page configuration
st.set_page_config(
    page_title="Search - QuadCast",
    page_icon="🔍",
    layout="wide"
)


@st.cache_resource
def get_connection():
    """Get cached database connection"""
    return get_rds_connection()


st.title("🔍 Semantic Search")
st.markdown("Search across podcast content using AI-powered semantic search")

st.divider()

# Search input
search_query = st.text_input(
    "Enter your search query",
    placeholder="e.g., 'machine learning applications' or 'climate change solutions'",
    label_visibility="collapsed"
)

# Search parameters
col1, col2 = st.columns(2)

with col1:
    num_results = st.slider(
        "Number of results",
        min_value=1,
        max_value=20,
        value=5
    )

with col2:
    similarity_threshold = st.slider(
        "Minimum similarity",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05
    )

st.divider()

# Perform search when query is entered
if search_query:
    conn = get_connection()

    with st.spinner("Searching..."):
        try:
            results = search_episodes_by_embedding(
                conn,
                query=search_query,
                limit=num_results,
                similarity_threshold=similarity_threshold
            )

            if results.empty:
                st.info("No relevant results found. Try adjusting your search query or similarity threshold.")
            else:
                st.success(f"Found {len(results)} relevant results")
                st.divider()

                # Display results
                for idx, row in results.iterrows():
                    with st.container(border=True):
                        # Header with podcast and episode info
                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.markdown(f"### 🎙️ {row['podcast_name']}")
                            st.markdown(f"**Episode:** {row['episode_title']}")

                        with col2:
                            similarity_pct = (row['similarity'] * 100)
                            st.metric(
                                "Match",
                                f"{similarity_pct:.1f}%"
                            )

                        st.divider()

                        # Chunk text with highlight
                        st.markdown("**Relevant excerpt:**")
                        st.markdown(
                            f"""
                            <div style="
                                background-color: #f0f2f6;
                                padding: 15px;
                                border-radius: 5px;
                                border-left: 4px solid #667eea;
                                font-style: italic;
                                line-height: 1.6;
                            ">
                                {row['chunk_text']}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # Metadata
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            if pd.notna(row['published_at']):
                                published_date = pd.to_datetime(row['published_at']).strftime('%B %d, %Y')
                                st.caption(f"📅 {published_date}")

                        with col2:
                            st.caption(f"📍 Chunk {int(row['chunk_index'])}")

                        with col3:
                            st.caption(f"🏷️ Episode {int(row['episode_id'])}")

        except Exception as e:
            st.error(f"Error performing search: {str(e)}")

st.divider()
st.caption("QuadCast Search | Built with Streamlit")
