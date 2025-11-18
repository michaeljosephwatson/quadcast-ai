from datetime import datetime


def validate_podcast_name(podcast_name: str) -> str:
    """Validates the podcast name to ensure it meets criteria."""
    if not isinstance(podcast_name, str):
        raise ValueError("Podcast name must be a string.")

    if len(podcast_name) == 0:
        raise ValueError("Podcast name cannot be empty.")

    return podcast_name.strip()


def validate_publish_date(publish_date: str) -> datetime:
    """Validates and converts the publish date to a datetime object."""

    if not isinstance(publish_date, str):
        raise ValueError("Publish date must be passed a string.")

    if len(publish_date) == 0:
        raise ValueError("Publish date cannot be empty.")

    try:
        return datetime.strptime(publish_date, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError as e:
        raise ValueError(f"Publish date format is incorrect: {e}")


def validate_language(language: str) -> str:
    """Validates the language code to ensure it meets criteria."""

    if not isinstance(language, str):
        raise ValueError("Language must be a string.")

    if len(language) == 0:
        raise ValueError("Language code cannot be empty.")

    return language.strip().lower()


def validate_feed(feed: dict) -> dict:
    """Validates the feed data to ensure required fields are present."""

    podcast_name = validate_podcast_name(feed.get("author"))
    publish_date = validate_publish_date(feed.get("published"))
    language = validate_language(feed.get("language"))
    link = feed.get("link")

    return {
        "podcast_name": podcast_name,
        "publish_date": publish_date,
        "language": language,
        "link": link
    }
