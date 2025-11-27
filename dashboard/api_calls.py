"""Script used to make API calls related to podcasts and episodes."""
import requests

API_BASE_URL = "https://na87woqgo9.execute-api.eu-west-2.amazonaws.com/dev"


def add_podcast(rss_url: str) -> requests.Response:
    """
    Add a new podcast via API Gateway

    Args:
        rss_url: The RSS feed URL to add

    Returns:
        Response object from the requests library containing status code and response data
    """
    endpoint = f"{API_BASE_URL}/podcast"

    response = requests.post(
        endpoint,
        json={"podcast_url": rss_url}
    )

    return response


def update_episodes() -> requests.Response:
    """
    Update episodes for a given podcast via API Gateway

    Args:
        podcast_id: The ID of the podcast to update episodes for
    Returns:
        Response object from the requests library containing status code and response data
    """
    endpoint = f"{API_BASE_URL}/workflow"

    response = requests.post(
        endpoint
    )

    return response


if __name__ == "__main__":
    # Example usage
    rss_feed = "https://audioboom.com/channels/5157206.rss"
    result = add_podcast(rss_feed)
    print(result)
