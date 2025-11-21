"""Tests for database operations."""
import pytest
from unittest.mock import MagicMock, patch
from database import (
    store_topics,
    store_analysis,
    get_episode_analysis
)


SAMPLE_ANALYSIS = {
    'topics': ['AI', 'Machine Learning', 'Ethics'],
    'summary': 'Discussion about AI ethics and machine learning.'
}


@pytest.fixture
def mock_connection():
    """Create mock database connection."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    conn.cursor.return_value.__exit__.return_value = None
    return conn, cursor


def test_store_topics_new_topics(mock_connection):
    """Should insert new topics and link to episode."""
    conn, cursor = mock_connection

    # Mock topic_id returns
    cursor.fetchone.side_effect = [(1,), (2,), (3,)]

    store_topics(conn, episode_id=123, topics=['AI', 'ML', 'Ethics'])

    # Should call execute 6 times (3 inserts + 3 links)
    assert cursor.execute.call_count == 6


def test_store_topics_empty_list(mock_connection):
    """Should handle empty topics list."""
    conn, cursor = mock_connection

    store_topics(conn, episode_id=123, topics=[])

    # Should not call execute
    cursor.execute.assert_not_called()


@patch('database.get_db_connection')
def test_store_analysis_success(mock_get_conn):
    """Should successfully store analysis."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.side_effect = [(1,), (2,), (3,)]
    mock_get_conn.return_value = mock_conn

    store_analysis(episode_id=123, analysis=SAMPLE_ANALYSIS)

    # Should commit
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


@patch('database.get_db_connection')
def test_store_analysis_rollback_on_error(mock_get_conn):
    """Should rollback on error."""
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = Exception("DB error")
    mock_get_conn.return_value = mock_conn

    with pytest.raises(Exception) as exc_info:
        store_analysis(episode_id=123, analysis=SAMPLE_ANALYSIS)

    # Should rollback
    mock_conn.rollback.assert_called_once()
    mock_conn.close.assert_called_once()
    assert "Failed to store analysis" in str(exc_info.value)


@patch('database.get_db_connection')
def test_get_episode_analysis_success(mock_get_conn):
    """Should retrieve episode analysis."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Mock summary query
    mock_cursor.fetchone.return_value = ("Test summary",)

    # Mock topics query
    mock_cursor.fetchall.return_value = [("AI",), ("ML",), ("Ethics",)]

    mock_get_conn.return_value = mock_conn

    result = get_episode_analysis(episode_id=123)

    assert result['summary'] == "Test summary"
    assert result['topics'] == ["AI", "ML", "Ethics"]
    mock_conn.close.assert_called_once()


@patch('database.get_db_connection')
def test_get_episode_analysis_no_data(mock_get_conn):
    """Should handle episode with no analysis."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Mock no summary
    mock_cursor.fetchone.return_value = None

    # Mock no topics
    mock_cursor.fetchall.return_value = []

    mock_get_conn.return_value = mock_conn

    result = get_episode_analysis(episode_id=999)

    assert result['summary'] is None
    assert result['topics'] == []
