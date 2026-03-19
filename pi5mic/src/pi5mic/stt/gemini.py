"""Gemini batch speech-to-text backend."""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path

from pi5mic.errors import STTError
from pi5mic.models import TranscriptionResult

from .base import SpeechToTextBackend

_TRANSCRIPTION_PROMPT = (
    "Transcribe this audio. Preserve the spoken language and return only the transcript text."
)


class GeminiBackend(SpeechToTextBackend):
    """Run batch audio transcription through the Gemini API."""

    def __init__(
        self,
        *,
        model: str = "gemini-3-flash-preview",
    ) -> None:
        self.model = model

    def transcribe(self, audio_path: str | Path) -> TranscriptionResult:
        """Transcribe an audio file through Gemini."""
        source = Path(audio_path).expanduser().resolve()
        if not source.is_file():
            raise STTError(f"Audio file not found: {source}")

        if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
            raise STTError("Gemini credentials are not configured in the environment.")

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - optional dependency path
            raise STTError(
                "The 'google-genai' package is required for Gemini transcription."
            ) from exc

        mime_type = mimetypes.guess_type(source.name)[0] or "audio/wav"
        if mime_type in {"audio/x-wav", "audio/vnd.wave"}:
            mime_type = "audio/wav"
        audio_bytes = source.read_bytes()
        client = genai.Client()

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                    _TRANSCRIPTION_PROMPT,
                ],
            )
        except Exception as exc:  # pragma: no cover - network/backend path
            raise STTError(f"Gemini transcription failed: {exc}") from exc

        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise STTError("Gemini did not return transcript text.")

        return TranscriptionResult(
            text=text.strip(),
            backend="gemini",
            model=self.model,
            raw={"mime_type": mime_type},
        )
