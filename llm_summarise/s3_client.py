"""S3 operations for reading transcripts."""
import os
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


def read_transcript(s3_key: str, bucket_name: str = S3_BUCKET) -> str:
    """Read transcript file from S3, returns transcript text as string. Raises FileNotFoundError: If transcript doesn't exist."""
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
    """Check if transcript exists in S3.Returns true if exists, False otherwise"""
    s3 = get_s3_client()

    try:
        s3.head_object(Bucket=bucket_name, Key=s3_key)
        return True
    except ClientError:
        return False
