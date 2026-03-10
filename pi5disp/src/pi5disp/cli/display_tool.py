"""Interactive display tool — Menu-driven display testing and configuration."""

from __future__ import annotations

import click


@click.command("display-tool")
def display_tool() -> None:
    """Launch the interactive display tool."""
    click.echo()
    click.echo(
        click.style("╔══════════════════════════════════════════════════════════════╗", fg="cyan")
    )
    click.echo(
        click.style("║               pi5disp Interactive Tool                      ║", fg="cyan")
    )
    click.echo(
        click.style("╠══════════════════════════════════════════════════════════════╣", fg="cyan")
    )
    click.echo(
        click.style("║  1. Init          - Set up display module & pin config      ║", fg="cyan")
    )
    click.echo(
        click.style("║  2. Show Image    - Display an image file                   ║", fg="cyan")
    )
    click.echo(
        click.style("║  3. Show Text     - Display text (with optional scroll)     ║", fg="cyan")
    )
    click.echo(
        click.style("║  4. Ball Demo     - Run bouncing ball animation             ║", fg="cyan")
    )
    click.echo(
        click.style("║  5. Brightness    - Adjust backlight brightness             ║", fg="cyan")
    )
    click.echo(
        click.style("║  6. Info          - Show driver state & config              ║", fg="cyan")
    )
    click.echo(
        click.style("║  7. Clear         - Clear the display                       ║", fg="cyan")
    )
    click.echo(
        click.style("║  8. Config        - Export/import configuration             ║", fg="cyan")
    )
    click.echo(
        click.style("║  9. Exit                                                    ║", fg="cyan")
    )
    click.echo(
        click.style("╚══════════════════════════════════════════════════════════════╝", fg="cyan")
    )

    while True:
        try:
            choice = click.prompt("\nSelect an option", type=int, default=9)
        except (EOFError, KeyboardInterrupt):
            click.echo("\nExiting.")
            break

        if choice == 1:
            _do_init()
        elif choice == 2:
            _do_image()
        elif choice == 3:
            _do_text()
        elif choice == 4:
            _do_demo()
        elif choice == 5:
            _do_brightness()
        elif choice == 6:
            _do_info()
        elif choice == 7:
            _do_clear()
        elif choice == 8:
            _do_config()
        elif choice == 9:
            click.echo("Goodbye!")
            break
        else:
            click.echo("Invalid choice. Please enter 1-9.")


def _do_init() -> None:
    """Run the init wizard."""
    from pi5disp.config.config_manager import ConfigManager

    config_manager = ConfigManager()
    config_manager.init_config(interactive=True)


def _do_image() -> None:
    """Prompt for path and display image."""
    from pi5disp.cli.image_cmd import image

    path = click.prompt("Image path", type=str)
    ctx = click.Context(image)
    ctx.invoke(image, path=path, rotation=None)


def _do_text() -> None:
    """Prompt for text and display it."""
    from pi5disp.cli.text_cmd import text

    text_content = click.prompt("Text to display", type=str)
    scroll = click.confirm("Enable scrolling?", default=False)
    lang = click.prompt("Language (en/ja/zh-tw)", type=str, default="en")
    ctx = click.Context(text)
    ctx.invoke(
        text,
        text_content=text_content,
        scroll=scroll,
        lang=lang,
        size=32,
        color="255,255,255",
        bg="0,0,0",
        speed=2.0,
        duration=15.0,
    )


def _do_demo() -> None:
    """Run ball demo with prompts."""
    from pi5disp.cli.demo_cmd import demo

    num_balls = click.prompt("Number of balls", type=int, default=3)
    duration = click.prompt("Duration (seconds)", type=float, default=10.0)
    ctx = click.Context(demo)
    ctx.invoke(demo, num_balls=num_balls, fps=30, duration=duration)


def _do_brightness() -> None:
    """Prompt for brightness and apply it."""
    from pi5disp.__main__ import brightness

    percent = click.prompt("Brightness (0-100%)", type=int, default=100)
    ctx = click.Context(brightness)
    ctx.invoke(brightness, percent=percent)


def _do_info() -> None:
    """Show display info."""
    from pi5disp.cli.info_cmd import info

    ctx = click.Context(info)
    ctx.invoke(info)


def _do_clear() -> None:
    """Clear the display."""
    from pi5disp.__main__ import clear

    ctx = click.Context(clear)
    ctx.invoke(clear)


def _do_config() -> None:
    """Config management submenu."""
    click.echo("\n  1. Show config")
    click.echo("  2. Export config")
    click.echo("  3. Import config")
    choice = click.prompt("  Choice", type=int, default=1)

    from pi5disp.__main__ import config_export, config_import, show

    if choice == 1:
        ctx = click.Context(show)
        ctx.invoke(show)
    elif choice == 2:
        path = click.prompt("Export path", type=str)
        ctx = click.Context(config_export)
        ctx.invoke(config_export, path=path)
    elif choice == 3:
        path = click.prompt("Import path", type=str)
        ctx = click.Context(config_import)
        ctx.invoke(config_import, path=path)
