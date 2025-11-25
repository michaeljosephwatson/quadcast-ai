"""Module for semantic search queries using vector embeddings"""
import logging
import os
import re
from typing import Optional
import pandas as pd
from psycopg2.extensions import connection
from openai import OpenAI
import tiktoken

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
EMBEDDING_MODEL = 'text-embedding-3-small'


def get_openai_client() -> OpenAI:
    """Get OpenAI client instance"""
    return OpenAI(api_key=OPENAI_API_KEY)


def get_tokenizer(model: str = EMBEDDING_MODEL):
    """Get tiktoken tokenizer for the embedding model"""
    encoding = tiktoken.encoding_for_model(model)
    return encoding


def trim_to_sentence_boundaries(text: str) -> str:
    """
    Trim text to start at a sentence boundary instead of mid-sentence.
    Only trims the start if text begins mid-sentence, preserves most of the content.
    """
    # Check if text starts with a lowercase letter or mid-sentence indicator
    if len(text) > 0 and text[0].islower():
        # Find the first sentence boundary before our position
        # Look for previous sentence ending within first 100 chars
        search_window = text[:min(100, len(text))]
        last_boundary = -1

        for match in re.finditer(r'[.!?]\s+', search_window):
            last_boundary = match.end()

        if last_boundary > 0:
            # Start from the sentence boundary
            trimmed = text[last_boundary:].strip()
            return trimmed if trimmed else text

    # Return original text if it starts with capital letter or no boundary found
    return text


def embed_query(query: str, model: str = EMBEDDING_MODEL) -> list:
    """Generate embedding vector for search query"""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    client = get_openai_client()

    try:
        response = client.embeddings.create(
            model=model,
            input=query
        )
        embedding = response.data[0].embedding
        logger.debug("Generated query embedding: %s dimensions", len(embedding))
        return embedding

    except Exception as e:
        logger.error("OpenAI embedding error: %s", str(e))
        raise Exception("Failed to generate embedding for query: %s" % str(e)) from e


def search_episodes_by_embedding(
    conn: connection,
    query: str,
    limit: int = 5,
    similarity_threshold: float = 0.5
) -> pd.DataFrame:
    """
    Search for relevant episode chunks using semantic similarity.

    Args:
        conn: Database connection
        query: Search query text
        limit: Maximum number of results to return
        similarity_threshold: Minimum cosine similarity score (0.0 to 1.0)

    Returns:
        DataFrame with search results containing episode info and chunk text
    """
    logger.info("Searching for query: %s", query)

    # Generate embedding for the query
    query_embedding = embed_query(query)

    # Convert embedding to PostgreSQL vector format
    embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'

    search_query = f"""
        SELECT
            e.episode_id,
            e.episode_title,
            p.podcast_name,
            e.published_at,
            ee.chunk_index,
            ee.chunk_text,
            (1 - (ee.transcript_embedding <=> %s::vector)) AS similarity
        FROM episode_embedding ee
        JOIN episode e ON ee.episode_id = e.episode_id
        JOIN podcast p ON e.podcast_id = p.podcast_id
        WHERE (1 - (ee.transcript_embedding <=> %s::vector)) > %s
        ORDER BY similarity DESC
        LIMIT %s
    """

    try:
        df = pd.read_sql(
            search_query,
            conn,
            params=(embedding_str, embedding_str, similarity_threshold, limit)
        )

        # Trim chunk_text to sentence boundaries
        if not df.empty and 'chunk_text' in df.columns:
            df['chunk_text'] = df['chunk_text'].apply(trim_to_sentence_boundaries)

        logger.info("Found %s results", len(df))
        return df

    except Exception as e:
        logger.error("Search query failed: %s", str(e))
        raise Exception("Search failed: %s" % str(e)) from e
