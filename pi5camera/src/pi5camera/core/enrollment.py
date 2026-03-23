"""Enrollment workflows for pi5camera."""

from __future__ import annotations

from pathlib import Path

from pi5camera.errors import EnrollmentError
from pi5camera.models import FaceBoundingBox
from pi5camera.recognition.face_recognition_backend import build_recognition_backend
from pi5camera.storage.face_store import FaceStore


def enroll_face_from_image(config: dict, *, name: str, image_path: Path) -> dict:
    """Enroll a known face from a still image file."""
    source_image = image_path.expanduser().resolve()
    backend = build_recognition_backend(config)
    detected = backend.detect_and_encode(source_image)
    if not detected:
        raise EnrollmentError(f"No faces were found in '{source_image}'.")
    if len(detected) > 1:
        raise EnrollmentError(
            f"Found {len(detected)} faces in '{source_image}'. Use a single-face image for enrollment."
        )

    store = FaceStore(config)
    saved_path = store.save_known_face(
        name=name,
        source_image=source_image,
        box=detected[0].bounding_box,
        encoding=detected[0].encoding,
    )
    return {
        "name": name.strip(),
        "source_image_path": str(source_image),
        "saved_image_path": str(saved_path),
    }


def enroll_pending_face(
    config: dict,
    *,
    recognition_id: str,
    face_id: str,
    name: str,
) -> dict:
    """Enroll a pending unknown face using a previously saved recognition result."""
    normalized_name = name.strip()
    if not normalized_name:
        raise EnrollmentError("Known face name must not be empty.")

    store = FaceStore(config)
    pending = store.load_pending_record(recognition_id)
    pending_faces = pending.get("faces", [])
    if not isinstance(pending_faces, list):
        raise EnrollmentError(f"Pending recognition '{recognition_id}' is malformed.")

    target_face = None
    remaining_faces: list[dict] = []
    for face in pending_faces:
        if str(face.get("face_id")) == face_id and target_face is None:
            target_face = face
            continue
        remaining_faces.append(face)

    if target_face is None:
        raise EnrollmentError(
            f"Pending recognition '{recognition_id}' does not contain face '{face_id}'."
        )

    photo_path = Path(str(pending["photo_path"])).expanduser().resolve()
    box = FaceBoundingBox.from_dict(target_face["bounding_box"])
    saved_path = store.save_known_face(
        name=normalized_name,
        source_image=photo_path,
        box=box,
        encoding=[float(value) for value in target_face.get("encoding", [])],
        crop_path=target_face.get("crop_path"),
    )

    if remaining_faces:
        pending["faces"] = remaining_faces
        store.save_pending_record(recognition_id, pending)
    else:
        store.remove_pending_record(recognition_id)

    return {
        "recognition_id": recognition_id,
        "face_id": face_id,
        "name": normalized_name,
        "saved_image_path": str(saved_path),
        "pending_remaining": len(remaining_faces),
    }
