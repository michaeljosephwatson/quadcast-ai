# QuadCast AI

An AI-powered podcast analytics platform that automatically transcribes episodes with speaker identification, extracts insights, and provides a comprehensive dashboard for discovery and analysis. Built on AWS Lambda, PostgreSQL, and OpenAI GPT-4o.

**Live Dashboard**: Streamlit web interface for browsing, searching, and analyzing transcribed podcasts with semantic search capabilities.

## Overview

QuadCast processes podcasts through a fully automated serverless pipeline:

1. **Podcast Discovery** - Add RSS feeds or let the daily pipeline find new episodes
2. **Transcription** - OpenAI GPT-4o transcribes audio with speaker diarization
3. **Analysis** - Extract topics, speakers, and generate semantic embeddings
4. **Exploration** - Search and analyze content through an interactive dashboard

## Team

- **Lorenzo** (@Lorenzo-O114) - Project Manager
- **Mikey** (@michaeljosephwatson) - Architect & DevOps
- **Helena** (@helenacalvert) - QA Tester
- **Zuhayr** (@zu56789) - Business Analyst

*Everyone also served as Engineer & Analyst throughout the project.*

## Features

- **Multiple Podcast Sources** - Add podcasts via RSS feed URL
- **Automatic Episode Discovery** - Daily scheduled checks for new episodes
- **AI Transcription** - OpenAI GPT-4o with speaker diarization
- **Topic & Speaker Extraction** - Automatically identify key topics and speakers
- **Semantic Search** - Find episodes using natural language queries powered by embeddings
- **Keyword Search** - Full-text search across transcripts
- **Analytics Dashboard** - Browse podcasts, view statistics, and explore content
- **Flexible Filtering** - Filter by podcast, speaker, topic, and date range

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          User Interface                          │
│                     Streamlit Dashboard                          │
│              (Browse, Search, Filter, Analyze)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data & Search APIs                        │
│            (RDS Queries, Semantic Search, Analytics)             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       PostgreSQL RDS                             │
│    (Podcasts, Episodes, Speakers, Topics, Embeddings)           │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
  ┌──────────┐         ┌──────────┐         ┌──────────┐
  │   S3     │         │ Athena   │         │OpenAI    │
  │Transcripts        │ SQL      │         │API       │
  └──────────┘         └──────────┘         └──────────┘
        ▲                     ▲                     ▲
        └─────────────────────┼─────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Lambda Functions                          │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │ add_podcast  │  │ daily_pipeline │  │ transcribe_      │   │
│  │ (REST API)   │  │ (EventBridge   │  │ pipeline (Step   │   │
│  │              │  │  trigger)      │  │ Functions)       │   │
│  └──────────────┘  └────────────────┘  └──────────────────┘   │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │llm_summarise │  │vector_embedding│  │count_episodes    │   │
│  │ (Step Func)  │  │ (Step Func)    │  │ (Monitoring)     │   │
│  └──────────────┘  └────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Diagram

![Architecture Diagram](ARCHITECTURE.png)

### Database Design

![Entity Relationship Diagram](ERD.png)

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Compute** | AWS Lambda (Python 3.9+) | Serverless processing functions |
| **Database** | PostgreSQL (RDS) | Structured data with pgvector for embeddings |
| **Storage** | AWS S3 | Transcripts and audio files |
| **AI/ML** | OpenAI GPT-4o | Transcription, diarization, analysis, embeddings |
| **Frontend** | Streamlit | Web dashboard and UI |
| **Query Engine** | AWS Athena | SQL queries on S3 data |
| **Catalog** | AWS Glue | Data catalog for Athena |
| **API** | AWS API Gateway | REST endpoints |
| **Scheduling** | AWS EventBridge | Daily pipeline triggers |
| **Orchestration** | AWS Step Functions | Multi-step Lambda workflows |
| **Infrastructure** | Terraform | Infrastructure as Code |
| **Containers** | Docker & ECR | Lambda deployment containers |

## Quick Start

### Prerequisites

- Python 3.9+
- AWS Account with appropriate credentials configured
- OpenAI API Key
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/quadcast-ai.git
   cd quadcast-ai
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the root directory:
   ```bash
   # Database
   RDS_HOST=your-rds-endpoint.eu-west-2.rds.amazonaws.com
   RDS_PORT=5432
   RDS_DB_NAME=quadcast_db
   RDS_USERNAME=postgres
   RDS_PASSWORD=your-secure-password

   # OpenAI
   OPENAI_API_KEY=sk-your-api-key-here

   # AWS
   AWS_REGION=eu-west-2
   S3_BUCKET=your-quadcast-bucket

   # Configuration
   USE_SECRETS_MANAGER=false
   EMBEDDING_MODEL=text-embedding-3-small
   ```

5. **Run the dashboard locally**
   ```bash
   cd dashboard
   streamlit run 🏠_Overview.py
   ```

   The dashboard will be available at `http://localhost:8501`

### Running Tests

```bash
# Run all tests
pytest

# Run tests for a specific module
pytest add_podcast/
pytest dashboard/

# Run with coverage
pytest --cov=.
```

### Deploying to AWS

#### Deploy Infrastructure with Terraform

```bash
cd terraform

# Initialize Terraform (first time only)
terraform init

# Review planned changes
terraform plan

# Apply infrastructure
terraform apply
```

#### Deploy Lambda Functions

```bash
# Deploy all Lambdas at once
./deploy_all_lambdas.sh

# Or deploy individual Lambdas
cd add_podcast && ./bash_scripts/deploy_lambda.sh
cd ../daily_pipeline && ./bash_scripts/deploy_lambda.sh
# ... and so on for other modules
```

#### Deploy Dashboard to AWS ECS

```bash
# Dashboard is deployed via Terraform
# It creates an ECS task running the Streamlit app
cd terraform
terraform apply -target=aws_ecs_task_definition.dashboard_task
```

## Project Structure

```
quadcast-ai/
├── README.md                          # This file
├── ARCHITECTURE.png                   # System architecture diagram
├── ERD.png                           # Database entity-relationship diagram
├── requirements.txt                  # Root-level Python dependencies
├── deploy_all_lambdas.sh             # Deployment automation script
│
├── add_podcast/                      # Lambda: Add podcasts via REST API
│   ├── README.md                     # Module documentation
│   ├── handler.py                    # Lambda entry point
│   ├── extract.py                    # Extract podcast metadata
│   ├── load.py                       # Load data to RDS
│   ├── transform.py                  # Validate & transform data
│   ├── requirements.txt              # Module dependencies
│   └── bash_scripts/                 # Deployment scripts
│   └── Dockerfile
│
├── daily_pipeline/                   # Lambda: Check for new episodes daily
│   ├── README.md                     # Module documentation
│   ├── handler.py                    # Lambda entry point
│   ├── extract_episodes.py           # Fetch episodes from RSS feeds
│   ├── load_episodes.py              # Insert to RDS
│   ├── transform_episodes.py         # Validate & normalize
│   ├── requirements.txt              # Module dependencies
│   └── bash_scripts/                 # Deployment scripts
│   └── Dockerfile
│
├── transcribe_pipeline/              # Lambda: Transcribe episodes with diarization
│   ├── README.md                     # Module documentation
│   ├── lambda_handler.py             # Lambda entry point
│   ├── extract_urls.py               # Get episode audio URLs
│   ├── transcribe.py                 # OpenAI transcription
│   ├── requirements.txt              # Module dependencies
│   └── bash_scripts/                 # Deployment scripts
│   └── Dockerfile
│
├── llm_summarise/                    # Lambda: Extract topics and speakers
│   ├── README.md                     # Module documentation
│   ├── lambda_handler.py             # Lambda entry point
│   ├── analyser.py                   # OpenAI analysis logic
│   ├── s3_client.py                  # S3 transcript access
│   ├── database.py                   # Database operations
│   ├── requirements.txt              # Module dependencies
│   └── bash_scripts/                 # Deployment scripts
│   └── Dockerfile
│
├── vector_embedding/                 # Lambda: Generate semantic embeddings
│   ├── README.md                     # Module documentation
│   ├── lambda_handler.py             # Lambda entry point
│   ├── extract.py                    # Extract transcripts
│   ├── transform.py                  # Create embeddings
│   ├── load.py                       # Store in RDS
│   ├── requirements.txt              # Module dependencies
│   └── bash_scripts/                 # Deployment scripts
│   └── Dockerfile
│
├── count_episodes/                   # Lambda: Monitor transcription backlog
│   ├── README.md                     # Module documentation
│   ├── lambda_handler.py             # Lambda entry point
│   ├── requirements.txt              # Module dependencies
│   └── bash_scripts/                 # Deployment scripts
│   └── Dockerfile
│
├── dashboard/                        # Streamlit web application
│   ├── README.md                     # Module documentation
│   ├── 🏠_Overview.py                # Home page & statistics
│   ├── pages/
│   │   ├── 1_📻_Podcasts.py          # Browse podcasts & episodes
│   │   ├── 2_📊_Analytics.py         # Analytics and statistics
│   │   └── 3_🔍_Search.py            # Keyword and semantic search
│   ├── search_queries.py             # OpenAI semantic search
│   ├── rds_queries.py                # Database queries
│   ├── athena_queries.py             # AWS Athena queries
│   ├── chatbot.py                    # AI chatbot functionality
│   ├── visualisations.py             # Chart formatting
│   ├── requirements.txt              # Module dependencies
│   └── .env                          # Environment configuration
│
├── db_schema/                        # Database schema
│   ├── README.md                     # Schema documentation
│   ├── schema.sql                    # Main PostgreSQL schema (8 tables)
│   └── vector_table.sql              # Vector embeddings schema
│
├── terraform/                        # Infrastructure as Code
│   ├── README.md                     # Terraform documentation
│   ├── add_podcast_lambda.tf         # Lambda configurations
│   ├── daily_pipeline_lambda.tf
│   ├── transcribe_pipeline_lambda.tf
│   ├── llm_summarise_lambda.tf
│   ├── vector_embedding_lambda.tf
│   ├── count_episodes_lambda.tf
│   ├── *_ecr.tf                      # ECR registry configurations
│   ├── daily_eventbridge.tf          # EventBridge scheduling
│   ├── dashboard-ecs.tf              # ECS task for Streamlit
│   ├── api_gateway.tf                # REST API endpoints
│   ├── rds.tf                        # PostgreSQL database
│   ├── s3.tf                         # S3 buckets
│   ├── athena.tf                     # Athena SQL engine
│   ├── glue.tf                       # Glue catalog
│   ├── backend.tf                    # Terraform state management
│   ├── outputs.tf                    # Output values
│   └── variables.tf                  # Input variables
│
├── .github/
│   └── ISSUE_TEMPLATE/ticket.md      # GitHub issue template
│
├── .gitignore                        # Git ignore rules
└── .env.example                      # Example environment file
```

## Database Schema

QuadCast uses a PostgreSQL database with 8 core tables:

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| **podcast** | Podcast metadata | name, rss_url, language, created_at |
| **episode** | Individual episodes | podcast_id, title, url, transcribed, published_at |
| **speakers** | Speaker/host information | name, podcast_id, bio |
| **topics** | Topics/categories | name, description |
| **language** | Supported languages | code, name |
| **episode_speakers** | Episode-speaker mapping | episode_id, speaker_id |
| **episode_topics** | Episode-topic mapping | episode_id, topic_id |
| **episode_embeddings** | Vector embeddings for semantic search | episode_id, embedding (pgvector) |

For detailed schema information, see [db_schema/README.md](db_schema/README.md)

## Data Processing Pipeline

### Ingestion Flow

```
1. Add Podcast (REST API)
   ↓
   └─► Validate RSS feed → Extract metadata → Load to RDS

2. Daily Episode Discovery (Scheduled)
   ↓
   └─► Check all RSS feeds → Extract new episodes → Validate → Load to RDS

3. Transcription Pipeline (Step Functions)
   ↓
   ├─► Extract episode audio URLs
   ├─► Download and transcribe with OpenAI GPT-4o
   ├─► Add speaker diarization
   ├─► Store transcript in S3
   └─► Update episode status in RDS

4. Analysis Pipeline (Step Functions)
   ├─► Extract topics and speakers (LLM analysis)
   ├─► Store analysis results in RDS
   └─► Generate semantic embeddings

5. Semantic Indexing (Vector Embedding)
   ├─► Extract transcripts from S3
   ├─► Generate embeddings via OpenAI
   ├─► Store vectors in RDS (pgvector)
   └─► Enable semantic search
```

### Scheduled Triggers

- **Daily Pipeline**: Runs at 2 AM UTC via EventBridge
- **Transcription**: Triggered when new episodes are detected
- **Analysis**: Triggered after successful transcription
- **Vector Embedding**: Triggered after analysis completion

## Module Documentation

Each module has detailed documentation:

- [**add_podcast**](add_podcast/README.md) - REST API for adding podcast feeds
- [**daily_pipeline**](daily_pipeline/README.md) - Automated episode discovery
- [**transcribe_pipeline**](transcribe_pipeline/README.md) - OpenAI transcription with diarization
- [**llm_summarise**](llm_summarise/README.md) - Topic and speaker extraction
- [**vector_embedding**](vector_embedding/README.md) - Semantic embedding generation
- [**count_episodes**](count_episodes/README.md) - Backlog monitoring
- [**dashboard**](dashboard/README.md) - Streamlit web interface
- [**db_schema**](db_schema/README.md) - Database schema reference
- [**terraform**](terraform/README.md) - Infrastructure configuration

## API Endpoints

### Add Podcast Endpoint

```
POST /api/podcasts
Content-Type: application/json

{
  "name": "The Example Podcast",
  "rss_url": "https://example.com/feed.xml",
  "language": "en"
}

Response:
{
  "podcast_id": 123,
  "status": "success",
  "message": "Podcast added successfully"
}
```

For more API details, see [add_podcast/README.md](add_podcast/README.md)

## Configuration

### Environment Variables

**Required Variables:**
- `OPENAI_API_KEY` - OpenAI API key for GPT-4o access
- `RDS_HOST` - PostgreSQL RDS endpoint
- `RDS_DB_NAME` - Database name
- `RDS_USERNAME` - Database username
- `RDS_PASSWORD` - Database password

**Optional Variables:**
- `RDS_PORT` - PostgreSQL port (default: 5432)
- `AWS_REGION` - AWS region (default: eu-west-2)
- `S3_BUCKET` - S3 bucket for transcripts
- `USE_SECRETS_MANAGER` - Use AWS Secrets Manager (default: false)
- `EMBEDDING_MODEL` - OpenAI embedding model (default: text-embedding-3-small)

See individual module READMEs for additional module-specific variables.

## Contributing

1. Create a feature branch from `main`
2. Make your changes and commit with clear messages
3. Add or update tests as needed
4. Run `pytest` to ensure all tests pass
5. Push your branch and create a Pull Request
6. Ensure code review and CI/CD checks pass

## Code Quality

- **Testing**: All modules have unit tests with pytest
- **Linting**: Python code follows PEP 8 standards
- **Type Hints**: Type annotations recommended for new code
- **Documentation**: Update README files for significant changes

## Deployment Checklist

- [ ] All tests pass locally (`pytest`)
- [ ] Environment variables configured
- [ ] AWS credentials available
- [ ] Terraform state initialized
- [ ] Infrastructure deployed (`terraform apply`)
- [ ] Lambda functions deployed (`./deploy_all_lambdas.sh`)
- [ ] Database schema applied
- [ ] Dashboard accessible at deployed URL
- [ ] Daily pipeline executing on schedule
- [ ] Transcription queue processing

## Troubleshooting

### Dashboard not connecting to database
- Verify RDS security group allows Lambda/ECS connections
- Check `RDS_HOST`, `RDS_USERNAME`, `RDS_PASSWORD` in `.env`
- Test connection: `psql -h $RDS_HOST -U $RDS_USERNAME -d $RDS_DB_NAME`

### Transcription jobs failing
- Check OpenAI API key validity and quota
- Verify S3 bucket exists and Lambda has IAM permissions
- Check CloudWatch logs: `aws logs tail /aws/lambda/transcribe_pipeline`

### Daily pipeline not triggering
- Verify EventBridge rule is enabled
- Check Lambda execution role has correct permissions
- Review CloudWatch Events history

For more detailed troubleshooting, see individual module READMEs.

## Performance Considerations

- **Database**: Indexes on `podcast_id`, `transcribed`, `published_at`
- **Embeddings**: Vector queries use pgvector with appropriate indexing
- **Lambdas**: Configured with appropriate memory and timeout values
- **S3**: Transcripts organized by podcast/episode hierarchy
- **Caching**: Dashboard caches query results for performance

## Security

- Credentials stored in AWS Secrets Manager (production)
- IAM roles follow least-privilege principle
- RDS PostgreSQL with encryption at rest
- S3 buckets with appropriate ACLs and policies
- API Gateway authentication (API key recommended)

## License

[Add license information here]

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review individual module READMEs
- Contact the team on Slack

## Acknowledgments

Built with:
- OpenAI GPT-4o for transcription and analysis
- AWS services for scalable infrastructure
- Streamlit for rapid dashboard development
- PostgreSQL with pgvector for semantic search

