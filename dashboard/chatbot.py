"""Chatbot script which handles user interactions and responses about episodes with RAG"""
import json
import boto3
from botocore.exceptions import ClientError
from openai import OpenAI
from rds_embedding_queries import (
    find_similar_chunks_in_episode,
    episode_has_embeddings,
    find_similar_episodes_by_episode_id
)


def get_openai_key() -> str:
    """Retrieve OpenAI API key from AWS Secrets Manager"""
    secret_name = "c20-quadcast-secrets"
    region_name = "eu-west-2"
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = get_secret_value_response['SecretString']
    secret_dict = json.loads(secret)
    return secret_dict.get('OPENAI_API_KEY')


# Initialise openai client based on secrets manager api key
openai_key = get_openai_key()
client = OpenAI(api_key=openai_key)


def get_query_embedding(text: str) -> list:
    """Get embedding for user's question using OpenAI"""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def fetch_episode_chunks(conn, episode_id: int, query_embedding: list) -> str:
    """Fetch and format relevant chunks for an episode using pre-computed embedding."""

    if not episode_has_embeddings(conn, episode_id):
        return ""

    try:
        relevant_chunks = find_similar_chunks_in_episode(
            conn,
            episode_id,
            query_embedding,
            top_k=5
        )

        if relevant_chunks:
            return "\n\n".join([
                f"[Chunk {chunk['chunk_index']}]: {chunk['chunk_text']}"
                for chunk in relevant_chunks
            ])
        return ""
    except Exception as e:
        return f"Error retrieving context: {str(e)}"


def is_message_about_similar_eps(user_message: str) -> bool:
    """Determine if user is asking for similar episodes."""
    keywords = ['similar', 'like this', 'recommend', 'related episodes']
    return any(word in user_message.lower() for word in keywords)


def fetch_similar_episodes(conn, episode_id: int, top_k: int = 5) -> str:
    """Fetch and format similar episodes."""
    from rds_embedding_queries import find_similar_episodes_by_episode_id

    try:
        similar_eps = find_similar_episodes_by_episode_id(
            conn, episode_id, top_k=top_k
        )

        if not similar_eps:
            return ""

        context = "\n\n**Similar Episodes Available:**\n"
        for ep in similar_eps:
            context += (
                f"- {ep['episode_title']} ({ep['podcast_name']}) - "
                f"Similarity: {ep['similarity_score']:.1%}\n"
            )
        return context
    except Exception:
        return ""


def build_episode_context(conn, episode_id: int, query_embedding: list, user_message: str) -> dict:
    """Build complete context for episode response."""
    chunks_context = fetch_episode_chunks(conn, episode_id, query_embedding)

    similar_episodes_context = ""
    if is_message_about_similar_eps(user_message):
        similar_episodes_context = fetch_similar_episodes(conn, episode_id)

    return {
        'chunks': chunks_context,
        'similar_episodes': similar_episodes_context
    }


if __name__ == "__main__":
    openai_key = get_openai_key()
    print(openai_key)
