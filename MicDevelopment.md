# pi5mic Development Plan

## Contents
- [1. What This Document Is For](#1-what-this-document-is-for)
- [2. Simple Word List](#2-simple-word-list)
- [3. Audit Scope And Fact-Check Inputs](#3-audit-scope-and-fact-check-inputs)
- [4. What The Current Codebase Already Supports](#4-what-the-current-codebase-already-supports)
- [5. What Is Missing Today](#5-what-is-missing-today)
- [6. External Fact Check Summary](#6-external-fact-check-summary)
- [7. Feasibility Verdict](#7-feasibility-verdict)
- [8. Recommended pi5mic Package Shape](#8-recommended-pi5mic-package-shape)
- [9. Recommended System Logic](#9-recommended-system-logic)
- [10. Required Safety And Robustness Rules](#10-required-safety-and-robustness-rules)
- [11. Phased Implementation Plan](#11-phased-implementation-plan)
- [12. Quality Gate After Every Phase](#12-quality-gate-after-every-phase)
- [13. Raspberry Pi Validation Plan](#13-raspberry-pi-validation-plan)
- [14. Final Recommendation Before Coding](#14-final-recommendation-before-coding)
- [15. References](#15-references)

## 1. What This Document Is For
This document defines the build plan for a new standalone-first microphone library named `pi5mic` inside the NinjaClawBot workspace.

The target outcome is a voice input path that works in two modes:

- `Standalone mode`: a local CLI workflow centered around `mic-tool`
- `Integrated mode`: capture voice locally, transcribe it, submit it into OpenClaw, and keep NinjaClawBot robot output behavior consistent with the current OpenClaw integration

This revision is not a speculative draft. It was re-audited against:

- the current `ninjaclawbot` Python runtime and bridge code
- the current OpenClaw plugin implementation in this repository
- the current package patterns used by the existing `pi5*` libraries
- upstream OpenClaw and vendor documentation checked on `2026-03-19`

The main purpose of this document is to prevent us from building the wrong thing. The earlier version was directionally good, but it left a few important gaps:

- it assumed a public OpenClaw presence tool was the right external control surface
- it hard-locked Gemini 2.5 Flash too early
- it treated Telegram mirroring as if it were automatically safe
- it did not define session isolation, secret handling, or audio-retention policy clearly enough
- it did not fully account for the fact that current OpenClaw and `ninjaclawbot` already expose some of the pieces we need

No `pi5mic` code is implemented in this document. This is the corrected plan we should follow before implementation starts.

## 2. Simple Word List
Short explanations are included here so the plan stays readable.

- `STT`: speech-to-text
- `Wake word`: the keyword that starts voice capture
- `VAD`: voice activity detection
- `CLI`: command line interface
- `Gateway RPC`: a request sent to the OpenClaw gateway over its documented RPC interface
- `Session key`: the OpenClaw conversation identity that controls memory, queueing, and turn serialization
- `Delivery target`: the explicit chat or channel destination used for an outbound reply
- `Single-flight`: only one active microphone request is allowed at a time
- `Retention`: whether recorded audio is deleted immediately or kept temporarily for debugging

## 3. Audit Scope And Fact-Check Inputs
This revision reviewed the current repository and the external contracts that matter for voice integration.

### 3.1 Local repository inputs reviewed
Planning and workspace docs:

- `MicDevelopment.md`
- `README.md`
- `DevelopmentGuide.md`
- `InstallationGuide.md`
- `backup/developmentPlan.md`
- `backup/DevelopmentLog.md`

Important repository correction:

- the old migration plan is archived at `backup/developmentPlan.md`, not root `developmentPlan.md`
- the development log is archived at `backup/DevelopmentLog.md`, not root `DevelopmentLog.md`

Audited `ninjaclawbot` files:

- `ninjaclawbot/src/ninjaclawbot/config.py`
- `ninjaclawbot/src/ninjaclawbot/actions.py`
- `ninjaclawbot/src/ninjaclawbot/adapters.py`
- `ninjaclawbot/src/ninjaclawbot/executor.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/src/ninjaclawbot/presence.py`
- `ninjaclawbot/src/ninjaclawbot/expressions/player.py`
- `ninjaclawbot/src/ninjaclawbot/openclaw/service.py`
- `ninjaclawbot/src/ninjaclawbot/openclaw/bridge.py`
- `ninjaclawbot/src/ninjaclawbot/__main__.py`

Audited OpenClaw plugin files in this repository:

- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/schemas.ts`
- `integrations/openclaw/ninjaclawbot-plugin/openclaw.plugin.json`
- `integrations/openclaw/ninjaclawbot-plugin/tests/index.test.ts`
- `integrations/openclaw/ninjaclawbot-plugin/tests/runner.test.ts`

Audited existing `pi5*` package patterns:

- root `pyproject.toml`
- `ninjaclawbot/pyproject.toml`
- `pi5servo/pyproject.toml`
- `pi5disp/pyproject.toml`
- `pi5buzzer/pyproject.toml`
- `pi5vl53l0x/pyproject.toml`
- representative `__init__.py`, `__main__.py`, `driver.py`, and config-manager files from each package

Audited test coverage surfaces:

- `ninjaclawbot/tests/test_actions.py`
- `ninjaclawbot/tests/test_executor.py`
- `ninjaclawbot/tests/test_runtime.py`
- `ninjaclawbot/tests/test_openclaw_bridge.py`
- `ninjaclawbot/tests/test_cli_tools.py`
- plugin tests under `integrations/openclaw/ninjaclawbot-plugin/tests`

### 3.2 External upstream inputs fact-checked
Primary sources reviewed:

- OpenClaw Agent Loop docs
- OpenClaw Plugin Agent Tools docs
- OpenClaw Plugins docs
- OpenClaw Talk Mode docs
- OpenClaw Voice Wake docs
- OpenClaw Audio and Voice Notes docs
- OpenClaw Telegram docs
- OpenClaw Remote Access docs
- Google Gemini API Audio Understanding docs
- Google Gen AI Python SDK docs
- Picovoice Porcupine Python Quick Start docs

These external references changed the plan in meaningful ways, especially around transport choice, wake-word policy, and Telegram delivery safety.

## 4. What The Current Codebase Already Supports
The current codebase already gives us more than the earlier draft credited.

### 4.1 Robot output is already cleanly separated
`NinjaClawbotRuntime` is a composed runtime that owns:

- servo control
- buzzer control
- display control
- distance sensing
- expression orchestration

That means `pi5mic` should not try to solve robot hardware itself. It should produce text input, request presence changes when appropriate, and reuse the existing robot action layer.

### 4.2 The robot action contract is already stable
`ActionType` already includes stable actions such as:

- `perform_reply`
- `perform_expression`
- `set_idle`
- `set_presence_mode`
- `shutdown_sequence`
- `health_check`
- `stop_all`

This is important because microphone integration does not need a new robot action model.

### 4.3 Presence support already exists end to end in Python
This is one of the most important audit findings.

The current code already supports:

- `normalize_presence_mode()` with valid modes `idle`, `thinking`, `listening`
- `ActionType.SET_PRESENCE_MODE`
- `ActionExecutor` dispatch for `set_presence_mode`
- `NinjaClawbotRuntime.set_presence_mode()`
- `OpenClawServiceCore.set_presence_mode()`
- bridge protocol request type `set_presence_mode`

So the missing part is not Python support. The missing part is the right reusable external control surface for `pi5mic`.

### 4.4 The OpenClaw plugin already has a persistent-bridge helper
The plugin runner already contains `setPersistentPresenceMode()` and uses it in lifecycle hooks for:

- `gateway_start`
- `message_received`
- `agent_end`
- `gateway_stop`

This means the plugin already knows how to talk to the persistent bridge for presence changes. Adding a reusable external control path is a small plugin extension, not a large redesign.

### 4.5 Execution is already serialized inside the robot layer
Two locks matter:

- `ActionExecutor` runs through `runtime.execution_lock`
- `OpenClawServiceCore` uses its own service lock

That is good news for action correctness, but it also means `pi5mic` must not create a second uncontrolled hardware-control path. If it spawns competing robot runtimes, we risk process-level contention even if single-runtime locking is correct.

### 4.6 Existing tests already cover the bridge and lifecycle model
The current test suite already covers:

- startup sequence behavior
- `set_presence_mode` bridge request handling
- stale idle suppression
- repeated thinking coalescing
- plugin hook registration
- plugin bridge command construction

This gives us a strong place to extend tests for microphone-related integration without starting from zero.

### 4.7 Existing `pi5*` libraries give us the right package style, but not one single config convention
The current standalone libraries are consistent in broad shape:

- `pyproject.toml`
- `README.md`
- `src/<package>/__init__.py`
- `src/<package>/__main__.py`
- `driver.py`
- `config/*`
- `cli/*`
- `tests/*`

But their config-path behavior is not fully consistent:

- `pi5buzzer` defaults to `buzzer.json` in the working directory
- `pi5disp` defaults to package-local `display.json`
- `pi5servo` defaults to package-local `servo.json`

So `pi5mic` must choose its config strategy deliberately instead of assuming the repo already has one unified rule.

## 5. What Is Missing Today
The current audit showed the following real gaps.

### 5.1 There is no microphone input layer in the project
There is no current package for:

- microphone device enumeration
- local audio capture
- always-on listening
- silence auto-stop
- wake-word detection
- transcription

### 5.2 There is no voice-session state machine
The current project has output-oriented state and lifecycle handling, but it does not have a voice-input state machine such as:

- armed
- listening
- transcribing
- dispatching
- waiting for reply
- error recovery

That state machine must exist inside `pi5mic`.

### 5.3 The earlier plan picked the wrong external control shape for presence
The previous draft proposed a public OpenClaw agent tool like `ninjaclawbot_set_presence_mode`.

That is not the best primary control surface for `pi5mic`.

Why:

- agent tools are designed for LLM calls inside agent runs
- `pi5mic` is an external local process, not the model itself
- exposing an agent tool does not automatically give a local process a clean direct-call path

The stronger design is:

- keep optional agent tooling available if useful later
- add a small plugin-owned gateway-facing control path for `presence.set`
- let `pi5mic` call that path through the documented gateway transport

### 5.4 There is no defined OpenClaw transport client for local microphone input
The current plugin is designed to animate the robot during agent runs that were started elsewhere. There is no current local `pi5mic` client for:

- submitting text into OpenClaw through documented gateway entry points
- waiting for final output
- choosing a session key safely
- deciding whether the request is local-only or mirrored to a channel

### 5.5 Telegram mirroring is not safe without an explicit delivery target
The earlier draft treated Telegram mirroring as if it should happen automatically.

That is not robust enough.

The OpenClaw docs make two relevant points:

- Telegram inbound traffic naturally replies back to Telegram
- local mic-originated requests do not automatically inherit a Telegram target

So `pi5mic` must require an explicit delivery target before mirroring outward. Otherwise it risks:

- sending to the wrong chat
- leaking private local voice interactions
- producing inconsistent session history

### 5.6 The previous plan did not define session isolation
OpenClaw serializes work per session key. A mic-originated request therefore needs an explicit session policy.

We must choose and document whether `pi5mic` uses:

- a dedicated mic session like `voice:local-mic`
- or a shared session like `main`

For safety and predictability, the default should be a dedicated mic session.

### 5.7 The previous plan did not define secret handling
`mic.json` must not contain:

- Gemini API keys
- OpenClaw gateway tokens
- Telegram bot credentials

Those must come from environment variables or the gateway configuration already managed by OpenClaw.

### 5.8 The previous plan did not define audio retention and cleanup
Recorded audio is sensitive user input. The build plan must specify:

- delete-on-success by default
- temporary retention only when debugging is explicitly enabled
- bounded retention lifetime

### 5.9 There is no offline or degraded-mode strategy
If either dependency fails:

- microphone backend unavailable
- wake-word engine unavailable
- Gemini unreachable
- OpenClaw gateway unavailable

then `pi5mic` still needs safe fallback behavior instead of hanging in a broken loop.

## 6. External Fact Check Summary
The upstream docs materially changed the plan.

### 6.1 OpenClaw facts that matter
Verified upstream behavior:

- OpenClaw’s documented agent entry points are Gateway RPC `agent` and `agent.wait`
- plugin lifecycle hooks include `message_received`, `agent_end`, `gateway_start`, and `gateway_stop`
- plugin tools can be `optional` and require allowlist opt-in
- Talk Mode is described as a continuous voice loop and explicitly sends transcript text into the main session before waiting for the reply
- Voice Wake stores wake words at the gateway level and the docs note that custom wake words are not yet per-node
- Audio and Voice Notes already support transcription providers and an `echoTranscript` option
- Telegram routing is deterministic for Telegram-originated traffic, but that does not create a safe automatic target for a local microphone request
- `openclaw gateway {status,health,send,agent,call}` can target a remote gateway URL explicitly

Plan impact:

- `pi5mic` should use a documented gateway transport, not a guessed private API
- the default session should be explicit
- external delivery must be explicit
- a plugin-facing RPC control path is more useful than an agent-only tool for local presence updates

### 6.2 Gemini facts that matter
Verified upstream behavior:

- Gemini can analyze audio and return transcription-like text output
- Google’s current audio docs show audio-understanding examples using `gemini-3-flash-preview`
- Google’s audio docs explicitly state that the Gemini API does not support real-time transcription use cases
- Google recommends the Live API for real-time voice interactions and Google Cloud Speech-to-Text for dedicated real-time STT

Plan impact:

- do not hard-code `Gemini 2.5 Flash` as an unchangeable requirement
- define a generic STT backend interface
- use Gemini as a default batch-transcription backend, not as a real-time streaming assumption

### 6.3 Picovoice facts that matter
Verified upstream behavior:

- Porcupine Python Quick Start explicitly lists Raspberry Pi 5 support
- Porcupine requires a Picovoice `AccessKey`

Plan impact:

- if we choose Porcupine, the plan must account for one more secret that must not live in `mic.json`
- wake-word backend choice should be configurable, not hidden in the code

## 7. Feasibility Verdict
The build is feasible, but the first version must be slightly stricter than the earlier draft.

### 7.1 Can `pi5mic` be added as a sibling library?
Yes.

That still remains the right boundary:

- `pi5mic` handles local voice input
- OpenClaw handles session, reasoning, and outbound messaging
- `ninjaclawbot` handles robot actions and hardware state

### 7.2 Should `pi5mic` be merged into `NinjaClawbotRuntime`?
No.

`NinjaClawbotRuntime` is still an output-device runtime. Long-running microphone capture does not belong inside it.

### 7.3 What must change from the earlier draft?
The corrected first-version rules are:

- use a dedicated session key by default
- do not mirror to Telegram unless an explicit delivery target exists
- do not store secrets in `mic.json`
- use a transport abstraction for OpenClaw
- use a backend abstraction for STT
- treat wake-word and listening as a single-flight state machine
- avoid spawning competing robot runtimes if the persistent bridge is already active

## 8. Recommended pi5mic Package Shape
The new package should follow the existing standalone-first `pi5*` shape while adding the pieces a voice library actually needs.

```text
pi5mic/
├── LICENSE
├── README.md
├── pyproject.toml
├── mic.json
├── src/
│   └── pi5mic/
│       ├── __init__.py
│       ├── __main__.py
│       ├── driver.py
│       ├── models.py
│       ├── errors.py
│       ├── config/
│       │   └── config_manager.py
│       ├── core/
│       │   ├── devices.py
│       │   ├── recorder.py
│       │   ├── listener.py
│       │   └── session.py
│       ├── wakeword/
│       │   ├── base.py
│       │   └── porcupine.py
│       ├── vad/
│       │   ├── base.py
│       │   └── silence.py
│       ├── stt/
│       │   ├── base.py
│       │   └── gemini.py
│       ├── transport/
│       │   ├── base.py
│       │   ├── gateway_agent.py
│       │   └── openclaw_cli.py
│       ├── integration/
│       │   ├── presence.py
│       │   └── delivery.py
│       └── cli/
│           ├── __init__.py
│           ├── _common.py
│           ├── cmd.py
│           ├── config_cmd.py
│           ├── status.py
│           └── mic_tool.py
└── tests/
    ├── test_config.py
    ├── test_devices.py
    ├── test_recorder.py
    ├── test_listener.py
    ├── test_wakeword.py
    ├── test_vad.py
    ├── test_stt_gemini.py
    ├── test_gateway_agent.py
    ├── test_delivery.py
    ├── test_cli.py
    └── test_mic_tool.py
```

### Why this shape fits the current project
It preserves the project’s current expectations:

- standalone-first package
- compatibility `driver.py`
- config manager
- interactive CLI tooling
- clear hardware and integration boundaries

### Required config-path decision
Because the current `pi5*` libraries are inconsistent, `pi5mic` must choose clearly:

- default `mic.json` location should be the current working directory or explicitly passed `--config-file`
- all CLIs must support an explicit config path override
- secrets must stay outside the JSON config file

This is the safest choice for workspace use because users will most often run `uv run pi5mic ...` from the project root.

## 9. Recommended System Logic
This is the corrected end-to-end logic for the first stable version.

### 9.1 Config contract
`mic.json` should store only non-secret runtime preferences such as:

- input device id or name
- wake-word backend name
- wake-word keyword or model path
- silence timeout
- maximum clip duration
- STT backend name
- default STT model id
- OpenClaw gateway URL
- OpenClaw agent id
- OpenClaw session key
- whether presence integration is enabled
- whether delivery mirroring is enabled
- explicit delivery channel and target
- temporary audio retention policy

It must not store:

- Gemini API key
- Picovoice access key
- OpenClaw gateway token
- Telegram credentials

### 9.2 Runtime state machine
`pi5mic` should have an explicit local state machine:

- `idle`
- `armed`
- `listening`
- `transcribing`
- `dispatching`
- `waiting_for_reply`
- `cooldown`
- `error`

Rules:

- only one active request at a time
- reject or queue new wake-word hits while busy
- always return to `idle` or `armed`
- never leave the robot stuck in `listening` or `thinking`

### 9.3 Standalone mode
Standalone mode should work without OpenClaw.

Flow:

1. Detect the selected microphone
2. Wait for either:
   - wake word
   - or a manual trigger command in `mic-tool`
3. Record until either:
   - silence timeout
   - max duration
   - or manual stop
4. Transcribe the clip
5. Show transcript and metadata locally
6. Delete the temp clip unless debug retention is enabled

### 9.4 OpenClaw integrated mode
Integrated mode should use a documented OpenClaw transport.

Preferred flow:

1. Local microphone wake event starts capture
2. `pi5mic` optionally sets robot presence to `listening` through a gateway-facing control path owned by the OpenClaw plugin
3. Clip is recorded locally
4. STT backend returns transcript
5. `pi5mic` submits transcript to OpenClaw through:
   - Gateway RPC `agent` + `agent.wait` as the preferred backend
   - a CLI fallback backend only if RPC transport is unavailable
6. While OpenClaw is processing, robot presence can switch to `thinking`
7. Final reply is shown locally
8. Outbound mirroring happens only if a delivery target is explicitly configured
9. Robot returns to `idle`

### 9.5 Session policy
Default session policy should be:

- dedicated mic session key, for example `voice:local-mic`

Why:

- cleaner queueing
- no surprise conversation mixing with Telegram
- easier troubleshooting

Only make `main` the default if the user explicitly decides that local mic and other OpenClaw surfaces should share one memory lane.

### 9.6 Delivery policy
There are three safe delivery modes:

- `local_only`
- `local_plus_explicit_channel_target`
- `agent_managed_only` for cases where a future OpenClaw-native voice path owns delivery

For v1, the default should be `local_only`.

If the user later configures Telegram mirroring, the config must include explicit target information and a clear statement that this is an outbound send, not an automatic reply continuation.

## 10. Required Safety And Robustness Rules
These rules are mandatory for implementation.

### 10.1 Do not create two competing robot-control processes
If OpenClaw’s persistent bridge already owns the robot hardware path, `pi5mic` must reuse a plugin-owned control surface instead of spawning its own long-lived competing runtime.

### 10.2 Secrets never go into committed JSON config
Use environment variables or the existing gateway environment.

### 10.3 Audio clips are sensitive
Delete temp clips by default. Retention must be:

- opt-in
- bounded
- documented

### 10.4 Integrated mode must degrade safely
If OpenClaw or the STT backend is unavailable:

- show the error locally
- return the robot to `idle`
- do not loop forever

### 10.5 Wake-word behavior must have cooldown and busy protection
Without this, repeated triggers can flood OpenClaw and fight the robot lifecycle hooks.

### 10.6 Presence integration must be best-effort, not a hard failure gate
If presence update fails, microphone capture and transcription should still be able to continue when safe.

## 11. Phased Implementation Plan
This is the corrected phased plan.

### Phase 0: Architecture lock and dependency spike
Objective: lock the boundaries before writing package code.

Likely files:

- `MicDevelopment.md`
- `DevelopmentGuide.md`
- `InstallationGuide.md`
- new `pi5mic/pyproject.toml`
- new `pi5mic/README.md`

Required decisions in this phase:

- choose default microphone config-path strategy
- choose default wake-word backend and its secret handling
- choose STT backend abstraction and default backend
- choose OpenClaw transport backend:
  - Gateway RPC preferred
  - CLI fallback optional
- choose default session key
- choose default delivery mode
- choose audio retention policy
- define the external presence-control path

Important corrected defaults:

- do not hard-lock `Gemini 2.5 Flash`
- do not default to unconditional Telegram mirroring
- do not assume an agent tool is the right external presence API

Linting and validation:

```bash
git diff --check
```

Hardware risk:

- low

Documentation updates:

- `MicDevelopment.md`
- `DevelopmentGuide.md`
- `InstallationGuide.md`

### Phase 1: Standalone package scaffold, config, and recorder abstraction
Objective: create `pi5mic` as a real standalone library with a clear config contract.

Likely files:

- `pi5mic/pyproject.toml`
- `pi5mic/src/pi5mic/__init__.py`
- `pi5mic/src/pi5mic/__main__.py`
- `pi5mic/src/pi5mic/driver.py`
- `pi5mic/src/pi5mic/models.py`
- `pi5mic/src/pi5mic/errors.py`
- `pi5mic/src/pi5mic/config/config_manager.py`
- `pi5mic/src/pi5mic/core/devices.py`
- `pi5mic/src/pi5mic/core/recorder.py`
- `pi5mic/tests/test_config.py`
- `pi5mic/tests/test_devices.py`
- `pi5mic/tests/test_recorder.py`

Key implementation points:

- explicit `mic.json` schema
- device listing and selection
- bounded WAV capture
- temp-file cleanup behavior
- no secrets in config file

Linting and validation:

```bash
cd pi5mic
uv run --extra dev python -m compileall src tests
uv run --extra dev ruff check src tests
uv run --extra dev ruff format --check src tests
uv run --extra dev pytest -q tests -c pyproject.toml
```

Hardware risk:

- low to medium

Documentation updates:

- `pi5mic/README.md`
- `InstallationGuide.md`

### Phase 2: Listener state machine, wake-word backend, and silence stop
Objective: build the local voice state machine safely.

Likely files:

- `pi5mic/src/pi5mic/core/listener.py`
- `pi5mic/src/pi5mic/core/session.py`
- `pi5mic/src/pi5mic/wakeword/base.py`
- `pi5mic/src/pi5mic/wakeword/porcupine.py`
- `pi5mic/src/pi5mic/vad/base.py`
- `pi5mic/src/pi5mic/vad/silence.py`
- matching tests

Key implementation points:

- wake-word support
- silence auto-stop
- maximum clip length
- cooldown
- single-flight protection
- busy-state handling

Linting and validation:

```bash
cd pi5mic
uv run --extra dev python -m compileall src tests
uv run --extra dev ruff check src tests
uv run --extra dev ruff format --check src tests
uv run --extra dev pytest -q tests -c pyproject.toml
```

Hardware risk:

- medium

Documentation updates:

- `pi5mic/README.md`
- `InstallationGuide.md`

### Phase 3: STT backend abstraction and default Gemini batch transcription
Objective: add transcription through a stable backend interface.

Likely files:

- `pi5mic/src/pi5mic/stt/base.py`
- `pi5mic/src/pi5mic/stt/gemini.py`
- `pi5mic/src/pi5mic/models.py`
- matching tests

Key implementation points:

- backend interface, not hard-coded provider logic
- default Gemini batch transcription path
- model id configurable
- retries and timeout handling
- transcript metadata and language preservation
- delete or retain temp audio according to policy

Important design note:

- this phase is batch transcription after capture
- do not present it as real-time streaming transcription

Linting and validation:

```bash
cd pi5mic
uv run --extra dev python -m compileall src tests
uv run --extra dev ruff check src tests
uv run --extra dev ruff format --check src tests
uv run --extra dev pytest -q tests -c pyproject.toml
```

Hardware risk:

- low to medium

Documentation updates:

- `pi5mic/README.md`
- `InstallationGuide.md`

### Phase 4: Local CLI and operator diagnostics
Objective: make the package usable by a non-programmer before OpenClaw integration.

Likely files:

- `pi5mic/src/pi5mic/cli/cmd.py`
- `pi5mic/src/pi5mic/cli/config_cmd.py`
- `pi5mic/src/pi5mic/cli/status.py`
- `pi5mic/src/pi5mic/cli/_common.py`
- `pi5mic/src/pi5mic/cli/mic_tool.py`
- matching tests

Key implementation points:

- list devices
- select active mic
- test recording
- test wake-word path
- test transcription path
- show effective config
- show degraded-state diagnostics

Linting and validation:

```bash
cd pi5mic
uv run --extra dev python -m compileall src tests
uv run --extra dev ruff check src tests
uv run --extra dev ruff format --check src tests
uv run --extra dev pytest -q tests -c pyproject.toml
```

Hardware risk:

- medium

Documentation updates:

- `pi5mic/README.md`
- `InstallationGuide.md`

### Phase 5: OpenClaw transport backend
Objective: submit transcript text into OpenClaw using a documented transport.

Likely files:

- `pi5mic/src/pi5mic/transport/base.py`
- `pi5mic/src/pi5mic/transport/gateway_agent.py`
- `pi5mic/src/pi5mic/transport/openclaw_cli.py`
- matching tests

Key implementation points:

- Gateway RPC `agent` + `agent.wait` as the preferred backend
- explicit gateway URL and auth handling
- explicit session key
- explicit agent id
- typed response parsing
- local-only fallback when delivery is disabled

Linting and validation:

```bash
cd pi5mic
uv run --extra dev python -m compileall src tests
uv run --extra dev ruff check src tests
uv run --extra dev ruff format --check src tests
uv run --extra dev pytest -q tests -c pyproject.toml
```

Integration validation:

```bash
cd /Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code\ library/NinjaClawbot
uv run --extra dev python -m compileall .
uv run --extra dev ruff check .
uv run --extra dev ruff format --check .
uv run pytest -q pi5mic/tests -c pi5mic/pyproject.toml
git diff --check
```

Hardware risk:

- medium

Documentation updates:

- `pi5mic/README.md`
- `DevelopmentGuide.md`
- `InstallationGuide.md`

### Phase 6: OpenClaw-side presence control and explicit delivery integration
Objective: let `pi5mic` reuse the active OpenClaw robot path safely.

Likely files:

- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
- plugin tests
- `pi5mic/src/pi5mic/integration/presence.py`
- `pi5mic/src/pi5mic/integration/delivery.py`
- matching tests

Key implementation points:

- add a gateway-facing plugin-owned presence control path that reuses the persistent bridge
- support `idle`, `thinking`, and `listening`
- keep lifecycle hooks intact
- use explicit delivery targeting for any Telegram mirror behavior
- default to no external mirroring until target config exists

Important correction:

- a plugin-side gateway-facing control path is the primary external interface here
- an optional agent tool may still be added later, but it is not the main requirement for `pi5mic`

Linting and validation:

```bash
cd integrations/openclaw/ninjaclawbot-plugin
npm run typecheck
npm test
```

Workspace validation:

```bash
cd /Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code\ library/NinjaClawbot
uv run --extra dev python -m compileall .
uv run --extra dev ruff check .
uv run --extra dev ruff format --check .
uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml
git diff --check
```

Hardware risk:

- medium

Documentation updates:

- root `README.md`
- `DevelopmentGuide.md`
- `InstallationGuide.md`
- plugin docs if needed

### Phase 7: Workspace integration and final release pass
Objective: add `pi5mic` to the workspace and document the supported user path.

Likely files:

- root `pyproject.toml`
- root `README.md`
- `DevelopmentGuide.md`
- `InstallationGuide.md`
- `pi5mic/README.md`

Key implementation points:

- add `pi5mic` to the workspace
- keep standalone install support
- document environment variables and secrets setup
- document session policy and delivery policy
- document Raspberry Pi validation and rollback steps

Linting and validation:

```bash
cd /Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code\ library/NinjaClawbot
uv run --extra dev python -m compileall .
uv run --extra dev ruff check .
uv run --extra dev ruff format --check .
uv run pytest -q pi5mic/tests -c pi5mic/pyproject.toml
uv run pytest -q pi5buzzer/tests -c pi5buzzer/pyproject.toml
uv run pytest -q pi5servo/tests -c pi5servo/pyproject.toml
uv run pytest -q pi5disp/tests -c pi5disp/pyproject.toml
uv run pytest -q pi5vl53l0x/tests -c pi5vl53l0x/pyproject.toml
uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml
git diff --check
```

Hardware risk:

- medium

Documentation updates:

- all user-facing docs that mention setup, architecture, or voice input

## 12. Quality Gate After Every Phase
We should not move to the next phase until the current phase passes its checks.

For `pi5mic` package work:

```bash
cd pi5mic
uv run --extra dev python -m compileall src tests
uv run --extra dev ruff check src tests
uv run --extra dev ruff format --check src tests
uv run --extra dev pytest -q tests -c pyproject.toml
```

For root workspace integration work:

```bash
cd /Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code\ library/NinjaClawbot
uv run --extra dev python -m compileall .
uv run --extra dev ruff check .
uv run --extra dev ruff format --check .
uv run pytest -q pi5mic/tests -c pi5mic/pyproject.toml
uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml
git diff --check
```

For OpenClaw plugin changes:

```bash
cd integrations/openclaw/ninjaclawbot-plugin
npm run typecheck
npm test
```

## 13. Raspberry Pi Validation Plan
Every hardware-facing phase needs a real Raspberry Pi validation pass.

### Safe smoke tests
These tests should not move the robot.

- USB microphone is detected
- selected input device can record a short WAV clip
- wake word can be enabled and disabled
- silence timeout stops capture correctly
- 30-second maximum capture limit works
- temp-audio cleanup policy behaves as configured
- local-only transcription works end to end

### Device communication tests
These confirm networked and service dependencies.

- Gemini credentials are valid
- Picovoice access key is valid if Porcupine is enabled
- OpenClaw gateway is reachable
- configured session key works
- explicit delivery target validates before first outbound mirror

### Robot-presence tests
These are conservative robot-state tests.

- `listening` can be entered and left safely
- `thinking` can be entered and left safely
- failure during presence update does not wedge the mic state machine
- OpenClaw lifecycle hooks still work after adding the external presence path

### End-to-end conversational tests
Run these in order:

1. local-only voice request with no outbound mirroring
2. local voice request with robot `thinking` state only
3. local voice request with explicit outbound mirror target
4. repeated wake-and-speak cycles
5. OpenClaw restart while `pi5mic` is idle
6. network disconnect during transcription
7. gateway disconnect during reply wait

### Power-risk and long-run tests
These matter because listening is a long-running feature.

- 20 to 30 minute idle listening run
- repeated wake cycles across the full session
- microphone unplug/replug recovery
- memory use and temp-file cleanup after repeated requests

### Rollback steps
Rollback must be documented before shipping any Pi validation slice.

Minimum rollback:

- disable `pi5mic`
- return to the current Telegram-only OpenClaw path
- confirm startup greeting, reply expression, and sleepy shutdown still work

## 14. Final Recommendation Before Coding
The best first version is still:

- a new sibling library named `pi5mic`
- not a large refactor inside `ninjaclawbot`

But the corrected first-version defaults should now be:

- standalone-first package
- explicit local voice state machine
- configurable wake-word backend
- batch STT backend abstraction with Gemini as the first default backend
- OpenClaw Gateway RPC transport as the preferred integration path
- dedicated mic session key by default
- local-only delivery by default
- outbound channel mirroring only after explicit target configuration
- plugin-owned external presence control path that reuses the persistent bridge

This is the safest version of the architecture:

- `pi5mic` handles voice input and local state
- OpenClaw handles agent orchestration, sessions, and delivery
- `ninjaclawbot` handles robot output

That separation fits the current codebase, matches upstream OpenClaw contracts more closely, and reduces the main build risks that were previously under-specified.

## 15. References
Repository sources:

- `ninjaclawbot/src/ninjaclawbot/actions.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/src/ninjaclawbot/openclaw/service.py`
- `ninjaclawbot/src/ninjaclawbot/openclaw/bridge.py`
- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/schemas.ts`

Upstream references checked on `2026-03-19`:

- OpenClaw Agent Loop: `https://docs.openclaw.ai/concepts/agent-loop`
- OpenClaw Plugin Agent Tools: `https://docs.openclaw.ai/plugins/agent-tools`
- OpenClaw Plugins: `https://docs.openclaw.ai/tools/plugin`
- OpenClaw Talk Mode: `https://docs.openclaw.ai/nodes/talk`
- OpenClaw Voice Wake: `https://docs.openclaw.ai/nodes/voicewake`
- OpenClaw Audio and Voice Notes: `https://docs.openclaw.ai/nodes/audio`
- OpenClaw Telegram: `https://docs.openclaw.ai/channels/telegram`
- OpenClaw Remote Access: `https://docs.openclaw.ai/gateway/remote`
- Google Gemini Audio Understanding: `https://ai.google.dev/gemini-api/docs/audio`
- Google Gen AI Python SDK: `https://github.com/googleapis/python-genai`
- Picovoice Porcupine Python Quick Start: `https://picovoice.ai/docs/quick-start/porcupine-python/`
