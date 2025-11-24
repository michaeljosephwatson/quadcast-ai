"""S3 extraction operations for embedding pipeline."""
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


def build_transcript_key(podcast_id: int, episode_id: int, filename: str = "data.jsonl") -> str:
    """Build S3 key for transcript file."""
    return f"transcripts/podcast_id={podcast_id}/episode_id={episode_id}/{filename}"


def read_transcript_jsonl(s3_key: str, bucket_name: str = S3_BUCKET) -> str:
    """Read transcript from JSONL file in S3. Extracts 'transcript_text' field from each line and concatenates."""
    s3 = get_s3_client()

    logger.info(f"Reading transcript from s3://{bucket_name}/{s3_key}")

    try:
        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise FileNotFoundError(
                f"Not found: s3://{bucket_name}/{s3_key}") from e
        raise Exception(f"S3 error: {str(e)}") from e

    content = response['Body'].read().decode('utf-8')

    # Parse JSONL - each line is a JSON object
    transcript_parts = []
    for line_num, line in enumerate(content.strip().split('\n'), 1):
        if not line.strip():
            continue

        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse JSON on line {line_num}: {line[:100]}")
            raise Exception(
                f"Invalid JSONL format at line {line_num}: {str(e)}") from e

        text = data.get('transcript_text', '')
        if not text:
            logger.warning(f"Line {line_num} missing 'transcript_text'")

        transcript_parts.append(text)

    if not transcript_parts:
        raise Exception(f"No transcript text found in {s3_key}")

    full_transcript = ' '.join(transcript_parts)
    logger.info(
        f"Extracted {len(full_transcript)} characters from {len(transcript_parts)} segments")

    return full_transcript


def read_transcript_for_embedding(podcast_id: int, episode_id: int) -> str:
    """Read and extract transcript from S3 for embedding pipeline. Returns full transcript text as string."""
    logger.info(
        f"Extracting transcript for podcast_id={podcast_id}, episode_id={episode_id}")

    # Build S3 key
    s3_key = build_transcript_key(podcast_id, episode_id)

    # Read and parse transcript
    transcript = read_transcript_jsonl(s3_key)

    logger.info(
        f"Successfully extracted transcript: {len(transcript)} characters")

    return transcript


def validate_transcript(transcript: str, min_length: int = 100) -> bool:
    """Validate transcript meets minimum requirements for embedding."""
    if not transcript or not transcript.strip():
        logger.warning("Transcript is empty")
        return False

    if len(transcript.strip()) < min_length:
        logger.warning(
            f"Transcript too short: {len(transcript.strip())} chars (min: {min_length})")
        return False

    return True
