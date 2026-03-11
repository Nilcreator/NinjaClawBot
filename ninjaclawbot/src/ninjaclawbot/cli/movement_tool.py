"""Interactive movement asset authoring for ninjaclawbot."""

from __future__ import annotations

import copy
import time

import click

from ninjaclawbot.cli.common import (
    create_executor,
    extract_movement_data,
    parse_movement_command,
    print_json,
)
from ninjaclawbot.errors import ExecutionError


def _available_endpoints(executor) -> list[str]:
    endpoints = executor.runtime.servo.configured_endpoints()
    if not endpoints:
        raise click.ClickException(
            "No configured servo endpoints were found. Run `uv run pi5servo calib <endpoint>` "
            "or `uv run pi5servo servo-tool` from the project root first."
        )
    return endpoints


def _current_angles(executor, endpoints: list[str]) -> dict[str, float]:
    current = executor.runtime.servo.current_angles()
    return {endpoint: float(current.get(endpoint, 0.0)) for endpoint in endpoints}


def _complete_moves(
    endpoints: list[str],
    parsed_moves: dict[str, dict[str, float | str | None]],
    base_angles: dict[str, float],
) -> tuple[dict[str, float], dict[str, str]]:
    angles, per_servo_speeds = extract_movement_data(parsed_moves)
    completed = dict(base_angles)
    completed.update(angles)
    return {
        endpoint: float(completed.get(endpoint, 0.0)) for endpoint in endpoints
    }, per_servo_speeds


def _preview_sequence(executor, sequence: list[dict]) -> None:
    click.echo("Previewing sequence...")
    executor.runtime.servo.center_all()
    time.sleep(0.5)
    for index, step in enumerate(sequence, start=1):
        click.echo(f"  - Step {index}: {step['moves']}")
        completed = executor.runtime.move_servos(
            step["moves"],
            speed_mode=step["speed"],
            per_servo_speeds=step.get("per_servo_speeds"),
            force=True,
            easing="linear",
        )
        if not completed:
            raise ExecutionError("Movement preview was aborted.")
        pause_after_ms = int(step.get("pause_after_ms", 0))
        if pause_after_ms > 0:
            time.sleep(pause_after_ms / 1000)
    click.echo("Preview finished.")
    time.sleep(0.5)
    executor.runtime.servo.center_all()


def _record_new_movement(executor, store) -> None:
    endpoints = _available_endpoints(executor)
    click.echo("\n--- Record New Movement ---")
    click.echo(
        "Commands: [S|M|F]_ENDPOINT:ANGLE/ENDPOINT:ANGLE with optional per-servo S/M/F suffix."
    )
    click.echo("Examples: F_gpio12:45/gpio13:-30  or  12:45S/13:-30F")
    click.echo(f"Available endpoints: {', '.join(endpoints)}")

    click.echo("\nSetting all servos to center position to begin...")
    executor.runtime.servo.center_all()
    sequence: list[dict] = []
    previous_angles = _current_angles(executor, endpoints)

    while True:
        command_str = click.prompt("Enter servo movement command", type=str).strip()
        global_speed, parsed_moves = parse_movement_command(command_str)
        completed_moves, per_servo_speeds = _complete_moves(
            endpoints, parsed_moves, previous_angles
        )

        click.echo(f"Executing: {completed_moves} with global speed {global_speed}")
        completed = executor.runtime.move_servos(
            completed_moves,
            speed_mode=global_speed,
            per_servo_speeds=per_servo_speeds,
            force=True,
        )
        if not completed:
            raise click.ClickException("Movement was aborted before completion.")

        step = {
            "speed": global_speed,
            "moves": completed_moves,
            "per_servo_speeds": per_servo_speeds,
            "pause_after_ms": 0,
        }
        choice = click.prompt(
            "1. Confirm & Next | 2. Reset | 3. Finish Recording",
            type=str,
        ).strip()
        if choice == "1":
            sequence.append(step)
            previous_angles = _current_angles(executor, endpoints)
            click.echo("Movement step confirmed.")
        elif choice == "2":
            click.echo("Resetting to previous position...")
            executor.runtime.move_servos(previous_angles, speed_mode="F", force=True)
        elif choice == "3":
            sequence.append(step)
            movement_name = click.prompt("Enter a name for this movement", type=str).strip()
            description = click.prompt("Description", default="", show_default=False).strip()
            path = store.save_movement(
                {"name": movement_name, "description": description, "steps": sequence}
            )
            click.echo(f"Saved movement: {path}")
            executor.runtime.servo.center_all()
            return
        else:
            click.echo("Invalid option.")


def _edit_sequence_menu(executor, movement: dict) -> None:
    endpoints = _available_endpoints(executor)
    temp_sequence = copy.deepcopy(movement["steps"])

    while True:
        click.echo("\n--- Editing Sequence ---")
        for index, step in enumerate(temp_sequence, start=1):
            click.echo(
                f"Step {index}: Speed={step['speed']}, Moves={step['moves']}, "
                f"Per-servo={step.get('per_servo_speeds', {})}"
            )
        click.echo(
            "\nOptions: 1. Edit Step | 2. Insert Step | 3. Delete Step | "
            "4. Preview | 5. Save & Exit | 6. Abort"
        )
        choice = click.prompt("Select an option", type=str).strip()

        try:
            if choice == "1":
                step_index = int(click.prompt("Enter step number to edit", type=int)) - 1
                if not 0 <= step_index < len(temp_sequence):
                    raise click.ClickException("Invalid step number.")
                command_str = click.prompt("Enter new movement command", type=str).strip()
                speed, parsed_moves = parse_movement_command(command_str)
                base_angles = (
                    temp_sequence[step_index - 1]["moves"]
                    if step_index > 0
                    else {endpoint: 0.0 for endpoint in endpoints}
                )
                completed_moves, per_servo_speeds = _complete_moves(
                    endpoints, parsed_moves, base_angles
                )
                temp_sequence[step_index] = {
                    "speed": speed,
                    "moves": completed_moves,
                    "per_servo_speeds": per_servo_speeds,
                    "pause_after_ms": int(temp_sequence[step_index].get("pause_after_ms", 0)),
                }
                click.echo("Step updated.")
            elif choice == "2":
                position = (
                    int(
                        click.prompt(
                            f"Enter position to insert new step (1 to {len(temp_sequence) + 1})",
                            type=int,
                        )
                    )
                    - 1
                )
                if not 0 <= position <= len(temp_sequence):
                    raise click.ClickException("Invalid position.")
                command_str = click.prompt("Enter movement command for the new step", type=str)
                speed, parsed_moves = parse_movement_command(command_str)
                base_angles = (
                    temp_sequence[position - 1]["moves"]
                    if position > 0
                    else {endpoint: 0.0 for endpoint in endpoints}
                )
                completed_moves, per_servo_speeds = _complete_moves(
                    endpoints, parsed_moves, base_angles
                )
                temp_sequence.insert(
                    position,
                    {
                        "speed": speed,
                        "moves": completed_moves,
                        "per_servo_speeds": per_servo_speeds,
                        "pause_after_ms": 0,
                    },
                )
                click.echo("Step inserted.")
            elif choice == "3":
                step_index = int(click.prompt("Enter step number to delete", type=int)) - 1
                if not 0 <= step_index < len(temp_sequence):
                    raise click.ClickException("Invalid step number.")
                if click.confirm(f"Delete Step {step_index + 1}?", default=False):
                    del temp_sequence[step_index]
                    click.echo("Step deleted.")
            elif choice == "4":
                _preview_sequence(executor, temp_sequence)
            elif choice == "5":
                updated = dict(movement)
                updated["steps"] = temp_sequence
                path = executor.asset_store.save_movement(updated)
                click.echo(f"Saved movement: {path}")
                return
            elif choice == "6":
                click.echo("Aborting without saving.")
                return
            else:
                click.echo("Invalid option.")
        except click.ClickException as exc:
            click.echo(f"Error: {exc.message}")


@click.command("movement-tool")
@click.pass_context
def movement_tool(ctx: click.Context) -> None:
    """Create, edit, preview, and delete named movement assets."""

    executor = create_executor(ctx.obj["root_dir"])
    store = executor.asset_store

    try:
        while True:
            click.echo("\nMovement Tool")
            click.echo("1. List movements")
            click.echo("2. Create movement")
            click.echo("3. Edit movement")
            click.echo("4. Show movement")
            click.echo("5. Run movement")
            click.echo("6. Delete movement")
            click.echo("7. Exit")
            choice = click.prompt("Choose an option", type=str).strip()

            if choice == "1":
                print_json({"movements": store.list_assets("movements")})
            elif choice == "2":
                _record_new_movement(executor, store)
            elif choice == "3":
                name = click.prompt("Movement name").strip()
                _edit_sequence_menu(executor, store.load_movement(name))
            elif choice == "4":
                name = click.prompt("Movement name").strip()
                print_json(store.load_movement(name))
            elif choice == "5":
                name = click.prompt("Movement name").strip()
                result = executor.execute(
                    {"action": "perform_movement", "parameters": {"name": name}}
                )
                print_json(result.to_dict())
            elif choice == "6":
                name = click.prompt("Movement name").strip()
                store.delete_movement(name)
                click.echo(f"Deleted movement '{name}'.")
            elif choice == "7":
                click.echo("Goodbye!")
                return
            else:
                click.echo("Invalid option.")
    finally:
        executor.runtime.close()
