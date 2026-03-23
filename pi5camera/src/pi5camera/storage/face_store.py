"""Filesystem-backed storage for pi5camera."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from PIL import Image

from pi5camera.errors import StorageError
from pi5camera.models import FaceBoundingBox


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _timestamp() -> str:
    return _utc_now().strftime("%Y%m%d-%H%M%S")


def _slugify_name(name: str) -> str:
    raw = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in name.strip())
    return raw.strip("_") or "person"


class FaceStore:
    """Store photo output, known faces, and pending recognition state."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config
        paths = config.get("paths", {})
        recognition = config.get("recognition", {})
        self.photo_dir = Path(str(paths["photo_dir"])).expanduser().resolve()
        self.data_dir = Path(str(paths["data_dir"])).expanduser().resolve()
        self.known_faces_dir = self.data_dir / "known_faces"
        self.index_dir = self.data_dir / "index"
        self.index_path = self.index_dir / "encodings.json"
        self.pending_dir = self.data_dir / "pending"
        self.pending_ttl_seconds = int(recognition.get("pending_ttl_seconds", 86_400))
        self.save_unknown_crops = bool(recognition.get("save_unknown_crops", True))

    def ensure_layout(self) -> None:
        """Create the expected storage directories."""
        try:
            self.photo_dir.mkdir(parents=True, exist_ok=True)
            self.known_faces_dir.mkdir(parents=True, exist_ok=True)
            self.index_dir.mkdir(parents=True, exist_ok=True)
            self.pending_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(f"Could not create camera storage directories: {exc}") from exc

    def create_photo_path(self, *, prefix: str = "photo") -> Path:
        """Create a timestamped output path in the configured photo directory."""
        self.ensure_layout()
        return self.photo_dir / f"{prefix}-{_timestamp()}.jpg"

    def _load_index(self) -> dict[str, Any]:
        self.ensure_layout()
        if not self.index_path.exists():
            return {"version": 1, "entries": []}
        try:
            with self.index_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError(f"Could not read face index '{self.index_path}': {exc}") from exc
        if not isinstance(data, dict):
            raise StorageError(f"Face index '{self.index_path}' must contain a JSON object.")
        entries = data.get("entries")
        if not isinstance(entries, list):
            raise StorageError(f"Face index '{self.index_path}' is missing a valid entries list.")
        return data

    def _save_index(self, payload: dict[str, Any]) -> None:
        try:
            self.index_dir.mkdir(parents=True, exist_ok=True)
            with self.index_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
                handle.write("\n")
        except OSError as exc:
            raise StorageError(f"Could not write face index '{self.index_path}': {exc}") from exc

    def list_known_faces(self) -> list[str]:
        """Return all known saved identity names."""
        index = self._load_index()
        names = {str(entry.get("name", "")).strip() for entry in index["entries"]}
        return sorted(name for name in names if name)

    def load_known_entries(self) -> list[dict[str, Any]]:
        """Return all stored known-face entries."""
        return list(self._load_index()["entries"])

    def remove_known_face(self, name: str) -> bool:
        """Remove all stored data for a known identity."""
        normalized = name.strip()
        if not normalized:
            return False

        index = self._load_index()
        before_count = len(index["entries"])
        index["entries"] = [
            entry for entry in index["entries"] if str(entry.get("name", "")).strip() != normalized
        ]
        if len(index["entries"]) == before_count:
            return False

        self._save_index(index)
        person_dir = self.known_faces_dir / _slugify_name(normalized)
        if person_dir.exists():
            shutil.rmtree(person_dir, ignore_errors=True)
        return True

    def _save_crop(self, source_image: Path, box: FaceBoundingBox, destination: Path) -> Path:
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(source_image) as image:
                cropped = image.crop(box.as_crop_box())
                cropped.save(destination)
        except OSError as exc:
            raise StorageError(f"Could not save face crop '{destination}': {exc}") from exc
        return destination

    def save_known_face(
        self,
        *,
        name: str,
        source_image: Path,
        box: FaceBoundingBox,
        encoding: list[float],
        crop_path: str | None = None,
    ) -> Path:
        """Save an enrolled face crop and append it to the known index."""
        normalized_name = name.strip()
        if not normalized_name:
            raise StorageError("Known face name must not be empty.")

        self.ensure_layout()
        person_dir = self.known_faces_dir / _slugify_name(normalized_name)
        destination = person_dir / f"{_timestamp()}.jpg"

        if crop_path:
            crop_source = Path(crop_path).expanduser().resolve()
            try:
                person_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(crop_source, destination)
            except OSError as exc:
                raise StorageError(
                    f"Could not copy saved face image to '{destination}': {exc}"
                ) from exc
        else:
            self._save_crop(source_image, box, destination)

        index = self._load_index()
        index["entries"].append(
            {
                "name": normalized_name,
                "encoding": [float(value) for value in encoding],
                "image_path": str(destination),
                "saved_at": _utc_now().isoformat(),
            }
        )
        self._save_index(index)
        return destination

    def purge_expired_pending(self) -> None:
        """Delete expired pending-recognition records."""
        self.ensure_layout()
        for record_dir in self.pending_dir.iterdir():
            if not record_dir.is_dir():
                continue
            record_path = record_dir / "record.json"
            try:
                with record_path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
            except (OSError, json.JSONDecodeError):
                shutil.rmtree(record_dir, ignore_errors=True)
                continue
            expires_at = str(payload.get("expires_at", "")).strip()
            if not expires_at:
                continue
            try:
                expiry = datetime.fromisoformat(expires_at)
            except ValueError:
                shutil.rmtree(record_dir, ignore_errors=True)
                continue
            if _utc_now() >= expiry:
                shutil.rmtree(record_dir, ignore_errors=True)

    def save_pending_recognition(
        self,
        *,
        photo_path: Path,
        photo_metadata: dict[str, Any],
        unknown_faces: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Persist unknown-face context for later enrollment."""
        self.ensure_layout()
        self.purge_expired_pending()

        recognition_id = uuid4().hex
        record_dir = self.pending_dir / recognition_id
        record_dir.mkdir(parents=True, exist_ok=True)

        stored_faces: list[dict[str, Any]] = []
        for face in unknown_faces:
            face_id = str(face["face_id"])
            crop_path = None
            if self.save_unknown_crops:
                crop_destination = record_dir / f"{face_id}.jpg"
                crop_path = str(
                    self._save_crop(
                        photo_path,
                        FaceBoundingBox.from_dict(face["bounding_box"]),
                        crop_destination,
                    )
                )

            stored_face = dict(face)
            stored_face["crop_path"] = crop_path
            stored_faces.append(stored_face)

        payload = {
            "recognition_id": recognition_id,
            "created_at": _utc_now().isoformat(),
            "expires_at": (_utc_now() + timedelta(seconds=self.pending_ttl_seconds)).isoformat(),
            "photo_path": str(photo_path),
            "photo_metadata": dict(photo_metadata),
            "faces": stored_faces,
        }
        record_path = record_dir / "record.json"
        try:
            with record_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
                handle.write("\n")
        except OSError as exc:
            raise StorageError(
                f"Could not write pending recognition '{record_path}': {exc}"
            ) from exc
        return payload

    def load_pending_record(self, recognition_id: str) -> dict[str, Any]:
        """Load a pending-recognition record by id."""
        self.purge_expired_pending()
        record_path = self.pending_dir / recognition_id / "record.json"
        if not record_path.exists():
            raise StorageError(f"Unknown pending recognition '{recognition_id}'.")
        try:
            with record_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError(
                f"Could not read pending recognition '{record_path}': {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise StorageError(f"Pending recognition '{record_path}' must be a JSON object.")
        return payload

    def save_pending_record(self, recognition_id: str, payload: dict[str, Any]) -> None:
        """Update an existing pending-recognition record."""
        record_path = self.pending_dir / recognition_id / "record.json"
        try:
            with record_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
                handle.write("\n")
        except OSError as exc:
            raise StorageError(
                f"Could not update pending recognition '{record_path}': {exc}"
            ) from exc

    def remove_pending_record(self, recognition_id: str) -> None:
        """Delete a pending-recognition record directory."""
        shutil.rmtree(self.pending_dir / recognition_id, ignore_errors=True)
