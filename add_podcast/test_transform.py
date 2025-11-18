import pytest
from datetime import datetime
from transform import (
    validate_podcast_name,
    validate_publish_date,
    validate_language,
    validate_feed
)


class TestValidatePodcastName:
    """Test suite for validate_podcast_name function"""

    def test_validate_podcast_name_valid(self):
        """Test with a valid podcast name"""
        result = validate_podcast_name("My Awesome Podcast")
        assert result == "My Awesome Podcast"

    def test_validate_podcast_name_with_leading_trailing_spaces(self):
        """Test that leading and trailing spaces are stripped"""
        result = validate_podcast_name("  My Podcast  ")
        assert result == "My Podcast"

    def test_validate_podcast_name_single_character(self):
        """Test with a single character podcast name"""
        result = validate_podcast_name("P")
        assert result == "P"

    def test_validate_podcast_name_not_string(self):
        """Test that non-string input raises ValueError"""
        with pytest.raises(ValueError, match="Podcast name must be a string"):
            validate_podcast_name(123)

    def test_validate_podcast_name_not_string_list(self):
        """Test that list input raises ValueError"""
        with pytest.raises(ValueError, match="Podcast name must be a string"):
            validate_podcast_name(["My", "Podcast"])

    def test_validate_podcast_name_not_string_none(self):
        """Test that None input raises ValueError"""
        with pytest.raises(ValueError, match="Podcast name must be a string"):
            validate_podcast_name(None)

    def test_validate_podcast_name_empty_string(self):
        """Test that empty string raises ValueError"""
        with pytest.raises(ValueError, match="Podcast name cannot be empty"):
            validate_podcast_name("")

    def test_validate_podcast_name_whitespace_only(self):
        """Test that whitespace-only string raises ValueError"""
        with pytest.raises(ValueError, match="Podcast name cannot be empty"):
            validate_podcast_name("   ")

    def test_validate_podcast_name_with_special_characters(self):
        """Test podcast name with special characters"""
        result = validate_podcast_name("My Podcast & Show #1")
        assert result == "My Podcast & Show #1"

    def test_validate_podcast_name_unicode(self):
        """Test podcast name with unicode characters"""
        result = validate_podcast_name("Podcast en Español")
        assert result == "Podcast en Español"


class TestValidatePublishDate:
    """Test suite for validate_publish_date function"""

    def test_validate_publish_date_valid(self):
        """Test with a valid publish date string"""
        date_str = "Mon, 01 Jan 2024 12:00:00 +0000"
        result = validate_publish_date(date_str)
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1

    def test_validate_publish_date_different_timezone(self):
        """Test with different timezone offset"""
        date_str = "Tue, 15 Feb 2024 14:30:00 -0500"
        result = validate_publish_date(date_str)
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 2
        assert result.day == 15

    def test_validate_publish_date_not_string(self):
        """Test that non-string input raises ValueError"""
        with pytest.raises(ValueError, match="Publish date must be passed a string"):
            validate_publish_date(123)

    def test_validate_publish_date_not_string_datetime(self):
        """Test that datetime object raises ValueError"""
        with pytest.raises(ValueError, match="Publish date must be passed a string"):
            validate_publish_date(datetime.now())

    def test_validate_publish_date_not_string_none(self):
        """Test that None input raises ValueError"""
        with pytest.raises(ValueError, match="Publish date must be passed a string"):
            validate_publish_date(None)

    def test_validate_publish_date_empty_string(self):
        """Test that empty string raises ValueError"""
        with pytest.raises(ValueError, match="Publish date cannot be empty"):
            validate_publish_date("")

    def test_validate_publish_date_invalid_format(self):
        """Test that invalid date format raises ValueError"""
        with pytest.raises(ValueError, match="Publish date format is incorrect"):
            validate_publish_date("2024-01-01")

    def test_validate_publish_date_invalid_format_iso(self):
        """Test that ISO format raises ValueError"""
        with pytest.raises(ValueError, match="Publish date format is incorrect"):
            validate_publish_date("2024-01-01T12:00:00Z")

    def test_validate_publish_date_invalid_day(self):
        """Test that invalid day raises ValueError"""
        with pytest.raises(ValueError, match="Publish date format is incorrect"):
            validate_publish_date("Mon, 32 Jan 2024 12:00:00 +0000")

    def test_validate_publish_date_invalid_month(self):
        """Test that invalid month raises ValueError"""
        with pytest.raises(ValueError, match="Publish date format is incorrect"):
            validate_publish_date("Mon, 01 Xyz 2024 12:00:00 +0000")


class TestValidateLanguage:
    """Test suite for validate_language function"""

    def test_validate_language_valid_code(self):
        """Test with a valid language code"""
        result = validate_language("en-us")
        assert result == "en-us"

    def test_validate_language_uppercase_converted(self):
        """Test that uppercase is converted to lowercase"""
        result = validate_language("EN-US")
        assert result == "en-us"

    def test_validate_language_mixed_case(self):
        """Test that mixed case is converted to lowercase"""
        result = validate_language("En-Us")
        assert result == "en-us"

    def test_validate_language_with_spaces(self):
        """Test that leading and trailing spaces are stripped"""
        result = validate_language("  en  ")
        assert result == "en"

    def test_validate_language_iso_639_1(self):
        """Test with ISO 639-1 language codes"""
        result = validate_language("fr")
        assert result == "fr"

    def test_validate_language_iso_639_1_extended(self):
        """Test with ISO 639-1 extended language code"""
        result = validate_language("pt-br")
        assert result == "pt-br"

    def test_validate_language_not_string(self):
        """Test that non-string input raises ValueError"""
        with pytest.raises(ValueError, match="Language must be a string"):
            validate_language(123)

    def test_validate_language_not_string_dict(self):
        """Test that dict input raises ValueError"""
        with pytest.raises(ValueError, match="Language must be a string"):
            validate_language({"lang": "en"})

    def test_validate_language_not_string_none(self):
        """Test that None input raises ValueError"""
        with pytest.raises(ValueError, match="Language must be a string"):
            validate_language(None)

    def test_validate_language_empty_string(self):
        """Test that empty string raises ValueError"""
        with pytest.raises(ValueError, match="Language code cannot be empty"):
            validate_language("")

    def test_validate_language_whitespace_only(self):
        """Test that whitespace-only string raises ValueError"""
        with pytest.raises(ValueError, match="Language code cannot be empty"):
            validate_language("   ")


class TestValidateFeed:
    """Test suite for validate_feed function"""

    def test_validate_feed_valid(self):
        """Test with a valid feed dictionary"""
        feed = {
            "author": "My Podcast",
            "published": "Mon, 01 Jan 2024 12:00:00 +0000",
            "language": "en-us",
            "link": "https://example.com/feed"
        }
        result = validate_feed(feed)
        assert result["podcast_name"] == "My Podcast"
        assert isinstance(result["publish_date"], datetime)
        assert result["language"] == "en-us"
        assert result["link"] == "https://example.com/feed"

    def test_validate_feed_with_spaces(self):
        """Test that feed data is properly cleaned"""
        feed = {
            "author": "  My Podcast  ",
            "published": "Mon, 01 Jan 2024 12:00:00 +0000",
            "language": "  EN-US  ",
            "link": "https://example.com"
        }
        result = validate_feed(feed)
        assert result["podcast_name"] == "My Podcast"
        assert result["language"] == "en-us"

    def test_validate_feed_missing_author(self):
        """Test that missing author raises ValueError"""
        feed = {
            "published": "Mon, 01 Jan 2024 12:00:00 +0000",
            "language": "en-us",
            "link": "https://example.com"
        }
        with pytest.raises(ValueError, match="Podcast name must be a string"):
            validate_feed(feed)

    def test_validate_feed_missing_published(self):
        """Test that missing published raises ValueError"""
        feed = {
            "author": "My Podcast",
            "language": "en-us",
            "link": "https://example.com"
        }
        with pytest.raises(ValueError, match="Publish date must be passed a string"):
            validate_feed(feed)

    def test_validate_feed_missing_language(self):
        """Test that missing language raises ValueError"""
        feed = {
            "author": "My Podcast",
            "published": "Mon, 01 Jan 2024 12:00:00 +0000",
            "link": "https://example.com"
        }
        with pytest.raises(ValueError, match="Language must be a string"):
            validate_feed(feed)

    def test_validate_feed_missing_link(self):
        """Test that missing link is handled (not required)"""
        feed = {
            "author": "My Podcast",
            "published": "Mon, 01 Jan 2024 12:00:00 +0000",
            "language": "en-us"
        }
        result = validate_feed(feed)
        assert result["link"] is None

    def test_validate_feed_invalid_author(self):
        """Test that invalid author raises ValueError"""
        feed = {
            "author": "",
            "published": "Mon, 01 Jan 2024 12:00:00 +0000",
            "language": "en-us",
            "link": "https://example.com"
        }
        with pytest.raises(ValueError, match="Podcast name cannot be empty"):
            validate_feed(feed)

    def test_validate_feed_invalid_published_format(self):
        """Test that invalid publish date format raises ValueError"""
        feed = {
            "author": "My Podcast",
            "published": "2024-01-01",
            "language": "en-us",
            "link": "https://example.com"
        }
        with pytest.raises(ValueError, match="Publish date format is incorrect"):
            validate_feed(feed)

    def test_validate_feed_invalid_language(self):
        """Test that invalid language raises ValueError"""
        feed = {
            "author": "My Podcast",
            "published": "Mon, 01 Jan 2024 12:00:00 +0000",
            "language": "",
            "link": "https://example.com"
        }
        with pytest.raises(ValueError, match="Language code cannot be empty"):
            validate_feed(feed)

    def test_validate_feed_extra_fields(self):
        """Test that extra fields in feed are ignored"""
        feed = {
            "author": "My Podcast",
            "published": "Mon, 01 Jan 2024 12:00:00 +0000",
            "language": "en-us",
            "link": "https://example.com",
            "extra_field": "should be ignored",
            "another_field": 123
        }
        result = validate_feed(feed)
        assert "extra_field" not in result
        assert "another_field" not in result
        assert len(result) == 4

    def test_validate_feed_with_special_characters(self):
        """Test feed with special characters in author"""
        feed = {
            "author": "Podcast & Show #1",
            "published": "Mon, 01 Jan 2024 12:00:00 +0000",
            "language": "en-us",
            "link": "https://example.com"
        }
        result = validate_feed(feed)
        assert result["podcast_name"] == "Podcast & Show #1"

    def test_validate_feed_complex_language_code(self):
        """Test feed with complex language code"""
        feed = {
            "author": "My Podcast",
            "published": "Mon, 01 Jan 2024 12:00:00 +0000",
            "language": "zh-CN",
            "link": "https://example.com"
        }
        result = validate_feed(feed)
        assert result["language"] == "zh-cn"
