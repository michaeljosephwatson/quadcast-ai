"""Tests for S3 client."""
import boto3
from moto import mock_aws
import pytest
from s3_client import read_transcript, transcript_exists


BUCKET = 'test-bucket'
TRANSCRIPT_KEY = 'Podcast(1)/Episode(123)/transcript.txt'
TRANSCRIPT_TEXT = "This is a test podcast transcript about AI."


@pytest.fixture
def mock_s3():
    """Setup mock S3 with test data."""
    with mock_aws():
        s3 = boto3.client('s3', region_name='eu-west-2')

        # Create bucket
        s3.create_bucket(
            Bucket=BUCKET,
            CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'}
        )

        # Upload test transcript
        s3.put_object(
            Bucket=BUCKET,
            Key=TRANSCRIPT_KEY,
            Body=TRANSCRIPT_TEXT.encode('utf-8')
        )

        yield s3


def test_read_transcript_success(mock_s3):
    """Should read transcript successfully."""
    transcript = read_transcript(TRANSCRIPT_KEY, BUCKET)

    assert transcript == TRANSCRIPT_TEXT
    assert len(transcript) > 0


def test_read_transcript_not_found(mock_s3):
    """Should raise FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        read_transcript('Missing(1)/Episode(999)/transcript.txt', BUCKET)


def test_transcript_exists_true(mock_s3):
    """Should return True if transcript exists."""
    exists = transcript_exists(TRANSCRIPT_KEY, BUCKET)
    assert exists is True


def test_transcript_exists_false(mock_s3):
    """Should return False if transcript doesn't exist."""
    exists = transcript_exists(
        'Missing(1)/Episode(999)/transcript.txt', BUCKET)
    assert exists is False


def test_read_empty_transcript(mock_s3):
    """Should handle empty transcripts."""
    empty_key = 'Empty(1)/Episode(1)/transcript.txt'

    mock_s3.put_object(Bucket=BUCKET, Key=empty_key, Body=b'')

    transcript = read_transcript(empty_key, BUCKET)
    assert transcript == ''


def test_read_large_transcript(mock_s3):
    """Should handle large transcripts."""
    large_key = 'Large(1)/Episode(1)/transcript.txt'
    large_text = "Test content. " * 1000  # ~14KB

    mock_s3.put_object(Bucket=BUCKET, Key=large_key,
                       Body=large_text.encode('utf-8'))

    transcript = read_transcript(large_key, BUCKET)
    assert len(transcript) > 10000
    assert transcript == large_text
