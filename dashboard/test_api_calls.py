from api_calls import add_podcast


def test_add_podcast_success(mocker):
    """Test adding a podcast with a valid RSS URL"""
    rss_url = "https://audioboom.com/channels/5157206.rss"

    # Create a mock response object using pytest-mock
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = "Podcast data added successfully!"

    # Mock the requests.post call using pytest-mock
    mocker.patch('api_calls.requests.post', return_value=mock_response)

    response = add_podcast(rss_url)
    assert response.status_code == 200
    assert response.json() == "Podcast data added successfully!"


def test_add_podcast_missing_url(mocker):
    """Test adding a podcast without providing a URL (empty string)"""
    rss_url = ""

    # Create a mock response object - should return 400 for missing URL
    mock_response = mocker.Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = "Invalid request: podcast_url is required."

    # Mock the requests.post call using pytest-mock
    mocker.patch('api_calls.requests.post', return_value=mock_response)

    response = add_podcast(rss_url)
    assert response.status_code == 400
    assert response.json() == "Invalid request: podcast_url is required."


def test_add_podcast_invalid_rss_format(mocker):
    """Test adding a podcast with a URL that doesn't end in .rss or .xml"""
    rss_url = "https://example.com/not-a-feed"

    # Lambda would return 500 when ValueError is raised in extract.py
    mock_response = mocker.Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {
        "errorMessage": "The provided URL is not a valid RSS feed URL.",
        "errorType": "ValueError"
    }

    # Mock the requests.post call using pytest-mock
    mocker.patch('api_calls.requests.post', return_value=mock_response)

    response = add_podcast(rss_url)
    assert response.status_code == 500


def test_add_podcast_invalid_feed_data(mocker):
    """Test adding a podcast with invalid feed data (missing required fields)"""
    rss_url = "https://example.com/invalid-feed.rss"

    # Lambda would return 500 when ValueError is raised in transform.py
    mock_response = mocker.Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {
        "errorMessage": "Podcast name must be a string",
        "errorType": "ValueError"
    }

    # Mock the requests.post call using pytest-mock
    mocker.patch('api_calls.requests.post', return_value=mock_response)

    response = add_podcast(rss_url)
    assert response.status_code == 500


def test_add_podcast_database_connection_error(mocker):
    """Test adding a podcast when database connection fails"""
    rss_url = "https://audioboom.com/channels/5157206.rss"

    # Lambda would return 500 when database connection fails
    mock_response = mocker.Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {
        "errorMessage": "Failed to connect to database",
        "errorType": "OperationalError"
    }

    # Mock the requests.post call using pytest-mock
    mocker.patch('api_calls.requests.post', return_value=mock_response)

    response = add_podcast(rss_url)
    assert response.status_code == 500
