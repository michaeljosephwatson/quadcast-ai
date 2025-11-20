"""
This module contains functions to load validated episode data into the RDS database.

The episode data should already be transformed and validated by transform_episodes.py
before being passed to these functions.

Episode table structure:
- podcast_id: INTEGER (foreign key)
- audio_url: TEXT (unique, required)
- episode_title: TEXT
- published_at: TIMESTAMP
- transcribed: BOOLEAN (defaults to FALSE)
"""

import os
import logging
from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2 import errors as db_errors
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


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


def load_episode(conn: connection, episode: dict) -> bool:
    """Loads a single episode into the database

    Args:
        conn: PostgreSQL database connection object
        episode: Dictionary with structure:
                 {
                     'podcast_id': int,
                     'episode_title': str,
                     'audio_url': str,
                     'published_at': datetime,
                     'transcribed': bool
                 }

    Returns:
        bool: True if episode was inserted successfully, False if skipped due to conflict

    Raises:
        ValueError: If episode data is invalid
    """
    if not isinstance(episode, dict):
        raise ValueError("Episode must be a dictionary.")

    # Validate required fields
    podcast_id = episode.get('podcast_id')
    if podcast_id is None:
        raise ValueError("Episode must include podcast_id.")

    audio_url = episode.get('audio_url')
    if not audio_url:
        raise ValueError("Episode must include audio_url.")

    episode_title = episode.get('episode_title')
    published_at = episode.get('published_at')
    transcribed = episode.get('transcribed', False)

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO episode (podcast_id, audio_url, episode_title, published_at, transcribed)
                VALUES (%s, %s, %s, %s, %s)
            """, (podcast_id, audio_url, episode_title, published_at, transcribed))
            conn.commit()
            logger.debug(
                f"Successfully inserted episode {audio_url} for podcast {podcast_id}")
            return True

    except db_errors.UniqueViolation:
        # Episode with this audio_url already exists
        conn.rollback()
        logger.debug(
            f"Episode {audio_url} already exists in database, skipping")
        return False

    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting episode {audio_url}: {str(e)}")
        raise


def load_podcast_episodes(conn: connection, podcast_data: dict) -> dict:
    """Loads all episodes for a single podcast into the database

    Args:
        conn: PostgreSQL database connection object
        podcast_data: Dictionary with structure:
                      {
                          'podcast_id': int,
                          'podcast_name': str,
                          'episodes': list[dict]  # Validated episode data
                      }

    Returns:
        dict: Summary statistics with structure:
              {
                  'podcast_id': int,
                  'podcast_name': str,
                  'total_episodes': int,
                  'inserted_episodes': int,
                  'skipped_episodes': int
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
    episodes = podcast_data.get('episodes', [])

    if not isinstance(episodes, list):
        raise ValueError("Episodes must be a list.")

    logger.info(
        f"Loading {len(episodes)} episodes for podcast {podcast_id} ({podcast_name})")

    inserted_count = 0
    skipped_count = 0

    for episode in episodes:
        try:
            was_inserted = load_episode(conn, episode)
            if was_inserted:
                inserted_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            logger.warning(
                f"Failed to load episode for podcast {podcast_id}: {str(e)}")
            skipped_count += 1
            continue

    logger.info(
        f"Podcast {podcast_id}: inserted {inserted_count}/{len(episodes)} episodes, skipped {skipped_count}")

    return {
        'podcast_id': podcast_id,
        'podcast_name': podcast_name,
        'total_episodes': len(episodes),
        'inserted_episodes': inserted_count,
        'skipped_episodes': skipped_count
    }


def load_all_episodes(conn: connection, podcast_episodes_list: list) -> dict:
    """Loads episodes for all podcasts into the database

    Main orchestration function that loads validated episodes from all podcasts
    into the RDS database.

    Args:
        conn: PostgreSQL database connection object
        podcast_episodes_list: List of podcast data dictionaries with structure:
                               [
                                   {
                                       'podcast_id': int,
                                       'podcast_name': str,
                                       'episodes': list[dict]
                                   },
                                   ...
                               ]

    Returns:
        dict: Overall loading statistics with structure:
              {
                  'total_podcasts': int,
                  'total_episodes': int,
                  'total_inserted': int,
                  'total_skipped': int,
                  'podcast_stats': list[dict]  # Per-podcast statistics
              }

    Raises:
        ValueError: If input is not a list
    """
    if not isinstance(podcast_episodes_list, list):
        raise ValueError("Input must be a list of podcast data.")

    logger.info(f"Starting load of {len(podcast_episodes_list)} podcasts")

    total_inserted = 0
    total_skipped = 0
    podcast_stats = []

    for podcast_data in podcast_episodes_list:
        try:
            stats = load_podcast_episodes(conn, podcast_data)
            podcast_stats.append(stats)
            total_inserted += stats['inserted_episodes']
            total_skipped += stats['skipped_episodes']

        except ValueError as e:
            podcast_id = podcast_data.get('podcast_id', 'unknown')
            logger.error(f"Podcast {podcast_id} validation failed: {str(e)}")
            continue
        except Exception as e:
            podcast_id = podcast_data.get('podcast_id', 'unknown')
            logger.error(f"Error loading podcast {podcast_id}: {str(e)}")
            continue

    total_episodes = total_inserted + total_skipped

    logger.info(
        f"Load complete: {total_inserted} episodes inserted, {total_skipped} episodes skipped")

    return {
        'total_podcasts': len(podcast_episodes_list),
        'total_episodes': total_episodes,
        'total_inserted': total_inserted,
        'total_skipped': total_skipped,
        'podcast_stats': podcast_stats
    }


if __name__ == "__main__":
    from pprint import pprint
    from extract_episodes import extract_all_new_episodes
    from transform_episodes import transform_all_episodes

    load_dotenv()
    conn = get_rds_connection()

    # Extract -> Transform -> Load pipeline
    extracted_data = extract_all_new_episodes(conn)
    transformed_data = transform_all_episodes(extracted_data)
    load_stats = load_all_episodes(conn, transformed_data)

    pprint(load_stats)
    conn.close()
