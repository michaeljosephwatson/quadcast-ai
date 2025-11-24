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
    top_topics_df = df.groupby('podcast_name').apply(
        lambda x: x.nlargest(3, 'episode_count')
    ).reset_index(drop=True)

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

    # Text labels
    text = alt.Chart(top_topics_df).mark_text(
        color='white',
        fontWeight='bold',
        fontSize=12,
        baseline='middle'
    ).encode(
        x=alt.X('podcast_name:N'),
        y=alt.Y('episode_count:Q',
                stack='zero',
                bandPosition=0.5)
    )

    chart = (bars + text).properties(
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


if __name__ == "__main__":
    ...
