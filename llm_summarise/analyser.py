"""OpenAI API integration for transcript analysis."""
import os
import json
import logging
from typing import Dict
from openai import OpenAI

logger = logging.getLogger(__name__)


# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = 'gpt-4o-mini'


def get_openai_client():
    """Get OpenAI client."""
    return OpenAI(api_key=OPENAI_API_KEY)


def build_analysis_prompt(transcript: str) -> str:
    """Build prompt for OpenAI analysis. Returns formatted prompt string."""
    # Truncate transcript to avoid token limits (~10k chars = ~2500 tokens)
    truncated = transcript[:10000]

    return f"""Analyze this podcast transcript and extract:

1. Topics: 2-4 main topics or themes discussed
2. Summary: A 3-sentence summary

Return JSON with this structure:
{{
  "topics": ["topic1", "topic2"],
  "summary": "summary text"
}}

Transcript:
{truncated}"""


def call_openai_api(prompt: str) -> Dict:
    """Call OpenAI API with prompt. Returns parsed JSON response from OpenAI."""
    client = get_openai_client()

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are a podcast analyst. Extract structured information from transcripts."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except json.JSONDecodeError as e:
        raise Exception(f"OpenAI returned invalid JSON: {str(e)}")
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")


def parse_analysis_response(response: Dict) -> Dict:
    """Parse and validate OpenAI response. Returns validated analysis dict."""
    return {
        'topics': response.get('topics', []),
        'summary': response.get('summary', '')
    }


def analyze_transcript(transcript: str) -> Dict:
    """
    Analyze transcript using OpenAI.

    Returns:
        Analysis results dict with keys:
        - topics: List of topic strings
        - summary: Summary string
    """
    logger.info(f"Analyzing transcript ({len(transcript)} chars)")

    # Build prompt
    prompt = build_analysis_prompt(transcript)

    # Call OpenAI
    raw_response = call_openai_api(prompt)

    # Parse and validate
    analysis = parse_analysis_response(raw_response)

    logger.info(f"Analysis complete: {len(analysis['topics'])} topics")

    return analysis
