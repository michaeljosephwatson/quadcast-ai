"""Module to extract untranscribed episode URLs from the database and mark them as transcribed."""
import os
import json
import boto3
from psycopg2 import connect
from psycopg2.extensions import connection


def get_secret():
    """Retrieve database credentials from AWS Secrets Manager"""
    secret_name = "c20-quadcast-secrets"
    region_name = os.getenv("AWS_REGION", "eu-west-2")

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])

    return secret


def get_rds_connection() -> connection:
    """Returns the connection to the RDS database"""

    # Check if running locally or in Lambda
    if os.getenv("USE_SECRETS_MANAGER") == "true":
        secret = get_secret()
        conn = connect(
            host=secret['RDS_HOST'],
            database=secret['RDS_DB_NAME'],
            user=secret['RDS_USERNAME'],
            password=secret['RDS_PASSWORD'],
            port=int(secret['RDS_PORT'])
        )
    else:
        # Local testing with direct env vars
        conn = connect(
            host=os.getenv("RDS_HOST"),
            database=os.getenv("RDS_DB_NAME"),
            user=os.getenv("RDS_USERNAME"),
            password=os.getenv("RDS_PASSWORD"),
            port=int(os.getenv("RDS_PORT", 5432))
        )

    return conn


def get_untranscribed_episode(conn: connection) -> dict:
    """
    Fetches ONE untranscribed episode from the database with row-level locking.
    Uses SELECT FOR UPDATE SKIP LOCKED to ensure parallel Lambda executions
    don't pick the same episode.

    The lock is held until the transaction commits (via update_episode_transcribed).
    """
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT
                e.episode_id,
                p.podcast_id,
                p.podcast_name,
                e.episode_title,
                e.audio_url
            FROM episode as e
            JOIN podcast as p
                 ON e.podcast_id = p.podcast_id
            WHERE e.transcribed = FALSE
            ORDER BY e.uploaded_at ASC
            LIMIT 1
            FOR UPDATE OF e SKIP LOCKED
        """)
        result = cursor.fetchone()

        if not result:
            return None

        return {
            "episode_id": result[0],
            "podcast_id": result[1],
            "podcast_name": result[2],
            "episode_title": result[3],
            "audio_url": result[4]
        }


def update_episode_transcribed(conn: connection, episode_id: int):
    """Marks episode as transcribed."""
    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE episode
            SET transcribed = TRUE
            WHERE episode_id = %s
        """, (episode_id,))
        conn.commit()
