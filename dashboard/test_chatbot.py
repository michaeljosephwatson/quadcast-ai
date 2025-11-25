from chatbot import get_openai_key


def test_get_openai_key():
    """Test retrieval of OpenAI API key from AWS Secrets Manager"""
    key = get_openai_key()
    assert isinstance(key, str)
    assert len(key) > 0
