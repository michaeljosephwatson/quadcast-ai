"""Tests for OpenAI analyzer."""
import json
from unittest.mock import Mock, patch
import pytest
from analyser import (
    build_analysis_prompt,
    parse_analysis_response,
    analyze_transcript,
    call_openai_api
)


SAMPLE_TRANSCRIPT = """
Speaker 1: Welcome to the AI podcast. Today we're discussing machine learning.
Speaker 2: Thanks for having me. I think AI safety is crucial.
"""

SAMPLE_OPENAI_RESPONSE = {
    "topics": ["AI", "machine learning"],
    "summary": "Discussion about AI and machine learning."
}


def test_build_analysis_prompt():
    """Should build proper analysis prompt."""
    prompt = build_analysis_prompt(SAMPLE_TRANSCRIPT)

    assert "Analyze this podcast transcript" in prompt
    assert "topics" in prompt.lower()
    assert "summary" in prompt.lower()
    assert SAMPLE_TRANSCRIPT in prompt


def test_build_analysis_prompt_truncates_long_transcript():
    """Should truncate very long transcripts."""
    long_transcript = "Test content. " * 2000  # ~26KB
    prompt = build_analysis_prompt(long_transcript)

    # Prompt should be truncated to ~10k chars
    assert len(prompt) < 12000


def test_parse_analysis_response():
    """Should parse OpenAI response correctly."""
    result = parse_analysis_response(SAMPLE_OPENAI_RESPONSE)

    assert result['topics'] == ["AI", "machine learning"]
    assert result['summary'] == "Discussion about AI and machine learning."


def test_parse_analysis_response_missing_fields():
    """Should handle missing fields gracefully."""
    incomplete_response = {
        "topics": ["AI"]
    }

    result = parse_analysis_response(incomplete_response)

    assert result['topics'] == ["AI"]
    assert result['summary'] == ''


def test_parse_analysis_response_empty():
    """Should handle empty response."""
    result = parse_analysis_response({})

    assert result['topics'] == []
    assert result['summary'] == ''


@patch('analyser.get_openai_client')
def test_call_openai_api_success(mock_get_client):
    """Should successfully call OpenAI API."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = json.dumps(
        SAMPLE_OPENAI_RESPONSE)
    mock_client.chat.completions.create.return_value = mock_response
    mock_get_client.return_value = mock_client

    prompt = "Test prompt"
    result = call_openai_api(prompt)

    assert result == SAMPLE_OPENAI_RESPONSE
    mock_client.chat.completions.create.assert_called_once()


@patch('analyser.get_openai_client')
def test_call_openai_api_invalid_json(mock_get_client):
    """Should raise exception for invalid JSON response."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Not valid JSON"
    mock_client.chat.completions.create.return_value = mock_response
    mock_get_client.return_value = mock_client

    with pytest.raises(Exception) as exc_info:
        call_openai_api("Test prompt")

    assert "invalid JSON" in str(exc_info.value)


@patch('analyser.call_openai_api')
def test_analyze_transcript_success(mock_call_api):
    """Should successfully analyze transcript."""
    mock_call_api.return_value = SAMPLE_OPENAI_RESPONSE

    result = analyze_transcript(SAMPLE_TRANSCRIPT)

    assert result['topics'] == ["AI", "machine learning"]
    assert result['summary'] == "Discussion about AI and machine learning."


@patch('analyser.call_openai_api')
def test_analyze_transcript_handles_errors(mock_call_api):
    """Should propagate OpenAI API errors."""
    mock_call_api.side_effect = Exception("API error")

    with pytest.raises(Exception) as exc_info:
        analyze_transcript(SAMPLE_TRANSCRIPT)

    assert "API error" in str(exc_info.value)
