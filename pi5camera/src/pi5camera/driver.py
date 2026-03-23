"""Compatibility re-exports for standalone pi5camera usage."""

from pi5camera import (
    CONFIG_FILE_NAME,
    DEFAULT_CONFIG,
    CameraConfigManager,
    FaceStore,
    capture_photo,
    enroll_face_from_image,
    enroll_pending_face,
    get_default_config_filepath,
    recognize_faces,
)

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
