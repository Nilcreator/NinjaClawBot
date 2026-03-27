"""Public package exports for pi5camera.

The package keeps hardware and image-processing imports lazy so lightweight
commands such as ``uv run pi5camera --help`` do not depend on Pillow,
Picamera2, or face-recognition loading successfully at startup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pi5camera.config.config_manager import (
    CONFIG_FILE_NAME,
    DEFAULT_CONFIG,
    CameraConfigManager,
    get_default_config_filepath,
)

if TYPE_CHECKING:
    from pi5camera.core.capture import capture_photo
    from pi5camera.core.enrollment import enroll_face_from_image, enroll_pending_face
    from pi5camera.core.recognition import recognize_faces
    from pi5camera.storage.face_store import FaceStore

__all__ = [
    "CONFIG_FILE_NAME",
    "DEFAULT_CONFIG",
    "CameraConfigManager",
    "FaceStore",
    "capture_photo",
    "enroll_face_from_image",
    "enroll_pending_face",
    "get_default_config_filepath",
    "recognize_faces",
]


def __getattr__(name: str):
    if name == "capture_photo":
        from pi5camera.core.capture import capture_photo

        return capture_photo
    if name == "enroll_face_from_image":
        from pi5camera.core.enrollment import enroll_face_from_image

        return enroll_face_from_image
    if name == "enroll_pending_face":
        from pi5camera.core.enrollment import enroll_pending_face

        return enroll_pending_face
    if name == "recognize_faces":
        from pi5camera.core.recognition import recognize_faces

        return recognize_faces
    if name == "FaceStore":
        from pi5camera.storage.face_store import FaceStore

        return FaceStore
    raise AttributeError(f"module 'pi5camera' has no attribute {name!r}")
