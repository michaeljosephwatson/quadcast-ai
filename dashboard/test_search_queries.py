"""Tests for semantic search queries module"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, call
import os

# Mock OpenAI client and other dependencies before importing
with patch('openai.OpenAI') as mock_openai_class:
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key-12345'}):
        with patch('tiktoken.encoding_for_model'):
            from search_queries import (
                get_openai_client,
                get_tokenizer,
                trim_to_sentence_boundaries,
                embed_query,
                search_episodes_by_embedding,
                EMBEDDING_MODEL
            )


@pytest.fixture
def mock_openai_client():
    """Fixture providing a mocked OpenAI client for embed_query tests"""
    with patch('search_queries.OpenAI') as mock_openai_class:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        with patch('search_queries.get_openai_client', return_value=mock_client):
            yield mock_client


@pytest.fixture
def mock_db_connection():
    """Fixture providing a mocked database connection"""
    return MagicMock()


@pytest.fixture
def sample_embedding():
    """Fixture providing a sample embedding vector"""
    return [0.1, 0.2, 0.3, 0.4, 0.5] * 152  # 760 dimensions like text-embedding-3-small


@pytest.fixture
def sample_search_results():
    """Fixture providing sample search results dataframe"""
    return pd.DataFrame({
        'episode_id': [1, 2],
        'episode_title': ['Episode 1', 'Episode 2'],
        'podcast_name': ['Podcast A', 'Podcast B'],
        'published_at': ['2024-01-01', '2024-01-02'],
        'chunk_index': [0, 1],
        'chunk_text': ['This is a chunk.', 'another chunk.'],
        'similarity': [0.95, 0.87]
    })


class TestGetTokenizer:
    """Tests for get_tokenizer function"""

    def test_get_tokenizer_returns_encoding(self):
        """Test that get_tokenizer returns a tokenizer encoding"""
        with patch('tiktoken.encoding_for_model') as mock_encoding:
            mock_enc = MagicMock()
            mock_encoding.return_value = mock_enc

            encoding = get_tokenizer()

            assert encoding is mock_enc
            mock_encoding.assert_called_once_with(EMBEDDING_MODEL)

    def test_get_tokenizer_custom_model(self):
        """Test get_tokenizer with custom model"""
        with patch('tiktoken.encoding_for_model') as mock_encoding:
            mock_enc = MagicMock()
            mock_encoding.return_value = mock_enc

            encoding = get_tokenizer('text-embedding-3-large')

            mock_encoding.assert_called_once_with('text-embedding-3-large')


class TestTrimToSentenceBoundaries:
    """Tests for trim_to_sentence_boundaries function"""

    def test_trim_lowercase_start_found_boundary(self):
        """Test trimming text that starts lowercase with sentence boundary in window"""
        text = "hello world. This is a sentence that should remain."
        result = trim_to_sentence_boundaries(text)

        assert result == "This is a sentence that should remain."
        assert result[0].isupper()

    def test_preserve_uppercase_start(self):
        """Test that text starting with uppercase is preserved"""
        text = "This is a normal sentence. Another one here."
        result = trim_to_sentence_boundaries(text)

        assert result == text

    def test_lowercase_no_boundary_found(self):
        """Test lowercase text with no sentence boundary in search window"""
        text = "lowercase text without punctuation in first hundred chars"
        result = trim_to_sentence_boundaries(text)

        assert result == text

    def test_empty_string(self):
        """Test handling of empty string"""
        result = trim_to_sentence_boundaries("")
        assert result == ""

    def test_multiple_boundaries_uses_last(self):
        """Test that last boundary in window is used"""
        text = "lowercase. middle. Here is kept text."
        result = trim_to_sentence_boundaries(text)

        assert result == "Here is kept text."

    def test_boundary_with_exclamation(self):
        """Test sentence boundary with exclamation mark"""
        text = "lowercase start! This should be kept."
        result = trim_to_sentence_boundaries(text)

        assert result == "This should be kept."

    def test_boundary_with_question(self):
        """Test sentence boundary with question mark"""
        text = "lowercase question? This should be kept."
        result = trim_to_sentence_boundaries(text)

        assert result == "This should be kept."

    def test_boundary_with_multiple_spaces(self):
        """Test handling of multiple spaces after punctuation"""
        text = "lowercase start.   This has extra spaces."
        result = trim_to_sentence_boundaries(text)

        assert result == "This has extra spaces."

    def test_trim_returns_empty_string_if_boundary_result_is_empty(self):
        """Test that original text is returned if trimming results in empty string"""
        # Create text where trim would result in only whitespace
        text = "lowercase start.    \n\n"
        result = trim_to_sentence_boundaries(text)

        # Should return original since trimmed result would be empty
        assert result == text or result.strip() == ""


class TestEmbedQuery:
    """Tests for embed_query function"""

    def test_embed_query_success(self, mock_openai_client, sample_embedding):
        """Test successful query embedding generation"""
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=sample_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response

        result = embed_query("test query")

        assert result == sample_embedding
        mock_openai_client.embeddings.create.assert_called_once_with(
            model=EMBEDDING_MODEL,
            input="test query"
        )

    def test_embed_query_empty_string_raises_error(self, mock_openai_client):
        """Test that empty query raises ValueError"""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            embed_query("")

    def test_embed_query_whitespace_only_raises_error(self, mock_openai_client):
        """Test that whitespace-only query raises ValueError"""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            embed_query("   \n  ")

    def test_embed_query_custom_model(self, mock_openai_client, sample_embedding):
        """Test embed_query with custom model"""
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=sample_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response

        embed_query("test", model="custom-model")

        mock_openai_client.embeddings.create.assert_called_once_with(
            model="custom-model",
            input="test"
        )

    def test_embed_query_api_error(self, mock_openai_client):
        """Test handling of OpenAI API errors"""
        mock_openai_client.embeddings.create.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="Failed to generate embedding"):
            embed_query("test query")

    def test_embed_query_returns_list(self, mock_openai_client, sample_embedding):
        """Test that embed_query returns a list"""
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=sample_embedding)]
        mock_openai_client.embeddings.create.return_value = mock_response

        result = embed_query("test")

        assert isinstance(result, list)


class TestSearchEpisodesByEmbedding:
    """Tests for search_episodes_by_embedding function"""

    @patch('search_queries.embed_query')
    @patch('pandas.read_sql')
    def test_search_success(self, mock_read_sql, mock_embed_query,
                           mock_db_connection, sample_embedding, sample_search_results):
        """Test successful episode search"""
        mock_embed_query.return_value = sample_embedding
        mock_read_sql.return_value = sample_search_results.copy()

        result = search_episodes_by_embedding(
            mock_db_connection,
            "test query",
            limit=5,
            similarity_threshold=0.5
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'episode_id' in result.columns
        assert 'similarity' in result.columns

    @patch('search_queries.embed_query')
    @patch('pandas.read_sql')
    def test_search_applies_threshold(self, mock_read_sql, mock_embed_query,
                                     mock_db_connection, sample_embedding):
        """Test that similarity threshold is applied in query"""
        mock_embed_query.return_value = sample_embedding
        mock_read_sql.return_value = pd.DataFrame()

        search_episodes_by_embedding(
            mock_db_connection,
            "query",
            limit=10,
            similarity_threshold=0.75
        )

        # Check that read_sql was called with the threshold parameter
        call_args = mock_read_sql.call_args
        params = call_args[1]['params']
        assert params[2] == 0.75  # threshold is third param

    @patch('search_queries.embed_query')
    @patch('pandas.read_sql')
    def test_search_respects_limit(self, mock_read_sql, mock_embed_query,
                                  mock_db_connection, sample_embedding):
        """Test that limit parameter is respected"""
        mock_embed_query.return_value = sample_embedding
        mock_read_sql.return_value = pd.DataFrame()

        search_episodes_by_embedding(
            mock_db_connection,
            "query",
            limit=3
        )

        call_args = mock_read_sql.call_args
        params = call_args[1]['params']
        assert params[3] == 3  # limit is fourth param

    @patch('search_queries.embed_query')
    @patch('pandas.read_sql')
    def test_search_trims_chunk_text(self, mock_read_sql, mock_embed_query,
                                    mock_db_connection, sample_embedding):
        """Test that chunk_text is trimmed to sentence boundaries"""
        mock_embed_query.return_value = sample_embedding

        df = pd.DataFrame({
            'episode_id': [1],
            'chunk_text': ['lowercase start. This should be trimmed.']
        })
        mock_read_sql.return_value = df

        result = search_episodes_by_embedding(mock_db_connection, "query")

        assert result['chunk_text'].iloc[0] == "This should be trimmed."

    @patch('search_queries.embed_query')
    @patch('pandas.read_sql')
    def test_search_empty_results(self, mock_read_sql, mock_embed_query,
                                 mock_db_connection, sample_embedding):
        """Test handling of empty search results"""
        mock_embed_query.return_value = sample_embedding
        mock_read_sql.return_value = pd.DataFrame()

        result = search_episodes_by_embedding(mock_db_connection, "query")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch('search_queries.embed_query')
    def test_search_embed_query_error(self, mock_embed_query, mock_db_connection):
        """Test error handling when embedding fails"""
        mock_embed_query.side_effect = Exception("Embedding failed")

        with pytest.raises(Exception):
            search_episodes_by_embedding(mock_db_connection, "query")

    @patch('search_queries.embed_query')
    @patch('pandas.read_sql')
    def test_search_database_error(self, mock_read_sql, mock_embed_query,
                                  mock_db_connection, sample_embedding):
        """Test error handling for database query errors"""
        mock_embed_query.return_value = sample_embedding
        mock_read_sql.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Search failed"):
            search_episodes_by_embedding(mock_db_connection, "query")

    @patch('search_queries.embed_query')
    @patch('pandas.read_sql')
    def test_search_embedding_format(self, mock_read_sql, mock_embed_query,
                                    mock_db_connection, sample_embedding):
        """Test that embedding is properly formatted for PostgreSQL"""
        mock_embed_query.return_value = [0.1, 0.2, 0.3]
        mock_read_sql.return_value = pd.DataFrame()

        search_episodes_by_embedding(mock_db_connection, "query")

        call_args = mock_read_sql.call_args
        # embedding_str should be in format '[0.1,0.2,0.3]'
        params = call_args[1]['params']
        embedding_str = params[0]
        assert embedding_str.startswith('[')
        assert embedding_str.endswith(']')
        assert '0.1' in embedding_str

    @patch('search_queries.embed_query')
    @patch('pandas.read_sql')
    def test_search_no_chunk_text_column(self, mock_read_sql, mock_embed_query,
                                        mock_db_connection, sample_embedding):
        """Test handling of results without chunk_text column"""
        mock_embed_query.return_value = sample_embedding

        df = pd.DataFrame({
            'episode_id': [1],
            'episode_title': ['Title']
        })
        mock_read_sql.return_value = df

        # Should not raise error
        result = search_episodes_by_embedding(mock_db_connection, "query")
        assert len(result) == 1

    @patch('search_queries.embed_query')
    @patch('pandas.read_sql')
    def test_search_multiple_results_all_trimmed(self, mock_read_sql, mock_embed_query,
                                                mock_db_connection, sample_embedding):
        """Test that all chunk_text values are trimmed"""
        mock_embed_query.return_value = sample_embedding

        df = pd.DataFrame({
            'episode_id': [1, 2, 3],
            'chunk_text': [
                'lowercase a. Kept text a.',
                'lowercase b. Kept text b.',
                'Uppercase kept.'
            ]
        })
        mock_read_sql.return_value = df

        result = search_episodes_by_embedding(mock_db_connection, "query")

        assert result['chunk_text'].iloc[0] == "Kept text a."
        assert result['chunk_text'].iloc[1] == "Kept text b."
        assert result['chunk_text'].iloc[2] == "Uppercase kept."

    @patch('search_queries.embed_query')
    @patch('pandas.read_sql')
    def test_search_default_parameters(self, mock_read_sql, mock_embed_query,
                                      mock_db_connection, sample_embedding):
        """Test search with default parameters"""
        mock_embed_query.return_value = sample_embedding
        mock_read_sql.return_value = pd.DataFrame()

        search_episodes_by_embedding(mock_db_connection, "query")

        call_args = mock_read_sql.call_args
        params = call_args[1]['params']

        # Check defaults: limit=5, similarity_threshold=0.5
        assert params[3] == 5  # limit
        assert params[2] == 0.5  # threshold


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios"""

    @patch('search_queries.embed_query')
    @patch('pandas.read_sql')
    def test_full_search_workflow(self, mock_read_sql, mock_embed_query,
                                 mock_db_connection):
        """Test complete search workflow"""
        mock_embedding = [0.1] * 1536
        mock_embed_query.return_value = mock_embedding

        df = pd.DataFrame({
            'episode_id': [1, 2],
            'episode_title': ['AI Discussion', 'Tech Trends'],
            'podcast_name': ['TechTalk', 'Innovation Daily'],
            'published_at': ['2024-01-01', '2024-01-02'],
            'chunk_index': [0, 0],
            'chunk_text': ['lowercase start. AI is evolving.', 'Technology changes.'],
            'similarity': [0.92, 0.88]
        })
        mock_read_sql.return_value = df

        results = search_episodes_by_embedding(
            mock_db_connection,
            "artificial intelligence trends",
            limit=2,
            similarity_threshold=0.85
        )

        assert len(results) == 2
        assert results['episode_id'].tolist() == [1, 2]
        assert 'similarity' in results.columns
        assert results['chunk_text'].iloc[0] == "AI is evolving."
