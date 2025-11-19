import pytest
from unittest.mock import patch, MagicMock
import os
from psycopg2.extensions import connection as psycopg2_connection
from psycopg2 import OperationalError
from extract_urls import get_rds_connection, get_untranscribed_podcasts


class TestGetRdsConnection:
    """Test suite for get_rds_connection function"""

    @patch('extract_urls.connect')
    def test_get_rds_connection_valid_env_vars(self, mock_connect):
        """Test successful connection with valid environment variables"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_connect.return_value = mock_conn

        with patch.dict(os.environ, {
            'RDS_HOST': 'localhost',
            'RDS_DB_NAME': 'testdb',
            'RDS_USERNAME': 'testuser',
            'RDS_PASSWORD': 'testpass'
        }):
            # Act
            result = get_rds_connection()

            # Assert
            assert result == mock_conn
            mock_connect.assert_called_once_with(
                host='localhost',
                database='testdb',
                user='testuser',
                password='testpass'
            )

    @patch('extract_urls.connect')
    def test_get_rds_connection_correct_parameters(self, mock_connect):
        """Test that connection uses correct parameter names"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_connect.return_value = mock_conn

        with patch.dict(os.environ, {
            'RDS_HOST': 'db.example.com',
            'RDS_DB_NAME': 'production_db',
            'RDS_USERNAME': 'admin',
            'RDS_PASSWORD': 'secure_pass'
        }):
            # Act
            get_rds_connection()

            # Assert
            mock_connect.assert_called_once()
            call_kwargs = mock_connect.call_args.kwargs
            assert 'host' in call_kwargs
            assert 'database' in call_kwargs
            assert 'user' in call_kwargs
            assert 'password' in call_kwargs

    @patch('extract_urls.connect')
    def test_get_rds_connection_connection_error(self, mock_connect):
        """Test that connection errors are propagated"""
        # Arrange
        mock_connect.side_effect = OperationalError("Failed to connect")

        with patch.dict(os.environ, {
            'RDS_HOST': 'invalid_host',
            'RDS_DB_NAME': 'testdb',
            'RDS_USERNAME': 'testuser',
            'RDS_PASSWORD': 'testpass'
        }):
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
            'RDS_PASSWORD': 'testpass'
        }):
            # Act
            result = get_rds_connection()

            # Assert
            assert hasattr(result, 'cursor')
            assert hasattr(result, 'commit')
            assert hasattr(result, 'rollback')
            assert hasattr(result, 'close')

    @patch('extract_urls.connect')
    def test_get_rds_connection_missing_env_var(self, mock_connect):
        """Test that missing environment variables cause error"""
        # Arrange - Provide only partial environment variables
        with patch.dict(os.environ, {
            'RDS_HOST': 'localhost',
            'RDS_DB_NAME': 'testdb'
            # Missing RDS_USERNAME and RDS_PASSWORD
        }, clear=False):
            # Act & Assert
            # This will raise TypeError or similar when None is passed
            mock_connect.side_effect = TypeError(
                "'NoneType' object is not a string")
            with pytest.raises(TypeError):
                get_rds_connection()

    @patch('extract_urls.connect')
    def test_get_rds_connection_with_special_characters(self, mock_connect):
        """Test connection with special characters in credentials"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_connect.return_value = mock_conn

        with patch.dict(os.environ, {
            'RDS_HOST': 'db.us-east-1.rds.amazonaws.com',
            'RDS_DB_NAME': 'prod_db_2024',
            'RDS_USERNAME': 'admin_user',
            'RDS_PASSWORD': 'P@ssw0rd!#$%'
        }):
            # Act
            result = get_rds_connection()

            # Assert
            assert result == mock_conn

    @patch('extract_urls.connect')
    def test_get_rds_connection_with_aws_rds_host(self, mock_connect):
        """Test connection with AWS RDS endpoint"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_connect.return_value = mock_conn

        with patch.dict(os.environ, {
            'RDS_HOST': 'mydb.c9akciq32.us-east-1.rds.amazonaws.com',
            'RDS_DB_NAME': 'postgres',
            'RDS_USERNAME': 'postgres',
            'RDS_PASSWORD': 'mypassword'
        }):
            # Act
            result = get_rds_connection()

            # Assert
            assert result == mock_conn
            mock_connect.assert_called_once()


class TestGetUntranscribedPodcasts:
    """Test suite for get_untranscribed_podcasts function"""

    @patch('extract_urls.connect')
    def test_get_untranscribed_podcasts_returns_list(self, mock_connect):
        """Test that function returns a list of tuples"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        test_data = [
            ('Podcast A', 'Episode 1', 'https://example.com/audio1.mp3'),
            ('Podcast B', 'Episode 2', 'https://example.com/audio2.mp3'),
        ]
        mock_cursor.fetchall.return_value = test_data

        # Act
        result = get_untranscribed_podcasts(mock_conn)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2

    @patch('extract_urls.connect')
    def test_get_untranscribed_podcasts_correct_tuple_structure(
            self, mock_connect):
        """Test that each result tuple has correct structure"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        test_data = [
            ('Podcast Name', 'Episode Title', 'https://example.com/audio.mp3'),
        ]
        mock_cursor.fetchall.return_value = test_data

        # Act
        result = get_untranscribed_podcasts(mock_conn)

        # Assert
        assert result[0] == ('Podcast Name', 'Episode Title',
                             'https://example.com/audio.mp3')

    @patch('extract_urls.connect')
    def test_get_untranscribed_podcasts_empty_result(self, mock_connect):
        """Test that function handles empty result set"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        mock_cursor.fetchall.return_value = []

        # Act
        result = get_untranscribed_podcasts(mock_conn)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    @patch('extract_urls.connect')
    def test_get_untranscribed_podcasts_sql_query_correct(
            self, mock_connect):
        """Test that correct SQL query is executed"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        mock_cursor.fetchall.return_value = []

        # Act
        get_untranscribed_podcasts(mock_conn)

        # Assert
        executed_query = mock_cursor.execute.call_args[0][0]
        assert 'SELECT' in executed_query
        assert 'p.podcast_name' in executed_query
        assert 'e.episode_title' in executed_query
        assert 'e.audio_url' in executed_query
        assert 'WHERE e.transcribed = FALSE' in executed_query

    @patch('extract_urls.connect')
    def test_get_untranscribed_podcasts_multiple_results(
            self, mock_connect):
        """Test function with multiple results"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        test_data = [
            ('Podcast A', 'Episode 1', 'https://example.com/audio1.mp3'),
            ('Podcast B', 'Episode 2', 'https://example.com/audio2.mp3'),
            ('Podcast C', 'Episode 3', 'https://example.com/audio3.mp3'),
            ('Podcast A', 'Episode 4', 'https://example.com/audio4.mp3'),
        ]
        mock_cursor.fetchall.return_value = test_data

        # Act
        result = get_untranscribed_podcasts(mock_conn)

        # Assert
        assert len(result) == 4
        assert all(isinstance(item, tuple) for item in result)

    @patch('extract_urls.connect')
    def test_get_untranscribed_podcasts_cursor_context_manager(
            self, mock_connect):
        """Test that cursor is used as context manager"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        mock_cursor.fetchall.return_value = []

        # Act
        get_untranscribed_podcasts(mock_conn)

        # Assert
        mock_conn.cursor.assert_called_once()
        mock_conn.cursor.return_value.__enter__.assert_called_once()
        mock_conn.cursor.return_value.__exit__.assert_called_once()

    @patch('extract_urls.connect')
    def test_get_untranscribed_podcasts_with_special_characters_in_urls(
            self, mock_connect):
        """Test function with special characters in URLs"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False)

        test_data = [
            ('Podcast & Co', 'Episode #1: Test',
             'https://example.com/audio?id=123&token=abc'),
        ]
        mock_cursor.fetchall.return_value = test_data

        # Act
        result = get_untranscribed_podcasts(mock_conn)

        # Assert
        assert len(result) == 1
        assert result[0][0] == 'Podcast & Co'
        assert result[0][1] == 'Episode #1: Test'
