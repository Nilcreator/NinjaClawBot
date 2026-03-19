# NinjaClawBot Development Guide

<div align="center">

**Developer Reference for the Final Validated NinjaClawBot Build**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Workspace](https://img.shields.io/badge/workspace-uv-blue.svg)](https://docs.astral.sh/uv/)
[![Platform: Raspberry Pi 5](https://img.shields.io/badge/platform-Raspberry%20Pi%205-red.svg)](https://www.raspberrypi.com/)
[![OpenClaw Ready](https://img.shields.io/badge/OpenClaw-ready-0F766E.svg)](https://docs.openclaw.ai/)

[Project README](README.md) | [Installation Guide](InstallationGuide.md) | [Archive](backup/README.md)

</div>

---

## Contents

- [Project summary](#project-summary)
- [Repository map](#repository-map)
- [Complete file structure](#complete-file-structure)
- [Library guides](#library-guides)
- [Validated runtime model](#validated-runtime-model)
- [ninjaclawbot package map](#ninjaclawbot-package-map)
- [OpenClaw plugin map](#openclaw-plugin-map)
- [Action surface](#action-surface)
- [Main commands](#main-commands)
- [Runtime files](#runtime-files)
- [Development workflow](#development-workflow)
- [Validation gates](#validation-gates)
- [Raspberry Pi validation](#raspberry-pi-validation)
- [Troubleshooting shortcuts](#troubleshooting-shortcuts)

## Project Summary

This repository contains the full NinjaClawBot software workspace.

Think of it in three layers:

1. standalone Raspberry Pi 5 hardware libraries
2. the integrated robot layer `ninjaclawbot`
3. the OpenClaw integration layer

If you only need a hardware driver, open the matching library README first.
If you need the full robot behavior, start from `ninjaclawbot`.
If you need chat-driven behavior, start from the OpenClaw plugin and the root installation guide.

## Repository Map

Top-level folders you will work with most often:

- [ninjaclawbot](ninjaclawbot): integrated robot package
- [pi5servo](pi5servo): servo driver and calibration tooling
- [pi5disp](pi5disp): display driver and display tooling
- [pi5buzzer](pi5buzzer): buzzer driver and sound tooling
- [pi5mic](pi5mic): microphone capture, STT, and OpenClaw handoff tooling
- [pi5vl53l0x](pi5vl53l0x): distance sensor driver and sensor tooling
- [integrations/openclaw/ninjaclawbot-plugin](integrations/openclaw/ninjaclawbot-plugin): official OpenClaw plugin
- [ninjaclawbot_data](ninjaclawbot_data): saved movement and expression assets
- [InstallationGuide.md](InstallationGuide.md): end-user deployment guide
- [README.md](README.md): project introduction
- [backup/README.md](backup/README.md): archived plans and logs

Root workspace facts:

- the root `pyproject.toml` installs the whole workspace in one step
- `uv sync --extra dev` from the repository root is the normal install path
- root tests cover all Python libraries together

## Complete File Structure

This is the current development-facing repository layout for the final validated build.

Generated folders such as local virtual environments, `node_modules`, cache folders, and other machine-local artifacts are intentionally left out here so the structure stays useful for real development work.

```text
NinjaClawBot/
├── AGENTS.md
├── README.md
├── DevelopmentGuide.md
├── InstallationGuide.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── conftest.py
├── src/
│   └── ninjaclawbot_workspace/
│       └── __init__.py
├── .agents/
│   └── skills/
│       ├── ninjaclawbot-implementation/
│       │   └── SKILL.md
│       ├── pi-validation/
│       │   └── SKILL.md
│       └── project-documentation/
│           └── SKILL.md
├── backup/
│   ├── README.md
│   ├── DevelopmentLog.md
│   ├── EnhancementPlan.md
│   └── developmentPlan.md
├── ninjaclawbot/
│   ├── LICENSE
│   ├── README.md
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── ninjaclawbot_data/
│   │   ├── expressions/
│   │   └── movements/
│   ├── src/
│   │   └── ninjaclawbot/
│   │       ├── __init__.py
│   │       ├── __main__.py
│   │       ├── actions.py
│   │       ├── adapters.py
│   │       ├── assets.py
│   │       ├── config.py
│   │       ├── errors.py
│   │       ├── executor.py
│   │       ├── locks.py
│   │       ├── presence.py
│   │       ├── results.py
│   │       ├── runtime.py
│   │       ├── cli/
│   │       │   ├── __init__.py
│   │       │   ├── common.py
│   │       │   ├── expression_tool.py
│   │       │   └── movement_tool.py
│   │       ├── expressions/
│   │       │   ├── __init__.py
│   │       │   ├── catalog.py
│   │       │   ├── faces.py
│   │       │   ├── player.py
│   │       │   ├── policy.py
│   │       │   └── sounds.py
│   │       └── openclaw/
│   │           ├── __init__.py
│   │           ├── bridge.py
│   │           └── service.py
│   └── tests/
│       ├── test_actions.py
│       ├── test_adapters.py
│       ├── test_assets.py
│       ├── test_cli_tools.py
│       ├── test_dependency_imports.py
│       ├── test_executor.py
│       ├── test_expressions.py
│       ├── test_openclaw_bridge.py
│       ├── test_policy.py
│       ├── test_repo_hygiene.py
│       ├── test_results.py
│       └── test_runtime.py
├── ninjaclawbot_data/
│   ├── expressions/
│   └── movements/
├── pi5servo/
│   ├── LICENSE
│   ├── README.md
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── src/
│   │   └── pi5servo/
│   │       ├── __init__.py
│   │       ├── __main__.py
│   │       ├── driver.py
│   │       ├── cli/
│   │       ├── config/
│   │       ├── core/
│   │       ├── motion/
│   │       └── parser/
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_backend.py
│       ├── test_cli.py
│       ├── test_config.py
│       ├── test_core.py
│       ├── test_motion.py
│       ├── test_parser.py
│       └── test_servo_tool.py
├── pi5disp/
│   ├── LICENSE
│   ├── README.md
│   ├── display.json
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── src/
│   │   └── pi5disp/
│   │       ├── __init__.py
│   │       ├── __main__.py
│   │       ├── cli/
│   │       ├── config/
│   │       ├── core/
│   │       ├── effects/
│   │       └── fonts/
│   └── tests/
│       ├── conftest.py
│       ├── test_cli.py
│       ├── test_config.py
│       ├── test_display_tool.py
│       ├── test_driver.py
│       ├── test_renderer.py
│       ├── test_smoke.py
│       └── test_text_ticker.py
├── pi5buzzer/
│   ├── LICENSE
│   ├── README.md
│   ├── pyproject.toml
│   ├── src/
│   │   └── pi5buzzer/
│   │       ├── __init__.py
│   │       ├── __main__.py
│   │       ├── driver.py
│   │       ├── notes.py
│   │       ├── cli/
│   │       ├── config/
│   │       └── core/
│   └── tests/
│       ├── conftest.py
│       ├── test_config.py
│       ├── test_driver.py
│       └── test_music.py
├── pi5vl53l0x/
│   ├── LICENSE
│   ├── README.md
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── src/
│   │   └── pi5vl53l0x/
│   │       ├── __init__.py
│   │       ├── __main__.py
│   │       ├── driver.py
│   │       ├── registers.py
│   │       ├── cli/
│   │       ├── config/
│   │       └── core/
│   └── tests/
│       ├── test_cli.py
│       ├── test_config.py
│       ├── test_i2c.py
│       └── test_sensor.py
├── pi5mic/
│   ├── LICENSE
│   ├── README.md
│   ├── pyproject.toml
│   ├── src/
│   │   └── pi5mic/
│   │       ├── __init__.py
│   │       ├── __main__.py
│   │       ├── driver.py
│   │       ├── cli/
│   │       ├── config/
│   │       ├── core/
│   │       ├── install/
│   │       ├── integration/
│   │       ├── stt/
│   │       ├── transport/
│   │       ├── vad/
│   │       └── wakeword/
│   └── tests/
│       ├── test_cli.py
│       ├── test_config.py
│       ├── test_doctor.py
│       ├── test_listener.py
│       ├── test_mic_tool.py
│       ├── test_recorder.py
│       ├── test_stt_gemini.py
│       ├── test_stt_whisper_cpp.py
│       ├── test_transport_openclaw.py
│       ├── test_vad.py
│       └── test_wakeword.py
└── integrations/
    └── openclaw/
        └── ninjaclawbot-plugin/
            ├── openclaw.plugin.json
            ├── package.json
            ├── package-lock.json
            ├── tsconfig.json
            ├── src/
            │   ├── index.ts
            │   ├── runner.ts
            │   └── schemas.ts
            ├── tests/
            │   ├── index.test.ts
            │   └── runner.test.ts
            └── skills/
                └── ninjaclawbot_control/
                    └── SKILL.md
```

## Library Guides

Use these first if you are touching one hardware area only:

- Servo: [pi5servo/README.md](pi5servo/README.md)
- Display: [pi5disp/README.md](pi5disp/README.md)
- Buzzer: [pi5buzzer/README.md](pi5buzzer/README.md)
- Distance sensor: [pi5vl53l0x/README.md](pi5vl53l0x/README.md)
- Microphone: [pi5mic/README.md](pi5mic/README.md)
- Integrated robot layer: [ninjaclawbot/README.md](ninjaclawbot/README.md)

What each README is best for:

- `pi5servo`: endpoint model, calibration, backend selection, safe movement testing
- `pi5disp`: display wiring, brightness, rotation, `display-tool`, and config export
- `pi5buzzer`: buzzer initialization, tones, emotion sounds, `buzzer-tool`
- `pi5vl53l0x`: I2C checks, calibration, `sensor-tool`
- `pi5mic`: microphone setup, `whisper.cpp` default STT, optional Gemini, `run`, and `mic-tool`
- `ninjaclawbot`: integrated commands, assets, OpenClaw-facing usage

## Validated Runtime Model

The final validated build is hybrid. That matters for future development.

### What owns what

- Standalone driver libraries own direct hardware behavior
- `pi5mic` owns local microphone capture, STT selection, and the preview OpenClaw voice handoff
- `ninjaclawbot` owns runtime composition, assets, expressions, and structured actions
- the OpenClaw plugin owns the persistent bridge and the operator-facing tool surface
- startup greeting is validated through:
  - OpenClaw internal `boot-md`
  - workspace `BOOT.md`
- reply reliability is validated through:
  - workspace `AGENTS.md`
  - enabled `ninjaclawbot_control` skill
  - tool allowlist in `openclaw.json`
- shutdown is validated through the plugin-managed persistent bridge

### What this means in practice

- do not assume the Python service `startup_sequence()` is the only startup path
- do not assume `pi5mic` is already an always-on validated voice daemon; the current build is a guided preview path
- do not assume plugin config alone makes replies work
- when debugging reply behavior, always check:
  - allowlist
  - skill
  - workspace `AGENTS.md`
- when debugging startup greeting, always check:
  - `boot-md`
  - workspace `BOOT.md`
  - `ninjaclawbot_diagnostics`

## ninjaclawbot Package Map

Main source folder:

- [ninjaclawbot/src/ninjaclawbot](ninjaclawbot/src/ninjaclawbot)

Important modules:

- [actions.py](ninjaclawbot/src/ninjaclawbot/actions.py)
  - stable machine action names
  - request validation
  - required parameter checks
- [executor.py](ninjaclawbot/src/ninjaclawbot/executor.py)
  - dispatches validated actions into runtime operations
- [runtime.py](ninjaclawbot/src/ninjaclawbot/runtime.py)
  - owns adapters, lifecycle cleanup, and runtime state
- [adapters.py](ninjaclawbot/src/ninjaclawbot/adapters.py)
  - bridges `ninjaclawbot` to the standalone `pi5*` libraries
- [assets.py](ninjaclawbot/src/ninjaclawbot/assets.py)
  - saved movement and expression asset loading
- [presence.py](ninjaclawbot/src/ninjaclawbot/presence.py)
  - persistent presence modes: `idle`, `thinking`, `listening`
- [locks.py](ninjaclawbot/src/ninjaclawbot/locks.py)
  - runtime execution locking and overlap protection
- [config.py](ninjaclawbot/src/ninjaclawbot/config.py)
  - root-level config paths and runtime path resolution
- [results.py](ninjaclawbot/src/ninjaclawbot/results.py)
  - structured action results
- [errors.py](ninjaclawbot/src/ninjaclawbot/errors.py)
  - typed runtime and validation errors

### CLI modules

- [__main__.py](ninjaclawbot/src/ninjaclawbot/__main__.py)
  - main CLI entrypoint
  - commands such as `health-check`, `perform-reply`, `run-action`, `openclaw-serve`
- [cli/common.py](ninjaclawbot/src/ninjaclawbot/cli/common.py)
  - shared CLI helpers
- [cli/expression_tool.py](ninjaclawbot/src/ninjaclawbot/cli/expression_tool.py)
  - interactive expression preview and management
- [cli/movement_tool.py](ninjaclawbot/src/ninjaclawbot/cli/movement_tool.py)
  - interactive movement preview and management

### Expression system

- [expressions/catalog.py](ninjaclawbot/src/ninjaclawbot/expressions/catalog.py)
  - built-in expression definitions
- [expressions/faces.py](ninjaclawbot/src/ninjaclawbot/expressions/faces.py)
  - built-in face frames
- [expressions/sounds.py](ninjaclawbot/src/ninjaclawbot/expressions/sounds.py)
  - built-in sound patterns
- [expressions/policy.py](ninjaclawbot/src/ninjaclawbot/expressions/policy.py)
  - reply-state mapping such as `greeting`, `thinking`, `success`, `error`
- [expressions/player.py](ninjaclawbot/src/ninjaclawbot/expressions/player.py)
  - expression playback, presence mode, idle reset, and shutdown sequencing

### OpenClaw bridge internals

- [openclaw/service.py](ninjaclawbot/src/ninjaclawbot/openclaw/service.py)
  - persistent Python bridge service
  - service-side arbitration and dedupe
- [openclaw/bridge.py](ninjaclawbot/src/ninjaclawbot/openclaw/bridge.py)
  - stdio request/response bridge transport

## OpenClaw Plugin Map

Plugin folder:

- [integrations/openclaw/ninjaclawbot-plugin](integrations/openclaw/ninjaclawbot-plugin)

Important files:

- [src/index.ts](integrations/openclaw/ninjaclawbot-plugin/src/index.ts)
  - registers plugin lifecycle hooks and tool definitions
- [src/runner.ts](integrations/openclaw/ninjaclawbot-plugin/src/runner.ts)
  - bridge management
  - deployment inspection
  - diagnostics generation
- [src/schemas.ts](integrations/openclaw/ninjaclawbot-plugin/src/schemas.ts)
  - tool parameter schemas
- [openclaw.plugin.json](integrations/openclaw/ninjaclawbot-plugin/openclaw.plugin.json)
  - plugin metadata and config schema
- [skills/ninjaclawbot_control/SKILL.md](integrations/openclaw/ninjaclawbot-plugin/skills/ninjaclawbot_control/SKILL.md)
  - OpenClaw skill guidance for tool use

Important rule:

- `ninjaclawbot_reply` animates the robot first
- OpenClaw should still send the normal visible text reply to the user after that tool call

## Action Surface

The machine action surface is defined in [actions.py](ninjaclawbot/src/ninjaclawbot/actions.py).

### Stable action names

- `health_check`
- `list_capabilities`
- `move_servos`
- `perform_movement`
- `perform_reply`
- `display_text`
- `play_sound`
- `show_expression`
- `perform_expression`
- `set_idle`
- `set_presence_mode`
- `stop_expression`
- `shutdown_sequence`
- `read_distance`
- `list_assets`
- `stop_all`

### Required parameters

| Action | Required parameters | Notes |
| --- | --- | --- |
| `move_servos` | `targets` | `per_servo_speeds` is optional; valid speed values are `S`, `M`, `F` |
| `perform_movement` | `name` | runs a saved movement asset |
| `perform_reply` | `text`, `reply_state` | optional `display_text`, `idle_reset`, `sound_enabled` |
| `display_text` | `text` | plain display output |
| `perform_expression` | `name` | saved or built-in expression name |
| `set_presence_mode` | `mode` | valid modes: `idle`, `thinking`, `listening` |
| `list_assets` | none | optional `asset_type`: `all`, `movements`, `expressions` |
| all others above | none | no required parameters |

### Reply states

Canonical reply states currently include:

- `greeting`
- `confirmation`
- `success`
- `speaking`
- `listening`
- `thinking`
- `confusing`
- `asking_clarification`
- `cannot_answer`
- `warning`
- `error`
- `sad`
- `sleepy`
- `curious`

Aliases such as `hello`, `reply`, `done`, and `clarify` are normalized in [expressions/policy.py](ninjaclawbot/src/ninjaclawbot/expressions/policy.py).

## Main Commands

From the project root:

```bash
uv sync --extra dev
uv run ninjaclawbot --help
uv run ninjaclawbot health-check
uv run ninjaclawbot list-capabilities
uv run ninjaclawbot expression-tool
uv run ninjaclawbot movement-tool
uv run ninjaclawbot perform-expression greeting
uv run ninjaclawbot perform-reply --reply-state greeting "Hello"
uv run ninjaclawbot run-action '{"action":"read_distance"}'
```

Standalone library tools:

```bash
uv run pi5servo servo-tool
uv run pi5disp display-tool
uv run pi5buzzer buzzer-tool
uv run pi5vl53l0x sensor-tool
```

Plugin validation:

```bash
cd integrations/openclaw/ninjaclawbot-plugin
npm install
npm run typecheck
npm test
```

## Runtime Files

The normal root-level runtime files are:

- `servo.json`
- `buzzer.json`
- `display.json`
- `vl53l0x.json`
- `ninjaclawbot_data/movements/*.json`
- `ninjaclawbot_data/expressions/*.json`

Important display note:

- `pi5disp` keeps its own package config file
- `ninjaclawbot` prefers the root `display.json`
- after display setup, export the package config into the root file:

```bash
cd ~/NinjaClawBot
uv run pi5disp config export "$PWD/display.json"
```

## Development Workflow

Use this order for normal work:

1. reproduce the problem or confirm the desired behavior
2. identify the correct layer:
   - standalone library
   - integrated `ninjaclawbot`
   - OpenClaw plugin or workspace setup
3. make the smallest safe change
4. run the validation gate
5. update the docs
6. write Pi validation steps if hardware behavior changed

### Which layer to change

- Servo motion issue only:
  - start in [pi5servo/README.md](pi5servo/README.md)
- Display orientation or brightness issue:
  - start in [pi5disp/README.md](pi5disp/README.md)
- Expression composition or reply-state issue:
  - start in `ninjaclawbot`
- OpenClaw startup, Telegram reply, or diagnostics issue:
  - start in the plugin plus workspace/deployment checks

## Validation Gates

Workspace-level Python gate:

```bash
cd /path/to/NinjaClawBot
uv run --extra dev python -m compileall .
uv run --extra dev ruff check .
uv run --extra dev ruff format --check .
uv run pytest -q pi5buzzer/tests -c pi5buzzer/pyproject.toml
uv run pytest -q pi5servo/tests -c pi5servo/pyproject.toml
uv run pytest -q pi5disp/tests -c pi5disp/pyproject.toml
uv run pytest -q pi5vl53l0x/tests -c pi5vl53l0x/pyproject.toml
uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml
```

Why this is written this way:

- this workspace uses sibling package folders such as `pi5buzzer/` and
  `pi5disp/`
- a generic root `pytest -q` can resolve those folders before their `src/`
  packages
- the package-specific pytest commands above are the stable, validated path

Package-level `ninjaclawbot` gate:

```bash
cd /path/to/NinjaClawBot/ninjaclawbot
uv run --extra dev python -m compileall src tests
uv run --extra dev ruff check src tests
uv run --extra dev ruff format --check src tests
uv run --extra dev pytest -q tests -c pyproject.toml
```

Plugin gate:

```bash
cd /path/to/NinjaClawBot/integrations/openclaw/ninjaclawbot-plugin
npm install
npm run typecheck
npm test
```

## Raspberry Pi Validation

Use four buckets whenever hardware-facing behavior changes.

### Safe smoke tests

- `uv run ninjaclawbot health-check`
- `uv run ninjaclawbot expression-tool`
- `uv run pi5disp display-tool`
- `uv run pi5vl53l0x sensor-tool`

### Device communication tests

- `i2cdetect -y 1`
- OpenClaw startup
- `ninjaclawbot_diagnostics`
- Telegram message / reply cycle

### Actuator-moving tests

- `uv run pi5servo servo-tool`
- `uv run ninjaclawbot movement-tool`
- one small known-safe saved movement only

### Power-risk tests

- `openclaw gateway restart`
- `openclaw gateway stop`
- confirm sleepy then display power-down

## Troubleshooting Shortcuts

### `pi5mic` says `PortAudio library not found`

- this is usually a Raspberry Pi system-library issue, not a Python-code issue
- install PortAudio first:

```bash
sudo apt update
sudo apt install -y libportaudio2 portaudio19-dev
```

- then re-run:

```bash
cd ~/NinjaClawBot
uv run pi5mic doctor
```

### `pi5mic` says `Invalid sample rate`

- this usually means the microphone exists, but the saved sample rate in
  `mic.json` does not match what ALSA accepts for that device
- rerun setup and accept the recommended rate:

```bash
cd ~/NinjaClawBot
uv run pi5mic setup
uv run pi5mic doctor
```

- many Raspberry Pi microphones prefer `44100` Hz or `48000` Hz instead of
  `16000` Hz
- the current `pi5mic` build will try to recommend the device default and the
  doctor command may pass with a warning when it can auto-correct safely

### `uv` not found in OpenClaw

- check the absolute path:

```bash
command -v uv
```

- store that path in `plugins.entries.ninjaclawbot.config.uvCommand`

### Display works in `display-tool` but looks wrong in `expression-tool`

- export the display config to the root:

```bash
cd ~/NinjaClawBot
uv run pi5disp config export "$PWD/display.json"
uv run ninjaclawbot health-check
```

### Robot reacts but Telegram shows no text

- check:
  - workspace `AGENTS.md`
  - `ninjaclawbot_control` skill
  - allowlist contains `ninjaclawbot_reply`
- the correct behavior is:
  - robot animation first
  - normal visible text reply after that

### Startup greeting missing

- check:
  - `boot-md` enabled
  - workspace `BOOT.md`
  - `ninjaclawbot_diagnostics`
- on the validated build, trust:
  - `startup.trackingMode`
  - `startup.effectiveCompleted`
  more than the raw service field `startup_completed`

### Best first debugging command

Run this through the OpenClaw gateway:

```bash
curl -sS "http://127.0.0.1:YOUR_GATEWAY_PORT/tools/invoke" \
  -H "Authorization: Bearer YOUR_OPENCLAW_GATEWAY_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "tool": "ninjaclawbot_diagnostics",
    "args": {},
    "sessionKey": "main"
  }' | python3 -m json.tool
```

That one tool gives you:

- bridge health
- service state
- startup interpretation
- deployment readiness
- display config summary
- recovery hints
