# Dashboard

Streamlit web application for browsing, searching, and analyzing podcast content.

## Purpose

Interactive dashboard for discovering podcast episodes through traditional and semantic search. Displays podcast metadata, transcripts, topics, speakers, and enables AI-powered semantic search using vector embeddings.

The frontend for exploring the entire podcast platform - where users find and explore content.

## How It Works

- **Browse**: View all podcasts and episodes with metadata, publish dates, and duration
- **Full-Text Search**: Search transcripts and titles by keywords
- **Semantic Search**: Uses vector embeddings to find conceptually similar episodes (no keyword match needed)
- **Topic Filtering**: Filter episodes by extracted topics/themes
- **Speaker View**: See which speakers participated in each episode
- **Transcript Display**: Read full transcripts with formatting

## Setup

### Prerequisites

- Python 3.8+
- RDS PostgreSQL with schema and vector embeddings
- OpenAI API key (for semantic search queries)
- S3 bucket with transcript files (optional, for direct access)

### Environment Variables

```
OPENAI_API_KEY         # OpenAI API key (required for semantic search)
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

### Running Locally

```bash
# Create .env file with credentials
export OPENAI_API_KEY=sk-...
export RDS_HOST=localhost
export RDS_DB_NAME=quadcast
export RDS_USERNAME=postgres
export RDS_PASSWORD=password

# Run dashboard
streamlit run app.py
```

Dashboard will be available at `http://localhost:8501`

## Dependencies

- streamlit - Web framework
- psycopg2-binary - PostgreSQL adapter
- pandas - Data handling
- openai - Semantic search queries
- boto3 - AWS integration
- altair - Visualization library
- tiktoken - Token counting

## Key Files

### `search_queries.py`
- `get_openai_client()`: Creates OpenAI client
- `search_episodes_by_embedding()`: Semantic search via embeddings
- `search_episodes_by_keyword()`: Full-text search
- `get_tokenizer()`: Token counting for embeddings

### `rds_embedding_queries.py`
- `query_similar_episodes()`: Find semantically similar episodes
- `get_episode_transcripts()`: Retrieve transcripts from database
- `get_podcast_topics()`: Get topics for filtering
- `get_podcast_speakers()`: Get speakers for filtering

### `visualisations.py`
- `format_episode_display()`: Format episode cards
- `create_topic_chart()`: Visualize topic distribution
- `create_speaker_chart()`: Show speaker participation
- `format_transcript_display()`: Style transcript text

## Features

### Browse Mode
- List all podcasts with metadata
- Click to see all episodes
- View episode details (title, date, duration)
- Read full transcript

### Search Modes

#### Keyword Search
- Search for specific words in transcripts
- Searches titles and descriptions
- Fast, exact matching

#### Semantic Search
- Find episodes by topic/concept
- Example: "Machine learning applications" → finds relevant episodes regardless of exact keywords
- Powered by OpenAI embeddings + pgvector
- More accurate for discovering related content

### Filtering
- Filter by topic (e.g., "AI", "Leadership")
- Filter by speaker
- Filter by podcast
- Combine multiple filters

## Database Queries

### Semantic Search Query
```sql
-- Find similar episodes using vector distance
SELECT episode_id, (embedding <-> query_embedding) as distance
FROM episode_embeddings
WHERE episode_id != current_episode
ORDER BY distance
LIMIT 10
```

### Keyword Search Query
```sql
-- Full-text search on transcripts
SELECT episode_id, episode_title
FROM episode
WHERE transcript ILIKE '%keyword%'
```

### Topic Filtering
```sql
-- Get episodes by topic
SELECT DISTINCT episode.episode_id
FROM episode
JOIN episode_topics ON episode.episode_id = episode_topics.episode_id
JOIN topics ON episode_topics.topic_id = topics.topic_id
WHERE topics.topic_name = 'AI'
```

## User Flows

### Flow 1: Browse and Discover
```
Home → Select Podcast → Browse Episodes → Read Transcript → View Topics/Speakers
```

### Flow 2: Keyword Search
```
Search Box → Enter Keywords → View Results → Click Episode → Read Details
```

### Flow 3: Semantic Discovery
```
Semantic Search → Describe Topic → Results Ranked by Relevance → Click to Explore
```

## Performance Considerations

- **Caching**: Streamlit caches database queries automatically
- **Pagination**: Large result sets paginated to prevent slow rendering
- **Embedding Queries**: Vector searches are fast with proper indexing
- **Connection Pooling**: Reuses database connections

## Deployment

### Local Development
```bash
streamlit run app.py
```

### Docker
```bash
docker build -t dashboard .
docker run -p 8501:8501 dashboard
```

### AWS
- Deploy to CloudFront + S3 or Amplify
- Use Streamlit Cloud for managed hosting
- Or deploy to ECS/Fargate with ALB

## Cost Considerations

- OpenAI API calls for semantic search (per query)
- RDS database queries for every search
- S3 access for transcript files (minimal)
- Streamlit Cloud hosting (if used)

## Notes

- Semantic search requires vector embeddings to exist in database
- Each semantic search costs OpenAI tokens
- Dashboard shows data from the last 24 hours by default (configurable)
- Speaker and topic data extracted by llm_summarise pipeline
- Semantic embeddings generated by vector_embedding pipeline