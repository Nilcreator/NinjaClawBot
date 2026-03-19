"""Optional Picovoice Porcupine wake-word backend."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

from pi5mic.errors import WakeWordError

from .base import WakeWordDetector, WakeWordResult


class PorcupineWakeWordDetector(WakeWordDetector):
    """Thin lazy-import wrapper around `pvporcupine`."""

    def __init__(
        self,
        *,
        access_key: str,
        keywords: Sequence[str] | None = None,
        keyword_paths: Sequence[str | Path] | None = None,
        model_path: str | Path | None = None,
    ) -> None:
        if not access_key.strip():
            raise WakeWordError("Picovoice access key is required for Porcupine.")
        if not keywords and not keyword_paths:
            keywords = ["picovoice"]

        try:
            import pvporcupine
        except ImportError as exc:  # pragma: no cover - optional dependency path
            raise WakeWordError(
                "The 'pvporcupine' package is required for Porcupine wake-word support."
            ) from exc

        create_kwargs: dict[str, object] = {"access_key": access_key}
        if keywords is not None:
            create_kwargs["keywords"] = list(keywords)
            self._keywords = list(keywords)
        else:
            resolved_paths = [str(Path(path)) for path in keyword_paths or []]
            create_kwargs["keyword_paths"] = resolved_paths
            self._keywords = resolved_paths
        if model_path is not None:
            create_kwargs["model_path"] = str(Path(model_path))

        try:
            self._engine = pvporcupine.create(**create_kwargs)
        except Exception as exc:  # pragma: no cover - native backend path
            raise WakeWordError(f"Could not initialize Porcupine: {exc}") from exc

    @classmethod
    def from_environment(
        cls,
        *,
        env_var: str = "PICOVOICE_ACCESS_KEY",
        keywords: Sequence[str] | None = None,
        keyword_paths: Sequence[str | Path] | None = None,
        model_path: str | Path | None = None,
    ) -> "PorcupineWakeWordDetector":
        """Create a detector from the configured environment variable."""
        access_key = os.getenv(env_var, "").strip()
        if not access_key:
            raise WakeWordError(f"Environment variable '{env_var}' is not set.")
        return cls(
            access_key=access_key,
            keywords=keywords,
            keyword_paths=keyword_paths,
            model_path=model_path,
        )

    @property
    def frame_length(self) -> int:
        """The number of PCM samples expected per frame."""
        return int(self._engine.frame_length)

    @property
    def sample_rate(self) -> int:
        """The expected sample rate for the backend."""
        return int(self._engine.sample_rate)

    def process(self, pcm_frame: Sequence[int]) -> WakeWordResult:
        """Run one frame through Porcupine."""
        try:
            keyword_index = int(self._engine.process(pcm_frame))
        except Exception as exc:  # pragma: no cover - native backend path
            raise WakeWordError(f"Porcupine processing failed: {exc}") from exc

        if keyword_index < 0:
            return WakeWordResult(detected=False)

        keyword = self._keywords[keyword_index] if keyword_index < len(self._keywords) else None
        return WakeWordResult(detected=True, keyword_index=keyword_index, keyword=keyword)

    def close(self) -> None:
        """Release native resources."""
        delete = getattr(self._engine, "delete", None)
        if callable(delete):
            delete()
