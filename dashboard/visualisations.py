"""Script for creating visualisations for the QuadCast Dashboard"""
import altair as alt
import pandas as pd


def create_episodes_per_podcast_bar(df: pd.DataFrame):
    """Create bar chart for episodes per podcast using Altair"""
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('podcast_name:N',
                title='Podcast Name',
                axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('episode_count:Q',
                title='Number of Episodes'),
        color=alt.Color('episode_count:Q',
                        scale=alt.Scale(scheme='teals'),
                        legend=None),
        tooltip=[
            alt.Tooltip('podcast_name:N', title='Podcast'),
            alt.Tooltip('episode_count:Q', title='Episodes')
        ]
    ).properties(
        title='Episodes per Podcast',
        width=600,
        height=400
    ).configure_mark(
        opacity=0.9
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        fontSize=16,
        anchor='start'
    )

    return chart


def create_topics_by_podcast_stacked(df: pd.DataFrame):
    """Create stacked bar chart for top 3 topics per podcast"""
    # Get top 3 topics per podcast
    top_topics_df = (
        df.sort_values(['podcast_name', 'episode_count'],
                       ascending=[True, False])
        .groupby('podcast_name', as_index=False).head(3)
    )

    # Get all unique topics and sort them for consistent coloring
    all_topics = sorted(top_topics_df['topic_name'].unique())

    # Base bar chart
    bars = alt.Chart(top_topics_df).mark_bar().encode(
        x=alt.X('podcast_name:N',
                title='Podcast',
                axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('episode_count:Q',
                title='Number of Episodes for specific Topics',
                stack='zero'),
        color=alt.Color('topic_name:N',
                        title='Topic',
                        scale=alt.Scale(
                            domain=all_topics,  # Ensures overlapping topics have same color
                            scheme='tableau20'
                        ),
                        sort=all_topics),
        tooltip=[
            alt.Tooltip('podcast_name:N', title='Podcast'),
            alt.Tooltip('topic_name:N', title='Topic'),
            alt.Tooltip('episode_count:Q', title='Episodes')
        ]
    )

    chart = bars.properties(
        title='Top 3 Topics per Podcast',
        width=800,
        height=500
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        fontSize=16,
        anchor='start'
    ).configure_legend(
        titleFontSize=12,
        labelFontSize=11
    )

    return chart


def create_published_episodes_over_time_line(df: pd.DataFrame):
    """Create line chart for published episodes for all podcasts in the past month"""
    # Filter to only past month
    one_month_ago = pd.Timestamp.now() - pd.DateOffset(months=1)
    df['published_at'] = pd.to_datetime(df['published_at'])
    recent_df = df[df['published_at'] >= one_month_ago].copy()
    if recent_df.empty:
        # Return a message chart if no episodes in the past month
        return alt.Chart(pd.DataFrame({'message': ['No episodes published in the past month']})).mark_text(
            text='No episodes published in the past month',
            size=16
        ).encode()
    recent_df = recent_df.sort_values('published_at')

    # Calculate cumulative episodes per podcast
    recent_df['cumulative_episodes'] = recent_df.groupby(
        'podcast_name').cumcount() + 1

    chart = alt.Chart(recent_df).mark_line(point=True, strokeWidth=2).encode(
        x=alt.X('published_at:T',
                title='Published Date',
                axis=alt.Axis(
                    format='%b %d',
                    labelAngle=-45,
                    tickCount='week'
                )),
        y=alt.Y('cumulative_episodes:Q',
                title='Cumulative Episodes Published',
                scale=alt.Scale(zero=True)),
        color=alt.Color('podcast_name:N',
                        title='Podcast',
                        scale=alt.Scale(scheme='category10')),
        tooltip=[
            alt.Tooltip('podcast_name:N', title='Podcast'),
            alt.Tooltip('published_at:T', title='Published',
                        format='%b %d, %Y'),
            alt.Tooltip('cumulative_episodes:Q', title='Total Episodes')
        ]
    ).properties(
        title='Published Episodes Over Time (Past Month)',
        width=700,
        height=400
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        fontSize=16,
        anchor='start'
    ).configure_legend(
        titleFontSize=12,
        labelFontSize=11
    )

    return chart


def create_topics_frequency_bar(df: pd.DataFrame):
    """Create horizontal bar chart for topic frequency (top 5)"""
    # Limit to top 5
    top_df = df.head(5)

    chart = alt.Chart(top_df).mark_bar().encode(
        y=alt.Y('topic_name:N',
                title='Topic',
                sort='-x'),
        x=alt.X('episode_count:Q',
                title='Episodes'),
        color=alt.Color('episode_count:Q',
                        scale=alt.Scale(scheme='blues'),
                        legend=None),
        tooltip=[
            alt.Tooltip('topic_name:N', title='Topic'),
            alt.Tooltip('episode_count:Q', title='Episodes')
        ]
    ).properties(
        title='Top 5 Topics',
        width=700,
        height=300
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        fontSize=16,
        anchor='start'
    )

    return chart


def create_speakers_frequency_bar(df: pd.DataFrame):
    """Create horizontal bar chart for speaker frequency (top 5)"""
    # Limit to top 5
    top_df = df.head(5)

    chart = alt.Chart(top_df).mark_bar().encode(
        y=alt.Y('speaker_name:N',
                title='Speaker',
                sort='-x'),
        x=alt.X('episode_count:Q',
                title='Episodes'),
        color=alt.Color('episode_count:Q',
                        scale=alt.Scale(scheme='oranges'),
                        legend=None),
        tooltip=[
            alt.Tooltip('speaker_name:N', title='Speaker'),
            alt.Tooltip('episode_count:Q', title='Episodes')
        ]
    ).properties(
        title='Top 5 Speakers',
        width=700,
        height=300
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        fontSize=16,
        anchor='start'
    )

    return chart


def create_episode_transcript_length_line(df: pd.DataFrame, word_counts_dict: dict):
    """Create line chart showing transcript word count per episode over time"""
    df['published_at'] = pd.to_datetime(df['published_at'])
    df = df.sort_values('published_at')

    # Add word counts to dataframe
    df['word_count'] = df['episode_id'].astype(str).map(word_counts_dict)
    df = df.dropna(subset=['word_count'])

    if df.empty:
        return alt.Chart(pd.DataFrame({'message': ['No transcript data available']})).mark_text(
            text='No transcript data available',
            size=14
        ).encode()

    chart = alt.Chart(df).mark_line(point=True, strokeWidth=2).encode(
        x=alt.X('published_at:T',
                title='Published Date',
                axis=alt.Axis(format='%b %d, %Y', labelAngle=-45)),
        y=alt.Y('word_count:Q',
                title='Transcript Word Count',
                scale=alt.Scale(zero=False)),
        color=alt.value('#2ca02c'),
        tooltip=[
            alt.Tooltip('episode_title:N', title='Episode'),
            alt.Tooltip('published_at:T', title='Published', format='%b %d, %Y'),
            alt.Tooltip('word_count:Q', title='Words', format=',')
        ]
    ).properties(
        title='Transcript Length Over Time',
        width=800,
        height=400
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        fontSize=16,
        anchor='start'
    )

    return chart
