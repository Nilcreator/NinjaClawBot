# NinjaClawBot

NinjaClawBot is a Raspberry Pi 5 robot software stack.

It combines:

- standalone Pi 5 hardware libraries
- a high-level robot-control layer called `ninjaclawbot`
- an official OpenClaw plugin and skill wrapper

The project is designed so that:

- each `pi5*` library still works on its own
- `ninjaclawbot` reuses those libraries instead of duplicating driver logic
- external AI assistants such as OpenClaw use the `ninjaclawbot` control boundary instead of calling raw hardware drivers directly

If you want the full install and setup path, read [InstallationGuide.md](InstallationGuide.md).

If you want advanced developer details, read [DevelopmentGuide.md](DevelopmentGuide.md).

## What The Project Contains

### 1. Standalone hardware libraries

- [`pi5buzzer`](pi5buzzer/README.md)
  - passive buzzer control
  - notes, songs, and emotion sounds
- [`pi5servo`](pi5servo/README.md)
  - servo control for Raspberry Pi header PWM, DFR0566 HAT PWM, and optional PCA9685
  - calibration and interactive servo tools
- [`pi5disp`](pi5disp/README.md)
  - ST7789V display control
  - text, images, animation demos, and display tools
- [`pi5vl53l0x`](pi5vl53l0x/README.md)
  - VL53L0X distance sensor support
  - testing and offset calibration

### 2. Integrated robot layer

- [`ninjaclawbot`](ninjaclawbot/README.md)
  - saved movement assets
  - saved expression assets
  - animated face and sound expression engine
  - `movement-tool`
  - `expression-tool`
  - structured action results for external callers

### 3. OpenClaw integration

- `integrations/openclaw/ninjaclawbot-plugin`
  - official OpenClaw plugin
  - official OpenClaw skill wrapper
  - typed `ninjaclawbot_*` tools for robot control

## Project Layout

```text
NinjaClawbot/
├── pyproject.toml
├── uv.lock
├── README.md
├── InstallationGuide.md
├── DevelopmentGuide.md
├── DevelopmentLog.md
├── EnhancementPlan.md
├── developmentPlan.md
├── pi5buzzer/
├── pi5servo/
├── pi5disp/
├── pi5vl53l0x/
├── ninjaclawbot/
├── integrations/
│   └── openclaw/
│       └── ninjaclawbot-plugin/
└── NinjaRobotV5_bak/
```

## How You Install And Run It

The project is **root-first**.

That means:

- install from the project root
- keep shared config files at the project root
- run `uv run ...` commands from the project root

Main install command:

```bash
uv sync --extra dev
```

This installs:

- `ninjaclawbot`
- all `pi5*` libraries
- the development tools used by this project

For the full step-by-step process, including Raspberry Pi setup, hardware interface setup, calibration, and OpenClaw connection, read [InstallationGuide.md](InstallationGuide.md).

For the detailed OpenClaw installation itself, use the linked
`NinjaClawAgent` guide from [InstallationGuide.md](InstallationGuide.md).

`InstallationGuide.md` also includes:

- the shortest interactive-tool-first Raspberry Pi setup path
- commands to find the real NinjaClawBot project root and plugin folder paths
- a safe copy-paste command to patch `~/.openclaw/openclaw.json`
- the validated `BOOT.md` and workspace `AGENTS.md` setup for startup greeting and reply expressions
- an appendix with troubleshooting and alternative commands for each setup stage
- a full reference OpenClaw config template with placeholders
- a local test step that now includes both `expression-tool` and
  `movement-tool`

## What Files Are Created At Runtime

When you use the project from the root, these files are created there:

- `servo.json`
- `buzzer.json`
- `display.json`
- `vl53l0x.json`
- `ninjaclawbot_data/movements/*.json`
- `ninjaclawbot_data/expressions/*.json`

## Main Root Commands

These are the most important root-level commands:

```bash
uv run ninjaclawbot health-check
uv run ninjaclawbot list-assets
uv run ninjaclawbot list-capabilities
uv run ninjaclawbot perform-expression idle
uv run ninjaclawbot perform-reply --reply-state greeting "Hello"
uv run ninjaclawbot set-idle
uv run ninjaclawbot movement-tool
uv run ninjaclawbot expression-tool
```

For the full testing order, read [InstallationGuide.md](InstallationGuide.md).

## How It Works With OpenClaw

OpenClaw should not call the raw `pi5*` driver commands directly.

Instead, the flow is:

```text
OpenClaw agent
  -> NinjaClawBot OpenClaw plugin
  -> plugin-managed persistent ninjaclawbot bridge
  -> ninjaclawbot runtime / action executor
  -> pi5* hardware libraries
```

This gives you:

- one clear robot-control boundary
- one warm runtime reused across OpenClaw tool calls while the gateway is running
- lifecycle-aware robot presence during the OpenClaw gateway session
- service-side arbitration so duplicate low-priority lifecycle updates do not replay forever
- typed JSON-style action results
- safer hardware access
- a shared reply-emotion policy
- a one-shot `openclaw-action` fallback path if the persistent bridge is unavailable

For the exact OpenClaw setup and plugin configuration steps, use
[InstallationGuide.md](InstallationGuide.md).

For troubleshooting or release checks, use the OpenClaw tool
`ninjaclawbot_diagnostics`. It reports:

- persistent bridge health
- degraded or one-shot fallback state
- current service presence mode
- startup and lifecycle state
- deployment readiness hints for `BOOT.md`, `AGENTS.md`, allowlists, and skill enablement

## OpenClaw Examples

### Greeting

OpenClaw can use the `ninjaclawbot_reply` tool with a greeting reply state.

Result:

- the robot shows a greeting face
- the buzzer plays the matching sound
- the robot returns to idle after the greeting

### Clarifying question

OpenClaw can use `reply_state: "asking_clarification"`.

Result:

- the robot shows a confused or thinking-style face
- the reply feels more natural when the agent needs more information

### Successful task completion

OpenClaw can use `reply_state: "success"` after it completes a robot task.

Result:

- the robot shows a more positive completion expression
- the user gets both spoken-style and visual feedback

### Waiting for the next user message

OpenClaw should keep the robot on idle while waiting.

Result:

- the robot looks alive even when it is not actively replying
- temporary expressions do not stay on screen too long

### Always On lifecycle

With the persistent bridge and Always On lifecycle enabled, the plugin now
drives these transitions automatically:

- gateway start:
  - greeting expression
  - then persistent `idle`
- user message received:
  - persistent `thinking`
- explicit final reply:
  - emotion from `ninjaclawbot_reply`
  - then back to `idle`
- gateway stop:
  - `sleepy`
  - display power-down

Operator note:

- `openclaw hooks list --verbose` should show NinjaClawBot lifecycle hooks when
  the plugin is loaded correctly
- after changing plugin or skill behavior, start a fresh chat session so the
  OpenClaw prompt picks up the latest NinjaClawBot skill snapshot
- `ninjaclawbot` now reads the root-level `display.json` file directly instead
  of silently using the package-local `pi5disp` default config
- old clones that still contain tracked `__pycache__` files should update once
  and then keep those files ignored; the repository now ignores Python cache
  artifacts by default

## Recommended Reading Order

If you are new to the project:

1. [InstallationGuide.md](InstallationGuide.md)
2. [`ninjaclawbot/README.md`](ninjaclawbot/README.md)
3. the hardware library README files you actually use

Recommended hardware library docs:

- [`pi5buzzer/README.md`](pi5buzzer/README.md)
- [`pi5servo/README.md`](pi5servo/README.md)
- [`pi5disp/README.md`](pi5disp/README.md)
- [`pi5vl53l0x/README.md`](pi5vl53l0x/README.md)

If you are developing the project:

- [DevelopmentGuide.md](DevelopmentGuide.md)
- [DevelopmentLog.md](DevelopmentLog.md)
- [EnhancementPlan.md](EnhancementPlan.md)
- [developmentPlan.md](developmentPlan.md)

## Current Status

The current stack supports:

- root-level installation
- root-level calibration and testing
- standalone `pi5*` usage
- integrated `ninjaclawbot` usage
- Stage 1 expression engine and expression tool
- Stage 2 persistent bridge, Always On lifecycle hooks, and sleepy shutdown sequence
- Phase 2.4 service-side lifecycle dedupe, root-level display-config loading,
  and repository cache-file hygiene
- Phase 2.5 operator-facing diagnostics, deployment readiness inspection, and
  repository hygiene release checks

The main remaining work is final Raspberry Pi validation and extended recovery
testing on top of the new diagnostics path.
