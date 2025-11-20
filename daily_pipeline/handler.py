"""
AWS Lambda handler for the daily podcast episode pipeline.

This handler orchestrates the complete Extract-Transform-Load (ETL) pipeline:
1. Extract: Fetch new episodes from RSS feeds for all podcasts
2. Transform: Validate and transform episode data
3. Load: Insert validated episodes into RDS database

Environment variables are provided via:
- Lambda environment variables (automatically available as os.getenv)
- Local .env file (for local development only)
"""

import logging
import json
from extract_episodes import get_rds_connection, extract_all_new_episodes
from transform_episodes import transform_all_episodes
from load_episodes import load_all_episodes

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event=None, context=None):
    """
    Lambda handler that runs the daily episode pipeline.

    Args:
        event: Lambda event (not used, but required by Lambda signature)
        context: Lambda context object

    Returns:
        dict: Response object with status code and pipeline statistics
              {
                  'statusCode': 200 or 500,
                  'body': JSON string containing pipeline results or error message
              }
    """
    try:
        logger.info("Starting daily episode pipeline")

        # Step 1: Extract new episodes from RSS feeds
        logger.info("Step 1: Extracting episodes from RSS feeds")
        conn = get_rds_connection()
        extracted_data = extract_all_new_episodes(conn)
        logger.info("Successfully extracted episodes for %s podcasts",
                    len(extracted_data))

        # Step 2: Transform and validate episode data
        logger.info("Step 2: Transforming and validating episode data")
        transformed_data = transform_all_episodes(extracted_data)
        logger.info("Successfully transformed %s podcasts with validated episodes", len(
            transformed_data))

        # Step 3: Load validated episodes into database
        logger.info("Step 3: Loading episodes into RDS database")
        load_stats = load_all_episodes(conn, transformed_data)
        logger.info("Successfully loaded episodes: %s inserted, %s skipped",
                    load_stats['total_inserted'], load_stats['total_skipped'])

        # Close database connection
        conn.close()

        # Return success response with detailed statistics
        response_body = {
            'status': 'success',
            'message': 'Daily episode pipeline completed successfully',
            'summary': {
                'total_podcasts_checked': load_stats['total_podcasts'],
                'total_episodes_processed': load_stats['total_episodes'],
                'total_episodes_inserted': load_stats['total_inserted'],
                'total_episodes_skipped': load_stats['total_skipped']
            },
            'details': load_stats['podcast_stats']
        }

        logger.info("Pipeline completed successfully")
        return {
            'statusCode': 200,
            'body': json.dumps(response_body)
        }

    except Exception as e:
        # Log the error and return failure response
        logger.error("Pipeline failed with error: %s", str(e), exc_info=True)
        error_response = {
            'error': 'Pipeline failed',
            'message': str(e)
        }

        try:
            if 'conn' in locals():
                conn.close()
        except Exception as close_err:
            logger.warning("Failed to close database connection during error handling: %s", str(
                close_err), exc_info=True)

        return {
            'statusCode': 500,
            'body': json.dumps(error_response)
        }


if __name__ == "__main__":
    # For local testing
    from dotenv import load_dotenv
    load_dotenv()
    response = lambda_handler(None, None)
    print(json.dumps(json.loads(response['body']), indent=2))
