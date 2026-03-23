"""CLI command exports for pi5camera."""

from .camera_tool import camera_tool
from .capture_cmd import capture_cmd
from .doctor import doctor
from .enroll_cmd import enroll_cmd
from .manage_faces_cmd import manage_faces
from .recognize_cmd import recognize_cmd
from .setup_cmd import setup_cmd
from .status import status

__all__ = [
    "camera_tool",
    "capture_cmd",
    "doctor",
    "enroll_cmd",
    "manage_faces",
    "recognize_cmd",
    "setup_cmd",
    "status",
]
