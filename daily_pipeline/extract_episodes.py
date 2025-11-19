"""
This module contains functions to extract podcast and episode data from the database
and RSS feeds. It's used to:
1. Get all podcasts from the database
2. Fetch RSS feeds for each podcast
3. Identify new episodes since the last check
4. Return episode data for processing
"""

import os
import feedparser
from datetime import datetime
from email.utils import parsedate_to_datetime
from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor


def get_rds_connection() -> connection:
    """Returns a connection to the RDS database using environment variables

    Environment variables required:
    - RDS_HOST: Database host URL
    - RDS_DB_NAME: Database name
    - RDS_USERNAME: Database username
    - RDS_PASSWORD: Database password

    Returns:
        connection: PostgreSQL database connection object

    Raises:
        psycopg2.OperationalError: If connection fails
        TypeError: If required environment variables are missing
    """
    conn = connect(
        host=os.getenv("RDS_HOST"),
        database=os.getenv("RDS_DB_NAME"),
        user=os.getenv("RDS_USERNAME"),
        password=os.getenv("RDS_PASSWORD")
    )
    return conn


def get_episodes_from_rss(rss_url: str) -> list:
    """Gets all episodes from an RSS feed

    Args:
        rss_url: The URL of the RSS feed (.rss or .xml)

    Returns:
        list: List of episode dictionaries from the RSS feed,
              ordered with newest first (as provided by feedparser)

    Raises:
        ValueError: If URL is empty or not a valid RSS/XML feed URL
    """
    if len(rss_url) == 0:
        raise ValueError("The provided RSS feed URL is empty.")

    if not rss_url.endswith(".rss") and not rss_url.endswith(".xml"):
        raise ValueError("The provided URL is not a valid RSS feed URL.")

    parsed_feed = feedparser.parse(rss_url)
    return parsed_feed.entries


def get_all_podcasts(conn: connection) -> list:
    """Gets all podcasts from the database

    Args:
        conn: PostgreSQL database connection object

    Returns:
        list: List of podcast dictionaries with keys:
              - podcast_id
              - podcast_name
              - podcast_url
              (and any other fields in the podcast table)
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT podcast_id, podcast_name, podcast_url
            FROM podcast
            ORDER BY podcast_id
        """)
        return cursor.fetchall()


def get_latest_episode_date(conn: connection, podcast_id: int) -> datetime:
    """Gets the published date of the most recent episode for a podcast

    Args:
        conn: PostgreSQL database connection object
        podcast_id: The ID of the podcast

    Returns:
        datetime: The published_at timestamp of the latest episode,
                  or None if no episodes exist for this podcast
    """
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT published_at
            FROM episode
            WHERE podcast_id = %s
            ORDER BY published_at DESC
            LIMIT 1
        """, (podcast_id,))
        result = cursor.fetchone()
        return result[0] if result else None


def get_new_episodes_since(rss_url: str, since_date: datetime) -> list:
    """Gets episodes from RSS feed that were published after a given date

    Args:
        rss_url: The URL of the RSS feed (.rss or .xml)
        since_date: Only return episodes published after this date.
                    If None, returns all episodes (up to 20)

    Returns:
        list: Episodes published after since_date, ordered newest first
    """
    if len(rss_url) == 0:
        raise ValueError("The provided RSS feed URL is empty.")

    if not rss_url.endswith(".rss") and not rss_url.endswith(".xml"):
        raise ValueError("The provided URL is not a valid RSS feed URL.")

    episodes = get_episodes_from_rss(rss_url)

    if since_date is None:
        # Return latest 20 episodes if no reference date
        return episodes[:20]

    new_episodes = []
    for episode in episodes:
        # Try to parse the published date from the episode
        try:
            ep_date = None

            # feedparser provides published_parsed as a time.struct_time
            if episode.get('published_parsed'):
                ep_date = datetime(*episode['published_parsed'][:6])
            elif episode.get('published'):
                # Fallback: try to parse string date like 'Sun, 16 Nov 2025 23:55:00 +0000'
                ep_date = parsedate_to_datetime(episode['published'])

            # Only include episodes published after since_date
            if ep_date and ep_date > since_date:
                new_episodes.append(episode)
        except (ValueError, TypeError, AttributeError):
            # Skip episodes with unparseable dates
            continue

    return new_episodes


def extract_episodes_for_podcast(conn: connection, podcast: dict) -> list:
    """Main extraction logic: get new episodes for a single podcast

    Orchestrates the extraction process:
    - If podcast has no episodes in DB: return latest 20 from RSS
    - If podcast has episodes in DB: return new episodes since latest in DB

    Args:
        conn: PostgreSQL database connection object
        podcast: Dictionary with keys podcast_id, podcast_name, podcast_url

    Returns:
        list: Episode dictionaries from RSS feed to be processed
    """
    podcast_id = podcast['podcast_id']
    rss_url = podcast['podcast_url']

    # Get the latest episode date for this podcast
    latest_date = get_latest_episode_date(conn, podcast_id)

    if latest_date is None:
        # No episodes yet: fetch latest 20
        episodes = get_episodes_from_rss(rss_url)[:20]
    else:
        # Podcast has episodes: fetch only new ones since latest
        episodes = get_new_episodes_since(rss_url, latest_date)

    return episodes


def extract_all_new_episodes(conn: connection) -> list[dict]:
    """Extract new episodes for all podcasts in the database

    This is the main orchestration function that:
    1. Gets all podcasts from the database
    2. For each podcast, extracts new/latest episodes from its RSS feed
    3. Returns all episodes with their associated podcast information

    Args:
        conn: PostgreSQL database connection object

    Returns:
        list: List of dictionaries with structure:
              {
                  'podcast_id': int,
                  'podcast_name': str,
                  'podcast_url': str (RSS feed URL),
                  'episodes': list[dict]  # Raw episode data from RSS
              }
              Each episode dict contains all RSS fields like:
              title, published, published_parsed, links, summary, etc.
    """
    # Get all podcasts from the database
    podcasts = get_all_podcasts(conn)

    all_podcast_episodes = []

    for podcast in podcasts:
        try:
            # Extract episodes for this specific podcast
            episodes = extract_episodes_for_podcast(conn, podcast)

            # Only include podcasts that have new episodes
            if episodes:
                podcast_data = {
                    'podcast_id': podcast['podcast_id'],
                    'podcast_name': podcast['podcast_name'],
                    'podcast_url': podcast['podcast_url'],
                    'episodes': episodes
                }
                all_podcast_episodes.append(podcast_data)
        except Exception as e:
            # Log error but continue processing other podcasts
            # In production, you'd want proper logging here
            print(
                f"Error extracting episodes for podcast {podcast['podcast_id']}: {str(e)}")
            continue

    return all_podcast_episodes


if __name__ == "__main__":
    conn = get_rds_connection()
    extract_all_new_episodes(conn)
