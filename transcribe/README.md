# Transcribe Lambda

AWS Lambda function for transcribing podcast audio using OpenAI's GPT-4o-transcribe-diarize model.

## Overview

This module provides a serverless transcription pipeline that:
- Queries RDS database for untranscribed episodes
- Downloads audio files from episode URLs
- Processes them with OpenAI's GPT-4o-transcribe-diarize model with automatic chunking and diarization
- Uploads generated transcripts and diarized segments to S3
- Updates the database to mark episodes as transcribed

## Features

- **Audio Transcription**: Converts podcast audio to text using GPT-4o-transcribe-diarize model
- **Speaker Diarization**: Identifies and labels different speakers with timestamps
- **Automatic Chunking**: Splits audio into 2-minute chunks for optimal processing
- **Async Concurrency**: Processes chunks concurrently (default: 5) for faster transcription
- **Retry Logic**: Automatic retry with exponential backoff for failed chunks
- **S3 Output Storage**: Stores transcripts and segments in S3
- **Database Integration**: Reads from RDS PostgreSQL and marks episodes as processed
- **Error Handling**: Comprehensive error handling and logging

## Architecture

### Input Flow
1. Lambda handler queries RDS for the oldest untranscribed episode
2. Episode data includes: `episode_id`, `podcast_id`, `podcast_name`, `episode_title`, `audio_url`

### Output Flow
Results are stored in S3 with partitioned structure: `{podcast_name}{podcast_id}/{episode_title}{episode_id}/`
```
{podcast_name}{podcast_id}/{episode_title}{episode_id}/transcript.txt           # Full transcript text
{podcast_name}{podcast_id}/{episode_title}{episode_id}/diarized_segments.txt    # Segments with speaker labels
```

Example: `MyPodcast42/Episode1Intro101/transcript.txt`

Episode is marked as `transcribed = TRUE` in RDS database.

## Setup

### Environment Variables
```
OPENAI_API_KEY         # Your OpenAI API key (required)
USE_SECRETS_MANAGER    # Set to "true" to use AWS Secrets Manager (optional)
AWS_REGION             # AWS region for S3 and Secrets Manager (default: eu-west-2)
RDS_HOST               # Database host (required if USE_SECRETS_MANAGER != "true")
RDS_DB_NAME            # Database name (required if USE_SECRETS_MANAGER != "true")
RDS_USERNAME           # Database username (required if USE_SECRETS_MANAGER != "true")
RDS_PASSWORD           # Database password (required if USE_SECRETS_MANAGER != "true")
RDS_PORT               # Database port (default: 5432)
```

### AWS Secrets Manager
If `USE_SECRETS_MANAGER=true`, expects secret `c20-quadcast-secrets` containing:
```json
{
  "RDS_HOST": "...",
  "RDS_DB_NAME": "...",
  "RDS_USERNAME": "...",
  "RDS_PASSWORD": "...",
  "RDS_PORT": "..."
}
```

### Installation
```bash
pip install -r requirements.txt
```

## Dependencies

- `openai`: OpenAI Python client for GPT-4o model access
- `boto3`: AWS SDK for S3 operations and Secrets Manager
- `psycopg2-binary`: PostgreSQL database adapter
- `requests`: HTTP library for downloading audio files
- `pydub`: Audio processing library for splitting and format conversion

## Lambda Handler

### Entry Point
```python
lambda_handler(event, context)
```

### Response
Success (HTTP 200):
```json
{
  "statusCode": 200,
  "body": {
    "status": "success",
    "episode_id": 123,
    "transcript_s3_key": "{podcast_name}{podcast_id}/{episode_title}{episode_id}/transcript.txt",
    "segments_s3_key": "{podcast_name}{podcast_id}/{episode_title}{episode_id}/diarized_segments.txt"
  }
}
```

No work (HTTP 200):
```json
{
  "statusCode": 200,
  "body": {
    "status": "no_work"
  }
}
```

Error (HTTP 500):
```json
{
  "statusCode": 500,
  "body": {
    "status": "error",
    "message": "Error description"
  }
}
```

## Key Functions

### `extract_urls.py`
- `get_secret()`: Retrieves database credentials from AWS Secrets Manager
- `get_rds_connection()`: Establishes RDS PostgreSQL connection
- `get_untranscribed_episode()`: Fetches oldest untranscribed episode
- `update_episode_transcribed()`: Marks episode as transcribed in database

### `transcribe.py`
- `split_audio_2min()`: Splits audio into 2-minute FLAC chunks in memory
- `transcribe_chunk_async()`: Async transcription of single chunk
- `robust_transcribe_chunk()`: Retry wrapper with exponential backoff
- `transcribe_full_audio_async()`: Main async pipeline with concurrency control
- `transcribe_audio()`: Wrapper function for sync execution

### `lambda_handler.py`
- `download_audio()`: Downloads audio from URL with streaming
- `upload_to_s3()`: Uploads file to S3 bucket
- `save_transcript_files()`: Saves and uploads both transcript and segments to partitioned S3 structure
- `lambda_handler()`: Main Lambda entry point

## Processing Pipeline

1. Query RDS for untranscribed episode
2. Download audio file from episode URL
3. Split audio into 2-minute chunks
4. Concurrently transcribe all chunks with diarization
5. Merge results and maintain speaker/timestamp alignment
6. Save transcript text and formatted segments
7. Upload both files to S3
8. Mark episode as transcribed in RDS
9. Cleanup temporary files from `/tmp`

## Error Handling

The function handles:
- No untranscribed episodes available
- Database connection failures
- Invalid or unreachable audio URLs
- Audio format/processing errors
- OpenAI API errors with retry logic
- S3 upload failures
- Database update failures

All errors are logged and return appropriate HTTP status codes.