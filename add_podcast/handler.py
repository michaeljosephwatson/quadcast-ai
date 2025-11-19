"""This file acts as the entry point for the add_podcast Lambda function."""

import json
from load import load_data_to_db_from_rss
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Entry point for the lambda function to add podcast data from an RSS feed to the database. 
    Takes the RSS feed URL from the event body."""

    logger.info(f"Received event: %s", event)

    body = json.loads(event['body'])
    rss_url = body['podcast_url']

    logger.info("Received RSS URL: %s", rss_url)

    if rss_url:
        load_data_to_db_from_rss(rss_url)
        return {
            'statusCode': 200,
            'body': json.dumps('Podcast data added successfully!')
        }

    return {
        'statusCode': 400,
        'body': json.dumps('Invalid request: podcast_url is required.')
    }
