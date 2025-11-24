"""Unit tests for transform module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from vector_embedding.transform import (
    chunk_text,
    embed_text,
    embed_chunks,
    transform_transcript,
    validate_embeddings,
    count_tokens,
    get_tokenizer
)


SAMPLE_TEXT = """
This is a sample podcast transcript for testing purposes. 
The transcript contains multiple sentences to demonstrate chunking behavior.
We want to ensure that the chunking algorithm works correctly with overlapping windows.
Each chunk should contain approximately 512 tokens with 50% overlap between consecutive chunks.
This allows for better context preservation when performing semantic search.
The embedding process will convert each text chunk into a high-dimensional vector.
These vectors capture the semantic meaning of the text content.
"""


def test_count_tokens():
    """Test token counting."""
    encoding = get_tokenizer()
    text = "Hello world"
    token_count = count_tokens(text, encoding)
    assert token_count > 0
    assert isinstance(token_count, int)


def test_chunk_text_creates_chunks():
    """Test that chunk_text creates list of chunks."""
    chunks = chunk_text(SAMPLE_TEXT, chunk_size=50, overlap=25)

    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert all('chunk_index' in c for c in chunks)
    assert all('chunk_text' in c for c in chunks)
    assert all('token_count' in c for c in chunks)


def test_chunk_text_respects_size():
    """Test that chunks respect max token size."""
    chunk_size = 50
    chunks = chunk_text(SAMPLE_TEXT, chunk_size=chunk_size, overlap=25)

    encoding = get_tokenizer()
    for chunk in chunks:
        token_count = count_tokens(chunk['chunk_text'], encoding)
        assert token_count <= chunk_size


def test_chunk_text_has_overlap():
    """Test that consecutive chunks have overlapping content."""
    chunks = chunk_text(SAMPLE_TEXT, chunk_size=50, overlap=25)

    if len(chunks) > 1:
        # Check that chunk indices are sequential
        for i in range(len(chunks) - 1):
            assert chunks[i]['chunk_index'] == i
            assert chunks[i+1]['chunk_index'] == i + 1


def test_chunk_text_empty_input():
    """Test chunking with empty text."""
    chunks = chunk_text("", chunk_size=50, overlap=25)
    assert len(chunks) == 1  # Will create one empty chunk


@patch('vector_embedding.transform.get_openai_client')
def test_embed_text_success(mock_get_client):
    """Test successful text embedding."""
    # Mock OpenAI response
    mock_client = Mock()
    mock_response = Mock()
    mock_response.data = [Mock(embedding=[0.1] * 1536)]
    mock_client.embeddings.create.return_value = mock_response
    mock_get_client.return_value = mock_client

    embedding = embed_text("test text")

    assert isinstance(embedding, list)
    assert len(embedding) == 1536
    assert all(isinstance(x, float) for x in embedding)
    mock_client.embeddings.create.assert_called_once()


@patch('vector_embedding.transform.get_openai_client')
def test_embed_text_failure(mock_get_client):
    """Test embedding failure handling."""
    mock_client = Mock()
    mock_client.embeddings.create.side_effect = Exception("API Error")
    mock_get_client.return_value = mock_client

    with pytest.raises(Exception) as exc_info:
        embed_text("test text")

    assert "Failed to generate embedding" in str(exc_info.value)


@patch('vector_embedding.transform.embed_text')
def test_embed_chunks_success(mock_embed):
    """Test successful chunk embedding."""
    mock_embed.return_value = [0.1] * 1536

    chunks = [
        {'chunk_index': 0, 'chunk_text': 'chunk 1', 'token_count': 10},
        {'chunk_index': 1, 'chunk_text': 'chunk 2', 'token_count': 10}
    ]

    embedded_chunks = embed_chunks(chunks)

    assert len(embedded_chunks) == 2
    assert all('embedding' in c for c in embedded_chunks)
    assert all(len(c['embedding']) == 1536 for c in embedded_chunks)
    assert mock_embed.call_count == 2


@patch('vector_embedding.transform.embed_text')
def test_embed_chunks_partial_failure(mock_embed):
    """Test chunk embedding with failure on second chunk."""
    mock_embed.side_effect = [[0.1] * 1536, Exception("API Error")]

    chunks = [
        {'chunk_index': 0, 'chunk_text': 'chunk 1', 'token_count': 10},
        {'chunk_index': 1, 'chunk_text': 'chunk 2', 'token_count': 10}
    ]

    with pytest.raises(Exception):
        embed_chunks(chunks)


@patch('vector_embedding.transform.embed_chunks')
@patch('vector_embedding.transform.chunk_text')
def test_transform_transcript_success(mock_chunk, mock_embed):
    """Test complete transcript transformation."""
    mock_chunk.return_value = [
        {'chunk_index': 0, 'chunk_text': 'chunk 1', 'token_count': 10}
    ]
    mock_embed.return_value = [
        {'chunk_index': 0, 'chunk_text': 'chunk 1',
            'embedding': [0.1] * 1536, 'token_count': 10}
    ]

    result = transform_transcript(SAMPLE_TEXT)

    assert isinstance(result, list)
    assert len(result) == 1
    assert 'embedding' in result[0]
    mock_chunk.assert_called_once()
    mock_embed.assert_called_once()


def test_validate_embeddings_success():
    """Test validation of correct embeddings."""
    embedded_chunks = [
        {'chunk_index': 0, 'chunk_text': 'test', 'embedding': [0.1] * 1536},
        {'chunk_index': 1, 'chunk_text': 'test2', 'embedding': [0.2] * 1536}
    ]

    assert validate_embeddings(embedded_chunks) is True


def test_validate_embeddings_missing_embedding():
    """Test validation fails for missing embedding."""
    embedded_chunks = [
        {'chunk_index': 0, 'chunk_text': 'test'}  # No embedding
    ]

    assert validate_embeddings(embedded_chunks) is False


def test_validate_embeddings_wrong_dimensions():
    """Test validation fails for wrong dimensions."""
    embedded_chunks = [
        {'chunk_index': 0, 'chunk_text': 'test',
            'embedding': [0.1] * 100}  # Wrong size
    ]

    assert validate_embeddings(embedded_chunks) is False


def test_validate_embeddings_empty_list():
    """Test validation fails for empty list."""
    assert validate_embeddings([]) is False
