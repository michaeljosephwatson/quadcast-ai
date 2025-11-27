"""Analytics Page for QuadCast Dashboard"""
import streamlit as st
import pandas as pd
from rds_queries import (get_rds_connection, get_num_episodes_per_podcast,
                         get_topics_per_podcast, get_published_episodes_over_time,
                         get_all_podcasts, get_topics_per_episode_for_podcast,
                         get_topics_frequency_for_podcast,
                         get_speakers_frequency_for_podcast, get_episode_stats_for_podcast)
from athena_queries import get_athena_connection, get_transcript_word_counts_for_podcast
from visualisations import (create_episodes_per_podcast_bar,
                            create_topics_by_podcast_stacked, create_published_episodes_over_time_line,
                            create_topics_frequency_bar, create_speakers_frequency_bar,
                            create_episode_transcript_length_line)
from theme import apply_theme

st.set_page_config("Analytics", "📊", "wide")

# Add logo to sidebar using st.logo (appears at the very top)
st.logo("assets/logo.png")

apply_theme()

# Cache the database connection


@st.cache_resource
def get_connection():
    """Get cached database connection"""
    return get_rds_connection()


# Title
st.title("📊 Analytics")
st.markdown("View insights and statistics about your podcast collection")

# Get connection
conn = get_connection()


# Main content area
st.markdown("### 📈 Overview")

# Tabs for different sections
tab1, tab2 = st.tabs(["Podcasts", "Episodes"])

with tab1:
    st.markdown("#### Podcasts Analytics")

    # Get data
    episodes_per_podcast = get_num_episodes_per_podcast(conn)

    col1, col2, col3, col4, col5 = st.columns(5)

    total_podcasts = len(episodes_per_podcast)
    total_episodes = episodes_per_podcast['episode_count'].sum()
    avg_episodes = episodes_per_podcast['episode_count'].mean()
    max_episodes = episodes_per_podcast['episode_count'].max()
    min_episodes = episodes_per_podcast['episode_count'].min()

    with col1:
        st.metric("Total Podcasts", int(total_podcasts))

    with col2:
        st.metric("Total Episodes", int(total_episodes))

    with col3:
        st.metric("Avg per Podcast", f"{avg_episodes:.1f}")

    with col4:
        st.metric("Most Episodes", int(max_episodes))

    with col5:
        st.metric("Least Episodes", int(min_episodes))

    st.divider()

    # Chart full width
    st.markdown("##### 📈 Episodes per Podcast")
    chart = create_episodes_per_podcast_bar(episodes_per_podcast)
    st.altair_chart(chart, use_container_width=True)

    st.divider()

    # Add the topics stacked chart
    st.markdown("##### 🏷️ Top 3 Topics per Podcast")
    topics_df = get_topics_per_podcast(conn)
    topics_chart = create_topics_by_podcast_stacked(topics_df)
    st.altair_chart(topics_chart, use_container_width=True)

    st.divider()

    # Published episodes over time
    st.markdown("##### 📅 Published Episodes Over Time (Past Month)")
    published_df = get_published_episodes_over_time(conn)
    published_chart = create_published_episodes_over_time_line(
        published_df)
    st.altair_chart(published_chart, use_container_width=True)

with tab2:
    st.markdown("#### Episodes Analytics")

    # Get podcasts for selection
    podcasts_df = get_all_podcasts(conn)

    if podcasts_df.empty:
        st.warning("No podcasts found. Please subscribe to podcasts first!")
    else:
        # Podcast selector
        podcast_names = sorted(podcasts_df['podcast_name'].unique().tolist())
        selected_podcast = st.selectbox(
            "📻 Select a Podcast:",
            options=podcast_names,
            key="episode_analytics_podcast_selector"
        )

        # Get podcast ID for Athena queries
        podcast_id = podcasts_df[podcasts_df['podcast_name']
                                 == selected_podcast]['podcast_id'].iloc[0]

        st.divider()

        # Episode Statistics (KPIs)
        st.markdown("##### 📊 Episode Statistics")
        stats = get_episode_stats_for_podcast(conn, selected_podcast)

        if stats:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Total Episodes",
                    int(stats.get('total_episodes', 0))
                )

            with col2:
                transcribed = int(stats.get('transcribed_episodes', 0))
                st.metric(
                    "Transcribed",
                    transcribed
                )

            with col3:
                untranscribed = int(stats.get('untranscribed_episodes', 0))
                st.metric(
                    "Untranscribed",
                    untranscribed
                )

            with col4:
                avg_speakers = stats.get('avg_speakers_per_episode', 0)
                st.metric(
                    "Avg Speakers/Episode",
                    f"{avg_speakers:.1f}"
                )

            st.divider()

        # Two columns for frequency charts
        col_freq1, col_freq2 = st.columns(2)

        # Topics Frequency
        with col_freq1:
            st.markdown("##### 🏷️ Topic Frequency")
            try:
                topics_freq = get_topics_frequency_for_podcast(
                    conn, selected_podcast)
                if not topics_freq.empty:
                    topics_freq_chart = create_topics_frequency_bar(
                        topics_freq)
                    st.altair_chart(topics_freq_chart,
                                    use_container_width=True)
                else:
                    st.info("No topics available for this podcast")
            except Exception as e:
                st.error(f"Error loading topic frequency: {str(e)}")

        # Speakers Frequency
        with col_freq2:
            st.markdown("##### 🎤 Speaker Frequency")
            try:
                speakers_freq = get_speakers_frequency_for_podcast(
                    conn, selected_podcast)
                if not speakers_freq.empty:
                    speakers_freq_chart = create_speakers_frequency_bar(
                        speakers_freq)
                    st.altair_chart(speakers_freq_chart,
                                    use_container_width=True)
                else:
                    st.info("No speakers available for this podcast")
            except Exception as e:
                st.error(f"Error loading speaker frequency: {str(e)}")

        st.divider()

        # Transcript Length Over Time (from Athena)
        st.markdown("##### 📝 Transcript Length Over Time")
        try:
            athena_client = get_athena_connection()
            word_counts = get_transcript_word_counts_for_podcast(
                athena_client, podcast_id=str(podcast_id))

            # Get episode details for the line chart
            episode_details = get_topics_per_episode_for_podcast(
                conn, selected_podcast)

            if not episode_details.empty and word_counts:
                transcript_chart = create_episode_transcript_length_line(
                    episode_details, word_counts)
                st.altair_chart(transcript_chart, use_container_width=True)
            else:
                st.info("No transcript data available for this podcast yet")
        except Exception as e:
            st.warning(f"Could not load transcript data: {str(e)}")

st.divider()
st.caption("QuadCast Analytics | Built with Streamlit")
