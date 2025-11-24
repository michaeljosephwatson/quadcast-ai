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


def get_transcript_for_episode(client: boto3.client, podcast_id: int, episode_id: int) -> str:
    """Fetch transcript for a given episode from Athena"""

    query = f"""
    SELECT transcript_text
    FROM transcripts 
    WHERE podcast_id = '{podcast_id}'
    AND episode_id = '{episode_id}'
    """

    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': DATABASE_NAME
        },
        ResultConfiguration={
            'OutputLocation': S3_OUTPUT_LOCATION
        }
    )

    query_execution_id = response['QueryExecutionId']

    # Wait for the query to complete
    while True:
        query_status = client.get_query_execution(
            QueryExecutionId=query_execution_id)
        status = query_status['QueryExecution']['Status']['State']

        if status == 'SUCCEEDED':
            break
        elif status in ['FAILED', 'CANCELLED']:
            error_message = query_status['QueryExecution']['Status'].get(
                'StateChangeReason', 'Unknown error')
            logger.error(f"Query failed: {error_message}")
            raise Exception(f"Query failed: {error_message}")

        time.sleep(2)

    # Get results
    result_response = client.get_query_results(
        QueryExecutionId=query_execution_id)

    rows = result_response['ResultSet']['Rows']

    # Check if we have data (more than just header)
    if len(rows) <= 1:
        raise ValueError(
            f"No transcript found for podcast_id={podcast_id}, episode_id={episode_id}")

    transcript = rows[1]['Data'][0].get('VarCharValue')

    if not transcript:
        raise ValueError(
            f"Transcript is empty for podcast_id={podcast_id}, episode_id={episode_id}")

    return transcript


def get_summary_for_episode(client: boto3.client, podcast_id: str, episode_id: str) -> dict:
    """Fetch summary, topics, and speakers for a given episode from Athena"""

    query = f"""
    SELECT summary, topics, speakers
    FROM summaries 
    WHERE podcast_id = '{podcast_id}'
    AND episode_id = '{episode_id}'
    """

    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': DATABASE_NAME
        },
        ResultConfiguration={
            'OutputLocation': S3_OUTPUT_LOCATION
        }
    )

    query_execution_id = response['QueryExecutionId']

    # Wait for the query to complete
    while True:
        query_status = client.get_query_execution(
            QueryExecutionId=query_execution_id)
        status = query_status['QueryExecution']['Status']['State']

        if status == 'SUCCEEDED':
            break
        elif status in ['FAILED', 'CANCELLED']:
            error_message = query_status['QueryExecution']['Status'].get(
                'StateChangeReason', 'Unknown error')
            logger.error(f"Query failed: {error_message}")
            raise Exception(f"Query failed: {error_message}")

        time.sleep(2)

    # Get results
    result_response = client.get_query_results(
        QueryExecutionId=query_execution_id)

    rows = result_response['ResultSet']['Rows']

    # Check if we have data (more than just header)
    if len(rows) <= 1:
        raise ValueError(
            f"No summary found for podcast_id={podcast_id}, episode_id={episode_id}")

    data_row = rows[1]['Data']
    summary = data_row[0].get('VarCharValue', '')
    topics = data_row[1].get('VarCharValue', '')
    speakers = data_row[2].get('VarCharValue', '')

    if not summary:
        raise ValueError(
            f"Summary is empty for podcast_id={podcast_id}, episode_id={episode_id}")

    return {
        'summary': summary,
        'topics': topics,
        'speakers': speakers
    }


if __name__ == "__main__":
    athena_client = get_athena_connection()
    logger.info("✅ Athena client created")

    # try:
    #     transcript = get_transcript_for_episode(
    #         athena_client, podcast_id=4, episode_id=10)
    #     logger.info(f"✅ Transcript fetched: {transcript}")
    # except ValueError as e:
    #     logger.warning(f"⚠️  {e}")
    # except Exception as e:
    #     logger.error(f"❌ Error: {e}")

    try:
        summary_data = get_summary_for_episode(
            athena_client, podcast_id='4', episode_id='10')
        logger.info(f"✅ Summary data fetched: {summary_data}")
    except ValueError as e:
        logger.warning(f"⚠️  {e}")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
