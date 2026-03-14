# NinjaClawBot Driver Migration Plan

Date: 2026-03-10

## Table Of Contents

- [Purpose](#purpose)
- [Primary Usage Model](#primary-usage-model)
- [Scope Of Audit](#scope-of-audit)
- [Legacy Validation Snapshot](#legacy-validation-snapshot)
- [Hardware And Software Evaluation](#hardware-and-software-evaluation)
- [Code Audit Summary](#code-audit-summary)
- [Recommended Pi 5 Backend Strategy](#recommended-pi-5-backend-strategy)
- [Researched Replacement For `pigpio` On Raspberry Pi 5](#researched-replacement-for-pigpio-on-raspberry-pi-5)
- [GPIO Accuracy Strategy For `pi5servo`](#gpio-accuracy-strategy-for-pi5servo)
- [Recommended Production Position](#recommended-production-position)
- [Proposed Target Structure](#proposed-target-structure)
- [Phased Migration Plan](#phased-migration-plan)
- [Driver-Specific Migration Notes](#driver-specific-migration-notes)
- [DFR0566 Endpoint Model For `pi5servo`](#dfr0566-endpoint-model-for-pi5servo)
- [Affected `pi5servo` Functions For Endpoint Refinement](#affected-pi5servo-functions-for-endpoint-refinement)
- [Optional Future Integration With `ninja_core`](#optional-future-integration-with-ninja_core)
- [Rebuilt `ninjaclawbot` Integration Layer](#rebuilt-ninjaclawbot-integration-layer)
- [Interactive Tool Strategy For Rebuilt `ninjaclawbot`](#interactive-tool-strategy-for-rebuilt-ninjaclawbot)
- [Phased `ninjaclawbot` Rebuild Plan](#phased-ninjaclawbot-rebuild-plan)
- [Quality Gates For Every Future Implementation Phase](#quality-gates-for-every-future-implementation-phase)
- [Raspberry Pi 5 Validation Plan](#raspberry-pi-5-validation-plan)
- [Recommended Implementation Order](#recommended-implementation-order)
- [References](#references)
- [Current Status](#current-status)

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

## Researched Replacement For `pigpio` On Raspberry Pi 5

### Core conclusion

There is no single, fully drop-in `pigpio` replacement on Raspberry Pi 5 that cleanly reproduces all of these at once:

- local GPIO line control
- edge callbacks
- SPI and I2C wrappers
- daemon-based remote access
- low-jitter PWM and servo pulse generation on arbitrary pins

The reliable replacement for the new `pi5*` libraries is a layered backend strategy.

### Reliable replacement stack by function

#### 1. Digital GPIO, edge callbacks, and general pin ownership

Recommended base:

- `libgpiod` ecosystem through `lgpio` or `rpi-lgpio`

Why:

- Raspberry Pi’s GPIO usage whitepaper says `pigpio` does not yet work on Raspberry Pi 5 and is not recommended for new projects.
- The same whitepaper says `lgpio` should run on all Raspberry Pi models and notes that `rpi-lgpio` is the `RPi.GPIO`-compatible option expected to function on Pi 5.
- `gpiozero` documentation shows that `LGPIOFactory` uses `lgpio` against `/dev/gpiochip*`, which is aligned with the Pi 5 GPIO model.

Use in `pi5*` libraries:

- output pins
- input pins
- edge detection
- simple on-off control
- non-critical PWM use

Important behavior difference:

- `rpi-lgpio` follows Linux gpiochip exclusivity rules, so one process claiming a line prevents another process from using it at the same time.
- debounce behavior also changes compared with legacy `RPi.GPIO`.

Implication for the new libraries:

- each `pi5*` driver must own and release its GPIO lines explicitly
- no two drivers should assume they can quietly share the same GPIO pin

#### 2. High-level component control for standalone demos and tools

Recommended base:

- `gpiozero` with explicit `LGPIOFactory`

Why:

- it is well aligned with Raspberry Pi’s current GPIO recommendations
- it is useful for small standalone CLI tools and smoke tests
- it should not be the low-level transport for the production driver internals, but it is useful for examples and validation tooling

#### 3. Remote daemon model similar to `pigpiod`

Recommended base:

- `rgpiod` plus `rgpio`

Why:

- the `lg` project provides a daemon and remote client model that is architecturally closer to `pigpiod`
- it preserves remote GPIO, SPI, I2C, and callback style features for future development if NinjaClawBot later needs network-transparent I/O access

Use in `pi5*` libraries:

- keep optional room for remote backends
- do not make remote daemon mode the default local runtime path

#### 4. SPI and I2C

Recommended base:

- standard Linux device interfaces first
- `spidev` for SPI
- `i2c-dev` via `smbus2` or equivalent for I2C

Reasoning:

- Raspberry Pi 5 still exposes SPI and I2C through stable kernel interfaces
- these interfaces match the hardware model better than trying to rebuild a `pigpio`-style monolithic abstraction
- `lgpio` also exposes SPI and I2C wrappers, but the new standalone libraries should prefer standard kernel device interfaces unless a strong reason appears during implementation

Recommended library mapping:

- `pi5disp`: use SPI kernel device access, not a `pigpio` SPI shim
- `pi5vl53l0x`: use kernel I2C access, not a `pigpio` I2C shim

#### 5. Accurate PWM and servo pulse generation

Recommended base:

- do not use `lgpio` software servo mode for production servo control

Reasoning:

- the `lgpio` documentation explicitly says its servo pulses are software timed, recommended only for testing, and warns that timing jitter will make servos fidget and may cause overheating or premature wear

Production-worthy Pi 5 options:

1. RP1 hardware PWM on PWM-capable header pins for a small number of channels
2. the official `pwm-pio` driver from Raspberry Pi’s PIOLib work when arbitrary header GPIO choice or higher signal stability is needed
3. an external PWM controller such as PCA9685 when many servos are needed or when the pulse generator must be fully decoupled from Linux scheduling

### Replacement recommendation by new library

| New library | Recommended replacement for `pigpio` |
|---|---|
| `pi5buzzer` | `lgpio` or `rpi-lgpio` for simple pin control or PWM, with room to move to Linux PWM if audible stability needs improve |
| `pi5servo` | hardware-backed PWM only: RP1 hardware PWM, `pwm-pio`, or external PWM controller; not `lgpio.tx_servo` in production |
| `pi5disp` | `spidev` plus `lgpio`/`libgpiod` style GPIO control for DC and reset, separate backlight PWM backend |
| `pi5vl53l0x` | kernel I2C via `smbus2` or equivalent |

## GPIO Accuracy Strategy For `pi5servo`

### Key engineering principle

To keep signal accuracy on Pi 5, Python must not be responsible for generating the 50 Hz servo waveform itself.

Python should do:

- angle planning
- calibration mapping
- speed and easing calculations
- command scheduling

The backend should do:

- continuous pulse generation
- pulse width updates
- line ownership
- safe shutdown

This preserves the current `pi0servo` motion logic while moving the time-critical signal generation into hardware or kernel-managed components.

### Why software-timed servo generation is not sufficient

`pigpio` earned its reputation partly because it used DMA-backed timing, which kept GPIO waveforms accurate even when Linux user-space timing fluctuated.

On Pi 5, replacing that with ordinary user-space sleeps or software-timed GPIO toggling would regress servo behavior in several ways:

- visible jitter
- inconsistent endpoints
- multi-servo desynchronization
- increased heating if the servo hunts around the target angle

Because `lgpio` itself warns that software-timed servo pulses are only appropriate for testing, `pi5servo` should not ship with a software-servo backend as the default production path.

### Recommended backend order for `pi5servo`

This ordering is a design recommendation based on the current research.

#### Preferred for highest reliability and scalability

- external PWM controller backend, for example PCA9685 over I2C

Why:

- the pulse train is generated outside Linux user space
- the Raspberry Pi only sends target values over I2C
- this is the most reliable path when the robot needs several servos at once

Inference from sources:

- the PCA9685 is a 16-channel, 12-bit PWM controller accessed over I2C
- because pulse generation is offloaded into dedicated hardware, it is the best fit when we need many simultaneous servo channels and minimal dependence on Linux scheduling jitter

#### Preferred on-board option for a small number of servos

- `pwm-pio` backend

Why:

- Raspberry Pi’s official PIOLib announcement says `pwm-pio` creates a very stable PWM signal on any GPIO on the 40-pin header
- it avoids user-space pulse synthesis
- it preserves more pin flexibility than fixed hardware PWM pins

Constraint:

- the current official implementation exposes up to four PWM interfaces, limited by available PIO state machines

#### Secondary on-board option when the pin map is acceptable

- RP1 hardware PWM backend

Why:

- RP1 has dedicated PWM controllers and an independent PWM clock
- third-party Python wrappers such as `rpi-hardware-pwm` already document Pi 5 channel mappings for GPIO12, GPIO13, GPIO18, and GPIO19

Constraint:

- channel count and pin placement are limited compared with the old `pigpio` arbitrary-pin model

#### Testing-only fallback

- `lgpio` software-servo backend

Policy:

- keep only for bench testing or bring-up if needed
- mark as unsupported for production robot movement
- never make it the default backend

### How to keep pulse accuracy in the new codebase

The new `pi5servo` library should separate motion planning from pulse transport with a backend protocol such as:

- `claim(pin)`
- `set_pulse_us(pin, pulse_width_us)`
- `get_pulse_us(pin)`
- `off(pin)`
- `close()`

Accuracy-preserving implementation rules:

1. Keep calibration and motion planning in microseconds.
   The existing `Servo.angle_to_pulse()` logic should remain the single source of truth for target pulse widths.

2. Update a long-lived pulse generator instead of recreating it.
   The backend should keep PWM active and only change compare or pulse-width values.

3. Use hardware-backed output for the carrier.
   Linux user space should request a new pulse width, but hardware, kernel PWM, PIO, or an external controller should generate the waveform.

4. Batch multi-servo updates by control tick.
   `ServoGroup` should compute a full frame of target pulse widths each motion step, then hand them to the backend together or as tightly grouped writes.

5. Preserve exclusive ownership of active lines.
   Because gpiochip access is exclusive, `pi5servo` must claim pins once and release them once, not open-close them repeatedly during motion.

6. Validate under CPU stress, not just at idle.
   The backend is acceptable only if pulse quality remains stable while the Pi is also doing display updates, sensor reads, and normal application work.

### Recommended validation method for servo signal accuracy

For the `pi5servo` migration, manual validation should include direct signal measurement on Pi 5.

Required validation steps:

- observe pulse width and frame rate with a logic analyser or oscilloscope
- test center, min, and max pulse widths
- test repeated small movements around center to reveal jitter or hunting
- test at idle and under CPU load
- test one-servo and multi-servo cases separately

Acceptance criteria to define during implementation:

- pulse width remains stable enough that the connected servo does not visibly hunt
- commanded pulse changes match expected calibration outputs
- abort and `off()` stop or detach cleanly without stray pulses

## Recommended Production Position

Based on the researched sources, the most reliable path for the new Pi 5 driver family is:

- `pi5buzzer`: `lgpio`-family GPIO control is acceptable
- `pi5disp`: kernel SPI plus GPIO line control is the right replacement
- `pi5vl53l0x`: kernel I2C is the right replacement
- `pi5servo`: use hardware-backed PWM only, and prefer `pwm-pio` or an external PWM controller over software-timed servo generation

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
- keep the native Raspberry Pi GPIO servo path available while leaving room for a later mixed-endpoint refinement

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
- keep the native GPIO shorthand path stable while planning for explicit endpoint ids such as `gpio12` and `hat_pwm1`
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
- implement backend candidates in this order: external PWM controller backend, `pwm-pio` backend, RP1 hardware PWM backend, then testing-only `lgpio` software backend
- keep legacy compatibility methods for future integration work, but do not make `ninja_core` a runtime requirement of the standalone package
- distinguish native GPIO servo outputs from future HAT-managed PWM outputs explicitly in config and command parsing
- treat DFR0566 digital ports as native GPIO breakouts, not as DFR0566 PWM servo channels

Behavioral parity checks:

- same angle-to-pulse mapping
- same duration and easing behavior
- same abort behavior
- same calibration JSON
- same `MultiServo` alias
- same native GPIO numeric shorthand for existing CLI and Python usage until explicit endpoint syntax is introduced

Open technical risk:

- if the chosen Pi 5 backend cannot hold stable multi-pin servo pulses, identical real-world behavior will require a more specialized pulse-generation strategy
- the current integer-only servo identifier model is not sufficient for mixed native GPIO and DFR0566 PWM routing

## DFR0566 Endpoint Model For `pi5servo`

The DFRobot Raspberry Pi IO Expansion HAT DFR0566 must be modeled as two different servo connection families:

1. Native GPIO servo endpoints
   - direct Raspberry Pi header GPIO pins
   - DFR0566 digital ports when they are used only as Raspberry Pi GPIO breakouts
   - these stay on the native Raspberry Pi backend path

2. DFR0566 HAT PWM servo endpoints
   - the four dedicated PWM channels on the HAT
   - these are controlled by the HAT MCU over I2C at the board address, not by direct Raspberry Pi PWM
   - these require a dedicated `dfr0566` backend

Design rules:

- a DFR0566 digital port used for servo signal must still be treated as a native GPIO endpoint
- a DFR0566 PWM port must be treated as a HAT PWM endpoint
- the two endpoint families must not share the same ambiguous integer namespace

Recommended logical endpoint naming for the refinement:

- native GPIO: `gpio12`, `gpio13`, `gpio18`
- HAT PWM: `hat_pwm1`, `hat_pwm2`, `hat_pwm3`, `hat_pwm4`

Backward-compatibility policy:

- existing numeric command targets such as `12:45` remain shorthand for native GPIO during the transition
- new mixed-backend support should use explicit endpoint syntax such as `gpio12:45/hat_pwm1:-30`

Recommended config direction:

- move from plain `int -> calibration` assumptions toward endpoint-aware servo records
- keep legacy numeric keys readable for native GPIO-only setups
- add endpoint metadata so calibration and backend selection are tied to the same logical servo

## Affected `pi5servo` Functions For Endpoint Refinement

The following functions and modules were reviewed and will need adaptation when the explicit endpoint split is implemented.

Backend selection and backend creation:

- [create_servo_backend](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/backend.py)
  - currently selects one backend by name for a whole servo or group
  - must gain `dfr0566` support and coexist cleanly with native GPIO backends

Single-servo construction:

- [Servo.__init__](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/servo.py)
  - currently stores one integer `pin` or identifier
  - must accept or derive an endpoint identity without conflating GPIO numbers and HAT PWM channels

Multi-servo routing:

- [ServoGroup.__init__](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/multi_servos.py#L30)
- [ServoGroup._resolve_backend](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/multi_servos.py#L74)
- [ServoGroup._resolve_targets](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/multi_servos.py#L343)
  - currently assume one shared backend and one integer-indexed pin list
  - must be refactored for backend routing across native GPIO and HAT PWM endpoints

Parser and command model:

- [ServoTarget](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/parser/command.py#L16)
- [ParsedCommand](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/parser/command.py#L35)
- [parse_command](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/parser/command.py#L50)
  - currently parse only numeric targets
  - must support endpoint-aware tokens such as `gpio12` and `hat_pwm1`

CLI creation helpers:

- [parse_pin_list](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/_common.py#L30)
- [create_servo_from_config](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/_common.py#L170)
- [create_group_from_config](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/_common.py#L206)
  - currently build servos and groups from integer pin lists only
  - must be extended to resolve endpoint-aware config and mixed backend group creation

Configuration model:

- [ConfigManager.load](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py#L63)
- [ConfigManager.get_calibration](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py#L118)
- [ConfigManager.set_calibration](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py#L141)
- [ConfigManager.get_all_calibrations](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py#L158)
  - currently assume integer keys for servo data
  - must be adapted for endpoint-aware servo records while remaining backward-compatible for native GPIO-only configs

CLI commands that will inherit the endpoint change:

- [cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/cmd.py)
- [move.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/move.py)
- [calib.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/calib.py)
- [status.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/status.py)
- [servo_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/servo_tool.py)
  - all of these currently present integer GPIO-centric UX
  - each must explicitly distinguish native GPIO and HAT PWM endpoints after the refinement

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

## Rebuilt `ninjaclawbot` Integration Layer

The first `ninjaclawbot` implementation should be treated as rejected design work, not as the base for future fixes.

Reason for reset:

- it mixed raw `pi5*` driver assumptions directly into the integration layer
- it did not preserve the legacy `ninja_core` movement model closely enough
- it introduced asset and CLI behavior that diverged from the real operator workflow
- it still required install and execution habits centered on the `ninjaclawbot` subfolder instead of the project root

Refined direction:

- keep the working standalone Pi 5 drivers:
  - `pi5servo`
  - `pi5disp`
  - `pi5buzzer`
  - `pi5vl53l0x`
- delete the current `ninjaclawbot` implementation internals
- rebuild `ninjaclawbot` as a clean integration layer with the same package name
- move the canonical install and run flow to the repository root through a real `uv` workspace

Purpose of the rebuilt `ninjaclawbot`:

- provide the single robot-control integration layer for NinjaClawBot
- consolidate the `pi5*` libraries behind validated adapters instead of exposing raw driver objects
- replace the old role spread across `ninja_core`, `ninja_agent`, and legacy wrappers
- become the only robot-facing control surface for external AI assistants such as OpenClaw
- remain fully usable for direct human operation without any AI assistant present
- return detailed execution results after every action

Non-negotiable design rules:

- external callers must call `ninjaclawbot`, not `pi5*` drivers directly
- `pi5*` libraries must continue to work the same way in standalone mode
- the repository root must become the primary install and runtime entrypoint
- the rebuilt layer must not depend on legacy `ninja_core` at runtime
- legacy `ninja_core` and `ninja_utils` remain behavior references only
- no arbitrary Python code execution path is allowed

Legacy sources that must guide the rebuild:

- `NinjaRobotV5_bak/ninja_core/src/ninja_core/movement_cli.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/movement_controller.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/dispatcher.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/web_server.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/facial_expressions.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/robot_sound.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/perception.py`
- `NinjaRobotV5_bak/ninja_utils/src/ninja_utils/interfaces.py`

Target responsibility split inside the rebuilt `ninjaclawbot`:

- workspace and package boundary
  - project-root installation and execution
  - workspace ownership of local `pi5*` package wiring
- config and migration layer
  - root-owned robot config
  - legacy config import helpers
  - asset migration helpers for old movement definitions
- driver adapter layer
  - one adapter per `pi5*` library
  - normalize health checks, lifecycle, and result shapes
- runtime and lock layer
  - compose and own live devices
  - enforce exclusive robot-action execution
  - initialize only the devices required for the requested tool or action
  - define startup, post-action reset, and shutdown policy
- capability layer
  - movement
  - expression rendering
  - sound playback
  - display rendering
  - distance sensing
- asset layer
  - validated movement assets
  - validated expression assets
  - shared load/save schema used by both tools and executor
- execution layer
  - typed action requests
  - typed action results
  - bounded execution and rollback hints
  - cancellation and `stop_all` handling
  - optional event/log sink for UI or future transports without exposing raw drivers
- interactive tooling layer
  - movement authoring
  - expression authoring
  - manual robot control and preview flows

Legacy behaviors that must be preserved in the rebuild:

- movement steps are stored as structured data, not raw free-form command strings
- movement authoring supports full-step completion using previous servo positions
- movement editing supports edit, insert, delete, preview, save, and abort
- servo-centered startup and exit behavior exists where a tool depends on active PWM priming
- calibration and config-changing actions rebuild live state, not only on-disk files
- composite actions can perform a deterministic post-action reset, such as center servos or return the face to idle

Legacy behaviors that are explicitly out of scope for the first rebuilt integration pass:

- the old `SafeExecutor` arbitrary Python execution model
- BLE transport wiring from `ninja_ble`
- ngrok startup and QR display boot flow
- the old FastAPI/websocket server transport

Those can be reconsidered later as separate transport layers that call `ninjaclawbot`, but they should not shape the first rebuild.

Required result contract for every robot action:

- `status`
- `action`
- `request_id`
- `started_at`
- `ended_at`
- `duration_ms`
- `devices_used`
- `data`
- `warnings`
- `error_code`
- `error_message`
- `rollback_hint`

The rebuilt result schema replaces the old `dispatcher` and `SafeExecutor` style of broad wrapper behavior with one narrow, typed robot-action boundary.

## Interactive Tool Strategy For Rebuilt `ninjaclawbot`

The rebuilt integration layer must provide interactive tools, but those tools must now be treated as asset authors and safe manual operators, not as ad hoc command shells.

Required tool scope:

- movement authoring and editing
  - create named movement sequences
  - edit and delete movement steps
  - preview movements safely
  - save validated movement assets
- expression authoring and editing
  - create named display and sound expressions
  - preview sound-only, display-only, or combined expressions
  - save validated expression assets
- manual robot control
  - invoke saved movements and expressions directly
  - run health checks
  - run bounded manual servo/display/sound tests when explicitly allowed
- external AI reuse
  - the same saved movement and expression assets must be callable through named `ninjaclawbot` actions
  - OpenClaw should request `perform_movement`, `perform_expression`, `health_check`, or other typed actions instead of constructing raw driver commands

Critical refinement from the legacy audit:

- the movement tool must follow the behavior model of `ninja_core.movement_cli`, not the first `ninjaclawbot` prototype
- saved movement steps must use a structured schema modeled after the legacy format:
  - `speed`
  - `moves`
  - optional `per_servo_speeds`
- the tool must center or safely reinitialize servos where required by the legacy flow
- calibration and config changes must rebuild live movement state, not only reload files

Asset rules:

- movement assets and expression assets must be saved under a root-owned data path, not tied to one transient package session
- the non-interactive executor and the interactive tools must read the same schema
- invalid shorthand or malformed endpoints must be rejected at save time, not only at execution time
- assets must support future AI invocation without needing translation layers outside `ninjaclawbot`
- movement assets must preserve enough information for edit, insert, preview, and loop execution without lossy conversion
- a legacy movement import path should exist for old `config.movements` data so users are not forced to recreate every asset by hand

Recommended asset layout:

- `ninjaclawbot_data/movements/`
- `ninjaclawbot_data/expressions/`
- optional versioned schemas for future migrations

## Phased `ninjaclawbot` Rebuild Plan

### Phase 1: Root Workspace And Reset Boundary

Objective:

- make the repository root the canonical install and run location
- reserve the `ninjaclawbot` package name but remove the current broken integration internals

Files and modules likely to change:

- new root `pyproject.toml`
- new root `uv.lock`
- `ninjaclawbot/pyproject.toml`
- delete and replace the current implementation under `ninjaclawbot/src/ninjaclawbot/`
- delete and replace the current tests under `ninjaclawbot/tests/`

Key requirements to preserve or define:

- `uv sync --extra dev` works from the project root
- `uv run ...` works from the project root
- standalone `pi5*` usage remains unchanged
- current `ninjaclawbot` internals are removed cleanly before new logic is added
- the root workspace does not force users into the `ninjaclawbot` subfolder for install or execution

Lint, test, and validation gate:

- `python -m compileall .`
- `ruff check .`
- `ruff format --check .`
- `pytest -q`

Hardware risk level:

- low

Documentation updates required:

- `developmentPlan.md`
- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

### Phase 2: Minimal Package Scaffold And Typed External Contract

Objective:

- create the clean `ninjaclawbot` package shell
- freeze the external action/result contract before wiring real devices

Files and modules likely to change:

- `ninjaclawbot/src/ninjaclawbot/__init__.py`
- `ninjaclawbot/src/ninjaclawbot/actions.py`
- `ninjaclawbot/src/ninjaclawbot/results.py`
- `ninjaclawbot/src/ninjaclawbot/errors.py`
- `ninjaclawbot/tests/test_actions.py`
- `ninjaclawbot/tests/test_results.py`

Key requirements to preserve or define:

- typed action request model
- typed action result model
- no raw-driver object exposure
- explicit room for named movement and named expression actions
- explicit config model for root-owned robot settings and data-path discovery
- explicit action-cancellation and `stop_all` result semantics

Lint, test, and validation gate:

- `python -m compileall .`
- `ruff check .`
- `ruff format --check .`
- `pytest -q`

Hardware risk level:

- low

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

### Phase 3: Driver Adapter Layer And Runtime Ownership

Objective:

- rebuild runtime composition through explicit adapters around `pi5servo`, `pi5disp`, `pi5buzzer`, and `pi5vl53l0x`
- normalize health checks, lifecycle, and ownership before adding higher-level behavior

Files and modules likely to change:

- `ninjaclawbot/src/ninjaclawbot/adapters/servo.py`
- `ninjaclawbot/src/ninjaclawbot/adapters/display.py`
- `ninjaclawbot/src/ninjaclawbot/adapters/sound.py`
- `ninjaclawbot/src/ninjaclawbot/adapters/distance.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/src/ninjaclawbot/config.py`
- `ninjaclawbot/src/ninjaclawbot/locks.py`
- `ninjaclawbot/tests/test_runtime.py`
- `ninjaclawbot/tests/test_adapters.py`

Key requirements to preserve or define:

- deterministic device init and shutdown
- explicit, driver-correct health reporting
- exclusive robot-action execution lock
- no direct external access to live `pi5*` device objects
- selective device ownership so movement-only tools do not initialize unnecessary hardware
- deterministic startup and post-action reset hooks modeled after the legacy startup/center/idle flow

Lint, test, and validation gate:

- `python -m compileall .`
- `ruff check .`
- `ruff format --check .`
- `pytest -q`

Hardware risk level:

- medium

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

### Phase 4: Asset Schemas And Storage

Objective:

- rebuild movement and expression asset storage around validated schemas before rebuilding the tools

Files and modules likely to change:

- `ninjaclawbot/src/ninjaclawbot/assets/movements.py`
- `ninjaclawbot/src/ninjaclawbot/assets/expressions.py`
- `ninjaclawbot/src/ninjaclawbot/assets/schema.py`
- `ninjaclawbot/tests/test_movement_assets.py`
- `ninjaclawbot/tests/test_expression_assets.py`

Key requirements to preserve or define:

- movement step schema aligned to legacy `movement_cli` and `MovementController`
- expression schema aligned to future combined sound/display behavior
- save-time validation of endpoint names and command structure
- asset storage under project-root data directories
- import path for legacy movement data stored inside old `config.json`
- migration notes for any incompatible schema introduced by the rebuild

Lint, test, and validation gate:

- `python -m compileall .`
- `ruff check .`
- `ruff format --check .`
- `pytest -q`

Hardware risk level:

- low

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

### Phase 5: Movement Capability And Interactive Movement Tool

Objective:

- rebuild movement execution and the movement authoring tool using the legacy `ninja_core` movement behavior as the reference

Files and modules likely to change:

- `ninjaclawbot/src/ninjaclawbot/movement.py`
- `ninjaclawbot/src/ninjaclawbot/capabilities/servo.py`
- `ninjaclawbot/src/ninjaclawbot/cli/movement_tool.py`
- `ninjaclawbot/tests/test_movement.py`
- `ninjaclawbot/tests/test_movement_tool.py`

Key requirements to preserve or define:

- named movement execution modeled after legacy `MovementController`
- structured steps with `speed`, `moves`, and optional `per_servo_speeds`
- safe preview and edit workflow
- config and calibration refresh behavior modeled after the old movement tool
- edit, insert, delete, preview, save, abort, and reset-to-previous-position flows modeled after the old movement CLI
- interruption handling for long-running movement previews and executions

Lint, test, and validation gate:

- `python -m compileall .`
- `ruff check .`
- `ruff format --check .`
- `pytest -q`

Hardware risk level:

- high

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

### Phase 6: Expression Capability And Interactive Expression Tool

Objective:

- rebuild named robot expressions on top of the new runtime and asset layer

Files and modules likely to change:

- `ninjaclawbot/src/ninjaclawbot/expressions.py`
- `ninjaclawbot/src/ninjaclawbot/capabilities/display.py`
- `ninjaclawbot/src/ninjaclawbot/capabilities/sound.py`
- `ninjaclawbot/src/ninjaclawbot/cli/expression_tool.py`
- `ninjaclawbot/tests/test_expressions.py`
- `ninjaclawbot/tests/test_expression_tool.py`

Key requirements to preserve or define:

- create and edit named expressions
- preview sound-only, display-only, or combined expressions safely
- reuse the same saved definitions for manual operators and external AI callers

Lint, test, and validation gate:

- `python -m compileall .`
- `ruff check .`
- `ruff format --check .`
- `pytest -q`

Hardware risk level:

- medium-high

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

### Phase 7: Action Executor And External AI Hook

Objective:

- rebuild the single validated execution boundary used by OpenClaw and any future external assistant

Files and modules likely to change:

- `ninjaclawbot/src/ninjaclawbot/executor.py`
- `ninjaclawbot/src/ninjaclawbot/schemas.py`
- `ninjaclawbot/src/ninjaclawbot/__main__.py`
- `ninjaclawbot/tests/test_executor.py`
- `ninjaclawbot/tests/test_schemas.py`

Key requirements to preserve or define:

- explicit robot actions such as:
  - `move_servos`
  - `perform_movement`
  - `show_expression`
  - `perform_expression`
  - `display_text`
  - `play_sound`
  - `read_distance`
  - `health_check`
  - `stop_all`
- structured results returned after every action
- no arbitrary code execution path
- OpenClaw consumes `ninjaclawbot` only, not raw drivers
- optional event/log sink for future UI transports without rebuilding the executor contract
- clear distinction between one-shot action results and streaming status updates

Lint, test, and validation gate:

- `python -m compileall .`
- `ruff check .`
- `ruff format --check .`
- `pytest -q`

Hardware risk level:

- high

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

### Phase 8: Raspberry Pi 5 End-To-End Validation For The Rebuilt Integration Layer

Objective:

- validate the rebuilt `ninjaclawbot` stack on Raspberry Pi 5 hardware before external-AI adoption

Files and modules likely to change:

- validation notes and test fixtures as needed
- documentation only if code remains stable

Key requirements to preserve or define:

- saved movement assets execute correctly
- saved expression assets execute correctly
- manual tools and external action execution use the same asset definitions
- the rebuilt integration layer reports detailed outcomes for success, warnings, and failures

Lint, test, and validation gate:

- `python -m compileall .`
- `ruff check .`
- `ruff format --check .`
- `pytest -q`

Hardware risk level:

- very high

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

Expected Raspberry Pi validation coverage for the rebuilt layer:

- safe smoke tests
  - root workspace install
  - root CLI `--help`
  - runtime init
  - driver availability report
- device communication tests
  - buzzer, display, distance sensor, and servo readiness through adapters
- actuator-moving tests
  - single-servo move
  - named movement execution
  - named expression preview
  - combined expression plus movement run where mechanically safe
  - same-session movement editing, preview, and save flow
  - cancellation and `stop_all` behavior during a long-running motion or preview
- power-risk tests
  - servo external power and common ground
  - stop-all behavior
  - controlled shutdown after partial failures

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

Driver migration order is complete. The remaining implementation order is now:

1. confirm standalone `pi5servo` stability on Raspberry Pi 5 after the interactive-tool fixes
2. create the root workspace and reset boundary for `ninjaclawbot`
3. rebuild the `ninjaclawbot` contract and adapter/runtime layers
4. rebuild movement assets and the movement tool against legacy `ninja_core` behavior
5. rebuild expression assets and the expression tool
6. rebuild the external AI execution hook for OpenClaw
7. complete Raspberry Pi 5 end-to-end validation for the rebuilt integration layer

Reasoning:

- the standalone Pi 5 drivers are already the stable base and should not be reworked first
- `pi5servo` is the most safety-critical driver and must stay confirmed before integration reset work begins
- the broken first `ninjaclawbot` implementation should be discarded before any new integration logic is layered on top
- movement and expression tooling must be rebuilt after the runtime and schema foundation exists

## References

- [Raspberry Pi: GPIO on Raspberry Pi 5 and similar devices](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-on-raspberry-pi-5-and-similar-devices)
- [Raspberry Pi GPIO best-practices whitepaper PDF](https://pip-assets.raspberrypi.com/categories/685-whitepapers-app-notes-compliance-guides/documents/RP-006553-WP/A-history-of-GPIO-usage-on-Raspberry-Pi-devices-and-current-best-practices)
- [Raspberry Pi RP1 peripherals datasheet](https://datasheets.raspberrypi.com/rp1/rp1-peripherals.pdf)
- [Raspberry Pi PIOLib announcement with `pwm-pio`](https://www.raspberrypi.com/news/piolib-a-userspace-library-for-pio-control/)
- [gpiozero pin factory documentation](https://gpiozero.readthedocs.io/en/stable/api_pins.html)
- [gpiozero `LGPIOFactory` API](https://gpiozero.readthedocs.io/en/stable/api_pins.html#gpiozero.pins.lgpio.LGPIOFactory)
- [lgpio package index](https://pypi.org/project/lgpio/)
- [lgpio servo timing warning](https://lg.raspberrybasic.org/rgpio.html#tx_servo)
- [rpi-lgpio package index](https://pypi.org/project/rpi-lgpio/)
- [rpi-lgpio changelog](https://rpi-lgpio.readthedocs.io/en/latest/changelog.html)
- [rpi-lgpio API differences](https://rpi-lgpio.readthedocs.io/en/latest/differences.html)
- [rgpiod and rgpio overview](https://github.com/joan2937/lg)
- [NXP PCA9685 product page](https://www.nxp.com/products/power-drivers/lighting-driver-and-controller-ics/led-drivers/16-channel-12-bit-pwm-fm-plus-ic-bus-led-driver:PCA9685)
- [rpi-hardware-pwm package index](https://pypi.org/project/rpi-hardware-pwm/)
- [DFRobot DFR0566 wiki docs](https://wiki.dfrobot.com/dfr0566/#docs)
- [DFRobot DFR0566 tech specs](https://wiki.dfrobot.com/dfr0566/#tech_specs)
- [DFRobot Raspberry Pi Expansion Board library](https://github.com/DFRobot/DFRobot_RaspberryPi_Expansion_Board)

## Current Status

This document started as the original migration audit and driver migration plan. The standalone `pi5*` driver libraries now exist and are the accepted hardware-control base for the project.

Current accepted status:

- `pi5buzzer` exists
- `pi5vl53l0x` exists
- `pi5disp` exists
- `pi5servo` exists
- `pi5servo` now includes the DFR0566 endpoint work and the interactive-tool fixes for same-session calibration and Quick Move behavior

Current rejected status:

- the first `ninjaclawbot` implementation is not the accepted base for future work
- it should be treated as disposable integration-prototype code
- the integration layer will be rebuilt from a clean scaffold while preserving the working `pi5*` drivers

Next implementation focus:

- finish documenting and preserving the reset plan for the integration layer
- keep `pi5*` drivers as stable standalone libraries
- rebuild `ninjaclawbot` from scratch as the only approved integration hook for future OpenClaw access
