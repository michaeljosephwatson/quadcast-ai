"""Test suite for lambda_handler.py module"""
import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock, call

# Mock external dependencies before importing lambda_handler and transcribe
sys.modules['boto3'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['pydub'] = MagicMock()
sys.modules['pydub.AudioSegment'] = MagicMock()
sys.modules['openai'] = MagicMock()

from lambda_handler import (
    lambda_handler,
    sanitize_s3_key,
    download_audio,
    upload_to_s3,
    save_transcript_files
)


class TestSanitizeS3Key:
    """Test suite for sanitize_s3_key function"""

    def test_sanitize_removes_problematic_characters(self):
        """Test that problematic characters are removed"""
        # Arrange
        text = "Podcast/Episode:Title|Test"

        # Act
        result = sanitize_s3_key(text)

        # Assert
        assert "/" not in result
        assert ":" not in result
        assert "|" not in result

    def test_sanitize_replaces_spaces(self):
        """Test that spaces are replaced with underscores"""
        # Arrange
        text = "Podcast Episode Title"

        # Act
        result = sanitize_s3_key(text)

        # Assert
        assert " " not in result
        assert "_" in result

    def test_sanitize_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped"""
        # Arrange
        text = "  Podcast Title  "

        # Act
        result = sanitize_s3_key(text)

        # Assert
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_sanitize_preserves_alphanumeric(self):
        """Test that alphanumeric characters are preserved"""
        # Arrange
        text = "Podcast123Episode456"

        # Act
        result = sanitize_s3_key(text)

        # Assert
        assert "Podcast123Episode456" == result


class TestDownloadAudio:
    """Test suite for download_audio function"""

    @patch('lambda_handler.requests.get')
    def test_download_audio_creates_file(self, mock_get):
        """Test that audio file is created"""
        # Arrange
        mock_response = MagicMock()
        mock_response.iter_content = MagicMock(return_value=[b"audio_data"])
        mock_get.return_value = mock_response

        # Act
        with patch("builtins.open", create=True) as mock_open:
            download_audio("http://example.com/audio.mp3", "/tmp/test.mp3")

        # Assert
        mock_open.assert_called_once_with("/tmp/test.mp3", "wb")
        mock_get.assert_called_once()

    @patch('lambda_handler.requests.get')
    def test_download_audio_uses_correct_url(self, mock_get):
        """Test that correct URL is requested"""
        # Arrange
        mock_response = MagicMock()
        mock_response.iter_content = MagicMock(return_value=[])
        mock_get.return_value = mock_response
        test_url = "https://example.com/episode.mp3"

        # Act
        with patch("builtins.open", create=True):
            download_audio(test_url, "/tmp/test.mp3")

        # Assert
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['stream'] is True
        assert call_kwargs['timeout'] == 300

    @patch('lambda_handler.requests.get')
    def test_download_audio_raises_on_http_error(self, mock_get):
        """Test that HTTP errors are raised"""
        # Arrange
        mock_get.return_value.raise_for_status.side_effect = Exception("HTTP 404")

        # Act & Assert
        with pytest.raises(Exception):
            with patch("builtins.open", create=True):
                download_audio("http://invalid.com/audio.mp3", "/tmp/test.mp3")


class TestUploadToS3:
    """Test suite for upload_to_s3 function"""

    @patch('lambda_handler.s3_client')
    def test_upload_to_s3_calls_upload_file(self, mock_s3):
        """Test that s3_client.upload_file is called"""
        # Arrange
        mock_s3.upload_file = MagicMock()

        # Act
        result = upload_to_s3("/tmp/test.jsonl", "transcripts/data.jsonl")

        # Assert
        mock_s3.upload_file.assert_called_once()
        assert result == "transcripts/data.jsonl"

    @patch('lambda_handler.s3_client')
    def test_upload_to_s3_uses_correct_bucket(self, mock_s3):
        """Test that correct bucket is used"""
        # Arrange
        mock_s3.upload_file = MagicMock()

        # Act
        upload_to_s3("/tmp/test.jsonl", "test.jsonl")

        # Assert
        call_args = mock_s3.upload_file.call_args[0]
        assert "c20-quadcast-s3-bucket" in call_args or call_args[1] is not None


class TestSaveTranscriptFiles:
    """Test suite for save_transcript_files function"""

    @patch('lambda_handler.upload_to_s3')
    @patch('lambda_handler.os.remove')
    def test_save_transcript_files_creates_files(self, mock_remove, mock_upload):
        """Test that transcript files are created"""
        # Arrange
        mock_upload.return_value = "s3_key"
        transcript_data = {
            'text': 'Full transcript text',
            'segments': [
                {'start': 0, 'end': 10, 'speaker': 'A', 'text': 'Hello'}
            ]
        }

        # Act
        with patch("builtins.open", create=True) as mock_open:
            result = save_transcript_files(
                "Test Podcast",
                1,
                "Test Episode",
                1,
                transcript_data
            )

        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 2
        mock_upload.assert_called()

    @patch('lambda_handler.upload_to_s3')
    @patch('lambda_handler.os.remove')
    def test_save_transcript_files_cleans_up(self, mock_remove, mock_upload):
        """Test that temporary files are removed"""
        # Arrange
        mock_upload.return_value = "s3_key"
        transcript_data = {
            'text': 'text',
            'segments': []
        }

        # Act
        with patch("builtins.open", create=True):
            save_transcript_files("Podcast", 1, "Episode", 1, transcript_data)

        # Assert
        assert mock_remove.called


class TestLambdaHandler:
    """Test suite for lambda_handler function"""

    @patch('lambda_handler.get_rds_connection')
    @patch('lambda_handler.get_untranscribed_episode')
    def test_lambda_handler_no_episodes(self, mock_get_episode, mock_get_conn):
        """Test handler when no untranscribed episodes available"""
        # Arrange
        mock_get_episode.return_value = None
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        event = {'body': 'irrelevant'}
        context = MagicMock()

        # Act
        result = lambda_handler(event, context)

        # Assert
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['status'] == 'no_work'

    @patch('lambda_handler.download_audio')
    @patch('lambda_handler.transcribe_audio')
    @patch('lambda_handler.save_transcript_files')
    @patch('lambda_handler.update_episode_transcribed')
    @patch('lambda_handler.get_rds_connection')
    @patch('lambda_handler.get_untranscribed_episode')
    @patch('lambda_handler.os.remove')
    def test_lambda_handler_success(
        self, mock_remove, mock_get_episode, mock_get_conn,
        mock_update, mock_save, mock_transcribe, mock_download
    ):
        """Test successful transcription"""
        # Arrange
        mock_get_episode.return_value = {
            'episode_id': 1,
            'podcast_id': 1,
            'podcast_name': 'Test Podcast',
            'episode_title': 'Test Episode',
            'audio_url': 'https://example.com/audio.mp3'
        }
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_transcribe.return_value = {'text': 'test', 'segments': []}
        mock_save.return_value = ('s3_key1', 's3_key2')
        event = {'body': 'irrelevant'}
        context = MagicMock()

        # Act
        result = lambda_handler(event, context)

        # Assert
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['status'] == 'success'
        assert body['episode_id'] == 1
        mock_download.assert_called_once()
        mock_transcribe.assert_called_once()
        mock_update.assert_called_once_with(mock_conn, 1)

    @patch('lambda_handler.get_rds_connection')
    @patch('lambda_handler.get_untranscribed_episode')
    def test_lambda_handler_missing_required_fields(
        self, mock_get_episode, mock_get_conn
    ):
        """Test error handling for missing required fields"""
        # Arrange
        mock_get_episode.return_value = {
            'episode_id': 1,
            'podcast_id': 1,
            'podcast_name': None,  # Missing
            'episode_title': 'Test Episode',
            'audio_url': 'https://example.com/audio.mp3'
        }
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        event = {'body': 'irrelevant'}
        context = MagicMock()

        # Act
        result = lambda_handler(event, context)

        # Assert
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert body['status'] == 'error'

    @patch('lambda_handler.download_audio')
    @patch('lambda_handler.get_rds_connection')
    @patch('lambda_handler.get_untranscribed_episode')
    def test_lambda_handler_download_failure(
        self, mock_get_episode, mock_get_conn, mock_download
    ):
        """Test error handling when download fails"""
        # Arrange
        mock_get_episode.return_value = {
            'episode_id': 1,
            'podcast_id': 1,
            'podcast_name': 'Test Podcast',
            'episode_title': 'Test Episode',
            'audio_url': 'https://example.com/audio.mp3'
        }
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_download.side_effect = Exception("Download failed")
        event = {'body': 'irrelevant'}
        context = MagicMock()

        # Act
        result = lambda_handler(event, context)

        # Assert
        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert body['status'] == 'error'
        mock_conn.close.assert_called_once()

    @patch('lambda_handler.download_audio')
    @patch('lambda_handler.transcribe_audio')
    @patch('lambda_handler.save_transcript_files')
    @patch('lambda_handler.update_episode_transcribed')
    @patch('lambda_handler.get_rds_connection')
    @patch('lambda_handler.get_untranscribed_episode')
    @patch('lambda_handler.os.remove')
    def test_lambda_handler_closes_connection(
        self, mock_remove, mock_get_episode, mock_get_conn,
        mock_update, mock_save, mock_transcribe, mock_download
    ):
        """Test that connection is closed after processing"""
        # Arrange
        mock_get_episode.return_value = {
            'episode_id': 1,
            'podcast_id': 1,
            'podcast_name': 'Test Podcast',
            'episode_title': 'Test Episode',
            'audio_url': 'https://example.com/audio.mp3'
        }
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_transcribe.return_value = {'text': 'test', 'segments': []}
        mock_save.return_value = ('s3_key1', 's3_key2')
        event = {'body': 'irrelevant'}
        context = MagicMock()

        # Act
        lambda_handler(event, context)

        # Assert
        mock_conn.close.assert_called_once()

    @patch('lambda_handler.download_audio')
    @patch('lambda_handler.transcribe_audio')
    @patch('lambda_handler.get_rds_connection')
    @patch('lambda_handler.get_untranscribed_episode')
    def test_lambda_handler_error_closes_connection(
        self, mock_get_episode, mock_get_conn, mock_transcribe, mock_download
    ):
        """Test that connection is closed on error"""
        # Arrange
        mock_get_episode.return_value = {
            'episode_id': 1,
            'podcast_id': 1,
            'podcast_name': 'Test Podcast',
            'episode_title': 'Test Episode',
            'audio_url': 'https://example.com/audio.mp3'
        }
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_transcribe.side_effect = Exception("Transcription error")
        event = {'body': 'irrelevant'}
        context = MagicMock()

        # Act
        result = lambda_handler(event, context)

        # Assert
        assert result['statusCode'] == 500
        mock_conn.close.assert_called_once()
