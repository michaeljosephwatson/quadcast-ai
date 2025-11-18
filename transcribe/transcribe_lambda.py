"""
Lambda function to transcribe podcast audio files using OpenAI Whisper.

Expects S3 structure: {podcast_name}/{episode_id}/audio.mp3
Outputs: {podcast_name}/{episode_id}/transcript.txt
"""

import json
import os
from urllib.parse import unquote_plus
import boto3
import openai
import psycopg2


# Initialize AWS clients
s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')

# Configuration
S3_BUCKET = 'c20-quadcast-s3'
SECRET_NAME = 'c20-quadcast-secrets'
EXPECTED_FILE_PARTS = 3
EXPECTED_FILENAME = 'audio.mp3'
DOWNLOAD_PATH = '/tmp/audio.mp3'


def get_secrets():
    """Retrieve secrets from AWS Secrets Manager."""
    response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
    return json.loads(response['SecretString'])


def parse_s3_key(key):
    """
    Parse S3 key to extract podcast name and episode ID.

    Args:
        key (str): S3 object key

    Returns:
        tuple: (podcast_name, episode_id)

    Raises:
        ValueError: If key structure is invalid
    """
    parts = key.split('/')
    if len(parts) != EXPECTED_FILE_PARTS or parts[2] != EXPECTED_FILENAME:
        raise ValueError(f"Unexpected file structure: {key}")

    return parts[0], parts[1]


def transcribe_audio(file_path, api_key):
    """
    Transcribe audio file using OpenAI Whisper.

    Args:
        file_path (str): Path to audio file
        api_key (str): OpenAI API key

    Returns:
        str: Transcribed text
    """
    openai.api_key = api_key

    with open(file_path, 'rb') as audio_file:
        transcript_response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )

    return transcript_response.text


def upload_transcript(bucket, key, content):
    """
    Upload transcript to S3.

    Args:
        bucket (str): S3 bucket name
        key (str): S3 object key
        content (str): Transcript content
    """
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=content,
        ContentType='text/plain'
    )


def lambda_handler(event, context):
    """
    AWS Lambda handler for audio transcription.

    Args:
        event (dict): Lambda event containing S3 trigger information
        context (object): Lambda context object

    Returns:
        dict: Response with status code and body
    """
    try:
        # Get secrets
        secrets = get_secrets()

        # Extract S3 event information
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = unquote_plus(event['Records'][0]['s3']['object']['key'])

        print(f"Processing: s3://{bucket}/{key}")

        # Parse S3 key
        podcast_name, episode_id = parse_s3_key(key)

        # Download audio file
        s3_client.download_file(bucket, key, DOWNLOAD_PATH)
        print(f"Downloaded to {DOWNLOAD_PATH}")

        # Transcribe audio
        transcript_text = transcribe_audio(
            DOWNLOAD_PATH,
            secrets['openai_api_key']
        )
        print(f"Transcription complete: {len(transcript_text)} characters")

        # Upload transcript
        transcript_key = f"{podcast_name}/{episode_id}/transcript.txt"
        upload_transcript(bucket, transcript_key, transcript_text)
        print(f"Transcript saved to: s3://{bucket}/{transcript_key}")

        update_episode_in_rds(episode_id, transcript_key, secrets)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Transcription complete',
                'podcast': podcast_name,
                'episode': episode_id,
                'transcript_s3_key': transcript_key
            })
        }

    except ValueError as ve:
        print(f"Validation error: {str(ve)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(ve)})
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def update_episode_in_rds(episode_id, transcript_key, secrets):
    """
    Update Episode table in RDS with transcription results.

    Args:
        episode_id (str): Episode identifier
        transcript_key (str): S3 key for transcript
        secrets (dict): Database credentials
    """

    conn = psycopg2.connect(
        host=secrets['DB_HOST'],
        database=secrets['DB_NAME'],
        user=secrets['DB_USER'],
        password=secrets['DB_PASSWORD'],
        port=secrets.get('DB_PORT', '5432')
    )

    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Episode 
            SET transcribed = TRUE, transcript_s3_key = %s 
            WHERE episode_id = %s
        """, (transcript_key, episode_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
