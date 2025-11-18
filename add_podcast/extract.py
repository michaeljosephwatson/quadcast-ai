"""This file contains functions to extract podcast data from an RSS feed. This is currently for given a link that the user provides."""

import feedparser
from pprint import pprint


def get_data_from_rss(rss_url: str) -> dict:
    """Gets all the data for the podcast from the RSS"""

    if not rss_url.endswith(".rss") and not rss_url.endswith(".xml"):
        raise ValueError("The provided URL is not a valid RSS feed URL.")

    if len(rss_url) == 0:
        raise ValueError("The provided RSS feed URL is empty.")

    return feedparser.parse(rss_url).feed


if __name__ == "__main__":
    TEST_RSS_URL = "https://audioboom.com/channels/2399216.rss"
    pprint(get_data_from_rss(TEST_RSS_URL))
