from datetime import datetime


def validate_podcast_name(podcast_name: str) -> str:
    """Validates the podcast name to ensure it meets criteria."""
    if not isinstance(podcast_name, str):
        raise ValueError(
            f"Podcast name must be a string, type is {type(podcast_name)}.")

    podcast_name = podcast_name.strip()

    if len(podcast_name) == 0:
        raise ValueError("Podcast name cannot be empty.")

    return podcast_name


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

    language = language.strip()

    if len(language) == 0:
        raise ValueError("Language code cannot be empty.")

    return language.lower()


def get_rss_link(feed: dict) -> str:
    """Extracts the RSS feed link from the feed data."""

    # Try itunes_new-feed-url first (most reliable for RSS URL)
    if feed.get("itunes_new-feed-url"):
        return feed.get("itunes_new-feed-url")

    # Try to find the self link in the links array
    links = feed.get("links", [])
    for link in links:
        if link.get("rel") == "self" and link.get("type") == "application/rss+xml":
            return link.get("href")

    # Fall back to the main link and append .rss if not present
    main_link = feed.get("link", "")
    if not main_link.endswith(".rss") and not main_link.endswith(".xml"):
        main_link += ".rss"

    return main_link


def validate_feed(feed: dict) -> dict:
    """Validates the feed data to ensure required fields are present."""

    podcast_name = validate_podcast_name(feed.get("author"))
    publish_date = validate_publish_date(feed.get("published"))
    language = validate_language(feed.get("language"))
    link = get_rss_link(feed)

    return {
        "podcast_name": podcast_name,
        "publish_date": publish_date,
        "language": language,
        "link": link
    }
