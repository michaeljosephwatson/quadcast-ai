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
    """Returns boto3 S3 client for AWS region."""
    logger.debug(f"Getting S3 client for region: {AWS_REGION}")
    return boto3.client('s3', region_name=AWS_REGION)


def read_transcript_jsonl(s3_key: str, bucket_name: str = S3_BUCKET) -> str:
    """Reads JSONL transcript from S3 and returns concatenated transcript string."""
    logger.info(f"Reading JSONL transcript from s3://{bucket_name}/{s3_key}")
    s3 = get_s3_client()

    try:
        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        content = response['Body'].read().decode('utf-8')
        logger.debug(f"Downloaded file: {len(content)} bytes")

        # Parse JSONL - each line is a JSON object
        transcript_parts = []
        for line in content.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    text = data.get('transcript_text', '')
                    if not text:
                        logger.warning(f"Line missing 'transcript_text': {line[:100]}")
                    transcript_parts.append(text)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON line: {line[:100]}")
                    raise Exception(f"Invalid JSONL format: {str(e)}") from e

        full_transcript = ' '.join(transcript_parts)
        logger.info(f"Read {len(full_transcript)} characters from {len(transcript_parts)} segments")
        return full_transcript

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.error(f"File not found: s3://{bucket_name}/{s3_key}")
            raise FileNotFoundError(f"Not found: s3://{bucket_name}/{s3_key}")
        logger.error(f"S3 error: {str(e)}")
        raise Exception(f"S3 error: {str(e)}") from e


def read_transcript(s3_key: str, bucket_name: str = S3_BUCKET) -> str:
    """Reads transcript from S3 (auto-detects .jsonl or .txt format)."""
    logger.info(f"Reading transcript from s3://{bucket_name}/{s3_key}")
    if s3_key.endswith('.jsonl'):
        return read_transcript_jsonl(s3_key, bucket_name)

    # Plain text format
    s3 = get_s3_client()

    try:
        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        transcript = response['Body'].read().decode('utf-8')
        logger.info(f"Read {len(transcript)} characters")
        return transcript

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.error(f"File not found: s3://{bucket_name}/{s3_key}")
            raise FileNotFoundError(f"Not found: s3://{bucket_name}/{s3_key}")
        logger.error(f"S3 error: {str(e)}")
        raise Exception(f"S3 error: {str(e)}") from e


def transcript_exists(s3_key: str, bucket_name: str = S3_BUCKET) -> bool:
    """Checks if transcript exists in S3."""
    logger.debug(f"Checking if transcript exists: s3://{bucket_name}/{s3_key}")
    s3 = get_s3_client()

    try:
        s3.head_object(Bucket=bucket_name, Key=s3_key)
        logger.debug("Transcript exists")
        return True
    except ClientError:
        logger.debug("Transcript does not exist")
        return False


def read_segments(s3_key: str, bucket_name: str = S3_BUCKET) -> list:
    """Reads diarized segments from JSONL in S3 (returns empty list if not found)."""
    logger.info(f"Reading segments from s3://{bucket_name}/{s3_key}")
    s3 = get_s3_client()

    try:
        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        content = response['Body'].read().decode('utf-8')

        segments = []
        for line in content.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    segments.append(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse segment line: {line[:100]}")

        logger.info(f"Read {len(segments)} segments")
        return segments

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.warning(f"Segments file not found: s3://{bucket_name}/{s3_key}")
            return []
        logger.error(f"S3 error: {str(e)}")
        raise Exception(f"S3 error: {str(e)}") from e


def save_summary_to_s3(podcast_id: int, episode_id: int, analysis: dict, bucket_name: str = S3_BUCKET) -> str:
    """Saves analysis data to S3 as JSONL and returns the S3 key."""
    logger.info(f"Saving analysis for podcast {podcast_id}, episode {episode_id}")
    s3 = get_s3_client()

    s3_key = f"summaries/podcast_id={podcast_id}/episode_id={episode_id}/data.jsonl"

    try:
        # Create JSONL format - single line with complete analysis
        # Note: podcast_id and episode_id are in the S3 path (partitions), not in the data
        jsonl_data = {
            'summary': analysis.get('summary', ''),
            'topics': analysis.get('topics', []),
            'speakers': analysis.get('speakers', [])
        }
        jsonl_content = json.dumps(jsonl_data) + '\n'

        logger.debug(f"Uploading to s3://{bucket_name}/{s3_key}")
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=jsonl_content.encode('utf-8'),
            ContentType='application/x-ndjson'
        )

        logger.info(f"Analysis saved ({len(jsonl_content)} bytes, {len(analysis.get('topics', []))} topics, {len(analysis.get('speakers', []))} speakers)")
        return s3_key

    except Exception as e:
        logger.error(f"Failed to save analysis to S3: {str(e)}")
        raise Exception(f"Failed to save analysis to S3: {str(e)}") from e


def build_segments_key(podcast_id: int, episode_id: int, filename: str = "data.jsonl") -> str:
    """Builds S3 key path for segments file."""
    logger.debug(f"Building segments key: podcast {podcast_id}, episode {episode_id}")
    return f"segments/podcast_id={podcast_id}/episode_id={episode_id}/{filename}"


def build_transcript_key(podcast_id: int, episode_id: int, filename: str = "data.jsonl") -> str:
    """Builds S3 key path for transcript file."""
    logger.debug(f"Building transcript key: podcast {podcast_id}, episode {episode_id}")
    return f"transcripts/podcast_id={podcast_id}/episode_id={episode_id}/{filename}"


def build_segment_key(podcast_id: int, episode_id: int, filename: str) -> str:
    """Builds S3 key path for segment file."""
    logger.debug(f"Building segment key: podcast {podcast_id}, episode {episode_id}")
    return f"segments/podcast_id={podcast_id}/episode_id={episode_id}/{filename}"
