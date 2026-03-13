"""Root workspace test harness for the NinjaClawBot monorepo."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

PYTHON_TEST_SUITES = [
    ("pi5buzzer", "pi5buzzer/tests", "pi5buzzer/pyproject.toml"),
    ("pi5servo", "pi5servo/tests", "pi5servo/pyproject.toml"),
    ("pi5disp", "pi5disp/tests", "pi5disp/pyproject.toml"),
    ("pi5vl53l0x", "pi5vl53l0x/tests", "pi5vl53l0x/pyproject.toml"),
    ("ninjaclawbot", "ninjaclawbot/tests", "ninjaclawbot/pyproject.toml"),
]


@pytest.mark.parametrize(("label", "tests_path", "config_path"), PYTHON_TEST_SUITES)
def test_package_pytest_suite(label: str, tests_path: str, config_path: str) -> None:
    """Run each package-local pytest suite with its own config."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            tests_path,
            "-c",
            config_path,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"{label} test suite failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
