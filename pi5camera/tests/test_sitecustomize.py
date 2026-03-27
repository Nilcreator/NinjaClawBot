from __future__ import annotations

import sys

import sitecustomize


def test_matches_target_detects_supported_modules() -> None:
    assert sitecustomize._matches_target("libcamera") is True
    assert sitecustomize._matches_target("libcamera._libcamera") is True
    assert sitecustomize._matches_target("PIL") is False


def test_ensure_rpi_system_packages_visible_installs_targeted_finder(monkeypatch) -> None:
    monkeypatch.setattr(sitecustomize.platform, "system", lambda: "Linux")
    monkeypatch.setattr(sitecustomize, "_is_virtual_environment", lambda: True)
    monkeypatch.setattr(
        sitecustomize,
        "_get_system_site_packages",
        lambda system_python=sitecustomize.SYSTEM_PYTHON: ["/usr/lib/python3/dist-packages"],
    )
    sys.meta_path[:] = [
        finder
        for finder in sys.meta_path
        if getattr(finder, "marker", None) != sitecustomize.SYSTEM_FINDER_MARKER
    ]

    sitecustomize.ensure_rpi_system_packages_visible()

    assert any(
        getattr(finder, "marker", None) == sitecustomize.SYSTEM_FINDER_MARKER
        for finder in sys.meta_path
    )
    sys.meta_path[:] = [
        finder
        for finder in sys.meta_path
        if getattr(finder, "marker", None) != sitecustomize.SYSTEM_FINDER_MARKER
    ]


def test_system_finder_ignores_unrelated_modules() -> None:
    finder = sitecustomize._Pi5CameraSystemFinder(["/usr/lib/python3/dist-packages"])
    assert finder.find_spec("PIL") is None
