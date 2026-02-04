import base64
import io

from openai import OpenAI

from backend.config import settings

client = None
if settings.OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
    except Exception as e:
        print(f"Failed to init OpenAI client: {e}")

# Phrases Whisper is known to emit when fed silence or near-silence audio.
# Only includes clearly spurious outputs.  Legitimate short utterances
# (e.g. "hello", "check my balance") are kept; dead-air is filtered
# upstream by the minimum-byte-size checks before transcription is attempted.
HALLUCINATIONS = [
    "copyright",
    "all rights reserved",
    "subtitles",
    "subtitle",
    "amara.org",
    "viewers",
]

# Audio clips shorter than this (bytes) are too brief to contain real speech.
MIN_AUDIO_BYTES = 500


def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribes audio bytes to text using OpenAI Whisper."""
    if not client:
        print("WARNING: No OpenAI Key. Returning mock transcript.")
        return "Check my balance"

    if len(audio_bytes) < MIN_AUDIO_BYTES:
        print(f"Skipped transcription: audio too short ({len(audio_bytes)} bytes)")
        return ""

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "input.webm"

    try:
        transcript = client.audio.transcriptions.create(
            model=settings.STT_MODEL,
            file=audio_file,
            response_format="text",
            language=settings.STT_LANGUAGE,
            prompt=settings.STT_PROMPT,
        )

        # Reject known Whisper hallucination phrases
        text_clean = transcript.strip().lower().rstrip(".!?")
        if text_clean in HALLUCINATIONS:
            print(f"Filtered hallucination: '{transcript}'")
            return ""

        return transcript
    except Exception as e:
        print(f"STT Error: {e}")
        return ""


def generate_audio(text: str) -> str:
    """Generates audio from text using OpenAI TTS (Buffered)."""
    if not client:
        print("WARNING: No OpenAI Key. Returning empty audio.")
        return ""

    try:
        response = client.audio.speech.create(
            model=settings.TTS_MODEL,
            voice=settings.TTS_VOICE,
            input=text,
        )
        return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        print(f"TTS Error: {e}")
        return ""


def stream_audio(text: str):
    """Generates audio from text using OpenAI TTS (Streaming). Yields base64 chunks."""
    if not client:
        return

    try:
        response = client.audio.speech.create(
            model=settings.TTS_MODEL,
            voice=settings.TTS_VOICE,
            input=text,
            response_format="mp3",
        )

        for chunk in response.iter_bytes(chunk_size=settings.AUDIO_CHUNK_SIZE):
            if chunk:
                yield base64.b64encode(chunk).decode('utf-8')
    except Exception as e:
        print(f"TTS Stream Error: {e}")
