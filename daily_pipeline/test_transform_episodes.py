import pytest
from datetime import datetime
from transform_episodes import (
    validate_episode_title,
    validate_audio_url,
    validate_published_date,
    extract_audio_url_from_links,
    validate_episode,
    transform_podcast_episodes,
    transform_all_episodes
)


class TestValidateEpisodeTitle:
    """Tests for validate_episode_title function"""

    def test_valid_title(self):
        """Test that valid title is returned"""
        result = validate_episode_title("My Episode Title")
        assert result == "My Episode Title"

    def test_title_with_whitespace_stripped(self):
        """Test that whitespace is stripped from title"""
        result = validate_episode_title("  My Episode Title  \n")
        assert result == "My Episode Title"

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError"""
        with pytest.raises(ValueError, match="Episode title cannot be empty"):
            validate_episode_title("")

    def test_whitespace_only_raises_error(self):
        """Test that whitespace-only string raises ValueError"""
        with pytest.raises(ValueError, match="Episode title cannot be empty"):
            validate_episode_title("   \n  ")

    def test_non_string_raises_error(self):
        """Test that non-string input raises ValueError"""
        with pytest.raises(ValueError, match="Episode title must be a string"):
            validate_episode_title(123)

    def test_none_raises_error(self):
        """Test that None raises ValueError"""
        with pytest.raises(ValueError, match="Episode title must be a string"):
            validate_episode_title(None)


class TestValidateAudioUrl:
    """Tests for validate_audio_url function"""

    def test_valid_https_url(self):
        """Test that valid HTTPS URL is accepted"""
        url = "https://example.com/audio.mp3"
        result = validate_audio_url(url)
        assert result == url

    def test_valid_http_url(self):
        """Test that valid HTTP URL is accepted"""
        url = "http://example.com/audio.mp3"
        result = validate_audio_url(url)
        assert result == url

    def test_s3_url(self):
        """Test that S3 URLs are accepted"""
        url = "https://s3.amazonaws.com/bucket/audio.mp3"
        result = validate_audio_url(url)
        assert result == url

    def test_url_with_whitespace_stripped(self):
        """Test that whitespace is stripped from URL"""
        url = "  https://example.com/audio.mp3  \n"
        result = validate_audio_url(url)
        assert result == "https://example.com/audio.mp3"

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError"""
        with pytest.raises(ValueError, match="Audio URL cannot be empty"):
            validate_audio_url("")

    def test_invalid_protocol_raises_error(self):
        """Test that URL without http/https raises ValueError"""
        with pytest.raises(ValueError, match="Audio URL must start with"):
            validate_audio_url("ftp://example.com/audio.mp3")

    def test_non_string_raises_error(self):
        """Test that non-string input raises ValueError"""
        with pytest.raises(ValueError, match="Audio URL must be a string"):
            validate_audio_url(123)


class TestValidatePublishedDate:
    """Tests for validate_published_date function"""

    def test_datetime_object_returned_as_is(self):
        """Test that datetime object is returned unchanged"""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = validate_published_date(dt)
        assert result == dt

    def test_tuple_converted_to_datetime(self):
        """Test that time tuple is converted to datetime"""
        # time.struct_time-like tuple: (year, month, day, hour, min, sec, ...)
        date_tuple = (2024, 1, 15, 10, 30, 0, 0, 15, 0)
        result = validate_published_date(date_tuple)
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_rfc2822_string_parsed(self):
        """Test that RFC 2822 date string is parsed"""
        date_str = "Sun, 15 Jan 2024 10:30:00 +0000"
        result = validate_published_date(date_str)
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError"""
        with pytest.raises(ValueError, match="Published date cannot be empty"):
            validate_published_date("")

    def test_invalid_string_raises_error(self):
        """Test that invalid date string raises ValueError"""
        with pytest.raises(ValueError, match="Published date format is incorrect"):
            validate_published_date("invalid-date")

    def test_invalid_tuple_raises_error(self):
        """Test that invalid tuple raises ValueError"""
        with pytest.raises(ValueError, match="Published date tuple is invalid"):
            validate_published_date((2024, 13, 32, 25, 60, 60))

    def test_none_raises_error(self):
        """Test that None raises ValueError"""
        with pytest.raises(ValueError, match="Published date must be"):
            validate_published_date(None)


class TestExtractAudioUrlFromLinks:
    """Tests for extract_audio_url_from_links function"""

    def test_finds_enclosure_link(self):
        """Test that enclosure link is correctly identified"""
        links = [
            {'rel': 'alternate', 'href': 'https://example.com/page'},
            {'rel': 'enclosure', 'href': 'https://example.com/audio.mp3',
                'type': 'audio/mpeg'},
        ]
        result = extract_audio_url_from_links(links)
        assert result == 'https://example.com/audio.mp3'

    def test_fallback_to_first_href(self):
        """Test that first href is used if no enclosure"""
        links = [
            {'href': 'https://example.com/audio.mp3'},
            {'href': 'https://example.com/other.mp3'},
        ]
        result = extract_audio_url_from_links(links)
        assert result == 'https://example.com/audio.mp3'

    def test_empty_links_raises_error(self):
        """Test that empty links list raises ValueError"""
        with pytest.raises(ValueError, match="Episode has no links"):
            extract_audio_url_from_links([])

    def test_none_links_raises_error(self):
        """Test that None raises ValueError"""
        with pytest.raises(ValueError, match="Episode has no links"):
            extract_audio_url_from_links(None)

    def test_links_without_href_raises_error(self):
        """Test that links without href raises ValueError"""
        links = [
            {'rel': 'alternate'},
            {'rel': 'enclosure'},
        ]
        with pytest.raises(ValueError, match="No valid audio link found"):
            extract_audio_url_from_links(links)


class TestValidateEpisode:
    """Tests for validate_episode function"""

    def test_valid_episode_with_enclosure(self):
        """Test validation of valid episode with enclosure link"""
        episode = {
            'title': 'Episode Title',
            'links': [
                {'rel': 'enclosure', 'href': 'https://example.com/audio.mp3'}
            ],
            'published_parsed': (2024, 1, 15, 10, 30, 0, 0, 15, 0)
        }
        result = validate_episode(episode, podcast_id=1)

        assert result['podcast_id'] == 1
        assert result['episode_title'] == 'Episode Title'
        assert result['audio_url'] == 'https://example.com/audio.mp3'
        assert result['transcribed'] is False
        assert isinstance(result['published_at'], datetime)

    def test_episode_with_link_fallback(self):
        """Test episode with fallback link field"""
        episode = {
            'title': 'Episode Title',
            'link': 'https://example.com/audio.mp3',
            'published': 'Sun, 15 Jan 2024 10:30:00 +0000'
        }
        result = validate_episode(episode, podcast_id=1)

        assert result['episode_title'] == 'Episode Title'
        assert result['audio_url'] == 'https://example.com/audio.mp3'

    def test_missing_title_raises_error(self):
        """Test that missing title raises ValueError"""
        episode = {
            'links': [{'rel': 'enclosure', 'href': 'https://example.com/audio.mp3'}],
            'published_parsed': (2024, 1, 15, 10, 30, 0, 0, 15, 0)
        }
        with pytest.raises(ValueError, match="Episode has no title"):
            validate_episode(episode, podcast_id=1)

    def test_missing_audio_url_raises_error(self):
        """Test that missing audio URL raises ValueError"""
        episode = {
            'title': 'Episode Title',
            'published_parsed': (2024, 1, 15, 10, 30, 0, 0, 15, 0)
        }
        with pytest.raises(ValueError, match="Episode has no audio URL"):
            validate_episode(episode, podcast_id=1)

    def test_missing_published_date_raises_error(self):
        """Test that missing published date raises ValueError"""
        episode = {
            'title': 'Episode Title',
            'links': [{'rel': 'enclosure', 'href': 'https://example.com/audio.mp3'}]
        }
        with pytest.raises(ValueError, match="Episode has no published date"):
            validate_episode(episode, podcast_id=1)

    def test_non_dict_raises_error(self):
        """Test that non-dict input raises ValueError"""
        with pytest.raises(ValueError, match="Episode must be a dictionary"):
            validate_episode("not a dict", podcast_id=1)


class TestTransformPodcastEpisodes:
    """Tests for transform_podcast_episodes function"""

    def test_transform_valid_podcast(self):
        """Test transforming valid podcast with episodes"""
        podcast_data = {
            'podcast_id': 1,
            'podcast_name': 'Test Podcast',
            'episodes': [
                {
                    'title': 'Episode 1',
                    'links': [{'rel': 'enclosure', 'href': 'https://example.com/ep1.mp3'}],
                    'published_parsed': (2024, 1, 15, 10, 30, 0, 0, 15, 0)
                },
                {
                    'title': 'Episode 2',
                    'links': [{'rel': 'enclosure', 'href': 'https://example.com/ep2.mp3'}],
                    'published_parsed': (2024, 1, 16, 10, 30, 0, 0, 16, 0)
                }
            ]
        }
        result = transform_podcast_episodes(podcast_data)

        assert result['podcast_id'] == 1
        assert result['podcast_name'] == 'Test Podcast'
        assert len(result['episodes']) == 2
        assert result['episodes'][0]['episode_title'] == 'Episode 1'
        assert result['episodes'][1]['episode_title'] == 'Episode 2'

    def test_skips_invalid_episodes(self):
        """Test that invalid episodes are skipped but processing continues"""
        podcast_data = {
            'podcast_id': 1,
            'podcast_name': 'Test Podcast',
            'episodes': [
                {
                    'title': 'Valid Episode',
                    'links': [{'rel': 'enclosure', 'href': 'https://example.com/ep1.mp3'}],
                    'published_parsed': (2024, 1, 15, 10, 30, 0, 0, 15, 0)
                },
                {
                    'title': 'Invalid Episode',
                    # Missing links and published date
                },
                {
                    'title': 'Another Valid Episode',
                    'links': [{'rel': 'enclosure', 'href': 'https://example.com/ep3.mp3'}],
                    'published_parsed': (2024, 1, 17, 10, 30, 0, 0, 17, 0)
                }
            ]
        }
        result = transform_podcast_episodes(podcast_data)

        assert len(result['episodes']) == 2
        assert result['episodes'][0]['episode_title'] == 'Valid Episode'
        assert result['episodes'][1]['episode_title'] == 'Another Valid Episode'

    def test_missing_podcast_id_raises_error(self):
        """Test that missing podcast_id raises ValueError"""
        podcast_data = {
            'podcast_name': 'Test Podcast',
            'episodes': []
        }
        with pytest.raises(ValueError, match="podcast_id"):
            transform_podcast_episodes(podcast_data)

    def test_missing_podcast_name_raises_error(self):
        """Test that missing podcast_name raises ValueError"""
        podcast_data = {
            'podcast_id': 1,
            'episodes': []
        }
        with pytest.raises(ValueError, match="podcast_name"):
            transform_podcast_episodes(podcast_data)

    def test_non_dict_raises_error(self):
        """Test that non-dict input raises ValueError"""
        with pytest.raises(ValueError, match="must be a dictionary"):
            transform_podcast_episodes("not a dict")


class TestTransformAllEpisodes:
    """Tests for transform_all_episodes function"""

    def test_transform_multiple_podcasts(self):
        """Test transforming multiple podcasts"""
        podcast_list = [
            {
                'podcast_id': 1,
                'podcast_name': 'Podcast 1',
                'episodes': [
                    {
                        'title': 'Episode 1',
                        'links': [{'rel': 'enclosure', 'href': 'https://example.com/ep1.mp3'}],
                        'published_parsed': (2024, 1, 15, 10, 30, 0, 0, 15, 0)
                    }
                ]
            },
            {
                'podcast_id': 2,
                'podcast_name': 'Podcast 2',
                'episodes': [
                    {
                        'title': 'Episode 2',
                        'links': [{'rel': 'enclosure', 'href': 'https://example.com/ep2.mp3'}],
                        'published_parsed': (2024, 1, 16, 10, 30, 0, 0, 16, 0)
                    }
                ]
            }
        ]
        result = transform_all_episodes(podcast_list)

        assert len(result) == 2
        assert result[0]['podcast_id'] == 1
        assert result[1]['podcast_id'] == 2

    def test_skips_podcasts_with_no_valid_episodes(self):
        """Test that podcasts with no valid episodes are excluded"""
        podcast_list = [
            {
                'podcast_id': 1,
                'podcast_name': 'Podcast 1',
                'episodes': [
                    {
                        'title': 'Valid Episode',
                        'links': [{'rel': 'enclosure', 'href': 'https://example.com/ep1.mp3'}],
                        'published_parsed': (2024, 1, 15, 10, 30, 0, 0, 15, 0)
                    }
                ]
            },
            {
                'podcast_id': 2,
                'podcast_name': 'Podcast 2',
                'episodes': [
                    {
                        'title': 'Invalid Episode'
                        # Missing required fields
                    }
                ]
            }
        ]
        result = transform_all_episodes(podcast_list)

        assert len(result) == 1
        assert result[0]['podcast_id'] == 1

    def test_empty_list_returns_empty(self):
        """Test that empty list returns empty list"""
        result = transform_all_episodes([])
        assert result == []

    def test_non_list_raises_error(self):
        """Test that non-list input raises ValueError"""
        with pytest.raises(ValueError, match="must be a list"):
            transform_all_episodes("not a list")

    def test_continues_on_podcast_error(self):
        """Test that processing continues even if one podcast fails"""
        podcast_list = [
            {
                'podcast_id': 1,
                'podcast_name': 'Valid Podcast',
                'episodes': [
                    {
                        'title': 'Episode 1',
                        'links': [{'rel': 'enclosure', 'href': 'https://example.com/ep1.mp3'}],
                        'published_parsed': (2024, 1, 15, 10, 30, 0, 0, 15, 0)
                    }
                ]
            },
            {
                'podcast_id': 2,
                # Missing podcast_name - will fail
                'episodes': []
            },
            {
                'podcast_id': 3,
                'podcast_name': 'Another Valid Podcast',
                'episodes': [
                    {
                        'title': 'Episode 3',
                        'links': [{'rel': 'enclosure', 'href': 'https://example.com/ep3.mp3'}],
                        'published_parsed': (2024, 1, 17, 10, 30, 0, 0, 17, 0)
                    }
                ]
            }
        ]
        result = transform_all_episodes(podcast_list)

        # Should have processed podcasts 1 and 3, skipping 2
        assert len(result) == 2
        assert result[0]['podcast_id'] == 1
        assert result[1]['podcast_id'] == 3
