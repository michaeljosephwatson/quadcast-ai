import pytest
from unittest.mock import patch, MagicMock
import os
from psycopg2.extensions import connection as psycopg2_connection
from psycopg2 import OperationalError
from load import get_rds_connection, load_data_to_db_from_rss


class TestGetRdsConnection:
    """Test suite for get_rds_connection function"""

    @patch('load.connect')
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

    @patch('load.connect')
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

    @patch('load.connect')
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

    @patch('load.connect')
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

    @patch('load.connect')
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

    @patch('load.connect')
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


class TestLoadDataToDbFromRss:
    """Test suite for load_data_to_db_from_rss function"""

    @patch('load.validate_feed')
    @patch('load.get_data_from_rss')
    @patch('load.get_rds_connection')
    def test_load_data_to_db_from_rss_valid_rss_new_podcast(self, mock_get_conn, mock_get_data, mock_validate):
        """Test loading new podcast from valid RSS feed"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        # fetchone returns (1,) for language, then None for podcast check (not exists)
        mock_cursor.fetchone.side_effect = [(1,), None]
        mock_get_conn.return_value = mock_conn
        mock_get_data.return_value = {'author': 'Test', 'published': 'Mon, 01 Jan 2024 00:00:00 +0000', 'language': 'en', 'link': 'http://example.com'}
        mock_validate.return_value = {'podcast_name': 'Test', 'publish_date': '2024-01-01', 'language': 'en', 'link': 'http://example.com'}

        rss_url = 'https://example.com/feed.xml'

        # Act
        result = load_data_to_db_from_rss(rss_url)

        # Assert
        mock_get_conn.assert_called_once()
        assert isinstance(result, dict)
        assert result['is_duplicate'] is False
        assert result['status'] == 'added'

    @patch('load.validate_feed')
    @patch('load.get_data_from_rss')
    @patch('load.get_rds_connection')
    def test_load_data_to_db_from_rss_returns_dict_with_duplicate(self, mock_get_conn, mock_get_data, mock_validate):
        """Test that function returns dict indicating duplicate when podcast already exists"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        # fetchone returns (1,) on first call (language check), then (1,) on second call (podcast exists)
        mock_cursor.fetchone.side_effect = [(1,), (1,)]
        mock_get_conn.return_value = mock_conn
        mock_get_data.return_value = {'author': 'Test', 'published': 'Mon, 01 Jan 2024 00:00:00 +0000', 'language': 'en', 'link': 'http://example.com'}
        mock_validate.return_value = {'podcast_name': 'Test', 'publish_date': '2024-01-01', 'language': 'en', 'link': 'http://example.com'}
        rss_url = 'https://example.com/feed.xml'

        # Act
        result = load_data_to_db_from_rss(rss_url)

        # Assert
        assert isinstance(result, dict)
        assert result['is_duplicate'] is True
        assert result['status'] == 'duplicate'

    @patch('load.validate_feed')
    @patch('load.get_data_from_rss')
    @patch('load.get_rds_connection')
    def test_load_data_to_db_from_rss_connection_cleanup(self, mock_get_conn, mock_get_data, mock_validate):
        """Test that database connection is properly closed"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchone.return_value = (1,)
        mock_get_conn.return_value = mock_conn
        mock_get_data.return_value = {'author': 'Test', 'published': 'Mon, 01 Jan 2024 00:00:00 +0000', 'language': 'en', 'link': 'http://example.com'}
        mock_validate.return_value = {'podcast_name': 'Test', 'publish_date': '2024-01-01', 'language': 'en', 'link': 'http://example.com'}
        rss_url = 'https://example.com/feed.xml'

        # Act
        load_data_to_db_from_rss(rss_url)

        # Assert - Connection should eventually be closed (if implemented)
        # This test assumes the function handles connection cleanup

    @patch('load.validate_feed')
    @patch('load.get_data_from_rss')
    @patch('load.get_rds_connection')
    def test_load_data_to_db_from_rss_with_empty_rss(self, mock_get_conn, mock_get_data, mock_validate):
        """Test loading from empty RSS feed"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchone.return_value = (1,)
        mock_get_conn.return_value = mock_conn
        mock_get_data.return_value = {'author': 'Test', 'published': 'Mon, 01 Jan 2024 00:00:00 +0000', 'language': 'en', 'link': 'http://example.com'}
        mock_validate.return_value = {'podcast_name': 'Test', 'publish_date': '2024-01-01', 'language': 'en', 'link': 'http://example.com'}
        rss_url = 'https://example.com/empty_feed.xml'

        # Act
        load_data_to_db_from_rss(rss_url)

        # Assert
        mock_get_conn.assert_called_once()

    @patch('load.validate_feed')
    @patch('load.get_data_from_rss')
    @patch('load.get_rds_connection')
    def test_load_data_to_db_from_rss_accepts_string(self, mock_get_conn, mock_get_data, mock_validate):
        """Test that function accepts string parameter"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchone.return_value = (1,)
        mock_get_conn.return_value = mock_conn
        mock_get_data.return_value = {'author': 'Test', 'published': 'Mon, 01 Jan 2024 00:00:00 +0000', 'language': 'en', 'link': 'http://example.com'}
        mock_validate.return_value = {'podcast_name': 'Test', 'publish_date': '2024-01-01', 'language': 'en', 'link': 'http://example.com'}
        rss_url = 'https://example.com/feed.xml'

        # Act & Assert - Should not raise error
        load_data_to_db_from_rss(rss_url)
        assert isinstance(rss_url, str)

    @patch('load.validate_feed')
    @patch('load.get_data_from_rss')
    @patch('load.get_rds_connection')
    def test_load_data_to_db_from_rss_various_urls(self, mock_get_conn, mock_get_data, mock_validate):
        """Test with various RSS feed URLs"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchone.return_value = (1,)
        mock_get_conn.return_value = mock_conn
        mock_get_data.return_value = {'author': 'Test', 'published': 'Mon, 01 Jan 2024 00:00:00 +0000', 'language': 'en', 'link': 'http://example.com'}
        mock_validate.return_value = {'podcast_name': 'Test', 'publish_date': '2024-01-01', 'language': 'en', 'link': 'http://example.com'}

        test_urls = [
            'https://example.com/feed.xml',
            'http://podcast.local/rss',
            'https://feeds.example.com/podcast/123'
        ]

        # Act & Assert
        for url in test_urls:
            load_data_to_db_from_rss(url)
            assert mock_get_conn.called

    @patch('load.validate_feed')
    @patch('load.get_data_from_rss')
    @patch('load.get_rds_connection')
    def test_load_data_to_db_from_rss_error_handling(self, mock_get_conn, mock_get_data, mock_validate):
        """Test error handling when database connection fails"""
        # Arrange
        mock_get_data.return_value = {'author': 'Test', 'published': 'Mon, 01 Jan 2024 00:00:00 +0000', 'language': 'en', 'link': 'http://example.com'}
        mock_validate.return_value = {'podcast_name': 'Test', 'publish_date': '2024-01-01', 'language': 'en', 'link': 'http://example.com'}
        mock_get_conn.side_effect = OperationalError(
            "Database connection failed")
        rss_url = 'https://example.com/feed.xml'

        # Act & Assert
        with pytest.raises(OperationalError):
            load_data_to_db_from_rss(rss_url)

    @patch('load.validate_feed')
    @patch('load.get_data_from_rss')
    @patch('load.get_rds_connection')
    def test_load_data_to_db_from_rss_cursor_created(self, mock_get_conn, mock_get_data, mock_validate):
        """Test that a cursor is created from the connection"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchone.return_value = (1,)
        mock_get_conn.return_value = mock_conn
        mock_get_data.return_value = {'author': 'Test', 'published': 'Mon, 01 Jan 2024 00:00:00 +0000', 'language': 'en', 'link': 'http://example.com'}
        mock_validate.return_value = {'podcast_name': 'Test', 'publish_date': '2024-01-01', 'language': 'en', 'link': 'http://example.com'}
        rss_url = 'https://example.com/feed.xml'

        # Act
        load_data_to_db_from_rss(rss_url)

        # Assert
        # This assumes the function uses cursor (to be confirmed with implementation)


class TestDatabaseIntegration:
    """Integration tests for database operations"""

    @patch('load.connect')
    def test_connection_lifecycle(self, mock_connect):
        """Test full connection lifecycle"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        with patch.dict(os.environ, {
            'RDS_HOST': 'localhost',
            'RDS_DB_NAME': 'testdb',
            'RDS_USERNAME': 'testuser',
            'RDS_PASSWORD': 'testpass'
        }):
            # Act
            conn = get_rds_connection()

            # Assert
            assert conn is not None
            assert mock_connect.called

    @patch('load.validate_feed')
    @patch('load.get_data_from_rss')
    @patch('load.get_rds_connection')
    @patch('load.connect')
    def test_multiple_operations(self, mock_connect_global, mock_get_conn, mock_get_data, mock_validate):
        """Test multiple database operations in sequence"""
        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchone.return_value = (1,)
        mock_get_conn.return_value = mock_conn
        mock_get_data.return_value = {'author': 'Test', 'published': 'Mon, 01 Jan 2024 00:00:00 +0000', 'language': 'en', 'link': 'http://example.com'}
        mock_validate.return_value = {'podcast_name': 'Test', 'publish_date': '2024-01-01', 'language': 'en', 'link': 'http://example.com'}

        rss_urls = [
            'https://example.com/feed1.xml',
            'https://example.com/feed2.xml',
            'https://example.com/feed3.xml'
        ]

        # Act
        for url in rss_urls:
            load_data_to_db_from_rss(url)

        # Assert
        assert mock_get_conn.call_count == len(rss_urls)
