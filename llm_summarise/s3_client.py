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
    """Read transcript from JSONL file in S3.Extracts 'text' field from each line and concatenates. Returns full transcript as string"""
    s3 = get_s3_client()

    try:
        logger.info(f"Reading JSONL from s3://{bucket_name}/{s3_key}")

        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        content = response['Body'].read().decode('utf-8')

        # Parse JSONL - each line is a JSON object
        transcript_parts = []
        for line in content.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    text = data.get('transcript_text', '')
                    if not text:
                        logger.warning(
                            f"Line missing 'transcript_text': {line[:100]}")
                    transcript_parts.append(text)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON line: {line[:100]}")
                    raise Exception(f"Invalid JSONL format: {str(e)}") from e

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


def read_segments(s3_key: str, bucket_name: str = S3_BUCKET) -> list:
    """
    Read diarized segments from JSONL file in S3.

    Returns:
        List of segment dicts with keys: start_time, end_time, speaker, text
    """
    s3 = get_s3_client()

    try:
        logger.info(f"Reading segments from s3://{bucket_name}/{s3_key}")

        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        content = response['Body'].read().decode('utf-8')

        segments = []
        for line in content.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    segments.append(data)
                except json.JSONDecodeError as e:
                    logger.warning(
                        f"Failed to parse segment line: {line[:100]}")

        logger.info(f"Read {len(segments)} segments")
        return segments

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.warning(
                f"Segments file not found: s3://{bucket_name}/{s3_key}")
            return []  # Return empty list if segments don't exist
        raise Exception(f"S3 error: {str(e)}") from e


def save_summary_to_s3(podcast_id: int, episode_id: int, summary: str, bucket_name: str = S3_BUCKET) -> str:
    """
    Save analysis summary to S3.

    Args:
        podcast_id: Podcast ID
        episode_id: Episode ID
        summary: Summary text
        bucket_name: S3 bucket name

    Returns:
        S3 key where summary was saved
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


def build_segments_key(podcast_id: int, episode_id: int, filename: str = "data.jsonl") -> str:
    """Build S3 key for segments file."""
    return f"segments/podcast_id={podcast_id}/episode_id={episode_id}/{filename}"


def build_transcript_key(podcast_id: int, episode_id: int, filename: str = "data.jsonl") -> str:
    """Build S3 key for transcript file.Returns S3 key path: transcripts/podcast_id={podcast_id}/episode_id={episode_id}/{filename}"""
    return f"transcripts/podcast_id={podcast_id}/episode_id={episode_id}/{filename}"


def build_segment_key(podcast_id: int, episode_id: int, filename: str) -> str:
    """Build S3 key for segment file.Returns S3 key path: segments/podcast_id={podcast_id}/episode_id={episode_id}/{filename}"""
    return f"segments/podcast_id={podcast_id}/episode_id={episode_id}/{filename}"
