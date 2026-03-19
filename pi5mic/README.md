# pi5mic

`pi5mic` is the standalone-first microphone library for the NinjaClawBot workspace.

It now provides a real preview voice-input path with:

- local microphone capture
- `whisper.cpp` as the default STT backend
- Gemini as the optional fallback STT backend
- a guided `setup` wizard and `mic-tool` menu
- a manual `run` flow for both `standalone` and `openclaw` profiles
- OpenClaw handoff through the supported `openclaw agent --json` CLI
- plugin-owned NinjaClawBot presence updates through `ninjaclawbot.presence.set`

## Current Scope

Implemented now:

- `mic.json` config rooted in the current working directory by default
- microphone device discovery using `sounddevice`
- bounded WAV capture
- listener state tracking and cooldown protection
- optional Porcupine wake-word wrapper
- `whisper.cpp` batch transcription
- Gemini batch transcription
- guided `setup`, `install whispercpp`, `doctor`, `status`, `run`, and `mic-tool`
- OpenClaw profile support with explicit session and delivery policy

Still not complete:

- always-on wake-word daemon behavior on Raspberry Pi
- direct Gateway RPC transport backend
- long-run Raspberry Pi validation for the new voice path

## Install

From the workspace root:

```bash
cd /Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code\ library/NinjaClawbot
uv sync --extra dev
```

If your platform needs PortAudio system libraries for `sounddevice`, install those first.

Optional extras:

- Gemini backend: `uv sync --extra dev --extra gemini`
- Porcupine wake word: `uv sync --extra dev --extra wakeword`

## First Run

Recommended guided path:

```bash
cd /Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code\ library/NinjaClawbot
uv run pi5mic mic-tool
```

Direct guided path:

```bash
uv run pi5mic setup
uv run pi5mic doctor
uv run pi5mic run --once
```

## Main Commands

Show help:

```bash
uv run pi5mic --help
```

List microphones:

```bash
uv run pi5mic devices
```

Register an existing `whisper.cpp` install:

```bash
uv run pi5mic install whispercpp --model-path ~/.local/share/pi5mic/models/ggml-base.bin
```

Run the guided setup wizard:

```bash
uv run pi5mic setup
```

Check local readiness:

```bash
uv run pi5mic doctor
uv run pi5mic status
```

Run one voice cycle:

```bash
uv run pi5mic run --once
```

Use an existing clip:

```bash
uv run pi5mic run --once --audio-file ./sample.wav
```

## Profiles

`standalone`

- record locally
- transcribe locally
- print the transcript locally

`openclaw`

- record locally
- transcribe locally
- send transcript to OpenClaw through the `openclaw` CLI
- print the final reply locally
- optionally request robot presence changes through the OpenClaw plugin

Important:

- the current integrated path is manual/guided, not a validated always-on voice daemon yet
- `delivery_mode` defaults to `local_only`
- outbound channel delivery must be configured explicitly

## Config Notes

By default, `pi5mic` looks for `mic.json` in the current working directory. You can override that path with `--config-file`.

Secrets do not belong in `mic.json`.

Use environment variables instead:

- `GOOGLE_API_KEY` or `GEMINI_API_KEY` for Gemini
- `OPENCLAW_GATEWAY_TOKEN` or `OPENCLAW_GATEWAY_PASSWORD` for remote OpenClaw gateways
- Picovoice access key only if you enable Porcupine later

## Validation

Package-local checks:

```bash
cd /Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code\ library/NinjaClawbot/pi5mic
uv run --extra dev python -m compileall src tests
uv run --extra dev ruff check src tests
uv run --extra dev ruff format --check src tests
uv run --extra dev pytest -q tests -c pyproject.toml
```
