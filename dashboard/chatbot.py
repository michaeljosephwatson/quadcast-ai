"""Chatbot script which handles user interactions and responses about episodes with RAG"""
import boto3
from botocore.exceptions import ClientError
from openai import OpenAI


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
    return secret


if __name__ == "__main__":
    openai_key = get_openai_key()
    print("Successfully retrieved OpenAI key from Secrets Manager.")
