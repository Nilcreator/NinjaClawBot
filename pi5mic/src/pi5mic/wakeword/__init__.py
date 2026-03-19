"""Wake-word backends for pi5mic."""

from pi5mic.wakeword.base import WakeWordDetector, WakeWordResult
from pi5mic.wakeword.porcupine import PorcupineWakeWordDetector

__all__ = ["PorcupineWakeWordDetector", "WakeWordDetector", "WakeWordResult"]
