import pytest
from chatbot import (get_openai_key, get_query_embedding, fetch_episode_chunks,
                     is_message_about_similar_eps, fetch_similar_episodes, build_episode_context)
from rds_embedding_queries import get_rds_connection


@pytest.fixture
def conn():
    """Fixture to provide a database connection for tests."""
    connection = get_rds_connection()
    yield connection
    connection.close()


def test_get_openai_key():
    """Test retrieval of OpenAI API key from AWS Secrets Manager"""
    key = get_openai_key()
    assert isinstance(key, str)
    assert len(key) > 0


def test_get_query_embedding():
    """Test generation of query embedding using OpenAI"""
    sample_text = "What are the main topics discussed in this episode?"
    embedding = get_query_embedding(sample_text)
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(x, float) for x in embedding)


def test_fetch_episode_chunks(conn):
    """Test fetching relevant episode chunks based on query embedding"""
    episode_id = 10
    query_embedding = get_query_embedding("Tell me about the main topics.")
    chunks = fetch_episode_chunks(conn, episode_id, query_embedding)
    assert isinstance(chunks, str)
    if chunks:
        assert "[Chunk" in chunks  # Basic check for formatted chunk text


def test_is_message_about_similar_eps():
    """Test detection of user intent for similar episodes"""
    positive_messages = [
        "Can you recommend similar episodes?",
        "I want to hear something like this.",
        "Are there related episodes?"
    ]
    negative_messages = [
        "What is the episode about?",
        "Tell me more about the host.",
        "How long is this episode?"
    ]

    for msg in positive_messages:
        assert is_message_about_similar_eps(msg) is True

    for msg in negative_messages:
        assert is_message_about_similar_eps(msg) is False


def test_fetch_similar_episodes(conn):
    """Test fetching similar episodes based on episode ID"""
    episode_id = 10
    similar_eps = fetch_similar_episodes(conn, episode_id)
    assert isinstance(similar_eps, str)
    if similar_eps:
        assert "Episode" in similar_eps  # Basic check for formatted episode text


def test_build_episode_context(conn):
    """Test building episode context including chunks and similar episodes"""
    episode_id = 10
    user_message = "Can you recommend similar episodes?"

    context = build_episode_context(
        conn, episode_id, query_embedding=get_query_embedding(user_message), user_message=user_message)
    assert isinstance(context, dict)
    assert 'chunks' in context
    assert 'similar_episodes' in context

    assert isinstance(context['chunks'], str)
    assert isinstance(context['similar_episodes'], str)
    if context['chunks']:
        assert "[Chunk" in context['chunks']
    if context['similar_episodes']:
        assert "Episode" in context['similar_episodes']
