CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE episode_embedding (
    embedding_id SERIAL PRIMARY KEY,
    episode_id INTEGER NOT NULL REFERENCES episode(episode_id) ON DELETE CASCADE,
    transcript_embedding VECTOR(1536) NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    UNIQUE(episode_id, chunk_index)
);

CREATE INDEX idx_episode_embedding_episode_id ON episode_embedding(episode_id);
CREATE INDEX idx_episode_embedding_vector ON episode_embedding USING ivfflat (transcript_embedding vector_cosine_ops);