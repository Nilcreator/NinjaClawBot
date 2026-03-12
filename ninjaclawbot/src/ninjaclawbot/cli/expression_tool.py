"""Interactive expression asset authoring for ninjaclawbot."""

from __future__ import annotations

import click

from ninjaclawbot.cli.common import create_executor, print_json
from ninjaclawbot.expressions.catalog import list_builtin_expressions


@click.command("expression-tool")
@click.pass_context
def expression_tool(ctx: click.Context) -> None:
    """Create, edit, preview, and delete named expression assets."""

    executor = create_executor(ctx.obj["root_dir"])
    store = executor.asset_store

    try:
        while True:
            click.echo("\nExpression Tool")
            click.echo("1. List saved expressions")
            click.echo("2. List built-in expressions")
            click.echo("3. Preview built-in expression")
            click.echo("4. Create expression asset")
            click.echo("5. Show saved expression")
            click.echo("6. Run saved expression")
            click.echo("7. Set idle expression")
            click.echo("8. Stop active expression")
            click.echo("9. Delete expression")
            click.echo("10. Exit")
            choice = click.prompt("Choose an option", type=str).strip()

            try:
                if choice == "1":
                    print_json({"expressions": store.list_assets("expressions")})
                elif choice == "2":
                    print_json({"builtins": list_builtin_expressions()})
                elif choice == "3":
                    builtin = click.prompt("Built-in expression name").strip()
                    payload = executor.runtime.perform_expression({"builtin": builtin})
                    print_json(payload)
                elif choice == "4":
                    name = click.prompt("Expression name").strip()
                    description = click.prompt(
                        "Description", default="", show_default=False
                    ).strip()
                    builtin = click.prompt(
                        "Built-in expression (blank for none)",
                        default="",
                        show_default=False,
                    ).strip()
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
                    sound_duration = click.prompt(
                        "Sound duration (seconds)", default=0.3, type=float
                    )
                    face_chain_raw = click.prompt(
                        "Face chain override (comma-separated, blank for default)",
                        default="",
                        show_default=False,
                    ).strip()
                    idle_reset = click.confirm(
                        "Return to idle after playing?",
                        default=True if builtin else False,
                    )

                    face_chain = []
                    if face_chain_raw:
                        face_chain = [
                            {"expression": step.strip(), "duration": 1.2}
                            for step in face_chain_raw.split(",")
                            if step.strip()
                        ]

                    path = store.save_expression(
                        {
                            "name": name,
                            "description": description,
                            "builtin": builtin,
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
                            "face_chain": face_chain,
                            "idle_reset": idle_reset,
                        }
                    )
                    click.echo(f"Saved expression: {path}")
                elif choice == "5":
                    name = click.prompt("Expression name").strip()
                    print_json(store.load_expression(name))
                elif choice == "6":
                    name = click.prompt("Expression name").strip()
                    result = executor.execute(
                        {"action": "perform_expression", "parameters": {"name": name}}
                    )
                    print_json(result.to_dict())
                elif choice == "7":
                    executor.runtime.set_idle_expression()
                    click.echo("Idle expression started.")
                elif choice == "8":
                    executor.runtime.stop_expression()
                    click.echo("Active expression stopped.")
                elif choice == "9":
                    name = click.prompt("Expression name").strip()
                    store.delete_expression(name)
                    click.echo(f"Deleted expression '{name}'.")
                elif choice == "10":
                    click.echo("Goodbye!")
                    return
                else:
                    click.echo("Invalid option.")
            except Exception as exc:  # pragma: no cover - interactive guard
                click.echo(f"Error: {exc}")
    finally:
        executor.runtime.close()
