from unittest.mock import patch
from extract import get_data_from_rss


class TestGetDataFromRss:
    """Test suite for get_data_from_rss function"""

    @patch('extract.feedparser.parse')
    def test_get_data_from_rss_valid_url(self, mock_parse):
        """Test that function returns feed data from valid RSS URL"""
        # Arrange
        mock_feed = {
            'title': 'Test Podcast',
            'link': 'https://example.com',
            'description': 'A test podcast',
        }
        mock_parse.return_value.feed = mock_feed
        rss_url = 'https://example.com/feed.xml'

        # Act
        result = get_data_from_rss(rss_url)

        # Assert
        assert result == mock_feed
        mock_parse.assert_called_once_with(rss_url)

    @patch('extract.feedparser.parse')
    def test_get_data_from_rss_returns_dict(self, mock_parse):
        """Test that function returns a dictionary"""
        # Arrange
        mock_parse.return_value.feed = {}
        rss_url = 'https://example.com/feed.xml'

        # Act
        result = get_data_from_rss(rss_url)

        # Assert
        assert isinstance(result, dict)

    @patch('extract.feedparser.parse')
    def test_get_data_from_rss_with_empty_feed(self, mock_parse):
        """Test that function handles empty feed gracefully"""
        # Arrange
        mock_parse.return_value.feed = {}
        rss_url = 'https://example.com/feed.xml'

        # Act
        result = get_data_from_rss(rss_url)

        # Assert
        assert result == {}

    @patch('extract.feedparser.parse')
    def test_get_data_from_rss_with_complex_feed(self, mock_parse):
        """Test that function handles complex RSS feed with multiple fields"""
        # Arrange
        mock_feed = {
            'title': 'Complex Podcast',
            'link': 'https://example.com',
            'description': 'A complex test podcast',
            'language': 'en-us',
            'copyright': '2024 Example',
            'author': 'John Doe',
            'updated': '2024-01-01T00:00:00Z',
            'entries': [
                {'title': 'Episode 1', 'link': 'https://example.com/ep1'},
                {'title': 'Episode 2', 'link': 'https://example.com/ep2'},
            ]
        }
        mock_parse.return_value.feed = mock_feed
        rss_url = 'https://example.com/feed.xml'

        # Act
        result = get_data_from_rss(rss_url)

        # Assert
        assert result == mock_feed
        assert result['title'] == 'Complex Podcast'
        assert len(result.get('entries', [])) == 2

    @patch('extract.feedparser.parse')
    def test_get_data_from_rss_with_different_urls(self, mock_parse):
        """Test that function calls feedparser with correct URL"""
        # Arrange
        mock_parse.return_value.feed = {'title': 'Test'}
        url1 = 'https://example1.com/feed.xml'
        url2 = 'https://example2.com/feed.xml'

        # Act
        get_data_from_rss(url1)
        get_data_from_rss(url2)

        # Assert
        assert mock_parse.call_count == 2
        mock_parse.assert_any_call(url1)
        mock_parse.assert_any_call(url2)

    @patch('extract.feedparser.parse')
    def test_get_data_from_rss_preserves_feed_structure(self, mock_parse):
        """Test that function preserves the complete feed structure"""
        # Arrange
        mock_feed = {
            'title': 'Podcast',
            'id': 'urn:uuid:60a76c80-d399-11d9-b91C-0003939e0af6',
            'updated': '2024-01-15T10:30:00Z',
        }
        mock_parse.return_value.feed = mock_feed
        rss_url = 'https://example.com/feed.xml'

        # Act
        result = get_data_from_rss(rss_url)

        # Assert
        assert result == mock_feed
        assert 'id' in result
        assert 'updated' in result

    @patch('extract.feedparser.parse')
    def test_get_data_from_rss_with_special_characters(self, mock_parse):
        """Test that function handles RSS feeds with special characters"""
        # Arrange
        mock_feed = {
            'title': 'Podcast & Show: Special "�dition"',
            'description': 'Test <podcast> with special chars: �, �, �',
        }
        mock_parse.return_value.feed = mock_feed
        rss_url = 'https://example.com/feed.xml'

        # Act
        result = get_data_from_rss(rss_url)

        # Assert
        assert result == mock_feed
        assert '&' in result['title']
        assert '�' in result['description']
