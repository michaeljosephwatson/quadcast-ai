"""QuadCast Dashboard - Podcasts Page"""
import time
import streamlit as st
import pandas as pd
from rds_queries import get_rds_connection, get_all_podcasts, get_episodes_with_podcast_info
from api_calls import add_podcast

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

# Modal dialog for adding a new podcast


@st.dialog("Add New Podcast")
def add_podcast_modal() -> None:
    """Modal dialog for adding a new podcast"""
    st.write("Enter the RSS feed URL of the podcast you want to add:")

    rss_url = st.text_input(
        "RSS Feed URL",
        placeholder="https://audioboom.com/channels/2399216.rss",
        label_visibility="collapsed"
    )

    col1, col2 = st.columns(2)

    add_button = col1.button("Add Podcast", use_container_width=True)
    cancel_button = col2.button("Cancel", use_container_width=True)

    if cancel_button:
        st.rerun()

    if add_button:
        with st.spinner("Adding podcast..."):
            response = add_podcast(rss_url)

            # Handle non-200 responses
            if response.status_code != 200:
                st.error(
                    f"❌ Failed to add podcast (Status: {response.status_code} {response.text})")
                return

            # Success case
            st.success("✅ Podcast added successfully!")
            st.cache_data.clear()
            time.sleep(0.5)
            st.rerun()


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

# Add New Podcast Button
if st.sidebar.button("🎙️ Add New Podcast", use_container_width=True):
    add_podcast_modal()

st.sidebar.markdown("---")

# Podcasts sorted by upload date
podcast_names = podcasts_df.sort_values('uploaded_at', ascending=False)[
    'podcast_name'].unique().tolist()

selected_podcast_name = st.sidebar.selectbox(
    "📻 Choose a Podcast:",
    options=podcast_names,
    key="podcast_selector"
)

# Filter episodes for selected podcast
podcast_episodes = episodes_df[episodes_df['podcast_name']
                               == selected_podcast_name].copy()

# Sort episodes by published date (newest first)
if 'published_at' in podcast_episodes.columns:
    podcast_episodes = podcast_episodes.sort_values(
        'published_at', ascending=True)

# Add filter for transcribed episodes in sidebar
st.sidebar.markdown("---")
transcript_filter = st.sidebar.radio(
    "📝 Filter by Transcript:",
    options=["All Episodes", "With Transcript", "Without Transcript"],
    key="transcript_filter"
)

# Apply transcript filter
filtered_episodes = podcast_episodes.copy()
if transcript_filter == "With Transcript":
    filtered_episodes = filtered_episodes[filtered_episodes['transcribed']]
elif transcript_filter == "Without Transcript":
    filtered_episodes = filtered_episodes[~filtered_episodes['transcribed']]

st.sidebar.markdown("---")

# Episode selector in sidebar - now with filtered episodes
if not filtered_episodes.empty:
    # Create episode display names (title + date)
    episode_options = []
    episode_map = {}

    for idx, episode in filtered_episodes.iterrows():
        title = episode['episode_title'] if pd.notna(
            episode['episode_title']) else "Untitled Episode"
        if 'published_at' in episode and pd.notna(episode['published_at']):
            date_str = pd.to_datetime(
                episode['published_at']).strftime('%Y-%m-%d')
            display_name = f"{title} ({date_str})"
        else:
            display_name = title

        episode_options.append(display_name)
        episode_map[display_name] = episode

    selected_episode_display = st.sidebar.selectbox(
        "🎧 Choose an Episode:",
        options=episode_options,
        key="episode_selector"
    )

    selected_episode = episode_map[selected_episode_display]

    # Show count of filtered episodes
    if transcript_filter != "All Episodes":
        st.sidebar.info(
            f"📊 Showing {len(filtered_episodes)} of {len(podcast_episodes)} episodes")
else:
    selected_episode = None
    if transcript_filter != "All Episodes":
        st.sidebar.warning(
            f"⚠️ No episodes match the '{transcript_filter}' filter")
    else:
        st.sidebar.info("No episodes found for this podcast.")

st.sidebar.markdown("---")

st.divider()

# Get selected podcast details
selected_podcast = podcasts_df[podcasts_df['podcast_name']
                               == selected_podcast_name].iloc[0]

# Podcast Details Section
st.subheader(f"📻 {selected_podcast_name}")

col1, col2 = st.columns(2)

with col1:
    st.metric("Total Episodes", len(podcast_episodes))

with col2:
    transcripts_count = len(
        podcast_episodes[podcast_episodes['transcribed']])
    st.metric("Transcripts Available", transcripts_count)


st.divider()

# Selected Episode Details
if selected_episode is not None:
    st.subheader("🎧 Episode Details")

    episode_title = selected_episode['episode_title'] if pd.notna(
        selected_episode['episode_title']) else "Untitled Episode"
    st.markdown(f"### {episode_title}")

    # Episode metadata
    col1, col2 = st.columns(2)

    with col1:
        if 'published_at' in selected_episode and pd.notna(selected_episode['published_at']):
            st.markdown(
                f"**📅 Published: **"
                f"{pd.to_datetime(selected_episode['published_at']).strftime('%B %d, %Y')}")

    with col2:
        if selected_episode['transcribed']:
            st.markdown("**✅ Transcript Available**")
        else:
            st.markdown("**⏳ No Transcript**")

    # Episode description
    if 'description' in selected_episode and pd.notna(selected_episode['description']):
        st.markdown("#### Description")
        st.write(selected_episode['description'])

    # Audio link
    if 'audio_url' in selected_episode and pd.notna(selected_episode['audio_url']):
        st.markdown("#### 🎵 Listen Now")
        try:
            st.audio(selected_episode['audio_url'])
        except Exception as e:
            st.error(f"Unable to load audio player: {e}")
            st.markdown(
                f"**🔗 [Direct Audio Link]({selected_episode['audio_url']})**")

else:
    st.info(
        "No episodes found for this podcast or no episodes match the current filter.")

st.divider()
st.caption("QuadCast Dashboard | Built with Streamlit")
