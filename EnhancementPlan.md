# NinjaClawBot Enhancement Plan

Updated: 2026-03-13

This document tracks enhancement work in two stages:

- Stage 1: completed foundation work kept as a concise reference
- Stage 2: refined Always On OpenClaw integration and seamless robot presence, implemented in a hybrid-ready way

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

Stage 1 delivered the expression/runtime layer and the initial OpenClaw integration surface now present in the repository. The next work is not a rebuild of that foundation. The next work is to make the existing integration lifecycle-aware, persistent, and robust during real OpenClaw gateway operation.

## Stage 2: Refined Always On OpenClaw Integration

Status: Planned

### Stage 2 Purpose

Stage 2 is focused on making NinjaClawBot behave like a continuously present robot companion when used through OpenClaw.

The goal is to move from a one-action-per-process bridge to a gateway-aware lifecycle model that:

- reacts automatically when the OpenClaw gateway starts
- keeps the robot visibly alive while the agent is waiting
- switches into a deliberate thinking state when a query arrives
- expresses the emotion of the final answer consistently
- shuts down cleanly with a sleepy reaction, display power-down, and runtime cleanup

### Stage 2 Key Features

- automatic greeting expression on OpenClaw gateway startup
- automatic transition to persistent `idle` after startup greeting
- automatic `thinking` reaction on incoming user query
- final answer emotion still rendered through the existing explicit reply-state tool path
- graceful shutdown sequence with `sleepy`, display power-down, and pipeline cleanup
- deeper plugin integration with OpenClaw lifecycle hooks and background services
- one persistent robot runtime shared across hooks and tools during gateway lifetime
- future-ready service core that can later be launched outside OpenClaw without redesigning the runtime

### Stage 2 Verification Summary

Stage 2 was re-audited against both the repository code and current official OpenClaw documentation before refining the plan.

Verified findings:

1. The current plugin is still one-shot.
   - `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts` spawns a fresh `uv run ninjaclawbot ...` process for each tool call.
   - `ninjaclawbot/src/ninjaclawbot/__main__.py` closes the runtime after every command.
   - Result: persistent `idle` cannot survive across OpenClaw tool calls in the current model.

2. OpenClaw already supports the right lifecycle primitives.
   - official plugin docs confirm plugin-managed background services and lifecycle hooks are available
   - official agent-loop docs confirm `gateway_start`, `gateway_stop`, `message_received`, `message_sent`, and `agent_end`
   - result: the robust solution should be plugin-service-first, not shell-call-first
   - long-term refinement: plugin-service-first should be treated as the deployment mode for Stage 2, not as a plugin-only architecture baked into the Python core

3. The current expression system is still reaction-oriented, not presence-oriented.
   - `ExpressionPlayer.perform()` runs a temporary face and sound sequence, then returns
   - only `set_idle()` currently runs indefinitely
   - result: `thinking`, `listening`, and shutdown behavior need explicit persistent-mode support instead of being overloaded onto temporary reply actions

4. `message_sent` is not a safe primary trigger for answer emotion.
   - official agent-loop docs describe partial-message and streaming behavior
   - result: final answer emotion should remain explicit through `ninjaclawbot_reply`; hook-based post-send behavior should only be used as bounded fallback

5. Display shutdown and config handling still need hardening.
   - `pi5disp` already exposes `off()`, `sleep()`, and `close()`
   - `ninjaclawbot` currently builds the display through `pi5disp.cli._common`, which still loads package-local config instead of reliably honoring `--root-dir`

6. The current lock model is too strict for lifecycle events on its own.
   - `ExecutionLock` rejects overlapping actions instead of queueing or coalescing them
   - result: a persistent bridge must add scheduling, dedupe, and stale-event suppression around the existing executor

### Refined Stage 2 Architecture

The verified target architecture is:

```text
OpenClaw gateway
  -> NinjaClawBot plugin background service
  -> persistent Python bridge process
  -> lifecycle controller + action queue
  -> NinjaClawbotRuntime / ExpressionPlayer / reply policy
  -> pi5disp / pi5buzzer / pi5servo / pi5vl53l0x
```

Important design decision:

- the preferred persistent path is a plugin-managed background service that owns a long-lived Python bridge process
- the current one-shot CLI bridge remains as a manual tool path and fallback path
- the plugin should not require operators to manage a separate standalone daemon manually for the primary path
- the Python bridge and lifecycle controller should still be designed as reusable service-core modules so a standalone daemon can be added later without reworking the runtime model

### Hybrid Model Preservation Rules

Stage 2 should preserve long-term standalone flexibility even though the first persistent deployment mode is plugin-managed.

Required design rules:

1. Keep the Python bridge transport-agnostic.
   - Stage 2 may use stdin/stdout or another plugin-friendly local IPC transport first.
   - The bridge protocol should be shaped so it can later be exposed by a standalone daemon with minimal change.

2. Keep OpenClaw-specific behavior out of the core runtime where possible.
   - lifecycle event mapping can live in an OpenClaw integration layer
   - expression playback, presence modes, shutdown sequencing, and scheduling should live in reusable Python service-core modules

3. Preserve a stable internal request contract.
   - tools, hooks, plugin services, and any future standalone daemon should talk to the same Python-side action and lifecycle contract where practical

4. Keep deployment concerns separate from behavior concerns.
   - Stage 2 should implement plugin-managed process ownership now
   - future standalone launch modes such as `systemd`, manual daemon start, or another client should be additive deployment wrappers, not a behavior rewrite

5. Keep diagnostics reusable.
   - service status, current presence mode, last lifecycle event, and last error should be exposed in a way that works for both plugin-managed and future standalone deployment

6. Avoid plugin-only naming where it would leak into the long-term architecture.
   - it is acceptable for the plugin package to remain OpenClaw-specific
   - reusable Python service-core modules should be named around bridge, lifecycle, presence, and runtime rather than around a single host platform

### Stage 2 Part 1: Refined Implementation Plan

This is the verified and refined implementation plan for the Always On OpenClaw integration work.

#### Phase 2.1: Plugin-Managed Persistent Bridge Service

Objective:

- add a plugin-managed background service that owns one long-lived Python bridge process
- keep one `NinjaClawbotRuntime` alive across OpenClaw hooks and tools
- replace per-call process startup with a persistent request/response channel
- do this in a way that keeps the same bridge core reusable for a future standalone daemon mode

Verified reason for this phase:

- official OpenClaw docs already support plugin background services
- the current tool-only spawn model cannot keep `idle` or `thinking` alive between calls
- a plugin-owned bridge is simpler and more robust than asking operators to manage a separate daemon first
- long-term robot use still benefits from keeping the bridge core host-neutral and reusable

Recommended implementation shape:

- add a new persistent Python bridge command such as `ninjaclawbot openclaw-serve`
- use a line-delimited JSON or similar stdin/stdout protocol between the plugin service and Python bridge
- keep the existing one-shot `openclaw-action` command for compatibility and fallback
- make the plugin lazily `ensureBridge()` so startup ordering between service start and hooks does not become fragile
- split the Python implementation into:
  - reusable service-core modules for lifecycle, scheduling, presence, and runtime ownership
  - a thin OpenClaw-hosted entrypoint that wires the plugin-managed process to that core
- preserve the option to later add a separate command such as `ninjaclawbot serve` or equivalent standalone launcher on top of the same service core

Files or modules likely to change:

- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
- `integrations/openclaw/ninjaclawbot-plugin/openclaw.plugin.json`
- new plugin-side bridge/service helper files under `integrations/openclaw/ninjaclawbot-plugin/src/`
- `ninjaclawbot/src/ninjaclawbot/__main__.py`
- new `ninjaclawbot/src/ninjaclawbot/openclaw/bridge.py`
- new `ninjaclawbot/src/ninjaclawbot/openclaw/service.py`
- new `ninjaclawbot/tests/test_openclaw_bridge.py`

Classes, functions, or interfaces to preserve:

- `ActionExecutor`
- `NinjaClawbotRuntime`
- existing action names such as `perform_reply`, `perform_expression`, `set_idle`, and `stop_all`
- current one-shot bridge payload shape for compatibility
- a reusable internal bridge request contract that is not tied only to plugin tool calls

Lint and validation:

- `npm run typecheck` in `integrations/openclaw/ninjaclawbot-plugin`
- `npm test` in `integrations/openclaw/ninjaclawbot-plugin`
- `uv run python -m compileall ninjaclawbot/src ninjaclawbot/tests`
- `uv run ruff check ninjaclawbot/src ninjaclawbot/tests`
- `uv run ruff format --check ninjaclawbot/src ninjaclawbot/tests`
- `uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml`

Manual Raspberry Pi validation required:

- start the OpenClaw gateway and confirm the bridge starts once
- verify repeated tool calls reuse the same runtime instead of respawning hardware state
- verify bridge restart or gateway restart does not leave stale child processes behind
- verify the bridge core can still be started directly from Python or CLI in a controlled local debug path without OpenClaw

Hardware risk:

- medium

Documentation updates required:

- `EnhancementPlan.md`
- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`
- `InstallationGuide.md`

Concrete implementation checklist:

1. Define the persistent bridge protocol.
   - choose a transport-neutral request/response envelope for the Python bridge
   - use a simple line-delimited JSON protocol first
   - define minimum message types:
     - `execute_action`
     - `health_ping`
     - `status`
     - `shutdown`
   - define stable response fields:
     - `ok`
     - `request_id`
     - `data`
     - `error`

2. Build the reusable Python service core.
   - create a service-core object that owns one `NinjaClawbotRuntime`
   - keep one `ActionExecutor` and one asset store alive for the full service lifetime
   - expose methods for:
     - startup/prewarm
     - action execution
     - status reporting
     - graceful shutdown

3. Add the persistent Python bridge entrypoint.
   - add a new CLI command such as `openclaw-serve`
   - wire stdin/stdout to the service core
   - keep `openclaw-action` unchanged as the one-shot fallback path
   - ensure the bridge exits cleanly on EOF, explicit shutdown request, or fatal initialization failure

4. Refactor the plugin runner into a reusable bridge client.
   - preserve current config parsing
   - split one-shot command construction from persistent bridge management
   - add lazy bridge startup and reconnect handling
   - route existing tools through the bridge client first, then optional fallback to the one-shot command if the bridge is unavailable

5. Add plugin-managed process lifecycle handling.
   - start the bridge once per plugin lifetime or first use
   - cache the child process handle and connection state
   - add bounded startup timeout, request timeout, and shutdown timeout
   - ensure the bridge process is stopped on plugin shutdown

6. Add direct diagnostics for Phase 2.1.
   - make the bridge capable of returning simple service status
   - include runtime-alive state and last error information
   - keep this diagnostic path internal or operator-focused, not a new unsafe robot-control surface

7. Expand automated tests.
   - add Python tests for:
     - repeated action execution using one persistent runtime
     - clean bridge shutdown
     - malformed input handling
     - one-shot compatibility retention
   - add plugin tests for:
     - lazy bridge startup
     - persistent client request routing
     - timeout behavior
     - fallback behavior if the bridge cannot start

8. Validate on Raspberry Pi before Phase 2.2.
   - confirm the bridge starts once
   - confirm multiple tool invocations reuse the same runtime
   - confirm restarts do not leave stale child processes
   - confirm the one-shot bridge still works if the persistent bridge is disabled

File-by-file change map:

- `ninjaclawbot/src/ninjaclawbot/__main__.py`
  - add `openclaw-serve`
  - keep `openclaw-action` unchanged for fallback compatibility
  - factor bridge startup and shutdown wiring out of `_execute_and_print`

- `ninjaclawbot/src/ninjaclawbot/openclaw/bridge.py`
  - new file
  - implement the stdin/stdout bridge loop
  - parse request envelopes
  - serialize structured responses
  - own low-level protocol framing and I/O error handling

- `ninjaclawbot/src/ninjaclawbot/openclaw/service.py`
  - new file
  - implement the reusable service core
  - own persistent runtime, executor, asset store, prewarm logic, status reporting, and graceful cleanup
  - keep host-specific policy out of this file so it can later back a standalone daemon

- `ninjaclawbot/src/ninjaclawbot/openclaw/__init__.py`
  - new file
  - expose the bridge/service-core entry points cleanly

- `ninjaclawbot/tests/test_openclaw_bridge.py`
  - new file
  - cover bridge request parsing, runtime reuse, status response, shutdown flow, and malformed input

- `ninjaclawbot/tests/test_cli_tools.py`
  - extend existing CLI coverage
  - verify `openclaw-serve` command bootstrap behavior and that legacy one-shot commands remain intact

- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
  - refactor from one-shot spawn helper into:
    - config parsing
    - persistent bridge client
    - child-process lifecycle management
    - fallback one-shot execution path
  - add helper functions such as `ensureBridge`, `sendBridgeRequest`, and `shutdownBridge`

- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
  - keep current tool registrations
  - route all existing tool executions through the persistent bridge client
  - prepare plugin-level startup and teardown wiring for later lifecycle hooks

- `integrations/openclaw/ninjaclawbot-plugin/openclaw.plugin.json`
  - extend config schema with bounded bridge settings such as:
    - startup timeout
    - request timeout
    - shutdown timeout
    - optional persistent-bridge enable flag
  - keep `projectRoot`, `rootDir`, and `uvCommand`

- `integrations/openclaw/ninjaclawbot-plugin/tests/runner.test.ts`
  - extend existing runner tests
  - add coverage for bridge config parsing, persistent bridge startup, fallback path selection, and shutdown behavior

- `integrations/openclaw/ninjaclawbot-plugin/package.json`
  - update test script or add any plugin-local helper dependency only if needed for bridge lifecycle testing
  - avoid introducing runtime dependencies unless there is a clear need

#### Phase 2.2: Persistent Presence Modes And Shutdown Contract

Objective:

- add explicit persistent robot-presence modes instead of forcing temporary reply actions to do long-lived work
- add an explicit shutdown sequence contract for sleepy -> display off -> cleanup

Verified reason for this phase:

- current `ExpressionPlayer` can only keep `idle` alive indefinitely
- `thinking` and `listening` currently behave like temporary reactions, not true persistent states
- current shutdown behavior relies on generic runtime close, not an explicit sleepy-then-power-down flow

Recommended action-surface refinement:

- preserve `set_idle` as a compatibility alias
- add a generalized persistent-mode action such as `set_presence_mode`
- recommended supported persistent modes:
  - `idle`
  - `thinking`
  - `listening`
- add an explicit `shutdown_sequence` action for:
  - play `sleepy` without auto-reset to `idle`
  - turn the display off or sleep it
  - close the runtime safely

Recommended runtime refinement:

- extend `ExpressionPlayer` so any built-in expression can run indefinitely when requested
- separate temporary reply expressions from persistent presence modes
- add a display power-down helper that uses `off()`, `sleep()`, and then `close()` with defensive fallbacks

Files or modules likely to change:

- `ninjaclawbot/src/ninjaclawbot/actions.py`
- `ninjaclawbot/src/ninjaclawbot/executor.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/src/ninjaclawbot/adapters.py`
- `ninjaclawbot/src/ninjaclawbot/expressions/player.py`
- `ninjaclawbot/src/ninjaclawbot/expressions/catalog.py`
- `integrations/openclaw/ninjaclawbot-plugin/src/schemas.ts`
- `ninjaclawbot/tests/test_executor.py`
- `ninjaclawbot/tests/test_expressions.py`
- `ninjaclawbot/tests/test_runtime.py`

Interfaces to preserve:

- `perform_reply` as the main answer-expression API
- current built-in expression names where possible
- `set_idle` as a stable public command

Lint and validation:

- same Python validation gate as Phase 2.1
- new tests for persistent `thinking` and `listening`
- new tests ensuring `shutdown_sequence` does not bounce back to `idle`
- new tests for display power-down fallback ordering

Manual Raspberry Pi validation required:

- verify `idle` remains animated between gateway events
- verify `thinking` remains active until replaced
- verify shutdown shows `sleepy`, then powers down the display, then cleans up

Hardware risk:

- medium

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`
- `InstallationGuide.md`

#### Phase 2.3: Lifecycle Hook Orchestration And Reply Policy Coordination

Objective:

- connect OpenClaw lifecycle events and the existing reply policy into one coherent robot-presence model
- make startup, waiting, thinking, answer, and shutdown transitions deterministic

Verified reason for this phase:

- OpenClaw lifecycle hooks exist, but the current plugin does not use them
- answer emotion is already encoded in the explicit `ninjaclawbot_reply` tool path
- `message_sent` is too risky to use as the primary answer trigger because of streaming and partial-message behavior

Recommended lifecycle policy:

- service start:
  - prewarm the bridge
  - optionally run a lightweight health probe
- `gateway_start` or service-start callback:
  - perform startup greeting
  - then set persistent `idle`
- `message_received`:
  - fire-and-forget `thinking` if no higher-priority explicit action is already active
- final answer:
  - remain driven by explicit `ninjaclawbot_reply` calls from the agent and skill
- `agent_end`:
  - bounded fallback to `idle` if the robot is still left in `thinking`
- service stop or `gateway_stop`:
  - run `shutdown_sequence` with a timeout

Important rule:

- do not make automatic text-emotion inference from raw assistant text the primary control path
- keep the final answer emotion explicit and agent-driven through `reply_state`
- keep lifecycle orchestration separate enough that a future standalone host could trigger the same presence transitions without needing OpenClaw-specific codepaths in the core service

Files or modules likely to change:

- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
- `integrations/openclaw/ninjaclawbot-plugin/skills/ninjaclawbot_control/SKILL.md`
- `ninjaclawbot/src/ninjaclawbot/expressions/policy.py`
- `ninjaclawbot/tests/test_policy.py`
- new lifecycle-orchestration tests in both plugin and Python test suites

Interfaces to preserve:

- `ninjaclawbot_reply` as the preferred answer-emotion tool
- existing reply-state names already shipped in the plugin schema unless additive aliases are approved

Lint and validation:

- same plugin and Python validation gates as earlier phases
- tests for startup -> idle
- tests for thinking -> reply -> idle
- tests for `agent_end` fallback restoring idle after abandoned thinking state

Manual Raspberry Pi validation required:

- verify startup greeting then persistent idle
- verify incoming user query changes the robot into `thinking`
- verify final answer emotion follows the explicit reply state
- verify the robot returns to `idle` after the final answer

Hardware risk:

- low to medium

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`
- `InstallationGuide.md`

#### Phase 2.4: Arbitration, Dedupe, Degraded Mode, And Config Hardening

Objective:

- make the lifecycle system resilient when hooks, tools, retries, and hardware failures interact
- remove the remaining integration rough edges found during the audit

Verified reason for this phase:

- current `ExecutionLock` rejects overlaps instead of queueing or coalescing them
- one physical robot may receive multiple lifecycle events faster than hardware should react
- current display config loading does not consistently honor `--root-dir`
- robot-side failures must not destabilize the OpenClaw gateway

Recommended hardening work:

- add a bridge-side action queue or scheduler
- treat low-priority lifecycle events such as repeated `thinking` or fallback `idle` as coalescible
- add an activity epoch or similar stale-event suppression so old fallback events do not overwrite newer states
- define a clear precedence order:
  - shutdown
  - explicit user-initiated robot actions
  - explicit reply tool actions
  - lifecycle presence updates
  - fallback idle updates
- make bridge and hook failures degrade gracefully:
  - log warnings
  - keep the gateway alive
  - return structured errors for explicit tools
- fix integrated display construction so root-level display config is respected
- add bounded plugin config options for:
  - enabling or disabling Always On behavior
  - startup greeting
  - auto-thinking
  - bridge timeouts
  - shutdown timeout
- keep these controls layered so:
  - plugin config governs OpenClaw-hosted deployment choices
  - Python-side service-core config remains reusable if a future standalone daemon is added

Files or modules likely to change:

- `ninjaclawbot/src/ninjaclawbot/adapters.py`
- `ninjaclawbot/src/ninjaclawbot/locks.py`
- `ninjaclawbot/src/ninjaclawbot/openclaw/service.py`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
- `integrations/openclaw/ninjaclawbot-plugin/openclaw.plugin.json`
- `pi5disp/src/pi5disp/cli/_common.py` or an equivalent display-config path if needed
- `ninjaclawbot/tests/test_adapters.py`
- plugin service and runner tests

Interfaces to preserve:

- standalone `pi5*` package boundaries
- current driver public entry points
- current manual `ninjaclawbot` CLI usage

Lint and validation:

- rerun the plugin and Python validation gates
- rerun any affected `pi5disp` tests if config-loading behavior changes
- add queue and stale-event suppression tests
- add degraded-mode tests for unavailable hardware or bridge restart

Manual Raspberry Pi validation required:

- restart the OpenClaw gateway multiple times and confirm no stale bridge remains
- verify repeated inbound messages do not cause flickering or queue storms
- verify the configured root-level display file is actually used by `ninjaclawbot`
- verify hardware failures do not crash the OpenClaw gateway process

Hardware risk:

- medium

Documentation updates required:

- `EnhancementPlan.md`
- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`
- `InstallationGuide.md`

#### Phase 2.5: Validation, Observability, And Release Gate

Objective:

- make the Stage 2 rollout diagnosable and safe to validate on Raspberry Pi before wider use

Verified reason for this phase:

- lifecycle bugs are difficult to debug if bridge state is invisible
- gateway-start, message-received, and gateway-stop issues can otherwise look like random robot glitches

Recommended additions:

- add a simple service-status or bridge-status diagnostic path for operators
- expose whether the bridge is connected, current persistent mode, last lifecycle event, and last error
- add explicit Pi validation instructions for startup, thinking, reply, shutdown, and recovery
- ensure the diagnostics model is reusable for both plugin-managed and future standalone deployment

Files or modules likely to change:

- plugin-side diagnostics in `integrations/openclaw/ninjaclawbot-plugin/src/`
- optional Python-side status reporting in `ninjaclawbot/src/ninjaclawbot/openclaw/`
- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`
- `InstallationGuide.md`

Lint and validation:

- rerun all Phase 2 plugin and Python validation gates
- verify diagnostics do not expose unsafe raw hardware controls

Manual Raspberry Pi validation required:

- confirm operator can inspect bridge state during startup, idle, thinking, and shutdown
- confirm recovery steps are sufficient after forced gateway stop or bridge crash

Hardware risk:

- low

Documentation updates required:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`
- `InstallationGuide.md`

### Stage 2 Part 2: Target OpenClaw Behavior

The intended user-facing behavior is:

1. Startup
   - when the OpenClaw gateway starts, NinjaClawBot is initialized automatically
   - the robot performs a greeting expression with face and sound
   - after the greeting, the robot moves into persistent `idle`

2. Idle waiting
   - while the OpenClaw agent is waiting for a user query, the robot remains in `idle`
   - `idle` is owned by `ninjaclawbot`, not manually retriggered after every tool call

3. Query received
   - when a user query arrives, the robot shows persistent `thinking`
   - the thinking state remains active until superseded by an explicit reply or fallback idle transition

4. Answer delivery
   - when the final answer is ready, the robot shows the matching answer emotion through the explicit reply-state tool path
   - after the answer reaction completes, the robot returns to `idle`

5. Shutdown
   - when the OpenClaw gateway stops, the robot shows `sleepy`
   - after the expression completes, the display is turned off or put to sleep, and the runtime is cleaned up

### Stage 2 Part 3: Validation Gate

Stage 2 should not be considered complete until Raspberry Pi validation passes with a real OpenClaw gateway session.

Required validation groups:

- safe smoke tests
- bridge startup and restart tests
- lifecycle communication tests
- conversational state-transition tests
- shutdown and recovery tests

Expected outcomes:

- the plugin starts one persistent robot bridge
- the persistent bridge is implemented on top of reusable Python service-core modules
- the robot greets automatically on gateway start
- the robot stays in `idle` while waiting
- the robot shows persistent `thinking` on incoming query
- the robot shows the correct answer emotion and returns to `idle`
- the robot shuts down with `sleepy`, powers off the display, and cleans up safely
- gateway stability is preserved even if robot hardware is unavailable
- adding a future standalone daemon mode should require a new launcher and deployment wrapper, not a redesign of runtime behavior

Rollback path:

- disable Always On lifecycle features in plugin config
- fall back to the current one-shot `ninjaclawbot` plugin tools
- use `ninjaclawbot_stop_all` if runtime behavior becomes unsafe

### Research Basis

Stage 2 planning is based on:

- the existing `ninjaclawbot` runtime, expression, and OpenClaw plugin code in this repository
- official OpenClaw plugin documentation
- official OpenClaw agent-loop lifecycle documentation
- official OpenClaw prompting documentation for `BOOT.md` and callbacks
