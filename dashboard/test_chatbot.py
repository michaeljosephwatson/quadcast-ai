import pytest
from chatbot import (get_openai_key, get_query_embedding, fetch_episode_chunks,
                     is_message_about_similar_eps, fetch_similar_episodes,
                     build_episode_context, build_system_prompt, prepare_messages,
                     call_openai_chat, get_episode_response)
from rds_embedding_queries import get_rds_connection


@pytest.fixture
def conn():
    """Fixture to provide a database connection for tests."""
    connection = get_rds_connection()
    yield connection
    connection.close()


@pytest.fixture
def sample_episode_context():
    """Fixture providing sample episode metadata for testing."""
    return {
        'title': 'Test Episode',
        'podcast_name': 'Test Podcast',
        'summary': 'A fascinating discussion about AI and technology.',
        'topics': ['AI', 'Technology', 'Innovation'],
        'speakers': ['John Doe', 'Jane Smith']
    }


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


def test_build_system_prompt(sample_episode_context):
    """Test building system prompt with episode context"""
    current_context = "[Chunk 1]: Some relevant content here."
    similar_context = "**Similar Episodes Available:**\n- Episode 5"

    prompt = build_system_prompt(
        sample_episode_context, current_context, similar_context)

    assert isinstance(prompt, str)
    assert sample_episode_context['title'] in prompt
    assert sample_episode_context['podcast_name'] in prompt
    assert 'AI' in prompt  # Check topics are included
    assert 'John Doe' in prompt  # Check speakers are included
    assert current_context in prompt
    assert similar_context in prompt


def test_prepare_messages_without_history(sample_episode_context):
    """Test message preparation without chat history"""
    system_prompt = "You are a helpful assistant."
    user_message = "What is this episode about?"

    messages = prepare_messages(system_prompt, user_message)

    assert isinstance(messages, list)
    assert len(messages) == 2
    assert messages[0]['role'] == 'system'
    assert messages[0]['content'] == system_prompt
    assert messages[1]['role'] == 'user'
    assert messages[1]['content'] == user_message


def test_prepare_messages_with_history(sample_episode_context):
    """Test message preparation with chat history"""
    system_prompt = "You are a helpful assistant."
    user_message = "Tell me more."
    chat_history = [
        {"role": "user", "content": "What is this about?"},
        {"role": "assistant", "content": "This episode discusses AI."},
    ]

    messages = prepare_messages(system_prompt, user_message, chat_history)

    assert isinstance(messages, list)
    assert len(messages) == 4  # system + 2 history + new user message
    assert messages[0]['role'] == 'system'
    assert messages[1] == chat_history[0]
    assert messages[2] == chat_history[1]
    assert messages[3]['role'] == 'user'
    assert messages[3]['content'] == user_message


def test_prepare_messages_limits_history():
    """Test that message preparation limits chat history to last 10 messages"""
    system_prompt = "You are a helpful assistant."
    user_message = "Current question"

    # Create 15 messages of history
    chat_history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
        for i in range(15)
    ]

    messages = prepare_messages(system_prompt, user_message, chat_history)

    # Should be: 1 system + 10 history + 1 new user = 12 total
    assert len(messages) == 12
    assert messages[0]['role'] == 'system'
    assert messages[-1]['content'] == user_message
    # Check that only last 10 history messages are included
    assert messages[1]['content'] == "Message 5"


def test_call_openai_chat():
    """Test OpenAI chat API call with simple messages"""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'test successful' if you receive this."}
    ]

    response = call_openai_chat(messages)

    assert isinstance(response, str)
    assert len(response) > 0
    # Should not be an error message
    assert not response.startswith("Sorry, I encountered an error:")


# Integration tests for different user questions on episode 10

def test_episode_content_question(conn, sample_episode_context):
    """Test asking about episode content"""
    episode_id = 10
    user_message = "What are the main topics discussed in this episode?"

    response = get_episode_response(
        user_message,
        sample_episode_context,
        conn,
        episode_id
    )

    assert isinstance(response, str)
    assert len(response) > 0
    assert not response.startswith("Sorry, I encountered an error:")


def test_similar_episodes_request(conn, sample_episode_context):
    """Test requesting similar episodes"""
    episode_id = 10
    user_message = "Can you recommend similar episodes?"

    response = get_episode_response(
        user_message,
        sample_episode_context,
        conn,
        episode_id
    )

    assert isinstance(response, str)
    assert len(response) > 0
    # Response might mention similar episodes if available


def test_unrelated_question_rejection(conn, sample_episode_context):
    """Test that unrelated questions are rejected"""
    episode_id = 10
    user_message = "What is 2 + 2?"

    response = get_episode_response(
        user_message,
        sample_episode_context,
        conn,
        episode_id
    )

    assert isinstance(response, str)
    # Should contain rejection message about podcast-only questions
    assert "podcast" in response.lower() or "episode" in response.lower()


def test_question_with_chat_history(conn, sample_episode_context):
    """Test question with existing chat history"""
    episode_id = 10
    user_message = "Can you elaborate on that?"
    chat_history = [
        {"role": "user", "content": "What is this episode about?"},
        {"role": "assistant", "content": "This episode discusses AI technology."}
    ]

    response = get_episode_response(
        user_message,
        sample_episode_context,
        conn,
        episode_id,
        chat_history
    )

    assert isinstance(response, str)
    assert len(response) > 0


def test_timestamp_question(conn, sample_episode_context):
    """Test asking about specific parts of the episode"""
    episode_id = 10
    user_message = "Where in the episode do they discuss machine learning?"

    response = get_episode_response(
        user_message,
        sample_episode_context,
        conn,
        episode_id
    )

    assert isinstance(response, str)
    assert len(response) > 0
    # May reference chunk numbers if available


def test_empty_message_handling(conn, sample_episode_context):
    """Test handling of empty or whitespace-only messages"""
    episode_id = 10
    user_message = "   "

    response = get_episode_response(
        user_message,
        sample_episode_context,
        conn,
        episode_id
    )

    assert isinstance(response, str)
    # Should handle gracefully without crashing


def test_nonexistent_episode(conn, sample_episode_context):
    """Test handling of a nonexistent episode ID"""
    episode_id = -3
    user_message = "What is this episode about?"

    response = get_episode_response(
        user_message,
        sample_episode_context,
        conn,
        episode_id
    )

    assert isinstance(response, str)
    # Should handle gracefully, possibly indicating no data found


def test_personal_data_request(conn, sample_episode_context):
    """Test handling of personal data requests"""
    episode_id = 10
    user_message = "Can you tell me personal information about the host?"

    response = get_episode_response(
        user_message,
        sample_episode_context,
        conn,
        episode_id
    )

    assert isinstance(response, str)
    # Should respond with privacy statement
    assert "respect user privacy" in response.lower()
