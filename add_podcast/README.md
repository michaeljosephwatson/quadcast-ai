# Add Podcast Lambda

Lambda function to add new podcasts to the tracking system.

## Purpose

HTTP API endpoint that accepts a podcast RSS feed URL, extracts metadata and episodes, and adds to database. Prevents duplicates by URL and triggers transcription workflows for new podcasts.

Entry point for discovering and adding new podcasts to the platform.

## How It Works

1. **Input**: Receives POST request with RSS feed URL:
   ```json
   {
     "podcast_url": "https://example.com/podcast.rss"
   }
   ```

2. **Extract**:
   - Parses RSS feed using feedparser
   - Extracts podcast metadata (name, URL, description)
   - Gets initial episodes from feed

3. **Validate**:
   - Checks if podcast URL already exists in database
   - Returns 409 Conflict if duplicate

4. **Load**:
   - Inserts podcast into database
   - Inserts initial episodes
   - Marks episodes as not transcribed

5. **Trigger**:
   - If new podcast, invokes Step Functions workflow:
     - `c20-quadcast-episode-transcription-workflow`
   - Starts transcription pipeline for all episodes

6. **Output**:
   - 200 (success): Podcast added, workflow triggered
   - 409 (conflict): Podcast already exists
   - 400 (bad request): Missing/invalid URL
   - 500 (error): Processing failed

## Setup

### Prerequisites

- RDS PostgreSQL with schema deployed
- AWS Step Functions state machine configured
- IAM Lambda execution role with:
  - RDS network access
  - Step Functions invoke permission

### Environment Variables

```
RDS_HOST               # Database host
RDS_DB_NAME            # Database name
RDS_USERNAME           # Database username
RDS_PASSWORD           # Database password
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
# Create test event
cat > test_event.json <<EOF
{
  "body": "{\"podcast_url\": \"https://example.com/podcast.rss\"}"
}
EOF

# Run test
python -c "from handler import lambda_handler; import json; print(json.dumps(lambda_handler(json.load(open('test_event.json')), None), indent=2))"
```

## Dependencies

- psycopg2-binary - PostgreSQL adapter
- feedparser - RSS feed parsing
- boto3 - AWS SDK for Step Functions

## Key Functions

- `get_data_from_rss()`: Parses RSS feed and extracts data
- `load_data_to_db_from_rss()`: Validates and loads podcast data
- `lambda_handler(event, context)`: API entry point, triggers workflow

## API Usage

### Request

```bash
curl -X POST https://<api-gateway-url>/podcasts \
  -H "Content-Type: application/json" \
  -d '{"podcast_url": "https://example.com/podcast.rss"}'
```

### Response - Success (200)

```json
{
  "statusCode": 200,
  "body": {
    "message": "Podcast data added successfully!",
    "is_duplicate": false
  }
}
```

### Response - Duplicate (409)

```json
{
  "statusCode": 409,
  "body": {
    "message": "Podcast already exists",
    "is_duplicate": true
  }
}
```

### Response - Error (400)

```json
{
  "statusCode": 400,
  "body": {
    "error": "Invalid request: podcast_url is required."
  }
}
```

## RSS Feed Requirements

- Must be valid RSS feed (.rss or .xml)
- Must include:
  - Feed title/name
  - Feed URL
  - Entries with episode information
- Optional:
  - Description
  - Author
  - Language

## Pipeline Integration

```
User → Add Podcast API → Database → Step Functions
                                    ↓
                        Transcription Workflow
                                    ↓
                        transcribe_pipeline → llm_summarise → vector_embedding → Dashboard
```

## Notes

- RSS feed validation happens during extraction
- Duplicate detection by podcast_url (UNIQUE constraint)
- Step Functions workflow trigger is non-blocking
- All episodes added as untranscribed initially