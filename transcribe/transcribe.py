"""
Transcription logic for Lambda
"""
import asyncio
import random
from io import BytesIO
from pydub import AudioSegment
from openai import AsyncOpenAI


def split_audio_2min(path, chunk_seconds=120):
    """Split audio into 2-minute FLAC chunks in memory."""
    print("Splitting audio into ~2 minute chunks...")

    audio = AudioSegment.from_file(path)
    duration_ms = len(audio)
    chunk_ms = chunk_seconds * 1000

    chunks = []
    num_chunks = (duration_ms + chunk_ms - 1) // chunk_ms

    for i in range(num_chunks):
        start = i * chunk_ms
        end = min((i + 1) * chunk_ms, duration_ms)

        segment = audio[start:end]

        buffer = BytesIO()
        segment.export(buffer, format="flac")
        buffer.name = f"chunk_{i}.flac"
        buffer.seek(0)

        chunks.append({
            "index": i,
            "buffer": buffer,
            "duration": (end - start) / 1000.0
        })

        print(
            f"Created chunk {i+1}/{num_chunks} ({(end-start)/60000:.1f} min)")

    return chunks


async def transcribe_chunk_async(client, chunk):
    """Async transcription of a single chunk."""
    idx = chunk["index"]
    print(f"Transcribing chunk {idx+1}...")

    buffer = chunk["buffer"]
    buffer.seek(0)

    response = await client.audio.transcriptions.create(
        model="gpt-4o-transcribe-diarize",
        file=("chunk.flac", buffer, "audio/flac"),
        response_format="diarized_json",
        chunking_strategy="auto"
    )

    return idx, response


async def robust_transcribe_chunk(client, chunk, retries=3):
    """Robust async retry wrapper."""
    for attempt in range(retries):
        try:
            return await transcribe_chunk_async(client, chunk)
        except Exception as e:
            if attempt == retries - 1:
                raise
            wait = 1.5 + random.random() * 2
            print(
                f"Chunk {chunk['index']} failed attempt {attempt+1}/{retries}, retrying in {wait:.1f}s")
            await asyncio.sleep(wait)


async def transcribe_full_audio_async(path, concurrency=4):
    """Async transcription pipeline."""
    client = AsyncOpenAI()

    chunks = split_audio_2min(path)

    print(f"\nStarting async transcription with concurrency={concurrency}\n")

    semaphore = asyncio.Semaphore(concurrency)

    async def sem_task(chunk):
        async with semaphore:
            return await robust_transcribe_chunk(client, chunk)

    tasks = [asyncio.create_task(sem_task(chunk)) for chunk in chunks]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    full_text = ""
    all_segments = []
    global_offset = 0

    for (chunk, res) in zip(chunks, results):
        idx = chunk["index"]
        if isinstance(res, Exception):
            print(f"Chunk {idx+1} failed permanently: {res}")
            raise Exception(
                f"Transcription failed: chunk {idx+1} could not be processed")

        idx_returned, r = res

        full_text += r.text + " "

        for seg in r.segments:
            all_segments.append({
                "speaker": seg.speaker,
                "start": seg.start + global_offset,
                "end": seg.end + global_offset,
                "text": seg.text,
                "chunk": idx,
            })

        global_offset += chunk["duration"]
        print(f"Completed chunk {idx+1}")

    all_segments.sort(key=lambda s: s["start"])

    print("\nAll async chunks processed successfully!")

    return {
        "text": full_text.strip(),
        "segments": all_segments
    }


def transcribe_audio(audio_file_path):
    """Main transcription function."""
    return asyncio.run(transcribe_full_audio_async(audio_file_path, concurrency=5))
