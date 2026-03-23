from __future__ import annotations

from pathlib import Path

from pi5camera.config.config_manager import CameraConfigManager
from pi5camera.core.capture import build_output_path


def test_config_defaults_are_root_aware(tmp_path: Path) -> None:
    config_path = tmp_path / "workspace" / "camera.json"
    manager = CameraConfigManager(config_path)

    config = manager.load()

    assert manager.active_root == config_path.parent.resolve()
    assert Path(config["paths"]["photo_dir"]) == config_path.parent.resolve() / "photo"
    assert Path(config["paths"]["data_dir"]) == config_path.parent.resolve() / "camera_data"


def test_build_output_path_supports_directory_and_file_overrides(tmp_path: Path) -> None:
    manager = CameraConfigManager(tmp_path / "camera.json")
    config = manager.load()

    directory_override = build_output_path(
        config,
        output_path=tmp_path / "exports",
        filename_prefix="snapshot",
    )
    file_override = build_output_path(
        config,
        output_path=tmp_path / "exports" / "named-photo.jpg",
    )

    assert directory_override.parent == (tmp_path / "exports").resolve()
    assert directory_override.name.startswith("snapshot-")
    assert directory_override.suffix == ".jpg"
    assert file_override == (tmp_path / "exports" / "named-photo.jpg").resolve()
