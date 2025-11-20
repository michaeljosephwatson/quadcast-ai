"""Database operations for storing analysis results."""
import os
import logging
import psycopg2
from psycopg2.extensions import connection
from typing import Dict, List

logger = logging.getLogger(__name__)

RDS_HOST = os.getenv('RDS_HOST')
RDS_DB_NAME = os.getenv('RDS_DB_NAME')
RDS_USERNAME = os.getenv('RDS_USERNAME')
RDS_PASSWORD = os.getenv('RDS_PASSWORD')
RDS_PORT = int(os.getenv('RDS_PORT', 5432))


def get_db_connection() -> connection:
    """Create database connection."""
    logger.info(f"Connecting to database: {RDS_HOST}:{RDS_PORT}/{RDS_DB_NAME}")

    conn = psycopg2.connect(
        host=RDS_HOST,
        database=RDS_DB_NAME,
        user=RDS_USERNAME,
        password=RDS_PASSWORD,
        port=RDS_PORT
    )

    logger.info("Database connection established")
    return conn


def update_episode_summary(conn: connection, episode_id: int, summary: str):
    """Update episode with summary."""
    logger.info(f"Updating summary for episode {episode_id}")

    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE episode
            SET summary = %s
            WHERE episode_id = %s
        """, (summary, episode_id))

    logger.info(f"Summary updated for episode {episode_id}")


def store_topics(conn: connection, episode_id: int, topics: List[str]):
    """Store topics and link to episode."""
    logger.info(f"Storing {len(topics)} topics for episode {episode_id}")

    with conn.cursor() as cursor:
        for topic_name in topics:
            cursor.execute("""
                INSERT INTO topics (topic_name)
                VALUES (%s)
                ON CONFLICT (topic_name) DO UPDATE
                SET topic_name = EXCLUDED.topic_name
                RETURNING topic_id
            """, (topic_name,))

            topic_id = cursor.fetchone()[0]
            logger.debug(f"Topic '{topic_name}' has ID {topic_id}")

            cursor.execute("""
                INSERT INTO episode_topics (episode_id, topic_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (episode_id, topic_id))

    logger.info(f"Stored {len(topics)} topics for episode {episode_id}")


def store_analysis(episode_id: int, analysis: Dict):
    """Store complete analysis results in database."""
    logger.info(f"Storing analysis for episode {episode_id}")

    conn = get_db_connection()

    try:
        # Update episode summary
        update_episode_summary(conn, episode_id, analysis['summary'])

        # Store topics
        store_topics(conn, episode_id, analysis['topics'])

        # Commit transaction
        conn.commit()
        logger.info(f"✅ Successfully stored analysis for episode {episode_id}")

    except Exception as e:
        logger.error(
            f"Failed to store analysis for episode {episode_id}: {str(e)}")
        conn.rollback()
        raise Exception(f"Failed to store analysis: {str(e)}") from e

    finally:
        conn.close()
        logger.debug("Database connection closed")


def get_episode_analysis(episode_id: int) -> Dict:
    """Retrieve analysis for an episode.Returns dict with 'summary' and 'topics'"""
    logger.info(f"Retrieving analysis for episode {episode_id}")

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            # Get summary
            cursor.execute("""
                SELECT summary
                FROM episode
                WHERE episode_id = %s
            """, (episode_id,))

            result = cursor.fetchone()
            summary = result[0] if result else None

            # Get topics
            cursor.execute("""
                SELECT t.topic_name
                FROM topics t
                JOIN episode_topics et ON t.topic_id = et.topic_id
                WHERE et.episode_id = %s
            """, (episode_id,))

            topics = [row[0] for row in cursor.fetchall()]

            logger.info(
                f"Retrieved analysis: {len(topics)} topics, summary={'present' if summary else 'missing'}")

            return {
                'summary': summary,
                'topics': topics
            }

    finally:
        conn.close()
        logger.debug("Database connection closed")


def episode_exists(episode_id: int) -> bool:
    """Check if episode exists in database.Returns True if exists, False otherwise"""
    logger.debug(f"Checking if episode {episode_id} exists")

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM episode WHERE episode_id = %s
            """, (episode_id,))

            exists = cursor.fetchone() is not None
            logger.debug(f"Episode {episode_id} exists: {exists}")
            return exists

    finally:
        conn.close()
