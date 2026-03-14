# NinjaClawBot Enhancement Plan

Updated: 2026-03-14
Branch baseline: `clawbotV1_beta_01`

This document is the concise implementation record for the current enhancement work.

- Stage 1 is kept as a completed reference.
- Stage 2 tracks the current OpenClaw-facing robot presence work.
- The validated deployment model is now hybrid:
  - plugin-managed persistent bridge and shutdown
  - OpenClaw `boot-md` plus workspace `BOOT.md` for startup greeting
  - workspace `AGENTS.md` plus enabled skill and tool allowlist for reply-expression behavior

## Stage 1: Completed Foundation

Status: Done

### Objective

Establish the modern `ninjaclawbot` runtime, expression system, and first approved OpenClaw integration boundary on top of the Pi 5 driver libraries.

### Key Implementation Points

- built the expression and reply-state model
- added animated face playback and sound-expression orchestration
- added persistent `idle`
- added `expression-tool`
- added the first official OpenClaw plugin and skill wrapper

### Libraries Affected

- `ninjaclawbot`
- `pi5disp`
- `pi5buzzer`
- `pi5servo`
- `pi5vl53l0x`
- `integrations/openclaw/ninjaclawbot-plugin`

## Stage 2: Always On OpenClaw Integration

Status: In Progress

### Objective

Make NinjaClawBot behave like a continuously present robot companion during OpenClaw gateway use, while keeping the Python service core reusable for a future standalone host.

### Current Validated Build Shape

- minimal supported plugin config:
  - `projectRoot`
  - `rootDir`
  - `uvCommand`
  - `enablePersistentBridge`
  - bridge timeout settings
- startup greeting is validated through `boot-md` and workspace `BOOT.md`
- reply-expression behavior is validated through:
  - tool allowlist
  - enabled `ninjaclawbot_control` skill
  - workspace `AGENTS.md`
- shutdown sleepy and display power-down are validated through the plugin-managed persistent bridge

### Stage 2 Architecture

```text
OpenClaw gateway
  -> NinjaClawBot plugin background service
  -> persistent Python bridge
  -> lifecycle/service core
  -> NinjaClawbotRuntime / ActionExecutor / ExpressionPlayer
  -> pi5disp / pi5buzzer / pi5servo / pi5vl53l0x
```

### Phase 2.1: Persistent Bridge Service

Status: Done

#### Objective

Replace per-call robot process startup with one persistent Python bridge owned by the OpenClaw plugin.

#### Key Implementation Points

- added long-lived `openclaw-serve` bridge support
- kept the one-shot action path as fallback
- moved bridge lifecycle ownership into the plugin service layer
- kept the Python bridge reusable for future standalone deployment

#### Libraries Affected

- `ninjaclawbot`
- `integrations/openclaw/ninjaclawbot-plugin`

### Phase 2.2: Presence Modes And Shutdown Sequence

Status: Done

#### Objective

Add explicit robot presence states and a controlled shutdown sequence instead of one-shot reaction-only behavior.

#### Key Implementation Points

- added persistent presence-mode support for lifecycle control
- added startup, `thinking`, and `idle` presence transitions in the Python service core
- added `sleepy -> display power-down -> cleanup` shutdown sequencing
- kept reply emotion explicit through `reply_state`

#### Libraries Affected

- `ninjaclawbot`
- `pi5disp`
- `pi5buzzer`

### Phase 2.3: Hybrid OpenClaw Lifecycle Integration

Status: Done in validated hybrid deployment form

#### Objective

Wire the persistent robot service into OpenClaw lifecycle behavior without forcing a plugin-only architecture.

#### Key Implementation Points

- plugin-managed bridge start and stop are active
- startup greeting is delivered through OpenClaw `boot-md` and workspace `BOOT.md`
- reply-expression reliability is delivered through:
  - `ninjaclawbot_reply`
  - enabled `ninjaclawbot_control` skill
  - workspace `AGENTS.md`
  - tool allowlist
- shutdown sleepy is driven by the persistent bridge stop path

#### Libraries Affected

- `integrations/openclaw/ninjaclawbot-plugin`
- `ninjaclawbot`
- OpenClaw workspace files and config

### Phase 2.4: Arbitration, Dedupe, Degraded Mode, And Config Hardening

Status: Initial hardening slice implemented and Pi-validated

#### Objective

Make lifecycle behavior deterministic under duplicate, overlapping, stale, or partially degraded events, and align the code with the validated Raspberry Pi deployment.

#### Key Implementation Points

- added service-side suppression and dedupe for:
  - duplicate startup after startup already completed
  - repeated `message_received -> thinking`
  - stale or unnecessary `agent_end -> idle`
- added internal status fields for:
  - activity epochs
  - suppressed lifecycle counts
  - last transition source and reason
  - last explicit action
- added plugin-side bridge telemetry for:
  - `healthy`
  - `degraded`
  - `disabled`
- hardened display config loading so `ninjaclawbot` honors the root `display.json` path and falls back safely when needed
- removed tracked Python cache artifacts and added ignore rules so Pi `git pull` no longer breaks on generated files

#### Libraries Affected

- `ninjaclawbot`
- `integrations/openclaw/ninjaclawbot-plugin`
- `pi5disp`
- repository root ignore/config files

### Phase 2.5: Validation, Observability, And Release Gate

Status: Implemented and Raspberry Pi validated

#### Objective

Make the current build diagnosable by non-developers, expose the real deployment state safely, and turn the validated Raspberry Pi flow into a repeatable release gate.

#### Why This Phase Is Necessary

- the code already tracks useful internal state, but operators still have no direct diagnostics tool
- recent bugs required manual log inspection and config spelunking to understand:
  - bad `uvCommand`
  - missing workspace files
  - missing hook behavior
  - reply-tool selection failures
- the current deployment is hybrid, so readiness depends on more than plugin code alone

#### Key Implementation Points

1. Operator-facing diagnostics
   - add a secret-safe tool such as `ninjaclawbot_diagnostics`
   - expose:
     - bridge status
     - degraded or fallback mode
     - current presence mode
     - startup completion
     - last lifecycle event
     - last error
     - request counters
     - suppression counters

2. Deployment health reporting
   - report whether the validated deployment prerequisites are present:
     - persistent bridge enabled
     - workspace path available
     - `BOOT.md` present
     - `AGENTS.md` present
     - required tools allowlisted
     - `ninjaclawbot_control` skill enabled
   - treat optional lifecycle plugin flags as compatibility overrides, not the primary supported setup

3. Release gate
   - define the release-tested path as:
     - startup greeting
     - reply expression
     - idle recovery
     - sleepy shutdown
     - degraded fallback visibility
   - add a concise regression and Pi validation checklist
   - keep repository hygiene checks in the release gate

4. Recovery and rollback guidance
   - provide a direct path for diagnosing:
     - bridge degradation
     - missing workspace guidance
     - text-only reply fallback
     - one-shot rollback when needed

#### Libraries Affected

- `ninjaclawbot`
- `integrations/openclaw/ninjaclawbot-plugin`
- OpenClaw workspace and deployment documentation

#### Detailed Implementation Plan

##### Phase 2.5A: Operator Diagnostics Surface

Status: Implemented and Raspberry Pi validated

Objective:

- expose the current internal service and bridge state through one simple operator-facing entrypoint
- reuse the status already tracked in the Python service and plugin runner instead of inventing a second state model

Implementation scope:

- add a new OpenClaw tool such as `ninjaclawbot_diagnostics`
- make the tool combine:
  - Python bridge service status
  - plugin-side persistent bridge telemetry
  - a sanitized deployment summary
- keep the output stable, human-readable, and safe to paste into bug reports
- avoid exposing secrets from `openclaw.json`, provider settings, or gateway tokens

Expected diagnostic sections:

- `bridge`
  - `status`
  - `fallback_count`
  - `last_error`
  - `last_successful_persistent_at`
  - `last_mode_change_at`
- `service`
  - `requests_handled`
  - `current_presence_mode`
  - `startup_completed`
  - `last_lifecycle_event`
  - `last_transition_source`
  - `last_transition_reason`
  - `last_explicit_action`
  - `suppressed_lifecycle_events`
- `display`
  - active `config_path`
  - whether root-level config is being used
- `summary`
  - high-level state such as:
    - `healthy`
    - `degraded`
    - `one_shot_fallback`
    - `missing_workspace_guidance`
  - `startup`
    - `trackingMode`
    - `configured`
    - `observedByService`
    - `effectiveCompleted`

Likely implementation shape:

- extend the existing bridge `status` response only where fields are still missing
- add a plugin-side formatter that merges:
  - `readBridgeTelemetry()`
  - bridge `status`
  - deployment inspection hints from the local OpenClaw config and workspace
- register one operator-facing tool in the plugin, not multiple overlapping status tools

Likely files:

- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/schemas.ts`
- `ninjaclawbot/src/ninjaclawbot/openclaw/service.py`
- `ninjaclawbot/src/ninjaclawbot/openclaw/bridge.py`
- plugin diagnostics tests
- `ninjaclawbot/tests/test_openclaw_bridge.py`

Validation gate:

- `npm run typecheck`
- `npm test`
- `uv run --extra dev python -m compileall src tests`
- `uv run --extra dev ruff check src tests`
- `uv run --extra dev ruff format --check src tests`
- `uv run --extra dev pytest -q tests -c pyproject.toml`

Raspberry Pi validation target:

- run diagnostics during:
  - startup
  - idle
  - thinking
  - reply
  - shutdown preparation
- confirm the tool clearly distinguishes:
  - healthy persistent mode
  - degraded persistent mode
  - one-shot fallback mode

Hardware risk:

- low

##### Phase 2.5B: Deployment Health And Readiness Checks

Status: Implemented and Raspberry Pi validated

Objective:

- make diagnostics reflect the real validated deployment model instead of only runtime internals
- catch common Raspberry Pi setup drift before it turns into confusing robot behavior

Implementation scope:

- add deployment health inspection around the validated OpenClaw shape:
  - minimal plugin config
  - internal `boot-md` enabled
  - workspace path present
  - workspace `BOOT.md` present
  - workspace `AGENTS.md` present
  - `ninjaclawbot_control` skill enabled
  - required `ninjaclawbot_*` tools allowlisted
- keep this inspection secret-safe:
  - report booleans, paths, and health hints
  - do not echo tokens, pairing codes, API keys, or provider secrets
- classify results as:
  - `ready`
  - `warning`
  - `misconfigured`

Expected readiness rules:

- `ready`
  - persistent bridge is enabled
  - workspace exists
  - startup guidance exists
  - reply guidance exists
  - tools and skill are present
- `warning`
  - runtime still works, but a non-critical prerequisite is missing
  - example:
    - startup greeting path missing while reply path still works
- `misconfigured`
  - the deployment is likely to fail or partially fail
  - example:
    - bad `uvCommand`
    - missing project root
    - missing allowlist for `ninjaclawbot_reply`

Likely implementation shape:

- add a plugin-side deployment inspector that reads the local OpenClaw deployment files best-effort
- prefer checking the validated minimal config path first
- treat optional lifecycle plugin flags as compatibility overrides only
- if some config fields are not reliably available from the plugin runtime, fall back to documented operator warnings instead of guessing

Likely files:

- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
- new plugin-side deployment health helper under `integrations/openclaw/ninjaclawbot-plugin/src/`
- plugin diagnostics/readiness tests
- `README.md`
- `DevelopmentGuide.md`
- `InstallationGuide.md`

Validation gate:

- same plugin and Python validation gate as Phase 2.5A
- add plugin tests for:
  - missing `BOOT.md`
  - missing `AGENTS.md`
  - missing tool allowlist
  - skill disabled
  - bad `uvCommand`

Raspberry Pi validation target:

- intentionally break one prerequisite at a time and confirm diagnostics report the correct readiness state
- verify the guidance remains readable by non-developers

Hardware risk:

- low

##### Phase 2.5C: Release Gate, Recovery, And Pi Validation Pack

Status: Implemented and Raspberry Pi validated

Objective:

- codify the validated Raspberry Pi deployment into a repeatable release check
- reduce future regressions caused by repo hygiene, config drift, or silent deployment differences

Implementation scope:

- add a release gate that checks:
  - startup greeting path
  - `thinking` transition
  - explicit reply expression path
  - idle recovery
  - sleepy shutdown and display power-down
  - degraded fallback visibility
  - repository hygiene
- add concise recovery guidance for the most common failure modes:
  - bad `uvCommand`
  - persistent bridge unavailable
  - startup greeting missing
  - text-only replies
  - wrong display config path
  - rollback to one-shot mode
- keep the release gate aligned with the current supported deployment model:
  - plugin-managed bridge
  - `boot-md` startup
  - workspace `AGENTS.md`
  - enabled skill and tool allowlist

Expected release-gate deliverables:

- automated checks for code quality and test coverage
- a repository hygiene check that rejects tracked cache artifacts and similar generated files
- a Pi validation checklist split into:
  - safe smoke tests
  - communication tests
  - actuator-moving tests
  - power-risk tests
- a short rollback checklist for operator use after a bad update

Likely implementation shape:

- add one lightweight hygiene check in the repo or test suite
- add a single documented validation flow instead of scattered troubleshooting steps
- make the new diagnostics tool the first step in operator troubleshooting

Likely files:

- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`
- `InstallationGuide.md`
- `EnhancementPlan.md`
- repository hygiene check file or test if needed

Validation gate:

- `npm run typecheck`
- `npm test`
- `uv run --extra dev python -m compileall src tests`
- `uv run --extra dev ruff check src tests`
- `uv run --extra dev ruff format --check src tests`
- `uv run --extra dev pytest -q tests -c pyproject.toml`
- `git diff --check`

Raspberry Pi validation target:

- prove the documented release flow works end-to-end on real hardware
- confirm a non-developer can identify and recover from the common failure modes using the new diagnostics and guide

Hardware risk:

- low to medium

##### Phase 2.5 Completion Criteria

Phase 2.5 is complete only when all of the following are true:

- an operator can run one diagnostics command or tool and understand the current robot state
- the diagnostics output reflects the hybrid OpenClaw deployment that is actually validated on Raspberry Pi
- the release gate catches repo hygiene and deployment drift before another Pi update is attempted
- the installation and developer docs use the new diagnostics and recovery flow as the primary support path

#### Completed Validation Gate

- `npm run typecheck`
- `npm test`
- `uv run --extra dev python -m compileall src tests`
- `uv run --extra dev ruff check src tests`
- `uv run --extra dev ruff format --check src tests`
- `uv run --extra dev pytest -q tests -c pyproject.toml`
 - Raspberry Pi validation completed for:
  - startup
  - reply expression
  - Telegram text reply
  - shutdown
  - diagnostics and recovery flow

## Current Recommended Next Step

The Stage 2 enhancement scope is complete on the validated Raspberry Pi path.

Recommended next step:

1. focus future work on optional long-run stress testing and recovery hardening, not new lifecycle features
3. finish the release gate and Pi validation pack

That keeps the current working robot behavior intact while making the deployment safer to update and easier to support.
