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


def get_episode_response(user_message: str, episode_context: dict, conn, episode_id: int,
                         chat_history: list = None) -> str:
    """Generate chatbot response using RAG approach for a specific episode"""
    current_context = ""
    if episode_has_embeddings(conn, episode_id):
        try:
            query_embedding = get_query_embedding(user_message)
            relevant_chunks = find_similar_chunks_in_episode(
                conn,
                episode_id,
                query_embedding,
                top_k=5
            )

            if relevant_chunks:
                current_episode_context = "\n\n".join([
                    f"[Chunk {chunk['chunk_index']}]: {chunk['chunk_text']}"
                    for chunk in relevant_chunks
                ])
        except Exception as e:
            current_episode_context = f"Error retrieving context: {str(e)}"

    # Check for similar episodes request
    similar_episodes_context = ""
    if any(word in user_message.lower() for word in ['similar', 'like this', 'recommend', 'related episodes']):
        try:
            similar_eps = find_similar_episodes_by_episode_id(
                conn, episode_id, top_k=5)
            if similar_eps:
                similar_episodes_context = "\n\n**Similar Episodes Available:**\n"
                for ep in similar_eps:
                    similar_episodes_context += f"- {ep['episode_title']} ({ep['podcast_name']}) - Similarity: {ep['similarity_score']:.1%}\n"
        except Exception as e:
            pass


if __name__ == "__main__":
    openai_key = get_openai_key()
    print(openai_key)
