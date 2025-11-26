import pytest
from unittest.mock import patch, MagicMock

# Mock AWS and OpenAI BEFORE importing chatbot
with patch('boto3.session.Session.client') as mock_boto_client:
    mock_secrets = MagicMock()
    mock_secrets.get_secret_value.return_value = {
        'SecretString': '{"OPENAI_API_KEY": "test-key-12345"}'
    }
    mock_boto_client.return_value = mock_secrets

    with patch('openai.OpenAI'):
        # Now safe to import chatbot
        from chatbot import (is_message_about_similar_eps, fetch_similar_episodes,
                             build_system_prompt, prepare_messages)


@pytest.fixture
def conn():
    """Mock database connection for tests."""
    mock_conn = MagicMock()
    yield mock_conn


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


def test_prepare_messages_without_history():
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


def test_prepare_messages_with_history():
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


def test_system_prompt_includes_guidelines(sample_episode_context):
    """Test that system prompt includes important guidelines"""
    current_context = "Some context"
    similar_context = ""

    prompt = build_system_prompt(
        sample_episode_context, current_context, similar_context)

    # Check for important guidelines
    assert "podcast" in prompt.lower()
    assert "privacy" in prompt.lower()
    assert "reject" in prompt.lower() or "only help" in prompt.lower()


def test_system_prompt_handles_empty_context(sample_episode_context):
    """Test system prompt generation with empty contexts"""
    prompt = build_system_prompt(sample_episode_context, "", "")

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert sample_episode_context['title'] in prompt


def test_system_prompt_handles_missing_metadata():
    """Test system prompt with minimal episode context"""
    minimal_context = {
        'title': 'Test Episode',
        'podcast_name': 'Test Podcast'
    }

    prompt = build_system_prompt(minimal_context, "", "")

    assert isinstance(prompt, str)
    assert minimal_context['title'] in prompt
    assert minimal_context['podcast_name'] in prompt


def test_prepare_messages_with_empty_history():
    """Test message preparation with empty chat history list"""
    system_prompt = "You are a helpful assistant."
    user_message = "What is this episode about?"
    chat_history = []

    messages = prepare_messages(system_prompt, user_message, chat_history)

    assert isinstance(messages, list)
    assert len(messages) == 2
    assert messages[0]['role'] == 'system'
    assert messages[1]['role'] == 'user'


def test_is_message_about_similar_eps_case_insensitive():
    """Test that similar episode detection is case insensitive"""
    messages = [
        "Can you RECOMMEND similar episodes?",
        "I want to hear something LIKE THIS.",
        "Are there RELATED episodes?"
    ]

    for msg in messages:
        assert is_message_about_similar_eps(msg) is True


def test_fetch_similar_episodes_nonexistent(conn):
    """Test fetching similar episodes for a nonexistent episode"""
    episode_id = -999
    similar_eps = fetch_similar_episodes(conn, episode_id)
    assert isinstance(similar_eps, str)
    # Should return empty string or handle gracefully


def test_fetch_similar_episodes_with_top_k(conn):
    """Test fetching similar episodes with custom top_k parameter"""
    episode_id = 10
    similar_eps = fetch_similar_episodes(conn, episode_id, top_k=3)
    assert isinstance(similar_eps, str)
