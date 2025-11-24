CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE episode_vector (
    episode_id INTEGER PRIMARY KEY REFERENCES episode(episode_id) ON DELETE CASCADE,
    podcast_id INTEGER NOT NULL REFERENCES podcast(podcast_id) ON DELETE CASCADE,
    transcript_embedding VECTOR(1536) NOT NULL
);

CREATE INDEX ON episode_vector USING ivfflat (transcript_embedding vector_cosine_ops);