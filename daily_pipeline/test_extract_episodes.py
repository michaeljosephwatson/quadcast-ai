import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from psycopg2 import OperationalError
from psycopg2.extensions import connection as psycopg2_connection
from extract_episodes import (
    get_rds_connection,
    get_episodes_from_rss,
    get_all_podcasts,
    get_latest_episode_date,
    get_new_episodes_since,
    extract_episodes_for_podcast,
    extract_all_new_episodes
)


class TestGetRdsConnection:
    """Tests for get_rds_connection function"""

    @patch('extract_episodes.connect')
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

    @patch('extract_episodes.connect')
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

    @patch('extract_episodes.connect')
    def test_get_rds_connection_returns_connection_object(self, mock_connect):
        """Test that connection object is returned with required methods"""

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
            assert hasattr(result, 'cursor')
            assert hasattr(result, 'commit')
            assert hasattr(result, 'close')

    @patch('extract_episodes.connect')
    def test_get_rds_connection_operational_error(self, mock_connect):
        """Test handling of database connection error"""

        # Arrange
        mock_connect.side_effect = OperationalError("Connection refused")

        with patch.dict('os.environ', {
            'RDS_HOST': 'invalid.host.com',
            'RDS_DB_NAME': 'testdb',
            'RDS_USERNAME': 'testuser',
            'RDS_PASSWORD': 'testpass'
        }):
            # Act & Assert
            with pytest.raises(OperationalError):
                get_rds_connection()

    @patch('extract_episodes.connect')
    def test_get_rds_connection_with_special_characters_in_password(self, mock_connect):
        """Test connection with special characters in password"""

        # Arrange
        mock_conn = MagicMock(spec=psycopg2_connection)
        mock_connect.return_value = mock_conn

        with patch.dict('os.environ', {
            'RDS_HOST': 'localhost',
            'RDS_DB_NAME': 'testdb',
            'RDS_USERNAME': 'testuser',
            'RDS_PASSWORD': 'p@$$w0rd!#%'
        }):
            # Act
            result = get_rds_connection()

            # Assert
            assert result == mock_conn
            mock_connect.assert_called_once_with(
                host='localhost',
                database='testdb',
                user='testuser',
                password='p@$$w0rd!#%'
            )


class TestGetEpisodesFromRss:
    """Tests for get_episodes_from_rss function"""

    def test_valid_rss_returns_episodes(self):
        """Test that valid RSS URL returns list of episodes"""

        with patch('extract_episodes.feedparser.parse') as mock_parse:
            mock_feed = MagicMock()
            mock_feed.entries = [
                {'title': 'Episode 1', 'published': '2024-01-01'},
                {'title': 'Episode 2', 'published': '2024-01-02'}
            ]
            mock_parse.return_value = mock_feed

            result = get_episodes_from_rss("https://example.com/feed.rss")

            assert len(result) == 2
            assert result[0]['title'] == 'Episode 1'
            assert result[1]['title'] == 'Episode 2'

    def test_empty_feed_returns_empty_list(self):
        """Test that feed with no episodes returns empty list"""

        with patch('extract_episodes.feedparser.parse') as mock_parse:
            mock_feed = MagicMock()
            mock_feed.entries = []
            mock_parse.return_value = mock_feed

            result = get_episodes_from_rss("https://example.com/feed.rss")

            assert result == []

    def test_invalid_url_format(self):
        """Test that non-RSS/XML URLs raise ValueError"""

        with pytest.raises(ValueError, match="must end with .rss or .xml"):
            get_episodes_from_rss("https://example.com/feed.txt")

    def test_empty_url(self):
        """Test that empty URL raises ValueError"""

        with pytest.raises(ValueError, match="RSS feed URL cannot be empty"):
            get_episodes_from_rss("")


class TestGetAllPodcasts:
    """Tests for get_all_podcasts function"""

    def test_returns_all_podcasts(self):
        """Test that all podcasts are returned from database"""

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            {'podcast_id': 1, 'podcast_name': 'Podcast 1',
                'podcast_url': 'https://example.com/feed1.rss'},
            {'podcast_id': 2, 'podcast_name': 'Podcast 2',
                'podcast_url': 'https://example.com/feed2.rss'}
        ]

        result = get_all_podcasts(mock_conn)

        assert len(result) == 2
        assert result[0]['podcast_name'] == 'Podcast 1'
        assert result[1]['podcast_name'] == 'Podcast 2'
        mock_cursor.execute.assert_called_once()

    def test_returns_empty_list_when_no_podcasts(self):
        """Test that empty list is returned when no podcasts exist"""

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        result = get_all_podcasts(mock_conn)

        assert result == []

    def test_uses_realdict_cursor(self):
        """Test that RealDictCursor is used for dictionary results"""

        mock_conn = MagicMock()

        get_all_podcasts(mock_conn)

        # Verify cursor was called with RealDictCursor factory
        mock_conn.cursor.assert_called_once()
        call_kwargs = mock_conn.cursor.call_args[1]
        assert 'cursor_factory' in call_kwargs


class TestGetLatestEpisodeDate:
    """Tests for get_latest_episode_date function"""

    def test_returns_latest_date_when_episodes_exist(self):
        """Test that the most recent episode date is returned"""

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        expected_date = datetime(2024, 1, 15, 10, 30)
        mock_cursor.fetchone.return_value = (expected_date,)

        result = get_latest_episode_date(mock_conn, 1)

        assert result == expected_date
        mock_cursor.execute.assert_called_once()
        # Verify the SQL query includes ORDER BY and LIMIT
        sql = mock_cursor.execute.call_args[0][0]
        assert 'ORDER BY uploaded_at DESC' in sql
        assert 'LIMIT 1' in sql

    def test_returns_none_when_no_episodes(self):
        """Test that None is returned when podcast has no episodes"""

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        result = get_latest_episode_date(mock_conn, 1)

        assert result is None

    def test_queries_correct_podcast_id(self):
        """Test that the correct podcast_id is used in the query"""

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        get_latest_episode_date(mock_conn, 42)

        # Verify podcast_id parameter was passed correctly
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1] == (42,)


class TestGetNewEpisodesSince:
    """Tests for get_new_episodes_since function"""

    def test_returns_episodes_after_date(self):
        """Test that only episodes after since_date are returned"""

        with patch('extract_episodes.feedparser.parse') as mock_parse:
            mock_feed = MagicMock()
            mock_feed.entries = [
                {'title': 'New Episode', 'published_parsed': (
                    2024, 1, 20, 10, 0, 0, 0, 0, 0)},
                {'title': 'Mid Episode', 'published_parsed': (
                    2024, 1, 15, 10, 0, 0, 0, 0, 0)},
                {'title': 'Old Episode', 'published_parsed': (
                    2024, 1, 10, 10, 0, 0, 0, 0, 0)}
            ]
            mock_parse.return_value = mock_feed

            since_date = datetime(2024, 1, 12, 10, 0, 0)
            result = get_new_episodes_since(
                "https://example.com/feed.rss", since_date)

            assert len(result) == 2
            assert result[0]['title'] == 'New Episode'
            assert result[1]['title'] == 'Mid Episode'

    def test_returns_empty_list_when_no_new_episodes(self):
        """Test that empty list is returned when no episodes are newer than since_date"""

        with patch('extract_episodes.feedparser.parse') as mock_parse:
            mock_feed = MagicMock()
            mock_feed.entries = [
                {'title': 'Episode 1', 'published_parsed': (
                    2024, 1, 5, 10, 0, 0, 0, 0, 0)},
                {'title': 'Episode 2', 'published_parsed': (
                    2024, 1, 3, 10, 0, 0, 0, 0, 0)}
            ]
            mock_parse.return_value = mock_feed

            since_date = datetime(2024, 1, 15, 10, 0, 0)
            result = get_new_episodes_since(
                "https://example.com/feed.rss", since_date)

            assert result == []

    def test_returns_latest_20_when_since_date_is_none(self):
        """Test that latest 20 episodes are returned when since_date is None"""

        with patch('extract_episodes.feedparser.parse') as mock_parse:
            mock_feed = MagicMock()
            # Create 30 test episodes
            mock_feed.entries = [
                {'title': f'Episode {i}', 'published': f'2024-01-{30-i:02d}'}
                for i in range(30)
            ]
            mock_parse.return_value = mock_feed

            result = get_new_episodes_since(
                "https://example.com/feed.rss", None)

            assert len(result) == 20
            assert result[0]['title'] == 'Episode 0'

    def test_invalid_url_format(self):
        """Test that non-RSS/XML URLs raise ValueError"""

        with pytest.raises(ValueError, match="must end with .rss or .xml"):
            get_new_episodes_since(
                "https://example.com/feed.json", datetime.now())

    def test_empty_url(self):
        """Test that empty URL raises ValueError"""

        with pytest.raises(ValueError, match="RSS feed URL cannot be empty"):
            get_new_episodes_since("", datetime.now())

    def test_handles_episodes_without_date(self):
        """Test that episodes without dates are skipped"""

        with patch('extract_episodes.feedparser.parse') as mock_parse:
            mock_feed = MagicMock()
            mock_feed.entries = [
                {'title': 'Episode with date', 'published_parsed': (
                    2024, 1, 20, 10, 0, 0, 0, 0, 0)},
                {'title': 'Episode without date'},
                {'title': 'Another with date', 'published_parsed': (
                    2024, 1, 18, 10, 0, 0, 0, 0, 0)}
            ]
            mock_parse.return_value = mock_feed

            since_date = datetime(2024, 1, 15, 10, 0, 0)
            result = get_new_episodes_since(
                "https://example.com/feed.rss", since_date)

            assert len(result) == 2
            assert result[0]['title'] == 'Episode with date'


class TestExtractEpisodesForPodcast:
    """Tests for extract_episodes_for_podcast function"""

    @patch('extract_episodes.get_new_episodes_since')
    @patch('extract_episodes.get_latest_episode_date')
    @patch('extract_episodes.get_episodes_from_rss')
    def test_returns_latest_20_when_podcast_has_no_episodes(self, mock_get_episodes, mock_get_latest, mock_get_new):
        """Test that latest 20 episodes are returned for new podcast"""

        mock_conn = MagicMock()
        mock_get_latest.return_value = None  # No episodes yet

        episodes = [{'title': f'Episode {i}'} for i in range(25)]
        mock_get_episodes.return_value = episodes

        podcast = {
            'podcast_id': 1,
            'podcast_name': 'Test Podcast',
            'podcast_url': 'https://example.com/feed.rss'
        }

        result = extract_episodes_for_podcast(mock_conn, podcast)

        assert len(result) == 20
        mock_get_latest.assert_called_once_with(mock_conn, 1)
        mock_get_episodes.assert_called_once_with(
            'https://example.com/feed.rss')
        mock_get_new.assert_not_called()

    @patch('extract_episodes.get_new_episodes_since')
    @patch('extract_episodes.get_latest_episode_date')
    @patch('extract_episodes.get_episodes_from_rss')
    def test_returns_new_episodes_when_podcast_has_episodes(self, mock_get_episodes, mock_get_latest, mock_get_new):
        """Test that only new episodes are returned for existing podcast"""

        mock_conn = MagicMock()
        latest_date = datetime(2024, 1, 15, 10, 0, 0)
        mock_get_latest.return_value = latest_date

        new_episodes = [
            {'title': 'New Episode 1', 'published': '2024-01-20'},
            {'title': 'New Episode 2', 'published': '2024-01-18'}
        ]
        mock_get_new.return_value = new_episodes

        podcast = {
            'podcast_id': 1,
            'podcast_name': 'Test Podcast',
            'podcast_url': 'https://example.com/feed.rss'
        }

        result = extract_episodes_for_podcast(mock_conn, podcast)

        assert len(result) == 2
        assert result[0]['title'] == 'New Episode 1'
        mock_get_latest.assert_called_once_with(mock_conn, 1)
        mock_get_new.assert_called_once_with(
            'https://example.com/feed.rss', latest_date)
        mock_get_episodes.assert_not_called()

    @patch('extract_episodes.get_new_episodes_since')
    @patch('extract_episodes.get_latest_episode_date')
    @patch('extract_episodes.get_episodes_from_rss')
    def test_uses_correct_podcast_id(self, mock_get_episodes, mock_get_latest, mock_get_new):
        """Test that the correct podcast_id is used in queries"""

        mock_conn = MagicMock()
        mock_get_latest.return_value = None
        mock_get_episodes.return_value = []

        podcast = {
            'podcast_id': 42,
            'podcast_name': 'Test Podcast',
            'podcast_url': 'https://example.com/feed.rss'
        }

        extract_episodes_for_podcast(mock_conn, podcast)

        mock_get_latest.assert_called_once_with(mock_conn, 42)

    @patch('extract_episodes.get_new_episodes_since')
    @patch('extract_episodes.get_latest_episode_date')
    @patch('extract_episodes.get_episodes_from_rss')
    def test_uses_correct_rss_url(self, mock_get_episodes, mock_get_latest, mock_get_new):
        """Test that the correct RSS URL is used"""

        mock_conn = MagicMock()
        mock_get_latest.return_value = None
        mock_get_episodes.return_value = []

        podcast = {
            'podcast_id': 1,
            'podcast_name': 'Test Podcast',
            'podcast_url': 'https://example.com/custom-feed.rss'
        }

        extract_episodes_for_podcast(mock_conn, podcast)

        mock_get_episodes.assert_called_once_with(
            'https://example.com/custom-feed.rss')

    @patch('extract_episodes.get_new_episodes_since')
    @patch('extract_episodes.get_latest_episode_date')
    @patch('extract_episodes.get_episodes_from_rss')
    def test_returns_empty_list_when_no_new_episodes(self, mock_get_episodes, mock_get_latest, mock_get_new):
        """Test that empty list is returned when there are no new episodes"""

        mock_conn = MagicMock()
        mock_get_latest.return_value = datetime(2024, 1, 15, 10, 0, 0)
        mock_get_new.return_value = []

        podcast = {
            'podcast_id': 1,
            'podcast_name': 'Test Podcast',
            'podcast_url': 'https://example.com/feed.rss'
        }

        result = extract_episodes_for_podcast(mock_conn, podcast)

        assert result == []


class TestExtractAllNewEpisodes:
    """Tests for extract_all_new_episodes function"""

    @patch('extract_episodes.extract_episodes_for_podcast')
    @patch('extract_episodes.get_all_podcasts')
    def test_returns_all_podcasts_with_episodes(self, mock_get_all, mock_extract_episodes):
        """Test that all podcasts with new episodes are returned"""

        mock_conn = MagicMock()

        # Mock podcasts from database
        mock_get_all.return_value = [
            {
                'podcast_id': 1,
                'podcast_name': 'Podcast 1',
                'podcast_url': 'https://example.com/feed1.rss'
            },
            {
                'podcast_id': 2,
                'podcast_name': 'Podcast 2',
                'podcast_url': 'https://example.com/feed2.rss'
            }
        ]

        # Mock episodes for each podcast
        mock_extract_episodes.side_effect = [
            [{'title': 'Episode 1-1'}, {'title': 'Episode 1-2'}],
            [{'title': 'Episode 2-1'}]
        ]

        result = extract_all_new_episodes(mock_conn)

        assert len(result) == 2
        assert result[0]['podcast_id'] == 1
        assert result[0]['podcast_name'] == 'Podcast 1'
        assert len(result[0]['episodes']) == 2
        assert result[1]['podcast_id'] == 2
        assert len(result[1]['episodes']) == 1

    @patch('extract_episodes.extract_episodes_for_podcast')
    @patch('extract_episodes.get_all_podcasts')
    def test_returns_empty_list_when_no_podcasts(self, mock_get_all, mock_extract_episodes):
        """Test that empty list is returned when no podcasts exist"""

        mock_conn = MagicMock()
        mock_get_all.return_value = []

        result = extract_all_new_episodes(mock_conn)

        assert result == []
        mock_extract_episodes.assert_not_called()

    @patch('extract_episodes.extract_episodes_for_podcast')
    @patch('extract_episodes.get_all_podcasts')
    def test_skips_podcasts_with_no_new_episodes(self, mock_get_all, mock_extract_episodes):
        """Test that podcasts with no new episodes are excluded from results"""

        mock_conn = MagicMock()

        mock_get_all.return_value = [
            {
                'podcast_id': 1,
                'podcast_name': 'Podcast 1',
                'podcast_url': 'https://example.com/feed1.rss'
            },
            {
                'podcast_id': 2,
                'podcast_name': 'Podcast 2',
                'podcast_url': 'https://example.com/feed2.rss'
            },
            {
                'podcast_id': 3,
                'podcast_name': 'Podcast 3',
                'podcast_url': 'https://example.com/feed3.rss'
            }
        ]

        # Podcast 1 and 3 have episodes, Podcast 2 doesn't
        mock_extract_episodes.side_effect = [
            [{'title': 'Episode 1-1'}],
            [],  # No episodes
            [{'title': 'Episode 3-1'}]
        ]

        result = extract_all_new_episodes(mock_conn)

        assert len(result) == 2
        assert result[0]['podcast_id'] == 1
        assert result[1]['podcast_id'] == 3

    @patch('extract_episodes.extract_episodes_for_podcast')
    @patch('extract_episodes.get_all_podcasts')
    def test_includes_podcast_metadata(self, mock_get_all, mock_extract_episodes):
        """Test that podcast metadata is included in results"""

        mock_conn = MagicMock()

        mock_get_all.return_value = [
            {
                'podcast_id': 42,
                'podcast_name': 'My Special Podcast',
                'podcast_url': 'https://example.com/special.rss'
            }
        ]

        mock_extract_episodes.return_value = [{'title': 'Episode 1'}]

        result = extract_all_new_episodes(mock_conn)

        assert len(result) == 1
        assert result[0]['podcast_id'] == 42
        assert result[0]['podcast_name'] == 'My Special Podcast'
        assert result[0]['podcast_url'] == 'https://example.com/special.rss'
        assert result[0]['episodes'] == [{'title': 'Episode 1'}]

    @patch('extract_episodes.extract_episodes_for_podcast')
    @patch('extract_episodes.get_all_podcasts')
    def test_continues_on_extraction_error(self, mock_get_all, mock_extract_episodes):
        """Test that function continues processing if one podcast fails"""

        mock_conn = MagicMock()

        mock_get_all.return_value = [
            {
                'podcast_id': 1,
                'podcast_name': 'Podcast 1',
                'podcast_url': 'https://example.com/feed1.rss'
            },
            {
                'podcast_id': 2,
                'podcast_name': 'Podcast 2',
                'podcast_url': 'https://example.com/feed2.rss'
            },
            {
                'podcast_id': 3,
                'podcast_name': 'Podcast 3',
                'podcast_url': 'https://example.com/feed3.rss'
            }
        ]

        # Podcast 2 extraction fails, but others succeed
        mock_extract_episodes.side_effect = [
            [{'title': 'Episode 1-1'}],
            Exception("Network error"),
            [{'title': 'Episode 3-1'}]
        ]

        result = extract_all_new_episodes(mock_conn)

        # Should have results from podcasts 1 and 3, skipping 2
        assert len(result) == 2
        assert result[0]['podcast_id'] == 1
        assert result[1]['podcast_id'] == 3

    @patch('extract_episodes.extract_episodes_for_podcast')
    @patch('extract_episodes.get_all_podcasts')
    def test_handles_multiple_episodes_per_podcast(self, mock_get_all, mock_extract_episodes):
        """Test that multiple episodes from a single podcast are all included"""

        mock_conn = MagicMock()

        mock_get_all.return_value = [
            {
                'podcast_id': 1,
                'podcast_name': 'Podcast 1',
                'podcast_url': 'https://example.com/feed1.rss'
            }
        ]

        episodes = [
            {'title': f'Episode {i}', 'published': f'2024-01-{i:02d}'}
            for i in range(1, 6)
        ]
        mock_extract_episodes.return_value = episodes

        result = extract_all_new_episodes(mock_conn)

        assert len(result) == 1
        assert len(result[0]['episodes']) == 5
        for i, ep in enumerate(result[0]['episodes'], 1):
            assert ep['title'] == f'Episode {i}'

    @patch('extract_episodes.extract_episodes_for_podcast')
    @patch('extract_episodes.get_all_podcasts')
    def test_preserves_podcast_order(self, mock_get_all, mock_extract_episodes):
        """Test that podcasts are processed and returned in the same order"""

        mock_conn = MagicMock()

        podcasts = [
            {
                'podcast_id': i,
                'podcast_name': f'Podcast {i}',
                'podcast_url': f'https://example.com/feed{i}.rss'
            }
            for i in [5, 2, 8, 1, 3]
        ]
        mock_get_all.return_value = podcasts

        mock_extract_episodes.side_effect = [
            [{'title': f'Episode {i}'}] for i in [5, 2, 8, 1, 3]
        ]

        result = extract_all_new_episodes(mock_conn)

        assert len(result) == 5
        for i, expected_id in enumerate([5, 2, 8, 1, 3]):
            assert result[i]['podcast_id'] == expected_id
