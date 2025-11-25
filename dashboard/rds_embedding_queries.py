import os
import pandas as pd
from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def get_rds_connection() -> connection:
    """Returns the connection to the RDS database"""
    conn = connect(
        host=os.getenv("RDS_HOST"),
        database=os.getenv("RDS_DB_NAME"),
        user=os.getenv("RDS_USERNAME"),
        password=os.getenv("RDS_PASSWORD")
    )
    return conn


def get_similar_episodes(conn: connection, query_embedding: list, top_k: int = 5) -> list:
    """Returns the top K most similar episodes based on the provided embedding"""
    # Convert embedding to string format for pgvector
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    query = """
        SELECT DISTINCT ON (e.episode_id)
            e.episode_id,
            e.episode_title,
            e.published_at,
            p.podcast_id,
            p.podcast_name,
            ee.chunk_text,
            1 - (ee.transcript_embedding <=> %s::vector) AS similarity_score
        FROM episode_embedding ee
        JOIN episode e ON ee.episode_id = e.episode_id
        JOIN podcast p ON e.podcast_id = p.podcast_id
        ORDER BY e.episode_id, similarity_score DESC
        LIMIT %s;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (embedding_str, top_k))
        return cursor.fetchall()


def episode_has_embeddings(conn: connection, episode_id: int) -> bool:
    """Check if an episode has embeddings"""
    query = """
        SELECT EXISTS(
            SELECT 1 
            FROM episode_embedding 
            WHERE episode_id = %s
        );
    """

    with conn.cursor() as cursor:
        cursor.execute(query, (episode_id,))
        return cursor.fetchone()[0]


if __name__ == "__main__":
    # Example usage
    conn = get_rds_connection()
    print(episode_has_embeddings(conn, 10))
