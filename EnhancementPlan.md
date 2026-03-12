# NinjaClawBot Expression And OpenClaw Enhancement Plan

Date: 2026-03-12

## Table Of Contents

- [Purpose](#purpose)
- [Scope](#scope)
- [Audit Sources](#audit-sources)
- [Legacy Expression Audit Summary](#legacy-expression-audit-summary)
- [Current `ninjaclawbot` Gap Summary](#current-ninjaclawbot-gap-summary)
- [Refined Target Architecture](#refined-target-architecture)
- [First-Class Expression Engine](#first-class-expression-engine)
- [Persistent Idle Policy](#persistent-idle-policy)
- [Reply-Emotion Policy Layer](#reply-emotion-policy-layer)
- [Built-In Expression Catalog](#built-in-expression-catalog)
- [Expression Asset Model Extension](#expression-asset-model-extension)
- [Expression-Tool Enhancement Direction](#expression-tool-enhancement-direction)
- [Official OpenClaw Plugin Tool Wrapper](#official-openclaw-plugin-tool-wrapper)
- [OpenClaw Skill Wrapper](#openclaw-skill-wrapper)
- [Recommended OpenClaw Behavior Rules](#recommended-openclaw-behavior-rules)
- [Phased Implementation Plan](#phased-implementation-plan)
- [Quality Gates](#quality-gates)
- [Raspberry-Pi-Validation-Plan](#raspberry-pi-validation-plan)
- [Recommended Implementation Order](#recommended-implementation-order)
- [References](#references)
- [Current Status](#current-status)

## Purpose

This document records the complete refined enhancement plan for the next stage of the NinjaClawBot integration layer.

The goal is to extend the rebuilt `ninjaclawbot` package so it can:

- provide a first-class animated face and sound expression engine
- preserve a persistent `idle` face while the robot waits for user input
- map reply intent and emotion into suitable face and sound reactions
- let manual users create, preview, and trigger richer expressions from `expression-tool`
- expose an official, typed, OpenClaw-facing tool wrapper as the only approved robot-control surface for the OpenClaw AI agent
- ship an OpenClaw skill that teaches the agent when and how to use the robot expression and action tools correctly

This plan is intentionally separate from `developmentPlan.md`, which remains the primary migration and integration record for the Pi 5 driver libraries and the base `ninjaclawbot` rebuild.

## Scope

In scope:

- audit of the legacy NinjaRobotV5 facial and sound expression implementation
- design of a richer expression engine for the current Pi 5 stack
- extension of `ninjaclawbot` expression assets and expression tooling
- OpenClaw plugin tool wrapper design
- OpenClaw skill-wrapper design
- phased implementation planning, quality gates, and Raspberry Pi validation planning

Out of scope for the first enhancement pass:

- reintroducing legacy web server transport, BLE, ngrok, or `SafeExecutor`
- direct raw driver access from OpenClaw
- replacing the current standalone `pi5*` driver package boundaries

## Audit Sources

Legacy NinjaRobotV5 code reviewed:

- `NinjaRobotV5_bak/ninja_core/src/ninja_core/facial_expressions.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/robot_sound.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/web_server.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/ninja_agent.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/api_wrappers.py`

Current NinjaClawBot code reviewed:

- `ninjaclawbot/src/ninjaclawbot/assets.py`
- `ninjaclawbot/src/ninjaclawbot/adapters.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/src/ninjaclawbot/executor.py`
- `ninjaclawbot/src/ninjaclawbot/cli/expression_tool.py`
- `ninjaclawbot/src/ninjaclawbot/__main__.py`

OpenClaw primary-source research:

- official Raspberry Pi runtime docs
- official tool and plugin docs
- official skill docs

## Legacy Expression Audit Summary

The legacy NinjaRobotV5 expression system is more capable than the current `ninjaclawbot` expression layer.

Important legacy behaviors:

1. `AnimatedFaces` is a real expression engine.
   - It is not just a text display helper.
   - It renders procedural faces at about 60 FPS in a background thread.
   - It uses shared drawing primitives for a consistent visual identity.

2. The legacy face catalog is already broad.
   - Available names include `idle`, `happy`, `laughing`, `sad`, `cry`, `angry`, `surprising`, `sleepy`, `speaking`, `shy`, `scary`, `exciting`, and `confusing`.
   - The style is consistent because expressions are built from shared eye, eyebrow, mouth, blush, and punctuation logic.

3. The legacy sound system is emotion-based and sequence-based.
   - `RobotSoundPlayer` reuses the emotion sound catalog from the buzzer package.
   - Legacy playback is blocking and sequential, which made orchestration simple and deterministic.

4. The legacy orchestration model already supports waiting-state and reaction-state behavior.
   - The old web server starts `idle` when waiting.
   - Greeting triggers `happy` face plus sound, then returns to `idle`.
   - Action plans can use `face_chain` and `sound_chain`.
   - Post-action reset restores `idle`.

5. The old AI agent prompt already encoded emotion mapping examples.
   - Greeting should use `happy`.
   - Thinking or uncertainty should use a confused or thinking expression.
   - Speaking responses should transition into a speaking face.

## Current `ninjaclawbot` Gap Summary

The current `ninjaclawbot` implementation supports saved expressions, but it does not yet provide a complete expression engine.

Current limitations:

- expressions are mostly `display.text` plus a simple `sound` block
- there is no built-in animated face renderer
- there is no persistent `idle` face manager
- there is no `face_chain` concept
- there is no reply-emotion policy
- `expression-tool` cannot browse or trigger a built-in face catalog
- there is no official OpenClaw plugin tool wrapper yet
- there is no OpenClaw skill that teaches expression-selection policy

## Refined Target Architecture

The next enhancement should introduce two coordinated layers:

1. A richer `ninjaclawbot` expression layer.
   - built-in face engine
   - built-in sound expression catalog
   - expression player and idle manager
   - richer expression assets
   - expression-tool support

2. A strict OpenClaw-facing wrapper layer.
   - official plugin agent tool
   - JSON-schema request/response surface
   - OpenClaw skill that teaches correct use of the wrapper
   - no raw `pi5*` driver access from OpenClaw

High-level structure:

```text
OpenClaw Agent
  -> OpenClaw skill
  -> OpenClaw plugin tool (typed JSON schema)
  -> ninjaclawbot executor
  -> expression/movement/runtime policy
  -> pi5disp / pi5buzzer / pi5servo / pi5vl53l0x
```

## First-Class Expression Engine

The plan must explicitly include a first-class expression engine, not just richer JSON assets.

Required capabilities:

- procedural face rendering on the ST7789V display
- consistent shared style primitives
- smooth frame-based animation
- named built-in expressions
- expression preview and playback
- controlled stop and replacement behavior
- deterministic face reset to `idle` after temporary reactions

Recommended module split:

- `ninjaclawbot/src/ninjaclawbot/expressions/faces.py`
- `ninjaclawbot/src/ninjaclawbot/expressions/primitives.py`
- `ninjaclawbot/src/ninjaclawbot/expressions/catalog.py`
- `ninjaclawbot/src/ninjaclawbot/expressions/player.py`
- `ninjaclawbot/src/ninjaclawbot/expressions/sounds.py`
- `ninjaclawbot/src/ninjaclawbot/expressions/policy.py`

Design rule:

- the face engine should reuse the legacy minimalist visual language
- the animation quality should improve through smoother interpolation, better blink timing, livelier speaking motion, and clearer emotion separation

## Persistent Idle Policy

The refined plan must include a persistent `idle` policy as a first-class runtime concern.

Required behavior:

- when no action is running, the robot should show `idle`
- temporary expressions should replace `idle`
- after a non-idle face or expression completes, the runtime should restore `idle`
- startup should move into `idle` once the display runtime is ready
- shutdown should stop the active face loop cleanly

Implementation rule:

- `idle` state should be managed by `ninjaclawbot`, not by OpenClaw directly
- OpenClaw should request temporary reactions or explicit mode changes, but the runtime should own the idle fallback

## Reply-Emotion Policy Layer

The refined plan must include a dedicated reply-emotion policy layer for OpenClaw.

Purpose:

- map conversational situations to robot expression choices
- keep emotion-selection rules centralized and testable
- avoid forcing OpenClaw to construct face and sound chains manually for every reply

Recommended policy outputs:

- `face_chain`
- `sound_chain`
- `response_mode`
- `idle_reset`
- optional `priority`

Minimum required conversational states:

- greeting
- confirmation
- success
- speaking
- thinking
- confusing
- asking_clarification
- warning
- error
- sad
- sleepy

Example mappings:

- greeting -> `happy` face plus `happy` sound, then `idle`
- asking_clarification -> `confusing` face plus `confusing` sound, then `idle`
- cannot_answer -> `confusing` or `sad` reaction, then `idle`
- normal reply -> `speaking`
- task complete -> `success` or `excited`

## Built-In Expression Catalog

Recommended first built-in catalog:

- `idle`
- `greeting`
- `happy`
- `excited`
- `success`
- `speaking`
- `listening`
- `thinking`
- `confusing`
- `curious`
- `surprised`
- `sad`
- `crying`
- `angry`
- `warning`
- `error`
- `sleepy`
- `shy`
- `scary`

Catalog design rules:

- keep the same visual language across all expressions
- make each expression distinct enough for quick human recognition
- preserve legacy names where practical for backward familiarity
- add aliases only when the meaning is clear and stable

## Expression Asset Model Extension

The current expression asset format is too narrow. It should be extended to support both built-in expression usage and fully composed custom expressions.

Recommended asset shape:

```json
{
  "name": "greeting_happy",
  "description": "Warm greeting reaction",
  "builtin": "greeting",
  "display": {
    "text": "Hello",
    "scroll": false,
    "duration": 2.0,
    "language": "en",
    "font_size": 32
  },
  "face_chain": [
    { "name": "happy", "duration": 2.0 },
    { "name": "speaking", "duration": 1.5 }
  ],
  "sound_chain": [
    { "name": "happy" }
  ],
  "idle_reset": true
}
```

Extension rules:

- keep compatibility with the current simple `display` plus `sound` format where reasonable
- validate names and durations strictly
- normalize built-in references at save time
- keep the file format human-editable

## Expression-Tool Enhancement Direction

The expression-tool should become both an authoring tool and a live test console.

Required new capabilities:

- list built-in expressions
- preview built-in expressions immediately
- create a custom asset from a built-in base
- compose `face_chain` and `sound_chain`
- preview a saved expression without leaving the tool
- stop the current expression and return to `idle`

Recommended menu growth:

- list expressions
- list built-in expressions
- preview built-in expression
- create expression
- edit expression
- show expression
- run expression
- delete expression
- set idle
- stop active expression
- exit

## Official OpenClaw Plugin Tool Wrapper

The refined plan must include an official OpenClaw plugin agent tool, not only a local CLI.

Recommended wrapper design:

- one plugin tool namespace for NinjaClawBot actions
- optional tool registration with explicit allowlisting
- JSON-schema parameters
- typed structured results from `ninjaclawbot`

Recommended tool surface:

- `ninjaclawbot.perform_reply`
- `ninjaclawbot.perform_expression`
- `ninjaclawbot.perform_movement`
- `ninjaclawbot.health_check`
- `ninjaclawbot.list_capabilities`
- `ninjaclawbot.set_idle`
- `ninjaclawbot.stop_all`

Design rule:

- OpenClaw should prefer `perform_reply` for normal conversational behavior
- lower-level actions stay available, but the preferred path should preserve emotion policy and idle policy automatically

Why plugin tool over shell-only integration:

- structured schema validation
- explicit allowlist control
- clearer agent behavior
- easier testing
- safer than exposing raw shell commands or direct driver calls

## OpenClaw Skill Wrapper

The refined plan must also include a dedicated OpenClaw skill.

Purpose:

- teach the agent when to use `perform_reply` versus lower-level actions
- teach the emotion mapping policy
- teach the idle requirement
- provide examples and guardrails

Skill requirements:

- explain that the robot should show `idle` while waiting for user input
- explain that OpenClaw must not call raw `pi5*` tools directly
- explain the preferred action flow
- include emotion mapping examples
- include uncertainty and clarification behavior examples

## Recommended OpenClaw Behavior Rules

The skill and wrapper should explicitly encode these rules:

1. While waiting for user input, keep the robot in `idle`.
2. For greetings, use a happy face and happy sound.
3. For normal answers, use a speaking face and keep transitions smooth.
4. For uncertainty, clarification requests, or missing answers, use `confusing`.
5. For warnings or problems, use `warning` or `error`.
6. After temporary reactions, return to `idle` unless another action is immediately running.
7. Do not call raw `pi5disp`, `pi5buzzer`, `pi5servo`, or `pi5vl53l0x` commands from OpenClaw.
8. Use the `ninjaclawbot` plugin tool as the single robot-control boundary.

## Phased Implementation Plan

### Phase 1: Expression Contract And Catalog Foundation

Objective:

- extend the expression asset model and add a built-in expression catalog contract

Files or modules likely to change:

- `ninjaclawbot/src/ninjaclawbot/assets.py`
- `ninjaclawbot/src/ninjaclawbot/actions.py`
- `ninjaclawbot/src/ninjaclawbot/executor.py`
- new `ninjaclawbot/src/ninjaclawbot/expressions/catalog.py`

Lint and validation:

- `uv run python -m compileall conftest.py ninjaclawbot/src ninjaclawbot/tests`
- `uv run ruff check ninjaclawbot/src ninjaclawbot/tests`
- `uv run ruff format --check ninjaclawbot/src ninjaclawbot/tests`
- `uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml`

Hardware risk:

- low

Documentation updates required:

- `EnhancementPlan.md`
- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

### Phase 2: First-Class Animated Face Engine

Objective:

- implement the procedural face engine and shared drawing primitives

Files or modules likely to change:

- new `ninjaclawbot/src/ninjaclawbot/expressions/faces.py`
- new `ninjaclawbot/src/ninjaclawbot/expressions/primitives.py`
- new `ninjaclawbot/src/ninjaclawbot/expressions/player.py`
- `ninjaclawbot/src/ninjaclawbot/adapters.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`

Lint and validation:

- same package-local gate
- expression-render tests
- animation-loop lifecycle tests

Hardware risk:

- high

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

### Phase 3: Built-In Sound Expression Engine

Objective:

- expand sound expressions into a richer, coordinated emotion catalog

Files or modules likely to change:

- new `ninjaclawbot/src/ninjaclawbot/expressions/sounds.py`
- `ninjaclawbot/src/ninjaclawbot/adapters.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/src/ninjaclawbot/executor.py`

Lint and validation:

- same package-local gate
- sequence-duration tests
- playback ordering tests

Hardware risk:

- medium

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

### Phase 4: Persistent Idle Policy And Expression Orchestration

Objective:

- add `idle` state ownership, `face_chain`, `sound_chain`, and deterministic reset behavior

Files or modules likely to change:

- new `ninjaclawbot/src/ninjaclawbot/expressions/policy.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/src/ninjaclawbot/executor.py`
- `ninjaclawbot/src/ninjaclawbot/assets.py`

Lint and validation:

- same package-local gate
- state-transition tests
- idle-restore tests

Hardware risk:

- high

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

### Phase 5: Expression-Tool Enhancement

Objective:

- upgrade `expression-tool` into a full authoring and live-preview console

Files or modules likely to change:

- `ninjaclawbot/src/ninjaclawbot/cli/expression_tool.py`
- `ninjaclawbot/src/ninjaclawbot/assets.py`
- `ninjaclawbot/src/ninjaclawbot/executor.py`

Lint and validation:

- same package-local gate
- CLI tests
- asset round-trip tests

Hardware risk:

- medium

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

### Phase 6: Reply-Emotion Policy Layer

Objective:

- implement reply-state to expression mapping for OpenClaw-facing reply behavior

Files or modules likely to change:

- new `ninjaclawbot/src/ninjaclawbot/expressions/reply_policy.py`
- `ninjaclawbot/src/ninjaclawbot/executor.py`
- `ninjaclawbot/src/ninjaclawbot/actions.py`

Lint and validation:

- same package-local gate
- policy mapping tests
- structured reply tests

Hardware risk:

- medium

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

### Phase 7: Official OpenClaw Plugin Tool

Objective:

- implement an official OpenClaw plugin tool with JSON-schema parameters

Files or modules likely to change:

- new OpenClaw plugin directory in the repo
- plugin manifest or config files
- tool schema and handler files
- `README.md`

Lint and validation:

- root Python gate where applicable
- plugin-local smoke tests
- schema validation tests

Hardware risk:

- medium

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

### Phase 8: OpenClaw Skill Wrapper

Objective:

- create a skill that teaches the robot behavior rules, emotion mapping, and tool usage

Files or modules likely to change:

- new OpenClaw `SKILL.md`
- optional supporting examples or templates

Lint and validation:

- markdown review
- wrapper example review
- manual OpenClaw prompt-path review

Hardware risk:

- low

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

### Phase 9: Raspberry Pi 5 Validation

Objective:

- validate the full enhanced expression system and OpenClaw wrapper on hardware

Files or modules likely to change:

- documentation and log entries primarily

Lint and validation:

- final package-local gate
- manual Raspberry Pi checklist

Hardware risk:

- very high

Documentation updates required:

- `DevelopmentLog.md`

## Quality Gates

Default gate for every implementation phase:

```bash
uv run python -m compileall conftest.py ninjaclawbot/src ninjaclawbot/tests
uv run ruff check ninjaclawbot/src ninjaclawbot/tests
uv run ruff format --check ninjaclawbot/src ninjaclawbot/tests
uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml
```

Additional root smoke checks after interface or wrapper changes:

```bash
uv run ninjaclawbot --help
uv run ninjaclawbot expression-tool
uv run ninjaclawbot perform-expression <name>
```

## Raspberry Pi Validation Plan

### Safe smoke tests

- `uv sync --extra dev`
- `uv run ninjaclawbot health-check`
- `uv run ninjaclawbot expression-tool`
- confirm clean exit after `Goodbye!`

### Device communication tests

- verify the display shows built-in expressions
- verify the buzzer plays full emotion sequences
- verify `idle` can start and stop cleanly

### Expression behavior tests

- preview `idle`, `happy`, `speaking`, `confusing`, and `sleepy`
- run a saved built-in expression from `expression-tool`
- run `perform-expression` from the command line
- verify temporary reactions return to `idle`

### OpenClaw behavior tests

- greeting prompt should trigger `happy`
- clarification prompt should trigger `confusing`
- normal response should use `speaking`
- waiting state should restore `idle`

### Power-risk tests

- power down before rewiring display or buzzer hardware
- verify expression loops stop on shutdown
- verify no GPIO cleanup tracebacks appear on exit

## Recommended Implementation Order

Recommended order:

1. Phase 1: expression contract and catalog foundation
2. Phase 2: first-class animated face engine
3. Phase 3: sound expression engine
4. Phase 4: persistent idle policy and orchestration
5. Phase 5: expression-tool enhancement
6. Phase 6: reply-emotion policy layer
7. Phase 7: OpenClaw plugin tool
8. Phase 8: OpenClaw skill wrapper
9. Phase 9: Raspberry Pi validation

This order is deliberate:

- the plugin wrapper should not be built before the expression engine and reply policy exist
- the skill should teach the final tool surface, not an unstable intermediate one
- `idle` policy must live in `ninjaclawbot` before OpenClaw instructions can depend on it

## References

Legacy code references:

- `NinjaRobotV5_bak/ninja_core/src/ninja_core/facial_expressions.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/robot_sound.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/web_server.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/ninja_agent.py`
- `NinjaRobotV5_bak/ninja_core/src/ninja_core/api_wrappers.py`

Current NinjaClawBot references:

- `ninjaclawbot/src/ninjaclawbot/assets.py`
- `ninjaclawbot/src/ninjaclawbot/adapters.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/src/ninjaclawbot/executor.py`
- `ninjaclawbot/src/ninjaclawbot/cli/expression_tool.py`

OpenClaw research references:

- official Raspberry Pi runtime documentation
- official tool documentation
- official plugin agent tool documentation
- official skill documentation

## Current Status

Current state:

- this is a planning document only
- no code was changed as part of this enhancement-planning refinement
- the refined plan now explicitly includes:
  - a first-class expression engine
  - a persistent idle policy
  - a reply-emotion policy layer
  - an official OpenClaw plugin tool
  - an OpenClaw skill wrapper with behavior rules and examples

Next implementation decision needed:

- approve the enhancement plan so work can begin at Phase 1
