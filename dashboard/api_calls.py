"""Script used to make API calls related to podcasts and episodes."""
import requests

API_BASE_URL = "https://na87woqgo9.execute-api.eu-west-2.amazonaws.com/dev"


def add_podcast(rss_url: str) -> dict:
    """
    Add a new podcast via API Gateway

    Args:
        rss_url: The RSS feed URL to add

    Returns:
        Raw JSON response from the API, or error dict if response is not JSON
    """
    endpoint = f"{API_BASE_URL}/podcast"

    response = requests.post(
        endpoint,
        json={"podcast_url": rss_url}
    )

    return response


if __name__ == "__main__":
    # Example usage
    rss_feed = "https://audioboom.com/channels/5157206.rss"
    result = add_podcast(rss_feed)
    print(result)
