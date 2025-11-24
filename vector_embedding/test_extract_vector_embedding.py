"""Test suite for extract.py module in vector_embedding pipeline."""
import pytest
import json
import os
from unittest.mock import patch, MagicMock, Mock
from io import BytesIO
from botocore.exceptions import ClientError

from extract import (
    get_s3_client,
    build_transcript_key,
    read_transcript_jsonl,
    read_transcript_for_embedding,
    validate_transcript
)


class TestGetS3Client:
    """Test suite for get_s3_client function"""

    @patch('extract.boto3.client')
    def test_get_s3_client_returns_client(self, mock_boto3_client):
        """Test that get_s3_client returns a boto3 S3 client"""
        # Arrange
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        # Act
        result = get_s3_client()

        # Assert
        assert result == mock_client
        mock_boto3_client.assert_called_once_with('s3', region_name='eu-west-2')

    @patch('extract.boto3.client')
    def test_get_s3_client_uses_default_region(self, mock_boto3_client):
        """Test that get_s3_client uses correct default region"""
        # Arrange
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        # Act
        get_s3_client()

        # Assert
        call_args = mock_boto3_client.call_args
        assert call_args[1]['region_name'] == 'eu-west-2'

    @patch('extract.AWS_REGION', 'us-east-1')
    @patch('extract.boto3.client')
    def test_get_s3_client_uses_env_region(self, mock_boto3_client):
        """Test that get_s3_client respects AWS_REGION environment variable"""
        # Arrange
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        # Act
        get_s3_client()

        # Assert
        call_args = mock_boto3_client.call_args
        assert call_args[1]['region_name'] == 'us-east-1'


class TestBuildTranscriptKey:
    """Test suite for build_transcript_key function"""

    def test_build_transcript_key_default_filename(self):
        """Test building S3 key with default filename"""
        # Act
        key = build_transcript_key(podcast_id=1, episode_id=42)

        # Assert
        assert key == "transcripts/podcast_id=1/episode_id=42/data.jsonl"

    def test_build_transcript_key_custom_filename(self):
        """Test building S3 key with custom filename"""
        # Act
        key = build_transcript_key(
            podcast_id=5,
            episode_id=100,
            filename="transcript.jsonl"
        )

        # Assert
        assert key == "transcripts/podcast_id=5/episode_id=100/transcript.jsonl"

    def test_build_transcript_key_large_ids(self):
        """Test building S3 key with large ID numbers"""
        # Act
        key = build_transcript_key(podcast_id=999999, episode_id=888888)

        # Assert
        assert key == "transcripts/podcast_id=999999/episode_id=888888/data.jsonl"

    def test_build_transcript_key_format(self):
        """Test S3 key format is correct"""
        # Act
        key = build_transcript_key(podcast_id=10, episode_id=20)

        # Assert
        assert key.startswith("transcripts/")
        assert "podcast_id=10" in key
        assert "episode_id=20" in key
        assert key.endswith(".jsonl")


class TestReadTranscriptJsonl:
    """Test suite for read_transcript_jsonl function"""

    @patch('extract.get_s3_client')
    def test_read_single_line_jsonl(self, mock_get_client, caplog):
        """Test reading single-line JSONL file"""
        # Arrange
        mock_s3 = MagicMock()
        mock_get_client.return_value = mock_s3

        jsonl_content = '{"transcript_text": "This is a test transcript"}\n'
        mock_body = MagicMock()
        mock_body.read.return_value = jsonl_content.encode('utf-8')
        mock_s3.get_object.return_value = {'Body': mock_body}

        # Act
        result = read_transcript_jsonl('test/path.jsonl')

        # Assert
        assert result == "This is a test transcript"
        mock_s3.get_object.assert_called_once_with(
            Bucket='c20-quadcast-s3-bucket',
            Key='test/path.jsonl'
        )

    @patch('extract.get_s3_client')
    def test_read_multiline_jsonl_concatenates(self, mock_get_client):
        """Test reading multi-line JSONL concatenates all segments"""
        # Arrange
        mock_s3 = MagicMock()
        mock_get_client.return_value = mock_s3

        jsonl_content = (
            '{"transcript_text": "Hello world"}\n'
            '{"transcript_text": "This is a test"}\n'
            '{"transcript_text": "Final segment"}\n'
        )
        mock_body = MagicMock()
        mock_body.read.return_value = jsonl_content.encode('utf-8')
        mock_s3.get_object.return_value = {'Body': mock_body}

        # Act
        result = read_transcript_jsonl('test/path.jsonl')

        # Assert
        assert result == "Hello world This is a test Final segment"

    @patch('extract.get_s3_client')
    def test_read_jsonl_handles_empty_lines(self, mock_get_client):
        """Test that empty lines are skipped"""
        # Arrange
        mock_s3 = MagicMock()
        mock_get_client.return_value = mock_s3

        jsonl_content = (
            '{"transcript_text": "First line"}\n'
            '\n'  # Empty line
            '{"transcript_text": "Second line"}\n'
        )
        mock_body = MagicMock()
        mock_body.read.return_value = jsonl_content.encode('utf-8')
        mock_s3.get_object.return_value = {'Body': mock_body}

        # Act
        result = read_transcript_jsonl('test/path.jsonl')

        # Assert
        assert result == "First line Second line"

    @patch('extract.get_s3_client')
    def test_read_jsonl_file_not_found_error(self, mock_get_client):
        """Test FileNotFoundError is raised for NoSuchKey"""
        # Arrange
        mock_s3 = MagicMock()
        mock_get_client.return_value = mock_s3

        error_response = {'Error': {'Code': 'NoSuchKey'}}
        mock_s3.get_object.side_effect = ClientError(error_response, 'GetObject')

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Not found"):
            read_transcript_jsonl('nonexistent.jsonl')

    @patch('extract.get_s3_client')
    def test_read_jsonl_other_s3_errors(self, mock_get_client):
        """Test that other S3 errors are raised as Exception"""
        # Arrange
        mock_s3 = MagicMock()
        mock_get_client.return_value = mock_s3

        error_response = {'Error': {'Code': 'AccessDenied'}}
        mock_s3.get_object.side_effect = ClientError(error_response, 'GetObject')

        # Act & Assert
        with pytest.raises(Exception, match="S3 error"):
            read_transcript_jsonl('test.jsonl')

    @patch('extract.get_s3_client')
    def test_read_jsonl_invalid_json(self, mock_get_client):
        """Test that malformed JSON raises Exception"""
        # Arrange
        mock_s3 = MagicMock()
        mock_get_client.return_value = mock_s3

        jsonl_content = (
            '{"transcript_text": "Valid line"}\n'
            '{invalid json here}\n'  # Malformed
        )
        mock_body = MagicMock()
        mock_body.read.return_value = jsonl_content.encode('utf-8')
        mock_s3.get_object.return_value = {'Body': mock_body}

        # Act & Assert
        with pytest.raises(Exception, match="Invalid JSONL format at line 2"):
            read_transcript_jsonl('test.jsonl')

    @patch('extract.get_s3_client')
    def test_read_jsonl_missing_transcript_text_field(self, mock_get_client, caplog):
        """Test handling missing transcript_text field"""
        # Arrange
        mock_s3 = MagicMock()
        mock_get_client.return_value = mock_s3

        jsonl_content = (
            '{"transcript_text": "Valid text"}\n'
            '{"other_field": "no transcript_text here"}\n'  # Missing field
            '{"transcript_text": "More valid text"}\n'
        )
        mock_body = MagicMock()
        mock_body.read.return_value = jsonl_content.encode('utf-8')
        mock_s3.get_object.return_value = {'Body': mock_body}

        # Act
        result = read_transcript_jsonl('test.jsonl')

        # Assert
        assert result == "Valid text  More valid text"
        assert "missing 'transcript_text'" in caplog.text

    @patch('extract.get_s3_client')
    def test_read_jsonl_no_transcript_text_found(self, mock_get_client):
        """Test Exception when no transcript text found"""
        # Arrange
        mock_s3 = MagicMock()
        mock_get_client.return_value = mock_s3

        jsonl_content = '{"other_field": "value"}\n'  # No transcript_text
        mock_body = MagicMock()
        mock_body.read.return_value = jsonl_content.encode('utf-8')
        mock_s3.get_object.return_value = {'Body': mock_body}

        # Act & Assert
        with pytest.raises(Exception, match="No transcript text found"):
            read_transcript_jsonl('test.jsonl')

    @patch('extract.get_s3_client')
    def test_read_jsonl_custom_bucket(self, mock_get_client):
        """Test reading from custom bucket"""
        # Arrange
        mock_s3 = MagicMock()
        mock_get_client.return_value = mock_s3

        jsonl_content = '{"transcript_text": "Test"}\n'
        mock_body = MagicMock()
        mock_body.read.return_value = jsonl_content.encode('utf-8')
        mock_s3.get_object.return_value = {'Body': mock_body}

        # Act
        read_transcript_jsonl('test/path.jsonl', bucket_name='custom-bucket')

        # Assert
        mock_s3.get_object.assert_called_once_with(
            Bucket='custom-bucket',
            Key='test/path.jsonl'
        )

    @patch('extract.get_s3_client')
    def test_read_jsonl_logs_extraction_info(self, mock_get_client, caplog):
        """Test that extraction information is logged"""
        # Arrange
        mock_s3 = MagicMock()
        mock_get_client.return_value = mock_s3

        jsonl_content = '{"transcript_text": "Test"}\n'
        mock_body = MagicMock()
        mock_body.read.return_value = jsonl_content.encode('utf-8')
        mock_s3.get_object.return_value = {'Body': mock_body}

        # Act
        read_transcript_jsonl('test/path.jsonl')

        # Assert
        assert "Reading transcript from s3://" in caplog.text
        assert "Extracted" in caplog.text
        assert "characters from" in caplog.text


class TestReadTranscriptForEmbedding:
    """Test suite for read_transcript_for_embedding function"""

    @patch('extract.read_transcript_jsonl')
    @patch('extract.build_transcript_key')
    def test_read_transcript_for_embedding_success(self, mock_build_key, mock_read_jsonl, caplog):
        """Test successfully reading transcript for embedding"""
        # Arrange
        mock_build_key.return_value = "transcripts/podcast_id=5/episode_id=123/data.jsonl"
        mock_read_jsonl.return_value = "This is a full transcript"

        # Act
        result = read_transcript_for_embedding(podcast_id=5, episode_id=123)

        # Assert
        assert result == "This is a full transcript"
        mock_build_key.assert_called_once_with(5, 123)
        mock_read_jsonl.assert_called_once_with(
            "transcripts/podcast_id=5/episode_id=123/data.jsonl"
        )
        assert "Extracting transcript for podcast_id=5, episode_id=123" in caplog.text

    @patch('extract.read_transcript_jsonl')
    @patch('extract.build_transcript_key')
    def test_read_transcript_for_embedding_propagates_filenotfound(self, mock_build_key, mock_read_jsonl):
        """Test FileNotFoundError is propagated"""
        # Arrange
        mock_build_key.return_value = "transcripts/podcast_id=5/episode_id=123/data.jsonl"
        mock_read_jsonl.side_effect = FileNotFoundError("File not found")

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            read_transcript_for_embedding(podcast_id=5, episode_id=123)

    @patch('extract.read_transcript_jsonl')
    @patch('extract.build_transcript_key')
    def test_read_transcript_for_embedding_propagates_exceptions(self, mock_build_key, mock_read_jsonl):
        """Test other exceptions are propagated"""
        # Arrange
        mock_build_key.return_value = "transcripts/podcast_id=5/episode_id=123/data.jsonl"
        mock_read_jsonl.side_effect = Exception("S3 error")

        # Act & Assert
        with pytest.raises(Exception, match="S3 error"):
            read_transcript_for_embedding(podcast_id=5, episode_id=123)

    @patch('extract.read_transcript_jsonl')
    @patch('extract.build_transcript_key')
    def test_read_transcript_for_embedding_long_transcript(self, mock_build_key, mock_read_jsonl):
        """Test handling very long transcripts"""
        # Arrange
        long_transcript = "This is a transcript. " * 1000  # ~22KB
        mock_build_key.return_value = "transcripts/podcast_id=10/episode_id=200/data.jsonl"
        mock_read_jsonl.return_value = long_transcript

        # Act
        result = read_transcript_for_embedding(podcast_id=10, episode_id=200)

        # Assert
        assert result == long_transcript
        assert len(result) > 20000

    @patch('extract.read_transcript_jsonl')
    @patch('extract.build_transcript_key')
    def test_read_transcript_for_embedding_logs_success(self, mock_build_key, mock_read_jsonl, caplog):
        """Test successful extraction is logged"""
        # Arrange
        mock_build_key.return_value = "transcripts/podcast_id=5/episode_id=123/data.jsonl"
        mock_read_jsonl.return_value = "Test transcript"

        # Act
        read_transcript_for_embedding(podcast_id=5, episode_id=123)

        # Assert
        assert "Successfully extracted transcript" in caplog.text


class TestValidateTranscript:
    """Test suite for validate_transcript function"""

    def test_validate_transcript_valid(self):
        """Test validating a good transcript"""
        # Arrange
        transcript = "This is a valid transcript with enough characters to pass validation"

        # Act
        result = validate_transcript(transcript)

        # Assert
        assert result is True

    def test_validate_transcript_minimum_length(self):
        """Test transcript at exactly minimum length"""
        # Arrange
        transcript = "x" * 100  # Exactly 100 characters

        # Act
        result = validate_transcript(transcript, min_length=100)

        # Assert
        assert result is True

    def test_validate_transcript_empty_string(self, caplog):
        """Test empty string is rejected"""
        # Act
        result = validate_transcript("")

        # Assert
        assert result is False
        assert "Transcript is empty" in caplog.text

    def test_validate_transcript_whitespace_only(self, caplog):
        """Test whitespace-only transcript is rejected"""
        # Act
        result = validate_transcript("   \n  \t  ")

        # Assert
        assert result is False
        assert "Transcript is empty" in caplog.text

    def test_validate_transcript_none(self, caplog):
        """Test None value is rejected"""
        # Act
        result = validate_transcript(None)

        # Assert
        assert result is False
        assert "Transcript is empty" in caplog.text

    def test_validate_transcript_too_short(self, caplog):
        """Test transcript below minimum length is rejected"""
        # Arrange
        transcript = "Too short"

        # Act
        result = validate_transcript(transcript, min_length=100)

        # Assert
        assert result is False
        assert "Transcript too short" in caplog.text

    def test_validate_transcript_custom_min_length_pass(self):
        """Test custom minimum length - passing case"""
        # Arrange
        transcript = "Short text"

        # Act
        result = validate_transcript(transcript, min_length=5)

        # Assert
        assert result is True

    def test_validate_transcript_custom_min_length_fail(self):
        """Test custom minimum length - failing case"""
        # Arrange
        transcript = "Short text"

        # Act
        result = validate_transcript(transcript, min_length=50)

        # Assert
        assert result is False

    def test_validate_transcript_just_below_minimum(self, caplog):
        """Test transcript just below minimum length"""
        # Arrange
        transcript = "x" * 99  # One character below minimum

        # Act
        result = validate_transcript(transcript, min_length=100)

        # Assert
        assert result is False
        assert "Transcript too short" in caplog.text
        assert "99 chars" in caplog.text

    def test_validate_transcript_with_leading_trailing_whitespace(self):
        """Test that leading/trailing whitespace is stripped for length calculation"""
        # Arrange
        transcript = "  " + ("x" * 100) + "  "  # 104 chars with whitespace, 100 without

        # Act
        result = validate_transcript(transcript, min_length=100)

        # Assert
        assert result is True
