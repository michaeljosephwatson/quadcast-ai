# Count Episodes Lambda

Lightweight Lambda that counts untranscribed episodes in the database.

## Purpose

Simple query utility to check how many episodes are waiting for transcription. Returns a count for monitoring and orchestration decisions. Typically called before triggering transcription workflows.

## How It Works

1. Connects to RDS PostgreSQL database
2. Executes: `SELECT COUNT(*) FROM episode WHERE transcribed = FALSE`
3. Returns the count in Lambda response
4. Used for monitoring backlog and determining if work needs processing

## Setup

### Prerequisites

- RDS PostgreSQL database with schema deployed
- AWS Lambda execution role with RDS network access

### Environment Variables

```
USE_SECRETS_MANAGER    # Set to "true" to use AWS Secrets Manager (recommended)
AWS_REGION             # AWS region (default: eu-west-2)
RDS_HOST               # Database host
RDS_DB_NAME            # Database name
RDS_USERNAME           # Database username
RDS_PASSWORD           # Database password
RDS_PORT               # Database port (default: 5432)
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
export RDS_PORT=5432

python -m pytest test_count_episodes_handler.py
```

## Dependencies

- boto3 - AWS SDK
- psycopg2-binary - PostgreSQL adapter

## Key Functions

- `get_secret()`: Retrieves credentials from AWS Secrets Manager
- `get_rds_connection()`: Establishes database connection
- `count_untranscribed_episodes()`: Counts untranscribed episodes
- `lambda_handler(event, context)`: Main entry point

## Lambda Response

```json
{
  "statusCode": 200,
  "body": {
    "count": 42
  }
}
```

## Architecture

Part of the orchestration layer. Typically invoked by:
- EventBridge schedules
- Step Functions state machines
- Manual monitoring dashboards
