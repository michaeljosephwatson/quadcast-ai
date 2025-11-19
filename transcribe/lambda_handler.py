import os
import json
import boto3
import requests
from extract_urls import get_rds_connection, get_untranscribed_episode, update_episode_transcribed
from transcribe import transcribe_audio

s3_client = boto3.client('s3')
S3_BUCKET = "c20-quadcast-s3-bucket"


def download_audio(audio_url, local_path):
    """Download audio file from URL to local path."""
    print(f"Downloading audio from: {audio_url}")

    response = requests.get(audio_url, stream=True, timeout=300)
    response.raise_for_status()

    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Downloaded to: {local_path}")


def upload_to_s3(local_path, s3_key):
    """Upload file to S3."""
    print(f"Uploading to S3: {s3_key}")

    s3_client.upload_file(local_path, S3_BUCKET, s3_key)

    print(f"Uploaded successfully")
    return s3_key


def save_transcript_files(podcast_name, podcast_id, episode_title, episode_id, transcript_data):
    """Save transcript and diarized segments to /tmp and upload to S3."""

    # Save transcript text
    transcript_path = f"/tmp/episode_{episode_id}_transcript.txt"
    with open(transcript_path, 'w', encoding='utf-8') as f:
        f.write(transcript_data['text'])

    # Save diarized segments
    segments_path = f"/tmp/episode_{episode_id}_diarized_segments.txt"
    with open(segments_path, 'w', encoding='utf-8') as f:
        for seg in transcript_data['segments']:
            f.write(
                f"[{seg['start']:.2f}-{seg['end']:.2f}] "
                f"Speaker {seg['speaker']}: {seg['text']}\n"
            )

    # Upload to S3 with partitioned structure: {podcast_name}{podcast_id}/{episode_title}{episode_id}/
    transcript_s3_key = upload_to_s3(
        transcript_path,
        f"{podcast_name}({podcast_id})/{episode_title}({episode_id})/transcript.txt"
    )

    segments_s3_key = upload_to_s3(
        segments_path,
        f"{podcast_name}({podcast_id})/{episode_title}({episode_id})/diarized_segments.txt"
    )

    return transcript_s3_key, segments_s3_key


def lambda_handler(event, context):
    """
    Main Lambda handler for transcription.
    Processes ONE untranscribed episode per invocation.
    """

    print("Starting transcription Lambda...")

    try:
        # Connect to database
        conn = get_rds_connection()

        # Get next untranscribed episode
        episode = get_untranscribed_episode(conn)

        if not episode:
            print("No untranscribed episodes found")
            conn.close()
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'no_work'})
            }

        episode_id = episode['episode_id']
        podcast_id = episode['podcast_id']
        podcast_name = episode['podcast_name']
        episode_title = episode['episode_title']
        audio_url = episode['audio_url']

        print(f"Processing episode {episode_id}: {episode_title}")

        # Download audio to /tmp
        audio_path = f"/tmp/episode_{episode_id}.mp3"
        download_audio(audio_url, audio_path)

        # Transcribe audio
        print("Starting transcription...")
        transcript_data = transcribe_audio(audio_path)
        print("Transcription complete!")

        # Save and upload results to S3
        transcript_s3_key, segments_s3_key = save_transcript_files(
            podcast_name, podcast_id, episode_title, episode_id, transcript_data)

        # Update database (only mark as transcribed)
        update_episode_transcribed(conn, episode_id)

        # Cleanup
        os.remove(audio_path)
        conn.close()

        print(f"Successfully transcribed episode {episode_id}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'episode_id': episode_id,
                'transcript_s3_key': transcript_s3_key,
                'segments_s3_key': segments_s3_key
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")

        if 'conn' in locals():
            conn.close()

        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'message': str(e)
            })
        }
