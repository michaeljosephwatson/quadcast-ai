"""Lambda handler for embedding ETL pipeline."""
import json
import logging
from extract import read_transcript_for_embedding, validate_transcript
from transform import transform_transcript, validate_embeddings
from load import load_embeddings

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Extract transcript from S3, transform into embeddings, load into database."""
    logger.info("Starting embedding ETL pipeline")
    logger.info("Event: %s", json.dumps(event))

    try:
        # Extract event data
        episode_id = event.get('episode_id')
        podcast_id = event.get('podcast_id')

        # Validate required fields
        if not episode_id:
            raise ValueError("Missing required field: episode_id")

        if not podcast_id:
            raise ValueError("Missing required field: podcast_id")

        logger.info("Processing podcast_id=%s, episode_id=%s",
                    podcast_id, episode_id)

        # EXTRACT: Read transcript from S3
        logger.info("📥 EXTRACT: Reading transcript from S3...")
        transcript = read_transcript_for_embedding(podcast_id, episode_id)
        logger.info("Extracted transcript: %s characters", len(transcript))

        # Validate transcript
        if not validate_transcript(transcript):
            raise ValueError(
                "Transcript validation failed - too short or empty")

        # TRANSFORM: Chunk and embed transcript
        logger.info("🔄 TRANSFORM: Chunking and embedding transcript...")
        embedded_chunks = transform_transcript(transcript)
        logger.info("Generated %s embedded chunks", len(embedded_chunks))

        # Validate embeddings
        if not validate_embeddings(embedded_chunks):
            raise ValueError(
                "Embedding validation failed - invalid dimensions")

        # LOAD: Store embeddings in database
        logger.info("💾 LOAD: Storing embeddings in database...")
        load_embeddings(episode_id, embedded_chunks)
        logger.info("Successfully stored %s embeddings", len(embedded_chunks))

        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'episode_id': episode_id,
                'podcast_id': podcast_id,
                'chunks_stored': len(embedded_chunks),
                'transcript_length': len(transcript)
            })
        }

    except FileNotFoundError as e:
        logger.error("Transcript not found: %s", str(e))
        return {
            'statusCode': 404,
            'body': json.dumps({
                'status': 'error',
                'error': 'Transcript not found',
                'message': str(e)
            })
        }

    except ValueError as e:
        logger.error("Validation error: %s", str(e))
        return {
            'statusCode': 400,
            'body': json.dumps({
                'status': 'error',
                'error': 'Validation error',
                'message': str(e)
            })
        }

    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': 'Internal server error',
                'message': str(e)
            })
        }
