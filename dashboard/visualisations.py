"""Script for creating visualisations for the QuadCast Dashboard"""
import altair as alt
import pandas as pd
from rds_queries import get_rds_connection, get_num_episodes_per_podcast


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


if __name__ == "__main__":
    # For quick testing
    conn = get_rds_connection()
    df = get_num_episodes_per_podcast(conn)
    chart = create_episodes_per_podcast_bar(df)
    chart.save('test_chart.html')
