"""This file acts as the entry point for the add_podcast Lambda function."""

import json
from load import load_data_to_db_from_rss
import logging
import boto3
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Entry point for the lambda function to add podcast data from an RSS feed to the database.
    Takes the RSS feed URL from the event body."""

    logger.info("Received event: %s", event)

    body = json.loads(event['body'])
    rss_url = body.get('podcast_url')

    logger.info("Received RSS URL: %s", rss_url)

    if not rss_url:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid request: podcast_url is required.'})
        }

    try:
        result = load_data_to_db_from_rss(rss_url)

        # Trigger the episode transcription workflow only for NEW podcasts
        if not result['is_duplicate']:
            try:
                sfn_client = boto3.client('stepfunctions', region_name='eu-west-2')
                sfn_client.start_execution(
                    stateMachineArn='arn:aws:states:eu-west-2:129033205317:stateMachine:c20-quadcast-episode-transcription-workflow',
                    name='triggered-by-add-podcast-' + str(uuid.uuid4()),
                    input=json.dumps({})
                )
                logger.info("Successfully triggered episode transcription workflow")
            except Exception as e:
                logger.error("Failed to trigger workflow: %s", str(e))
                # Don't fail the add_podcast request if workflow trigger fails

        # Return different response based on duplicate status
        if result['is_duplicate']:
            return {
                'statusCode': 409,
                'body': json.dumps({
                    'message': 'Podcast already exists',
                    'is_duplicate': True
                })
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Podcast data added successfully!',
                    'is_duplicate': False
                })
            }

    except Exception as e:
        logger.error("Error processing podcast: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
