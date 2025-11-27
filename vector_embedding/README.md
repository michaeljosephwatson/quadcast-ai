# Vector Embedding Lambda

Generates vector embeddings from episode transcripts for semantic search.

## Purpose

Converts transcript text into OpenAI embeddings for semantic search capabilities. Enables finding similar episodes without exact keyword matching.

Triggered event-driven when new transcripts become available (after transcription completes).

## How It Works

1. **Extract**:
   - Receives episode_id and podcast_id in event
   - Downloads transcript from S3
   - Validates transcript exists and meets minimum length (400+ chars)

2. **Transform**:
   - Chunks transcript into overlapping segments (default 512 chars, 50 char overlap)
   - Generates OpenAI embeddings (text-embedding-3-small) for each chunk
   - Validates embeddings have correct dimensions (1536)

3. **Load**:
   - Stores embeddings in PostgreSQL episode_embeddings table
   - Links to episode via episode_id
   - Includes chunk index and metadata

4. **Result**:
   - Enables semantic similarity queries across episodes
   - Powers dashboard search functionality

## Setup

### Prerequisites

- RDS PostgreSQL with pgvector extension installed:
  ```sql
  CREATE EXTENSION vector;
  ```
- Vector table schema deployed from db_schema/vector_table.sql
- OpenAI API account with embeddings API access
- S3 bucket with transcript files

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
EMBEDDING_MODEL        # Model for embeddings (default: text-embedding-3-small)
CHUNK_SIZE             # Characters per chunk (default: 512)
CHUNK_OVERLAP          # Overlap between chunks (default: 50)
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
python -m pytest test_*.py
```

## Dependencies

- openai - Embedding API
- boto3 - S3 and Secrets Manager
- psycopg2-binary - PostgreSQL adapter
- tiktoken - Token counting for OpenAI

## Key Functions

- `read_transcript_for_embedding()`: Downloads transcript from S3
- `validate_transcript()`: Ensures minimum length
- `transform_transcript()`: Chunks and generates embeddings
- `validate_embeddings()`: Checks embedding dimensions
- `load_embeddings()`: Stores in database
- `lambda_handler(event, context)`: Main entry point

## Lambda Event & Response

### Event Input
```json
{
  "episode_id": 123,
  "podcast_id": 42
}
```

### Response (Success)
```json
{
  "statusCode": 200,
  "body": {
    "status": "success",
    "episode_id": 123,
    "podcast_id": 42,
    "chunks_stored": 25,
    "transcript_length": 12800
  }
}
```

### Response (Error)
```json
{
  "statusCode": 404,
  "body": {
    "status": "error",
    "error": "Transcript not found"
  }
}
```

## S3 Path Format

Transcripts are located at:
```
{podcast_name}{podcast_id}/{episode_title}{episode_id}/transcript.txt
```

Example:
```
TechTalk42/EpisodeIntro101/transcript.txt
```

## Semantic Search Usage

Once embeddings are stored, query similar episodes:

```sql
-- Find similar episodes
SELECT episode_id, (embedding <-> query_embedding) as distance
FROM episode_embeddings
WHERE episode_id != 123
ORDER BY distance
LIMIT 5;
```

## Architecture

Part of the enrichment pipeline:
- Triggered by: S3 event or Lambda event from transcription service
- Feeds into: Dashboard semantic search
- Upstream: transcribe_pipeline (creates transcripts)
