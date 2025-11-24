"""Text chunking and embedding transformation for RAG pipeline."""
import os
import logging
import tempfile
from typing import List, Dict
import tiktoken
from openai import OpenAI

logger = logging.getLogger(__name__)

# Set tiktoken cache directory to temp location for testing/CI environments
if not os.getenv('TIKTOKEN_CACHE_DIR'):
    os.environ['TIKTOKEN_CACHE_DIR'] = tempfile.gettempdir()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
EMBEDDING_MODEL = 'text-embedding-3-small'
CHUNK_SIZE = 512
CHUNK_OVERLAP = 256


def get_openai_client():
    """Get OpenAI client instance."""
    return OpenAI(api_key=OPENAI_API_KEY)


def get_tokenizer(model: str = EMBEDDING_MODEL):
    """Get tiktoken tokenizer for the embedding model."""
    encoding = tiktoken.encoding_for_model(model)
    return encoding


def count_tokens(text: str, encoding) -> int:
    """Count number of tokens in text."""
    return len(encoding.encode(text))


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict]:
    """Split text into overlapping chunks of specified token size."""
    encoding = get_tokenizer()
    tokens = encoding.encode(text)

    chunks = []
    start_idx = 0
    chunk_index = 0

    logger.info(
        f"Chunking text: {len(tokens)} tokens into {chunk_size}-token chunks with {overlap}-token overlap")

    if not tokens:
        # Handle empty input - create one empty chunk
        chunks.append({
            'chunk_index': 0,
            'chunk_text': '',
            'token_count': 0,
            'start_token': 0,
            'end_token': 0
        })
    else:
        while start_idx < len(tokens):
            end_idx = start_idx + chunk_size
            chunk_tokens = tokens[start_idx:end_idx]
            chunk_text = encoding.decode(chunk_tokens)

            chunks.append({
                'chunk_index': chunk_index,
                'chunk_text': chunk_text,
                'token_count': len(chunk_tokens),
                'start_token': start_idx,
                'end_token': end_idx
            })

            chunk_index += 1
            start_idx += (chunk_size - overlap)

    logger.info(f"Created {len(chunks)} chunks")
    return chunks


def embed_text(text: str, model: str = EMBEDDING_MODEL) -> List[float]:
    """Generate embedding vector for text using OpenAI API."""
    client = get_openai_client()

    try:
        response = client.embeddings.create(
            model=model,
            input=text
        )
        embedding = response.data[0].embedding
        logger.debug(f"Generated embedding: {len(embedding)} dimensions")
        return embedding

    except Exception as e:
        logger.error(f"OpenAI embedding error: {str(e)}")
        raise Exception(f"Failed to generate embedding: {str(e)}") from e


def embed_chunks(chunks: List[Dict], model: str = EMBEDDING_MODEL) -> List[Dict]:
    """Generate embeddings for all chunks."""
    logger.info(f"Generating embeddings for {len(chunks)} chunks")

    embedded_chunks = []

    for i, chunk in enumerate(chunks):
        try:
            embedding = embed_text(chunk['chunk_text'], model)

            embedded_chunk = {
                'chunk_index': chunk['chunk_index'],
                'chunk_text': chunk['chunk_text'],
                'embedding': embedding,
                'token_count': chunk['token_count']
            }

            embedded_chunks.append(embedded_chunk)
            logger.debug(f"Embedded chunk {i+1}/{len(chunks)}")

        except Exception as e:
            logger.error(f"Failed to embed chunk {i}: {str(e)}")
            raise

    logger.info(f"Successfully embedded {len(embedded_chunks)} chunks")
    return embedded_chunks


def transform_transcript(transcript: str) -> List[Dict]:
    """Transform transcript into embedded chunks ready for storage."""
    logger.info(f"Transforming transcript: {len(transcript)} characters")

    # Step 1: Chunk the text
    chunks = chunk_text(transcript)

    # Step 2: Generate embeddings
    embedded_chunks = embed_chunks(chunks)

    logger.info(
        f"Transformation complete: {len(embedded_chunks)} embedded chunks")

    return embedded_chunks


def validate_embeddings(embedded_chunks: List[Dict], expected_dimensions: int = 1536) -> bool:
    """Validate that all embeddings have correct dimensions."""
    if not embedded_chunks:
        logger.warning("No embedded chunks to validate")
        return False

    for chunk in embedded_chunks:
        if 'embedding' not in chunk:
            logger.error(f"Chunk {chunk['chunk_index']} missing embedding")
            return False

        if len(chunk['embedding']) != expected_dimensions:
            logger.error(
                f"Chunk {chunk['chunk_index']} has wrong dimensions: {len(chunk['embedding'])}")
            return False

    logger.info(f"All {len(embedded_chunks)} chunks validated successfully")
    return True
