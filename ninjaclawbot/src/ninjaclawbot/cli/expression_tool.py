"""Interactive expression asset authoring for ninjaclawbot."""

from __future__ import annotations

import click

from ninjaclawbot.cli.common import create_executor, print_json


@click.command("expression-tool")
@click.pass_context
def expression_tool(ctx: click.Context) -> None:
    """Create, edit, preview, and delete named expression assets."""

    executor = create_executor(ctx.obj["root_dir"])
    store = executor.asset_store

    try:
        while True:
            click.echo("\nExpression Tool")
            click.echo("1. List expressions")
            click.echo("2. Create expression")
            click.echo("3. Show expression")
            click.echo("4. Run expression")
            click.echo("5. Delete expression")
            click.echo("6. Exit")
            choice = click.prompt("Choose an option", type=str).strip()

            if choice == "1":
                print_json({"expressions": store.list_assets("expressions")})
            elif choice == "2":
                name = click.prompt("Expression name").strip()
                description = click.prompt("Description", default="", show_default=False).strip()
                text = click.prompt("Display text", default="", show_default=False).strip()
                scroll = click.confirm("Scroll text?", default=False)
                duration = click.prompt("Display duration (seconds)", default=3.0, type=float)
                language = click.prompt("Language", default="en").strip()
                font_size = click.prompt("Font size", default=32, type=int)
                emotion = click.prompt("Sound emotion", default="", show_default=False).strip()
                frequency_raw = click.prompt(
                    "Tone frequency (Hz, blank for none)", default="", show_default=False
                ).strip()
                frequency = int(frequency_raw) if frequency_raw else None
                sound_duration = click.prompt("Sound duration (seconds)", default=0.3, type=float)

                path = store.save_expression(
                    {
                        "name": name,
                        "description": description,
                        "display": {
                            "text": text,
                            "scroll": scroll,
                            "duration": duration,
                            "language": language,
                            "font_size": font_size,
                        },
                        "sound": {
                            "emotion": emotion,
                            "frequency": frequency,
                            "duration": sound_duration,
                        },
                    }
                )
                click.echo(f"Saved expression: {path}")
            elif choice == "3":
                name = click.prompt("Expression name").strip()
                print_json(store.load_expression(name))
            elif choice == "4":
                name = click.prompt("Expression name").strip()
                result = executor.execute(
                    {"action": "perform_expression", "parameters": {"name": name}}
                )
                print_json(result.to_dict())
            elif choice == "5":
                name = click.prompt("Expression name").strip()
                store.delete_expression(name)
                click.echo(f"Deleted expression '{name}'.")
            elif choice == "6":
                click.echo("Goodbye!")
                return
            else:
                click.echo("Invalid option.")
    finally:
        executor.runtime.close()
