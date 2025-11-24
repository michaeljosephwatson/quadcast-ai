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


if __name__ == "__main__":
    # For quick testing
    conn = get_rds_connection()
    print("Number of Podcasts:", get_number_of_podcasts(conn))
    print("Number of Episodes:", get_number_of_episodes(conn))
    print("Number of Transcripts:", get_number_of_transcripts(conn))
    print("Episodes per Podcast:", get_num_episodes_per_podcast(conn))
    print("Topics per Podcast:", get_topics_per_podcast(conn))
