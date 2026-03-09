---
name: ninjaclawbot-implementation
description: Use for substantial NinjaClawBot driver-library work on pi5buzzer, pi5servo, pi5disp, and pi5vl53l0x. Covers standalone-first Pi 5 migration, required repository audit, phased planning with approval before coding, backend selection, mandatory quality gates, Raspberry Pi 5 manual validation after each library, and required documentation updates.
---

# NinjaClawBot Pi 5 Library Workflow

Use this skill for substantial work on the new Pi 5 driver libraries:

- `pi5buzzer`
- `pi5servo`
- `pi5disp`
- `pi5vl53l0x`

This skill is the agentic development guide for the new libraries.

## Core policy

- Treat each `pi5*` package as a standalone library first.
- Do not make `ninja_core` a runtime requirement for the new libraries.
- Preserve optional future integration hooks where cheap and sensible:
  - `driver.py` compatibility re-export entries
  - config-manager entry points
  - stable callable class surfaces
  - compatibility aliases such as `MultiServo`
- Migrate one library at a time.
- Do not begin coding until the user has approved a phased plan.
- Do not move to the next phase until the current phase passes the quality gate.
- After each library migration, produce a manual Raspberry Pi 5 validation gate.

## Required context to load first

Before planning substantial work, review:

- `/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code library/NinjaClawbot/developmentPlan.md`
- `/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code library/NinjaClawbot/README.md`
- `/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code library/NinjaClawbot/DevelopmentGuide.md`
- `/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code library/NinjaClawbot/DevelopmentLog.md`

In `developmentPlan.md`, focus on:

- `Primary Usage Model`
- `Code Audit Summary`
- `Recommended Pi 5 Backend Strategy`
- `Researched Replacement For pigpio On Raspberry Pi 5`
- `GPIO Accuracy Strategy For pi5servo`
- `Phased Migration Plan`
- `Driver-Specific Migration Notes`
- `Quality Gates For Every Future Implementation Phase`
- `Raspberry Pi 5 Validation Plan`

## Required tool order

Follow this order unless the task is trivial.

1. Serena first for repository understanding.
2. Context7 first for third-party library behavior and current package docs.
3. OpenAI docs MCP first for any OpenAI or Codex related behavior.
4. GitHub MCP first if branch, issue, PR, or repo state matters.
5. Web research using primary sources when Pi 5 compatibility or library support may have changed, or when Context7 is insufficient.

For Serena-based repository review, use:

- `activate_project`
- `check_onboarding_performed`
- `initial_instructions`

Then prefer:

- `list_dir`
- `find_file`
- `get_symbols_overview`
- `find_symbol`
- `search_for_pattern`

Use line-by-line file reads only when symbolic review is not enough or when reading markdown, JSON, TOML, or other non-code files.

## Required development workflow

### Step 1: Understand the request

Extract and state:

- target library or libraries
- requested outcome
- target hardware on Raspberry Pi 5
- standalone vs optional future integration scope
- safety risks
- expected output files

If the request is ambiguous and a wrong assumption would be risky, clarify before planning.

### Step 2: Audit the target library before planning

Always audit the legacy source contract before proposing changes.

Required source locations:

- `NinjaRobotV5_bak/pi0buzzer`
- `NinjaRobotV5_bak/pi0servo`
- `NinjaRobotV5_bak/pi0disp`
- `NinjaRobotV5_bak/pi0vl53l0x`

For the selected library, inspect at minimum:

- package `pyproject.toml`
- package `README.md`
- `src/<package>/__init__.py`
- `src/<package>/__main__.py`
- `src/<package>/driver.py` if present
- core driver modules
- config manager
- CLI modules
- tests

If future integration matters, also inspect legacy references in:

- `NinjaRobotV5_bak/ninja_core/src/ninja_core/hal.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/config.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/robot_sound.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/movement_cli.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/movement_controller.py`

Capture:

- public exports
- required classes and methods
- config file names and schemas
- CLI commands
- hardware-facing APIs
- compatibility surfaces that must remain available

### Step 3: Confirm backend strategy before coding

Do not guess the Pi 5 backend.

Use the current migration plan as the default:

- `pi5buzzer`: `lgpio` or `rpi-lgpio` family GPIO/PWM backend is acceptable
- `pi5disp`: kernel SPI (`spidev`) plus GPIO line control, with separate backlight handling
- `pi5vl53l0x`: kernel I2C (`smbus2` or equivalent)
- `pi5servo`: hardware-backed PWM only

For `pi5servo`, backend order is:

1. external PWM controller backend, such as PCA9685
2. `pwm-pio`
3. RP1 hardware PWM
4. `lgpio` software servo mode for testing only, never as the default production backend

If current Pi 5 compatibility or library support may have changed, verify using primary sources before planning.

### Step 4: Produce a phased plan and wait for approval

The plan must be explicit and library-by-library.

For each phase include:

- objective
- exact files and modules likely to change
- required classes or functions to preserve
- backend choice or backend options
- lint and test commands
- manual Raspberry Pi 5 validation required
- hardware risk level
- documentation files to update

Do not code until the user approves the plan.

### Step 5: Implement phase by phase

During implementation:

- keep diffs small and reviewable
- prefer modifying existing code over inventing unrelated new files
- mirror the audited legacy package structure in each `pi5*` package
- keep public behavior stable unless the user approved a change
- isolate transport and hardware access behind backend helpers or adapters

Expected target structure:

- `pi5buzzer/`
- `pi5servo/`
- `pi5disp/`
- `pi5vl53l0x/`

Typical required package files:

- `pyproject.toml`
- `README.md`
- `src/<package>/__init__.py`
- `src/<package>/__main__.py`
- `src/<package>/driver.py` where legacy compatibility expects it
- `src/<package>/core/*`
- `src/<package>/config/*`
- `src/<package>/cli/*`
- `tests/*`

## Required library contracts

Preserve these audited surfaces unless the user explicitly approves a change.

### `pi5buzzer`

Required behavior:

- exports `Buzzer`, `MusicBuzzer`
- keep note and emotion behavior compatible
- preserve queue-based non-blocking playback
- preserve `play_sound`, `queue_pause`, `play_note`, `play_song`, `play_emotion`, `play_demo`, `play_music`
- preserve config with `pin` and `volume`
- preserve CLI workflows

### `pi5servo`

Required behavior:

- exports `Servo`, `ServoCalibration`, `ServoGroup`, `ConfigManager`
- keep `MultiServo = ServoGroup`
- preserve `angle_to_pulse`, `pulse_to_angle`, `get_pulse`, `get_angle`, `set_pulse`, `set_angle`
- preserve `move_all_sync`, `move_all_async`, abort behavior, refresh behavior, and legacy helper methods
- preserve config schema in `servo.json`
- preserve CLI calibration and command workflows

### `pi5disp`

Required behavior:

- export `ST7789V`, `ConfigManager`
- preserve `display`, `display_region`, `clear`, `set_brightness`, `set_rotation`, `sleep`, `wake`, `health_check`, `initialize`, `execute`, `off`
- preserve config wizard and `display.json` style behavior
- preserve fonts, ticker, and CLI workflows
- preserve actual runtime behavior over README claims; note that legacy `display()` is full-frame by default

### `pi5vl53l0x`

Required behavior:

- export `VL53L0X`
- preserve `driver.py` compatibility re-export path
- preserve initialize and retry semantics
- preserve `get_range`, `get_data`, `get_ranges`, `get_range_async`, `set_offset`, `calibrate`, `health_check`, `reinitialize`, `close`
- preserve config and CLI workflows

## Required quality gate after every implementation phase

Do not continue to the next phase until the current phase passes the quality gate.

Prefer repo-defined commands if they exist for the target package.

Default gate:

```bash
python -m compileall .
ruff check .
ruff format --check .
pytest -q
```

If the package or repo already uses typing checks, also run:

```bash
mypy .
```

Preferred execution pattern:

- run package-local tests while porting a single library
- run broader repo checks only when the current task affects shared files

If the gate fails:

- stop
- fix the issue
- rerun the failing checks
- only continue after the phase is clean

## Required Raspberry Pi 5 manual validation after each library

Every migrated library must end its implementation phase with a manual Pi 5 validation checklist.

Each checklist must contain:

- safe smoke tests
- device communication tests
- actuator-moving tests if relevant
- power-risk tests if relevant
- expected outcomes
- rollback steps

### Extra rule for `pi5servo`

For `pi5servo`, signal accuracy is mandatory.

The agent must:

- treat pulse generation as hardware-backed, not Python-timed
- keep motion planning in microseconds
- require direct signal measurement with a logic analyser or oscilloscope when validating accuracy
- test center, min, max, small corrections around center, idle, and CPU-load conditions
- reject software-timed servo output as the default production backend

## Required documentation updates

If implementation changes code, the task is not complete until documentation is reviewed and updated.

Required files:

- `/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code library/NinjaClawbot/README.md`
- `/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code library/NinjaClawbot/DevelopmentGuide.md`
- `/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code library/NinjaClawbot/DevelopmentLog.md`

Update expectations:

- `README.md`: project purpose, driver overview, setup, usage examples
- `DevelopmentGuide.md`: workflow, module layout, backend notes, lint and test commands, Pi validation flow
- `DevelopmentLog.md`: dated summary, files changed, reason, checks run, Pi validation status, follow-up work

If the implementation meaningfully changes the migration strategy, also update:

- `/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code library/NinjaClawbot/developmentPlan.md`

## Final response requirements

At handoff, summarize:

- what changed
- which files were changed
- lint and test outcomes
- what was manually validated on Raspberry Pi 5 and what is still pending
- what docs were updated
- remaining risk
- recommended next step
