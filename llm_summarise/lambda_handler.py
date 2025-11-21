"""Main Lambda handler for OpenAI analysis."""
import json
import logging
import sys
from s3_client import read_transcript, build_transcript_key, save_summary_to_s3, read_segments, build_segments_key
from analyser import analyze_transcript
from database import store_analysis, episode_exists

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    """Analyzes transcript using OpenAI and stores results in database and S3."""
    logger.info("Starting OpenAI analysis Lambda")
    logger.debug(f"Event: {json.dumps(event)}")

    try:
        # Extract event data
        episode_id = event.get('episode_id')
        podcast_id = event.get('podcast_id')
        transcript_s3_key = event.get('transcript_s3_key')
        logger.debug(
            f"Extracted: episode_id={episode_id}, podcast_id={podcast_id}")

        # Validate required fields
        if not episode_id:
            raise ValueError("Missing required field: episode_id")

        # Build S3 key if not provided
        if not transcript_s3_key:
            if not podcast_id:
                raise ValueError(
                    "Missing required field: podcast_id (needed to build S3 key)")
            transcript_s3_key = build_transcript_key(podcast_id, episode_id)
            logger.info(f"Built S3 key: {transcript_s3_key}")

        # Check episode exists in database
        if not episode_exists(episode_id):
            raise ValueError(f"Episode {episode_id} not found in database")

        logger.info(f"Processing episode {episode_id}")

        # Read transcript from S3
        logger.debug("Reading transcript from S3")
        transcript = read_transcript(transcript_s3_key)
        logger.info(f"Read {len(transcript)} characters")

        # Read segments for speaker identification (optional - won't fail if missing)
        logger.debug("Reading segments from S3")
        segments_s3_key = build_segments_key(podcast_id, episode_id)
        segments = read_segments(segments_s3_key)
        logger.info(f"Read {len(segments)} segments")

        # Analyze with OpenAI (includes speaker identification if segments provided)
        logger.debug("Calling analyze_transcript")
        analysis = analyze_transcript(transcript, segments)
        logger.info(
            f"Analysis: {len(analysis['topics'])} topics, {len(analysis.get('speakers', []))} speakers")

        # Store topics and speakers in database
        logger.debug("Storing analysis in database")
        store_analysis(episode_id, analysis)

        # Store summary in S3
        logger.debug("Saving summary to S3")
        summary_s3_key = save_summary_to_s3(
            podcast_id, episode_id, analysis['summary'])
        logger.info(f"Summary saved to S3: {summary_s3_key}")

        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'episode_id': episode_id,
                'topics_count': len(analysis['topics']),
                'speakers_count': len(analysis.get('speakers', [])),
                'summary_s3_key': summary_s3_key
            })
        }

    except FileNotFoundError as e:
        logger.error(f"Transcript not found: {str(e)}")
        return {
            'statusCode': 404,
            'body': json.dumps({
                'status': 'error',
                'error': 'Transcript not found',
                'message': str(e)
            })
        }

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'status': 'error',
                'error': 'Validation error',
                'message': str(e)
            })
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': 'Internal server error',
                'message': str(e)
            })
        }
