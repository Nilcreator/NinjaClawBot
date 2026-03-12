# NinjaClawBot Development Guide

## Scope

This guide records the current developer workflow for the standalone Pi 5 driver libraries and the rebuilt integration layer:

- `pi5buzzer`
- `pi5servo`
- `pi5disp`
- `pi5vl53l0x`
- `ninjaclawbot`

The detailed migration and backend strategy lives in [developmentPlan.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/developmentPlan.md).

## Root Workspace Workflow

The repository root is now the main install and execution location.

Main rule:

- run `uv sync --extra dev` from the project root
- run `uv run ...` commands from the project root
- keep shared runtime files at the project root

Root-managed runtime files:

- `servo.json`
- `buzzer.json`
- `display.json`
- `vl53l0x.json`
- `ninjaclawbot_data/movements/*.json`
- `ninjaclawbot_data/expressions/*.json`

Why this matters:

- the standalone `pi5*` packages still work inside their own folders
- the integrated `ninjaclawbot` environment now uses the same code and the same root-level config files
- users no longer need to install `ninjaclawbot` first and then manually install each driver package into the same environment

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

## ninjaclawbot Integration Layer

The new [ninjaclawbot](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot) package is the high-level robot control layer for future OpenClaw integration and standalone operator control.

Current responsibilities:

- adapter-based composition of `pi5servo`, `pi5disp`, `pi5buzzer`, and `pi5vl53l0x`
- structured action validation and structured result reporting
- persistent movement and expression assets under `ninjaclawbot_data/`
- a first-class expression engine with animated built-in faces, sound chains, and idle orchestration
- interactive `movement-tool` and `expression-tool`
- CLI actions for `health-check`, `list-assets`, `move-servos`, `perform-movement`, `perform-expression`, and JSON `run-action`
- safe failure reporting when hardware is unavailable or not calibrated yet

Important rule:

- external AI assistants should call `ninjaclawbot`, not the raw `pi5*` drivers directly

## ninjaclawbot File Layout

Main package layout:

- `ninjaclawbot/src/ninjaclawbot/actions.py`
- `ninjaclawbot/src/ninjaclawbot/results.py`
- `ninjaclawbot/src/ninjaclawbot/errors.py`
- `ninjaclawbot/src/ninjaclawbot/config.py`
- `ninjaclawbot/src/ninjaclawbot/locks.py`
- `ninjaclawbot/src/ninjaclawbot/adapters.py`
- `ninjaclawbot/src/ninjaclawbot/assets.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/src/ninjaclawbot/executor.py`
- `ninjaclawbot/src/ninjaclawbot/expressions/catalog.py`
- `ninjaclawbot/src/ninjaclawbot/expressions/faces.py`
- `ninjaclawbot/src/ninjaclawbot/expressions/player.py`
- `ninjaclawbot/src/ninjaclawbot/expressions/sounds.py`
- `ninjaclawbot/src/ninjaclawbot/__main__.py`
- `ninjaclawbot/src/ninjaclawbot/cli/movement_tool.py`
- `ninjaclawbot/src/ninjaclawbot/cli/expression_tool.py`

Generated user asset paths:

- `ninjaclawbot_data/movements`
- `ninjaclawbot_data/expressions`

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

For the full project from the root, use:

```bash
uv sync --extra dev
uv run python -m compileall ninjaclawbot/src ninjaclawbot/tests src
uv run ruff check .
uv run ruff format --check .
uv run python -c "import ninjaclawbot, pi5buzzer, pi5servo, pi5disp, pi5vl53l0x"
uv run ninjaclawbot --help
```

For pytest in the root monorepo, run each package test suite from the root with
that package's own config:

```bash
uv run pytest -q pi5buzzer/tests -c pi5buzzer/pyproject.toml
uv run pytest -q pi5servo/tests -c pi5servo/pyproject.toml
uv run pytest -q pi5disp/tests -c pi5disp/pyproject.toml
uv run pytest -q pi5vl53l0x/tests -c pi5vl53l0x/pyproject.toml
uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml
```

For [ninjaclawbot](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot) alone, use:

```bash
cd ninjaclawbot
uv sync --extra dev
uv run python -m compileall src tests
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
uv run python -c "import pi5buzzer, pi5servo, pi5disp, pi5vl53l0x"
uv run ninjaclawbot --help
```

Packaging note:

- the root [pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pyproject.toml) is now the canonical project install entry
- it installs `ninjaclawbot` and all sibling `pi5*` packages through local editable `uv` path sources
- `ninjaclawbot/pyproject.toml` still keeps the integration package usable on its own

## ninjaclawbot Raspberry Pi Validation

Safe smoke tests:

- `uv run ninjaclawbot list-assets`
- `uv run ninjaclawbot health-check`

Device communication tests:

- `uv run ninjaclawbot run-action '{"action":"read_distance"}'`
- `uv run ninjaclawbot perform-expression <name>`

Actuator-moving tests:

- `uv run ninjaclawbot move-servos "M_gpio12:C"`
- `uv run ninjaclawbot perform-movement <name>`
- `uv run ninjaclawbot expression-tool`

Power-risk tests:

- use external servo power where required
- power down before rewiring SPI and I2C devices
- keep one-servo-only tests for the first movement validation pass

Expected integrated expression result:

- `perform-expression` should keep the display output stable
- `perform-expression` should resolve both saved expressions and built-in names such as `idle` or `greeting`
- built-in expression previews should show animated legacy-style faces rather than static text-only output
- queued buzzer emotion playback should finish before the command exits
- temporary reactions should return to `idle` when `idle_reset` is enabled
- leaving `expression-tool` should not print GPIO cleanup tracebacks

Recommended calibration order before integrated robot tests:

1. `uv run pi5servo calib <endpoint>` or `uv run pi5servo servo-tool`
2. `uv run pi5buzzer init <gpio>` if you need a non-default buzzer pin
3. `uv run pi5disp init --defaults`
4. `uv run pi5vl53l0x test`
5. `uv run ninjaclawbot health-check`

## ninjaclawbot Troubleshooting

### `expression-tool` exit cleanup

If `expression-tool` exits with `RPi.GPIO` or `lgpio` cleanup tracebacks:

- verify the integrated runtime is closing the display before the buzzer
- verify you are using the current root environment from `uv sync --extra dev`
- rerun `uv run ninjaclawbot expression-tool` and confirm it returns to the shell cleanly after `Goodbye!`

### `perform-expression` sound playback

If the display text appears but the emotion sound is cut short:

- verify you are running `uv run ninjaclawbot perform-expression <name>` from the project root
- verify the saved expression uses a valid `sound.emotion` value such as `happy`
- confirm the command does not return until the buzzer sequence finishes
- if needed, compare with `uv run pi5buzzer play happy` to confirm the buzzer hardware path itself is healthy

### Built-in expression execution

If `uv run ninjaclawbot perform-expression idle` or another built-in name fails:

- verify you are running from the project root after `uv sync --extra dev`
- confirm the name is one of the built-ins exposed by `expression-tool`
- check both execution paths:
  - `uv run ninjaclawbot perform-expression idle`
  - `uv run ninjaclawbot perform-expression <saved-name>`
- expected result: saved assets are loaded from `ninjaclawbot_data/expressions`, and built-in names fall back to the expression catalog when no saved asset exists

### Expression preview and idle policy

If a built-in preview does not look animated or the robot does not return to `idle` correctly:

- verify you are using the current root environment from `uv sync --extra dev`
- run `uv run ninjaclawbot expression-tool`
- preview `idle`, `happy`, `speaking`, `thinking`, and `confusing`
- use `7. Set idle expression`, then `8. Stop active expression`
- confirm the display returns to an animated waiting face when requested and stops cleanly on command

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

## pi5servo Migration Notes

Implemented package:

- [pi5servo](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo)

Legacy source audited for parity:

- [NinjaRobotV5_bak/pi0servo](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/NinjaRobotV5_bak/pi0servo)

Required public compatibility surface:

- `pi5servo.Servo`
- `pi5servo.ServoCalibration`
- `pi5servo.ServoGroup`
- `pi5servo.MultiServo`
- `pi5servo.ConfigManager`
- parser and motion exports in [__init__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/__init__.py)
- compatibility re-export in [driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/driver.py)
- CLI commands in [__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/__main__.py): `cmd`, `move`, `calib`, `status`, `servo-tool`, `config`
- config manager in [config_manager.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py) keeping `servo.json` compatibility and adding optional backend metadata

Backend rule:

- use the backend factory in [backend.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/backend.py)
- default runtime is standalone-first for Raspberry Pi 5 and prefers hardware-backed PWM on header-connected servo pins
- keep the legacy pigpio path available as a compatibility backend, not as the standalone default
- keep the high-level motion model, easing, calibration, and command parsing independent from the low-level pulse generator
- keep optional advanced external controller support through the `pca9685` backend
- `pwm_pio` remains a planned backend placeholder and is not a production runtime yet

DFR0566 endpoint rule:

- treat a DFR0566 digital port used for servo signal as a native GPIO endpoint
- treat a DFR0566 PWM servo connector as a HAT PWM endpoint driven by the dedicated `dfr0566` backend
- do not let those two connection families share one ambiguous integer namespace
- the implemented explicit endpoint naming model is:
  - native GPIO: `gpio12`, `gpio13`, `gpio18`, `gpio19`
  - DFR0566 PWM: `hat_pwm1`, `hat_pwm2`, `hat_pwm3`, `hat_pwm4`
- current physical mapping on the HAT is:
  - physical `PWM0` -> `hat_pwm1`
  - physical `PWM1` -> `hat_pwm2`
  - physical `PWM2` -> `hat_pwm3`
  - physical `PWM3` -> `hat_pwm4`
- numeric targets such as `12:45` still mean native GPIO shorthand, but explicit endpoint names are now supported for mixed routing

Functions adapted for DFR0566 mixed-endpoint support:

- [create_servo_backend](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/backend.py)
- [Servo.__init__](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/servo.py#L47)
- [ServoGroup.__init__](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/multi_servos.py#L30)
- [ServoGroup._resolve_backend](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/multi_servos.py#L74)
- [ServoGroup._resolve_targets](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/multi_servos.py#L343)
- [ServoTarget](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/parser/command.py#L16)
- [ParsedCommand](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/parser/command.py#L35)
- [parse_command](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/parser/command.py#L50)
- [parse_pin_list](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/_common.py#L30)
- [create_servo_from_config](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/_common.py#L170)
- [create_group_from_config](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/_common.py#L206)
- [ConfigManager.load](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py#L63)
- [ConfigManager.get_calibration](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py#L118)
- [ConfigManager.set_calibration](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py#L141)
- [ConfigManager.get_all_calibrations](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py#L158)
- [ConfigManager.get_all_endpoint_calibrations](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py)
- [config_cmd.show](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/config_cmd.py)
- [calib](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/calib.py)
- [servo_tool](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/servo_tool.py)

Quality gate result:

- `uv run python -m compileall src tests`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pytest -q`
- current result for [pi5servo](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo): `121 passed`

Raspberry Pi 5 validation checklist:

- safe smoke tests: run `uv run pi5servo --help`, `uv run pi5servo status --pins 12,13`, `uv run pi5servo config show`, and confirm the selected backend and `servo.json` values look correct
- empty-config interactive check: if `servo.json` has no saved endpoints, run `uv run pi5servo servo-tool` and confirm it does not auto-claim `GPIO12` or `GPIO13` before you enter an explicit endpoint
- DFR0566 smoke tests: run `uv run pi5servo status --backend dfr0566 --pins hat_pwm1 --address 0x10 --bus-id 1` and confirm the board responds cleanly
- firmware checks: confirm the correct PWM overlay is enabled in `/boot/firmware/config.txt`, reboot the Pi, and verify the intended PWM-capable pins match the selected backend mapping
- device communication tests: run `uv run pi5servo move 12 center`, `uv run pi5servo move 12 min`, `uv run pi5servo move 12 max`, `uv run pi5servo move hat_pwm1 center --backend dfr0566 --address 0x10 --bus-id 1`, `uv run pi5servo calib hat_pwm1 --backend dfr0566 --address 0x10 --bus-id 1`, and `uv run pi5servo cmd "M_gpio12:45/hat_pwm1:-30" --pins gpio12,hat_pwm1`
- actuator-moving tests: run `uv run pi5servo servo-tool`, verify calibration, quick move, single move, speed update, and clean exit centering behavior for both `gpioNN` and `hat_pwmN`
- same-session calibration check: calibrate a servo, stay inside the same `servo-tool` session, then run Quick Move and confirm the newly calibrated servo responds correctly without exiting and reopening the tool
- quick-move regression check: after moving a servo through the interactive tool, run `F_gpio12:0/gpio13:0` or the equivalent endpoints in Quick Move and confirm the servos return to center instead of silently skipping the PWM write
- mixed-routing tests: verify `servo-tool` accepts both `gpio12` and `hat_pwm1`, and confirm mixed commands no longer fail on mixed-type endpoint sorting
- signal accuracy tests: measure the servo signal with a logic analyser or oscilloscope at center, min, and max pulse widths before trusting the setup for full robot motion
- power-risk tests: use an external 5V servo supply with common ground, keep the robot linkage clear during first tests, and power the Pi down before rewiring
- expected outcome: stable pulse output on the intended GPIO pins, correct DFR0566 I2C communication at the configured address, correct endpoint-aware calibration save/load, repeatable sync movement, abortable motion, and safe release on `off()` and CLI exit
- rollback: stop the process, disconnect servo signal lines, remove `servo.json` if a clean config reset is needed, and revert to a single-servo center-only test before reintroducing multi-servo motion

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
