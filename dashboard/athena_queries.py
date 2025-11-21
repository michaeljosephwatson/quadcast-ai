import boto3
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

S3_BUCKET = "c20-quadcast-athena-results"
S3_OUTPUT_LOCATION = f"s3://{S3_BUCKET}/query-results/"
DATABASE_NAME = "c20_quadcast_db"
REGION = "eu-west-2"


def get_athena_connection() -> boto3.client:
    """Get Athena client connection"""
    client = boto3.client('athena', region_name=REGION)
    return client


if __name__ == "__main__":
    athena_client = get_athena_connection()
    logger.info("✅ Athena client created")
