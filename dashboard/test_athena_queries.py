import pytest
from athena_queries import get_transcript_for_episode, get_summary_for_episode


def test_get_transcript_for_episode_valid(mocker):
    """Test fetching transcript for a specific episode from Athena"""
    mock_athena_client = mocker.MagicMock()

    # Mock the start_query_execution response
    mock_athena_client.start_query_execution.return_value = {
        'QueryExecutionId': 'test-query-id'
    }

    # Mock the get_query_execution responses to simulate query completion
    mock_athena_client.get_query_execution.side_effect = [
        {
            'QueryExecution': {
                'Status': {'State': 'RUNNING'}
            }
        },
        {
            'QueryExecution': {
                'Status': {'State': 'SUCCEEDED'}
            }
        }
    ]

    # Mock the get_query_results response
    mock_athena_client.get_query_results.return_value = {
        'ResultSet': {
            'Rows': [
                {'Data': [{'VarCharValue': 'transcript'}]},  # Header row
                {'Data': [{'VarCharValue': 'This is a test transcript.'}]}
            ]
        }
    }

    transcript = get_transcript_for_episode(
        mock_athena_client, podcast_id=1, episode_id=1)

    assert transcript == "This is a test transcript."


def test_get_transcript_for_episode_no_data(mocker):
    """Test fetching transcript when no data is found"""
    mock_athena_client = mocker.MagicMock()

    # Mock the start_query_execution response
    mock_athena_client.start_query_execution.return_value = {
        'QueryExecutionId': 'test-query-id'
    }

    # Mock the get_query_execution responses to simulate query completion
    mock_athena_client.get_query_execution.side_effect = [
        {
            'QueryExecution': {
                'Status': {'State': 'SUCCEEDED'}
            }
        }
    ]

    # Mock the get_query_results response with no data
    mock_athena_client.get_query_results.return_value = {
        'ResultSet': {
            'Rows': [
                {'Data': [{'VarCharValue': 'transcript'}]}  # Only header row
            ]
        }
    }

    with pytest.raises(ValueError, match="No transcript found for podcast_id=1, episode_id=1"):
        get_transcript_for_episode(
            mock_athena_client, podcast_id=1, episode_id=1)


def test_get_transcript_for_episode_empty_transcript(mocker):
    """Test fetching transcript when the transcript is empty"""
    mock_athena_client = mocker.MagicMock()

    # Mock the start_query_execution response
    mock_athena_client.start_query_execution.return_value = {
        'QueryExecutionId': 'test-query-id'
    }

    # Mock the get_query_execution responses to simulate query completion
    mock_athena_client.get_query_execution.side_effect = [
        {
            'QueryExecution': {
                'Status': {'State': 'SUCCEEDED'}
            }
        }
    ]

    # Mock the get_query_results response with empty transcript
    mock_athena_client.get_query_results.return_value = {
        'ResultSet': {
            'Rows': [
                {'Data': [{'VarCharValue': 'transcript'}]},  # Header row
                {'Data': [{'VarCharValue': ''}]}  # Empty transcript
            ]
        }
    }

    with pytest.raises(ValueError, match="Transcript is empty for podcast_id=1, episode_id=1"):
        get_transcript_for_episode(
            mock_athena_client, podcast_id=1, episode_id=1)


def test_get_summary_for_episode_valid(mocker):
    """Test fetching summary for a specific episode from Athena"""
    mock_athena_client = mocker.MagicMock()

    # Mock the start_query_execution response
    mock_athena_client.start_query_execution.return_value = {
        'QueryExecutionId': 'test-query-id'
    }

    # Mock the get_query_execution responses to simulate query completion
    mock_athena_client.get_query_execution.side_effect = [
        {
            'QueryExecution': {
                'Status': {'State': 'RUNNING'}
            }
        },
        {
            'QueryExecution': {
                'Status': {'State': 'SUCCEEDED'}
            }
        }
    ]

    # Mock the get_query_results response
    mock_athena_client.get_query_results.return_value = {
        'ResultSet': {
            'Rows': [
                {'Data': [{'VarCharValue': 'summary'}, {'VarCharValue': 'topics'}, {
                    'VarCharValue': 'speakers'}]},  # Header row
                {'Data': [
                    {'VarCharValue': 'This is a test summary.'},
                    {'VarCharValue': 'Topic1, Topic2'},
                    {'VarCharValue': 'Speaker1, Speaker2'}
                ]}
            ]
        }
    }

    summary_data = get_summary_for_episode(
        mock_athena_client, podcast_id='1', episode_id='1')

    assert summary_data == {
        'summary': "This is a test summary.",
        'topics': "Topic1, Topic2",
        'speakers': "Speaker1, Speaker2"
    }


def test_get_summary_for_episode_no_data(mocker):
    """Test fetching summary when no data is found"""
    mock_athena_client = mocker.MagicMock()

    # Mock the start_query_execution response
    mock_athena_client.start_query_execution.return_value = {
        'QueryExecutionId': 'test-query-id'
    }

    # Mock the get_query_execution responses to simulate query completion
    mock_athena_client.get_query_execution.side_effect = [
        {
            'QueryExecution': {
                'Status': {'State': 'SUCCEEDED'}
            }
        }
    ]

    # Mock the get_query_results response with no data
    mock_athena_client.get_query_results.return_value = {
        'ResultSet': {
            'Rows': [
                {'Data': [{'VarCharValue': 'summary'}, {'VarCharValue': 'topics'}, {
                    'VarCharValue': 'speakers'}]}  # Only header row
            ]
        }
    }

    with pytest.raises(ValueError, match="No summary found for podcast_id=1, episode_id=1"):
        get_summary_for_episode(
            mock_athena_client, podcast_id='1', episode_id='1')


def test_get_summary_for_episode_empty_summary(mocker):
    """Test fetching summary when the summary is empty"""
    mock_athena_client = mocker.MagicMock()

    # Mock the start_query_execution response
    mock_athena_client.start_query_execution.return_value = {
        'QueryExecutionId': 'test-query-id'
    }

    # Mock the get_query_execution responses to simulate query completion
    mock_athena_client.get_query_execution.side_effect = [
        {
            'QueryExecution': {
                'Status': {'State': 'SUCCEEDED'}
            }
        }
    ]

    # Mock the get_query_results response with empty summary
    mock_athena_client.get_query_results.return_value = {
        'ResultSet': {
            'Rows': [
                {'Data': [{'VarCharValue': 'summary'}, {'VarCharValue': 'topics'}, {
                    'VarCharValue': 'speakers'}]},  # Header row
                {'Data': [
                    {'VarCharValue': ''},  # Empty summary
                    {'VarCharValue': 'Topic1, Topic2'},
                    {'VarCharValue': 'Speaker1, Speaker2'}
                ]}
            ]
        }
    }

    with pytest.raises(ValueError, match="Summary is empty for podcast_id=1, episode_id=1"):
        get_summary_for_episode(
            mock_athena_client, podcast_id='1', episode_id='1')
