"""QuadCast Dashboard - Vector Search Page"""
import streamlit as st
import pandas as pd
import re
from rds_queries import get_rds_connection, get_all_podcasts
from search_queries import search_episodes_by_embedding
from theme import apply_theme

st.set_page_config("Semantic Search", "🔍", "wide")

# Add logo to sidebar using st.logo (appears at the very top)
st.logo("assets/logo.png")


apply_theme()


@st.cache_resource
def get_connection():
    """Get cached database connection"""
    return get_rds_connection()


st.title("🔍 Semantic Search")
st.markdown("Search across podcast content using AI-powered semantic search")

st.divider()

# Search input - bigger and more prominent
st.markdown("### 🔎 What would you like to find?")
search_query = st.text_input(
    "Search",
    placeholder="e.g., 'machine learning applications' or 'climate change solutions'",
    label_visibility="collapsed",
    key="search_input"
)

# Custom CSS to make search input bigger
st.markdown("""
<style>
    input[type="text"] {
        font-size: 18px !important;
        padding: 12px !important;
        height: 50px !important;
    }
</style>
""", unsafe_allow_html=True)

# Get podcasts for filtering
conn = get_connection()
all_podcasts = get_all_podcasts(conn)
podcast_names = sorted(all_podcasts['podcast_name'].unique().tolist())

# Search parameters
st.markdown("### ⚙️ Search Settings")
col1, col2, col3, col4 = st.columns(4)

with col1:
    num_results = st.slider(
        "Number of results",
        min_value=1,
        max_value=20,
        value=5,
        key="num_results"
    )

with col2:
    similarity_threshold = st.slider(
        "Minimum similarity",
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.05,
        key="similarity_threshold"
    )

with col3:
    one_per_episode = st.checkbox(
        "One per episode",
        value=False,
        help="Show only the best match from each episode",
        key="one_per_episode"
    )

with col4:
    sort_by = st.selectbox(
        "Sort by",
        options=["Similarity (highest first)", "Date (newest first)",
                 "Date (oldest first)", "Chunk order"],
        key="sort_by"
    )

# Podcast filter
st.markdown("### 🎙️ Podcast Filter")
selected_podcasts = st.multiselect(
    "Select podcasts to search",
    options=podcast_names,
    default=podcast_names,
    key="podcast_filter"
)

# Search tips
with st.expander("💡 Search Tips", expanded=False):
    st.markdown("""
    **Tips for better search results:**
    - Use **specific keywords** rather than vague terms (e.g., "machine learning algorithms" vs "tech")
    - Try **phrases** to find exact topics (e.g., "climate change solutions")
    - Use **synonyms** if you don't find what you're looking for
    - Combine **multiple keywords** to narrow down results (e.g., "artificial intelligence business applications")
    - Lower the **similarity threshold** if you're getting too few results
    - Check the **match percentage** to see how relevant each result is
    """)

st.divider()

# Perform search when query is entered
if search_query:
    with st.spinner("Searching..."):
        try:
            results = search_episodes_by_embedding(
                conn,
                query=search_query,
                limit=num_results,
                similarity_threshold=similarity_threshold
            )

            if results.empty:
                st.info(
                    "No relevant results found. Try adjusting your search query or similarity threshold.")
            else:
                # Filter by selected podcasts
                results = results[results['podcast_name'].isin(
                    selected_podcasts)]

                if results.empty:
                    st.info("No results found in the selected podcasts.")
                else:
                    st.success(f"Found {len(results)} relevant results")
                    st.divider()

                    # Apply one per episode filter if enabled
                    display_results = results.copy()
                    if one_per_episode:
                        # Keep only the highest similarity result per episode
                        display_results = results.loc[results.groupby(
                            'episode_id')['similarity'].idxmax()]

                    # Apply sorting
                    if sort_by == "Similarity (highest first)":
                        display_results = display_results.sort_values(
                            'similarity', ascending=False)
                    elif sort_by == "Date (newest first)":
                        display_results = display_results.sort_values(
                            'published_at', ascending=False, na_position='last')
                    elif sort_by == "Date (oldest first)":
                        display_results = display_results.sort_values(
                            'published_at', ascending=True, na_position='last')
                    elif sort_by == "Chunk order":
                        display_results = display_results.sort_values(
                            ['episode_id', 'chunk_index'], ascending=True)

                # Filter results by episode
                unique_episodes = display_results[[
                    'episode_id', 'episode_title', 'podcast_name']].drop_duplicates().sort_values('episode_title')
                episode_options = [
                    f"{row['podcast_name']} - {row['episode_title']}" for _, row in unique_episodes.iterrows()]

                st.markdown("### Filter by Episode")
                selected_episodes = st.multiselect(
                    "Select episodes to display",
                    options=episode_options,
                    default=episode_options,
                    key="episode_filter"
                )

                # Filter results based on selected episodes
                filtered_results = display_results.copy()
                if selected_episodes:
                    # Extract episode titles from selected options
                    selected_titles = [opt.split(" - ", 1)[1]
                                       for opt in selected_episodes]
                    filtered_results = display_results[display_results['episode_title'].isin(
                        selected_titles)]

                st.divider()
                results_text = f"**Showing {len(filtered_results)} of {len(display_results)} results"
                if one_per_episode:
                    results_text += f" (from {len(results)} total matches)**"
                else:
                    results_text += "**"
                st.markdown(results_text)
                st.divider()

                # Helper function to highlight keywords in text
                def highlight_keywords(text, query):
                    """Highlight search query keywords in the text"""
                    # Split query into individual words and filter out common words
                    keywords = [word for word in query.lower().split()
                                if len(word) > 2]

                    highlighted_text = text
                    for keyword in keywords:
                        # Use case-insensitive regex to find and highlight
                        pattern = re.compile(
                            f'({re.escape(keyword)})', re.IGNORECASE)
                        highlighted_text = pattern.sub(
                            r'<mark style="background-color: #FFFF00; padding: 2px 4px; border-radius: 3px;">\1</mark>', highlighted_text)

                    return highlighted_text

                # Display results
                for result_idx, (idx, row) in enumerate(filtered_results.iterrows(), 1):
                    similarity_pct = (row['similarity'] * 100)

                    # Color coding for similarity
                    if similarity_pct >= 40:
                        color = "#10b981"  # Green
                    elif similarity_pct >= 20:
                        color = "#f59e0b"  # Amber
                    else:
                        color = "#ef4444"  # Red

                    # Collapsible result
                    with st.expander(
                        f"🎙️ {row['podcast_name']} - {row['episode_title'][:50]}... ({similarity_pct:.1f}%)",
                        expanded=False
                    ):
                        # Header with podcast and episode info
                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.markdown(f"### 🎙️ {row['podcast_name']}")
                            st.markdown(f"**Episode:** {row['episode_title']}")

                        with col2:
                            # Visual similarity score with progress bar
                            st.markdown(f"**Match Score**")
                            st.markdown(
                                f"""
                                <div style="
                                    background-color: #e5e7eb;
                                    height: 24px;
                                    border-radius: 4px;
                                    overflow: hidden;
                                ">
                                    <div style="
                                        background-color: {color};
                                        height: 100%;
                                        width: {similarity_pct}%;
                                        display: flex;
                                        align-items: center;
                                        justify-content: center;
                                        color: white;
                                        font-weight: bold;
                                        font-size: 12px;
                                    ">
                                        {similarity_pct:.1f}%
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        st.divider()

                        # Chunk text with highlighted keywords
                        st.markdown("**Relevant excerpt:**")
                        highlighted_chunk = highlight_keywords(
                            row['chunk_text'], search_query)
                        st.markdown(
                            f"""
                            <div style="
                                background-color: #ffffff;
                                color: #1a1a1a;
                                padding: 20px;
                                border-radius: 8px;
                                border-left: 5px solid {color};
                                font-size: 16px;
                                line-height: 1.8;
                                word-wrap: break-word;
                                white-space: normal;
                                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            ">
                                {highlighted_chunk}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # Metadata and action buttons
                        col1, col2, col3 = st.columns([2, 1, 1])

                        with col1:
                            if pd.notna(row['published_at']):
                                published_date = pd.to_datetime(
                                    row['published_at']).strftime('%B %d, %Y')
                                st.caption(f"📅 {published_date}")

                        with col2:
                            pass

                        with col3:
                            if st.button("🔗 View in Podcasts", key=f"view_podcast_{result_idx}"):
                                st.session_state.selected_podcast_name = row['podcast_name']
                                st.session_state.selected_episode_title = row['episode_title']
                                st.switch_page("pages/1_📻_Podcasts.py")

        except Exception as e:
            st.error(f"Error performing search: {str(e)}")

st.divider()
st.caption("QuadCast Search | Built with Streamlit")
