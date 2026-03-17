# pi5mic Development Plan

## Contents
- [1. What This Document Is For](#1-what-this-document-is-for)
- [2. Simple Word List](#2-simple-word-list)
- [3. Audit Scope](#3-audit-scope)
- [4. What The Current Ninjaclawbot Code Already Supports](#4-what-the-current-ninjaclawbot-code-already-supports)
- [5. What Is Missing Today](#5-what-is-missing-today)
- [6. Feasibility Verdict](#6-feasibility-verdict)
- [7. Recommended pi5mic Library Structure](#7-recommended-pi5mic-library-structure)
- [8. Recommended System Logic](#8-recommended-system-logic)
- [9. OpenClaw And Telegram Integration Model](#9-openclaw-and-telegram-integration-model)
- [10. Phased Implementation Plan](#10-phased-implementation-plan)
- [11. Quality Gate After Every Phase](#11-quality-gate-after-every-phase)
- [12. Raspberry Pi Validation Plan](#12-raspberry-pi-validation-plan)
- [13. Final Recommendation Before Coding](#13-final-recommendation-before-coding)

## 1. What This Document Is For
This document explains how to build a new USB microphone library named `pi5mic` for the NinjaClawBot project.

The goal is to make voice input work in two ways:

- `Standalone mode`: a local interactive tool named `mic-tool`
- `Integrated mode`: send the recognized voice command into the OpenClaw agent, while keeping Telegram text chat working

This plan is based on a code audit of the current `ninjaclawbot` library and the existing OpenClaw integration that already powers robot replies, startup actions, shutdown actions, and Telegram text replies.

No code changes are made in this document. This is the build plan we should follow before implementation starts.

## 2. Simple Word List
These short explanations are included so the plan is easier to read.

- `STT`: `speech-to-text`. This means turning recorded voice into text.
- `Wake word`: the word that starts recording. In this project the default word is `Ninja`.
- `VAD`: `voice activity detection`. This is a simple way to detect whether the user is still speaking.
- `CLI`: `command line interface`. This is the tool you run in Terminal.
- `API`: `application programming interface`. This means the way one program talks to another program.
- `Bridge`: a small connector process that passes requests between OpenClaw and `ninjaclawbot`.
- `Session`: the conversation state used by OpenClaw.
- `Telegram mirror`: sending the final reply from a mic-originated request to Telegram as well as showing local feedback.

## 3. Audit Scope
The current audit reviewed the important `ninjaclawbot` and OpenClaw integration files line by line.

Audited `ninjaclawbot` files:

- `ninjaclawbot/src/ninjaclawbot/config.py`
- `ninjaclawbot/src/ninjaclawbot/actions.py`
- `ninjaclawbot/src/ninjaclawbot/locks.py`
- `ninjaclawbot/src/ninjaclawbot/presence.py`
- `ninjaclawbot/src/ninjaclawbot/executor.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/src/ninjaclawbot/adapters.py`
- `ninjaclawbot/src/ninjaclawbot/cli/common.py`
- `ninjaclawbot/src/ninjaclawbot/__main__.py`
- `ninjaclawbot/src/ninjaclawbot/expressions/player.py`
- `ninjaclawbot/src/ninjaclawbot/openclaw/service.py`
- `ninjaclawbot/src/ninjaclawbot/openclaw/bridge.py`

Audited OpenClaw plugin files:

- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/schemas.ts`

Audited test coverage surfaces:

- `ninjaclawbot/tests/test_actions.py`
- `ninjaclawbot/tests/test_executor.py`
- `ninjaclawbot/tests/test_runtime.py`
- `ninjaclawbot/tests/test_adapters.py`
- `ninjaclawbot/tests/test_openclaw_bridge.py`
- `ninjaclawbot/tests/test_cli_tools.py`

## 4. What The Current Ninjaclawbot Code Already Supports
The current codebase already gives us several pieces that make `pi5mic` practical.

### 4.1 Robot output control is already cleanly separated
`NinjaClawbotRuntime` is already a composed runtime for robot outputs:

- servo control
- buzzer control
- display control
- distance sensor control
- expression orchestration

This means `pi5mic` does not need to solve robot hardware control. It only needs to produce text commands and optionally ask the robot to show a listening or thinking state.

### 4.2 The action system is already stable
`ActionRequest`, `ActionType`, and `ActionExecutor` already define stable robot actions like:

- `perform_reply`
- `perform_expression`
- `set_presence_mode`
- `shutdown_sequence`
- `health_check`

This is important because the robot reaction side does not need a redesign for microphone support.

### 4.3 Presence modes already exist
The runtime already supports persistent presence states:

- `idle`
- `thinking`
- `listening`

That is very useful for microphone integration. A voice workflow can show:

- `listening` while the user speaks
- `thinking` while transcription or agent work is happening
- `idle` when the system returns to waiting

### 4.4 OpenClaw already has a persistent bridge
The current OpenClaw integration already supports:

- a persistent Python bridge process
- startup sequence
- shutdown sequence
- diagnostics
- reply expressions

This means OpenClaw can already control the robot in a structured way. `pi5mic` does not need to invent a new robot bridge.

### 4.5 The plugin already supports visible chat replies after robot animation
The public tool `ninjaclawbot_reply` already tells the agent:

- animate the robot first
- then continue with the normal visible text reply

That is the correct behavior for voice input too. Once `pi5mic` turns speech into text and sends it into OpenClaw, the agent can keep using the same reply pattern that already works with Telegram.

### 4.6 Diagnostics already exist
The plugin already exposes `ninjaclawbot_diagnostics`.

That means the future `pi5mic` library can reuse the existing health and readiness information instead of inventing a second diagnostics system for robot state.

## 5. What Is Missing Today
The audit also showed clear gaps. These are not blockers, but they define the real implementation work.

### 5.1 There is no microphone device layer in `ninjaclawbot`
The current runtime has adapters for:

- servo
- buzzer
- display
- distance sensor

There is no microphone adapter or audio input service today.

### 5.2 There is no speech or text-input pipeline inside `ninjaclawbot`
The current `ninjaclawbot` library is built around robot output actions. It does not contain:

- microphone capture
- wake-word detection
- silence auto-stop logic
- cloud transcription
- agent input routing from external speech

### 5.3 There is no public OpenClaw tool for arbitrary presence changes
The runtime and service layer support `set_presence_mode`, but the public plugin tools do not expose a tool like:

- `ninjaclawbot_set_presence_mode`
- or a simpler `ninjaclawbot_set_listening`

This matters because `pi5mic` will likely want to set the robot to `listening` and `thinking` from outside the agent lifecycle hooks.

### 5.4 Telegram mirroring for mic-originated requests does not exist yet
Telegram text replies already work when the user types in Telegram.

What does not exist yet is a built-in flow that says:

- local mic request comes in
- OpenClaw processes it
- final answer is mirrored to Telegram by default

That must be added deliberately. It will not happen by itself.

### 5.5 The `ninjaclawbot` CLI is not the right place for always-on microphone behavior
The current `ninjaclawbot` CLI is designed for:

- direct robot actions
- local asset tools
- OpenClaw bridge serving

It is not designed for a long-running microphone capture loop. That is another reason `pi5mic` should be a sibling library, not a feature stuffed directly into `ninjaclawbot`.

## 6. Feasibility Verdict
The audit result is positive.

### 6.1 Can `pi5mic` be integrated into the NinjaClawBot project?
Yes.

The cleanest way is:

- build `pi5mic` as a new standalone-first `pi5*` library
- add it to the root workspace
- let it talk to OpenClaw as a client
- reuse existing `ninjaclawbot` tools and robot actions

### 6.2 Should `pi5mic` be built inside `NinjaClawbotRuntime`?
No for v1.

The current runtime is an output-device runtime. Mixing always-on microphone listening into it would create unnecessary coupling and make failure handling harder.

The better boundary is:

- `pi5mic` handles voice input
- OpenClaw remains the agent brain
- `ninjaclawbot` remains the robot control layer

### 6.3 Can OpenClaw properly use `pi5mic` in the current environment?
Yes, with one important addition.

OpenClaw can already use plain text very well. So once `pi5mic` transcribes speech into text, OpenClaw can process it like any other user message.

The one important extra feature we should add is a public presence tool so `pi5mic` can safely trigger:

- `listening`
- `thinking`
- `idle`

outside the existing built-in lifecycle hooks.

### 6.4 Is Telegram compatibility feasible?
Yes.

Telegram text input can remain unchanged.

For mic-originated requests, we should explicitly implement:

- local feedback in `mic-tool`
- OpenClaw agent processing
- final Telegram mirror by default

That is feasible and fits the current architecture, but it belongs in the `pi5mic` integration layer, not in the robot runtime.

## 7. Recommended pi5mic Library Structure
The new package should follow the same overall shape as the other `pi5*` libraries.

```text
pi5mic/
├── LICENSE
├── README.md
├── pyproject.toml
├── uv.lock
├── .python-version
├── mic.json
├── src/
│   └── pi5mic/
│       ├── __init__.py
│       ├── __main__.py
│       ├── driver.py
│       ├── models.py
│       ├── config/
│       │   └── config_manager.py
│       ├── core/
│       │   ├── devices.py
│       │   ├── audio.py
│       │   ├── recording.py
│       │   └── listener.py
│       ├── wakeword/
│       │   ├── base.py
│       │   └── porcupine.py
│       ├── vad/
│       │   └── silence.py
│       ├── stt/
│       │   ├── base.py
│       │   └── gemini.py
│       ├── integration/
│       │   ├── openclaw_client.py
│       │   ├── router.py
│       │   └── telegram_mirror.py
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
    ├── test_audio.py
    ├── test_listener.py
    ├── test_wakeword.py
    ├── test_vad.py
    ├── test_stt_gemini.py
    ├── test_openclaw_client.py
    ├── test_router.py
    ├── test_telegram_mirror.py
    ├── test_cli.py
    └── test_mic_tool.py
```

### Why this structure fits the current project
This layout matches the style already used by:

- `pi5servo`
- `pi5disp`
- `pi5buzzer`
- `pi5vl53l0x`

That keeps the project consistent and makes the new library easier to maintain.

## 8. Recommended System Logic
This is the recommended end-to-end logic for the first stable version.

### 8.1 Standalone mode
1. `pi5mic` listens to the USB microphone.
2. The local wake-word engine listens for `Ninja`.
3. When `Ninja` is detected, recording starts.
4. Recording stops when:
   - the user is silent for `5 seconds`
   - or the clip reaches `30 seconds`
5. The recorded audio is sent to Gemini 2.5 Flash for transcription.
6. The transcript is shown in `mic-tool`.
7. If OpenClaw mode is disabled, the process ends there.

### 8.2 OpenClaw integrated mode
1. `pi5mic` listens for `Ninja`.
2. The robot can be set to `listening`.
3. The audio clip is recorded.
4. The audio clip is transcribed by Gemini.
5. The transcript is sent to OpenClaw.
6. OpenClaw runs the agent.
7. The robot can be set to `thinking` while the response is generated.
8. The final reply is:
   - shown locally in `mic-tool`
   - sent to Telegram by default
9. The robot returns to `idle`.

### 8.3 Recommended function responsibilities
These are the main jobs each part of the library should own.

- `ConfigManager`
  - load and save `mic.json`
  - store device choice, wake word, silence timeout, max duration, gateway settings

- `Audio device layer`
  - list microphone devices
  - choose active input device
  - report audio backend health

- `Recording layer`
  - capture WAV audio
  - enforce 30-second limit
  - expose temporary file path or in-memory bytes

- `WakeWordEngine`
  - detect the default wake word `Ninja`
  - allow later replacement of keyword model files

- `VAD silence detector`
  - detect when the user stops speaking
  - stop recording after the configured silence timeout

- `Gemini STT backend`
  - send recorded audio to Gemini 2.5 Flash
  - return structured transcription data
  - preserve original language

- `OpenClawClient`
  - connect to the OpenClaw gateway
  - submit the transcript into the agent flow
  - read back the final answer

- `TelegramMirror`
  - send the final answer to Telegram when mic-originated requests are enabled for mirroring

- `mic-tool`
  - guide setup
  - test microphone input
  - test wake word
  - test Gemini transcription
  - test OpenClaw integration

## 9. OpenClaw And Telegram Integration Model
This section explains the safest way to connect the new library to the existing system.

### 9.1 What should stay unchanged
The current Telegram text workflow should stay exactly as it is now.

That means:

- user can still type into Telegram
- OpenClaw still replies in Telegram
- existing NinjaClawBot robot reactions still work

### 9.2 What `pi5mic` should add
The microphone should become a second input path.

That means:

- user can speak locally through the USB microphone
- the transcript is sent into OpenClaw
- OpenClaw responds through the same agent brain
- the final reply is mirrored to Telegram by default

### 9.3 One important plugin improvement
To make the microphone experience feel natural, the OpenClaw plugin should expose a public tool for presence updates.

Recommended new public tool:

- `ninjaclawbot_set_presence_mode`

Supported values:

- `idle`
- `thinking`
- `listening`

Why this matters:

- `pi5mic` can then put the robot into `listening` when the user starts speaking
- `pi5mic` can switch to `thinking` while Gemini or OpenClaw is busy
- `pi5mic` can safely return the robot to `idle` at the end

Without this tool, `pi5mic` can still work, but the robot experience will feel less complete.

## 10. Phased Implementation Plan

### Phase 0: Architecture lock and dependency spike
Objective: confirm the dependency set, config shape, and exact OpenClaw reply path before building the library.

Likely files:

- root `pyproject.toml`
- new `pi5mic/pyproject.toml`
- new `pi5mic/README.md`
- `DevelopmentGuide.md`
- `InstallationGuide.md`

Key implementation points:

- lock `Gemini 2.5 Flash` as the primary STT backend
- lock `Ninja` as the default wake word
- lock `30 seconds` as the default hard maximum recording duration
- lock `5 seconds` as the silence timeout default
- confirm Telegram mirror strategy
- define the `mic.json` contract

Linting and validation:

```bash
cd pi5mic
uv run --extra dev python -m compileall src tests
uv run --extra dev ruff check src tests
uv run --extra dev ruff format --check src tests
uv run --extra dev pytest -q tests -c pyproject.toml
```

Hardware risk:

- low

Documentation updates:

- `pi5mic/README.md`
- `DevelopmentGuide.md`
- `InstallationGuide.md`

### Phase 1: Standalone package scaffold and microphone device layer
Objective: create the standalone package and make USB microphone detection reliable.

Likely files:

- `pi5mic/src/pi5mic/__init__.py`
- `pi5mic/src/pi5mic/__main__.py`
- `pi5mic/src/pi5mic/driver.py`
- `pi5mic/src/pi5mic/config/config_manager.py`
- `pi5mic/src/pi5mic/core/devices.py`
- `pi5mic/src/pi5mic/core/audio.py`
- `pi5mic/src/pi5mic/cli/cmd.py`
- `pi5mic/src/pi5mic/cli/config_cmd.py`
- tests under `pi5mic/tests`

Key implementation points:

- list USB input devices
- select the active microphone
- record raw WAV files
- report basic microphone health

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

### Phase 2: Wake-word listening and silence auto-stop
Objective: detect `Ninja` locally and stop recording safely when the user stops speaking.

Likely files:

- `pi5mic/src/pi5mic/core/listener.py`
- `pi5mic/src/pi5mic/wakeword/base.py`
- `pi5mic/src/pi5mic/wakeword/porcupine.py`
- `pi5mic/src/pi5mic/vad/silence.py`
- matching tests

Key implementation points:

- local wake-word detection
- 5-second silence timeout
- 30-second hard recording limit
- cooldown and false-trigger handling

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
- `DevelopmentGuide.md`

### Phase 3: Gemini STT backend
Objective: transcribe the recorded audio clip into structured text in English, Traditional Chinese, or Japanese.

Likely files:

- `pi5mic/src/pi5mic/stt/base.py`
- `pi5mic/src/pi5mic/stt/gemini.py`
- `pi5mic/src/pi5mic/models.py`
- `pi5mic/src/pi5mic/core/recording.py`
- matching tests

Key implementation points:

- use `google-genai`
- send short clips directly
- preserve original language
- return structured JSON-style results
- store temporary clips for retry and troubleshooting

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

### Phase 4: `mic-tool` interactive tool
Objective: provide a setup and testing tool that non-programmers can use.

Likely files:

- `pi5mic/src/pi5mic/cli/mic_tool.py`
- `pi5mic/src/pi5mic/cli/status.py`
- `pi5mic/src/pi5mic/cli/_common.py`
- matching tests

Key implementation points:

- choose microphone device
- set wake word settings
- set silence timeout
- set max duration
- test recording
- test wake-word detection
- test Gemini transcription
- save config

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

### Phase 5: OpenClaw client and Telegram mirror
Objective: send mic-originated requests into OpenClaw and mirror the final reply to Telegram by default.

Likely files:

- `pi5mic/src/pi5mic/integration/openclaw_client.py`
- `pi5mic/src/pi5mic/integration/router.py`
- `pi5mic/src/pi5mic/integration/telegram_mirror.py`
- matching tests

Key implementation points:

- submit recognized text into OpenClaw
- read back the final response
- keep local feedback in `mic-tool`
- mirror the final answer to Telegram
- do not break existing Telegram text chat behavior

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
uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml
git diff --check
```

Hardware risk:

- medium

Documentation updates:

- root `README.md`
- `pi5mic/README.md`
- `DevelopmentGuide.md`
- `InstallationGuide.md`

### Phase 6: Small OpenClaw plugin extension for public presence updates
Objective: expose a safe public tool so `pi5mic` can drive `listening`, `thinking`, and `idle` cleanly.

Likely files:

- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/schemas.ts`
- plugin tests

Key implementation points:

- add a public tool like `ninjaclawbot_set_presence_mode`
- allow modes:
  - `idle`
  - `thinking`
  - `listening`
- keep the current lifecycle hooks untouched
- let `pi5mic` call the tool directly when voice capture starts or ends

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

### Phase 7: Workspace integration and final release pass
Objective: add `pi5mic` cleanly to the project workspace and document the finished user path.

Likely files:

- root `pyproject.toml`
- root `README.md`
- `DevelopmentGuide.md`
- `InstallationGuide.md`
- `pi5mic/README.md`

Key implementation points:

- add `pi5mic` to the workspace
- keep standalone install support
- write final Raspberry Pi validation steps
- keep secrets and tokens out of committed files

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

## 11. Quality Gate After Every Phase
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

## 12. Raspberry Pi Validation Plan
Every hardware-facing phase should include real Pi checks.

### Safe smoke tests
These tests do not move the robot.

- USB mic is detected
- wake word is detected
- a short recording succeeds
- a 30-second maximum-length recording ends cleanly
- Gemini transcription works in all 3 target languages

### Device communication tests
These check connections and service behavior.

- OpenClaw gateway reachable
- Gemini API key valid
- Telegram mirror configuration valid
- microphone reconnect works

### Actuator-moving tests
These should be conservative.

- first ask for a text-only voice request
- then ask for a safe expression-only voice request
- only test movement if the rest is stable

### Power-risk tests
These are important because voice listening is a long-running feature.

- 20 to 30 minute idle listening test
- repeated wake and speak cycles
- network disconnect during transcription
- OpenClaw restart while `pi5mic` is idle

## 13. Final Recommendation Before Coding
The audit shows that the best first version is:

- a new sibling library named `pi5mic`
- not a large refactor inside `ninjaclawbot`
- Gemini 2.5 Flash for transcription
- `Ninja` as the default wake word
- `30 seconds` as the default hard recording limit
- local feedback in `mic-tool`
- Telegram mirror enabled by default for mic-originated replies
- a small OpenClaw plugin extension so `pi5mic` can set `listening`, `thinking`, and `idle`

This plan fits the current codebase well and keeps the system understandable:

- `pi5mic` handles voice input
- OpenClaw handles agent reasoning
- `ninjaclawbot` handles robot output

That separation is the safest way to add voice support without destabilizing the existing build.
