from psycopg2 import connect
import os
from psycopg2.extensions import connection
from extract import get_data_from_rss
from transform import validate_feed
import logging


def get_rds_connection() -> connection:
    """Returns the connection to the RDS database"""
    conn = connect(
        host=os.getenv("RDS_HOST"),
        database=os.getenv("RDS_DB_NAME"),
        user=os.getenv("RDS_USERNAME"),
        password=os.getenv("RDS_PASSWORD")
    )
    return conn


def upload_language(conn: connection, language: str) -> int:
    """
    Insert or update a language and return its language_id.
    Uses PostgreSQL's RETURNING to avoid redundant SELECT queries.
    """
    sql = """
        INSERT INTO language (language_name)
        VALUES (%s)
        ON CONFLICT (language_name)
        DO UPDATE SET language_name = EXCLUDED.language_name
        RETURNING language_id;
    """

    with conn.cursor() as cursor:
        cursor.execute(sql, (language,))
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(f"Failed to upsert language '{language}'")
        return row[0]


def upload_podcast(conn: connection, podcast_data: dict) -> None:
    """Uploads the podcast data to the podcast table"""

    with conn.cursor() as cursor:
        query = """
            INSERT INTO podcast (podcast_name, publish_date, language_id, podcast_url)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
            """
        cursor.execute(query, (
            podcast_data.get('podcast_name'),
            podcast_data.get('publish_date'),
            podcast_data.get('language_id'),
            podcast_data.get('link')
        ))


def load_data_to_db_from_rss(rss: str) -> None:
    """Loads the podcast data from the RSS feed into the RDS database"""

    feed = get_data_from_rss(rss)
    values_to_add = validate_feed(feed)

    logging.info(f"Data to add: %s", values_to_add)

    with get_rds_connection() as conn:

        language_id = upload_language(conn, values_to_add.get('language'))
        logging.info(f"Uploaded language with ID: %s", language_id)

        values_to_add['language_id'] = language_id
        conn.commit()

        upload_podcast(conn, values_to_add)
        conn.commit()

        logging.info("Podcast data uploaded successfully.")


if __name__ == "__main__":
    TEST_RSS_URL = "https://audioboom.com/channels/2399216.rss"
    load_data_to_db_from_rss(TEST_RSS_URL)
