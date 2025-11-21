"""OpenAI API integration for transcript analysis."""
import os
import json
import logging
from typing import Dict, List
from openai import OpenAI

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = 'gpt-4o-mini'
MAX_TRANSCRIPT_CHARS = 10_000


def get_openai_client():
    """Initializes and returns OpenAI client."""
    logger.debug(f"Getting OpenAI client with model: {OPENAI_MODEL}")
    return OpenAI(api_key=OPENAI_API_KEY)


def extract_speaker_samples(segments: List[Dict], max_chars_per_speaker: int = 500) -> Dict[str, str]:
    """Extract representative text samples from each speaker."""
    logger.info(
        f"Extracting speaker samples from {len(segments)} segments (max {max_chars_per_speaker} chars per speaker)")
    speaker_samples = {}

    for segment in segments:
        speaker = segment.get('speaker')
        text = segment.get('text', '').strip()

        if not speaker or not text:
            continue

        if speaker not in speaker_samples:
            speaker_samples[speaker] = ""

        # Add text until we hit the character limit
        if len(speaker_samples[speaker]) < max_chars_per_speaker:
            speaker_samples[speaker] += text + " "

    # Trim to max length
    for speaker in speaker_samples:
        speaker_samples[speaker] = speaker_samples[speaker][:max_chars_per_speaker].strip()

    logger.info(
        f"Extracted samples for {len(speaker_samples)} speakers: {list(speaker_samples.keys())}")
    return speaker_samples


def build_analysis_prompt(transcript: str, speaker_samples: Dict[str, str] = None) -> str:
    """Build prompt for OpenAI analysis with optional speaker samples."""
    logger.info(
        f"Building analysis prompt (transcript: {len(transcript)} chars, speaker_samples: {bool(speaker_samples)})")
    # Truncate transcript to avoid token limits (~10k chars = ~2500 tokens)
    truncated = transcript[:MAX_TRANSCRIPT_CHARS]

    prompt = f"""Analyze this podcast transcript and extract:

1. Topics: 2-4 broad, general topics (1-2 words each, e.g., "Technology", "Politics", "Health")
2. Summary: A 3-sentence summary
3. Speakers: List of identifiable speaker names (ONLY if names are clearly stated)

TRANSCRIPT (for topic/summary analysis):
{truncated}
"""

    # Add speaker samples if provided
    if speaker_samples:
        prompt += "\n\nSPEAKER SAMPLES (for identification):\n"
        for label, text in speaker_samples.items():
            prompt += f"\nSpeaker {label} said:\n\"{text}\"\n"

        prompt += """
Based on these samples, identify each speaker's real name if clearly stated.
- ONLY return names that are explicitly mentioned or introduced
- If a speaker's name is not clear, DO NOT include them in the response
- Do NOT use placeholders like "Host", "Guest", or speaker labels
"""

    prompt += """
Return JSON with this structure:
{
  "topics": ["Technology", "Business"],
  "summary": "summary text",
  "speakers": [{"name": "John Smith"}, {"name": "Jane Doe"}]
}

For topics: Use broad, general category names (1-2 words). Examples: "AI", "Business", "Health", "Politics", "Science", "Entertainment", "Sports", "Technology"

If no speaker names are identifiable, return empty speakers array: "speakers": []
"""

    return prompt


def call_openai_api(prompt: str) -> Dict:
    """Calls OpenAI API and returns parsed JSON response."""
    logger.info(
        f"Calling OpenAI API with {OPENAI_MODEL} model (prompt: {len(prompt)} chars)")
    client = get_openai_client()

    try:
        logger.debug("Sending request to OpenAI API")
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are a podcast analyst. Extract structured information from transcripts. Only identify speakers when their names are explicitly stated."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.choices[0].message.content
        logger.info("OpenAI API request successful")
        return json.loads(content)

    except json.JSONDecodeError as e:
        logger.error(f"OpenAI returned invalid JSON: {str(e)}")
        raise Exception(f"OpenAI returned invalid JSON: {str(e)}")
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise Exception(f"OpenAI API error: {str(e)}")


def parse_analysis_response(response: Dict) -> Dict:
    """Parses and validates OpenAI response into structured format."""
    logger.info(
        f"Parsing response with {len(response.get('topics', []))} topics, {len(response.get('speakers', []))} speakers")
    speakers = response.get('speakers', [])

    # Ensure speakers is a list of dicts with valid 'name' string
    validated_speakers = []
    for speaker in speakers:
        if isinstance(speaker, dict) and 'name' in speaker:
            name = speaker['name']
            # Validate name is a non-empty string
            if isinstance(name, str) and name.strip():
                validated_speakers.append(name.strip())
                logger.debug(f"Validated speaker: {name}")
            else:
                logger.warning(
                    f"Skipping invalid speaker name (not a string): {name}")

    result = {
        'topics': response.get('topics', []),
        'summary': response.get('summary', ''),
        'speakers': validated_speakers
    }
    logger.info(
        f"Parsed {len(result['topics'])} topics, {len(result['speakers'])} speakers")
    return result


def analyze_transcript(transcript: str, segments: List[Dict] = None) -> Dict:
    """Analyzes transcript using OpenAI API and returns topics, summary, and speakers."""
    logger.info(
        f"Starting analysis: {len(transcript)} chars, {len(segments or [])} segments")

    # Extract speaker samples if segments provided
    speaker_samples = None
    if segments:
        speaker_samples = extract_speaker_samples(segments)
        logger.info(
            f"Using {len(speaker_samples)} speaker samples for identification")

    # Build prompt
    logger.debug("Building analysis prompt")
    prompt = build_analysis_prompt(transcript, speaker_samples)

    # Call OpenAI
    logger.debug("Calling OpenAI API")
    raw_response = call_openai_api(prompt)

    # Parse and validate
    logger.debug("Parsing response")
    analysis = parse_analysis_response(raw_response)

    logger.info(
        f"Analysis complete: {len(analysis['topics'])} topics, {len(analysis['speakers'])} speakers")
    return analysis
