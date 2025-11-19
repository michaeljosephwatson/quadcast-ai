# Transcribe Lambda

AWS Lambda function for transcribing podcast audio using OpenAI's GPT-4o-transcribe-diarise model.

## Overview

This module provides a serverless transcription pipeline that:
- Listens for S3 PUT events when podcast audio is uploaded
- Downloads audio files from S3
- Processes them with OpenAI's GPT-4o-transcribe-diarise model
- Uploads generated transcripts and diarization data back to S3

## Features

- **Audio Transcription**: Converts podcast audio to text using GPT-4o-transcribe-diarise
- **Speaker Diarization**: Identifies and labels different speakers in the audio
- **Multiple Format Support**: Handles MP3, WAV, M4A, OGG, and FLAC audio files
- **S3 Integration**: Automatic triggering and output storage via S3 events
- **Error Handling**: Comprehensive error handling and logging

## S3 Event Structure

### Input
Trigger on S3 PUT events with this key pattern:
```
{podcast}/{episode}/audio.mp3
```

### Outputs
```
{podcast}/{episode}/transcript.txt
{podcast}/{episode}/diarisation.json
```

## Setup

### Environment Variables
```
OPENAI_API_KEY    # Your OpenAI API key
DB_HOST            # (Optional) Database host for metadata
DB_NAME            # (Optional) Database name
DB_USER            # (Optional) Database user
DB_PASSWORD        # (Optional) Database password
DB_PORT            # (Optional) Database port (default: 5432)
AWS_REGION         # AWS region for S3
```

### Installation
```bash
pip install -r requirements.txt
```

## Dependencies

- `openai`: OpenAI Python client for GPT-4o model access
- `boto3`: AWS SDK for S3 operations
- `psycopg2-binary`: PostgreSQL database adapter (optional, for metadata storage)
- `requests`: HTTP library for API calls

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
    "message": "Transcription + diarisation complete",
    "podcast": "podcast_name",
    "episode": "episode_id",
    "transcript_key": "podcast_name/episode_id/transcript.txt",
    "diarisation_key": "podcast_name/episode_id/diarisation.json"
  }
}
```

Error (HTTP 500):
```json
{
  "statusCode": 500,
  "body": {
    "error": "Error message"
  }
}
```

## Testing

Run local tests with:
```bash
python test_transcribe.py
```

A test audio file (`test.mp3`) is included for local development and testing.

## Architecture

### Key Functions

- `parse_s3_event()`: Extracts bucket and key from S3 event
- `parse_key_structure()`: Validates and parses S3 key structure
- `download_audio()`: Downloads audio from S3 to Lambda's `/tmp` directory
- `run_gpt4o_transcription()`: Processes audio with GPT-4o model
- `upload_text()`: Uploads transcript to S3
- `upload_json()`: Uploads diarization data to S3

### Workflow
1. Receive S3 PUT event
2. Parse bucket and key from event
3. Validate key structure and audio format
4. Download audio to `/tmp`
5. Call OpenAI GPT-4o-transcribe-diarise API
6. Extract transcript text and speaker diarization
7. Upload both outputs to S3
8. Return success response

## Error Handling

The function handles:
- Invalid S3 key structures
- Unsupported audio formats
- S3 access errors
- OpenAI API errors
- File I/O errors

All errors are logged and returned with appropriate HTTP status codes and error messages.