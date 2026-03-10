"""Interactive servo control tool."""

from __future__ import annotations

import json
import time

import click

from ..config import ConfigManager
from ..core import Servo, ServoCalibration, ServoGroup
from ._common import backend_options, close_runtime_handle, create_group_from_config
from .calib import CalibApp

try:
    from blessed import Terminal

    HAS_BLESSED = True
except ImportError:
    HAS_BLESSED = False


@click.command("servo-tool")
@click.option(
    "-c",
    "--config",
    "config_path",
    default="servo.json",
    help="Path to calibration config file.",
)
@backend_options
def servo_tool(
    config_path: str,
    backend_name: str | None,
    chip: int | None,
    frequency_hz: int | None,
    address: str | None,
    pin_channel_map: str | None,
    channel_map: str | None,
) -> None:
    """Interactive servo control and configuration tool."""
    if not HAS_BLESSED:
        click.echo("❌ 'blessed' library required for interactive mode.")
        click.echo("   Install with: uv add blessed")
        return

    term = Terminal()
    manager = ConfigManager(config_path)
    manager.load()
    known_pins = sorted(manager.get_all_calibrations().keys()) or [12, 13]

    persistent_group = None
    runtime = None
    resolved_backend = None
    backend_kwargs = None

    def reload_manager() -> None:
        manager.load()

    def build_temp_group(pins: list[int]) -> ServoGroup:
        calibrations = {pin: manager.get_calibration(pin) for pin in pins}
        return ServoGroup(
            runtime,
            pins=pins,
            calibrations=calibrations,
            backend=persistent_group.backend if persistent_group is not None else None,
        )

    def build_temp_servo(pin: int) -> Servo:
        return Servo(
            runtime,
            pin,
            manager.get_calibration(pin),
            backend=persistent_group.backend if persistent_group is not None else None,
        )

    try:
        persistent_group, manager, runtime, resolved_backend, backend_kwargs = (
            create_group_from_config(
                pins=known_pins,
                config_path=config_path,
                backend_name=backend_name,
                chip=chip,
                frequency_hz=frequency_hz,
                address=address,
                pin_channel_map=pin_channel_map,
                channel_map=channel_map,
            )
        )

        if known_pins:
            persistent_group.center_all()
            time.sleep(0.1)
            click.echo(term.green(f"✓ All servos centered (0°): GPIO {known_pins}"))

        def show_menu() -> None:
            click.echo(term.clear())
            click.echo(term.bold("╔" + "═" * 58 + "╗"))
            click.echo(
                term.bold("║")
                + term.cyan("           pi5servo Interactive Tool")
                + " " * 20
                + term.bold("║")
            )
            click.echo(term.bold("╠" + "═" * 58 + "╣"))
            click.echo(
                term.bold("║")
                + "  1. Quick Move    - Enter commands like '12:30/13:M'    "
                + term.bold("║")
            )
            click.echo(
                term.bold("║")
                + "  2. Single Move   - Move one servo to angle             "
                + term.bold("║")
            )
            click.echo(
                term.bold("║")
                + "  3. Calibrate     - Launch calibration TUI              "
                + term.bold("║")
            )
            click.echo(
                term.bold("║")
                + "  4. Set Speed     - Adjust servo speed limit            "
                + term.bold("║")
            )
            click.echo(
                term.bold("║")
                + "  5. Status        - Show backend and servo configs      "
                + term.bold("║")
            )
            click.echo(
                term.bold("║")
                + "  6. Config        - Show/export/import config           "
                + term.bold("║")
            )
            click.echo(
                term.bold("║")
                + "  q. Exit                                                "
                + term.bold("║")
            )
            click.echo(term.bold("╚" + "═" * 58 + "╝"))
            click.echo()

        def quick_move() -> None:
            click.echo("\n" + term.cyan("=== Quick Move Mode ==="))
            click.echo("Enter commands like 'F_12:45/13:-30'. Type 'q' to return.\n")

            from ..parser import parse_command

            while True:
                cmd_str = input("> ").strip()
                if cmd_str.lower() in ("q", "b", "quit", "back"):
                    break
                if not cmd_str:
                    continue

                try:
                    parsed = parse_command(cmd_str)
                    pins = sorted({target.pin for target in parsed.targets})
                    if set(pins).issubset(set(persistent_group.pins)):
                        group = persistent_group
                        owns_group = False
                    else:
                        group = build_temp_group(pins)
                        owns_group = True

                    success = group.execute_command(cmd_str)
                    click.echo(term.green("✓ Done") if success else term.red("✗ Aborted"))

                    if owns_group:
                        group.close()
                except ValueError as exc:
                    click.echo(term.red(f"✗ Error: {exc}"))

        def single_move() -> None:
            click.echo("\n" + term.cyan("=== Single Move Mode ==="))
            click.echo("Enter GPIO pin:")
            try:
                pin = int(input("> ").strip())
            except ValueError:
                click.echo(term.red("Invalid pin"))
                input("\nPress Enter to continue...")
                return

            click.echo(
                f"Moving GPIO{pin}. Enter angle or 'min'/'center'/'max'. Type 'q' to return.\n"
            )
            servo = build_temp_servo(pin)

            try:
                while True:
                    angle_str = input("> ").strip().lower()
                    if angle_str in ("q", "b", "quit", "back"):
                        break
                    if not angle_str:
                        continue

                    cal = manager.get_calibration(pin)
                    if angle_str == "min":
                        angle = cal.angle_min
                    elif angle_str == "center":
                        angle = cal.angle_center
                    elif angle_str == "max":
                        angle = cal.angle_max
                    else:
                        try:
                            angle = float(angle_str)
                        except ValueError:
                            click.echo(term.red("Invalid angle"))
                            continue

                    servo.set_angle(angle)
                    click.echo(term.green(f"✓ GPIO{pin} → {angle}°"))
            finally:
                servo.close()

        def calibrate_servo() -> None:
            click.echo("\n" + term.yellow("Enter GPIO pin to calibrate:"))
            try:
                pin = int(input("> ").strip())
            except ValueError:
                click.echo(term.red("Invalid pin"))
                input("\nPress Enter to continue...")
                return

            servo = build_temp_servo(pin)
            app = CalibApp(servo, pin, config_path, manager)
            try:
                app.main()
            finally:
                app.end()
            reload_manager()
            click.echo(term.green("✓ Config reloaded"))

        def set_speed() -> None:
            click.echo("\n" + term.cyan("=== Set Servo Speed Limit ==="))
            configs = manager.get_all_calibrations()
            if configs:
                click.echo("\nCurrent speeds:")
                for pin_num, cal in sorted(configs.items()):
                    click.echo(f"  GPIO{pin_num}: {cal.speed}%")

            click.echo("\n" + term.yellow("Enter GPIO pin:"))
            try:
                pin = int(input("> ").strip())
            except ValueError:
                click.echo(term.red("Invalid pin"))
                input("\nPress Enter to continue...")
                return

            cal = manager.get_calibration(pin)
            click.echo(f"Current speed for GPIO{pin}: {cal.speed}%")
            click.echo(term.yellow("Enter new speed (0-100):"))
            try:
                new_speed = int(input("> ").strip())
            except ValueError:
                click.echo(term.red("Invalid speed"))
                input("\nPress Enter to continue...")
                return

            if not 0 <= new_speed <= 100:
                click.echo(term.red("Speed must be 0-100"))
                input("\nPress Enter to continue...")
                return

            manager.set_calibration(
                pin,
                ServoCalibration(
                    pulse_min=cal.pulse_min,
                    pulse_max=cal.pulse_max,
                    pulse_center=cal.pulse_center,
                    angle_min=cal.angle_min,
                    angle_max=cal.angle_max,
                    angle_center=cal.angle_center,
                    speed=new_speed,
                ),
            )
            manager.save()
            reload_manager()
            click.echo(term.green(f"✓ Speed for GPIO{pin} set to {new_speed}%"))
            input("\nPress Enter to continue...")

        def show_status() -> None:
            click.echo("\n" + term.cyan("=== Servo Status ==="))
            click.echo(f"Backend: {resolved_backend}")
            click.echo(f"Backend kwargs: {backend_kwargs or '{}'}")

            configs = manager.get_all_calibrations()
            if not configs:
                click.echo("No servos configured. Run calibration first.")
            else:
                for pin_num, cal in sorted(configs.items()):
                    click.echo(
                        f"  GPIO{pin_num}: pulse=[{cal.pulse_min}, {cal.pulse_center}, {cal.pulse_max}] speed={cal.speed}%"
                    )
            input("\nPress Enter to continue...")

        def config_menu() -> None:
            click.echo("\n" + term.cyan("=== Config Management ==="))
            click.echo("  1. Show current config")
            click.echo("  2. Export to file")
            click.echo("  3. Import from file")
            click.echo("  b. Back")

            choice = input("\nChoice: ").strip().lower()
            if choice == "1":
                click.echo("\n" + json.dumps(manager._to_dict(), indent=2))
            elif choice == "2":
                click.echo(term.yellow("Enter export path:"))
                path = input("> ").strip()
                if path:
                    manager.save_to(path)
                    click.echo(term.green(f"✓ Exported to {path}"))
            elif choice == "3":
                click.echo(term.yellow("Enter import path:"))
                path = input("> ").strip()
                if path:
                    manager.load_from(path)
                    click.echo(term.green(f"✓ Imported from {path}"))
                    reload_manager()
            input("\nPress Enter to continue...")

        running = True
        while running:
            show_menu()
            choice = input("Choice: ").strip().lower()

            if choice == "1":
                quick_move()
            elif choice == "2":
                single_move()
            elif choice == "3":
                calibrate_servo()
            elif choice == "4":
                set_speed()
            elif choice == "5":
                show_status()
            elif choice == "6":
                config_menu()
            elif choice == "q":
                running = False
            else:
                click.echo("Invalid choice")
                input("\nPress Enter to continue...")

    except Exception as exc:
        click.echo(f"❌ Error: {exc}")
        import traceback

        traceback.print_exc()
    finally:
        try:
            if persistent_group is not None and persistent_group.pins:
                persistent_group.move_all_sync(
                    [0.0] * len(persistent_group.pins),
                    speed_mode="M",
                    force=True,
                )
                click.echo(term.green("✓ All servos centered (0°) on exit"))
                persistent_group.off()
                persistent_group.close()
        except Exception:
            pass

        close_runtime_handle(runtime)
        click.echo("\nGoodbye!")
