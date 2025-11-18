-- schema.sql for Podcast Analysis Pipeline

-- Drop tables if they exist (in correct order due to foreign keys)
DROP TABLE IF EXISTS episode_topics CASCADE;
DROP TABLE IF EXISTS episode_speakers CASCADE;
DROP TABLE IF EXISTS Episode CASCADE;
DROP TABLE IF EXISTS Podcast CASCADE;
DROP TABLE IF EXISTS Topics CASCADE;
DROP TABLE IF EXISTS Speakers CASCADE;
DROP TABLE IF EXISTS language CASCADE;

-- Language table
CREATE TABLE language (
    language_id SERIAL PRIMARY KEY,
    language_name VARCHAR(100) NOT NULL UNIQUE
);

-- Speakers table
CREATE TABLE speakers (
    speaker_id SERIAL PRIMARY KEY,
    speaker_name VARCHAR(255) NOT NULL UNIQUE,
    speaker_username VARCHAR(255)
);

-- Topics table
CREATE TABLE topics (
    topic_id SERIAL PRIMARY KEY,
    topic_name VARCHAR(255) NOT NULL UNIQUE
);

-- Podcast table
CREATE TABLE podcast (
    podcast_id SERIAL PRIMARY KEY,
    podcast_name VARCHAR(255) NOT NULL,
    publish_date TIMESTAMP,
    language_id INTEGER REFERENCES language(language_id) ON DELETE SET NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    podcast_url VARCHAR(500) NOT NULL UNIQUE
);

-- Episode table
CREATE TABLE episode (
    episode_id SERIAL PRIMARY KEY,
    podcast_id INTEGER NOT NULL REFERENCES Podcast(podcast_id) ON DELETE CASCADE,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    audio_url VARCHAR(500) NOT NULL UNIQUE,
    transcribed BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP,
    episode_title VARCHAR(500)
);

-- episode_speakers junction table
CREATE TABLE episode_speakers (
    episode_speaker_id SERIAL PRIMARY KEY,
    speaker_id INTEGER NOT NULL REFERENCES Speakers(speaker_id) ON DELETE CASCADE,
    episode_id INTEGER NOT NULL REFERENCES Episode(episode_id) ON DELETE CASCADE,
    UNIQUE(speaker_id, episode_id)
);

-- episode_topics junction table
CREATE TABLE episode_topics (
    episode_topic_id SERIAL PRIMARY KEY,
    episode_id INTEGER NOT NULL REFERENCES Episode(episode_id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES Topics(topic_id) ON DELETE CASCADE,
    UNIQUE(episode_id, topic_id)
);

-- Create indexes for better query performance
CREATE INDEX idx_episode_podcast ON Episode(podcast_id);
CREATE INDEX idx_episode_transcribed ON Episode(transcribed);
CREATE INDEX idx_episode_published ON Episode(published_at);
CREATE INDEX idx_episode_speakers_episode ON episode_speakers(episode_id);
CREATE INDEX idx_episode_speakers_speaker ON episode_speakers(speaker_id);
CREATE INDEX idx_episode_topics_episode ON episode_topics(episode_id);
CREATE INDEX idx_episode_topics_topic ON episode_topics(topic_id);
CREATE INDEX idx_podcast_url ON Podcast(podcast_url);
CREATE INDEX idx_podcast_language_id ON Podcast(language_id);

-- Insert some default languages
INSERT INTO language (language_name) VALUES 
    ('English'),
    ('Spanish'),
    ('French'),
    ('German'),
    ('Mandarin');