"""S3 operations for reading transcripts."""
import os
import json
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


# Configuration
S3_BUCKET = os.getenv('S3_BUCKET', 'c20-quadcast-s3-bucket')
AWS_REGION = os.getenv('AWS_REGION', 'eu-west-2')


def get_s3_client():
    """Get boto3 S3 client."""
    return boto3.client('s3', region_name=AWS_REGION)


def read_transcript_jsonl(s3_key: str, bucket_name: str = S3_BUCKET) -> str:
    """
    Read transcript from JSONL file in S3.
    Extracts 'text' field from each line and concatenates.

    Returns:
        Full transcript as string
    """
    s3 = get_s3_client()

    try:
        logger.info(f"Reading JSONL from s3://{bucket_name}/{s3_key}")

        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        content = response['Body'].read().decode('utf-8')

        # Parse JSONL - each line is a JSON object
        transcript_parts = []
        for line in content.strip().split('\n'):
            if line:
                data = json.loads(line)
                # Extract text field (adjust field name if different)
                text = data.get('transcript_text', '')
                transcript_parts.append(text)

        full_transcript = ' '.join(transcript_parts)
        logger.info(
            f"Read {len(full_transcript)} characters from {len(transcript_parts)} segments")

        return full_transcript

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise FileNotFoundError(f"Not found: s3://{bucket_name}/{s3_key}")
        raise Exception(f"S3 error: {str(e)}") from e


def read_transcript(s3_key: str, bucket_name: str = S3_BUCKET) -> str:
    """
    Read transcript file from S3.
    Auto-detects if .jsonl or .txt format.
    """
    if s3_key.endswith('.jsonl'):
        return read_transcript_jsonl(s3_key, bucket_name)

    # Plain text format
    s3 = get_s3_client()

    try:
        logger.info(f"Reading from s3://{bucket_name}/{s3_key}")

        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        transcript = response['Body'].read().decode('utf-8')

        logger.info(f"Read {len(transcript)} characters")
        return transcript

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise FileNotFoundError(f"Not found: s3://{bucket_name}/{s3_key}")
        raise Exception(f"S3 error: {str(e)}") from e


def transcript_exists(s3_key: str, bucket_name: str = S3_BUCKET) -> bool:
    """Check if transcript exists in S3."""
    s3 = get_s3_client()

    try:
        s3.head_object(Bucket=bucket_name, Key=s3_key)
        return True
    except ClientError:
        return False


def save_summary_to_s3(podcast_id: int, episode_id: int, summary: str, bucket_name: str = S3_BUCKET):
    """
    Save analysis summary to S3.

    Args:
        podcast_id: Podcast ID
        episode_id: Episode ID
        summary: Summary text
        bucket_name: S3 bucket name
    """
    s3 = get_s3_client()

    s3_key = f"summaries/podcast_id={podcast_id}/episode_id={episode_id}/summary.txt"

    try:
        logger.info(f"Saving summary to s3://{bucket_name}/{s3_key}")

        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=summary.encode('utf-8'),
            ContentType='text/plain'
        )

        logger.info(f"Summary saved ({len(summary)} chars)")
        return s3_key

    except Exception as e:
        raise Exception(f"Failed to save summary to S3: {str(e)}") from e


def build_transcript_key(podcast_id: int, episode_id: int, filename: str = "data.jsonl") -> str:
    """Build S3 key for transcript file."""
    return f"transcripts/podcast_id={podcast_id}/episode_id={episode_id}/{filename}"


def build_segment_key(podcast_id: int, episode_id: int, filename: str) -> str:
    """Build S3 key for segment file."""
    return f"segments/podcast_id={podcast_id}/episode_id={episode_id}/{filename}"
