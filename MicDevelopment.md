# pi5mic Development Plan

Last updated: 2026-03-20

## 1. Purpose

This document is the current planning and status guide for `pi5mic`.

It now has two jobs:

1. summarize what has already been built and validated for the current
   one-shot microphone workflow
2. define the next implementation plan for the always-on voice input feature

This version replaces the earlier longer planning draft with a more practical
project view:

- overall development goal and product spec
- key features already developed
- what is finished and what still needs improvement
- the recommended always-on design
- the phased implementation plan for the next development cycle

## 2. Overall Development Goal

`pi5mic` is the standalone-first microphone library for the NinjaClawBot
workspace.

The target product is:

- a local Raspberry Pi microphone tool that works by itself
- an optional voice input path for the full NinjaClawBot project
- a clean OpenClaw integration that sends transcript text into the agent
  without adding a second robot-control runtime

The long-term finished user experience should be:

1. install the NinjaClawBot workspace
2. set up the hardware libraries
3. create servo movements in `movement-tool`
4. create expressions in `expression-tool`
5. optionally set up `pi5mic`
6. manually start always-on voice input when needed
7. say the wake word `Ninja`
8. speak a short request
9. let OpenClaw handle the text turn normally
10. receive the reply locally and, when configured safely, in Telegram too

## 3. Product Rules And User Clarifications

These are locked project rules for the next build:

- the spoken transcript must be sent to OpenClaw in the original user language
- `pi5mic` must not auto-translate everything into English
- always-on listening must be started manually for privacy and safety
- the user must be able to stop always-on listening manually
- `pi5mic` remains optional inside NinjaClawBot, but setup should strongly
  recommend it for users who may want USB microphone or mic-module voice input
  later
- OpenClaw must not fail if `pi5mic` is not installed or configured
- Telegram mirroring must stay explicit and target-based, never assumed

## 4. Current Build Status

### 4.1 What is already built

The one-shot voice path is now implemented and usable.

Current implemented features:

- `pi5mic` package scaffold and workspace integration
- standalone CLI commands:
  - `setup`
  - `mic-tool`
  - `doctor`
  - `status`
  - `run --once`
  - `record`
  - `transcribe`
- default local STT backend:
  - `whisper.cpp`
  - multilingual `ggml-base.bin`
- optional cloud STT backend:
  - Gemini batch transcription
- Raspberry Pi microphone hardening:
  - friendlier PortAudio errors
  - safer sample-rate handling
  - safer local Whisper defaults
  - Raspberry Pi health warnings in `doctor`
- OpenClaw integration:
  - CLI and config auto-discovery
  - pairing guidance and repair path
  - plugin-owned presence updates
  - session-id migration fixes
  - explicit local-plus-Telegram reply delivery
- regression coverage for the current CLI and transport flows

### 4.2 What is working today

The current supported mode is:

- one-time capture
- one-time transcription
- one-time dispatch into OpenClaw

This path works in:

- standalone mode
- the integrated NinjaClawBot project

### 4.3 What is not built yet

The following feature is still planned work, not finished work:

- always-on wake-word listening
- continuous background voice loop
- manual start/stop voice-input tool for the always-on path
- optional best-effort voice readiness inside NinjaClawBot health and OpenClaw
  diagnostics

## 5. Audit Summary

The latest repository audit, implementation pass, and external fact check show
that the always-on feature is feasible and now has a first working build, but it
still needs Raspberry Pi tuning and long-run validation.

### 5.1 `pi5mic` audit findings

Important current strengths:

- `pi5mic` already owns the right boundary:
  - microphone capture
  - STT backend selection
  - OpenClaw dispatch
  - OpenClaw presence hooks
- wake-word and VAD building blocks already exist:
  - `wakeword/porcupine.py`
  - `vad/silence.py`
- the request-state machine already exists:
  - `core/listener.py`
- the current transport already supports:
  - OpenClaw dispatch
  - explicit delivery mode
  - explicit reply target

The first implementation pass closed these earlier gaps:

- a live streaming audio loop now exists
- live resampling now adapts microphone frames for Porcupine
- wake-word config is now wired into runtime behavior
- silence timeout is now used by the always-on capture loop
- `voiceinput-tool` now provides manual start/stop/status/log control
- the listener now refuses overlapping voice turns while one is still busy

### 5.2 `ninjaclawbot` audit findings

Important current strengths:

- `ninjaclawbot` already owns robot output cleanly
- robot actions and presence control are stable
- the persistent bridge and OpenClaw service model are already tested

The first implementation pass closed these earlier gaps:

- `ninjaclawbot health-check` now reports optional voice-input readiness
- `ninjaclawbot` now exposes a thin `voiceinput-tool` wrapper
- root and package install docs now include mic-oriented setup guidance

### 5.3 OpenClaw plugin audit findings

Important current strengths:

- the plugin already owns:
  - lifecycle hooks
  - persistent bridge startup
  - presence RPC
  - diagnostics tooling
- the plugin is already the correct place for optional integration diagnostics

Important current constraints:

- the current plugin config name `enableAlwaysOn` still means robot lifecycle
  persistence, not microphone listening
- plugin services still auto-start with the gateway, which is why the
  microphone listener continues to live in `pi5mic`
- the plugin now exposes optional voice-input readiness reporting, but it does
  not and should not auto-start the microphone

### 5.4 External fact-check findings

Checked against upstream docs on 2026-03-20:

- OpenClaw plugin services are background services managed by the gateway, which
  makes them poor default homes for privacy-sensitive microphone capture
- OpenClaw gateway methods are a good fit for optional status/control surfaces
- OpenClaw Voice Wake is a gateway-level global trigger list, not a per-node
  local-microphone system
- OpenClaw Talk Mode uses a continuous listen-think-reply loop and targets the
  main session, which is a useful reference for session strategy
- Picovoice Porcupine supports Raspberry Pi 5 and custom wake words
- Picovoice Cobra is a credible future low-resource VAD upgrade path
- Gemini audio remains batch-oriented, not the main real-time engine

## 6. Key Design Decisions

### 6.1 Where the always-on engine should live

The core always-on engine should live in `pi5mic`, not in `ninjaclawbot` and
not inside the OpenClaw plugin service.

Why:

- `pi5mic` already owns the microphone, STT, and OpenClaw handoff boundary
- `ninjaclawbot` should stay focused on robot output and hardware actions
- the OpenClaw plugin should stay lightweight and optional
- manual start/stop is easier and safer when the listener is a local CLI tool

### 6.2 Where the future `voiceinput-tool` should live

Recommended decision:

- primary implementation: `uv run pi5mic voiceinput-tool`
- optional future convenience alias: `uv run ninjaclawbot voiceinput-tool`

Why:

- `pi5mic` is the real owner of the listener
- a direct `pi5mic` tool keeps the standalone-first design clean
- a thin `ninjaclawbot` alias can be added later if the user experience needs
  it, but it should not be the core implementation

### 6.3 OpenClaw plugin role

The OpenClaw plugin should not auto-start the local microphone listener.

Recommended plugin role:

- detect whether `pi5mic` is installed and configured
- report voice-input readiness in diagnostics
- expose optional voice-input status or recovery guidance if useful
- skip cleanly when `pi5mic` is not configured

### 6.4 Session policy

Current one-shot testing used a dedicated session successfully.

For the always-on feature, the recommended policy is:

- make session behavior configurable
- default always-on voice to the OpenClaw agent main session for smoother
  conversational continuity
- keep dedicated mic-session mode as an advanced option

### 6.5 Wake-word and silence policy

The planned always-on feature should behave like this:

- wake word: `Ninja`
- once triggered, begin capturing the user utterance
- stop capture after:
  - more than 3 seconds of silence
  - or 10 seconds maximum
- send transcript text to OpenClaw in the original input language

### 6.6 Safeguard policy

The system must reject or ignore new triggers while an earlier request is still
being processed.

The safeguard stack should include:

- `MicListener` state gating
- one active request at a time
- ignore wake-word hits while:
  - transcribing
  - dispatching
  - waiting for reply
- short cooldown after completion
- single-instance process lock so users do not accidentally run two listeners at
  once

## 7. Recommended Setup Flow

This is the recommended future setup order for the full project:

1. install the NinjaClawBot workspace libraries
2. set up and initialize:
   - `pi5servo`
   - `pi5vl53l0x`
   - `pi5buzzer`
   - `pi5disp`
   - optional but strongly recommended: `pi5mic`
3. run `movement-tool` to test and create servo movements
4. run `expression-tool` to test and create expressions
5. run `voiceinput-tool` to start always-on voice input manually

Important setup message to add in docs and guided setup:

- `pi5mic` remains optional
- but users who may want voice input later should install and configure it while
  they are already setting up the Raspberry Pi hardware

## 8. Always-On Voice Input Specification

The always-on feature should meet this spec.

### 8.1 Control model

- manual start
- manual stop
- no automatic start on OpenClaw gateway boot
- no automatic start just because the plugin is installed

### 8.2 Listener behavior

- stay idle while waiting for the wake word
- use minimal CPU while armed
- detect `Ninja`
- capture the next utterance
- stop after 3 seconds of silence
- hard-stop after 10 seconds
- recover cleanly after success or failure

### 8.3 Output behavior

- preserve the original spoken language
- do not force English translation
- submit text into OpenClaw
- keep presence updates best-effort
- optionally mirror the final reply to Telegram only when an explicit delivery
  target exists

### 8.4 Skip behavior

If any required voice-input dependency is missing, the system should not crash
the rest of the robot stack.

Expected skip cases:

- `pi5mic` not installed
- `mic.json` missing
- wake-word dependency missing
- missing Picovoice access key
- missing custom keyword file
- STT backend not configured
- OpenClaw not configured

In those cases:

- OpenClaw should skip voice-input enablement
- NinjaClawBot should stay usable
- diagnostics should explain the missing step clearly

## 9. What Has Been Done Already

The following work is complete:

- standalone-first `pi5mic` package created
- workspace dependency integration completed
- `whisper.cpp` selected as default STT backend
- Gemini kept as optional alternative backend
- guided setup and `mic-tool` created
- doctor, status, run, record, and transcribe commands created
- optional `voiceinput` install path added for the wake-word dependency
- always-on config block added to `mic.json`
- always-on streaming loop implemented in `pi5mic/core/voiceinput.py`
- wake-word plus silence-stop capture flow implemented
- manual `voiceinput-tool` added with:
  - status
  - start
  - stop
  - foreground
  - logs
- Raspberry Pi sample-rate, PortAudio, and local Whisper hardening added
- OpenClaw auto-discovery and pairing guidance added
- explicit Telegram reply routing added
- OpenClaw session-id migration fixed
- CLI import and delivery-banner regression fixed
- OpenClaw always-on session-strategy override added
- optional `ninjaclawbot voiceinput-tool` wrapper added
- optional `ninjaclawbot` health-check voice-input readiness reporting added
- OpenClaw plugin voice-input readiness reporting added through diagnostics and
  the `ninjaclawbot_voiceinput_status` tool

## 10. What Still Needs Improvement

The following work is still open:

- long-run Raspberry Pi wake-word validation
- false-positive tuning for the final `Ninja` keyword package
- stronger time-based silence tuning in real room-noise conditions
- optional higher-quality VAD backend
- optional richer OpenClaw agent-side voice orchestration beyond readiness
  reporting
- replacement for Python `audioop` before any future Python 3.13 upgrade
- long-run Raspberry Pi validation for idle listening and repeated turns

## 11. Phased Implementation Plan

### Phase 0: Planning lock and naming cleanup

Status: complete

Objective:

- lock the always-on architecture
- keep the listener in `pi5mic`
- decide final config names
- avoid reusing the plugin’s current `enableAlwaysOn` meaning for microphone
  listening

Likely files:

- `pi5mic/src/pi5mic/config/config_manager.py`
- `pi5mic/src/pi5mic/integration/openclaw_session.py`
- `pi5mic/src/pi5mic/transport/openclaw_cli.py`
- `integrations/openclaw/ninjaclawbot-plugin/openclaw.plugin.json`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`

Validation:

- Python compile and test gates for `pi5mic`
- TypeScript tests and typecheck for the plugin

Risk level:

- low

### Phase 1: Always-on core audio loop

Status: complete

Objective:

- add a long-running streaming input loop
- validate supported input settings
- resample or adapt frames for Porcupine
- keep microphone resource usage stable on Raspberry Pi

Likely files:

- `pi5mic/src/pi5mic/core/recorder.py`
- new streaming/orchestration modules under `pi5mic/src/pi5mic/core/`
- `pi5mic/src/pi5mic/models.py`

Validation:

- new unit tests for streaming behavior
- Raspberry Pi smoke tests with a real microphone

Risk level:

- medium

### Phase 2: Wake word, silence stop, and safeguard flow

Status: complete

Objective:

- wire `PorcupineWakeWordDetector` into the live loop
- use silence-based stop behavior with a 3-second window
- enforce the 10-second maximum
- prevent overlapping requests while OpenClaw is still processing

Likely files:

- `pi5mic/src/pi5mic/wakeword/porcupine.py`
- `pi5mic/src/pi5mic/vad/silence.py`
- `pi5mic/src/pi5mic/core/listener.py`
- `pi5mic/src/pi5mic/core/session.py`

Validation:

- unit tests for busy-state behavior
- manual Pi wake-word and silence-stop tests

Risk level:

- medium

### Phase 3: `voiceinput-tool` and guided operator UX

Status: complete

Objective:

- add the manual start/stop always-on tool
- extend setup, doctor, and status so users can configure wake-word dependencies
  clearly
- make the manual stop path obvious

Likely files:

- `pi5mic/src/pi5mic/__main__.py`
- `pi5mic/src/pi5mic/cli/setup_cmd.py`
- `pi5mic/src/pi5mic/cli/doctor.py`
- `pi5mic/src/pi5mic/cli/status.py`
- `pi5mic/src/pi5mic/cli/mic_tool.py`
- new CLI modules for the always-on tool

Validation:

- CLI regression tests
- Raspberry Pi manual tool-start and tool-stop validation

Risk level:

- low to medium

### Phase 4: OpenClaw session and delivery refinement

Status: complete

Objective:

- support a cleaner session strategy for always-on voice
- preserve original-language transcript dispatch
- keep dual local plus Telegram reply support when explicitly configured

Likely files:

- `pi5mic/src/pi5mic/transport/openclaw_cli.py`
- `pi5mic/src/pi5mic/integration/openclaw_setup.py`
- `pi5mic/src/pi5mic/integration/delivery.py`

Validation:

- transport tests
- OpenClaw local round-trip tests
- Telegram mirror tests when configured

Risk level:

- low

### Phase 5: Optional NinjaClawBot and plugin integration

Status: in progress

Objective:

- integrate `pi5mic` into the recommended project setup flow
- add optional voice readiness detection
- make OpenClaw skip voice enablement automatically when `pi5mic` is not ready

Likely files:

- `ninjaclawbot/src/ninjaclawbot/config.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/src/ninjaclawbot/__main__.py`
- `ninjaclawbot/README.md`
- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
- `integrations/openclaw/ninjaclawbot-plugin/openclaw.plugin.json`

Validation:

- Python tests for optional mic readiness
- plugin typecheck and tests
- integration checks with and without `mic.json`

Risk level:

- low

### Phase 6: Final Raspberry Pi validation and tuning

Status: planned

Objective:

- validate idle listening
- validate wake-word false positives
- validate silence stop and busy protection
- validate OpenClaw reply behavior
- validate power and thermal stability

Validation:

- repeated real-device tests on Raspberry Pi 5
- long-run idle listening
- repeated wake-word cycles

Risk level:

- medium

## 12. Quality Gates

Every implementation phase should pass:

- `python3 -m compileall .`
- `ruff check .`
- `ruff format --check .`
- `pytest -q`

For plugin phases, also run:

- `npm run typecheck`
- `npm test`

## 13. Raspberry Pi Validation Categories

Always separate validation into:

- safe smoke tests
- communication/interface tests
- actuator-moving tests
- power-risk and long-run tests

Current actuator note:

- the core always-on microphone loop should not move hardware by itself
- motion-triggered voice commands must only be tested after non-moving voice
  turns are stable

## 14. Final Recommendation Before Coding

The recommended implementation direction is:

- keep the always-on engine in `pi5mic`
- keep `pi5mic` optional but recommended in the full project setup
- add a manual `voiceinput-tool` first
- do not auto-start the microphone from the OpenClaw plugin
- use OpenClaw integration only when `pi5mic` is actually installed and
  configured
- preserve original-language transcript dispatch
- keep explicit delivery rules for Telegram

This is the most practical and reliable path for the current repository.

## 15. References

Repository inputs reviewed:

- `pi5mic/src/pi5mic/config/config_manager.py`
- `pi5mic/src/pi5mic/core/listener.py`
- `pi5mic/src/pi5mic/core/recorder.py`
- `pi5mic/src/pi5mic/wakeword/porcupine.py`
- `pi5mic/src/pi5mic/vad/silence.py`
- `pi5mic/src/pi5mic/stt/whisper_cpp.py`
- `pi5mic/src/pi5mic/stt/gemini.py`
- `pi5mic/src/pi5mic/transport/openclaw_cli.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/src/ninjaclawbot/openclaw/service.py`
- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
- `integrations/openclaw/ninjaclawbot-plugin/openclaw.plugin.json`

External primary sources checked on 2026-03-20:

- OpenClaw Plugins:
  - https://docs.openclaw.ai/tools/plugin
- OpenClaw Voice Wake:
  - https://docs.openclaw.ai/nodes/voicewake
- OpenClaw Talk Mode:
  - https://docs.openclaw.ai/nodes/talk
- OpenClaw Audio and Voice Notes:
  - https://docs.openclaw.ai/nodes/audio
- OpenClaw agent-send docs:
  - https://github.com/openclaw/openclaw/blob/main/docs/tools/agent-send.md
- Picovoice Porcupine Python Quick Start:
  - https://picovoice.ai/docs/quick-start/porcupine-python/
- Picovoice Porcupine overview:
  - https://picovoice.ai/docs/porcupine/
- Picovoice Cobra Python Quick Start:
  - https://picovoice.ai/docs/quick-start/cobra-python/
