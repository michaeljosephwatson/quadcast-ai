# transcribe_lambda.py
"""
Lambda: Transcribe podcast audio using GPT-4o-transcribe-diarise.
Trigger: S3 PUT event
Input key pattern: {podcast}/{episode}/audio.mp3

Outputs:
  {podcast}/{episode}/transcript.txt
  {podcast}/{episode}/diarisation.json
"""

import os
import json
from pathlib import Path
from urllib.parse import unquote_plus
import boto3
from openai import OpenAI

# --- Clients ---
s3 = boto3.client("s3")
client = OpenAI()

# --- Optional DB config (if you upsert metadata) ---
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")


# --------------------------
# Parsing helpers
# --------------------------
def parse_s3_event(event):
    record = event["Records"][0]
    bucket = record["s3"]["bucket"]["name"]
    key = unquote_plus(record["s3"]["object"]["key"])
    return bucket, key


def parse_key_structure(key):
    """
    Expected:
        podcast_name/episode_id/audio.mp3
    Returns:
        podcast_name, episode_id, filename
    """
    parts = key.split("/")
    if len(parts) < 3:
        raise ValueError(f"Invalid key structure: {key}")

    return parts[0], parts[1], parts[-1]


# --------------------------
# S3 Download / Upload
# --------------------------
def download_audio(bucket, key):
    local_path = f"/tmp/{key.replace('/', '_')}"
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"â¬‡ï¸ Downloading s3://{bucket}/{key}")
    s3.download_file(bucket, key, local_path)
    print(f"âœ… Downloaded to {local_path}")

    return local_path


def upload_text(bucket, key, text):
    print(f"â¬†ï¸ Uploading text â†’ s3://{bucket}/{key}")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=text.encode("utf-8"),
        ContentType="text/plain"
    )
    print("âœ… Uploaded transcript")


def upload_json(bucket, key, obj):
    print(f"â¬†ï¸ Uploading JSON â†’ s3://{bucket}/{key}")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(obj, indent=2).encode("utf-8"),
        ContentType="application/json"
    )
    print("âœ… Uploaded diarisation JSON")


# --------------------------
# GPT-4o Processing
# --------------------------
def run_gpt4o_transcription(local_audio_path: str):
    suffix = local_audio_path.split(".")[-1].lower()

    # Load file bytes
    with open(local_audio_path, "rb") as f:
        audio_bytes = f.read()

    print("ðŸŽ§ Calling gpt-4o-transcribe-diarise...")

    response = client.responses.create(
        model="gpt-4o-transcribe-diarise",
        input=[
            {
                "role": "user",
                "input_audio": {
                    "data": audio_bytes,
                    "format": suffix
                }
            }
        ]
    )

    transcript = response.output_text
    diarisation = response.output_audio_diarization

    print("âœ… GPT-4o transcription completed")

    return transcript, diarisation


# --------------------------
# Lambda handler
# --------------------------
def lambda_handler(event, context):
    print("ðŸ“¥ Event received")
    print(json.dumps(event))

    try:
        # Parse event
        bucket, key = parse_s3_event(event)
        podcast, episode, filename = parse_key_structure(key)

        if not filename.lower().endswith(("mp3", "wav", "m4a", "ogg", "flac")):
            raise ValueError(f"Unsupported audio type: {filename}")

        # Download audio to /tmp
        local_audio = download_audio(bucket, key)

        # Run GPT-4o diarised transcription
        transcript_text, diarisation = run_gpt4o_transcription(local_audio)

        # Output S3 keys
        base_prefix = f"{podcast}/{episode}"
        transcript_key = f"{base_prefix}/transcript.txt"
        diarisation_key = f"{base_prefix}/diarisation.json"

        # Upload outputs
        upload_text(bucket, transcript_key, transcript_text)
        upload_json(bucket, diarisation_key, diarisation)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Transcription + diarisation complete",
                "podcast": podcast,
                "episode": episode,
                "transcript_key": transcript_key,
                "diarisation_key": diarisation_key
            })
        }

    except Exception as e:
        print(f"âŒ ERROR: {e}")
        import traceback
        traceback.print_exc()

        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
