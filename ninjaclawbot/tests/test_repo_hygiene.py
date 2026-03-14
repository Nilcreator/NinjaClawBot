from __future__ import annotations

import subprocess
from pathlib import Path


def test_repository_does_not_track_python_cache_artifacts() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )

    tracked_cache_files = [
        line
        for line in result.stdout.splitlines()
        if "__pycache__/" in line or line.endswith(".pyc")
    ]

    assert tracked_cache_files == []
