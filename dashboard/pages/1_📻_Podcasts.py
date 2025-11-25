"""QuadCast Dashboard - Podcasts Page"""
import time
import streamlit as st
import pandas as pd
from rds_queries import get_rds_connection, get_all_podcasts, get_episodes_with_podcast_info
from api_calls import add_podcast
from athena_queries import get_athena_connection, get_transcript_for_episode, get_summary_for_episode

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


@st.cache_resource
def get_athena_client():
    """Get cached Athena client connection"""
    return get_athena_connection()

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

# Create main layout with left sidebar, main content, and right sidebar
left_sidebar = st.sidebar
main_col, right_sidebar = st.columns([3, 1])

with left_sidebar:
    st.markdown("## 🎯 Select Content")

    # Add New Podcast Button
    if st.button("🎙️ Add New Podcast", use_container_width=True):
        add_podcast_modal()

    st.markdown("---")

# Get all podcasts
podcasts_df = get_podcasts_data(conn)

if podcasts_df.empty:
    with main_col:
        st.warning("No podcasts found. Please subscribe to podcasts first!")

# Get all episodes
episodes_df = get_episodes_data(conn)

with left_sidebar:
    # Podcasts sorted by upload date
    podcast_names = podcasts_df.sort_values('uploaded_at', ascending=False)[
        'podcast_name'].unique().tolist()

    selected_podcast_name = st.selectbox(
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

with left_sidebar:
    # Add filter for transcribed episodes in sidebar
    st.markdown("---")
    transcript_filter = st.radio(
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

with left_sidebar:
    st.markdown("---")

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

        selected_episode_display = st.selectbox(
            "🎧 Choose an Episode:",
            options=episode_options,
            key="episode_selector"
        )

        selected_episode = episode_map[selected_episode_display]

        # Show count of filtered episodes
        if transcript_filter != "All Episodes":
            st.info(
                f"📊 Showing {len(filtered_episodes)} of {len(podcast_episodes)} episodes")
    else:
        selected_episode = None
        if transcript_filter != "All Episodes":
            st.warning(
                f"⚠️ No episodes match the '{transcript_filter}' filter")
        else:
            st.info("No episodes found for this podcast.")

    st.markdown("---")

# Main content area
with main_col:
    st.title("🎙️ Podcasts")
    st.markdown("Browse and explore your podcast collection")

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

        # Summary Section
        if selected_episode['transcribed']:
            try:
                athena_client = get_athena_client()

                # Get the actual scalar values
                podcast_id_raw = selected_episode['podcast_id']
                episode_id_raw = selected_episode['episode_id']

                # Convert podcast_id (it's a Series) to scalar
                if isinstance(podcast_id_raw, pd.Series):
                    podcast_id = str(podcast_id_raw.iloc[0])
                else:
                    podcast_id = str(podcast_id_raw)

                # Episode ID is already a scalar
                episode_id = str(episode_id_raw)

                with st.spinner("Loading summary..."):
                    summary_data = get_summary_for_episode(
                        athena_client,
                        podcast_id=podcast_id,
                        episode_id=episode_id
                    )

                # Display Episode Summary heading
                st.markdown("#### 📋 Episode Summary")

                # Display summary as simple text
                st.write(summary_data['summary'])

                st.markdown("")

                # Display topics and speakers in a tag-like format
                col1, col2 = st.columns(2)

                with col1:
                    if summary_data['topics']:
                        st.markdown("**🏷️ Topics:**")
                        # Parse topics
                        topics_str = summary_data['topics'].strip(
                            "[]").replace("'", "").replace('"', '')
                        topics_list = [topic.strip()
                                       for topic in topics_str.split(',')]

                        # Create badges for topics with green color
                        for topic in topics_list:
                            st.badge(topic, color="green")

                with col2:
                    if summary_data['speakers']:
                        st.markdown("**🎤 Speakers:**")
                        # Parse speakers
                        speakers_str = summary_data['speakers'].strip(
                            "[]").replace("'", "").replace('"', '')
                        speakers_list = [speaker.strip()
                                         for speaker in speakers_str.split(',')]

                        # Create badges for speakers with blue color
                        for speaker in speakers_list:
                            st.badge(speaker, color="blue")

            except ValueError as e:
                pass  # Silently skip if no summary available
            except Exception as e:
                st.error(f"❌ Error loading summary: {str(e)}")

        # Episode metadata
        col1, col2 = st.columns(2)

        with col1:
            if 'published_at' in selected_episode and pd.notna(selected_episode['published_at']):
                st.markdown(
                    f"**📅 Published:** "
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

        # Transcript Section
        if selected_episode['transcribed']:
            st.markdown("---")
            st.markdown("#### 📝 Transcript")

            try:
                athena_client = get_athena_client()

                # Get the actual scalar values
                podcast_id_raw = selected_episode['podcast_id']
                episode_id_raw = selected_episode['episode_id']

                # Convert podcast_id (it's a Series) to scalar
                if isinstance(podcast_id_raw, pd.Series):
                    podcast_id = str(podcast_id_raw.iloc[0])
                else:
                    podcast_id = str(podcast_id_raw)

                # Episode ID is already a scalar
                episode_id = str(episode_id_raw)

                with st.spinner("Loading transcript..."):
                    transcript = get_transcript_for_episode(
                        athena_client,
                        podcast_id=podcast_id,
                        episode_id=episode_id
                    )

                # Display transcript in a nice scrollable container
                st.markdown(
                    f"""
                    <div style="
                        background-color: #1e1e1e;
                        padding: 25px;
                        border-radius: 10px;
                        max-height: 500px;
                        overflow-y: auto;
                        border-left: 4px solid #667eea;
                        font-family: 'Georgia', serif;
                        line-height: 1.8;
                        color: #e0e0e0;
                    ">
                        <p style="margin: 0; white-space: pre-wrap; word-wrap: break-word;">
                            {transcript}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            except ValueError as e:
                st.warning(f"⚠️ {str(e)}")
            except Exception as e:
                st.error(f"❌ Error loading transcript: {str(e)}")

    else:
        st.info(
            "No episodes found for this podcast or no episodes match the current filter.")

    st.divider()
    st.caption("QuadCast Dashboard | Built with Streamlit")

# Right sidebar for chatbot
with right_sidebar:
    st.subheader("💬 Chat")

    # Chat input
    prompt = st.chat_input("Ask about this episode...")

    if prompt:
        st.chat_message("user").write(prompt)
        st.chat_message("assistant").write("🤖 Chatbot coming soon!")
