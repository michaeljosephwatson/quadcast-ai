# LLM Summarise Lambda

Lambda function that analyzes episode transcripts using OpenAI to extract topics and speakers.

## Purpose

Reads transcripts and diarized segments from S3, uses OpenAI to identify topics discussed and speakers involved, stores results in database for dashboard visualization and metadata enrichment.

Enables rich podcast content discovery by extracting semantic information from raw transcripts.

## How It Works

1. **Extract**:
   - Receives episode_id and podcast_id in event
   - Reads full transcript from S3
   - Reads diarized segments (speaker markers) if available

2. **Analyze**:
   - Sends transcript to OpenAI API
   - Uses diarized segments for speaker identification
   - Extracts:
     - Main topics/themes discussed
     - Speaker names and participation

3. **Load**:
   - Stores extracted topics in `topics` table
   - Links topics to episode in `episode_topics` junction table
   - Stores speaker information in `speakers` table
   - Links speakers to episode in `episode_speakers` table
   - Saves full analysis JSON to S3

4. **Result**:
   - Dashboard displays what was discussed
   - Enables topic-based search and filtering
   - Shows who participated in each episode

## Setup

### Prerequisites

- RDS PostgreSQL with schema deployed
- OpenAI API account with reasonable rate limits
- S3 bucket with transcript files from transcribe_pipeline
- Transcripts must exist before this function runs

### Environment Variables

```
OPENAI_API_KEY         # OpenAI API key (required)
S3_BUCKET              # S3 bucket containing transcripts (required)
RDS_HOST               # Database host (required)
RDS_DB_NAME            # Database name (required)
RDS_USERNAME           # Database username (required)
RDS_PASSWORD           # Database password (required)
RDS_PORT               # Database port (default: 5432)
USE_SECRETS_MANAGER    # Set to "true" to use AWS Secrets Manager (recommended)
AWS_REGION             # AWS region (default: eu-west-2)
```

### Installation

```bash
pip install -r requirements.txt
```

### Local Testing

```bash
# Create .env file with credentials
export OPENAI_API_KEY=sk-...
export S3_BUCKET=c20-quadcast-s3-bucket
export RDS_HOST=localhost
export RDS_DB_NAME=quadcast
export RDS_USERNAME=postgres
export RDS_PASSWORD=password

# Run tests
python -m pytest test_analyser.py
```

## Dependencies

- openai - OpenAI API client
- boto3 - S3 access and Secrets Manager
- psycopg2-binary - PostgreSQL adapter
- python-dotenv - Environment configuration

## Key Functions

### `s3_client.py`
- `read_transcript()`: Downloads transcript from S3
- `read_segments()`: Downloads diarized segments from S3
- `save_summary_to_s3()`: Uploads analysis results to S3
- `build_transcript_key()`: Constructs S3 path for transcript
- `build_segments_key()`: Constructs S3 path for segments

### `analyser.py`
- `analyze_transcript()`: Main OpenAI analysis function
  - Extracts topics from transcript
  - Identifies speakers from segments
  - Returns structured analysis

### `database.py`
- `episode_exists()`: Checks if episode exists in database
- `store_analysis()`: Saves topics and speakers to database
- `get_rds_connection()`: Establishes database connection

### `lambda_handler.py`
- `lambda_handler(event, context)`: Main entry point
  - Orchestrates extract-analyze-load pipeline
  - Error handling and validation

## Lambda Event & Response

### Event Input
```json
{
  "episode_id": 123,
  "podcast_id": 42
}
```

### Response - Success (200)
```json
{
  "statusCode": 200,
  "body": {
    "status": "success",
    "episode_id": 123,
    "topics_count": 5,
    "speakers_count": 3,
    "summary_s3_key": "podcast42/episode123/analysis.json"
  }
}
```

### Response - Transcript Not Found (404)
```json
{
  "statusCode": 404,
  "body": {
    "status": "error",
    "error": "Transcript not found"
  }
}
```

### Response - Error (500)
```json
{
  "statusCode": 500,
  "body": {
    "status": "error",
    "error": "Internal server error"
  }
}
```

## S3 Path Format

Transcripts are read from:
```
{podcast_name}{podcast_id}/{episode_title}{episode_id}/transcript.txt
```

Segments read from:
```
{podcast_name}{podcast_id}/{episode_title}{episode_id}/diarized_segments.txt
```

Analysis saved to:
```
{podcast_name}{podcast_id}/{episode_title}{episode_id}/analysis.json
```

## Extracted Data

### Topics
Stored in `topics` table:
- Topic name (e.g., "Machine Learning", "Leadership")
- Linked to episode via `episode_topics` junction table

### Speakers
Stored in `speakers` table:
- Speaker name
- Speaker username (if identifiable)
- Linked to episode via `episode_speakers` junction table

## Architecture

Part of the enrichment pipeline:

```
transcribe_pipeline (creates transcripts)
    ↓
llm_summarise (extracts topics/speakers)
    ↓
vector_embedding (creates semantic embeddings)
    ↓
dashboard (displays enriched content)
```

## Cost Considerations

- Each transcript uses OpenAI API tokens (text-davinci-003 or GPT-4)
- Charged per token used
- Large transcripts = higher cost
- Monitor usage via OpenAI dashboard

## Notes

- Requires transcript to exist from transcribe_pipeline first
- Diarized segments optional (won't fail if missing)
- Topics and speakers stored as database references for deduplication
- Results enable rich filtering and search in dashboard