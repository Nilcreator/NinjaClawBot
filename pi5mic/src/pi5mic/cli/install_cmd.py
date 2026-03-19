"""Install and registration helpers for pi5mic."""

from __future__ import annotations

from pathlib import Path

import click

from pi5mic.errors import ConfigError, STTError
from pi5mic.install.whisper_cpp import (
    DEFAULT_MODEL_FILE,
    find_whisper_cpp_command,
    resolve_model_path,
)

from ._common import load_manager


@click.group("install")
def install_cmd() -> None:
    """Install or register local backend assets."""


@install_cmd.command("whispercpp")
@click.option(
    "--command",
    "command_override",
    type=click.Path(path_type=Path),
    default=None,
    help="Explicit path to whisper-cli.",
)
@click.option(
    "--model-path",
    type=click.Path(path_type=Path),
    default=None,
    help="Explicit path to the multilingual ggml-base.bin model.",
)
@click.option("--save/--no-save", default=True, help="Save discovered paths into mic.json.")
@click.pass_context
def install_whispercpp(
    ctx: click.Context,
    command_override: Path | None,
    model_path: Path | None,
    save: bool,
) -> None:
    """Register an existing whisper.cpp install for pi5mic."""
    try:
        manager = load_manager(ctx.obj.get("config_file"))
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    config = manager.config
    whisper_config = config["stt"]["whisper_cpp"]
    command_candidate = command_override or whisper_config.get("command")
    resolved_command = find_whisper_cpp_command(command_candidate)
    if resolved_command is None:
        raise click.ClickException(
            "Could not find 'whisper-cli'.\n"
            "Suggested next steps:\n"
            "  git clone https://github.com/ggml-org/whisper.cpp.git\n"
            "  cd whisper.cpp\n"
            "  sh ./models/download-ggml-model.sh base\n"
            "  cmake -B build\n"
            "  cmake --build build -j --config Release\n"
        )

    model_candidate = model_path or whisper_config.get("model_path")
    if not model_candidate:
        default_model = Path.home() / ".local" / "share" / "pi5mic" / "models" / DEFAULT_MODEL_FILE
        raise click.ClickException(
            "No whisper.cpp model path is configured.\n"
            f"Suggested model location: {default_model}\n"
            "Download with whisper.cpp's official helper:\n"
            "  sh ./models/download-ggml-model.sh base\n"
        )

    try:
        resolved_model = resolve_model_path(model_candidate)
    except STTError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"whisper.cpp command: {resolved_command}")
    click.echo(f"whisper.cpp model:   {resolved_model}")

    if save:
        whisper_config["command"] = str(resolved_command)
        whisper_config["model_path"] = str(resolved_model)
        config["stt"]["selected"] = "whisper_cpp"
        manager.replace(config)
        manager.save()
        click.echo(f"Saved whisper.cpp settings to {manager.path}")
