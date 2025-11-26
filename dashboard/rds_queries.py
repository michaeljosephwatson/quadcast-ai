"""Module for RDS database queries"""
import os
import pandas as pd
from psycopg2 import connect
from psycopg2.extensions import connection
from dotenv import load_dotenv

load_dotenv()  # .env for local development, ignored in production


def get_rds_connection() -> connection:
    """Returns the connection to the RDS database"""
    conn = connect(
        host=os.getenv("RDS_HOST"),
        database=os.getenv("RDS_DB_NAME"),
        user=os.getenv("RDS_USERNAME"),
        password=os.getenv("RDS_PASSWORD")
    )
    return conn


def get_all_podcasts(conn: connection) -> pd.DataFrame:
    """Returns all podcasts as a DataFrame"""
    query = "SELECT * FROM podcast;"
    return pd.read_sql(query, conn)


def get_all_episodes(conn: connection) -> pd.DataFrame:
    """Returns all episodes as a DataFrame"""
    query = "SELECT * FROM episode;"
    return pd.read_sql(query, conn)


def get_episodes_with_podcast_info(conn: connection) -> pd.DataFrame:
    """Returns all episodes joined with their podcast information"""
    query = """
        SELECT *
        FROM episode e
        JOIN podcast p ON e.podcast_id = p.podcast_id;
    """
    return pd.read_sql(query, conn)


def get_number_of_podcasts(conn: connection) -> int:
    """Returns the total number of podcasts in the database"""
    df = get_all_podcasts(conn)
    return len(df)


def get_number_of_episodes(conn: connection, podcast_name=None) -> int:
    """Returns the total number of episodes in the database or for a specific podcast"""
    if not podcast_name:
        df = get_all_episodes(conn)
        return len(df)
    else:
        df = get_episodes_with_podcast_info(conn)
        return len(df[df['podcast_name'] == podcast_name])


def get_number_of_transcripts(conn: connection, podcast_name=None) -> int:
    """Returns the total number of transcripts in the database or for a specific podcast"""
    if not podcast_name:
        df = get_all_episodes(conn)
        return len(df[df['transcribed'] == True])
    else:
        df = get_episodes_with_podcast_info(conn)
        return len(df[(df['podcast_name'] == podcast_name) & (df['transcribed'] == True)])


def get_num_episodes_per_podcast(conn: connection) -> pd.DataFrame:
    """Returns a DataFrame with the number of episodes per podcast"""
    query = """
        SELECT p.podcast_name, COUNT(e.episode_id) AS episode_count
        FROM podcast p
        LEFT JOIN episode e ON p.podcast_id = e.podcast_id
        GROUP BY p.podcast_name;
    """
    return pd.read_sql(query, conn)


def get_topics_per_podcast(conn: connection) -> pd.DataFrame:
    """Get topics and their frequency per podcast"""
    query = """
        SELECT 
            p.podcast_name,
            INITCAP(LOWER(t.topic_name)) as topic_name,
            COUNT(DISTINCT e.episode_id) as episode_count
        FROM podcast p
        JOIN episode e ON p.podcast_id = e.podcast_id
        JOIN episode_topics et ON e.episode_id = et.episode_id
        JOIN topics t ON et.topic_id = t.topic_id
        GROUP BY p.podcast_name, INITCAP(LOWER(t.topic_name))
        ORDER BY p.podcast_name, episode_count DESC;
    """
    return pd.read_sql(query, conn)


def get_published_episodes_over_time(conn: connection) -> pd.DataFrame:
    """Get published episodes over time"""
    query = """
        SELECT
            p.podcast_name,
            e.published_at,
            e.episode_title
        FROM podcast p
        JOIN episode e ON p.podcast_id = e.podcast_id
        WHERE e.published_at IS NOT NULL
        ORDER BY p.podcast_name, e.published_at;
    """
    return pd.read_sql(query, conn)


def get_topics_per_episode_for_podcast(conn: connection, podcast_name: str) -> pd.DataFrame:
    """Get number of topics per episode for a specific podcast"""
    query = """
        SELECT
            e.episode_id,
            e.episode_title,
            e.published_at,
            e.transcribed,
            COUNT(DISTINCT et.topic_id) as topic_count
        FROM episode e
        JOIN podcast p ON e.podcast_id = p.podcast_id
        LEFT JOIN episode_topics et ON e.episode_id = et.episode_id
        WHERE p.podcast_name = %s
        GROUP BY e.episode_id, e.episode_title, e.published_at, e.transcribed
        ORDER BY e.published_at DESC;
    """
    return pd.read_sql(query, conn, params=[podcast_name])


def get_episode_details_for_podcast(conn: connection, podcast_name: str) -> pd.DataFrame:
    """Get detailed information about episodes for a specific podcast"""
    query = """
        SELECT
            e.episode_id,
            e.episode_title,
            e.published_at,
            e.transcribed,
            e.uploaded_at,
            COUNT(DISTINCT et.topic_id) as topic_count,
            COUNT(DISTINCT es.speaker_id) as speaker_count
        FROM episode e
        JOIN podcast p ON e.podcast_id = p.podcast_id
        LEFT JOIN episode_topics et ON e.episode_id = et.episode_id
        LEFT JOIN episode_speakers es ON e.episode_id = es.episode_id
        WHERE p.podcast_name = %s
        GROUP BY e.episode_id, e.episode_title, e.published_at, e.transcribed, e.uploaded_at
        ORDER BY e.published_at DESC;
    """
    return pd.read_sql(query, conn, params=[podcast_name])


def get_topics_frequency_for_podcast(conn: connection, podcast_name: str) -> pd.DataFrame:
    """Get topic frequency (how many episodes each topic appears in) for a specific podcast"""
    query = """
        SELECT
            INITCAP(LOWER(t.topic_name)) as topic_name,
            COUNT(DISTINCT e.episode_id) as episode_count
        FROM topics t
        JOIN episode_topics et ON t.topic_id = et.topic_id
        JOIN episode e ON et.episode_id = e.episode_id
        JOIN podcast p ON e.podcast_id = p.podcast_id
        WHERE p.podcast_name = %s
        GROUP BY INITCAP(LOWER(t.topic_name))
        ORDER BY episode_count DESC;
    """
    return pd.read_sql(query, conn, params=[podcast_name])


def get_speakers_frequency_for_podcast(conn: connection, podcast_name: str) -> pd.DataFrame:
    """Get speaker frequency (how many episodes each speaker appears in) for a specific podcast"""
    query = """
        SELECT
            s.speaker_name,
            COUNT(DISTINCT e.episode_id) as episode_count
        FROM speakers s
        JOIN episode_speakers es ON s.speaker_id = es.speaker_id
        JOIN episode e ON es.episode_id = e.episode_id
        JOIN podcast p ON e.podcast_id = p.podcast_id
        WHERE p.podcast_name = %s
        GROUP BY s.speaker_name
        ORDER BY episode_count DESC;
    """
    return pd.read_sql(query, conn, params=[podcast_name])


def get_episode_stats_for_podcast(conn: connection, podcast_name: str) -> dict:
    """Get summary statistics for episodes in a specific podcast"""
    query = """
        SELECT
            COUNT(DISTINCT episode_id) as total_episodes,
            COUNT(DISTINCT CASE WHEN transcribed = TRUE THEN episode_id END) as transcribed_episodes,
            COUNT(DISTINCT CASE WHEN transcribed = FALSE THEN episode_id END) as untranscribed_episodes,
            AVG(topic_count) as avg_topics_per_episode,
            AVG(speaker_count) as avg_speakers_per_episode
        FROM (
            SELECT
                e.episode_id,
                e.transcribed,
                COUNT(DISTINCT et.topic_id) as topic_count,
                COUNT(DISTINCT es.speaker_id) as speaker_count
            FROM episode e
            JOIN podcast p ON e.podcast_id = p.podcast_id
            LEFT JOIN episode_topics et ON e.episode_id = et.episode_id
            LEFT JOIN episode_speakers es ON e.episode_id = es.episode_id
            WHERE p.podcast_name = %s
            GROUP BY e.episode_id, e.transcribed
        ) as episode_stats;
    """
    df = pd.read_sql(query, conn, params=[podcast_name])
    if df.empty:
        return {}
    return df.iloc[0].to_dict()


if __name__ == "__main__":
    # For quick testing
    conn = get_rds_connection()
    print("Number of Podcasts:", get_number_of_podcasts(conn))
    print("Number of Episodes:", get_number_of_episodes(conn))
    print("Number of Transcripts:", get_number_of_transcripts(conn))
    print("Episodes per Podcast:", get_num_episodes_per_podcast(conn))
    print("Topics per Podcast:", get_topics_per_podcast(conn))
    print("Published Episodes Over Time:",
          get_published_episodes_over_time(conn))

    # Test new episode-level analytics queries
    print("\n--- Episode-Level Analytics ---")

    # Get first podcast for testing
    podcasts = get_all_podcasts(conn)
    if not podcasts.empty:
        test_podcast = podcasts.iloc[0]['podcast_name']
        print(f"\nTesting with podcast: {test_podcast}")

        print("\nTopics per Episode:")
        topics_per_ep = get_topics_per_episode_for_podcast(conn, test_podcast)
        print(topics_per_ep)

        print("\nEpisode Details (combined):")
        episode_details = get_episode_details_for_podcast(conn, test_podcast)
        print(episode_details)

        print("\nTopics Frequency:")
        topics_freq = get_topics_frequency_for_podcast(conn, test_podcast)
        print(topics_freq)

        print("\nSpeakers Frequency:")
        speakers_freq = get_speakers_frequency_for_podcast(conn, test_podcast)
        print(speakers_freq)

        print("\nEpisode Statistics:")
        stats = get_episode_stats_for_podcast(conn, test_podcast)
        print(stats)
    else:
        print("No podcasts found in database")
