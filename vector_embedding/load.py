"""Database operations for storing embeddings in pgvector."""
import os
import logging
from typing import List, Dict
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

# Database configuration
RDS_HOST = os.getenv('RDS_HOST')
RDS_DB_NAME = os.getenv('RDS_DB_NAME')
RDS_USERNAME = os.getenv('RDS_USERNAME')
RDS_PASSWORD = os.getenv('RDS_PASSWORD')
RDS_PORT = int(os.getenv('RDS_PORT', 5432))


def get_db_connection() -> connection:
    """Create database connection."""
    logger.info("Connecting to database: %s:%s/%s",
                RDS_HOST, RDS_PORT, RDS_DB_NAME)

    conn = psycopg2.connect(
        host=RDS_HOST,
        database=RDS_DB_NAME,
        user=RDS_USERNAME,
        password=RDS_PASSWORD,
        port=RDS_PORT
    )

    logger.info("Database connection established")
    return conn


def episode_exists(conn: connection, episode_id: int) -> bool:
    """Check if episode exists in database."""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM episode WHERE episode_id = %s",
            (episode_id,)
        )
        exists = cursor.fetchone() is not None
        logger.debug("Episode %s exists: %s", episode_id, exists)
        return exists


def clear_existing_embeddings(conn: connection, episode_id: int):
    """Remove any existing embeddings for this episode."""
    with conn.cursor() as cursor:
        cursor.execute(
            "DELETE FROM episode_embedding WHERE episode_id = %s",
            (episode_id,)
        )


def insert_embeddings(conn: connection, episode_id: int, embedded_chunks: List[Dict]):
    """Insert embedded chunks into episode_embedding table."""
    logger.info("Inserting %s embeddings for episode %s",
                len(embedded_chunks), episode_id)

    # Prepare data for bulk insert
    values = [
        (
            episode_id,
            chunk['embedding'],
            chunk['chunk_index'],
            chunk['chunk_text']
        )
        for chunk in embedded_chunks
    ]

    with conn.cursor() as cursor:
        execute_values(
            cursor,
            """
            INSERT INTO episode_embedding 
                (episode_id, transcript_embedding, chunk_index, chunk_text)
            VALUES %s
            """,
            values,
            template="(%s, %s::vector, %s, %s)"
        )

    logger.info("Successfully inserted %s embeddings", len(embedded_chunks))


def load_embeddings(episode_id: int, embedded_chunks: List[Dict]) -> bool:
    """Store embedded chunks in database."""
    logger.info("Loading %s embeddings for episode %s",
                len(embedded_chunks), episode_id)

    if not embedded_chunks:
        raise ValueError("embedded_chunks cannot be empty")

    if not all('embedding' in chunk for chunk in embedded_chunks):
        raise ValueError("All chunks must have 'embedding' field")

    conn = get_db_connection()

    try:
        if not episode_exists(conn, episode_id):
            raise ValueError("Episode %s not found in database" % episode_id)

        # Clear existing embeddings (allows re-processing)
        clear_existing_embeddings(conn, episode_id)

        # Insert new embeddings
        insert_embeddings(conn, episode_id, embedded_chunks)

        conn.commit()

        logger.info("✅ Successfully loaded %s embeddings for episode %s",
                    len(embedded_chunks), episode_id)

        return True

    except Exception as e:
        logger.error("Failed to load embeddings for episode %s: %s",
                     episode_id, str(e))
        conn.rollback()
        raise Exception("Failed to load embeddings: %s" % str(e)) from e

    finally:
        conn.close()
        logger.debug("Database connection closed")
