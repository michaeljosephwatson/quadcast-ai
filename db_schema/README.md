# Database Schema

PostgreSQL schema definitions for the podcast platform.

## Purpose

Defines the complete data model for storing:
- Podcasts and episodes with transcription status
- Speaker and topic information extracted by LLM
- Vector embeddings for semantic search
- Relationships between podcasts, episodes, speakers, and topics

## Files

- `schema.sql`: Main schema with 8 tables and indexes
- `vector_table.sql`: Schema for storing vector embeddings

## Setup

### Prerequisites

- PostgreSQL 12+
- pgvector extension installed

### Installation

```bash
# Deploy main schema
psql -h <RDS_HOST> -U <RDS_USERNAME> -d <RDS_DB_NAME> -f schema.sql

# Deploy vector embedding schema
psql -h <RDS_HOST> -U <RDS_USERNAME> -d <RDS_DB_NAME> -f vector_table.sql
```

## Core Tables

### `podcast`
Stores podcast metadata
```
- podcast_id (PK)
- podcast_name
- podcast_url (UNIQUE)
- publish_date
- language_id (FK)
- uploaded_at
```

### `episode`
Stores individual episodes with transcription status
```
- episode_id (PK)
- podcast_id (FK) → podcast
- episode_title
- audio_url (UNIQUE)
- transcribed (BOOLEAN) - tracks if transcription is complete
- published_at
- uploaded_at
```

### `speakers`
Speaker/personality information
```
- speaker_id (PK)
- speaker_name (UNIQUE)
- speaker_username
```

### `topics`
Topic/category taxonomy
```
- topic_id (PK)
- topic_name (UNIQUE)
```

### `language`
Supported podcast languages
```
- language_id (PK)
- language_name (UNIQUE)
```

## Junction Tables

### `episode_speakers`
Links episodes to speakers (many-to-many)
```
- episode_speaker_id (PK)
- episode_id (FK) → episode
- speaker_id (FK) → speakers
```

### `episode_topics`
Links episodes to topics (many-to-many)
```
- episode_topic_id (PK)
- episode_id (FK) → episode
- topic_id (FK) → topics
```

## Indexes

Performance indexes on frequently queried fields:
- `idx_episode_podcast`: Fast podcast episode lookups
- `idx_episode_transcribed`: Find untranscribed episodes
- `idx_episode_published`: Sort by publish date
- `idx_episode_speakers_*`: Fast speaker lookups
- `idx_episode_topics_*`: Fast topic lookups
- `idx_podcast_url`: Find podcast by URL

## Key Constraints

- **Cascade Delete**: Episodes deleted when podcast deleted
- **Unique URLs**: Prevents duplicate podcast/episode entries
- **Junction Uniqueness**: Prevents duplicate speaker/topic associations

## Vector Embeddings

The `vector_table.sql` creates:
```
- episode_embeddings table
- Stores embedding vectors (1536 dimensions for OpenAI)
- Linked to episodes for semantic search
```

## Default Data

Initial languages inserted:
- English
- Spanish
- French
- German
- Mandarin

Add more with:
```sql
INSERT INTO language (language_name) VALUES ('Italian');
```

## Data Flow

```
Podcasts Added → Episodes Found → Transcribed → Topics/Speakers Extracted → Embeddings Created
    ↓                ↓               ↓               ↓                      ↓
add_podcast      daily_pipeline  transcribe    llm_summarise          vector_embedding
```
