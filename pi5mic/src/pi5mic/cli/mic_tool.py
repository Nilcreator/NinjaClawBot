"""Simple interactive menu for pi5mic."""

from __future__ import annotations

import click

from pi5mic.cli.doctor import doctor
from pi5mic.cli.install_cmd import install_whispercpp
from pi5mic.cli.run_cmd import run_cmd
from pi5mic.cli.setup_cmd import setup_cmd
from pi5mic.cli.status import status


@click.command("mic-tool")
@click.pass_context
def mic_tool(ctx: click.Context) -> None:
    """Open a simple first-run menu for common pi5mic tasks."""
    click.echo("pi5mic mic-tool")
    click.echo("----------------")

    while True:
        click.echo("\n1. Run setup wizard")
        click.echo("2. Register whisper.cpp")
        click.echo("3. Run doctor")
        click.echo("4. Show status")
        click.echo("5. Run one capture cycle")
        click.echo("6. Exit")

        choice = click.prompt(
            "Choose an action",
            type=click.Choice(["1", "2", "3", "4", "5", "6"]),
            default="1",
            show_choices=False,
        )

        if choice == "1":
            ctx.invoke(setup_cmd)
        elif choice == "2":
            ctx.invoke(install_whispercpp, command_override=None, model_path=None, save=True)
        elif choice == "3":
            ctx.invoke(doctor)
        elif choice == "4":
            ctx.invoke(status)
        elif choice == "5":
            ctx.invoke(run_cmd, once=True, audio_file=None, duration=None, keep_audio=False)
        else:
            click.echo("Leaving pi5mic mic-tool.")
            break
