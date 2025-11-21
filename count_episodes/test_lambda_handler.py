"""Tests for count_episodes Lambda handler."""
import pytest
from unittest.mock import patch, MagicMock
import json
import os
from psycopg2.extensions import connection as psycopg2_connection
from lambda_handler import (
    get_rds_connection,
    count_untranscribed_episodes,
    lambda_handler
)


class TestGetRdsConnection:
    """Test suite for get_rds_connection function"""

    @patch('lambda_handler.connect')
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

    @patch('lambda_handler.get_secret')
    @patch('lambda_handler.connect')
    def test_get_rds_connection_secrets_manager(self, mock_connect, mock_get_secret):
        """Test connection using AWS Secrets Manager"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_connect.return_value = mock_conn
        mock_get_secret.return_value = {
            'RDS_HOST': 'prod.db.amazonaws.com',
            'RDS_DB_NAME': 'proddb',
            'RDS_USERNAME': 'produser',
            'RDS_PASSWORD': 'prodpass',
            'RDS_PORT': '5432'
        }

        with patch.dict(os.environ, {'USE_SECRETS_MANAGER': 'true'}, clear=False):
            # Act
            result = get_rds_connection()

            # Assert
            assert result == mock_conn
            mock_get_secret.assert_called_once()
            mock_connect.assert_called_once_with(
                host='prod.db.amazonaws.com',
                database='proddb',
                user='produser',
                password='prodpass',
                port=5432
            )


class TestCountUntranscribedEpisodes:
    """Test suite for count_untranscribed_episodes function"""

    def test_count_returns_zero_when_no_episodes(self):
        """Test counting when no episodes exist"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (0,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Act
        result = count_untranscribed_episodes(mock_conn)

        # Assert
        assert result == 0
        mock_cursor.execute.assert_called_once()
        assert "WHERE transcribed = FALSE" in mock_cursor.execute.call_args[0][0]

    def test_count_returns_correct_number(self):
        """Test counting multiple untranscribed episodes"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (15,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Act
        result = count_untranscribed_episodes(mock_conn)

        # Assert
        assert result == 15
        mock_cursor.execute.assert_called_once()

    def test_count_handles_null_result(self):
        """Test counting when query returns None"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Act
        result = count_untranscribed_episodes(mock_conn)

        # Assert
        assert result == 0


class TestLambdaHandler:
    """Test suite for lambda_handler function"""

    @patch('lambda_handler.get_rds_connection')
    @patch('lambda_handler.count_untranscribed_episodes')
    def test_lambda_handler_success(self, mock_count, mock_get_conn):
        """Test successful lambda execution"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_get_conn.return_value = mock_conn
        mock_count.return_value = 42

        # Act
        result = lambda_handler({}, None)

        # Assert
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['count'] == 42
        mock_conn.close.assert_called_once()

    @patch('lambda_handler.get_rds_connection')
    @patch('lambda_handler.count_untranscribed_episodes')
    def test_lambda_handler_zero_episodes(self, mock_count, mock_get_conn):
        """Test lambda execution when no episodes need transcription"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_get_conn.return_value = mock_conn
        mock_count.return_value = 0

        # Act
        result = lambda_handler({}, None)

        # Assert
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['count'] == 0
        mock_conn.close.assert_called_once()

    @patch('lambda_handler.get_rds_connection')
    def test_lambda_handler_database_error(self, mock_get_conn):
        """Test lambda execution with database error"""

        # Arrange
        mock_get_conn.side_effect = Exception("Database connection failed")

        # Act
        result = lambda_handler({}, None)

        # Assert
        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert 'error' in body
        assert 'Failed to count episodes' in body['error']

    @patch('lambda_handler.get_rds_connection')
    @patch('lambda_handler.count_untranscribed_episodes')
    def test_lambda_handler_closes_connection_on_error(self, mock_count, mock_get_conn):
        """Test that connection is closed even when counting fails"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_get_conn.return_value = mock_conn
        mock_count.side_effect = Exception("Count failed")

        # Act
        result = lambda_handler({}, None)

        # Assert
        assert result['statusCode'] == 500
        mock_conn.close.assert_called_once()
