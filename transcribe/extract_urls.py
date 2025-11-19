from psycopg2 import connect
import os
from psycopg2.extensions import connection


def get_rds_connection() -> connection:
    """Returns the connection to the RDS database"""
    conn = connect(
        host=os.getenv("RDS_HOST"),
        database=os.getenv("RDS_DB_NAME"),
        user=os.getenv("RDS_USERNAME"),
        password=os.getenv("RDS_PASSWORD")
    )
    return conn


def get_untranscribed_podcasts(conn: connection) -> list[tuple]:
    """Fetches urls of untranscribed podcasts from the database."""
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT
                p.podcast_name,
                e.episode_title,
                e.audio_url
            FROM episode as e
            JOIN podcast as p 
                 ON e.podcast_id = p.podcast_id
            WHERE e.transcribed = FALSE
        """)
        return cursor.fetchall()
