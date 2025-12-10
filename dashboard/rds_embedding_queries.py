import os
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
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

    query = """
        WITH ranked_chunks AS (
            SELECT
                ee.episode_id,
                ee.chunk_text,
                1 - (ee.transcript_embedding <=> %s::vector) AS similarity_score
            FROM episode_embedding ee
        )
        SELECT
            e.episode_id,
            e.episode_title,
            e.published_at,
            p.podcast_id,
            p.podcast_name,
            MAX(rc.similarity_score) AS similarity_score
        FROM ranked_chunks rc
        JOIN episode e ON rc.episode_id = e.episode_id
        JOIN podcast p ON e.podcast_id = p.podcast_id
        GROUP BY e.episode_id, p.podcast_id
        ORDER BY similarity_score DESC
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


def find_similar_chunks_in_episode(conn: connection, episode_id: int, query_embedding: list, top_k: int = 5) -> list:
    """Find k similar chunks within a specific episode"""
    # Convert embedding to string format for pgvector
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

    query = """
        SELECT 
            ee.embedding_id,
            ee.episode_id,
            ee.chunk_index,
            ee.chunk_text,
            1 - (ee.transcript_embedding <=> %s::vector) AS similarity_score
        FROM episode_embedding ee
        WHERE ee.episode_id = %s
        ORDER BY ee.transcript_embedding <=> %s::vector
        LIMIT %s;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            query, (embedding_str, episode_id, embedding_str, top_k))
        return cursor.fetchall()


def find_similar_episodes_by_episode_id(conn: connection, episode_id: int, top_k: int = 5) -> list:
    """Find k episodes similar to a given episode"""
    query = """
        WITH target_embedding AS (
            SELECT transcript_embedding
            FROM episode_embedding
            WHERE episode_id = %s
            LIMIT 1
        ),
        ranked_chunks AS (
            SELECT
                ee.episode_id,
                1 - (ee.transcript_embedding <=> (SELECT transcript_embedding FROM target_embedding)) AS similarity_score
            FROM episode_embedding ee
            WHERE ee.episode_id != %s
        )
        SELECT
            e.episode_id,
            e.episode_title,
            e.published_at,
            p.podcast_id,
            p.podcast_name,
            MAX(rc.similarity_score) AS similarity_score
        FROM ranked_chunks rc
        JOIN episode e ON rc.episode_id = e.episode_id
        JOIN podcast p ON e.podcast_id = p.podcast_id
        GROUP BY e.episode_id, p.podcast_id
        ORDER BY similarity_score DESC
        LIMIT %s;
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (episode_id, episode_id, top_k))
        return cursor.fetchall()


if __name__ == "__main__":
    # Example usage
    conn = get_rds_connection()

    # Test if episode has embeddings
    has_embeddings = episode_has_embeddings(conn, 10)
    print(f"Episode 10 has embeddings: {has_embeddings}")

    # If it has embeddings, find similar episodes
    if has_embeddings:
        similar = find_similar_episodes_by_episode_id(conn, 10, top_k=5)
        print(f"\nFound {len(similar)} similar episodes:")
        for ep in similar:
            print(
                f"  - {ep['episode_title']} (Score: {ep['similarity_score']:.3f})")

    conn.close()
