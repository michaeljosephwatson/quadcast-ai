import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from psycopg2 import errors as db_errors
from psycopg2.extensions import connection as psycopg2_connection
from load_episodes import (
    get_rds_connection,
    load_episode,
    load_podcast_episodes,
    load_all_episodes
)


class TestGetRdsConnection:
    """Tests for get_rds_connection function"""

    @patch('load_episodes.connect')
    def test_get_rds_connection_valid_env_vars(self, mock_connect):
        """Test successful connection with valid environment variables"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_connect.return_value = mock_conn

        with patch.dict('os.environ', {
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

    @patch('load_episodes.connect')
    def test_get_rds_connection_correct_parameters(self, mock_connect):
        """Test that connection uses correct parameter names"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_connect.return_value = mock_conn

        with patch.dict('os.environ', {
            'RDS_HOST': 'db.example.com',
            'RDS_DB_NAME': 'production_db',
            'RDS_USERNAME': 'admin',
            'RDS_PASSWORD': 'secure_pass'
        }):
            # Act
            result = get_rds_connection()

            # Assert
            assert result == mock_conn
            mock_connect.assert_called_once_with(
                host='db.example.com',
                database='production_db',
                user='admin',
                password='secure_pass'
            )


class TestLoadEpisode:
    """Tests for load_episode function"""

    def test_load_episode_success(self):
        """Test successful episode insertion"""

        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        episode = {
            'podcast_id': 1,
            'episode_title': 'Test Episode',
            'audio_url': 'https://example.com/audio.mp3',
            'published_at': datetime(2024, 1, 15, 10, 30),
            'transcribed': False
        }

        # Act
        result = load_episode(mock_conn, episode)

        # Assert
        assert result is True
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.rollback.assert_not_called()

    def test_load_episode_duplicate_raises_unique_violation(self):
        """Test that duplicate audio_url is handled gracefully"""

        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Simulate UniqueViolation error
        mock_cursor.execute.side_effect = db_errors.UniqueViolation()

        episode = {
            'podcast_id': 1,
            'episode_title': 'Test Episode',
            'audio_url': 'https://example.com/audio.mp3',
            'published_at': datetime(2024, 1, 15, 10, 30),
            'transcribed': False
        }

        # Act
        result = load_episode(mock_conn, episode)

        # Assert
        assert result is False
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()

    def test_load_episode_other_error_raises(self):
        """Test that other database errors are raised"""

        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Simulate other error
        mock_cursor.execute.side_effect = Exception("Database error")

        episode = {
            'podcast_id': 1,
            'episode_title': 'Test Episode',
            'audio_url': 'https://example.com/audio.mp3',
            'published_at': datetime(2024, 1, 15, 10, 30),
            'transcribed': False
        }

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            load_episode(mock_conn, episode)

        mock_conn.rollback.assert_called_once()

    def test_load_episode_missing_podcast_id(self):
        """Test that missing podcast_id raises ValueError"""

        mock_conn = MagicMock()

        episode = {
            'episode_title': 'Test Episode',
            'audio_url': 'https://example.com/audio.mp3',
            'published_at': datetime(2024, 1, 15, 10, 30),
            'transcribed': False
        }

        with pytest.raises(ValueError, match="podcast_id"):
            load_episode(mock_conn, episode)

    def test_load_episode_missing_audio_url(self):
        """Test that missing audio_url raises ValueError"""

        mock_conn = MagicMock()

        episode = {
            'podcast_id': 1,
            'episode_title': 'Test Episode',
            'published_at': datetime(2024, 1, 15, 10, 30),
            'transcribed': False
        }

        with pytest.raises(ValueError, match="audio_url"):
            load_episode(mock_conn, episode)

    def test_load_episode_not_dict_raises(self):
        """Test that non-dict episode raises ValueError"""

        mock_conn = MagicMock()

        with pytest.raises(ValueError, match="must be a dictionary"):
            load_episode(mock_conn, "not a dict")

    def test_load_episode_with_optional_fields(self):
        """Test episode insertion with all optional fields"""

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        episode = {
            'podcast_id': 2,
            'episode_title': 'Complete Episode',
            'audio_url': 'https://example.com/complete.mp3',
            'published_at': datetime(2024, 1, 20, 15, 45),
            'transcribed': True
        }

        result = load_episode(mock_conn, episode)

        assert result is True
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1] == (2, 'https://example.com/complete.mp3', 'Complete Episode',
                                datetime(2024, 1, 20, 15, 45), True)


class TestLoadPodcastEpisodes:
    """Tests for load_podcast_episodes function"""

    @patch('load_episodes.load_episode')
    def test_load_podcast_episodes_all_success(self, mock_load_episode):
        """Test loading all episodes successfully"""

        mock_conn = MagicMock()
        mock_load_episode.return_value = True

        podcast_data = {
            'podcast_id': 1,
            'podcast_name': 'Test Podcast',
            'episodes': [
                {
                    'podcast_id': 1,
                    'episode_title': 'Episode 1',
                    'audio_url': 'https://example.com/ep1.mp3',
                    'published_at': datetime(2024, 1, 15, 10, 0),
                    'transcribed': False
                },
                {
                    'podcast_id': 1,
                    'episode_title': 'Episode 2',
                    'audio_url': 'https://example.com/ep2.mp3',
                    'published_at': datetime(2024, 1, 16, 10, 0),
                    'transcribed': False
                }
            ]
        }

        result = load_podcast_episodes(mock_conn, podcast_data)

        assert result['podcast_id'] == 1
        assert result['podcast_name'] == 'Test Podcast'
        assert result['total_episodes'] == 2
        assert result['inserted_episodes'] == 2
        assert result['skipped_episodes'] == 0

    @patch('load_episodes.load_episode')
    def test_load_podcast_episodes_with_duplicates(self, mock_load_episode):
        """Test loading episodes with some duplicates"""

        mock_conn = MagicMock()
        mock_load_episode.side_effect = [True, False, True]

        podcast_data = {
            'podcast_id': 1,
            'podcast_name': 'Test Podcast',
            'episodes': [
                {'podcast_id': 1, 'episode_title': 'Ep1', 'audio_url': 'url1', 'published_at': datetime.now(), 'transcribed': False},
                {'podcast_id': 1, 'episode_title': 'Ep2', 'audio_url': 'url2', 'published_at': datetime.now(), 'transcribed': False},
                {'podcast_id': 1, 'episode_title': 'Ep3', 'audio_url': 'url3', 'published_at': datetime.now(), 'transcribed': False}
            ]
        }

        result = load_podcast_episodes(mock_conn, podcast_data)

        assert result['total_episodes'] == 3
        assert result['inserted_episodes'] == 2
        assert result['skipped_episodes'] == 1

    @patch('load_episodes.load_episode')
    def test_load_podcast_episodes_with_failures(self, mock_load_episode):
        """Test loading episodes when some fail"""

        mock_conn = MagicMock()
        mock_load_episode.side_effect = [True, Exception("DB error"), True]

        podcast_data = {
            'podcast_id': 1,
            'podcast_name': 'Test Podcast',
            'episodes': [
                {'podcast_id': 1, 'episode_title': 'Ep1', 'audio_url': 'url1', 'published_at': datetime.now(), 'transcribed': False},
                {'podcast_id': 1, 'episode_title': 'Ep2', 'audio_url': 'url2', 'published_at': datetime.now(), 'transcribed': False},
                {'podcast_id': 1, 'episode_title': 'Ep3', 'audio_url': 'url3', 'published_at': datetime.now(), 'transcribed': False}
            ]
        }

        result = load_podcast_episodes(mock_conn, podcast_data)

        assert result['total_episodes'] == 3
        assert result['inserted_episodes'] == 2
        assert result['skipped_episodes'] == 1

    def test_load_podcast_episodes_missing_podcast_id(self):
        """Test that missing podcast_id raises ValueError"""

        mock_conn = MagicMock()

        podcast_data = {
            'podcast_name': 'Test Podcast',
            'episodes': []
        }

        with pytest.raises(ValueError, match="podcast_id"):
            load_podcast_episodes(mock_conn, podcast_data)

    def test_load_podcast_episodes_not_dict_raises(self):
        """Test that non-dict podcast_data raises ValueError"""

        mock_conn = MagicMock()

        with pytest.raises(ValueError, match="must be a dictionary"):
            load_podcast_episodes(mock_conn, "not a dict")

    def test_load_podcast_episodes_empty_episodes(self):
        """Test loading podcast with no episodes"""

        mock_conn = MagicMock()

        podcast_data = {
            'podcast_id': 1,
            'podcast_name': 'Test Podcast',
            'episodes': []
        }

        result = load_podcast_episodes(mock_conn, podcast_data)

        assert result['total_episodes'] == 0
        assert result['inserted_episodes'] == 0
        assert result['skipped_episodes'] == 0


class TestLoadAllEpisodes:
    """Tests for load_all_episodes function"""

    @patch('load_episodes.load_podcast_episodes')
    def test_load_all_episodes_success(self, mock_load_podcast):
        """Test loading all episodes successfully"""

        mock_conn = MagicMock()

        mock_load_podcast.side_effect = [
            {
                'podcast_id': 1,
                'podcast_name': 'Podcast 1',
                'total_episodes': 2,
                'inserted_episodes': 2,
                'skipped_episodes': 0
            },
            {
                'podcast_id': 2,
                'podcast_name': 'Podcast 2',
                'total_episodes': 3,
                'inserted_episodes': 3,
                'skipped_episodes': 0
            }
        ]

        podcast_episodes_list = [
            {
                'podcast_id': 1,
                'podcast_name': 'Podcast 1',
                'episodes': [
                    {'podcast_id': 1, 'episode_title': 'Ep1', 'audio_url': 'url1', 'published_at': datetime.now(), 'transcribed': False},
                    {'podcast_id': 1, 'episode_title': 'Ep2', 'audio_url': 'url2', 'published_at': datetime.now(), 'transcribed': False}
                ]
            },
            {
                'podcast_id': 2,
                'podcast_name': 'Podcast 2',
                'episodes': [
                    {'podcast_id': 2, 'episode_title': 'Ep1', 'audio_url': 'url3', 'published_at': datetime.now(), 'transcribed': False},
                    {'podcast_id': 2, 'episode_title': 'Ep2', 'audio_url': 'url4', 'published_at': datetime.now(), 'transcribed': False},
                    {'podcast_id': 2, 'episode_title': 'Ep3', 'audio_url': 'url5', 'published_at': datetime.now(), 'transcribed': False}
                ]
            }
        ]

        result = load_all_episodes(mock_conn, podcast_episodes_list)

        assert result['total_podcasts'] == 2
        assert result['total_episodes'] == 5
        assert result['total_inserted'] == 5
        assert result['total_skipped'] == 0
        assert len(result['podcast_stats']) == 2

    @patch('load_episodes.load_podcast_episodes')
    def test_load_all_episodes_with_mixed_results(self, mock_load_podcast):
        """Test loading episodes with some successes and failures"""

        mock_conn = MagicMock()

        mock_load_podcast.side_effect = [
            {
                'podcast_id': 1,
                'podcast_name': 'Podcast 1',
                'total_episodes': 2,
                'inserted_episodes': 2,
                'skipped_episodes': 0
            },
            {
                'podcast_id': 2,
                'podcast_name': 'Podcast 2',
                'total_episodes': 3,
                'inserted_episodes': 1,
                'skipped_episodes': 2
            }
        ]

        podcast_episodes_list = [
            {'podcast_id': 1, 'podcast_name': 'Podcast 1', 'episodes': []},
            {'podcast_id': 2, 'podcast_name': 'Podcast 2', 'episodes': []}
        ]

        result = load_all_episodes(mock_conn, podcast_episodes_list)

        assert result['total_podcasts'] == 2
        assert result['total_episodes'] == 5
        assert result['total_inserted'] == 3
        assert result['total_skipped'] == 2

    @patch('load_episodes.load_podcast_episodes')
    def test_load_all_episodes_with_podcast_error(self, mock_load_podcast):
        """Test that podcast loading errors are caught and processing continues"""

        mock_conn = MagicMock()

        mock_load_podcast.side_effect = [
            {
                'podcast_id': 1,
                'podcast_name': 'Podcast 1',
                'total_episodes': 2,
                'inserted_episodes': 2,
                'skipped_episodes': 0
            },
            ValueError("Invalid podcast data"),
            {
                'podcast_id': 3,
                'podcast_name': 'Podcast 3',
                'total_episodes': 1,
                'inserted_episodes': 1,
                'skipped_episodes': 0
            }
        ]

        podcast_episodes_list = [
            {'podcast_id': 1, 'podcast_name': 'Podcast 1', 'episodes': []},
            {'podcast_id': 2, 'podcast_name': 'Podcast 2', 'episodes': []},
            {'podcast_id': 3, 'podcast_name': 'Podcast 3', 'episodes': []}
        ]

        result = load_all_episodes(mock_conn, podcast_episodes_list)

        # Should have processed 3 podcasts but only succeeded with 2
        assert result['total_podcasts'] == 3
        assert len(result['podcast_stats']) == 2
        assert result['total_inserted'] == 3

    def test_load_all_episodes_not_list_raises(self):
        """Test that non-list input raises ValueError"""

        mock_conn = MagicMock()

        with pytest.raises(ValueError, match="must be a list"):
            load_all_episodes(mock_conn, "not a list")

    def test_load_all_episodes_empty_list(self):
        """Test loading with empty list"""

        mock_conn = MagicMock()

        result = load_all_episodes(mock_conn, [])

        assert result['total_podcasts'] == 0
        assert result['total_episodes'] == 0
        assert result['total_inserted'] == 0
        assert result['total_skipped'] == 0
        assert result['podcast_stats'] == []
