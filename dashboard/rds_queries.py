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
        SELECT e.*, p.podcast_name, p.author, p.description as podcast_description
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
