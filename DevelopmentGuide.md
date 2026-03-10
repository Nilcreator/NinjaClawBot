# NinjaClawBot Development Guide

## Scope

This guide records the current developer workflow for the new standalone Pi 5 driver libraries:

- `pi5buzzer`
- `pi5servo`
- `pi5disp`
- `pi5vl53l0x`

The detailed migration and backend strategy lives in [developmentPlan.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/developmentPlan.md).

## Agentic Workflow

The source of truth for agent-led implementation work is:

- [.agents/skills/ninjaclawbot-implementation/SKILL.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/.agents/skills/ninjaclawbot-implementation/SKILL.md)

That skill requires the following workflow:

1. Audit the legacy `pi0*` driver before planning.
2. Plan one `pi5*` library migration phase at a time.
3. Wait for user approval before coding.
4. Keep each `pi5*` library standalone-first and preserve optional future integration hooks.
5. Pass the quality gate before advancing to the next phase.
6. Produce a manual Raspberry Pi 5 validation checklist after each migrated library.
7. Update developer documentation and the development log before closing the task.

## Required Files To Review During Driver Work

Always review:

- [developmentPlan.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/developmentPlan.md)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

For the selected legacy library, inspect:

- `NinjaRobotV5_bak/pi0buzzer`
- `NinjaRobotV5_bak/pi0servo`
- `NinjaRobotV5_bak/pi0disp`
- `NinjaRobotV5_bak/pi0vl53l0x`

At minimum inspect:

- `pyproject.toml`
- `README.md`
- `src/<package>/__init__.py`
- `src/<package>/__main__.py`
- `src/<package>/driver.py` if present
- core modules
- config manager
- CLI modules
- tests

## Quality Checks

Default quality gate for each implementation phase:

```bash
python -m compileall .
ruff check .
ruff format --check .
pytest -q
```

If the package already uses typing checks:

```bash
mypy .
```

Preferred practice:

- run package-local checks while migrating one library
- run broader repo checks only if shared files changed

## pi5buzzer Migration Notes

Implemented package:

- [pi5buzzer](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer)

Legacy source audited for parity:

- [NinjaRobotV5_bak/pi0buzzer](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/NinjaRobotV5_bak/pi0buzzer)

Required public compatibility surface:

- `pi5buzzer.Buzzer`
- `pi5buzzer.MusicBuzzer`
- `pi5buzzer.driver.Buzzer`
- `pi5buzzer.driver.MusicBuzzer`
- CLI commands in [__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/__main__.py): `init`, `beep`, `play`, `info`, `config`, `buzzer-tool`
- config manager in [config_manager.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/config/config_manager.py) keeping `buzzer.json` compatibility

Backend rule:

- use the backend factory in [driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/core/driver.py)
- default runtime is an `RPi.GPIO` compatible backend intended for `rpi-lgpio` on Raspberry Pi 5
- keep high-level queueing, frequency clamping, volume semantics, and music helpers independent from the GPIO transport

Phase 1 quality gate result:

- `python -m compileall .`
- `ruff check .`
- `ruff format --check .`
- `pytest -q`
- current result for [pi5buzzer](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer): `65 passed`

Phase 1 Raspberry Pi 5 validation checklist:

- safe smoke tests: install `rpi-lgpio`, run `pi5buzzer --help`, `pi5buzzer init 17`, and verify `buzzer.json` is created
- device communication tests: run `pi5buzzer info --health-check` and confirm the backend can claim the configured GPIO pin
- actuator tests: run `pi5buzzer beep 440 0.3`, `pi5buzzer play happy`, and a short Python `play_song()` sequence
- power-risk tests: verify `off()` and CLI exit leave the buzzer silent with no stuck PWM output
- expected outcome: short tones and queued playback are audible and stable on Raspberry Pi 5
- rollback: uninstall `pi5buzzer`, remove the created `buzzer.json`, and disconnect the buzzer from the GPIO pin

Phase 1 installation troubleshooting:

- if `uv sync --extra pi --extra dev` fails while building `lgpio`, check the Python version used by `uv`
- `lgpio 0.2.2.0` currently ships Linux ARM wheels for CPython 3.9 through 3.12, but not 3.13
- `uv` prefers managed Python versions, so an unmanaged install can drift to 3.13 and trigger a source build that needs `swig`
- keep [pi5buzzer/.python-version](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/.python-version) pinned to `3.11`
- if a broken `.venv` already exists, remove it and rerun `uv sync --extra pi --extra dev`
- manual fallback only: install `swig`, `python3-dev`, and `build-essential`, then retry the sync

Phase 1 shutdown regression note:

- `rpi-lgpio` PWM objects call `stop()` again during object destruction
- the `pi5buzzer` backend must release PWM objects before `GPIO.cleanup()` closes the chip handle
- expected result after the fix: `uv run pi5buzzer buzzer-tool`, then `9. Exit`, returns without a cleanup traceback

## pi5vl53l0x Migration Notes

Implemented package:

- [pi5vl53l0x](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x)

Legacy source audited for parity:

- [NinjaRobotV5_bak/pi0vl53l0x](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/NinjaRobotV5_bak/pi0vl53l0x)

Required public compatibility surface:

- `pi5vl53l0x.VL53L0X`
- `pi5vl53l0x.driver.VL53L0X`
- CLI commands in [__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/__main__.py): `get`, `performance`, `calibrate`, `test`, `status`, `config`, `sensor-tool`
- config manager in [config_manager.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/config/config_manager.py) keeping `vl53l0x.json` compatibility

Backend rule:

- use the retrying I2C wrapper in [i2c.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/core/i2c.py)
- default runtime is `smbus2` over `/dev/i2c-1` on Raspberry Pi 5
- keep sensor initialization, timing budget logic, calibration, and health-check behavior independent from the low-level transport

Quality gate result:

- `uv run python -m compileall src tests`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pytest -q`
- current result for [pi5vl53l0x](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x): `62 passed`

Raspberry Pi 5 validation checklist:

- safe smoke tests: run `pi5vl53l0x --help`, `pi5vl53l0x config show`, check `ls /dev/i2c-1`, and confirm `sudo i2cdetect -y 1` shows `29`
- device communication tests: run `pi5vl53l0x test`, `pi5vl53l0x get --count 5 --interval 0.5`, and `pi5vl53l0x status`
- sensor behavior tests: run `pi5vl53l0x performance --count 50`, `pi5vl53l0x calibrate --distance 200 --count 10`, and the interactive `pi5vl53l0x sensor-tool`
- power-risk tests: do not hot-plug the sensor while commands are reading; power the Pi down before rewiring
- expected outcome: stable initialization, visible address `0x29`, consistent distance readings, saved offset calibration, and successful reinitialize recovery
- rollback: stop the running process, power down before rewiring, and remove `src/pi5vl53l0x/config/vl53l0x.json` if a clean config reset is needed

## pi5disp Migration Notes

Implemented package:

- [pi5disp](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp)

Legacy source audited for parity:

- [NinjaRobotV5_bak/pi0disp](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/NinjaRobotV5_bak/pi0disp)

Required public compatibility surface:

- `pi5disp.ST7789V`
- `pi5disp.ConfigManager`
- `pi5disp.driver.ST7789V`
- CLI commands in [__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/__main__.py): `init`, `image`, `text`, `demo`, `info`, `clear`, `brightness`, `config`, `display-tool`
- config manager in [config_manager.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/config/config_manager.py) keeping `display.json` compatibility

Backend rule:

- use the Pi 5 adapter in [driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/core/driver.py)
- default runtime is `spidev` for SPI plus an `RPi.GPIO` compatible backend intended for `rpi-lgpio`
- keep `display()` as a full-frame write path and `display_region()` as the partial-update path to match the legacy tested behavior
- keep renderer helpers and text ticker effects independent from the low-level SPI and GPIO transport
- persist the saved `brightness` value in `display.json` and apply it when `create_display()` opens a new display instance
- keep `display-tool` on one live display session so demo, brightness, clear, and text/image actions do not churn the Pi 5 backend between menu steps

Quality gate result:

- `uv run python -m compileall src tests`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pytest -q`
- `uv run pi5disp --help`
- current result for [pi5disp](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp): `63 passed`

Raspberry Pi 5 validation checklist:

- safe smoke tests: run `pi5disp --help`, `pi5disp init --defaults`, `pi5disp config show`, `pi5disp info`, and confirm `ls /dev/spidev0.0` succeeds
- device communication tests: run `pi5disp clear`, `pi5disp brightness 50`, `pi5disp config show`, `pi5disp text "Hello NinjaClawBot"`, and `pi5disp image ./example.png`
- display behavior tests: run `pi5disp text "Scrolling text" --scroll --duration 10`, `pi5disp demo --num-balls 3 --duration 10`, and the interactive `pi5disp display-tool`
- session regression tests: inside `pi5disp display-tool`, run ball demo, change brightness, then run ball demo again without clearing first
- power-risk tests: power the Pi down before rewiring the display, do not hot-plug the SPI display while the backlight is active, and confirm CLI exit leaves the panel stable with the backlight under control
- expected outcome: stable clear, text, image, demo, brightness, and scrolling behavior on the ST7789V panel, saved brightness applied on new sessions, and no stuck GPIO or SPI state after exit
- rollback: stop the running process, power down before rewiring, and remove `display.json` if a clean config reset is needed

## Raspberry Pi 5 Validation Flow

After each migrated library, produce and review:

- safe smoke tests
- device communication tests
- actuator-moving tests where relevant
- power-risk tests where relevant
- expected outcomes
- rollback steps

Special rule for `pi5servo`:

- treat software-timed servo pulses as testing-only
- prefer hardware-backed PWM
- require direct signal measurement with a logic analyser or oscilloscope during real hardware validation
