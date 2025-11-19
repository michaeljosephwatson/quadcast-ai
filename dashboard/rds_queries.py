from psycopg2 import connect
from psycopg2.extensions import connection
import os
from dotenv import load_dotenv

load_dotenv()  # .env for local development, ignored in production


def get_rds_connection() -> connection:
    """Returns the connection to the RDS database"""
    conn = connect(
        host=os.getenv("RDS_HOST"),
        database=os.getenv("RDS_DB_NAME"),
        user=os.getenv("RDS_USERNAME"),
        password=os.getenv("RDS_PASSWORD"),
        port=int(os.getenv("RDS_PORT")),
    )
    return conn


def get_number_of_podcasts(conn: connection) -> int:
    """Returns the total number of podcasts in the database"""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM podcast;")
    result = cur.fetchone()
    cur.close()
    return result[0]


def get_number_of_episodes(conn: connection, podcast_name=None) -> int:
    """Returns the total number of episodes in the database or for a specific podcast"""
    cur = conn.cursor()
    if not podcast_name:
        cur.execute("SELECT COUNT(*) FROM episode;")
    else:
        cur.execute("""
            SELECT COUNT(*) FROM episode e
            JOIN podcast p  ON e.podcast_id = p.podcast_id
            WHERE p.podcast_name = %s;
        """, (podcast_name,))
    result = cur.fetchone()
    cur.close()
    return result[0]


def get_number_of_transcripts(conn: connection, podcast_name=None) -> int:
    """Returns the total number of transcripts in the database or for a specific podcast"""
    cur = conn.cursor()
    if not podcast_name:
        cur.execute("SELECT COUNT(*) FROM episode WHERE transcribed = TRUE;")
    else:
        cur.execute("""
            SELECT COUNT(*) FROM episode e
            JOIN podcast p  ON e.podcast_id = p.podcast_id
            WHERE p.podcast_name = %s AND e.transcribed = TRUE;
        """, (podcast_name,))
    result = cur.fetchone()
    cur.close()
    return result[0]


if __name__ == "__main__":
    conn = get_rds_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM podcast")
        result = cursor.fetchall()
        print(
            f"Connection Successful! Found {len(result)} results")
    print(f"Total Podcasts: {get_number_of_podcasts(conn)}")
    conn.close()
