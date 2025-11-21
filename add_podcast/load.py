from psycopg2 import connect
import os
from psycopg2.extensions import connection
from extract import get_data_from_rss
from transform import validate_feed
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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


def upload_podcast(conn: connection, podcast_data: dict) -> bool:
    """
    Uploads the podcast data to the podcast table.

    Returns:
        bool: True if podcast was inserted (new), False if it already exists (duplicate).
    """

    # First, check if podcast already exists
    check_query = "SELECT podcast_id FROM podcast WHERE podcast_url = %s"

    with conn.cursor() as cursor:
        cursor.execute(check_query, (podcast_data.get('link'),))
        existing = cursor.fetchone()

        if existing:
            # Podcast already exists - this is a duplicate
            return False

        # Podcast doesn't exist - insert it
        insert_query = """
            INSERT INTO podcast (podcast_name, publish_date, language_id, podcast_url)
            VALUES (%s, %s, %s, %s);
            """
        cursor.execute(insert_query, (
            podcast_data.get('podcast_name'),
            podcast_data.get('publish_date'),
            podcast_data.get('language_id'),
            podcast_data.get('link')
        ))

        return True  # Successfully inserted


def load_data_to_db_from_rss(rss: str) -> dict:
    """
    Loads the podcast data from the RSS feed into the RDS database.

    Returns:
        dict with 'is_duplicate' (bool) and 'status' (str)
    """

    feed = get_data_from_rss(rss)

    logger.info(f"Extracted feed data: %s", feed)

    values_to_add = validate_feed(feed)

    logger.info(f"Data to add: %s", values_to_add)

    with get_rds_connection() as conn:

        language_id = upload_language(conn, values_to_add.get('language'))
        logger.info(f"Uploaded language with ID: %s", language_id)

        values_to_add['language_id'] = language_id
        conn.commit()

        is_new = upload_podcast(conn, values_to_add)
        conn.commit()

        if is_new:
            logger.info("New podcast uploaded successfully.")
            return {'is_duplicate': False, 'status': 'added'}
        else:
            logger.info("Podcast already exists - duplicate detected.")
            return {'is_duplicate': True, 'status': 'duplicate'}


if __name__ == "__main__":
    TEST_RSS_URL = "https://audioboom.com/channels/2399216.rss"
    load_data_to_db_from_rss(TEST_RSS_URL)
