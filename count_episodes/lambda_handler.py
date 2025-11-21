"""Lambda function to count untranscribed episodes in the database."""

import os
import json
import logging
import boto3
from psycopg2 import connect
from psycopg2.extensions import connection

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_secret():
    """Retrieve database credentials from AWS Secrets Manager"""
    secret_name = "c20-quadcast-secrets"
    region_name = os.getenv("AWS_REGION", "eu-west-2")

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])

    return secret


def get_rds_connection() -> connection:
    """Returns the connection to the RDS database"""

    # Check if running locally or in Lambda
    if os.getenv("USE_SECRETS_MANAGER") == "true":
        secret = get_secret()
        conn = connect(
            host=secret['RDS_HOST'],
            database=secret['RDS_DB_NAME'],
            user=secret['RDS_USERNAME'],
            password=secret['RDS_PASSWORD'],
            port=int(secret['RDS_PORT'])
        )
    else:
        conn = connect(
            host=os.getenv("RDS_HOST"),
            database=os.getenv("RDS_DB_NAME"),
            user=os.getenv("RDS_USERNAME"),
            password=os.getenv("RDS_PASSWORD"),
            port=int(os.getenv("RDS_PORT", 5432))
        )

    return conn


def count_untranscribed_episodes(conn: connection) -> int:
    """Count episodes that need transcription."""

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM episode
            WHERE transcribed = FALSE
        """)
        result = cursor.fetchone()
        return result[0] if result else 0


def lambda_handler(event, context):
    """
    Lambda handler to count untranscribed episodes.

    Returns:
        dict: Response with count of untranscribed episodes
    """

    logger.info("Starting count_episodes Lambda")

    try:
        # Connect to database
        conn = get_rds_connection()

        # Count untranscribed episodes
        count = count_untranscribed_episodes(conn)

        # Close connection
        conn.close()

        logger.info("Found %s untranscribed episodes", count)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'count': count
            })
        }

    except Exception as e:
        logger.error("Error counting episodes: %s", str(e), exc_info=True)

        if 'conn' in locals():
            conn.close()

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to count episodes',
                'message': str(e)
            })
        }
