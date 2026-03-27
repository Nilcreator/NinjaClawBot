# NinjaClawBot Development Guide

<div align="center">

**Developer and maintainer reference for the NinjaClawBot workspace**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Workspace](https://img.shields.io/badge/workspace-uv-blue.svg)](https://docs.astral.sh/uv/)
[![Platform: Raspberry Pi 5](https://img.shields.io/badge/platform-Raspberry%20Pi%205-red.svg)](https://www.raspberrypi.com/)
[![OpenClaw Ready](https://img.shields.io/badge/OpenClaw-ready-0F766E.svg)](https://docs.openclaw.ai/)

[Project README](README.md) | [Installation Guide](InstallationGuide.md) | [Archive](backup/README.md)

</div>

---

## Contents

- [Purpose And Audience](#purpose-and-audience)
- [Project Specification](#project-specification)
- [Architecture At A Glance](#architecture-at-a-glance)
- [Repository And Package Map](#repository-and-package-map)
- [Curated Structure](#curated-structure)
- [Ownership And Runtime Boundaries](#ownership-and-runtime-boundaries)
- [Main Runtime Flows](#main-runtime-flows)
- [Public Surfaces](#public-surfaces)
- [Configuration And Runtime Files](#configuration-and-runtime-files)
- [Development Workflow](#development-workflow)
- [Validation Matrix](#validation-matrix)
- [Raspberry Pi Validation Model](#raspberry-pi-validation-model)
- [Maintenance And Extension Guidelines](#maintenance-and-extension-guidelines)
- [Bug Triage Map](#bug-triage-map)
- [Troubleshooting Shortcuts](#troubleshooting-shortcuts)

## Purpose And Audience

This document is for developers and maintainers.

Use it when you need to:

- understand the repository layout
- choose the correct package or layer for a fix
- locate the main command and API surfaces
- validate a change safely
- diagnose integration issues between the hardware libraries, `ninjaclawbot`, and OpenClaw

Use other docs when your goal is different:

- start with [README.md](README.md) for a project introduction
- start with [InstallationGuide.md](InstallationGuide.md) for a full Raspberry Pi build
- start with the package README in `pi5camera`, `pi5servo`, `pi5disp`, `pi5buzzer`, `pi5mic`, `pi5vl53l0x`, or `ninjaclawbot` if you are only touching one package

## Project Specification

The current repository targets this validated direction:

| Area | Current expectation |
| --- | --- |
| Development host | macOS or similar desktop environment |
| Deployment target | Raspberry Pi 5 |
| Python | 3.11+ |
| Workspace manager | `uv` |
| Robot runtime | `ninjaclawbot` |
| Hardware packages | `pi5camera`, `pi5servo`, `pi5disp`, `pi5buzzer`, `pi5mic`, `pi5vl53l0x` |
| Chat integration | OpenClaw plugin + workspace `BOOT.md` / `AGENTS.md` |
| Voice input | `pi5mic`, manual start, optional always-on listener |

Important design rules:

1. Each `pi5*` library should be usable and testable on its own.
2. `ninjaclawbot` composes the libraries into one robot runtime.
3. The OpenClaw plugin owns the bridge and chat-facing tool layer.
4. `pi5mic` owns microphone capture, STT selection, and the optional always-on voice-input loop.
5. Voice input is manual-start for safety and privacy. It is not an automatic background service by default.

## Architecture At A Glance

```mermaid
flowchart LR
    USER["User / Telegram / Local CLI"] --> OC["OpenClaw Gateway"]
    USER --> CAMCLI["pi5camera CLI / camera-tool"]
    USER --> MIC["pi5mic CLI / voiceinput-tool"]
    MIC --> STT["STT backend<br/>whisper.cpp or Gemini"]
    STT --> OC
    OC --> PLUGIN["OpenClaw plugin<br/>ninjaclawbot-plugin"]
    PLUGIN --> BRIDGE["Persistent bridge"]
    BRIDGE --> CORE["ninjaclawbot runtime"]
    CORE --> SERVO["pi5servo"]
    CORE --> CAMERA["pi5camera"]
    CORE --> DISP["pi5disp"]
    CORE --> BUZZER["pi5buzzer"]
    CORE --> SENSOR["pi5vl53l0x"]
    CORE --> PRES["robot presence / expressions"]
```

Think of the system as three layers:

1. **Standalone hardware libraries**
   Each `pi5*` package owns direct device interaction and its own setup/testing tool.

2. **Integrated robot layer**
   `ninjaclawbot` composes the packages into actions, expressions, movements, and persistent robot presence.

3. **OpenClaw integration layer**
   The plugin exposes robot tools to the OpenClaw gateway and keeps the bridge healthy during chat-driven operation.

## Repository And Package Map

| Path | Role | First place to look |
| --- | --- | --- |
| `README.md` | End-user introduction and navigation | New users |
| `InstallationGuide.md` | Full Raspberry Pi and OpenClaw deployment guide | End-to-end build work |
| `DevelopmentGuide.md` | Developer and maintainer reference | Architecture, validation, triage |
| `backup/DevelopmentLog.md` | Chronological change archive | What changed and why |
| `ninjaclawbot/` | Integrated robot runtime | Robot actions, expressions, assets |
| `pi5camera/` | Camera package | Photo capture, recognition, enrollment |
| `pi5servo/` | Servo driver package | Servo issues, calibration, motion |
| `pi5disp/` | Display driver package | Display setup and rendering |
| `pi5buzzer/` | Buzzer driver package | Sound and buzzer behavior |
| `pi5mic/` | Microphone and voice input package | STT, voice flow, OpenClaw voice handoff |
| `pi5vl53l0x/` | Distance sensor package | I2C and range sensing |
| `integrations/openclaw/ninjaclawbot-plugin/` | OpenClaw plugin | Tool exposure, diagnostics, lifecycle hooks |
| `ninjaclawbot_data/` | Saved expressions and movements | Content assets |

## Curated Structure

This is the developer-facing repository shape you will use most often.

```text
NinjaClawBot/
├── README.md
├── InstallationGuide.md
├── DevelopmentGuide.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── backup/
│   ├── README.md
│   └── DevelopmentLog.md
├── ninjaclawbot/
│   ├── README.md
│   ├── pyproject.toml
│   ├── src/ninjaclawbot/
│   │   ├── __main__.py
│   │   ├── actions.py
│   │   ├── adapters.py
│   │   ├── assets.py
│   │   ├── config.py
│   │   ├── executor.py
│   │   ├── presence.py
│   │   ├── runtime.py
│   │   ├── cli/
│   │   ├── expressions/
│   │   └── openclaw/
│   └── tests/
├── pi5camera/
│   ├── README.md
│   ├── src/pi5camera/
│   └── tests/
├── pi5servo/
│   ├── README.md
│   ├── src/pi5servo/
│   └── tests/
├── pi5disp/
│   ├── README.md
│   ├── src/pi5disp/
│   └── tests/
├── pi5buzzer/
│   ├── README.md
│   ├── src/pi5buzzer/
│   └── tests/
├── pi5mic/
│   ├── README.md
│   ├── src/pi5mic/
│   │   ├── __main__.py
│   │   ├── cli/
│   │   ├── config/
│   │   ├── core/
│   │   ├── install/
│   │   ├── integration/
│   │   ├── stt/
│   │   ├── transport/
│   │   ├── vad/
│   │   └── wakeword/
│   └── tests/
├── pi5vl53l0x/
│   ├── README.md
│   ├── src/pi5vl53l0x/
│   └── tests/
├── ninjaclawbot_data/
│   ├── expressions/
│   └── movements/
└── integrations/openclaw/ninjaclawbot-plugin/
    ├── openclaw.plugin.json
    ├── src/
    └── tests/
```

## Ownership And Runtime Boundaries

| Layer | Owns | Does not own |
| --- | --- | --- |
| `pi5servo` | Servo endpoints, calibration, movement hardware behavior | High-level robot conversation logic |
| `pi5camera` | Still capture, recognition backend selection, pending unknown-face storage, local enrollment | Main text-chat bridge ownership |
| `pi5disp` | Display driver, display config, display rendering | Reply policy or Telegram flow |
| `pi5buzzer` | Tone generation and buzzer playback | OpenClaw bridge behavior |
| `pi5vl53l0x` | Distance sensor access and sensor diagnostics | Robot expression policy |
| `pi5mic` | Recording, STT, OpenClaw voice handoff, always-on listener | Main text-chat bridge ownership |
| `ninjaclawbot` | Integrated actions, expressions, asset playback, persistent idle/listening/thinking states | Direct microphone streaming loop |
| OpenClaw plugin | Lifecycle hooks, bridge startup, tool registration, diagnostics | Hardware drivers themselves |

Important practical rules:

- If only one hardware module is wrong, start in the matching `pi5*` package.
- If an action or expression is wrong, start in `ninjaclawbot`.
- If the robot behaves correctly locally but not through chat, start in the OpenClaw plugin and deployment files.
- If the microphone records correctly but voice-to-OpenClaw flow is wrong, start in `pi5mic`, not in the plugin.

## Main Runtime Flows

### Local hardware tool flow

1. A package CLI such as `pi5servo servo-tool` or `pi5disp display-tool` loads its package config.
2. The tool calls package-local driver and core modules.
3. The tool saves or exports package config and assets.
4. `ninjaclawbot` later reuses that config or those assets.

### Local integrated robot flow

1. `uv run ninjaclawbot ...` enters `ninjaclawbot/src/ninjaclawbot/__main__.py`.
2. CLI helpers build an executor from the root project directory.
3. `ActionRequest` validates the action name and parameters.
4. `executor.py` dispatches to the runtime.
5. `runtime.py` calls the standalone packages through adapters.

### OpenClaw text flow

1. A user sends a message through Telegram or another OpenClaw channel.
2. OpenClaw selects the NinjaClawBot tool path.
3. The plugin forwards the tool call through the persistent bridge.
4. `ninjaclawbot` animates the robot and returns structured output.
5. OpenClaw still sends the normal visible text reply after the robot action.

### `pi5mic` voice flow

1. `voiceinput-tool` or `run --once` captures audio locally.
2. `pi5mic` sends the audio to `whisper.cpp` or Gemini.
3. `pi5mic` sends the original-language transcript to OpenClaw.
4. OpenClaw replies through the normal agent path.
5. The listener stays single-flight and uses this state sequence:

`LISTENING -> TRANSCRIBING -> DISPATCHING -> WAITING_FOR_REPLY -> COOLDOWN`

During this sequence, new wake words are intentionally ignored so multiple voice requests cannot overlap.

## Public Surfaces

### `ninjaclawbot` CLI

Command source: `ninjaclawbot/src/ninjaclawbot/__main__.py`

| Command | Purpose |
| --- | --- |
| `health-check` | Run an integrated hardware availability check |
| `list-assets` | List saved movement and expression assets |
| `list-capabilities` | Show supported actions, reply states, and asset types |
| `run-action` | Execute a JSON action payload |
| `capture-photo` | Take a normal camera photo and return the saved path |
| `recognize-faces` | Recognize faces from a live capture or existing image |
| `enroll-pending-face` | Save the user-provided name for a previously unknown face |
| `move-servos` | Move servos using `movement-tool` style endpoint syntax |
| `perform-movement` | Run a saved movement asset |
| `perform-reply` | Run the built-in reply-emotion pipeline |
| `perform-expression` | Run a saved or built-in expression |
| `set-idle` | Start the persistent idle expression |
| `stop-expression` | Stop the active expression loop |
| `expression-tool` | Interactive expression creation and preview |
| `movement-tool` | Interactive movement creation and preview |
| `camera-tool` | Wrapper around `pi5camera camera-tool` using the root `camera.json` |
| `voiceinput-tool` | Optional wrapper around `pi5mic voiceinput-tool` |

### `pi5camera` CLI

Command source: `pi5camera/src/pi5camera/__main__.py`

| Command | Purpose |
| --- | --- |
| `setup` | Guided configuration wizard for camera, storage, and recognition |
| `doctor` | Check config, writable directories, and camera/recognition backend readiness |
| `status` | Show current config and readiness summary |
| `capture` | Take one still photo |
| `recognize` | Recognize faces from a fresh capture or existing image |
| `enroll` | Save a known face from an image or a pending recognition |
| `manage-faces` | List and remove enrolled faces |
| `camera-tool` | Guided menu for setup, capture, recognition, and face management |

### `pi5mic` CLI

Command source: `pi5mic/src/pi5mic/__main__.py`

| Command | Purpose |
| --- | --- |
| `devices` | List available microphone input devices |
| `record` | Record a bounded WAV file |
| `transcribe` | Transcribe an existing audio file |
| `run` | Run one configured standalone or OpenClaw microphone cycle |
| `setup` | Guided configuration wizard |
| `doctor` | Check config, microphone readiness, STT, voice-input readiness, and OpenClaw handoff |
| `status` | Show current config and readiness summary |
| `mic-tool` | Guided menu for common setup and testing tasks |
| `voiceinput-tool` | Manual always-on listener controls |
| `install whispercpp` | Register the local `whisper.cpp` backend |
| `install openwakeword` | Register the wake-word model path and runtime assets |
| `config show/export/import` | Manage `mic.json` files |

### Other `pi5*` interactive tools

| Package | Tool | Purpose |
| --- | --- | --- |
| `pi5servo` | `servo-tool` | Servo setup, calibration, safe motion tests |
| `pi5disp` | `display-tool` | Display setup, preview, and config export |
| `pi5buzzer` | `buzzer-tool` | Tone and sound testing |
| `pi5camera` | `camera-tool` | Camera setup, photo capture, face recognition, and enrollment |
| `pi5vl53l0x` | `sensor-tool` | Distance sensor verification |

### Stable robot action surface

Action source: `ninjaclawbot/src/ninjaclawbot/actions.py`

Stable action names:

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
- `capture_photo`
- `recognize_faces`
- `enroll_pending_face`
- `list_assets`
- `stop_all`

Important required parameters:

| Action | Required parameters |
| --- | --- |
| `move_servos` | `targets` |
| `perform_movement` | `name` |
| `perform_reply` | `text`, `reply_state` |
| `display_text` | `text` |
| `perform_expression` | `name` |
| `set_presence_mode` | `mode` |
| `enroll_pending_face` | `recognition_id`, `face_id`, `name` |

### OpenClaw plugin tool surface

Tool source: `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`

| Tool | Purpose |
| --- | --- |
| `ninjaclawbot_reply` | Animate a conversational reply, then let OpenClaw send the visible text reply |
| `ninjaclawbot_perform_expression` | Run a saved or built-in expression |
| `ninjaclawbot_perform_movement` | Run a saved movement asset |
| `ninjaclawbot_move_servos` | Move servos directly |
| `ninjaclawbot_capture_photo` | Take a normal photo and return the absolute saved path |
| `ninjaclawbot_recognize_faces` | Recognize faces and return pending ids for unknown faces |
| `ninjaclawbot_enroll_pending_face` | Save the user-provided name for a previously unknown face |
| `ninjaclawbot_read_distance` | Read the current distance value |
| `ninjaclawbot_health` | Run a hardware health check |
| `ninjaclawbot_voiceinput_status` | Report whether optional `pi5mic` voice input is installed and ready |
| `ninjaclawbot_capabilities` | List supported actions and assets |
| `ninjaclawbot_set_idle` | Start the idle face |
| `ninjaclawbot_diagnostics` | Inspect bridge health and deployment readiness |
| `ninjaclawbot_stop` | Stop the active expression loop |
| `ninjaclawbot_stop_all` | Stop all active robot outputs |

Also exposed:

- gateway method `ninjaclawbot.presence.set` for presence updates used by `pi5mic` and the plugin lifecycle path

## Configuration And Runtime Files

| File | Owner | Purpose |
| --- | --- | --- |
| `pyproject.toml` | root workspace | Installs the whole workspace |
| `uv.lock` | root workspace | Locked dependency graph |
| `servo.json` | root project | Servo runtime config |
| `display.json` | root project | Display config used by `ninjaclawbot` |
| `buzzer.json` | root project | Buzzer runtime config |
| `vl53l0x.json` | root project | Distance sensor config |
| `camera.json` | root project or standalone `pi5camera` directory | Camera, recognition, and storage config |
| `mic.json` | root project or standalone `pi5mic` directory | Microphone, STT, OpenClaw, and voice-input config |
| `photo/` | root project or standalone `pi5camera` directory | Default saved photo directory |
| `camera_data/` | root project or standalone `pi5camera` directory | Known-face index, pending records, and crops |
| `ninjaclawbot_data/movements/*.json` | root project | Saved motion assets |
| `ninjaclawbot_data/expressions/*.json` | root project | Saved expression assets |
| `BOOT.md` | root workspace | Startup greeting and session boot guidance |
| `AGENTS.md` | root workspace | Tool and behavior instructions for OpenClaw/Codex-style agents |
| `~/.openclaw/openclaw.json` | OpenClaw install | Gateway, plugins, skills, allowlist, and deployment config |
| `.pi5mic-voiceinput-state.json` | `pi5mic` runtime | Listener state file |
| `.pi5mic-voiceinput.log` | `pi5mic` runtime | Listener log file |

Important note for display maintenance:

- `pi5disp` stores its own package config
- `ninjaclawbot` prefers the root-level `display.json`
- after display setup, export the package config to the root:

```bash
cd ~/NinjaClawBot
uv run pi5disp config export "$PWD/display.json"
```

## Development Workflow

Use this order for normal development work:

1. reproduce the issue or confirm the desired behavior
2. choose the correct layer
3. make the smallest safe change
4. run the matching validation gate
5. update the docs
6. write Raspberry Pi validation steps if hardware behavior changed

### Which layer to change

| Symptom | Start here |
| --- | --- |
| Servo endpoint or calibration issue | `pi5servo` |
| Display orientation, contrast, or config issue | `pi5disp` |
| Buzzer playback issue | `pi5buzzer` |
| VL53L0X or I2C issue | `pi5vl53l0x` |
| Camera capture, storage, or recognition issue | `pi5camera` |
| Microphone recording, STT, wake-word, or voice dispatch issue | `pi5mic` |
| Expression policy or action orchestration issue | `ninjaclawbot` |
| Chat-driven behavior differs from local behavior | OpenClaw plugin and deployment files |

## Validation Matrix

### Workspace Python gate

Use this from the repository root:

```bash
uv run --extra dev python -m compileall .
uv run --extra dev ruff check .
uv run --extra dev ruff format --check .
uv run pytest -q pi5buzzer/tests -c pi5buzzer/pyproject.toml
uv run pytest -q pi5servo/tests -c pi5servo/pyproject.toml
uv run pytest -q pi5disp/tests -c pi5disp/pyproject.toml
uv run pytest -q pi5vl53l0x/tests -c pi5vl53l0x/pyproject.toml
uv run pytest -q pi5camera/tests -c pi5camera/pyproject.toml
uv run pytest -q pi5mic/tests -c pi5mic/pyproject.toml
uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml
```

Why it is written this way:

- the workspace contains multiple sibling packages
- package-specific pytest commands are the stable validated path
- a generic root `pytest -q` is not the preferred gate for this repo

### Package-level Python gate

Example for one package:

```bash
cd /path/to/NinjaClawBot/pi5mic
uv run --extra dev python -m compileall src tests
uv run --extra dev ruff check src tests
uv run --extra dev ruff format --check src tests
uv run --extra dev pytest -q tests -c pyproject.toml
```

### OpenClaw plugin gate

```bash
cd /path/to/NinjaClawBot/integrations/openclaw/ninjaclawbot-plugin
npm install
npm run typecheck
npm test
```

## Raspberry Pi Validation Model

Use these four buckets whenever hardware-facing behavior changes.

### Safe smoke tests

- `uv run ninjaclawbot health-check`
- `uv run pi5camera doctor`
- `uv run ninjaclawbot capture-photo`
- `uv run ninjaclawbot expression-tool`
- `uv run pi5disp display-tool`
- `uv run pi5vl53l0x sensor-tool`
- `uv run pi5mic doctor`

### Device communication tests

- `i2cdetect -y 1`
- `rpicam-hello --list-cameras`
- microphone device listing
- OpenClaw startup
- `ninjaclawbot_diagnostics`
- Telegram message and reply cycle

### Actuator-moving tests

- `uv run pi5servo servo-tool`
- `uv run ninjaclawbot movement-tool`
- one small known-safe movement only

### Power-risk tests

- `openclaw gateway restart`
- `openclaw gateway stop`
- confirm sleepy face then display power-down
- for voice input, run a repeated wake-word cycle test and watch Pi temperature and throttling

## Maintenance And Extension Guidelines

### Adding a new hardware behavior

1. Put direct device logic in the matching `pi5*` package.
2. Add or update its interactive tool if the new behavior needs setup or manual testing.
3. Only then expose it through `ninjaclawbot` if it belongs in the integrated robot layer.

### Adding a new robot action

1. Add the action to `ActionType` in `ninjaclawbot/src/ninjaclawbot/actions.py`.
2. Define validation rules and required parameters.
3. Teach the executor/runtime how to run it.
4. Add tests.
5. If OpenClaw should call it directly, decide whether a new plugin tool is needed.

### Adding a new OpenClaw tool

1. Confirm the behavior already exists in `ninjaclawbot`.
2. Register the tool in `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`.
3. Add schema support if needed.
4. Update plugin tests and deployment docs.

### Adding a new voice feature

1. Start in `pi5mic`.
2. Keep microphone runtime ownership there.
3. Only add a thin wrapper or status surface in `ninjaclawbot` or the plugin when needed.
4. Avoid turning voice input into an automatic background service without an explicit safety decision.

## Bug Triage Map

| Problem | First check | Likely owner |
| --- | --- | --- |
| Local hardware tool fails | matching package README and package tests | matching `pi5*` package |
| `ninjaclawbot health-check` fails | root config files and adapters | `ninjaclawbot` |
| Camera works in `pi5camera` but not through OpenClaw | `ninjaclawbot` camera actions and plugin tool mapping | `ninjaclawbot` + OpenClaw plugin |
| Robot reacts locally but not through OpenClaw | plugin diagnostics, allowlist, skill, bridge | OpenClaw plugin |
| Telegram text missing but robot motion/expression works | OpenClaw tool usage and reply path | OpenClaw deployment |
| Voice capture works but chat handoff fails | `pi5mic doctor`, `status`, OpenClaw profile | `pi5mic` |
| Wake word works once but not repeatedly | `voiceinput-tool` state, overflow handling, presence timing | `pi5mic` |
| Startup greeting missing | `BOOT.md`, `boot-md`, diagnostics | OpenClaw deployment + plugin |

## Troubleshooting Shortcuts

### `pi5camera` says `Picamera2 is not importable`

This usually means the Raspberry Pi camera stack is incomplete in the active
environment. Common causes are:

- `python3-picamera2` or `python3-libcamera` is missing in the system Python
- the current `.venv` is stale and no longer reflects the system camera stack
- the active `.venv` can import a stale or partial camera package before it
  reaches the healthy Raspberry Pi system copy

The current fix path uses a targeted import finder for Raspberry Pi camera and
recognition modules, so unrelated venv packages such as `Pillow` stay in the
virtual environment.

Fastest recovery for the full workspace:

```bash
cd ~/NinjaClawBot
./scripts/bootstrap-rpi-workspace.sh
```

Standalone `pi5camera` recovery:

```bash
cd ~/pi5camera
./scripts/bootstrap-rpi-standalone.sh
```

Manual fallback if you need to do it step by step:

```bash
cd ~/NinjaClawBot
sudo apt update
sudo apt install -y python3-picamera2 python3-libcamera python3-venv
rm -rf .venv
/usr/bin/python3 -m venv --system-site-packages .venv
source .venv/bin/activate
uv sync --active --extra dev
.venv/bin/python -c "from pi5camera.environment import install_startup_import_hook; raise SystemExit(0 if install_startup_import_hook() else 1)"
uv run pi5camera doctor
```

### `pi5camera` says `face_recognition` is not importable

This means the recognition backend is not usable in the active environment. The
most common Raspberry Pi causes are:

- the Raspberry Pi image does not provide the recognition packages and the
  Python fallback has not been installed yet
- the active `.venv` contains a stale or corrupted compiled extension such as
  `dlib`, which shadows the system package

Fastest recovery for the full workspace:

```bash
cd ~/NinjaClawBot
./scripts/bootstrap-rpi-workspace.sh
```

Standalone `pi5camera` recovery:

```bash
cd ~/pi5camera
./scripts/bootstrap-rpi-standalone.sh
```

Manual fallback if your Raspberry Pi image does not provide
`python3-face-recognition`:

```bash
rm -rf .venv
/usr/bin/python3 -m venv --system-site-packages .venv
source .venv/bin/activate
uv sync --active --extra dev
uv pip install --python .venv/bin/python --reinstall "face-recognition>=1.3"
.venv/bin/python -c "from pi5camera.environment import install_startup_import_hook; raise SystemExit(0 if install_startup_import_hook() else 1)"
uv run python -c "import face_recognition; print('face-recognition-ok')"
uv run pi5camera doctor
```

Note:

- `pi5camera recognize` now checks the recognition backend before it takes a
  live photo, so a broken recognition environment should fail fast instead of
  capturing a new image first.
- if doctor reports `_dlib_pybind11 ... file too short`, treat it as a stale or
  corrupted `.venv` binary and recreate `.venv` from scratch with the bootstrap
  installer

### `pi5mic` says `PortAudio library not found`

Install the Raspberry Pi system packages first:

```bash
sudo apt update
sudo apt install -y libportaudio2 portaudio19-dev
```

Then rerun:

```bash
uv run pi5mic doctor
```

### `pi5mic` says `Invalid sample rate`

The microphone exists, but ALSA does not accept the saved rate in `mic.json`.

Fix path:

```bash
uv run pi5mic setup
uv run pi5mic doctor
```

Accept the sample rate recommended by the wizard. Many Raspberry Pi microphones prefer `44100` Hz or `48000` Hz.

### `pi5mic` says `openwakeword` is missing or the model is not ready

Install the optional dependency and register the model:

```bash
uv sync --extra dev --extra voiceinput
uv run pi5mic install openwakeword --model-path ~/NinjaClawBot/voiceinput/hey_ninja.onnx
uv run pi5mic doctor
```

### `pi5mic` says `pairing required` in OpenClaw mode

Use the guided recovery path first:

```bash
uv run pi5mic setup
```

Choose `Profile: openclaw` and let `pi5mic` auto-discover the OpenClaw settings. Approve the newest local device request when asked.

### `pi5mic` says `Invalid session ID` in OpenClaw mode

Older configs used a legacy `voice:local-mic` session id. Current `pi5mic` migrates that automatically to the safe value `voice-local-mic`.

Safest recovery:

```bash
uv run pi5mic setup
uv run pi5mic doctor
uv run pi5mic run --once
```

### `pi5servo servo-tool` says `Unable to create/write to /sys/class/pwm/pwmchip0/pwm1`

This error usually means the interactive tool tried to reopen the same native PWM
channel inside one session, or the backend hit a stale sysfs PWM node while
claiming a channel.

Current expected behavior:

- if a stale `pwm0` or `pwm1` sysfs node is present, the RP1 hardware PWM
  backend now best-effort unexports that node and retries the claim once
- if a multi-servo startup claims one channel and then fails on a later channel,
  the already-claimed earlier channels are now released during rollback
- if `gpio13` is already part of the live `servo.json` session, `servo-tool`
  now reuses that existing live servo for `Single Move` and `Calibrate`, then
  updates the live group in place instead of rebuilding it on exit
- if the endpoint is not already in the live session, `servo-tool` falls back
  to an isolated temporary servo, suspends the live group for that session, and
  then rebuilds from `servo.json` afterward
- on a normal healthy shutdown, the hardware PWM backend now leaves exported
  sysfs PWM channels in place so the next claim can reuse them instead of
  depending on a fresh export/recreate cycle

Safest recovery:

```bash
cd ~/NinjaClawBot
git pull
uv sync --extra dev
uv run pi5servo servo-tool
```

Then:

- choose `3. Calibrate` for `gpio13` or `13`
- confirm the calibration view opens normally
- return to the main menu and run a small Quick Move command such as `F_gpio13:0`
- if `gpio13` is already present in `servo.json`, it should calibrate in place
  without tearing down the live group first

If it still fails, check:

- `/boot/firmware/config.txt` still contains `dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4`
- `servo.json` still points at the intended backend and pin-channel map
- a standalone direct script can still drive GPIO13 before changing calibration data
- if both `gpio12` and `gpio13` suddenly fail after one bad run, reboot once to
  clear any kernel-level sysfs PWM state before continuing the audit
### Voice listener works once but does not re-arm well

Check:

- `uv run pi5mic doctor`
- `uv run pi5mic voiceinput-tool foreground`
- `.pi5mic-voiceinput.log`

Important current behavior:

- wake words are ignored while the previous request is still busy on purpose
- repeated audio overflow should trigger stream recovery, not permanent failure
- OpenClaw presence issues should degrade to warnings, not block the whole voice loop

### Display works in `display-tool` but looks wrong in `expression-tool`

Export the display package config to the root project file:

```bash
cd ~/NinjaClawBot
uv run pi5disp config export "$PWD/display.json"
uv run ninjaclawbot health-check
```

### Robot reacts but Telegram shows no text

Check:

- workspace `AGENTS.md`
- the `ninjaclawbot_control` skill
- OpenClaw allowlist entries for `ninjaclawbot_reply`

If this only happens on `pi5mic` voice turns, rerun:

```bash
uv run pi5mic status
```

Confirm that a reply target is saved.

### Startup greeting is missing

Check:

- `boot-md` is enabled
- workspace `BOOT.md` exists and contains the intended greeting
- `ninjaclawbot_diagnostics` shows startup tracking as expected

### Best first debugging command

When the bridge is up, start with the OpenClaw diagnostics tool. It usually gives the fastest single view of deployment readiness, bridge health, and recovery hints.
