# NinjaClawBot Driver Migration Plan

Date: 2026-03-10

## Purpose

This document records the code audit and migration plan for moving the legacy Raspberry Pi Zero 2 W driver libraries from `NinjaRobotV5_bak` into Raspberry Pi 5 compatible driver packages for the new NinjaClawBot project.

Target deliverables:

- `pi5buzzer/`
- `pi5servo/`
- `pi5disp/`
- `pi5vl53l0x/`

Constraint: each new driver must preserve the observable behavior, public functions, CLI features, config formats, and integration expectations of the audited legacy packages unless a migration note explicitly calls out an unavoidable Pi 5 platform difference.

Note: the repository contains `NinjaRobotV5_bak`, not `NinjaRobotB5_bak`. This plan audits `NinjaRobotV5_bak` because that is the legacy source present in the workspace.

## Primary Usage Model

The migrated `pi5*` drivers are intended to be used primarily as standalone libraries inside the new NinjaClawBot project.

Primary design rules:

- each `pi5*` package must be usable on its own without requiring `ninja_core`
- each library must keep its own CLI, config manager, and direct Python API
- future integration hooks should still be retained where practical, such as compatibility config paths, driver entry modules, and callable class surfaces
- optional future `ninja_core` integration must not block the standalone migration of any individual library

## Scope Of Audit

Audited source packages:

- `NinjaRobotV5_bak/pi0buzzer`
- `NinjaRobotV5_bak/pi0servo`
- `NinjaRobotV5_bak/pi0disp`
- `NinjaRobotV5_bak/pi0vl53l0x`

Audited integration points:

- `NinjaRobotV5_bak/ninja_core/src/ninja_core/hal.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/config.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/robot_sound.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/movement_cli.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/movement_controller.py`

Audit method:

- Serena repository inspection for directory structure, symbol surfaces, and integration references
- targeted source review for hardware access layers and public APIs
- legacy package test execution where possible
- upstream platform research for Raspberry Pi 5 GPIO, RP1, gpiochip, and replacement user-space GPIO stacks

## Legacy Validation Snapshot

The legacy drivers are internally healthy as Python packages before migration.

| Driver | Legacy test result | Main runtime dependency risk |
|---|---:|---|
| `pi0buzzer` | `61 passed` | `pigpio` PWM |
| `pi0servo` | `82 passed` | `pigpio` servo pulses |
| `pi0disp` | `54 passed` | `pigpio` SPI, GPIO, PWM |
| `pi0vl53l0x` | `60 passed` | `pigpio` I2C |

Observations:

- The core application logic, config handling, parsing, and CLI workflows are mostly platform-neutral.
- The major migration problem is not feature completeness. It is the hardware transport layer.
- A large share of the existing behavior can be preserved by keeping high-level logic and replacing low-level GPIO/SPI/I2C/PWM access behind Pi 5 specific backends.

## Hardware And Software Evaluation

### Platform Differences: Pi Zero 2 W vs Raspberry Pi 5

The legacy drivers were written around the older Raspberry Pi peripheral model where many Python libraries assumed direct SoC-oriented GPIO access patterns. Raspberry Pi 5 changes that assumption materially.

Key differences relevant to these drivers:

1. Raspberry Pi 5 routes most user-facing GPIO, SPI, I2C, and PWM related peripheral access through the RP1 I/O controller rather than the older direct SoC layout.
2. Raspberry Pi 5 user-space GPIO now sits in the Linux GPIO character-device world (`libgpiod` model), not the old sysfs-style assumptions that older Raspberry Pi Python GPIO libraries were built around.
3. gpiochip numbering changed on Pi 5 and may vary by kernel or userspace stack version; any hard-coded chip assumptions are fragile.
4. SPI and I2C are still available on Pi 5, but the stable access path is the kernel device interface (`/dev/spidev*`, `/dev/i2c-*`), not a daemon designed around the older peripheral mapping.
5. The Pi 5 platform is fast enough for more sophisticated Python scheduling, but servo timing and audio PWM still need careful validation because software timing quality matters more than CPU speed.

### Why The Existing Drivers Are Vulnerable On Pi 5

The current drivers assume `pigpio` is available and operational for all low-level device access:

- `pi0buzzer`: `set_PWM_frequency`, `set_PWM_dutycycle`
- `pi0servo`: `set_servo_pulsewidth`, `get_servo_pulsewidth`
- `pi0disp`: `spi_open`, `spi_write`, `write`, `set_PWM_dutycycle`
- `pi0vl53l0x`: `i2c_open`, byte/word/block read-write functions

This creates the following Pi 5 risks:

1. `pigpio` dependency risk.
   The Raspberry Pi 5 GPIO migration guidance explicitly warns that older GPIO libraries tailored to previous Raspberry Pi hardware are not directly compatible. The legacy drivers depend on `pigpio` end to end.

2. Shared-daemon assumption risk.
   The legacy drivers assume a `pigpiod` daemon can be started and shared across packages. On Pi 5, driver stacks built on `libgpiod` semantics can be more exclusive about line ownership, so the new design must define line-allocation rules clearly.

3. Hard timing risk.
   `pi0servo` and `pi0buzzer` depend on PWM-like timing quality. A backend change that is merely "compatible" but not stable enough will change real robot behavior even if the API still matches.

4. Transport coupling risk.
   `pi0disp` and `pi0vl53l0x` bundle stable high-level logic with unstable low-level transport code. A naive port that changes both layers at once will be difficult to validate.

5. Integration contract risk.
   the legacy stack imports the old package names directly and also reads package-local config files such as `pi0disp/display.json`. The new Pi 5 drivers should not depend on `ninja_core`, but they should preserve optional future integration hooks so a later adapter layer can be added without reworking the standalone libraries.

### Driver-Specific Vulnerabilities

#### `pi0buzzer`

- Hardware access is entirely `pigpio` PWM based.
- Background worker behavior, note tables, song queues, and emotion sounds are platform-neutral.
- Volume semantics are expressed as duty cycle `0..255`; preserving this exact external behavior is straightforward.
- Migration risk is moderate: the backend is simple, but audible behavior changes quickly if frequency generation or duty-cycle handling differs.

#### `pi0servo`

- This is the highest-risk driver.
- The public API is stable and well-tested, but the core movement model depends on `pigpio` servo pulses on arbitrary GPIO pins.
- `ServoGroup` preserves multiple important behaviors that must not regress:
  - velocity-based synchronized motion
  - per-servo calibration
  - per-servo speed limits
  - abort support
  - compatibility alias `MultiServo = ServoGroup`
  - legacy methods used by `ninja_core`
- If the replacement backend cannot provide stable pulse timing on arbitrary pins, functional parity will be incomplete.

#### `pi0disp`

- Uses `pigpio` for three separate jobs: SPI transport, GPIO pin toggling, and backlight PWM.
- The high-level rendering utilities are mostly platform-neutral.
- Important audit finding: `README.md` advertises smart delta rendering, but `ST7789V.display()` currently always performs full-frame writes. Migration should preserve actual runtime behavior unless explicitly approved to change it.
- Migration risk is moderate: SPI and simple GPIO control are straightforward on Pi 5, but backlight PWM choice needs to be decided carefully.

#### `pi0vl53l0x`

- The sensor logic is extensive but largely independent of the platform once register I/O is correct.
- The main transport dependency is a resilient `pigpio` I2C wrapper that adds retries, endian handling, and bus recovery.
- This is the lowest-risk migration if the replacement backend uses kernel I2C cleanly and retains the retry contract.
- Packaging needs cleanup: the legacy `pyproject.toml` places `pigpio` behind an optional extra even though the runtime driver depends on it on Raspberry Pi.

## Code Audit Summary

### `pi0buzzer`

Legacy source layout:

- `src/pi0buzzer/core/driver.py`
- `src/pi0buzzer/core/music.py`
- `src/pi0buzzer/config/config_manager.py`
- `src/pi0buzzer/cli/buzzer_tool.py`
- `src/pi0buzzer/notes.py`

Public behavior to preserve:

- exports `Buzzer`, `MusicBuzzer`
- `driver.py` compatibility re-export path
- non-blocking queue-based sound playback
- `play_sound`, `queue_pause`, `play_note`, `play_song`, `play_emotion`, `play_demo`, `play_music`
- context-manager behavior
- JSON config file with `pin` and `volume`
- CLI commands and interactive tool
- emotion and note tables used by `ninja_core.robot_sound`

Hardware touchpoints to replace:

- `pi.set_mode`
- `pi.set_PWM_frequency`
- `pi.set_PWM_dutycycle`
- `pi.stop`

### `pi0servo`

Legacy source layout:

- `src/pi0servo/core/servo.py`
- `src/pi0servo/core/multi_servos.py`
- `src/pi0servo/config/config_manager.py`
- `src/pi0servo/motion/*`
- `src/pi0servo/parser/*`
- `src/pi0servo/cli/*`

Public behavior to preserve:

- exports `Servo`, `ServoCalibration`, `ServoGroup`, `ConfigManager`
- `MultiServo = ServoGroup` compatibility alias
- angle/pulse conversion semantics
- `get_pulse`, `get_angle`, `set_pulse`, `set_angle`
- coordinated movement via `move_all_sync` and `move_all_async`
- command parsing and special angle support
- abort behavior
- limp-signal recovery methods `refresh`, `ensure_active`, `refresh_all`, `ensure_all_active`
- JSON config format in `servo.json`
- CLI calibration and command tools
- legacy methods used by `ninja_core`

Hardware touchpoints to replace:

- `set_servo_pulsewidth`
- `get_servo_pulsewidth`

Integration touchpoints outside the package:

- `ninja_core.hal._init_servos()` imports `pi0servo.ConfigManager`
- `ninja_core.movement_cli` shells out to `uv run pi0servo calib ...`
- `ninja_core.movement_controller` assumes `ServoGroup.move_all_sync`

### `pi0disp`

Legacy source layout:

- `src/pi0disp/core/driver.py`
- `src/pi0disp/core/renderer.py`
- `src/pi0disp/effects/text_ticker.py`
- `src/pi0disp/config/config_manager.py`
- `src/pi0disp/cli/*`
- `display.json`

Public behavior to preserve:

- exports `ST7789V`, `ConfigManager`
- `ST7789V` Actuator-like interface: `initialize`, `execute`, `off`
- image display, region display, clear, rotation, sleep, wake, brightness control, health check
- text ticker effect and bundled fonts
- config wizard and JSON format
- CLI commands and interactive tool

Important audit note:

- `display()` currently uses full-frame rendering for robustness.
- partial rendering exists via `display_region()`.
- delta-rendering utilities are present but not the main display path.

Hardware touchpoints to replace:

- `spi_open`, `spi_write`, `spi_close`
- GPIO writes for DC and reset
- backlight PWM

Integration touchpoints outside the package:

- `ninja_core.hal` loads `pi0disp.core.driver.ST7789V`
- `ninja_core.hal` reads `pi0disp/display.json` as a fallback
- `ninja_core.config` imports that same `display.json`

### `pi0vl53l0x`

Legacy source layout:

- `src/pi0vl53l0x/core/i2c.py`
- `src/pi0vl53l0x/core/sensor.py`
- `src/pi0vl53l0x/config/config_manager.py`
- `src/pi0vl53l0x/registers.py`
- `src/pi0vl53l0x/cli/sensor_tool.py`

Public behavior to preserve:

- export `VL53L0X`
- `driver.py` compatibility re-export path
- robust initialize sequence
- retrying I2C wrapper with bus recovery
- endian-correct word reads and writes
- methods `get_range`, `get_data`, `get_ranges`, `get_range_async`, `set_offset`, `calibrate`, `health_check`, `reinitialize`, `close`
- JSON config file for offset handling
- CLI commands and interactive tool

Hardware touchpoints to replace:

- `i2c_open`, `i2c_close`
- byte, word, and block transactions

Integration touchpoints outside the package:

- `ninja_core.hal` loads `pi0vl53l0x.driver.VL53L0X`

## Recommended Pi 5 Backend Strategy

The migration should keep high-level logic and replace only the transport layer first.

Recommended backend direction:

- `pi5buzzer`: GPIO/PWM backend abstraction, likely `lgpio` or `rpi-lgpio` based PWM path for the first migration pass
- `pi5servo`: dedicated servo pulse backend abstraction; prototype and validate timing first before locking the implementation
- `pi5disp`: `spidev` for SPI, `gpiod` or `lgpio` for DC/reset GPIO, explicit backlight backend
- `pi5vl53l0x`: `smbus2` or equivalent kernel-I2C backend preserving retry/endian logic

Non-negotiable migration rule:

- backend replacement must be isolated behind small adapter classes so the existing public classes, config managers, motion logic, parsers, and CLI behavior remain almost unchanged.

## Proposed Target Structure

Each new package should be created in the project root with a near-mirror of the legacy package layout:

```text
pi5buzzer/
  pyproject.toml
  README.md
  src/pi5buzzer/
    __init__.py
    __main__.py
    driver.py
    notes.py
    core/
    config/
    cli/
  tests/

pi5servo/
  pyproject.toml
  README.md
  src/pi5servo/
    __init__.py
    __main__.py
    core/
    config/
    motion/
    parser/
    cli/
  tests/

pi5disp/
  pyproject.toml
  README.md
  display.json
  src/pi5disp/
    __init__.py
    __main__.py
    core/
    config/
    effects/
    fonts/
    cli/
  tests/

pi5vl53l0x/
  pyproject.toml
  README.md
  src/pi5vl53l0x/
    __init__.py
    __main__.py
    driver.py
    registers.py
    core/
    config/
    cli/
  tests/
```

## Phased Migration Plan

Implementation is intentionally separated into phases so each driver library is migrated, tested, and manually validated on Raspberry Pi 5 before the next driver starts.

### Phase 0: Baseline And Contract Capture

Objective:

- freeze the audited legacy behavior as the reference contract

Files or modules likely involved:

- new `developmentPlan.md`
- future parity notes under each new `pi5*` package
- copied or adapted tests from legacy packages

Validation and checks:

- confirm legacy test counts and current pass state
- inventory every public export and CLI entry point
- document current config file names and formats

Hardware risk:

- low

Documentation updates required:

- this plan

### Phase 1: `pi5buzzer` Standalone Migration

Objective:

- migrate the buzzer driver as a standalone Pi 5 library first because it is the simplest `pigpio` replacement and establishes the backend pattern for the remaining packages

Files or modules likely to change:

- `pi5buzzer/pyproject.toml`
- `pi5buzzer/src/pi5buzzer/core/driver.py`
- `pi5buzzer/src/pi5buzzer/core/music.py`
- `pi5buzzer/src/pi5buzzer/config/config_manager.py`
- `pi5buzzer/src/pi5buzzer/cli/*`
- `pi5buzzer/src/pi5buzzer/driver.py`
- `pi5buzzer/src/pi5buzzer/__init__.py`
- `pi5buzzer/tests/*`

Validation and checks:

- port all legacy tests
- add parity tests for queue behavior, note lookup, emotion sounds, and volume semantics
- `python -m compileall .`
- `ruff check .`
- `ruff format --check .`
- package-local `pytest -q`

Manual Raspberry Pi 5 validation gate:

- wire the passive buzzer to the planned GPIO pin and confirm the new config file is created successfully
- run CLI `--help`, initialize config, and play a single short beep
- play at least one note, one emotion sound, and one queued multi-note sequence
- confirm `off()` or CLI exit leaves the buzzer silent and the GPIO released

Expected result before Phase 2 starts:

- standalone library works on Pi 5
- audible behavior is stable for short tones and queued playback
- optional compatibility surfaces such as `driver.py` entry re-exports remain intact

Hardware risk:

- medium

Documentation updates required:

- package README
- DevelopmentGuide standalone library usage note
- DevelopmentLog

### Phase 2: `pi5vl53l0x` Standalone Migration

Objective:

- migrate the distance sensor next as a standalone Pi 5 library because its high-level logic is stable and the transport can move cleanly to kernel I2C

Files or modules likely to change:

- `pi5vl53l0x/pyproject.toml`
- `pi5vl53l0x/src/pi5vl53l0x/core/i2c.py`
- `pi5vl53l0x/src/pi5vl53l0x/core/sensor.py`
- `pi5vl53l0x/src/pi5vl53l0x/config/config_manager.py`
- `pi5vl53l0x/src/pi5vl53l0x/cli/*`
- `pi5vl53l0x/src/pi5vl53l0x/driver.py`
- `pi5vl53l0x/src/pi5vl53l0x/__init__.py`
- `pi5vl53l0x/tests/*`

Validation and checks:

- port all legacy tests
- add backend tests for byte, word, and block operations
- add parity tests for retry behavior and config import-export
- `python -m compileall .`
- `ruff check .`
- `ruff format --check .`
- package-local `pytest -q`

Manual Raspberry Pi 5 validation gate:

- confirm the VL53L0X is detected on the expected I2C bus
- run a single read, repeated reads, and a basic health-check command
- verify offset config load-save behavior on the Pi
- run `reinitialize()` after a deliberate close or recovery scenario

Expected result before Phase 3 starts:

- standalone library can initialize and read consistently on Pi 5
- retry and recovery behavior work with the new I2C backend
- optional compatibility re-export entries remain available for future integration

Hardware risk:

- medium

Documentation updates required:

- package README
- DevelopmentGuide sensor section
- DevelopmentLog

### Phase 3: `pi5disp` Standalone Migration

Objective:

- migrate the display as a standalone Pi 5 library after the backend pattern is proven on simpler devices

Files or modules likely to change:

- `pi5disp/pyproject.toml`
- `pi5disp/src/pi5disp/core/driver.py`
- `pi5disp/src/pi5disp/core/renderer.py`
- `pi5disp/src/pi5disp/effects/text_ticker.py`
- `pi5disp/src/pi5disp/config/config_manager.py`
- `pi5disp/src/pi5disp/cli/*`
- `pi5disp/src/pi5disp/__init__.py`
- `pi5disp/display.json`
- `pi5disp/tests/*`

Validation and checks:

- port all legacy tests
- keep full-frame `display()` behavior unless an approved improvement is made
- add transport tests for SPI open-close and GPIO pin control
- `python -m compileall .`
- `ruff check .`
- `ruff format --check .`
- package-local `pytest -q`

Manual Raspberry Pi 5 validation gate:

- run the config wizard and save a working display profile on the Pi
- clear the display, render a static image, and verify rotation handling
- validate brightness changes, sleep-wake, and health check behavior
- run text ticker and repeated image updates long enough to expose SPI or GPIO instability

Expected result before Phase 4 starts:

- standalone display library renders reliably on Pi 5
- config and CLI workflows work without any `ninja_core` dependency
- future integration-related config entry points are preserved

Hardware risk:

- medium-high

Documentation updates required:

- package README
- DevelopmentGuide display wiring and setup
- DevelopmentLog

### Phase 4: `pi5servo` Standalone Migration

Objective:

- migrate the servo driver last as a standalone Pi 5 library because it has the strictest timing requirements and the highest real-world regression risk

Files or modules likely to change:

- `pi5servo/pyproject.toml`
- `pi5servo/src/pi5servo/core/servo.py`
- `pi5servo/src/pi5servo/core/multi_servos.py`
- `pi5servo/src/pi5servo/config/config_manager.py`
- `pi5servo/src/pi5servo/motion/*`
- `pi5servo/src/pi5servo/parser/*`
- `pi5servo/src/pi5servo/cli/*`
- `pi5servo/src/pi5servo/__init__.py`
- `pi5servo/tests/*`

Validation and checks:

- port all legacy tests
- add Pi tests for pulse stability, center-min-max calibration, multi-servo synchronization, abort handling, and limp-signal recovery
- add standalone API parity tests for `MultiServo`, legacy movement helpers, and config schema
- `python -m compileall .`
- `ruff check .`
- `ruff format --check .`
- package-local `pytest -q`

Manual Raspberry Pi 5 validation gate:

- connect one servo on external power with common ground and validate center, min, and max slowly
- validate calibration save-load and interactive calibration workflow
- validate one multi-servo slow synchronized move only after single-servo tests pass
- test abort, `off()`, and signal recovery behavior
- confirm the library leaves servos in a safe-off state when the CLI exits or the driver closes

Expected result before any optional integration phase starts:

- standalone servo library behaves safely and predictably on Pi 5
- timing quality is acceptable under realistic load
- future integration helper surfaces remain available but are not required for standalone use

Hardware risk:

- high

Documentation updates required:

- package README
- DevelopmentGuide servo calibration and safety section
- DevelopmentLog

### Phase 5: Optional Future Integration Hooks

Objective:

- retain or add optional integration features for future development without making them a blocker for standalone library completion

Files or modules likely to change:

- optional adapter modules or compatibility notes inside each `pi5*` package
- future NinjaClawBot HAL or driver registry files if the project later chooses to use them
- future config import-export bridge paths
- future tooling that shells out to CLI entry points

Validation and checks:

- import and smoke test any optional driver re-export entries
- verify optional config path compatibility if implemented
- confirm standalone packages still work after optional compatibility additions

Hardware risk:

- low-medium

Documentation updates required:

- root `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

## Driver-Specific Migration Notes

### `pi5buzzer`

Implementation approach:

- copy the legacy package structure
- keep `Buzzer` and `MusicBuzzer` APIs intact
- introduce a thin Pi 5 PWM backend
- preserve JSON config and CLI command names adjusted to the new package name

Behavioral parity checks:

- same note table
- same emotion tables
- same queue ordering
- same `volume` range and semantics
- same context-manager behavior

### `pi5servo`

Implementation approach:

- preserve `Servo`, `ServoCalibration`, `ServoGroup`, parser, motion utilities, config manager, and CLI tools
- isolate only the pulse I/O operations behind a backend
- keep legacy compatibility methods for future integration work, but do not make `ninja_core` a runtime requirement of the standalone package

Behavioral parity checks:

- same angle-to-pulse mapping
- same duration and easing behavior
- same abort behavior
- same calibration JSON
- same `MultiServo` alias

Open technical risk:

- if the chosen Pi 5 backend cannot hold stable multi-pin servo pulses, identical real-world behavior will require a more specialized pulse-generation strategy

### `pi5disp`

Implementation approach:

- preserve `ST7789V` surface and config manager behavior
- split SPI, GPIO, and backlight control into separate backend helpers
- keep renderer and ticker logic mostly unchanged

Behavioral parity checks:

- preserve full-frame `display()` semantics
- preserve `display_region()`, `clear()`, `set_rotation()`, `sleep()`, `wake()`
- preserve config wizard and JSON structure

### `pi5vl53l0x`

Implementation approach:

- preserve `VL53L0X` logic and register table
- rewrite only the bus wrapper around kernel I2C access
- keep endian swapping, retry policy, and bus-recovery semantics

Behavioral parity checks:

- same initialization order
- same exception contract
- same offset config behavior
- same CLI features

## Optional Future Integration With `ninja_core`

The new `pi5*` libraries should be considered complete when their standalone APIs, tests, and Raspberry Pi 5 manual validation gates pass.

If future development later chooses to integrate them with `ninja_core` style infrastructure, these items should be addressed in a separate optional phase:

1. Driver registry paths still reference `pi0*` modules in `ninja_core/hal.py`.
2. `ninja_core.robot_sound` imports `pi0buzzer.notes` directly.
3. `ninja_core.hal` and `ninja_core.config` use `pi0disp/display.json`.
4. `ninja_core.movement_cli` shells out to `uv run pi0servo calib`.
5. Servo config import logic assumes the legacy `servo.json` schema.

Standalone-first policy:

- create the new `pi5*` packages first
- keep optional compatibility entry points where they are cheap to preserve
- add explicit integration shims only if the new project later chooses to depend on them
- do not delay any individual driver migration waiting for `ninja_core`

## Quality Gates For Every Future Implementation Phase

If the repository does not define stricter standards, use this gate after every implementation phase:

```bash
python -m compileall .
ruff check .
ruff format --check .
pytest -q
```

Package-local execution is recommended during migration work so failures remain isolated to the driver being ported.

## Raspberry Pi 5 Validation Plan

The following validation categories must be produced and executed during the actual implementation phases.

### Safe Smoke Tests

- verify package imports on Pi 5
- verify CLI `--help`
- verify config file create/load/save paths
- verify backend initialization without moving actuators

Expected result:

- package starts cleanly and reports hardware availability accurately

Rollback:

- disable the new package from the driver registry and fall back to the last known good branch

### Device Communication Tests

- `pi5disp`: SPI open, reset line toggle, render a static frame
- `pi5vl53l0x`: identify sensor on bus 1, read multiple distances, verify reinitialize path
- `pi5buzzer`: generate stable frequency output without long-duration playback

Expected result:

- transport opens cleanly and basic device I/O succeeds with no repeated bus faults

Rollback:

- close device handles, power cycle peripherals, revert backend change if failures reproduce

### Actuator-Moving Tests

- `pi5servo`: center one servo, then min/max with mechanical clearance
- multi-servo synchronized move at slow speed only
- `pi5buzzer`: short melody playback
- `pi5disp`: text ticker and repeated frame updates

Expected result:

- motion is smooth, deterministic, and recoverable from abort

Rollback:

- cut PWM or backlight output immediately and return all actuators to safe-off state

### Power-Risk Tests

- servo load test with external power and common ground
- display backlight at multiple brightness levels
- repeated sensor and display activity while servos move slowly

Expected result:

- no brown-outs, USB disconnects, or kernel peripheral resets

Rollback:

- stop all drivers, disconnect external load, inspect power distribution before further testing

## Recommended Implementation Order

1. `pi5buzzer`
2. `pi5vl53l0x`
3. `pi5disp`
4. `pi5servo`
5. optional future integration hooks

Reasoning:

- it front-loads the simplest backend replacement
- it proves kernel-I2C migration early
- it defers the highest timing-risk work until the rest of the stack is stable

## References

- [Raspberry Pi: GPIO on Raspberry Pi 5 and similar devices](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-on-raspberry-pi-5-and-similar-devices)
- [Raspberry Pi RP1 peripherals datasheet](https://datasheets.raspberrypi.com/rp1/rp1-peripherals.pdf)
- [gpiozero pin factory documentation](https://gpiozero.readthedocs.io/en/stable/api_pins.html)
- [lgpio package index](https://pypi.org/project/lgpio/)
- [rpi-lgpio package index](https://pypi.org/project/rpi-lgpio/)
- [rpi-lgpio changelog](https://rpi-lgpio.readthedocs.io/en/latest/changelog.html)

## Current Status

This document completes the audit and planning stage only.

No migration code has been implemented yet.
