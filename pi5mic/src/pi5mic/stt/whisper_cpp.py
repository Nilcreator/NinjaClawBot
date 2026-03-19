"""whisper.cpp speech-to-text backend."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from pi5mic.errors import STTError
from pi5mic.install.whisper_cpp import resolve_model_path, resolve_whisper_cpp_command
from pi5mic.models import TranscriptionResult

from .base import SpeechToTextBackend


class WhisperCppBackend(SpeechToTextBackend):
    """Run local batch transcription through `whisper-cli`."""

    def __init__(
        self,
        *,
        command: str | Path | None,
        model_path: str | Path,
        language: str = "auto",
        translate_to_english: bool = False,
        threads: int | None = None,
        timeout_seconds: int = 120,
    ) -> None:
        self.command = resolve_whisper_cpp_command(command)
        self.model_path = resolve_model_path(model_path)
        self.language = language
        self.translate_to_english = translate_to_english
        self.threads = threads
        self.timeout_seconds = timeout_seconds

    def transcribe(self, audio_path: str | Path) -> TranscriptionResult:
        """Transcribe an audio file through whisper.cpp."""
        source = Path(audio_path).expanduser().resolve()
        if not source.is_file():
            raise STTError(f"Audio file not found: {source}")

        with tempfile.TemporaryDirectory(prefix="pi5mic-whispercpp-") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            output_prefix = temp_dir / source.stem
            command = [
                str(self.command),
                "-m",
                str(self.model_path),
                "-f",
                str(source),
                "-ojf",
                "-of",
                str(output_prefix),
                "-l",
                self.language,
            ]
            if self.threads is not None:
                command.extend(["-t", str(self.threads)])
            if self.translate_to_english:
                command.append("-tr")

            try:
                result = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                raise STTError("whisper.cpp transcription timed out.") from exc
            except OSError as exc:
                raise STTError(f"Could not start whisper.cpp: {exc}") from exc

            if result.returncode != 0:
                stderr = result.stderr.strip() or result.stdout.strip() or "unknown error"
                raise STTError(f"whisper.cpp transcription failed: {stderr}")

            json_path = Path(f"{output_prefix}.json")
            if not json_path.exists():
                raise STTError("whisper.cpp completed without producing a JSON transcript.")

            with json_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)

        text = _extract_transcript_text(payload)
        language = payload.get("language")
        return TranscriptionResult(
            text=text,
            backend="whisper_cpp",
            model=self.model_path.name,
            language=str(language) if language is not None else None,
            raw=payload,
        )


def _extract_transcript_text(payload: dict[str, object]) -> str:
    direct_text = payload.get("text")
    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text.strip()

    for key in ("transcription", "segments"):
        value = payload.get(key)
        if isinstance(value, list):
            parts = []
            for item in value:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"].strip())
            text = " ".join(part for part in parts if part).strip()
            if text:
                return text

    raise STTError("whisper.cpp JSON output did not contain transcript text.")
