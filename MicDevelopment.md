# pi5mic Development Plan

Last updated: 2026-03-20

## 1. Purpose

This document is the current planning and status guide for `pi5mic`.

It now has two jobs:

1. summarize what has already been built and validated for the current
   one-shot microphone workflow
2. define the next implementation plan for replacing the current preview
   always-on wake-word backend with `openWakeWord`

This version replaces the earlier longer planning draft with a more practical
project view:

- overall development goal and product spec
- key features already developed
- what is finished and what still needs improvement
- the recommended always-on design
- the phased replacement plan for the next development cycle

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

- final long-run Raspberry Pi validation for always-on wake-word listening
- migration from the current preview Picovoice backend to `openWakeWord`
- full removal of Picovoice-specific packaging, prompts, tests, and docs

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
- live resampling now adapts microphone frames for the active wake-word detector
- wake-word config is now wired into runtime behavior
- silence timeout is now used by the always-on capture loop
- `voiceinput-tool` now provides manual start/stop/status/log control
- the listener now refuses overlapping voice turns while one is still busy

Important replacement findings:

- the abstract `WakeWordDetector` interface is simple and reusable
- the always-on loop can stay largely intact if the detector backend changes
- the main Porcupine coupling is in:
  - `wakeword/porcupine.py`
  - `core/voiceinput.py`
  - `config/config_manager.py`
  - `cli/setup_cmd.py`
  - `cli/doctor.py`
- package extras, tests, and docs are also coupled to Picovoice concepts such
  as:
  - `pvporcupine`
  - `PICOVOICE_ACCESS_KEY`
  - `.ppn` keyword files

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
- `openWakeWord` is the best free noncommercial replacement candidate for
  `pi5mic`
- `openWakeWord` provides:
  - a Python API
  - Raspberry Pi support
  - frame-based streaming detection
  - optional built-in VAD filtering
  - optional noise suppression
- `openWakeWord` does not require a cloud account or paid key
- `openWakeWord` built-in pretrained models do not include `Ninja`, so the
  planned replacement should target a custom `Ninja` model file
- `openWakeWord` code is Apache-2.0, while bundled pretrained models are
  licensed for noncommercial use
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
- long-term wake-word engine target: `openWakeWord`
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
- missing `openWakeWord` package or inference runtime
- missing custom `Ninja` wake-word model file
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
- wake-word backend migrated to `openWakeWord`
- Picovoice code, packaging, prompts, tests, and active setup docs removed
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
- false-positive tuning for the final `Ninja` `openWakeWord` model
- stronger time-based silence tuning in real room-noise conditions
- optional higher-quality VAD backend
- optional richer OpenClaw agent-side voice orchestration beyond readiness
  reporting
- replacement for Python `audioop` before any future Python 3.13 upgrade
- long-run Raspberry Pi validation for idle listening and repeated turns

## 11. Phased Implementation Plan

### 11.1 First-generation always-on preview

Status: implemented

Summary:

- the first-generation always-on preview is already built
- it proved the core `pi5mic` architecture is workable
- it was then migrated to `openWakeWord` for the final free local wake-word path

Completed preview phases:

- planning lock and naming cleanup
- always-on core audio loop
- wake-word, silence-stop, and safeguard flow
- `voiceinput-tool` and guided operator UX
- OpenClaw session and delivery refinement
- optional NinjaClawBot and plugin integration

What this preview gave us:

- proof that the long-running listener belongs in `pi5mic`
- proof that the CLI and OpenClaw session model are viable
- a reusable state machine and streaming loop
- a clear list of Picovoice-specific coupling points to remove

### 11.2 Approved `openWakeWord` replacement plan

Implementation status:

- phases `R0` through `R5` are now complete
- phase `R6` Raspberry Pi field validation and tuning is still open

### Phase R0: Replacement decision and migration lock

Status: complete

Objective:

- lock the wake-word replacement target as `openWakeWord`
- keep the existing always-on listener architecture
- remove Picovoice as an active dependency and operator requirement

Likely files:

- `MicDevelopment.md`
- `pi5mic/src/pi5mic/config/config_manager.py`
- `pi5mic/src/pi5mic/core/voiceinput.py`
- `pi5mic/src/pi5mic/wakeword/base.py`

Validation:

- planning review only

Risk level:

- low

### Phase R1: Packaging and config migration

Status: complete

Objective:

- replace Picovoice install extras with `openwakeword`
- migrate old configs safely
- remove `PICOVOICE_ACCESS_KEY` and `.ppn` assumptions

Likely files:

- `pi5mic/pyproject.toml`
- `pyproject.toml`
- `ninjaclawbot/pyproject.toml`
- `pi5mic/src/pi5mic/config/config_manager.py`

Expected config direction:

- `wakeword.backend`: `openwakeword`
- remove:
  - `wakeword.access_key_env_var`
  - `wakeword.keyword_path`
- add or standardize:
  - `wakeword.model_path`
  - `wakeword.threshold`
  - `wakeword.vad_threshold`
  - `wakeword.enable_noise_suppression`
  - optional `wakeword.inference_framework`

Validation:

- `cd pi5mic && python3 -m compileall src tests`
- `cd pi5mic && uv run --extra dev ruff check src tests`
- `cd pi5mic && uv run --extra dev ruff format --check src tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`
- `uv lock`
- `cd ninjaclawbot && uv lock`

Risk level:

- low

### Phase R2: `openWakeWord` backend implementation

Status: complete

Objective:

- add a native `openWakeWord` detector backend that matches the existing
  `WakeWordDetector` contract
- remove the current Porcupine backend implementation

Likely files:

- new `pi5mic/src/pi5mic/wakeword/openwakeword.py`
- `pi5mic/src/pi5mic/wakeword/base.py`
- `pi5mic/src/pi5mic/wakeword/__init__.py`
- `pi5mic/src/pi5mic/__init__.py`
- delete `pi5mic/src/pi5mic/wakeword/porcupine.py`

Implementation targets:

- use `from openwakeword.model import Model`
- feed 16-bit 16 kHz PCM frames as `numpy.int16`
- target 1280-sample frame chunks for efficient streaming
- use thresholded detection results
- support custom `Ninja` model files

Validation:

- `cd pi5mic && python3 -m compileall src tests`
- `cd pi5mic && uv run --extra dev ruff check src tests`
- `cd pi5mic && uv run --extra dev ruff format --check src tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`

Risk level:

- low

### Phase R3: Always-on loop and CLI migration

Status: complete

Objective:

- wire `openWakeWord` into the existing always-on loop
- keep the current busy protection, silence-stop logic, and OpenClaw dispatch
- remove Picovoice-specific operator prompts and doctor checks

Likely files:

- `pi5mic/src/pi5mic/core/voiceinput.py`
- `pi5mic/src/pi5mic/cli/setup_cmd.py`
- `pi5mic/src/pi5mic/cli/doctor.py`
- `pi5mic/src/pi5mic/cli/status.py`
- `pi5mic/src/pi5mic/cli/voiceinput_tool.py`

Implementation notes:

- keep the existing `MicListener` safeguard behavior
- keep the current 3-second silence stop and 10-second max capture
- replace:
  - AccessKey prompts
  - `.ppn` keyword-file prompts
  - `pvporcupine` readiness checks
- add:
  - custom `openWakeWord` model-path checks
  - inference runtime checks
  - threshold and optional VAD/noise-suppression checks

Validation:

- `cd pi5mic && python3 -m compileall src tests`
- `cd pi5mic && uv run --extra dev ruff check src tests`
- `cd pi5mic && uv run --extra dev ruff format --check src tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`

Risk level:

- medium

### Phase R4: Test-suite replacement

Status: complete

Objective:

- replace Porcupine-specific tests with `openWakeWord` coverage
- verify config migration and failure messaging

Likely files:

- `pi5mic/tests/test_wakeword.py`
- `pi5mic/tests/test_voiceinput.py`
- `pi5mic/tests/test_doctor.py`
- related CLI setup/status tests

Validation:

- `cd pi5mic && python3 -m compileall src tests`
- `cd pi5mic && uv run --extra dev ruff check src tests`
- `cd pi5mic && uv run --extra dev ruff format --check src tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`

Risk level:

- low

### Phase R5: Documentation and repository cleanup

Status: complete

Objective:

- remove Picovoice-specific documentation, prompts, and setup guidance
- document `openWakeWord` as the only supported always-on wake-word path

Likely files:

- `README.md`
- `pi5mic/README.md`
- `InstallationGuide.md`
- `DevelopmentGuide.md`
- `MicDevelopment.md`
- `ninjaclawbot/README.md`
- `backup/DevelopmentLog.md`

Cleanup scope:

- remove references to:
  - Picovoice
  - Porcupine setup
  - `PICOVOICE_ACCESS_KEY`
  - `.ppn` files
- replace them with:
  - `openWakeWord` install guidance
  - custom `Ninja` model guidance
  - standalone and OpenClaw/NinjaClawBot validation steps

Validation:

- `git diff --check`
- plus package-level lint/tests if code changes land in the same phase

Risk level:

- low

### Phase R6: Raspberry Pi validation and tuning

Status: planned

Objective:

- validate `openWakeWord` on Raspberry Pi 5 in real always-on operation
- tune thresholds, false positives, and room-noise behavior
- confirm OpenClaw and Telegram reply behavior still works

Validation:

- safe smoke tests:
  - install the new `voiceinput` extra
  - run `pi5mic setup`
  - run `pi5mic doctor`
  - run `pi5mic voiceinput-tool foreground`
- communication tests:
  - wake-word detection
  - silence stop
  - 10-second max capture
  - original-language OpenClaw handoff
  - optional Telegram mirroring
- power-risk tests:
  - 20 to 30 minute idle armed run
  - repeated wake-word cycles
  - check CPU temperature, throttling, and memory use

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
- openWakeWord GitHub:
  - https://github.com/dscripka/openWakeWord
- openWakeWord `model.py`:
  - https://github.com/dscripka/openWakeWord/blob/main/openwakeword/model.py
- openWakeWord microphone example:
  - https://github.com/dscripka/openWakeWord/blob/main/examples/detect_from_microphone.py
- Home Assistant wake-word article using openWakeWord:
  - https://www.home-assistant.io/blog/2023/10/12/year-of-the-voice-chapter-4-wakewords
