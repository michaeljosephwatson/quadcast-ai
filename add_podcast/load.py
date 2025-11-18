from psycopg2 import connect
import os
from psycopg2.extensions import connection
from extract import get_data_from_rss
from transform import validate_feed


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
    """Uploads the language to to the language table and returns the language id"""

    with conn.cursor() as cursor:
        query = """
            INSERT INTO language (language_name)
            VALUES (%s)
            ON CONFLICT DO NOTHING
            RETURNING language_id;
            """
        cursor.execute(query, (language,))
        result = cursor.fetchone()
        if result:
            return result[0]

        query = """
            SELECT language_id FROM language WHERE language_name = %s;
            """

        cursor.execute(query, (language,))
        return cursor.fetchone()[0]


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

    with get_rds_connection() as conn:

        language_id = upload_language(conn, values_to_add.get('language'))
        values_to_add['language_id'] = language_id
        conn.commit()

        upload_podcast(conn, values_to_add)
        conn.commit()


if __name__ == "__main__":
    TEST_RSS_URL = "https://audioboom.com/channels/2399216.rss"
    load_data_to_db_from_rss(TEST_RSS_URL)
