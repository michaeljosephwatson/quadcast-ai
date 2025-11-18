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


def load_podcast_to_db_from_rss(rss: str) -> None:
    """Loads the podcast data from the RSS feed into the RDS database"""

    pass
