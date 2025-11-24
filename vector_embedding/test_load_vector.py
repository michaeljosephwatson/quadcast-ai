"""Unit tests for load.py module."""
import pytest
from unittest.mock import patch, MagicMock
from psycopg2.extensions import connection
import psycopg2

from vector_embedding.load import (
    get_db_connection,
    episode_exists,
    clear_existing_embeddings,
    insert_embeddings,
    load_embeddings
)


class TestGetDbConnection:
    """Test suite for get_db_connection function"""

    @patch.dict('os.environ', {
        'RDS_HOST': 'test-host.rds.amazonaws.com',
        'RDS_DB_NAME': 'test_db',
        'RDS_USERNAME': 'admin',
        'RDS_PASSWORD': 'password123',
        'RDS_PORT': '5432'
    }, clear=False)
    @patch('vector_embedding.load.psycopg2.connect')
    def test_get_db_connection_success(self, mock_connect):
        """Test successful database connection"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_connect.return_value = mock_conn

        # Act
        result = get_db_connection()

        # Assert
        assert result == mock_conn
        # Verify the connect method was called
        assert mock_connect.called

    @patch.dict('os.environ', {
        'RDS_HOST': 'localhost',
        'RDS_DB_NAME': 'embedding_db',
        'RDS_USERNAME': 'user',
        'RDS_PASSWORD': 'pass',
        'RDS_PORT': '5432'
    }, clear=False)
    @patch('vector_embedding.load.psycopg2.connect')
    def test_get_db_connection_with_different_env(self, mock_connect):
        """Test connection uses environment variables correctly"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_connect.return_value = mock_conn

        # Act
        get_db_connection()

        # Assert
        # Verify the connect method was called
        assert mock_connect.called

    @patch.dict('os.environ', {
        'RDS_HOST': 'test-host',
        'RDS_DB_NAME': 'test_db',
        'RDS_USERNAME': 'admin',
        'RDS_PASSWORD': 'password',
    }, clear=True)
    @patch('vector_embedding.load.psycopg2.connect')
    def test_get_db_connection_default_port(self, mock_connect):
        """Test connection uses default port when RDS_PORT not set"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_connect.return_value = mock_conn

        # Act
        get_db_connection()

        # Assert
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs['port'] == 5432

    @patch.dict('os.environ', {
        'RDS_HOST': 'test-host',
        'RDS_DB_NAME': 'test_db',
        'RDS_USERNAME': 'admin',
        'RDS_PASSWORD': 'password',
        'RDS_PORT': '5432'
    })
    @patch('vector_embedding.load.psycopg2.connect')
    def test_get_db_connection_failure(self, mock_connect):
        """Test connection failure is raised"""
        # Arrange
        mock_connect.side_effect = psycopg2.OperationalError(
            "Connection failed")

        # Act & Assert
        with pytest.raises(psycopg2.OperationalError):
            get_db_connection()


class TestEpisodeExists:
    """Test suite for episode_exists function"""

    def test_episode_exists_true(self):
        """Test episode_exists returns True when episode found"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)

        # Act
        result = episode_exists(mock_conn, 123)

        # Assert
        assert result is True
        mock_cursor.execute.assert_called_once_with(
            "SELECT 1 FROM episode WHERE episode_id = %s",
            (123,)
        )

    def test_episode_exists_false(self):
        """Test episode_exists returns False when episode not found"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        # Act
        result = episode_exists(mock_conn, 999)

        # Assert
        assert result is False

    def test_episode_exists_database_error(self):
        """Test episode_exists propagates database errors"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.DatabaseError(
            "Query failed")

        # Act & Assert
        with pytest.raises(psycopg2.DatabaseError):
            episode_exists(mock_conn, 123)

    def test_episode_exists_multiple_calls(self):
        """Test episode_exists works with multiple calls"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = [(1,), None, (1,)]

        # Act
        result1 = episode_exists(mock_conn, 1)
        result2 = episode_exists(mock_conn, 2)
        result3 = episode_exists(mock_conn, 3)

        # Assert
        assert result1 is True
        assert result2 is False
        assert result3 is True


class TestClearExistingEmbeddings:
    """Test suite for clear_existing_embeddings function"""

    def test_clear_existing_embeddings_success(self):
        """Test successfully clearing embeddings for episode"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Act
        clear_existing_embeddings(mock_conn, 42)

        # Assert
        mock_cursor.execute.assert_called_once_with(
            "DELETE FROM episode_embedding WHERE episode_id = %s",
            (42,)
        )

    def test_clear_existing_embeddings_different_episodes(self):
        """Test clearing embeddings for different episode IDs"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Act
        clear_existing_embeddings(mock_conn, 100)
        clear_existing_embeddings(mock_conn, 200)

        # Assert
        assert mock_cursor.execute.call_count == 2
        calls = mock_cursor.execute.call_args_list
        assert calls[0][0][1] == (100,)
        assert calls[1][0][1] == (200,)

    def test_clear_existing_embeddings_no_match(self):
        """Test clearing embeddings when none exist"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Act - should not raise error even if no rows deleted
        clear_existing_embeddings(mock_conn, 999)

        # Assert
        mock_cursor.execute.assert_called_once()

    def test_clear_existing_embeddings_database_error(self):
        """Test database errors are propagated"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.DatabaseError(
            "Delete failed")

        # Act & Assert
        with pytest.raises(psycopg2.DatabaseError):
            clear_existing_embeddings(mock_conn, 42)


class TestInsertEmbeddings:
    """Test suite for insert_embeddings function"""

    @patch('vector_embedding.load.execute_values')
    def test_insert_embeddings_success(self, mock_execute_values):
        """Test successfully inserting embeddings"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        embedded_chunks = [
            {
                'embedding': [0.1] * 1536,
                'chunk_index': 0,
                'chunk_text': 'First chunk'
            },
            {
                'embedding': [0.2] * 1536,
                'chunk_index': 1,
                'chunk_text': 'Second chunk'
            }
        ]

        # Act
        insert_embeddings(mock_conn, 42, embedded_chunks)

        # Assert
        mock_execute_values.assert_called_once()

    @patch('vector_embedding.load.execute_values')
    def test_insert_embeddings_single_chunk(self, mock_execute_values):
        """Test inserting a single embedding"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        embedded_chunks = [
            {
                'embedding': [0.1] * 1536,
                'chunk_index': 0,
                'chunk_text': 'Single chunk'
            }
        ]

        # Act
        insert_embeddings(mock_conn, 10, embedded_chunks)

        # Assert
        mock_execute_values.assert_called_once()

    @patch('vector_embedding.load.execute_values')
    def test_insert_embeddings_many_chunks(self, mock_execute_values):
        """Test inserting many embeddings"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        embedded_chunks = [
            {
                'embedding': [float(i) / 1536] * 1536,
                'chunk_index': i,
                'chunk_text': f'Chunk {i}'
            }
            for i in range(100)
        ]

        # Act
        insert_embeddings(mock_conn, 50, embedded_chunks)

        # Assert
        mock_execute_values.assert_called_once()

    @patch('vector_embedding.load.execute_values')
    def test_insert_embeddings_database_error(self, mock_execute_values):
        """Test database errors during insert"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_execute_values.side_effect = psycopg2.DatabaseError(
            "Insert failed")

        embedded_chunks = [
            {
                'embedding': [0.1] * 1536,
                'chunk_index': 0,
                'chunk_text': 'Chunk'
            }
        ]

        # Act & Assert
        with pytest.raises(psycopg2.DatabaseError):
            insert_embeddings(mock_conn, 42, embedded_chunks)

    @patch('vector_embedding.load.execute_values')
    def test_insert_embeddings_preserves_order(self, mock_execute_values):
        """Test embeddings are inserted in correct order"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        embedded_chunks = [
            {
                'embedding': [0.1] * 1536,
                'chunk_index': 0,
                'chunk_text': 'First'
            },
            {
                'embedding': [0.2] * 1536,
                'chunk_index': 1,
                'chunk_text': 'Second'
            },
            {
                'embedding': [0.3] * 1536,
                'chunk_index': 2,
                'chunk_text': 'Third'
            }
        ]

        # Act
        insert_embeddings(mock_conn, 42, embedded_chunks)

        # Assert
        mock_execute_values.assert_called_once()


class TestLoadEmbeddings:
    """Test suite for load_embeddings function"""

    @patch('vector_embedding.load.get_db_connection')
    @patch('vector_embedding.load.episode_exists')
    @patch('vector_embedding.load.clear_existing_embeddings')
    @patch('vector_embedding.load.insert_embeddings')
    def test_load_embeddings_success(self, mock_insert, mock_clear, mock_exists, mock_get_conn):
        """Test successfully loading embeddings"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_get_conn.return_value = mock_conn
        mock_exists.return_value = True

        embedded_chunks = [
            {
                'embedding': [0.1] * 1536,
                'chunk_index': 0,
                'chunk_text': 'Chunk'
            }
        ]

        # Act
        result = load_embeddings(42, embedded_chunks)

        # Assert
        assert result is True
        mock_get_conn.assert_called_once()
        mock_exists.assert_called_once_with(mock_conn, 42)
        mock_clear.assert_called_once_with(mock_conn, 42)
        mock_insert.assert_called_once_with(mock_conn, 42, embedded_chunks)
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('vector_embedding.load.get_db_connection')
    def test_load_embeddings_empty_chunks(self, mock_get_conn):
        """Test load_embeddings raises error for empty chunks"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_get_conn.return_value = mock_conn

        # Act & Assert
        with pytest.raises(ValueError, match="embedded_chunks cannot be empty"):
            load_embeddings(42, [])

    @patch('vector_embedding.load.get_db_connection')
    def test_load_embeddings_missing_embedding_field(self, mock_get_conn):
        """Test load_embeddings raises error when embedding field missing"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_get_conn.return_value = mock_conn

        embedded_chunks = [
            {
                'chunk_index': 0,
                'chunk_text': 'Chunk'
                # Missing 'embedding' field
            }
        ]

        # Act & Assert
        with pytest.raises(ValueError, match="All chunks must have 'embedding' field"):
            load_embeddings(42, embedded_chunks)

    @patch('vector_embedding.load.get_db_connection')
    @patch('vector_embedding.load.episode_exists')
    def test_load_embeddings_episode_not_found(self, mock_exists, mock_get_conn):
        """Test load_embeddings raises error when episode doesn't exist"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_get_conn.return_value = mock_conn
        mock_exists.return_value = False

        embedded_chunks = [
            {
                'embedding': [0.1] * 1536,
                'chunk_index': 0,
                'chunk_text': 'Chunk'
            }
        ]

        # Act & Assert
        with pytest.raises(Exception, match="Failed to load embeddings"):
            load_embeddings(999, embedded_chunks)

        # Verify connection is closed on error
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('vector_embedding.load.get_db_connection')
    @patch('vector_embedding.load.episode_exists')
    @patch('vector_embedding.load.clear_existing_embeddings')
    @patch('vector_embedding.load.insert_embeddings')
    def test_load_embeddings_insert_failure(self, mock_insert, mock_clear, mock_exists, mock_get_conn):
        """Test load_embeddings handles insert failure"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_get_conn.return_value = mock_conn
        mock_exists.return_value = True
        mock_insert.side_effect = Exception("Insert error")

        embedded_chunks = [
            {
                'embedding': [0.1] * 1536,
                'chunk_index': 0,
                'chunk_text': 'Chunk'
            }
        ]

        # Act & Assert
        with pytest.raises(Exception, match="Failed to load embeddings"):
            load_embeddings(42, embedded_chunks)

        # Verify rollback and close called
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('vector_embedding.load.get_db_connection')
    @patch('vector_embedding.load.episode_exists')
    @patch('vector_embedding.load.clear_existing_embeddings')
    @patch('vector_embedding.load.insert_embeddings')
    def test_load_embeddings_multiple_chunks(self, mock_insert, mock_clear, mock_exists, mock_get_conn):
        """Test loading multiple embedded chunks"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_get_conn.return_value = mock_conn
        mock_exists.return_value = True

        embedded_chunks = [
            {
                'embedding': [float(i) / 1536] * 1536,
                'chunk_index': i,
                'chunk_text': f'Chunk {i}'
            }
            for i in range(10)
        ]

        # Act
        result = load_embeddings(42, embedded_chunks)

        # Assert
        assert result is True
        mock_insert.assert_called_once_with(mock_conn, 42, embedded_chunks)
        mock_conn.commit.assert_called_once()

    @patch('vector_embedding.load.get_db_connection')
    @patch('vector_embedding.load.episode_exists')
    @patch('vector_embedding.load.clear_existing_embeddings')
    @patch('vector_embedding.load.insert_embeddings')
    def test_load_embeddings_connection_always_closed(self, mock_insert, mock_clear, mock_exists, mock_get_conn):
        """Test database connection is always closed, even on error"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_get_conn.return_value = mock_conn
        mock_exists.return_value = True
        mock_clear.side_effect = Exception("Clear error")

        embedded_chunks = [
            {
                'embedding': [0.1] * 1536,
                'chunk_index': 0,
                'chunk_text': 'Chunk'
            }
        ]

        # Act & Assert
        with pytest.raises(Exception):
            load_embeddings(42, embedded_chunks)

        # Verify close was called in finally block
        mock_conn.close.assert_called_once()

    @patch('vector_embedding.load.get_db_connection')
    @patch('vector_embedding.load.episode_exists')
    @patch('vector_embedding.load.clear_existing_embeddings')
    @patch('vector_embedding.load.insert_embeddings')
    def test_load_embeddings_reraises_with_context(self, mock_insert, mock_clear, mock_exists, mock_get_conn):
        """Test that exceptions are re-raised with context"""
        # Arrange
        mock_conn = MagicMock(spec=connection)
        mock_get_conn.return_value = mock_conn
        mock_exists.return_value = False

        embedded_chunks = [
            {
                'embedding': [0.1] * 1536,
                'chunk_index': 0,
                'chunk_text': 'Chunk'
            }
        ]

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            load_embeddings(999, embedded_chunks)

        # Verify error message format contains the episode ID
        assert "Episode 999" in str(exc_info.value)
