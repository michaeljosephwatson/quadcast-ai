import feedparser
from dotenv import load_dotenv
from pprint import pprint
load_dotenv()


def get_data_from_rss(rss_url: str) -> dict:
    """Gets all the data for the podcast from the RSS"""

    return feedparser.parse(rss_url).feed


if __name__ == "__main__":
    TEST_RSS_URL = "https://audioboom.com/channels/2399216.rss"
    pprint(get_data_from_rss(TEST_RSS_URL))
