import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from psycopg2.extensions import connection as psycopg2_connection
from psycopg2 import OperationalError

# Mock boto3 before importing extract_urls
sys.modules['boto3'] = MagicMock()

from extract_urls import get_rds_connection, get_untranscribed_episode, update_episode_transcribed


class TestGetRdsConnection:
    """Test suite for get_rds_connection function"""

    @patch('extract_urls.connect')
    def test_get_rds_connection_local_env_vars(self, mock_connect):
        """Test successful connection with local environment variables"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_connect.return_value = mock_conn

        with patch.dict(os.environ, {
            'RDS_HOST': 'localhost',
            'RDS_DB_NAME': 'testdb',
            'RDS_USERNAME': 'testuser',
            'RDS_PASSWORD': 'testpass',
            'USE_SECRETS_MANAGER': 'false'
        }, clear=False):
            # Act
            result = get_rds_connection()

            # Assert
            assert result == mock_conn
            mock_connect.assert_called_once_with(
                host='localhost',
                database='testdb',
                user='testuser',
                password='testpass',
                port=5432
            )

    @patch('extract_urls.connect')
    def test_get_rds_connection_with_custom_port(self, mock_connect):
        """Test connection with custom RDS port"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_connect.return_value = mock_conn

        with patch.dict(os.environ, {
            'RDS_HOST': 'db.example.com',
            'RDS_DB_NAME': 'production_db',
            'RDS_USERNAME': 'admin',
            'RDS_PASSWORD': 'secure_pass',
            'RDS_PORT': '5433',
            'USE_SECRETS_MANAGER': 'false'
        }, clear=False):
            # Act
            result = get_rds_connection()

            # Assert
            assert result == mock_conn
            mock_connect.assert_called_once_with(
                host='db.example.com',
                database='production_db',
                user='admin',
                password='secure_pass',
                port=5433
            )

    @patch('extract_urls.get_secret')
    @patch('extract_urls.connect')
    def test_get_rds_connection_with_secrets_manager(self, mock_connect, mock_get_secret):
        """Test connection using AWS Secrets Manager"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_connect.return_value = mock_conn
        mock_get_secret.return_value = {
            'RDS_HOST': 'secrets-host.rds.amazonaws.com',
            'RDS_DB_NAME': 'secrets_db',
            'RDS_USERNAME': 'secrets_user',
            'RDS_PASSWORD': 'secrets_pass',
            'RDS_PORT': '5432'
        }

        with patch.dict(os.environ, {
            'USE_SECRETS_MANAGER': 'true'
        }, clear=False):
            # Act
            result = get_rds_connection()

            # Assert
            assert result == mock_conn
            mock_get_secret.assert_called_once()
            mock_connect.assert_called_once_with(
                host='secrets-host.rds.amazonaws.com',
                database='secrets_db',
                user='secrets_user',
                password='secrets_pass',
                port=5432
            )

    @patch('extract_urls.connect')
    def test_get_rds_connection_connection_error(self, mock_connect):
        """Test that connection errors are propagated"""

        # Arrange
        mock_connect.side_effect = OperationalError("Failed to connect")

        with patch.dict(os.environ, {
            'RDS_HOST': 'invalid_host',
            'RDS_DB_NAME': 'testdb',
            'RDS_USERNAME': 'testuser',
            'RDS_PASSWORD': 'testpass',
            'USE_SECRETS_MANAGER': 'false'
        }, clear=False):
            # Act & Assert
            with pytest.raises(OperationalError):
                get_rds_connection()

    @patch('extract_urls.connect')
    def test_get_rds_connection_returns_connection_object(self, mock_connect):
        """Test that function returns a connection object"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_connect.return_value = mock_conn

        with patch.dict(os.environ, {
            'RDS_HOST': 'localhost',
            'RDS_DB_NAME': 'testdb',
            'RDS_USERNAME': 'testuser',
            'RDS_PASSWORD': 'testpass',
            'USE_SECRETS_MANAGER': 'false'
        }, clear=False):
            # Act
            result = get_rds_connection()

            # Assert
            assert hasattr(result, 'cursor')
            assert hasattr(result, 'commit')
            assert hasattr(result, 'rollback')
            assert hasattr(result, 'close')


class TestGetUntranscribedEpisode:
    """Test suite for get_untranscribed_episode function"""

    @patch('extract_urls.connect')
    def test_get_untranscribed_episode_returns_dict(self, _):
        """Test that function returns a dictionary"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        mock_cursor.fetchone.return_value = (
            1, 10, 'Podcast Name', 'Episode Title', 'https://example.com/audio.mp3'
        )

        # Act
        result = get_untranscribed_episode(mock_conn)

        # Assert
        assert isinstance(result, dict)

    @patch('extract_urls.connect')
    def test_get_untranscribed_episode_correct_structure(self, _):
        """Test that returned dict has correct keys"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        mock_cursor.fetchone.return_value = (
            1, 10, 'Test Podcast', 'Test Episode', 'https://example.com/audio.mp3'
        )

        # Act
        result = get_untranscribed_episode(mock_conn)

        # Assert
        assert result['episode_id'] == 1
        assert result['podcast_id'] == 10
        assert result['podcast_name'] == 'Test Podcast'
        assert result['episode_title'] == 'Test Episode'
        assert result['audio_url'] == 'https://example.com/audio.mp3'

    @patch('extract_urls.connect')
    def test_get_untranscribed_episode_no_results(self, _):
        """Test that function returns None when no results"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        mock_cursor.fetchone.return_value = None

        # Act
        result = get_untranscribed_episode(mock_conn)

        # Assert
        assert result is None

    @patch('extract_urls.connect')
    def test_get_untranscribed_episode_sql_query_correct(self, _):
        """Test that correct SQL query is executed"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        mock_cursor.fetchone.return_value = None

        # Act
        get_untranscribed_episode(mock_conn)

        # Assert
        executed_query = mock_cursor.execute.call_args[0][0]
        assert 'SELECT' in executed_query
        assert 'e.episode_id' in executed_query
        assert 'p.podcast_id' in executed_query
        assert 'p.podcast_name' in executed_query
        assert 'e.episode_title' in executed_query
        assert 'e.audio_url' in executed_query
        assert 'WHERE e.transcribed = FALSE' in executed_query
        assert 'LIMIT 1' in executed_query

    @patch('extract_urls.connect')
    def test_get_untranscribed_episode_cursor_context_manager(self, _):
        """Test that cursor is used as context manager"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        mock_cursor.fetchone.return_value = None

        # Act
        get_untranscribed_episode(mock_conn)

        # Assert
        mock_conn.cursor.assert_called_once()
        mock_conn.cursor.return_value.__enter__.assert_called_once()
        mock_conn.cursor.return_value.__exit__.assert_called_once()

    @patch('extract_urls.connect')
    def test_get_untranscribed_episode_with_special_characters(self, _):
        """Test function with special characters in data"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        mock_cursor.fetchone.return_value = (
            1, 5, 'Podcast & Co', 'Episode #1: "Test"',
            'https://example.com/audio?id=123&token=abc'
        )

        # Act
        result = get_untranscribed_episode(mock_conn)

        # Assert
        assert result['podcast_name'] == 'Podcast & Co'
        assert result['episode_title'] == 'Episode #1: "Test"'
        assert result['audio_url'] == 'https://example.com/audio?id=123&token=abc'


class TestUpdateEpisodeTranscribed:
    """Test suite for update_episode_transcribed function"""

    @patch('extract_urls.connect')
    def test_update_episode_transcribed_executes_query(self, _):
        """Test that SQL UPDATE query is executed"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        # Act
        update_episode_transcribed(mock_conn, 123)

        # Assert
        mock_cursor.execute.assert_called_once()
        executed_query = mock_cursor.execute.call_args[0][0]
        assert 'UPDATE episode' in executed_query
        assert 'SET transcribed = TRUE' in executed_query
        assert 'WHERE episode_id = %s' in executed_query

    @patch('extract_urls.connect')
    def test_update_episode_transcribed_correct_parameter(self, _):
        """Test that correct episode_id parameter is passed"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        episode_id = 456

        # Act
        update_episode_transcribed(mock_conn, episode_id)

        # Assert
        call_args = mock_cursor.execute.call_args
        assert call_args[0][1] == (episode_id,)

    @patch('extract_urls.connect')
    def test_update_episode_transcribed_commits_transaction(self, _):
        """Test that transaction is committed"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        # Act
        update_episode_transcribed(mock_conn, 789)

        # Assert
        mock_conn.commit.assert_called_once()

    @patch('extract_urls.connect')
    def test_update_episode_transcribed_cursor_context_manager(self, _):
        """Test that cursor is used as context manager"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        # Act
        update_episode_transcribed(mock_conn, 999)

        # Assert
        mock_conn.cursor.assert_called_once()
        mock_conn.cursor.return_value.__enter__.assert_called_once()
        mock_conn.cursor.return_value.__exit__.assert_called_once()

    @patch('extract_urls.connect')
    def test_update_episode_transcribed_multiple_episodes(self, _):
        """Test updating multiple episodes sequentially"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        # Act
        update_episode_transcribed(mock_conn, 1)
        update_episode_transcribed(mock_conn, 2)
        update_episode_transcribed(mock_conn, 3)

        # Assert
        assert mock_cursor.execute.call_count == 3
        assert mock_conn.commit.call_count == 3
