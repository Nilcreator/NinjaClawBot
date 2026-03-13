# NinjaClawBot Enhancement Plan

Updated: 2026-03-13

This document now tracks the enhancement work in two stages:

- Stage 1: completed foundation work kept as a concise reference
- Stage 2: planned seamless OpenClaw agent integration and richer Always On robot reactions

## Stage 1: Completed Foundation Reference

Status: Done

### Purpose

Stage 1 established the modern `ninjaclawbot` foundation on top of the Pi 5 driver libraries and created the first approved OpenClaw control boundary.

### Key Features Delivered

- built-in animated facial expression engine
- built-in sound-expression catalog and orchestration
- persistent `idle` behavior owned by `ninjaclawbot`
- richer expression asset model and `expression-tool` preview workflow
- reply-emotion policy for OpenClaw-facing responses
- official `ninjaclawbot` OpenClaw plugin wrapper
- official `ninjaclawbot_control` OpenClaw skill wrapper

### Development Stages Completed

1. Expression contract and built-in catalog foundation
2. First-class animated face engine
3. Built-in sound-expression engine
4. Persistent idle policy and expression orchestration
5. `expression-tool` enhancement
6. Reply-emotion policy layer
7. Official OpenClaw plugin tool wrapper
8. OpenClaw skill wrapper

### Stage 1 Implementation Plan Status

- Phase 1: Expression contract and catalog foundation. Status: Done.
- Phase 2: First-class animated face engine. Status: Done.
- Phase 3: Built-in sound-expression engine. Status: Done.
- Phase 4: Persistent idle policy and expression orchestration. Status: Done.
- Phase 5: `expression-tool` enhancement. Status: Done.
- Phase 6: Reply-emotion policy layer. Status: Done.
- Phase 7: Official OpenClaw plugin tool wrapper. Status: Done.
- Phase 8: OpenClaw skill wrapper. Status: Done.

### Stage 1 Reference Outcome

Stage 1 delivered the expression/runtime layer and the initial OpenClaw integration surface now present in the repository. The next work is not a rebuild of that foundation. The next work is to make the existing integration seamless, lifecycle-aware, and robust during real OpenClaw gateway operation.

## Stage 2: Seamless OpenClaw Agent Integration And Always On Reactions

Status: Planned

### Stage 2 Purpose

Stage 2 is focused on making NinjaClawBot behave like a continuously present robot companion when used through OpenClaw.

The main goal is to move from a one-action-per-process bridge to a gateway-aware lifecycle model that:

- reacts automatically when the OpenClaw gateway starts
- keeps the robot visibly alive while the agent is waiting
- switches into a deliberate thinking state when a query arrives
- expresses the emotion of the final answer consistently
- shuts down cleanly with a sleepy reaction, display-off step, and runtime cleanup

### Stage 2 Key Features

- automatic greeting expression on OpenClaw gateway startup
- automatic transition to persistent `idle` after startup greeting
- automatic `thinking` reaction on incoming user query
- answer-state emotion rendering through the existing reply policy surface
- graceful shutdown sequence with `sleepy`, display power-down, and pipeline cleanup
- deeper plugin integration with OpenClaw lifecycle hooks instead of tool-only usage
- service-based runtime persistence so `idle` can remain active between agent actions

### Stage 2 Part 1: Detailed Implementation Plan

This section is the first part of Stage 2 by design. It is the execution plan for the Always On OpenClaw integration work.

#### Phase 2.1: Persistent Lifecycle Runtime Service

Objective:

- add a long-lived `ninjaclawbot` service that owns one `NinjaClawbotRuntime`
- keep one `ExpressionPlayer` alive across OpenClaw events
- centralize lifecycle commands for `startup`, `idle`, `thinking`, `reply`, and `shutdown`

Files or modules likely to change:

- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/src/ninjaclawbot/__main__.py`
- `ninjaclawbot/src/ninjaclawbot/adapters.py`
- new `ninjaclawbot/src/ninjaclawbot/openclaw/service.py`
- new `ninjaclawbot/src/ninjaclawbot/openclaw/ipc.py`
- new `ninjaclawbot/tests/test_openclaw_service.py`

Classes, functions, or interfaces to preserve:

- `ActionExecutor`
- `NinjaClawbotRuntime`
- existing action names such as `perform_reply`, `perform_expression`, `set_idle`, and `stop_all`
- existing CLI tool bridge payload shape for compatibility

Design notes:

- the new service should wrap the current runtime instead of bypassing it
- the current one-shot CLI path should remain available for manual use and fallback
- no `pi5*` driver public API changes should be required in this phase

Lint and validation:

- `uv run python -m compileall ninjaclawbot/src ninjaclawbot/tests`
- `uv run ruff check ninjaclawbot/src ninjaclawbot/tests`
- `uv run ruff format --check ninjaclawbot/src ninjaclawbot/tests`
- `uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml`

Manual Raspberry Pi validation required:

- start the service manually without OpenClaw and confirm it initializes once
- trigger startup behavior and verify greeting runs once
- verify `idle` stays visible for at least 30 seconds without the runtime closing
- confirm clean shutdown leaves no stuck display or buzzer state

Hardware risk:

- medium

Documentation updates required:

- `EnhancementPlan.md`
- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`
- `InstallationGuide.md`

#### Phase 2.2: OpenClaw Plugin Lifecycle Hook Integration

Objective:

- upgrade the OpenClaw plugin from a tool-only process launcher into a service-aware client
- register lifecycle hooks so NinjaClawBot reacts automatically during the OpenClaw gateway loop

Files or modules likely to change:

- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/schemas.ts`
- `integrations/openclaw/ninjaclawbot-plugin/openclaw.plugin.json`
- `integrations/openclaw/ninjaclawbot-plugin/tests/runner.test.ts`
- optional new plugin-side lifecycle helper files

Interfaces to preserve:

- existing tool names such as `ninjaclawbot_reply`, `ninjaclawbot_set_idle`, and `ninjaclawbot_stop_all`
- existing plugin config keys `projectRoot`, `rootDir`, and `uvCommand` unless an additive extension is required

Design notes:

- preferred hook coverage: `gateway_start`, `message_received`, and `gateway_stop`
- `message_sent` should be used only when it clearly helps avoid missed transitions
- the plugin should call the persistent service where available and keep the current bridge as fallback only if needed

Lint and validation:

- `npm run typecheck` in `integrations/openclaw/ninjaclawbot-plugin`
- `npm test` in `integrations/openclaw/ninjaclawbot-plugin`
- rerun the Phase 2.1 Python validation gate

Manual Raspberry Pi validation required:

- start the OpenClaw gateway and confirm automatic greeting then `idle`
- send a user message and confirm the thinking transition occurs before the final reply
- stop the OpenClaw gateway and confirm the shutdown hook fires reliably

Hardware risk:

- low to medium

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`
- `InstallationGuide.md`

#### Phase 2.3: Reply And State Coordination

Objective:

- connect OpenClaw lifecycle events and the existing reply policy into one consistent behavior model
- ensure the robot shows the correct temporary state and then returns to the correct persistent state

Files or modules likely to change:

- `ninjaclawbot/src/ninjaclawbot/expressions/policy.py`
- `ninjaclawbot/src/ninjaclawbot/expressions/catalog.py`
- `ninjaclawbot/src/ninjaclawbot/actions.py`
- `ninjaclawbot/src/ninjaclawbot/executor.py`
- new lifecycle controller modules under `ninjaclawbot/src/ninjaclawbot/openclaw/`
- `ninjaclawbot/tests/test_policy.py`
- `ninjaclawbot/tests/test_executor.py`

Interfaces to preserve:

- `perform_reply` as the main answer-expression API
- existing reply-state names already shipped in the plugin schema
- current built-in expressions unless additive improvements are required

Design notes:

- gateway startup should trigger `greeting` and then `idle`
- incoming query should trigger `thinking`
- final answer should be expressed through the existing reply-state mechanism
- shutdown should trigger `sleepy` without automatically bouncing back to `idle`
- if needed, add an explicit lifecycle-aware override instead of overloading normal reply behavior

Lint and validation:

- same Python validation gate as Phase 2.1
- targeted tests for lifecycle state transitions
- tests ensuring shutdown expression does not reset to `idle`

Manual Raspberry Pi validation required:

- verify greeting then idle on startup
- verify `thinking -> answer emotion -> idle` on greeting, normal answer, clarification, success, warning, and error cases
- verify `sleepy -> display off -> cleanup` on gateway stop

Hardware risk:

- medium

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

#### Phase 2.4: Config, Safety, And Documentation Hardening

Objective:

- remove integration rough edges discovered during the audit
- document the lifecycle model, fallback path, safety boundaries, and Pi validation steps clearly

Files or modules likely to change:

- `ninjaclawbot/src/ninjaclawbot/adapters.py`
- `pi5disp/src/pi5disp/cli/_common.py` or an equivalent display-construction path if needed
- `integrations/openclaw/ninjaclawbot-plugin/skills/ninjaclawbot_control/SKILL.md`
- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`
- `InstallationGuide.md`

Interfaces to preserve:

- standalone `pi5*` package boundaries
- current driver public entry points
- current manual `ninjaclawbot` CLI usage

Design notes:

- make display config honor `--root-dir` consistently during integrated runtime usage
- document the service path and the one-shot fallback path separately
- make shutdown and recovery instructions explicit for Raspberry Pi operators

Lint and validation:

- rerun the `ninjaclawbot` validation gate
- rerun affected `pi5disp` tests if display config loading changes
- rerun plugin typecheck and tests

Manual Raspberry Pi validation required:

- verify the configured display file used by `ninjaclawbot` is the root-level config
- restart the OpenClaw gateway multiple times and confirm no stale service or socket remains
- verify `ninjaclawbot_stop_all` still works as the emergency fallback

Hardware risk:

- low

Documentation updates required:

- `EnhancementPlan.md`
- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`
- `InstallationGuide.md`

### Stage 2 Part 2: Target OpenClaw Behavior

The intended Stage 2 user-facing behavior is:

1. Startup
   - when the OpenClaw gateway starts, NinjaClawBot is initialized automatically
   - the robot performs a greeting expression with face and sound
   - after the greeting, the robot moves into persistent `idle`

2. Idle waiting
   - while the OpenClaw agent is waiting for a user query, the robot remains in `idle`
   - `idle` is owned by `ninjaclawbot`, not manually retriggered after every tool call

3. Query received
   - when a user query arrives, the robot shows `thinking`
   - the thinking state stays active while the agent is working

4. Answer delivery
   - when the final answer is ready, the robot shows the matching answer emotion
   - after the answer reaction completes, the robot returns to `idle`

5. Shutdown
   - when the OpenClaw gateway stops, the robot shows `sleepy`
   - after the expression completes, the display is turned off and the runtime is cleaned up

### Stage 2 Part 3: Feasibility Summary

Stage 2 is feasible on top of the existing repository, but it is not a small reply-schema-only change.

The main architectural fact is that the current OpenClaw plugin is still one-shot:

- each plugin tool invocation spawns a fresh `ninjaclawbot` process
- the current CLI closes the runtime after every action
- a truly persistent `idle` state cannot survive across OpenClaw tool calls in the current model

Because of that, the robust solution is:

- a persistent `ninjaclawbot` lifecycle service
- OpenClaw lifecycle hooks in the plugin
- controlled coordination between startup, thinking, answer, idle, and shutdown states

### Stage 2 Validation Gate

Stage 2 should not be considered complete until Raspberry Pi validation passes with a real OpenClaw gateway session.

Required validation groups:

- safe smoke tests
- plugin and lifecycle communication tests
- conversational state-transition tests
- shutdown and recovery tests

Expected outcomes:

- the robot greets automatically on gateway start
- the robot stays in `idle` while waiting
- the robot shows `thinking` on incoming query
- the robot shows the correct answer emotion and returns to `idle`
- the robot shuts down with `sleepy`, powers off the display, and cleans up safely

Rollback path:

- disable the lifecycle hook integration in the plugin
- fall back to the current one-shot `ninjaclawbot` plugin tools
- use `ninjaclawbot_stop_all` if runtime behavior becomes unsafe

### Research Basis

Stage 2 planning is based on:

- the existing `ninjaclawbot` runtime, expression, and OpenClaw plugin code in this repository
- official OpenClaw plugin documentation
- official OpenClaw agent-loop lifecycle documentation
- official OpenClaw prompting documentation for `BOOT.md` and callbacks

