# Daily Pipeline Lambda

Scheduled Lambda that discovers and ingests new podcast episodes daily.

## Purpose

Orchestrates the complete ETL pipeline to find new episodes from RSS feeds for all tracked podcasts and add them to the database. Runs daily (typically 2 AM UTC via EventBridge).

Enables the downstream transcription, summarization, and embedding pipelines by ensuring fresh episode data.

## How It Works

1. **Extract**:
   - Queries database for all tracked podcasts
   - Fetches RSS feed for each podcast
   - Parses episode entries

2. **Transform**:
   - Validates episode data (titles, URLs, publish dates)
   - Normalizes dates and URLs
   - Deduplicates against existing episodes

3. **Load**:
   - Inserts new episodes into RDS database
   - Skips duplicates (same audio URL)
   - Returns summary statistics

4. **Output**:
   - Returns episode counts (found/inserted/skipped)
   - Per-podcast statistics
   - Enables downstream processing

## Setup

### Prerequisites

- RDS PostgreSQL with schema deployed
- Network access from Lambda to RDS
- Tracked podcasts already in database

### Environment Variables

```
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
# Create .env file with database credentials
export RDS_HOST=localhost
export RDS_DB_NAME=quadcast
export RDS_USERNAME=postgres
export RDS_PASSWORD=password

python handler.py
```

## Dependencies

- psycopg2-binary - PostgreSQL adapter
- feedparser - RSS feed parsing
- python-dateutil - Date handling
- python-dotenv - Environment variables

## Key Functions

- `extract_all_new_episodes()`: Fetches and parses RSS feeds
- `transform_all_episodes()`: Validates and deduplicates episode data
- `load_all_episodes()`: Inserts episodes with statistics
- `lambda_handler(event, context)`: Main entry point

## Lambda Response

```json
{
  "statusCode": 200,
  "body": {
    "status": "success",
    "summary": {
      "total_podcasts_checked": 15,
      "total_episodes_processed": 87,
      "total_episodes_inserted": 23,
      "total_episodes_skipped": 64
    },
    "details": [
      {
        "podcast_id": 1,
        "podcast_name": "Tech Talk Daily",
        "episodes_found": 5,
        "episodes_inserted": 3,
        "episodes_skipped": 2
      }
    ]
  }
}
```

## Scheduling

Triggered daily via EventBridge:
```
Schedule: cron(0 2 * * ? *)    # 2 AM UTC daily
```

## Architecture

Part of the data ingestion pipeline. Feeds into:
- Transcription pipeline (transcribe_pipeline)
- Episode processing workflows
- Dashboard data display
