"""Interactive movement asset authoring for ninjaclawbot."""

from __future__ import annotations

import click

from ninjaclawbot.cli.common import create_executor, parse_step_command, print_json


@click.command("movement-tool")
@click.pass_context
def movement_tool(ctx: click.Context) -> None:
    """Create, edit, preview, and delete named movement assets."""

    executor = create_executor(ctx.obj["root_dir"])
    store = executor.asset_store

    while True:
        click.echo("\nMovement Tool")
        click.echo("1. List movements")
        click.echo("2. Create movement")
        click.echo("3. Show movement")
        click.echo("4. Run movement")
        click.echo("5. Delete movement")
        click.echo("6. Exit")
        choice = click.prompt("Choose an option", type=str).strip()

        if choice == "1":
            print_json({"movements": store.list_assets("movements")})
        elif choice == "2":
            name = click.prompt("Movement name").strip()
            description = click.prompt("Description", default="", show_default=False).strip()
            steps = []
            while True:
                command = click.prompt(
                    "Enter movement command ([S|M|F]_endpoint:angle/...)"
                ).strip()
                speed_mode, targets = parse_step_command(command)
                pause_after_ms = click.prompt("Pause after step (ms)", default=0, type=int)
                steps.append(
                    {
                        "targets": targets,
                        "speed_mode": speed_mode,
                        "pause_after_ms": pause_after_ms,
                    }
                )
                if not click.confirm("Add another step?", default=False):
                    break
            path = store.save_movement({"name": name, "description": description, "steps": steps})
            click.echo(f"Saved movement: {path}")
        elif choice == "3":
            name = click.prompt("Movement name").strip()
            print_json(store.load_movement(name))
        elif choice == "4":
            name = click.prompt("Movement name").strip()
            result = executor.execute({"action": "perform_movement", "parameters": {"name": name}})
            print_json(result.to_dict())
        elif choice == "5":
            name = click.prompt("Movement name").strip()
            store.delete_movement(name)
            click.echo(f"Deleted movement '{name}'.")
        elif choice == "6":
            executor.runtime.close()
            click.echo("Goodbye!")
            return
        else:
            click.echo("Invalid option.")
