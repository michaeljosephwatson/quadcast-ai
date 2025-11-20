"""
This module contains functions to validate and transform episode data
extracted from RSS feeds before loading into the database.

Episode table requires:
- podcast_id: INTEGER (foreign key)
- audio_url: TEXT (unique, required)
- episode_title: TEXT
- published_at: TIMESTAMP
- transcribed: BOOLEAN (defaults to FALSE)
"""

from dotenv import load_dotenv
import logging
from datetime import datetime
from email.utils import parsedate_to_datetime

logger = logging.getLogger(__name__)


def validate_episode_title(title: str) -> str:
    """Validates the episode title to ensure it meets criteria.

    Args:
        title: The episode title from RSS feed

    Returns:
        str: The validated and cleaned episode title

    Raises:
        ValueError: If title is invalid or empty
    """
    if not isinstance(title, str):
        raise ValueError("Episode title must be a string.")

    title = title.strip()

    if len(title) == 0:
        raise ValueError("Episode title cannot be empty.")

    return title


def validate_audio_url(audio_url: str) -> str:
    """Validates the audio URL to ensure it meets criteria.

    Audio URL is the unique identifier for episodes and is required.

    Args:
        audio_url: The audio file URL from RSS feed

    Returns:
        str: The validated audio URL

    Raises:
        ValueError: If audio_url is invalid or empty
    """
    if not isinstance(audio_url, str):
        raise ValueError("Audio URL must be a string.")

    audio_url = audio_url.strip()

    if len(audio_url) == 0:
        raise ValueError("Audio URL cannot be empty.")

    if not audio_url.startswith("http://") and not audio_url.startswith("https://"):
        raise ValueError("Audio URL must start with http:// or https://")

    return audio_url


def validate_published_date(published_date) -> datetime:
    """Validates and converts the published date to a datetime object.

    Handles both parsed datetime objects and string dates from RSS feeds.

    Args:
        published_date: Either a datetime object or RFC 2822 formatted string

    Returns:
        datetime: The validated published_at timestamp

    Raises:
        ValueError: If date cannot be parsed
    """
    # If already a datetime object, return it
    if isinstance(published_date, datetime):
        return published_date

    # If it's a tuple/time.struct_time (from feedparser), convert to datetime
    if isinstance(published_date, tuple) and len(published_date) >= 6:
        try:
            return datetime(*published_date[:6])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Published date tuple is invalid: {e}")

    # Try to parse string date
    if isinstance(published_date, str):
        published_date = published_date.strip()

        if len(published_date) == 0:
            raise ValueError("Published date cannot be empty.")

        try:
            # Try parsing RFC 2822 format: 'Sun, 16 Nov 2025 23:55:00 +0000'
            return parsedate_to_datetime(published_date)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Published date format is incorrect: {e}")

    raise ValueError("Published date must be a datetime, tuple, or string.")


def extract_audio_url_from_links(links) -> str:
    """Extracts the audio URL from episode links.

    RSS feeds can have multiple links. This function finds the enclosure
    link (which contains the actual audio file).

    Args:
        links: List of link dictionaries from RSS episode

    Returns:
        str: The audio URL

    Raises:
        ValueError: If no audio link is found
    """
    if not links:
        raise ValueError("Episode has no links.")

    # Look for enclosure links (these contain the audio file)
    for link in links:
        if isinstance(link, dict):
            # Enclosure links have rel='enclosure'
            if link.get('rel') == 'enclosure' and link.get('href'):
                return link.get('href')

    # Fallback: look for any link with href
    for link in links:
        if isinstance(link, dict) and link.get('href'):
            return link.get('href')

    raise ValueError("No valid audio link found in episode links.")


def validate_episode(episode: dict, podcast_id: int) -> dict:
    """Validates and transforms episode data for database insertion.

    Takes raw episode data from RSS feed and validates it, extracting
    only the fields needed for the episode table.

    Args:
        episode: Raw episode dictionary from RSS feed
        podcast_id: The ID of the parent podcast

    Returns:
        dict: Validated episode data ready for insertion:
              {
                  'podcast_id': int,
                  'episode_title': str,
                  'audio_url': str,
                  'published_at': datetime,
                  'transcribed': bool (always False for new episodes)
              }

    Raises:
        ValueError: If any required field is invalid or missing
    """
    if not isinstance(episode, dict):
        raise ValueError("Episode must be a dictionary.")

    # Validate required fields
    title = episode.get('title')
    if not title:
        raise ValueError("Episode has no title.")
    validated_title = validate_episode_title(title)

    # Extract audio URL from links
    links = episode.get('links', [])
    try:
        audio_url = extract_audio_url_from_links(links)
        audio_url = validate_audio_url(audio_url)
    except ValueError:
        # If no audio link, try alternate_link or link field
        audio_url = episode.get('link') or episode.get('href')
        if not audio_url:
            raise ValueError("Episode has no audio URL.")
        audio_url = validate_audio_url(audio_url)

    # Validate published date
    published_raw = episode.get('published_parsed') or episode.get('published')
    if not published_raw:
        raise ValueError("Episode has no published date.")
    validated_published = validate_published_date(published_raw)

    return {
        'podcast_id': podcast_id,
        'episode_title': validated_title,
        'audio_url': audio_url,
        'published_at': validated_published,
        'transcribed': False  # All new episodes start as not transcribed
    }


def transform_podcast_episodes(podcast_data: dict) -> dict:
    """Transforms all episodes for a podcast.

    Takes extracted podcast data with raw episodes from RSS and validates
    all episodes, returning clean data ready for database insertion.

    Args:
        podcast_data: Dictionary with structure:
                      {
                          'podcast_id': int,
                          'podcast_name': str,
                          'episodes': list[dict]  # Raw RSS episode data
                      }

    Returns:
        dict: Transformed podcast data with validated episodes:
              {
                  'podcast_id': int,
                  'podcast_name': str,
                  'episodes': list[dict]  # Validated episode data
              }

    Raises:
        ValueError: If podcast_data is invalid
    """
    if not isinstance(podcast_data, dict):
        raise ValueError("Podcast data must be a dictionary.")

    podcast_id = podcast_data.get('podcast_id')
    if podcast_id is None:
        raise ValueError("Podcast data must include podcast_id.")

    podcast_name = podcast_data.get('podcast_name')
    if not podcast_name:
        raise ValueError("Podcast data must include podcast_name.")

    episodes = podcast_data.get('episodes', [])
    if not isinstance(episodes, list):
        raise ValueError("Episodes must be a list.")

    logger.info(
        f"Transforming {len(episodes)} episodes for podcast {podcast_id} ({podcast_name})")

    # Validate each episode
    validated_episodes = []
    for i, episode in enumerate(episodes):
        try:
            validated_ep = validate_episode(episode, podcast_id)
            validated_episodes.append(validated_ep)
        except ValueError as e:
            # Log which episode failed but continue processing
            logger.warning(
                f"Episode {i} in podcast {podcast_id} failed validation: {str(e)}")
            continue

    logger.info(
        f"Successfully validated {len(validated_episodes)}/{len(episodes)} episodes for podcast {podcast_id}")

    return {
        'podcast_id': podcast_id,
        'podcast_name': podcast_name,
        'episodes': validated_episodes
    }


def transform_all_episodes(podcast_episodes_list: list) -> list:
    """Transforms episodes for all podcasts.

    Main orchestration function that transforms extracted episodes
    from all podcasts.

    Args:
        podcast_episodes_list: List of podcast data dictionaries from extract

    Returns:
        list: List of transformed podcast data, each containing validated episodes

    Raises:
        ValueError: If input is not a list
    """
    if not isinstance(podcast_episodes_list, list):
        raise ValueError("Input must be a list of podcast data.")

    logger.info(
        f"Starting transformation of {len(podcast_episodes_list)} podcasts")

    transformed_podcasts = []

    for podcast_data in podcast_episodes_list:
        try:
            transformed = transform_podcast_episodes(podcast_data)
            # Only include podcasts that have validated episodes
            if transformed['episodes']:
                transformed_podcasts.append(transformed)
            else:
                podcast_id = podcast_data.get('podcast_id', 'unknown')
                logger.info(
                    f"Podcast {podcast_id} has no validated episodes after transformation")
        except ValueError as e:
            # Log error but continue processing other podcasts
            podcast_id = podcast_data.get('podcast_id', 'unknown')
            logger.warning(
                f"Podcast {podcast_id} failed transformation: {str(e)}")
            continue

    logger.info(
        f"Transformation complete: {len(transformed_podcasts)} podcasts with validated episodes")

    return transformed_podcasts


if __name__ == "__main__":
    from pprint import pprint
    from dotenv import load_dotenv
    from extract_episodes import (
        get_rds_connection,
        extract_all_new_episodes
    )
    load_dotenv()
    conn = get_rds_connection()
    data = extract_all_new_episodes(conn)
    pprint(transform_all_episodes(data))
