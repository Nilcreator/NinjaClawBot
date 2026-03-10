# Development Log

## 2026-03-10

### pi5vl53l0x Migration

Summary:

- migrated the second Raspberry Pi 5 standalone driver library as [pi5vl53l0x](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x)
- kept the legacy `pi0vl53l0x` public API shape, CLI command set, config contract, calibration flow, health check, and reinitialize path
- replaced the legacy `pigpio` I2C transport with a thread-safe `smbus2` backend over the Raspberry Pi 5 kernel I2C interface
- ported and adapted the legacy test suite for I2C, sensor logic, config handling, and CLI smoke coverage

Files changed:

- [pi5vl53l0x/pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/pyproject.toml)
- [pi5vl53l0x/.python-version](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/.python-version)
- [pi5vl53l0x/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/README.md)
- [pi5vl53l0x/src/pi5vl53l0x/__init__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/__init__.py)
- [pi5vl53l0x/src/pi5vl53l0x/__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/__main__.py)
- [pi5vl53l0x/src/pi5vl53l0x/driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/driver.py)
- [pi5vl53l0x/src/pi5vl53l0x/registers.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/registers.py)
- [pi5vl53l0x/src/pi5vl53l0x/core/i2c.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/core/i2c.py)
- [pi5vl53l0x/src/pi5vl53l0x/core/sensor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/core/sensor.py)
- [pi5vl53l0x/src/pi5vl53l0x/config/config_manager.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/config/config_manager.py)
- [pi5vl53l0x/src/pi5vl53l0x/cli/sensor_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/cli/sensor_tool.py)
- [pi5vl53l0x/tests/test_i2c.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/tests/test_i2c.py)
- [pi5vl53l0x/tests/test_sensor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/tests/test_sensor.py)
- [pi5vl53l0x/tests/test_config.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/tests/test_config.py)
- [pi5vl53l0x/tests/test_cli.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/tests/test_cli.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- Raspberry Pi 5 does not support the legacy `pigpio` I2C path used by `pi0vl53l0x`
- the migration needed to preserve the known-good VL53L0X register sequencing while only replacing the transport layer
- the new library had to stay standalone-first for NinjaClawBot while keeping future compatibility hooks such as `driver.py`

Lint and test results:

- `uv run python -m compileall src tests`: passed
- `uv run ruff check .`: passed
- `uv run ruff format --check .`: passed
- `uv run pytest -q`: `62 passed in 2.43s`
- `uv run pi5vl53l0x --help`: passed

Raspberry Pi validation status:

- manual Raspberry Pi 5 validation is still required
- planned checks: `ls /dev/i2c-1`, `sudo i2cdetect -y 1`, `uv run pi5vl53l0x test`, `uv run pi5vl53l0x get --count 5 --interval 0.5`, `uv run pi5vl53l0x status`, `uv run pi5vl53l0x performance --count 50`, `uv run pi5vl53l0x calibrate --distance 200 --count 10`, and `uv run pi5vl53l0x sensor-tool`
- expected hardware result: visible sensor at address `0x29`, stable readings, successful calibration save, and successful reinitialize recovery

Follow-up:

- run the Raspberry Pi 5 manual validation checklist for `pi5vl53l0x`
- if hardware validation passes, proceed to the `pi5servo` or `pi5disp` migration phase

### pi5buzzer Migration

Summary:

- migrated the first Raspberry Pi 5 standalone driver library as [pi5buzzer](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer)
- kept the legacy `pi0buzzer` public API shape, note table, emotion sounds, CLI command set, and `buzzer.json` config format
- replaced direct `pigpio` usage with a backend abstraction and a default `RPi.GPIO` compatible backend factory intended for `rpi-lgpio` on Raspberry Pi 5
- ported and adapted the legacy test suite for the new package

Files changed:

- [pi5buzzer/pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/pyproject.toml)
- [pi5buzzer/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/README.md)
- [pi5buzzer/src/pi5buzzer/__init__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/__init__.py)
- [pi5buzzer/src/pi5buzzer/__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/__main__.py)
- [pi5buzzer/src/pi5buzzer/driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/driver.py)
- [pi5buzzer/src/pi5buzzer/notes.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/notes.py)
- [pi5buzzer/src/pi5buzzer/core/driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/core/driver.py)
- [pi5buzzer/src/pi5buzzer/core/music.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/core/music.py)
- [pi5buzzer/src/pi5buzzer/config/config_manager.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/config/config_manager.py)
- [pi5buzzer/src/pi5buzzer/cli/buzzer_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/cli/buzzer_tool.py)
- [pi5buzzer/tests/conftest.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/tests/conftest.py)
- [pi5buzzer/tests/test_driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/tests/test_driver.py)
- [pi5buzzer/tests/test_music.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/tests/test_music.py)
- [pi5buzzer/tests/test_config.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/tests/test_config.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- `pi5buzzer` was the lowest-risk first migration and establishes the backend pattern for the remaining Pi 5 libraries
- Raspberry Pi 5 does not support the legacy `pigpio` path used by `pi0buzzer`, so the GPIO transport needed to be isolated behind a Pi 5 compatible interface
- the new library had to remain standalone-first while keeping future integration surfaces such as `driver.py`

Lint and test results:

- `python -m compileall .`: passed
- `ruff check .`: passed
- `ruff format --check .`: passed
- `pytest -q`: `63 passed in 6.32s`

Raspberry Pi validation status:

- manual Raspberry Pi 5 validation is still required
- planned checks: `pi5buzzer --help`, `pi5buzzer init 17`, `pi5buzzer info --health-check`, `pi5buzzer beep 440 0.3`, `pi5buzzer play happy`, and a short `play_song()` Python sequence
- expected hardware result: audible short tones, stable queued playback, and silent output after `off()` or CLI exit

Follow-up:

- run the Raspberry Pi 5 manual validation checklist for `pi5buzzer`
- if hardware validation passes, proceed to the `pi5vl53l0x` migration phase

### pi5buzzer Installation Fix

Summary:

- investigated the standalone Raspberry Pi installation failure reported for `uv sync --extra pi --extra dev`
- identified the failure as an `lgpio` wheel-availability problem, not a `pi5buzzer` code defect
- pinned the standalone project to Python 3.11 and documented the manual recovery steps in the package README

Files changed:

- [pi5buzzer/pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/pyproject.toml)
- [pi5buzzer/.python-version](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/.python-version)
- [pi5buzzer/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- `rpi-lgpio` depends on `lgpio`
- `lgpio 0.2.2.0` currently publishes Raspberry Pi Linux ARM wheels for CPython 3.9, 3.10, 3.11, and 3.12, but not 3.13
- when `uv` selected Python 3.13, it fell back to a source build, which required `swig` and failed on a normal Raspberry Pi setup
- pinning the package to Python 3.11 gives a reliable install path on Raspberry Pi OS Bookworm

Lint and test results:

- no code tests run
- packaging and documentation update only

Raspberry Pi validation status:

- manual Raspberry Pi 5 installation retry is still required
- expected recovery path: remove `.venv`, rerun `uv sync --extra pi --extra dev`, then verify with `uv run pi5buzzer --help`

Follow-up:

- confirm the updated install flow works on the target Raspberry Pi 5
- if it does, keep Python 3.11 as the standalone default for the next Pi-facing driver packages

### pi5buzzer Shutdown Fix

Summary:

- audited the `pi5buzzer` backend shutdown path after a Raspberry Pi 5 runtime traceback was reported when leaving `buzzer-tool`
- identified the bug as a cleanup-order issue between our backend wrapper and `rpi-lgpio` PWM object destruction
- fixed the backend so PWM objects are released before `GPIO.cleanup()` closes the chip handle
- added regression tests for destructor-safe cleanup and repeated backend stop calls

Files changed:

- [pi5buzzer/src/pi5buzzer/core/driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/core/driver.py)
- [pi5buzzer/tests/conftest.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/tests/conftest.py)
- [pi5buzzer/tests/test_driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/tests/test_driver.py)
- [pi5buzzer/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- upstream `rpi-lgpio` PWM objects call `stop()` from `__del__`
- our wrapper previously closed the GPIO chip handle before those PWM objects were fully released
- that left the later destructor path running against a closed chip handle and produced the `NoneType & int` traceback on exit
- the same centralized backend fix also protects the other CLI paths that call `pi.stop()`

Lint and test results:

- `python -m compileall .`: passed
- `ruff check .`: passed
- `ruff format --check .`: passed
- `pytest -q`: `65 passed in 6.32s`

Raspberry Pi validation status:

- manual Raspberry Pi 5 validation is still required
- expected validation: run `uv run pi5buzzer buzzer-tool`, choose `9. Exit`, and confirm there is no cleanup traceback after `Goodbye!`

Follow-up:

- verify the clean shutdown behavior on the target Raspberry Pi 5
- if the result is clean, use the same shutdown pattern in future Pi 5 drivers that wrap `rpi-lgpio` resources

### Workflow Refinement

Summary:

- refined the agentic development workflow for the new Pi 5 driver libraries
- updated the `ninjaclawbot-implementation` skill to follow the standalone-first `pi5*` migration plan
- aligned repository docs so the skill, development plan, and developer guide point to the same workflow

Files changed:

- `.agents/skills/ninjaclawbot-implementation/SKILL.md`
- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

Why:

- the original skill was too generic for the current Pi 5 library migration work
- the new workflow needed explicit rules for required files, required functions, backend selection, quality checks, and manual Raspberry Pi 5 validation after each library

Lint and test results:

- no code tests run
- documentation-only update

Raspberry Pi validation status:

- not applicable for this change

Follow-up:

- use the updated skill as the default implementation guide for future `pi5buzzer`, `pi5servo`, `pi5disp`, and `pi5vl53l0x` work
